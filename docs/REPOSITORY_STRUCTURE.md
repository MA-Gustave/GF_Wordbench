# GF Wordbench — Repository Structure

**Document ID:** `GF-WB-REPOSITORY-STRUCTURE`  
**Status:** Normative  
**Path:** `docs/REPOSITORY_STRUCTURE.md`  
**Applies to:** GF Wordbench framework repository, active language project, reusable project template, tests, documentation and generated outputs  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** GF Wordbench maintainers  
**Structure version:** `1.1.0`  
**Last structural review:** `2026-07-24`

---

## 1. Purpose

This document defines the canonical repository structure of GF Wordbench.

It establishes:

- where each responsibility belongs;
- which directories are permanent;
- which directories are language-specific;
- which directories are generated;
- which files are authoritative;
- which files may be copied, replaced or deleted;
- which dependency directions are permitted;
- how a new language project is initialized;
- how structural drift is detected and prevented.

This document governs repository-level placement and ownership. Cross-document interpretation is governed by `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`.

Detailed behavioral contracts are defined in:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

The central rule is:

> Every file belongs to one responsibility domain, has one authoritative owner, and must not duplicate another file’s authority.

---

## 2. Design principles

### 2.1 One framework, one active language project

One GF Wordbench copy represents one active language project.

The repository contains:

```text
framework code
+ one active project
+ one clean project template
+ validation evidence
```

GF Wordbench is not designed to host several active language projects in parallel.

To begin another language:

1. clone or duplicate GF Wordbench;
2. reset generated and active-project content;
3. initialize the new active project from `templates/project/`;
4. preserve the framework, tests and documentation.

### 2.2 Framework and project separation

Framework-owned content belongs in:

```text
app/
tests/
docs/
templates/
scripts/
```

Active-language content belongs in:

```text
project/
```

Generated runtime content belongs outside source-owned directories:

```text
runs/
```

Framework code MUST NOT contain active-language identifiers, paths, module suffixes or linguistic decisions except in explicit migration fixtures or clearly marked examples.

### 2.3 One owner per responsibility

Every responsibility has one authoritative location.

Examples:

```text
application defaults       → app/config.py
project identity           → project/project.toml
shared runtime models      → app/models.py
GF source scanning         → app/audit/scanner.py
GF compilation             → app/audit/compiler.py
scenario execution         → app/audit/scenario_runner.py
machine summary            → app/reports/report_json.py
project dependency map     → project/docs/MODULE_DEPENDENCY_MAP.md
project contract lock      → project/docs/INTERFILE_CONTRACT_LOCK.md
```

A second file may explain or consume a responsibility, but it must not redefine it.

### 2.4 Source and generated data separation

Source-owned directories:

```text
app/
tests/
docs/
project/
templates/
scripts/
```

Generated directories:

```text
runs/
build/
dist/
coverage/
```

Generated files MUST NOT become hidden configuration sources.

### 2.5 Stable top-level structure

Top-level directories are stable architectural boundaries.

A top-level directory may be added only when:

- it has a distinct owner;
- it has a distinct lifecycle;
- it cannot fit cleanly into an existing boundary;
- its addition is documented;
- contract and schema locks are updated where required.

### 2.6 Minimal nesting

Directories exist to separate responsibilities, not to mirror every conceptual term.

A new subdirectory is justified when at least one is true:

- it contains multiple related files;
- it has a distinct dependency boundary;
- it has a distinct lifecycle;
- it has a distinct owner;
- it is copied, reset or generated independently.

Single-file directories SHOULD be avoided unless the boundary itself is important.

---

## 3. Canonical repository tree

```text
GF_Wordbench/
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE.md
├── pyproject.toml
├── .gitignore
├── .gf_wordbench_state.json
├── launch_cli.bat
├── launch_gui.bat
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── bootstrap.py
│   ├── state.py
│   ├── main_cli.py
│   ├── main_gui.py
│   │
│   ├── audit/
│   │   ├── __init__.py
│   │   ├── audit_core.py
│   │   ├── file_selector.py
│   │   ├── scanner.py
│   │   ├── compiler.py
│   │   ├── scenario_runner.py
│   │   ├── diagnostics.py
│   │   ├── classifier.py
│   │   ├── fingerprint.py
│   │   ├── diff.py
│   │   └── result_model.py
│   │
│   ├── project/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── validator.py
│   │   ├── initializer.py
│   │   └── reset.py
│   │
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── report_json.py
│   │   ├── report_md.py
│   │   ├── report_ai_ready.py
│   │   ├── report_logs.py
│   │   ├── report_details.py
│   │   └── report_manifest.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── project_schema.py
│   │   ├── state_schema.py
│   │   ├── summary_schema.py
│   │   ├── manifest_schema.py
│   │   └── migrations.py
│   │
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── controller.py
│   │   └── widgets.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── io_utils.py
│       ├── path_utils.py
│       ├── process_utils.py
│       └── text_utils.py
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── audit/
│   │   ├── project/
│   │   ├── reports/
│   │   ├── schemas/
│   │   └── utils/
│   ├── contracts/
│   ├── integration/
│   ├── fixtures/
│   └── legacy/
│
├── docs/
│   ├── 00_START_HERE.md
│   ├── PRODUCT_OVERVIEW.md
│   ├── SCOPE_AND_NON_GOALS.md
│   ├── GLOSSARY.md
│   ├── REPOSITORY_STRUCTURE.md
│   ├── DOCUMENTATION_MAP.md
│   ├── DOCUMENTATION_ALIGNMENT_LOCK.md
│   ├── INTERFILE_CONTRACT_LOCK.md
│   ├── EXTERNAL_TOOL_CONTRACT_LOCK.md
│   ├── PERSISTED_SCHEMA_LOCK.md
│   ├── architecture/
│   ├── gf/
│   ├── validation/
│   ├── scenarios/
│   ├── diagnostics/
│   ├── reports/
│   ├── configuration/
│   ├── usage/
│   ├── projects/
│   ├── development/
│   ├── operations/
│   ├── release/
│   ├── decisions/
│   └── reference/
│
├── project/
│   ├── README.md
│   ├── project.toml
│   ├── docs/
│   └── validation/
│       ├── README.md
│       ├── scenarios/
│       ├── gold/
│       └── inputs/
│
├── templates/
│   └── project/
│       ├── README.md
│       ├── project.toml
│       ├── docs/
│       └── validation/
│           ├── README.md
│           ├── scenarios/
│           ├── gold/
│           └── inputs/
│
├── scripts/
│   ├── init_project.py
│   ├── reset_project.py
│   ├── migrate_project.py
│   ├── validate_contracts.py
│   └── validate_schemas.py
│
└── runs/
    └── run_<run-id>/
```

This structure is normative. Every listed responsibility MUST remain in its designated boundary, and missing required paths are structural nonconformities.

---

## 4. Top-level files

### 4.1 `README.md`

Repository entry point.

It owns:

- concise product identity;
- installation summary;
- quick-start commands;
- links to authoritative documentation.

It MUST NOT duplicate full technical references.

### 4.2 `CHANGELOG.md`

Owns user-visible and compatibility-relevant changes.

It records:

- added features;
- changed behavior;
- fixed defects;
- deprecations;
- migrations;
- breaking changes.

Internal refactors with no external effect MAY be omitted.

### 4.3 `CONTRIBUTING.md`

Owns contribution workflow:

- development setup summary;
- branch or change expectations;
- tests required;
- contract-change procedure;
- documentation responsibilities;
- review checklist.

### 4.4 `SECURITY.md`

Owns:

- supported versions;
- vulnerability reporting;
- secret-handling rules;
- external process safety;
- path traversal and artifact integrity concerns.

### 4.5 `LICENSE.md`

Owns repository licensing terms.

No other file may redefine licensing.

### 4.6 `pyproject.toml`

Owns Python package and tool configuration:

- package identity;
- package version source;
- Python requirement;
- runtime dependencies;
- development dependencies;
- console entry points;
- test configuration;
- lint configuration;
- type-check configuration;
- build-system configuration.

Language-project configuration MUST NOT be stored here.

### 4.7 `.gitignore`

Owns version-control exclusions.

It SHOULD exclude:

```text
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
coverage/
htmlcov/
build/
dist/
*.pyc
*.pyo
runs/
.gf_wordbench_state.json
```

Project scenarios, inputs and gold files MUST NOT be excluded.

### 4.8 `.gf_wordbench_state.json`

Disposable local application state.

It:

- is generated;
- is not authoritative;
- is safe to delete;
- MUST NOT contain project-owned language definitions;
- SHOULD NOT be committed.

Its schema is governed by `docs/PERSISTED_SCHEMA_LOCK.md`.

### 4.9 Windows launchers

```text
launch_cli.bat
launch_gui.bat
```

These are thin convenience wrappers.

They MUST NOT implement audit logic, path policy or validation semantics.

They may:

- locate the repository;
- activate a virtual environment;
- start the canonical Python entry point;
- preserve process exit codes;
- display a clear launcher error.

---

## 5. `app/` — framework runtime

`app/` contains reusable Python framework code.

It MUST remain language-neutral.

### 5.1 Root application modules

#### `app/__init__.py`

Owns:

```text
application package name
application version
```

Package metadata MUST have one source of truth.

#### `app/config.py`

Owns application-wide defaults and stable filename constants.

It MUST NOT own active-language values. Active-language configuration belongs exclusively in `project/project.toml`.

Examples of framework-owned defaults:

```text
default timeout
default output root
report filenames
run-directory prefix
supported validation modes
supported status values
```

#### `app/models.py`

Owns shared runtime data models.

Examples:

```text
AppConfig
ProjectConfig
RunConfig
RunPaths
ScanCounts
CompileSummary
ProcessResult
SourceFingerprint
FileResult
ScenarioResult
DiffEntry
RunResult
```

Serialized meanings are additionally governed by `PERSISTED_SCHEMA_LOCK.md`.

#### `app/bootstrap.py`

Owns construction and validation of runtime configuration.

It combines:

```text
application defaults
+ project configuration
+ environment paths
+ CLI or GUI overrides
```

It MUST NOT execute an audit.

#### `app/state.py`

Owns reading, validation, migration and writing of application state.

It MUST NOT own project identity.

#### `app/main_cli.py`

Owns CLI argument parsing, user-facing CLI output and exit-code selection.

It delegates execution to `audit_core.run_audit()`.

#### `app/main_gui.py`

Owns GUI startup.

It MUST NOT contain audit-stage logic.

---

## 6. `app/audit/` — validation engine

`app/audit/` owns execution and interpretation of validation stages.

### 6.1 `audit_core.py`

Application-level orchestration entry point.

It owns:

- stage ordering;
- mode-specific pipeline selection;
- run lifecycle;
- partial-result handling;
- aggregation into `RunResult`;
- report-stage invocation.

It delegates implementation to specialized modules.

### 6.2 `file_selector.py`

Owns:

- source discovery;
- include and exclude rules;
- target-file selection;
- deterministic ordering;
- module-name extraction where appropriate.

It does not scan or compile files.

### 6.3 `scanner.py`

Owns heuristic static GF source checks.

It does not invoke GF.

It does not determine whether GF compilation succeeds.

### 6.4 `compiler.py`

Owns GF compilation and PGF build requests.

It:

- builds canonical commands;
- calls `process_utils`;
- captures raw evidence;
- returns structured compile summaries.

It does not classify dependency cascades or write reports.

### 6.5 `scenario_runner.py`

Owns native `.gfs` scenario execution.

It:

- resolves configured scenario files;
- invokes GF with scenario input;
- captures raw output;
- validates markers;
- normalizes output;
- compares gold files;
- returns `ScenarioResult`.

Normal execution MUST NOT rewrite gold files.

### 6.6 `diagnostics.py`

Owns normalization and parsing of GF and process diagnostics.

It separates:

```text
raw tool evidence
normalized diagnostic
classification relation
```

It MUST NOT execute external tools.

### 6.7 `classifier.py`

Owns causal classification:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

It consumes existing results and MUST NOT rerun tools.

### 6.8 `fingerprint.py`

Owns stable source fingerprints used for evidence and comparison.

Canonical content hashing uses SHA-256.

### 6.9 `diff.py`

Owns comparison with previous structured summaries.

It MUST consume `summary.json`, not Markdown reports.

### 6.10 `result_model.py`

Owns coherent construction and aggregation of result objects.

It MUST NOT perform external execution.

---

## 7. `app/project/` — active-project lifecycle

This package manages the active project boundary without containing linguistic content.

### 7.1 `loader.py`

Reads `project/project.toml` and constructs `ProjectConfig`.

### 7.2 `validator.py`

Validates:

- schema identity;
- required fields;
- source paths;
- entrypoints;
- checkpoints;
- scenario IDs;
- scenario-to-gold mappings;
- required project documentation.

### 7.3 `initializer.py`

Creates a new active project from `templates/project/`.

It MUST fail safely when destination content would be overwritten without explicit permission.

### 7.4 `reset.py`

Removes or archives active-project and generated content according to reset policy.

It MUST NOT delete framework code, framework tests or framework documentation.

---

## 8. `app/reports/` — persisted presentation and evidence indexes

Report modules consume `RunResult`.

They MUST NOT rerun compilation, scanning or scenarios.

### 8.1 `report_json.py`

Owns canonical `summary.json`.

### 8.2 `report_md.py`

Owns human-readable `summary.md`.

### 8.3 `report_ai_ready.py`

Owns `AI_READY.md`.

It creates a bounded, evidence-linked diagnostic packet without rerunning GF.

### 8.4 `report_logs.py`

Owns aggregate log products such as:

```text
top_errors.txt
ALL_SCAN_LOGS.TXT
ALL_LOGS.TXT
```

Raw stage logs remain owned by their execution stages.

### 8.5 `report_details.py`

Owns curated per-result detail artifacts.

### 8.6 `report_manifest.py`

Owns `manifest.json` and final artifact hashes.

It runs after final artifact writes and MUST NOT hash itself.

---

## 9. `app/schemas/` — persisted schema enforcement

This package implements the contracts documented in `PERSISTED_SCHEMA_LOCK.md`.

### 9.1 Responsibilities

```text
project schema validation
application-state schema validation
run-summary schema validation
manifest schema validation
legacy migration
canonical serialization support
```

### 9.2 Rules

- schema IDs and versions are explicit;
- readers may support documented legacy formats;
- writers emit only canonical current formats;
- migrations do not overwrite source files implicitly;
- schema logic does not execute audits.

---

## 10. `app/gui/` — graphical interface

The GUI is a client of the same framework APIs used by the CLI.

### 10.1 `main_window.py`

Owns view composition and user interaction.

### 10.2 `controller.py`

Owns translation between GUI events and application services.

It may call:

```text
bootstrap
state
audit_core
project lifecycle services
```

It must not call low-level compiler or scanner functions directly.

### 10.3 `widgets.py`

Contains reusable GUI components.

It must not contain business rules.

### 10.4 GUI rule

Equivalent CLI and GUI configuration MUST produce equivalent `RunConfig` and audit behavior.

---

## 11. `app/utils/` — low-level reusable primitives

Utility modules must remain narrow.

### 11.1 `io_utils.py`

Owns:

- UTF-8 text I/O;
- JSON/TOML helpers where appropriate;
- atomic writes;
- directory creation;
- safe copying.

### 11.2 `path_utils.py`

Owns:

- path normalization;
- containment checks;
- project-relative conversion;
- run-relative conversion;
- portable separator handling;
- safe-name generation.

### 11.3 `process_utils.py`

Owns:

- subprocess launch;
- stdin delivery;
- stdout/stderr capture;
- timeout;
- cancellation;
- duration;
- launch-failure distinction.

It MUST NOT interpret GF semantics.

### 11.4 `text_utils.py`

Owns small generic text transformations.

GF-specific diagnostic normalization belongs in `audit/diagnostics.py`, not here.

### 11.5 Utility restriction

A utility module MUST NOT become a miscellaneous dumping ground.

When a helper encodes audit, report, schema or project semantics, it belongs to that domain.

---

## 12. `tests/` — framework verification

Tests are framework-owned and language-neutral unless explicitly placed in legacy fixtures.

### 12.1 Canonical test structure

```text
tests/
├── conftest.py
├── unit/
│   ├── audit/
│   ├── project/
│   ├── reports/
│   ├── schemas/
│   └── utils/
├── contracts/
├── integration/
├── fixtures/
└── legacy/
```

### 12.2 `tests/unit/`

Tests isolated components with no real GF dependency unless a test explicitly targets the process boundary.

### 12.3 `tests/contracts/`

Verifies:

- interfile contracts;
- public models;
- artifact ownership;
- schema consistency;
- forbidden dependency directions;
- deterministic behavior;
- gold immutability.

### 12.4 `tests/integration/`

Verifies complete flows.

Tests requiring a real GF installation MUST be clearly marked and skippable when GF is unavailable.

### 12.5 `tests/fixtures/`

Contains small, neutral fixtures.

Fixture names SHOULD use neutral suffixes such as:

```text
Tst
Example
Fixture
```

They MUST NOT encode the active project.

### 12.6 `tests/legacy/`

Contains documented compatibility fixtures from predecessor formats.

Language-specific historical names are permitted only here when necessary to prove migration.

### 12.7 Test naming

```text
test_<subject>.py
```

Each test file SHOULD own one coherent subject.

---

## 13. `docs/` — framework documentation

`docs/` describes GF Wordbench itself.

It is permanent across language-project replacements.

### 13.1 Root documentation

```text
00_START_HERE.md
PRODUCT_OVERVIEW.md
SCOPE_AND_NON_GOALS.md
GLOSSARY.md
REPOSITORY_STRUCTURE.md
DOCUMENTATION_MAP.md
DOCUMENTATION_ALIGNMENT_LOCK.md
INTERFILE_CONTRACT_LOCK.md
EXTERNAL_TOOL_CONTRACT_LOCK.md
PERSISTED_SCHEMA_LOCK.md
```

These files define the main navigation and normative boundaries.

### 13.2 Documentation families

```text
architecture/    internal structure and dependency boundaries
gf/              GF toolchain integration
validation/      validation pipeline and gates
scenarios/       .gfs and gold test contracts
diagnostics/     parsing and classification
reports/         output artifacts and reports
configuration/   configuration and state
usage/           installation, CLI and GUI
projects/        project lifecycle
development/     contribution and implementation
operations/      run lifecycle and automation
release/         versioning and publication
decisions/       architecture decision records
reference/       stable enumerations and quick references
```

### 13.3 Documentation ownership rule

A rule has one normative owner.

Other documents link to the owner instead of restating the complete rule.

Examples:

```text
repository placement       → REPOSITORY_STRUCTURE.md
cross-document alignment   → DOCUMENTATION_ALIGNMENT_LOCK.md
Python interfile behavior  → INTERFILE_CONTRACT_LOCK.md
external command boundary  → EXTERNAL_TOOL_CONTRACT_LOCK.md
persisted data shape       → PERSISTED_SCHEMA_LOCK.md
status vocabulary          → reference/STATUS_VALUES.md
```

### 13.4 Documentation path rule

Documentation filenames use uppercase `SNAKE_CASE.md`, except:

```text
README.md
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
LICENSE.md
```

ADR filenames use:

```text
ADR-####-UPPERCASE-SLUG.md
```

---

## 14. `project/` — active language project

`project/` contains all replaceable language-specific content.

### 14.1 Canonical structure

```text
project/
├── README.md
├── project.toml
├── docs/
│   ├── 00_PROJECT_START_HERE.md
│   ├── INTERFILE_CONTRACT_LOCK.md
│   ├── LANGUAGE_OVERVIEW.md
│   ├── LANGUAGE_ARCHITECTURE.md
│   ├── MODULE_DEPENDENCY_MAP.md
│   ├── CATEGORY_AND_LINCAT_CONTRACT.md
│   ├── MORPHOLOGY_SPEC.md
│   ├── SYNTAX_AND_CONSTRUCTOR_RULES.md
│   ├── VALIDATION_SPEC.md
│   ├── TEST_COVERAGE_MATRIX.md
│   ├── DECISION_LOG.md
│   ├── KNOWN_ISSUES.md
│   ├── RELEASE_CRITERIA.md
│   └── RESEARCH_EVIDENCE.md
└── validation/
    ├── README.md
    ├── scenarios/
    ├── gold/
    └── inputs/
```

### 14.2 `project/README.md`

Project entry point.

It identifies:

- active language;
- source root;
- entrypoints;
- standard validation commands;
- documentation map.

### 14.3 `project/project.toml`

Authoritative active-project configuration.

It owns:

- project identity;
- language identity;
- source directory;
- file-selection rules;
- GF path parts;
- entrypoints;
- checkpoints;
- required scenarios;
- optional scenarios;
- release targets.

It MUST NOT contain transient GUI state or framework package configuration.

### 14.4 `project/docs/`

Owns language-specific design, contracts, validation criteria and decisions.

Its contents are replaced when the active language changes.

### 14.5 `project/validation/scenarios/`

Contains version-controlled `.gfs` scenario files.

Canonical extension:

```text
.gfs
```

### 14.6 `project/validation/gold/`

Contains reviewed expected outputs.

Canonical extension:

```text
.gold
```

Normal validation MUST NOT modify these files.

### 14.7 `project/validation/inputs/`

Contains stable scenario inputs such as:

```text
sentences
trees
lexical samples
expected category inventories
```

Inputs are source artifacts and SHOULD be version-controlled.

### 14.8 GF source location

The GF source tree may remain in its native repository location.

`project.toml` points to it.

GF source files do not need to be copied into `project/` unless GF Wordbench itself is the source repository.

This distinction prevents GF Wordbench from forcing one source-tree layout on every language project.

---

## 15. `templates/project/` — clean reusable project model

The template mirrors the active-project structure.

```text
templates/project/
├── README.md
├── project.toml
├── docs/
└── validation/
```

### 15.1 Template rule

The template MUST contain:

- generic instructions;
- placeholders;
- empty registries;
- generic validation examples;
- no active-language decisions;
- no old-language identifiers;
- no generated evidence;
- no local absolute paths.

### 15.2 Mirror rule

The active project and template MUST have matching required relative paths.

A required project document added to `project/` MUST also be added to `templates/project/`.

Project-specific content differs; structure does not.

### 15.3 Template contract lock

```text
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

is a normative template.

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

is the populated active-project lock.

They MUST NOT be treated as the same file or maintained as duplicate active contracts.

---

## 16. `scripts/` — maintenance entry points

Scripts are thin maintenance commands around framework services.

### 16.1 Canonical scripts

```text
init_project.py
reset_project.py
migrate_project.py
validate_contracts.py
validate_schemas.py
```

### 16.2 Script rules

Scripts MUST:

- call reusable application modules;
- validate arguments;
- preserve exit codes;
- avoid duplicating business logic;
- be safe by default;
- require explicit confirmation for destructive actions.

Scripts MUST NOT become alternate framework implementations.

### 16.3 Destructive operations

Reset and migration scripts MUST:

- show affected paths;
- preserve framework-owned content;
- avoid deleting source-language repositories;
- support dry-run behavior;
- fail safely on ambiguous roots.

---

## 17. `runs/` — generated validation evidence

`runs/` is generated and disposable as a collection, though individual runs may be archived as evidence.

### 17.1 Canonical run layout

```text
runs/
└── run_<run-id>/
    ├── summary.json
    ├── summary.md
    ├── AI_READY.md
    ├── top_errors.txt
    ├── manifest.json
    ├── details/
    ├── raw/
    │   ├── master.log
    │   ├── ALL_SCAN_LOGS.TXT
    │   ├── ALL_LOGS.TXT
    │   ├── compile/
    │   ├── scan/
    │   └── scenarios/
    └── artifacts/
        ├── gfo/
        ├── out/
        └── pgf/
```

The exact persisted layout is governed by `PERSISTED_SCHEMA_LOCK.md`.

### 17.2 Generated-data rules

- `runs/` SHOULD be ignored by version control.
- A run MUST NOT modify project sources.
- A run MUST NOT modify gold files unless an explicit gold-update command is used.
- Raw evidence MUST remain separate from normalized reports.
- Reports MUST point to artifacts rather than reconstruct locations.
- Cleanup policy MUST preserve explicitly archived release evidence.

### 17.3 No hidden authority

No configuration may be loaded from a previous run unless the operation is explicitly a migration or comparison.

Previous runs provide evidence, not active project identity.

---

## 18. Optional generated directories

### 18.1 `build/`

Temporary package or documentation build output.

Safe to delete.

### 18.2 `dist/`

Published Python distributions or release archives.

Generated by release tooling.

### 18.3 `coverage/` and `htmlcov/`

Generated test-coverage output.

Safe to delete.

These directories MUST NOT contain authoritative source files.

---

## 19. Allowed dependency directions

Expected framework directions:

```text
main_cli/main_gui
        ↓
     bootstrap
        ↓
    audit_core
        ↓
audit stages / project services
        ↓
models / schemas / utils
```

Report direction:

```text
audit_core
    ↓
reports
    ↓
models and existing evidence
```

Project direction:

```text
project.toml
    ↓
project loader
    ↓
bootstrap
    ↓
RunConfig
```

Scenario direction:

```text
project scenario
    ↓
scenario_runner
    ↓
process_utils
    ↓
GF
```

Schema direction:

```text
persisted file
    ↓
schema reader / migrator
    ↓
runtime model
```

---

## 20. Forbidden dependency directions

The following are prohibited:

```text
reports → compiler
reports → scanner
reports → scenario_runner
models → reports
models → GUI
process_utils → audit classification
scanner → compiler
compiler → reports
classifier → process execution
project configuration → GUI state
framework code → active-language implementation
template project → active project
generated run → active project identity
```

Circular dependencies between architectural layers are prohibited.

---

## 21. Naming conventions

### 21.1 Python modules

```text
lowercase_snake_case.py
```

### 21.2 Python packages

```text
lowercase_snake_case/
```

### 21.3 Framework documentation

```text
UPPERCASE_SNAKE_CASE.md
```

### 21.4 Tests

```text
test_<subject>.py
```

### 21.5 Scenarios

```text
lowercase-kebab-case.gfs
```

or:

```text
lowercase_snake_case.gfs
```

One convention MUST be chosen per project and used consistently.

Recommended:

```text
lowercase-kebab-case.gfs
```

### 21.6 Gold files

The gold filename MUST match the scenario stem:

```text
parse-core.gfs
parse-core.gold
```

### 21.7 Run directories

```text
run_<UTC-run-id>
```

### 21.8 Generated logs

Generated log names SHOULD include stable source or scenario identity and an explicit role:

```text
GrammarTst.stdout.txt
GrammarTst.stderr.txt
GrammarTst.scan.txt
parse-core.stdout.txt
parse-core.stderr.txt
parse-core.out
```

---

## 22. Version-control policy

### 22.1 Must be version-controlled

```text
app/
tests/
docs/
project/project.toml
project/docs/
project/validation/scenarios/
project/validation/gold/
project/validation/inputs/
templates/
scripts/
pyproject.toml
README.md
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
LICENSE.md
```

### 22.2 Must normally be ignored

```text
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.gf_wordbench_state.json
runs/
build/
dist/
coverage/
htmlcov/
*.pyc
*.pyo
```

### 22.3 Conditional archives

Selected release runs MAY be archived outside `runs/` or attached to releases.

An archived run MUST be immutable and include its manifest.

---

## 23. Project initialization

Canonical initialization flow:

```text
templates/project/
        ↓
app/project/initializer.py
        ↓
project/
```

The initializer MUST:

1. verify repository root;
2. verify template completeness;
3. detect existing project content;
4. refuse accidental overwrite;
5. copy required structure;
6. populate project identity;
7. validate `project.toml`;
8. verify required documentation;
9. leave scenarios and golds explicit, not silently invented;
10. report created paths.

The initializer MUST NOT copy:

- previous runs;
- application state;
- old-language names;
- generated artifacts;
- active-project decisions from another repository.

---

## 24. Project reset

Canonical reset scope:

```text
project/
runs/
.gf_wordbench_state.json
```

A reset policy may:

- archive the current `project/`;
- restore `project/` from `templates/project/`;
- remove generated runs;
- clear application state.

A reset MUST preserve:

```text
app/
tests/
docs/
templates/
scripts/
repository metadata
```

It MUST NOT delete the external GF source tree referenced by the project unless the user explicitly targets that external path through a separate operation.

---

## 25. Migration from predecessor `gf-audit`

The predecessor structure may contain:

```text
app/
tests/
_gf_audit/
.gf_audit_state.json
language-specific defaults in app/config.py
language-specific names in framework tests
```

Migration to GF Wordbench MUST separate:

```text
framework logic
project configuration
project documentation
generated runs
legacy fixtures
```

### 25.1 Move or transform

```text
.gf_audit_state.json
    → migrate to .gf_wordbench_state.json

_gf_audit/run_*
    → migrate or archive under runs/

language defaults from app/config.py
    → project/project.toml

language-specific framework tests
    → neutral fixtures or tests/legacy/

existing audit modules
    → app/audit/
```

### 25.2 Do not copy blindly

One-time repair scripts, obsolete report aliases and historical state files MUST NOT become permanent GF Wordbench architecture unless they have an ongoing supported role.

### 25.3 Migration evidence

Migration MUST preserve:

- source file hashes where relevant;
- old summary files;
- migration warnings;
- unmapped fields;
- compatibility tests.

---

## 26. Structural extension rules

### 26.1 Adding a file

A new file is justified when it has:

- one coherent responsibility;
- a named owner;
- defined consumers;
- tests or validation;
- no duplicate authority.

### 26.2 Splitting a file

Split when:

- unrelated responsibilities have separate change cycles;
- dependency boundaries are unclear;
- a component has multiple owners;
- testing requires excessive unrelated setup;
- one part is reusable without the other.

Do not split solely to reduce line count.

### 26.3 Merging files

Merge when:

- files always change together;
- neither has an independent public contract;
- separation creates duplicated explanations or forwarding layers;
- a directory contains artificial one-function modules.

Do not merge across an architectural ownership boundary.

### 26.4 Adding a directory

A new directory requires:

- a documented responsibility;
- at least two expected contents or a strong lifecycle boundary;
- dependency direction;
- ownership;
- update to this document;
- update to the documentation map.

### 26.5 Renaming or moving

A move is breaking when another file, persisted schema, launcher, test, user workflow or external tool depends on the path.

Before moving:

1. search all repository references;
2. identify contract IDs;
3. identify persisted path fields;
4. update imports;
5. update tests;
6. update documentation;
7. provide migration aliases when required;
8. validate clean installation and project migration.

---

## 27. Repository anti-drift checks

GF Wordbench SHOULD provide:

```text
gf-wordbench repository check
```

The check SHOULD detect:

- missing required top-level files;
- missing required directories;
- active-language names inside framework code;
- generated files committed in source-owned directories;
- project/template structural mismatch;
- duplicate authoritative configuration;
- report modules importing execution modules;
- invalid dependency directions;
- missing lock files;
- missing required project documents;
- scenario without matching registered identity;
- required scenario without gold when gold is required;
- template files containing populated language identity;
- absolute local paths inside templates;
- run artifacts outside `runs/`;
- project state inside `.gf_wordbench_state.json`;
- unregistered top-level directories.

Strict mode:

```text
gf-wordbench repository check --strict
```

Strict mode MAY additionally detect:

- undocumented public modules;
- empty architectural directories;
- duplicated path constants;
- private-symbol imports across components;
- orphan tests;
- stale renamed paths;
- files with no owner in the component map.

---

## 28. Required structural tests

Required tests:

```text
tests/contracts/test_repository_structure.py
tests/contracts/test_dependency_rules.py
tests/contracts/test_project_template_mirror.py
tests/contracts/test_artifact_ownership.py
tests/contracts/test_no_language_drift.py
```

These tests MUST verify:

- all required paths exist;
- template and active project share required relative paths;
- framework source contains no active-language identifiers;
- generated paths remain ignored;
- forbidden imports are absent;
- root package version source is unique;
- project configuration is authoritative for language identity;
- report modules do not execute GF;
- gold files are not written during normal validation;
- run paths match the persisted schema lock.

---

## 29. Required documentation relationships

This document owns repository placement.

Related documents own:

```text
ARCHITECTURE_OVERVIEW.md
    component purpose and high-level layering

COMPONENT_MAP.md
    exact component ownership and consumers

DEPENDENCY_RULES.md
    detailed permitted and forbidden imports

DOCUMENTATION_ALIGNMENT_LOCK.md
    cross-document interpretation and anti-drift rules

INTERFILE_CONTRACT_LOCK.md
    behavior at Python file boundaries

EXTERNAL_TOOL_CONTRACT_LOCK.md
    GF and operating-system process boundaries

PERSISTED_SCHEMA_LOCK.md
    persistent files and directory schemas

PROJECT_MODEL.md
    active-project lifecycle and semantics

DOCUMENTATION_MAP.md
    documentation navigation and ownership
```

These documents MUST link to this file rather than redefine the full canonical tree.

---

## 30. Structural invariants

The repository MUST satisfy all of the following:

```text
[ ] framework code is language-neutral
[ ] one active project exists
[ ] one clean project template exists
[ ] project and template required paths match
[ ] generated runs are isolated
[ ] persistent paths follow the schema lock
[ ] reports consume evidence without rerunning tools
[ ] GUI and CLI use the same application services
[ ] project identity comes from project.toml
[ ] application state remains disposable
[ ] external tool execution goes through process_utils
[ ] GF-specific execution belongs to audit stages
[ ] schemas and migrations are isolated
[ ] tests are neutral except documented legacy fixtures
[ ] every top-level directory has one lifecycle and owner
[ ] no structural rule is duplicated as a competing authority
```

---

## 31. Enforcement rule

Repository structure is part of the system contract.

A file is not correctly placed merely because the program can import it.

A file is correctly placed when:

- its responsibility matches its directory;
- its dependencies follow the allowed direction;
- its lifecycle matches neighboring files;
- its authority does not duplicate another file;
- its consumers use its documented contract;
- its persisted outputs use the canonical schema;
- its project or framework ownership is unambiguous.

Therefore:

> No file or directory may be added, moved, renamed or repurposed without reviewing ownership, dependencies, persisted paths, tests and documentation as one coordinated structural change.
