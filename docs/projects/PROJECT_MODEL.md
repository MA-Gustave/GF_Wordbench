# GF Wordbench — Project Model

**Document ID:** `GF-WB-PROJECT-MODEL`  
**Status:** Normative specification  
**Applies to:** One active GF language project managed by one GF Wordbench workspace  
**Owner:** GF Wordbench maintainers and active-project maintainers  
**Project schema:** `gf-wordbench.project/1.0`  
**Normative counterparts:**
- `docs/PRODUCT_OVERVIEW.md`
- `docs/SCOPE_AND_NON_GOALS.md`
- `docs/REPOSITORY_STRUCTURE.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`
- `docs/projects/CREATING_A_PROJECT.md`
- `docs/projects/CLONING_AND_RESETTING.md`
- `docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md`
- `docs/projects/PROJECT_COMPLETION_CHECKLIST.md`
- `project/project.toml`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`

**Document version:** `1.0.0`

---

## 1. Purpose

This document defines what a GF Wordbench project is, what it owns, how it is identified, how it relates to the reusable framework, and which assets must remain coherent.

A GF Wordbench project is not merely a directory containing `.gf` files.

It is a controlled unit containing:

- one active language identity;
- one GF source tree;
- one ordered set of module entrypoints;
- zero or more ordered checkpoints;
- one project-level GF path declaration;
- required and optional validation scenarios;
- reviewed scenario inputs and gold expectations;
- architecture and contract documentation;
- issue and decision records;
- release requirements;
- evidence produced by GF Wordbench runs.

The project model exists to make all of those parts refer to the same language implementation and the same intended release surface.

> One GF Wordbench workspace contains exactly one active GF language project.

A different active language is represented by another isolated Wordbench workspace or by an explicit reset, migration, or replacement of the active project—not by selecting a second simultaneous profile inside the same workspace.

---

## 2. Product-level definition

A GF Wordbench project is the language-specific half of the product.

The complete system consists of:

```text
GF Wordbench framework
+
one active GF language project
+
machine-local execution environment
+
run evidence
```

### 2.1 Framework

The framework provides reusable behavior:

- configuration loading;
- path resolution;
- source selection;
- static scanning;
- process execution;
- GF compilation;
- scenario execution;
- normalization;
- gold comparison;
- diagnostics;
- classification;
- reporting;
- manifests;
- release gates.

### 2.2 Active project

The active project provides language-specific facts and assets:

- project identity;
- source layout;
- GF module names;
- entrypoints;
- checkpoints;
- validation scenarios;
- gold expectations;
- architecture;
- public contracts;
- release criteria.

### 2.3 Environment

The environment provides machine-local values:

- GF executable;
- RGL root;
- output root;
- local workspace location;
- platform;
- optional local execution preferences.

### 2.4 Run evidence

A run records what happened for one resolved project and environment state.

Run evidence is output, not project identity.

### 2.5 Portfolio boundary

Multi-workspace discovery, multilingual aggregation, cross-project comparison, and portfolio readiness belong to the independent `gf-portfolio` product.

```text
gf-portfolio -> public versioned GF Wordbench artifacts
```

GF Wordbench does not read Portfolio configuration, persist Portfolio state, or require Portfolio to load, validate, report, or release the active project.

---

## 3. Core project rule

The active project has one authoritative machine-readable definition:

```text
project/project.toml
```

The active project has one authoritative project-level contract lock:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

The project configuration defines what must be selected and validated.

The contract lock defines what project files promise to one another.

Neither file replaces the other.

---

## 4. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **WORKSPACE ROOT**: root containing the framework and the canonical `project/` boundary.
- **PROJECT CONFIGURATION ROOT**: workspace root used to resolve portable paths declared by `project/project.toml`.
- **SOURCE ROOT**: configured directory containing active-language GF sources.
- **ACTIVE PROJECT**: the single language project loaded from one GF Wordbench workspace.
- **ENTRYPOINT**: top-level GF module used for loading, public use, PGF construction, or release validation.
- **CHECKPOINT**: GF module whose successful validation proves a defined project layer.
- **SCENARIO**: registered `.gfs` validation script.
- **GOLD**: reviewed expected normalized output for one scenario variant.
- **PROJECT ASSET**: source-controlled language-specific file owned by the active project.
- **FRAMEWORK ASSET**: language-neutral file owned by GF Wordbench.
- **ENVIRONMENT VALUE**: machine-local value not owned by the portable project.
- **RUN ARTIFACT**: file produced under a run directory.
- **PORTABLE**: relocatable without rewriting machine-local absolute paths into project files.
- **INITIALIZED**: project identity and minimum structure exist.
- **VALIDATABLE**: the framework can resolve and execute the configured project scope.
- **RELEASABLE**: all applicable required release gates can be evaluated.
- **COMPLETE**: the active project satisfies its documented release criteria.

---

## 5. Scope

This document governs:

- the single-active-language constraint;
- project identity;
- project ownership boundaries;
- workspace and project-configuration root semantics;
- source layout;
- module entrypoints;
- checkpoints;
- GF path requirements;
- scenario and gold registries;
- project documentation;
- project issue and decision records;
- release requirements;
- project portability;
- active project replacement;
- project cloning and reset semantics;
- project-model loading and validation;
- interaction with application state;
- interaction with run artifacts;
- project completeness.

This document does not define:

- the complete TOML field reference;
- individual GF command syntax;
- detailed scenario syntax;
- detailed report schemas;
- framework Python internals;
- linguistic rules of a particular language;
- RGL internals;
- source-control platform policy;
- package publication formats.

Those topics belong to their dedicated documents.

---

## 6. Single active language

### 6.1 Invariant

One workspace contains one active project configuration representing one language.

### 6.2 Consequences

The framework MUST NOT offer simultaneous active-language profiles whose sources, scenarios, output histories, or state can be mixed.

The active language is replaced through one of these controlled operations:

```text
clone framework
initialize project
reset project
migrate project
archive and replace project
```

### 6.3 Benefits

The constraint provides:

- one clear project identity;
- one source root;
- one scenario registry;
- one gold registry;
- one run history context;
- one release decision surface;
- reduced state leakage;
- simpler AI handoff;
- stronger anti-drift validation.

### 6.4 Prohibited inference

Active language identity MUST NOT be inferred from:

- the last opened source file;
- GUI state;
- output-directory names;
- previous run summaries;
- legacy project names;
- module filename suffix guesses;
- the RGL root;
- current working directory alone.

Identity comes from `project/project.toml`.

---

## 7. Project boundaries

### 7.1 Framework-owned boundary

The framework owns:

```text
app/
tests/
docs/
templates/
launchers and package metadata
```

Framework files MUST remain language-neutral except for explicitly labelled examples and migration fixtures.

### 7.2 Project-owned boundary

The active project owns:

```text
project/project.toml
project/README.md
project/docs/
project/validation/
active-language GF sources
project-specific fixtures
```

### 7.3 Environment-owned boundary

Machine-local configuration owns:

```text
GF executable path
RGL root
output root
local project location
local timeout preference
local UI state
```

### 7.4 Run-owned boundary

GF Wordbench owns:

```text
run_<run-id>/
```

including reports, logs, normalized outputs, `.gfo`, `.pgf`, and manifests generated for that run.

### 7.5 Ownership rule

A component may read another owner's asset only through the documented contract.

It MUST NOT silently rewrite an asset it does not own.

---

## 8. Canonical project structure

Recommended active-project structure:

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
    │   └── README.md
    ├── gold/
    │   └── README.md
    └── inputs/
        └── README.md
```

The active-language source tree may live elsewhere beneath the repository root, as declared by:

```toml
[sources]
directory = "..."
```

### 8.1 Exactness

The structure above is canonical.

A project may add language-specific subdirectories and files.

It MUST NOT remove required authorities without changing the project contract.

---

## 9. Project identity

### 9.1 Canonical fields

Schema `1.0` defines:

```toml
[project]
id = "<stable-id>"
name = "<display-name>"
language_code = "<language-identifier>"
root = "."
```

### 9.2 `project.id`

`project.id` is:

- stable;
- machine-oriented;
- path-safe;
- lowercase recommended;
- unique within an organization's project set.

It is used to associate runs and migrations with the intended project.

### 9.3 `project.name`

Human-readable project or language name.

It may include spaces and Unicode.

### 9.4 `language_code`

Stable language identifier.

It SHOULD use a recognized language code where appropriate, but the project model does not require one external registry when the project has a justified internal identifier.

### 9.5 `project.root`

Canonical value:

```text
.
```

A different value requires a documented repository-layout reason and valid schema semantics.

### 9.6 Stability

Changing `project.id` after published runs exist is a breaking project migration.

Changing display name without changing project identity may be compatible when all user-facing project documents are updated.

---

## 10. Project configuration schema

The canonical schema identity is:

```text
gf-wordbench.project/1.0
```

Canonical top-level areas:

```text
project
sources
gf
modules
validation
```

### 10.1 Configuration purpose

`project.toml` contains:

- stable project facts;
- portable source selection;
- portable GF path requirements;
- ordered module selection;
- validation registry;
- release PGF requirement.

### 10.2 Configuration exclusions

It MUST NOT store:

- transient GUI state;
- last-run paths;
- absolute `gf.exe` path;
- absolute RGL root;
- output root;
- secrets;
- runtime objects;
- current process state;
- raw diagnostic evidence.

### 10.3 Schema changes

New canonical fields require coordination with:

```text
docs/PERSISTED_SCHEMA_LOCK.md
docs/configuration/PROJECT_TOML_REFERENCE.md
project loader
project model
bootstrap
tests
migration policy
```

---

## 11. Canonical schema `1.0`

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "example"
name = "Example Language"
language_code = "xyz"
root = "."

[sources]
directory = "lib/src/example"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "( - Copie\\.gf$|\\.bak\\.gf$|\\.tmp\\.gf$|\\.disabled\\.gf$|\\s)"

[gf]
path_parts = [
  "lib/src",
  "lib/src/example",
  "abstract",
  "common",
  "prelude",
]
minimum_version = ""

[modules]
entrypoints = [
  "GrammarXyz.gf",
  "SyntaxXyz.gf",
]
checkpoints = [
  "MorphoXyz.gf",
  "NounXyz.gf",
  "VerbXyz.gf",
  "ExtendXyz.gf",
  "StructuralXyz.gf",
]

[validation]
required_scenarios = [
  "load",
  "missing",
  "linearize",
  "parse",
]
optional_scenarios = [
  "generation",
  "morphology",
]
release_requires_pgf = true
```

This is a neutral example.

Active projects replace all example identity and module values.

---

## 12. Source model

### 12.1 Source authority

The active source root is:

```toml
[sources]
directory = "..."
```

### 12.2 Source root properties

The source root MUST:

- resolve from a portable path declared relative to the workspace root;
- remain within an approved source boundary;
- exist for GF-backed validation;
- contain active-language source files selected by project rules;
- avoid machine-local absolute paths in project-owned configuration;
- agree with project documentation.

### 12.3 File selection

Selection uses:

```text
directory
glob
include_regex
exclude_regex
```

The selected inventory must be deterministic.

### 12.4 Required files

Configured entrypoints and checkpoints must not be excluded by source-selection rules.

### 12.5 Project source vs RGL source

Project source and RGL source are separate.

Project source belongs to the active project.

RGL source belongs to the configured external toolchain environment.

### 12.6 Generated files

Generated `.gfo` and `.pgf` files are not project source.

They SHOULD be isolated in run-owned artifact directories.

---

## 13. GF path model

### 13.1 Project declaration

```toml
[gf]
path_parts = [...]
```

The list describes portable project and RGL path requirements.

### 13.2 Machine-local root

The RGL root is supplied by environment configuration.

It is not stored as an absolute path in the project file.

### 13.3 Ordering

`path_parts` is ordered.

A loader MUST preserve declaration order.

### 13.4 Accepted categories

Path parts may represent:

- project-relative directories;
- documented RGL aliases;
- explicitly prefixed project/RGL paths when supported.

### 13.5 Shared resolution

Compilation, scenarios, introspection, and PGF construction consume one centralized resolved GF path.

### 13.6 Minimum version

```toml
minimum_version = ""
```

Empty means no project-level minimum beyond the framework policy.

A non-empty value may make project requirements stricter.

---

## 14. Module model

The project declares two ordered module groups:

```text
entrypoints
checkpoints
```

They are not interchangeable.

---

## 15. Entrypoints

### 15.1 Definition

An entrypoint is a top-level GF module used for one or more of:

- release compilation;
- grammar loading;
- syntax/API exposure;
- scenario execution;
- PGF construction;
- release validation;
- external use.

### 15.2 Required properties

Each configured entrypoint MUST:

- exist;
- resolve under project source rules;
- have a module name consistent with the file;
- have documented purpose;
- have documented consumers;
- compile under its required validation mode;
- appear in project architecture and dependency documentation;
- remain in stable declared order.

### 15.3 Multiple entrypoints

A project may declare several entrypoints, such as:

```text
grammar entrypoint
syntax entrypoint
language/API entrypoint
application entrypoint
```

Success of one does not imply success of another.

### 15.4 Release surface

The project-level contract identifies which entrypoint produces the expected PGF.

### 15.5 Silent substitution

GF Wordbench MUST NOT replace a failing configured entrypoint with another module and report success.

---

## 16. Checkpoints

### 16.1 Definition

A checkpoint is a module whose successful validation proves a coherent project layer.

Examples may include:

```text
morphology
categories
noun phrase
verb phrase
extensions
structural words
top-level concrete grammar
```

### 16.2 Purpose

Checkpoints provide:

- focused development milestones;
- earlier root-cause detection;
- stable dependency ordering;
- release prerequisites;
- evidence that lower layers work independently.

### 16.3 Optionality in schema

The `checkpoints` array may be empty during bootstrap.

A mature project SHOULD define checkpoints unless its architecture genuinely has no useful intermediate layers.

### 16.4 Ordering

Checkpoint order is semantically significant.

It should follow dependency direction from lower to higher layers.

### 16.5 Release relationship

A release entrypoint passing does not permit omission of required lower checkpoints when project release policy requires them.

---

## 17. Module dependency model

The source project is a directed dependency graph.

Recommended direction:

```text
resources and morphology
    → category implementations
    → syntax, structural, and extension modules
    → grammar and syntax entrypoints
    → language or API entrypoint
    → PGF
```

### 17.1 Authoritative documentation

```text
project/docs/MODULE_DEPENDENCY_MAP.md
```

### 17.2 Required consistency

The dependency map must agree with:

- actual imports;
- project architecture;
- checkpoints;
- entrypoints;
- interfile contract lock;
- scenario entrypoint targets.

### 17.3 Circularity

Circular module dependencies are prohibited unless GF semantics and project architecture explicitly permit a documented structure that is not an import cycle.

### 17.4 Failure classification

Dependency information supports direct/downstream classification.

It does not override GF compiler evidence.

---

## 18. Public project contracts

The project is a network of providers and consumers.

Contract domains include:

```text
CONFIG
MODULE
LINCAT
HELPER
ENTRY
SCENARIO
GOLD
ARTIFACT
DOC
RELEASE
```

### 18.1 Authority

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

### 18.2 Contract requirement

Any behavior relied upon across files becomes contractual.

Examples:

- public `oper`;
- constructor arity;
- lincat field;
- parameter value;
- entrypoint name;
- scenario ID;
- gold mapping;
- expected PGF name.

### 18.3 Internal freedom

A file may be refactored internally when all externally visible promises remain compatible.

### 18.4 Coordinated change

A contract-changing edit must update:

- provider;
- direct consumers;
- downstream entrypoints;
- scenarios;
- golds;
- configuration;
- dependency map;
- issue and decision records;
- contract lock;
- validation evidence.

---

## 19. Scenario model

### 19.1 Registry

Schema `1.0` declares:

```toml
[validation]
required_scenarios = [...]
optional_scenarios = [...]
```

### 19.2 Scenario asset

Canonical scenario path:

```text
project/validation/scenarios/<scenario-id>.gfs
```

### 19.3 Required scenario

A required scenario:

- must exist;
- must have unique ID;
- must have documented purpose;
- must load a documented entrypoint;
- must use finite execution bounds;
- must complete required markers/assertions;
- must run in every mode that requires it;
- must not be skipped in release mode.

### 19.4 Optional scenario

An optional scenario:

- may be selected by mode or user;
- remains registered and documented;
- does not become release evidence unless project release policy activates it.

### 19.5 Scenario order

Scenario execution order follows the deterministic project declaration or its structured scenario registry.

### 19.6 Native GF scripts

Scenarios remain native `.gfs` assets.

GF Wordbench orchestrates them but does not implement a replacement GF shell.

---

## 20. Scenario input model

Canonical root:

```text
project/validation/inputs/
```

Inputs may include:

- phrases;
- trees;
- morphology items;
- lexical lists;
- expected-case registries;
- project-specific test corpora.

### 20.1 Input rules

Inputs MUST:

- be project-controlled;
- use documented encoding;
- have documented line/record meaning;
- remain compatible with the scenario;
- be deterministic for release;
- avoid secrets and unrelated personal data.

### 20.2 Generated inputs

Generated temporary inputs do not replace reviewed canonical inputs during release unless the generation process itself is a locked and validated contract.

---

## 21. Gold model

Canonical root:

```text
project/validation/gold/
```

### 21.1 Ownership

Gold files are owned by project maintainers.

### 21.2 Mapping

Every required gold-backed scenario maps to one authoritative `.gold` file per declared variant.

### 21.3 Read-only normal validation

Quick, checkpoint, diagnostic, and release validation MUST NOT update gold files.

### 21.4 Explicit update

Gold creation/update is a separate reviewed operation.

### 21.5 Version control

Required gold files SHOULD be version-controlled with their scenarios and project changes.

### 21.6 Empty gold

An empty expected section is valid only when documented as meaningful.

---

## 22. Validation model

The project model declares validation intent; GF Wordbench executes it.

Validation layers:

```text
static source policy
module compilation
checkpoint compilation
entrypoint compilation
scenario execution
gold comparison
completeness checks
PGF build
release gates
```

### 22.1 Required specification

```text
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
```

### 22.2 Coverage

```text
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
```

### 22.3 Executable evidence

Every release criterion SHOULD have executable evidence where possible.

Manual criteria must state:

- owner;
- procedure;
- expected result;
- evidence location.

---

## 23. Validation modes and project scope

### 23.1 `quick`

Project contribution:

- target source context;
- relevant path parts;
- optional smoke scenario.

### 23.2 `checkpoint`

Project contribution:

- selected checkpoint;
- related modules;
- related scenarios;
- related golds.

### 23.3 `diagnostic`

Project contribution:

- broad source inventory;
- all useful scenarios;
- extended evidence.

### 23.4 `release`

Project contribution:

- all required checkpoints;
- all release entrypoints;
- all required scenarios;
- all required golds;
- completeness policy;
- PGF requirement;
- project release criteria;
- blocker registers.

---

## 24. Release model

### 24.1 Project release authorities

```text
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/KNOWN_ISSUES.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

### 24.2 PGF requirement

Schema `1.0` defines:

```toml
release_requires_pgf = true | false
```

### 24.3 Release-ready requirement

A project is release-ready only when all applicable required release gates are `OK` in one current release run.

### 24.4 Project blockers

Examples:

- missing required module;
- failing checkpoint;
- failing entrypoint;
- required scenario failure;
- gold mismatch;
- unapproved missing function;
- release-blocking known issue;
- missing required PGF;
- stale language identity;
- unresolved project contract.

### 24.5 Project limitation

A documented project limitation may be non-blocking only when the declared project scope explicitly permits it and the release criteria classify it accordingly.

---

## 25. Documentation model

Project documentation is part of the project, not optional commentary.

It defines design intent consumed by maintainers, validators, and AI-assisted workflows.

### 25.1 Start document

```text
project/docs/00_PROJECT_START_HERE__PROJECT_DOCS.md
```

Navigation, project identity, and authoritative document map.

### 25.2 Language overview

```text
project/docs/LANGUAGE_OVERVIEW.md
```

Language scope, intended coverage, and high-level features.

### 25.3 Architecture

```text
project/docs/LANGUAGE_ARCHITECTURE.md
```

Module layers, ownership, dependency direction, entrypoints.

### 25.4 Dependency map

```text
project/docs/MODULE_DEPENDENCY_MAP.md
```

Actual imports and downstream relationships.

### 25.5 Category/lincat contract

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

Cross-module category representations and consumed fields.

### 25.6 Morphology specification

```text
project/docs/MORPHOLOGY_SPEC.md
```

Morphological parameters, paradigms, irregularity and validation intent.

### 25.7 Syntax/constructor specification

```text
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
```

Construction rules, agreement behavior, complement structure, and public syntax assumptions.

### 25.8 Validation specification

```text
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
```

Required scenarios, assertions, golds, completeness checks, and mode mapping.

### 25.9 Coverage matrix

```text
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
```

Maps features/contracts to validation proof.


### 25.11 Decision log

```text
project/docs/DECISION_LOG.md
```

Records significant architectural and behavioral decisions.

### 25.12 Known issues

```text
project/docs/KNOWN_ISSUES.md
```

Records defects and limitations that affect behavior, validation, or release scope.

### 25.13 Release criteria

```text
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

Defines project-specific release acceptance.

### 25.14 Research evidence

```text
project/docs/RESEARCH_EVIDENCE.md
```

Records linguistic sources, evidence, uncertainties, and traceability.

---

## 26. Issue model

`KNOWN_ISSUES.md` tracks defects and limitations.

Each issue SHOULD define:

```text
issue ID
title
affected scope
severity
status
release impact
reproduction/evidence
workaround
owner
target
decision
```

### 26.1 Release blocker

A release-blocking issue cannot be ignored silently.

### 26.2 Duplicate tracking

One issue should have one authoritative entry.

Source comments may reference the issue ID but should not replace the issue record.

---

## 27. Decision model

Significant project changes require a decision record.

Examples:

- changing module ownership;
- changing public lincat shape;
- changing entrypoints;
- changing scenario IDs;
- accepting a linguistic behavior difference;
- changing normalization;
- accepting a project limitation;
- changing expected PGF name;
- migrating GF/RGL baseline.

### 27.1 Decision record

Recommended fields:

```text
decision ID
date
status
context
decision
alternatives
consequences
affected contracts
affected validation
migration
```

### 27.2 Immutable history

Superseded decisions remain recorded and link to the replacement decision.

---

## 28. Research evidence model

Linguistic decisions should be traceable.

Research evidence may include:

- grammar references;
- corpus examples;
- official orthography sources;
- dictionaries;
- scholarly analyses;
- native-speaker review;
- project-specific test observations.

### 28.1 Separation

Research evidence supports design decisions.

It does not automatically define executable behavior until translated into project specification and validation.

### 28.2 Uncertainty

Conflicting or incomplete evidence should remain visible.

The project must not present an unresolved hypothesis as settled release behavior without an explicit decision.

---

## 29. Initialization

Initialization creates a new active project from the language-neutral template.

It should create or resolve:

- `project.toml`;
- project README;
- required project documents;
- validation directories;
- initial source directory;
- entrypoints;
- checkpoints;
- initial scenario registry;
- release requirement.

### 29.1 Placeholder handling

Template placeholders are permitted before initialization.

They are prohibited in a release candidate.

### 29.2 Initial validity

An initialized project may have:

```text
required_scenarios = []
checkpoints = []
```

during bootstrap if schema and documentation explicitly permit it.

It is not complete merely because configuration parses.

---

## 30. Cloning

Cloning creates another independent GF Wordbench copy.

### 30.1 Preserved framework assets

Clone:

```text
app/
tests/
docs/
templates/
package metadata
generic launchers
```

### 30.2 Active project options

A clone may:

- preserve the active project to create an independent branch;
- replace it with a new initialized project;
- archive it and reset.

### 30.3 Run history

Run directories should not be copied into a clean language template unless archival purpose is explicit.

### 30.4 Machine-local state

Application state should not be treated as portable project identity.

---

## 31. Resetting

Reset removes active-language content while preserving the framework.

### 31.1 Reset targets

Reset should replace or remove:

- active project configuration;
- active project documentation;
- project validation scenarios;
- project inputs;
- project golds;
- active-language source paths or references;
- stale GUI language state;
- stale run pointers.

### 31.2 Preserved assets

Preserve:

- framework code;
- framework tests;
- framework documentation;
- generic project templates;
- migration fixtures;
- archived project package when requested.

### 31.3 Old-language scan

A reset should detect stale identifiers in:

```text
project/
active source tree
launchers/config defaults
state
scenario/gold filenames
documentation
```

### 31.4 No partial identity

A reset must not leave a new project configuration pointing to old-language modules.

---

## 32. Migration

Migration converts an existing language or legacy GF Audit setup into the canonical project model.

### 32.1 Migration inputs

May include:

- GF source tree;
- old scan-directory settings;
- old GF path;
- old GUI state;
- old entrypoint knowledge;
- old audit reports;
- informal test scripts;
- legacy language documentation.

### 32.2 Migration output

Must produce:

- canonical `project.toml`;
- mapped source root;
- documented entrypoints;
- documented checkpoints;
- scenario registry;
- project documentation baseline;
- migration warnings and losses.

### 32.3 No silent rewrite

Opening a project may propose migration.

Normal validation MUST NOT silently rewrite project configuration.

### 32.4 Legacy runs

Historical GF Audit summaries may be imported for comparison but cannot retroactively prove missing scenario or release evidence.

---

## 33. Portability

A portable project can move to another machine without editing language-specific facts solely because filesystem roots differ.

### 33.1 Portable project values

Use project-relative paths for:

```text
source directory
scenario paths
input paths
gold paths
module paths
project documents
```

### 33.2 Non-portable environment values

Keep outside the project:

```text
absolute GF executable
absolute RGL root
absolute output root
user home
temporary directories
IDE paths
```

### 33.3 New machine procedure

A new environment should only need to supply:

- local workspace location;
- GF executable;
- RGL root;
- output root;
- approved local execution settings.

### 33.4 Portability test

Project validation should include a path check that rejects accidental absolute machine-specific values in project-owned files where prohibited.

---

## 34. Application state relationship

Canonical state file:

```text
.gf_wordbench_state.json
```

### 34.1 State purpose

State stores disposable local preferences:

- environment paths;
- selected validation mode;
- timeout;
- UI selection;
- last-run pointers.

### 34.2 State non-authority

Deleting state must not damage project definition.

### 34.3 Project precedence

Project-owned facts come from `project.toml`, not state.

### 34.4 UI overrides

CLI or GUI may override permitted execution settings.

They MUST NOT silently bypass required project release constraints.

### 34.5 No language duplication

State must not become a second store for:

- active language;
- source root;
- entrypoints;
- checkpoints;
- scenario registry;
- expected PGF.

---

## 35. Run relationship

A project may have many runs.

A run belongs to exactly one resolved project identity.

### 35.1 Run metadata

Each run records:

```text
project ID
project name
project-configuration root
source root
mode
GF toolchain
source fingerprints
entrypoints/checkpoints/scenarios selected
artifacts
outcome
```

### 35.2 Run immutability

A finalized run is evidence of historical project state.

Changing the active project does not rewrite old runs.

### 35.3 Compatibility for diff

Run-to-run comparison requires compatible project identity and result semantics.

### 35.4 Cross-project comparison

Comparing different project IDs as if they were one timeline is prohibited by default.

---

## 36. Project loading pipeline

Recommended loading pipeline:

```text
locate project.toml
→ parse TOML
→ validate schema identity/version
→ validate required fields
→ normalize portable paths
→ resolve workspace and project-configuration roots
→ resolve source model
→ preserve ordered modules/scenarios
→ validate registries
→ build immutable ProjectModel
→ merge permitted environment configuration
→ construct resolved RunConfig
```

### 36.1 No partial object leakage

Invalid configuration should not produce a partially trusted active project object.

### 36.2 Validation phases

Separate:

```text
schema validation
semantic validation
filesystem validation
contract validation
execution prerequisites
release-gate prerequisites
```

### 36.3 Diagnostics

Project-load diagnostics must identify:

```text
field/path
problem
severity
source file
suggested correction
```

---

## 37. Recommended in-memory model

The persisted schema remains authoritative.

A typed in-memory model is recommended:

```python
@dataclass(frozen=True, slots=True)
class ProjectIdentity:
    project_id: str
    name: str
    language_code: str
    root: Path
```

```python
@dataclass(frozen=True, slots=True)
class ProjectSources:
    directory: Path
    glob: str
    include_regex: str
    exclude_regex: str
```

```python
@dataclass(frozen=True, slots=True)
class ProjectGFRequirements:
    path_parts: tuple[str, ...]
    minimum_version: str | None
```

```python
@dataclass(frozen=True, slots=True)
class ProjectModules:
    entrypoints: tuple[str, ...]
    checkpoints: tuple[str, ...]
```

```python
@dataclass(frozen=True, slots=True)
class ProjectValidation:
    required_scenarios: tuple[str, ...]
    optional_scenarios: tuple[str, ...]
    release_requires_pgf: bool
```

```python
@dataclass(frozen=True, slots=True)
class ProjectModel:
    schema_id: str
    schema_version: str
    config_path: Path
    identity: ProjectIdentity
    sources: ProjectSources
    gf: ProjectGFRequirements
    modules: ProjectModules
    validation: ProjectValidation
```

### 37.1 No undocumented fields

Runtime consumers must not attach dynamic project properties.

Future fields require typed and schema-coordinated extension.

### 37.2 Immutability

After successful loading, `ProjectModel` SHOULD be immutable for a run.

---

## 38. Model invariants

The project model enforces:

1. one project configuration;
2. one active project ID;
3. one source root;
4. at least one entrypoint;
5. unique entrypoints;
6. unique checkpoints;
7. unique scenario IDs across required and optional lists;
8. deterministic list order;
9. project-relative portable paths;
10. no environment roots in project configuration;
11. no active-language identity in framework defaults;
12. project documents agree with project identity;
13. configured modules exist before release;
14. required scenarios exist before release;
15. required golds exist when declared;
16. expected PGF contract is explicit when required;
17. no normal validation rewrites project assets;
18. project changes do not rewrite historical run evidence;
19. reset removes old-language identity;
20. schema changes are versioned and migrated.

---

## 39. Semantic validation

Beyond schema parsing, the loader/checker SHOULD validate:

- `project.id` syntax;
- source root containment;
- regular-expression validity;
- path-part syntax;
- entrypoint filename syntax;
- checkpoint filename syntax;
- duplicate module paths;
- duplicate scenario IDs;
- required/optional scenario overlap;
- missing entrypoints;
- missing checkpoints;
- missing scenario files;
- stale project identity;
- unresolved placeholders;
- contradictory PGF requirement;
- missing project documents.

### 39.1 Timing

Some filesystem checks may be deferred during initialization.

They become mandatory for relevant validation and release modes.

---

## 40. Project completeness

A complete project is not defined solely by module count.

Completion requires:

- intended language scope documented;
- architecture coherent;
- public cross-file contracts documented;
- required modules present and valid;
- required checkpoints passing;
- release entrypoints passing;
- required scenarios passing;
- gold expectations reviewed and matching;
- completeness/missing policy passing;
- blocking known issues resolved;
- required documentation current;
- required PGF built when applicable;
- release manifest verified;
- release decision `READY`.

### 40.1 Partial projects

GF Wordbench may manage an intentionally partial language project.

Its `RELEASE_CRITERIA.md` must state the accepted scope clearly.

It must not describe partial coverage as complete full-language support.

---

## 41. Project versioning

Schema `1.0` does not require a project release-version field.

Project versioning may be tracked through:

- source-control tags;
- release records;
- changelog;
- release artifact metadata;
- a versioned project schema extension.

### 41.1 Schema vs project version

Do not confuse:

```text
project schema version
GF Wordbench package version
GF core version
RGL identity
language project release version
normalization version
```

Each has separate meaning.

### 41.2 Future field

Adding a canonical project release-version field requires a project-schema minor or major revision according to compatibility impact.

---

## 42. Framework compatibility

An active project depends on a compatible GF Wordbench framework contract.

### 42.1 Minimum project-schema support

The framework must support the project's schema major version or require migration.

### 42.2 Feature requirements

A project must not declare a validation feature the installed framework cannot interpret.

### 42.3 No silent downgrade

Unsupported project semantics cannot be silently ignored during release validation.

### 42.4 Template compatibility

The bundled template version should match the current framework's canonical project schema.

---

## 43. Template model

Canonical template root:

```text
templates/project/
```

The template mirrors the active-project structure.

### 43.1 Template properties

The template MUST be:

- language-neutral;
- schema-valid or intentionally placeholder-valid under initializer rules;
- free of old active-language content;
- complete enough to initialize every required project document;
- aligned with the current project schema.

### 43.2 Template placeholders

Placeholders are allowed in template documents.

They must be replaced or explicitly removed during initialization.

### 43.3 Active project copy

Initialization copies or renders template assets into:

```text
project/
```

After initialization, the active project owns its copies.

Template updates must not overwrite an active project automatically.

---

## 44. Project identity migration

Changing any of the following requires coordinated migration:

```text
project.id
language_code
source root
module suffix
entrypoint names
scenario IDs
gold filenames
expected PGF name
```

### 44.1 Migration review

Review:

- project configuration;
- source filenames/module declarations;
- imports;
- scenarios;
- inputs;
- golds;
- project docs;
- run comparison policy;
- external consumers;
- release artifacts.

### 44.2 Historical identity

Old runs retain old identity.

A migration may define predecessor linkage, but must not rewrite historical summaries as if produced under the new identity.

---

## 45. Project deletion and archival

### 45.1 Archive

An archive should preserve:

- project source;
- `project.toml`;
- project documentation;
- validation assets;
- release evidence;
- toolchain identity;
- manifest.

### 45.2 Delete

Deleting an active project should require deliberate action.

Framework assets must remain intact unless the user is deleting the complete repository.

### 45.3 Restore

A restored project must be schema-validated and environment-resolved before execution.

---

## 46. Security and trust

A project may contain executable or semi-executable inputs.

### 46.1 Untrusted assets

Treat as untrusted until reviewed:

- `.gfs` scenarios;
- source paths;
- input paths;
- project configuration;
- external helper scripts;
- symlinks.

### 46.2 Path containment

Project-relative paths must remain beneath permitted roots after resolution.

### 46.3 Scenario shell escapes

Operating-system shell commands inside scenarios are prohibited in normal policy unless explicitly authorized.

### 46.4 Secrets

Project configuration and project documentation must not store secrets.

### 46.5 External source trees

A source directory outside the workspace root requires an explicit approved external-source contract and is not supported by the default project model.

---

## 47. Project diagnostics

Recommended project diagnostic codes:

```text
PROJECT_CONFIG_MISSING
PROJECT_SCHEMA_ID_INVALID
PROJECT_SCHEMA_VERSION_UNSUPPORTED
PROJECT_ID_INVALID
PROJECT_ID_MISMATCH
PROJECT_ROOT_INVALID
PROJECT_SOURCE_ROOT_MISSING
PROJECT_SOURCE_ROOT_OUTSIDE
PROJECT_REGEX_INVALID
PROJECT_PATH_PART_INVALID
PROJECT_ENTRYPOINT_MISSING
PROJECT_ENTRYPOINT_DUPLICATE
PROJECT_CHECKPOINT_MISSING
PROJECT_CHECKPOINT_DUPLICATE
PROJECT_SCENARIO_DUPLICATE
PROJECT_SCENARIO_OVERLAP
PROJECT_SCENARIO_MISSING
PROJECT_GOLD_MISSING
PROJECT_DOCUMENT_MISSING
PROJECT_PLACEHOLDER_UNRESOLVED
PROJECT_STALE_LANGUAGE_IDENTIFIER
PROJECT_CONTRACT_INCONSISTENT
PROJECT_RELEASE_REQUIREMENT_INCOMPLETE
PROJECT_MIGRATION_REQUIRED
```

### 47.1 Error categories

Project model errors normally use:

```text
error_kind = CONFIG
```

A project criterion that executes and fails may use `FAIL`.

A project that cannot be interpreted safely produces `ERROR`.

---

## 48. CLI behavior

Recommended commands:

```text
gf-wordbench project show
gf-wordbench project check
gf-wordbench project check --strict
gf-wordbench project init
gf-wordbench project reset
gf-wordbench project migrate
gf-wordbench project archive
```

### 48.1 `project show`

Displays:

- project ID;
- name;
- language code;
- source root;
- entrypoints;
- checkpoints;
- scenario counts;
- PGF requirement;
- readiness level.

### 48.2 `project check`

Validates:

- schema;
- semantics;
- paths;
- registries;
- required documents;
- contract consistency.

### 48.3 Write commands

`init`, `reset`, and `migrate` are explicit write operations.

Normal `show`, `check`, and validation commands are read-only for project assets.

Exact CLI syntax becomes normative in `CLI_REFERENCE.md`.

---

## 49. GUI behavior

The GUI SHOULD show:

- active project identity;
- source root;
- entrypoints/checkpoints;
- required/optional scenarios;
- validation and release-gate results;
- project-validation problems;
- links to project documents.

The GUI MUST NOT:

- create a second project identity store;
- infer language from state;
- silently change project configuration;
- hide missing required project assets;
- bypass project release requirements;
- mix runs from different project IDs as one history.

---

## 50. CI behavior

A project CI job SHOULD:

1. load canonical `project.toml`;
2. run project schema validation;
3. run project contract checks;
4. reject unresolved placeholders;
5. verify required files;
6. run configured validation mode;
7. preserve run evidence.

### 50.1 Clean environment

CI should not depend on developer-local GUI state.

### 50.2 Explicit toolchain

GF executable and RGL root should be supplied explicitly.

### 50.3 Release CI

Release CI must use the same project model and release requirements as local release mode.

---

## 51. Testing strategy

Recommended tests:

```text
tests/project/test_project_loader.py
tests/project/test_project_model.py
tests/project/test_project_validation.py
tests/project/test_project_lifecycle.py
tests/project/test_project_reset.py
tests/project/test_project_migration.py
tests/contracts/test_project_contract.py
tests/schemas/test_project_schema.py
tests/integration/test_project_fixture.py
```

### 51.1 Schema tests

- canonical project;
- missing schema ID;
- wrong schema ID;
- unsupported major version;
- missing required table;
- wrong field type;
- unknown optional field;
- deterministic list order.

### 51.2 Identity tests

- valid project ID;
- invalid path characters;
- Unicode display name;
- language code;
- project-ID migration;
- stale identity detection.

### 51.3 Source tests

- valid relative source root;
- missing source root;
- source root outside project;
- invalid glob;
- invalid regex;
- required module excluded accidentally.

### 51.4 Module tests

- one entrypoint;
- multiple entrypoints;
- duplicate entrypoint;
- missing entrypoint;
- ordered checkpoints;
- duplicate checkpoint;
- checkpoint dependency order review.

### 51.5 Scenario tests

- unique required scenarios;
- required/optional overlap;
- missing script;
- missing gold;
- stale scenario suffix;
- deterministic order.

### 51.6 Lifecycle tests

- template initialization;
- baseline state;
- reset clears active identity;
- archive preserves assets;
- migration warning;
- unsupported schema requires migration.

### 51.7 Boundary tests

- project facts do not come from GUI state;
- framework defaults contain no active-language identity;
- normal validation does not rewrite project files;
- historical runs are not rewritten after migration.

### 51.8 Integration fixture

A language-neutral fixture should prove:

- load project;
- resolve sources;
- resolve GF path;
- compile checkpoint;
- compile entrypoint;
- run scenario;
- compare gold;
- build PGF;
- write reports and manifest.

---

## 52. Project-model checker

Canonical command:

```text
gf-wordbench project check
```

It should detect at least:

```text
invalid schema
missing source root
missing entrypoint
duplicate checkpoint
duplicate scenario
required/optional overlap
missing scenario
missing gold
missing project document
unresolved placeholder
stale language identifier
broken scenario-to-entrypoint mapping
stale PGF name
contract/document mismatch
```

Strict mode may additionally check:

```text
unexplained files
undocumented public module ownership
dependency-map mismatch
undocumented temporary or fallback behavior
project-relative path portability
research evidence references
```

---

## 53. Change classification

### 53.1 Internal source change

No project-model change when:

- private source changes;
- project identity and public contracts remain stable;
- existing validation remains applicable.

### 53.2 Compatible project extension

Examples:

- add optional scenario;
- add checkpoint;
- add non-breaking project document;
- add optional module not in release surface.

Required:

- configuration/documentation update;
- tests;
- contract update where consumed;
- schema minor change only if persisted structure changes.

### 53.3 Breaking project change

Examples:

- change project ID;
- move source root;
- rename entrypoint;
- change module suffix;
- change scenario ID;
- change gold mapping;
- change expected PGF;
- change lincat shape;
- redefine release scope.

Required:

1. migration plan;
2. provider/consumer review;
3. configuration update;
4. source update;
5. scenario/gold update;
6. documentation update;
7. decision record;
8. contract update;
9. full validation;
10. historical compatibility policy.

---

## 54. Drift indicators

Project-model drift is likely when:

- `project.toml` names a missing module;
- project docs name a different language;
- GUI state selects another source root;
- a required scenario is absent;
- a gold has no registered scenario;
- a scenario loads an undocumented entrypoint;
- an entrypoint exists but is absent from architecture docs;
- the dependency map contradicts imports;
- temporary or fallback behavior is undocumented;
- the expected PGF name differs across files;
- old-language identifiers remain after reset;
- project paths are absolute and machine-specific;
- entrypoint/checkpoint order changes during loading;
- required release constraints are bypassed by UI selection;
- framework code contains the active language path;
- a normal run rewrites project assets;
- historical runs are reclassified under a new project ID.

Every drift indicator requires restoring the existing contract or performing a coordinated project migration.

---

## 55. Required project review checklist

```text
[ ] One active project is defined
[ ] project.toml schema is valid
[ ] Project ID is stable
[ ] Language name/code are current
[ ] Source root is portable and correct
[ ] Selection rules include required modules
[ ] GF path parts are ordered and valid
[ ] Entrypoints exist
[ ] Checkpoints exist and are ordered
[ ] Required scenario IDs are unique
[ ] Optional scenario IDs are unique
[ ] Required/optional scenarios do not overlap
[ ] Required scenario scripts exist
[ ] Required gold files exist
[ ] Scenario entrypoints are documented
[ ] Project interfile contracts are current
[ ] Architecture matches source layout
[ ] Dependency map matches imports
[ ] Category/lincat contracts match consumers
[ ] Known issues have release impact
[ ] Significant changes have decision records
[ ] Release criteria are explicit
[ ] PGF requirement is explicit
[ ] Required project docs exist
[ ] No unresolved template placeholders remain
[ ] No stale previous-language identity remains
[ ] Normal validation is read-only for project assets
[ ] Project can be relocated with environment reconfiguration only
```

---

## 56. Enforcement rule

A GF Wordbench project is one portable, active language definition—not a collection of loosely related paths and files.

Its identity, sources, entrypoints, checkpoints, scenarios, golds, documentation, and release requirements must remain coherent.

> The project is valid only when `project.toml`, the source tree, validation assets, project documentation, and public interfile contracts describe the same active language project.

A project-level change is complete only when all affected assets are updated, validated, and reviewable as one coordinated change.
