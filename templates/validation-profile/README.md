# GF Wordbench Project Template

**Document ID:** `GF-WB-TEMPLATE-PROJECT-README`  
**Document role:** Normative template guide  
**Decision status:** Accepted template contract  
**Implementation status:** Template available; active-project implementation depends on initialization  
**Verification status:** Requires placeholder, source, contract and validation checks after initialization  
**Template path:** `templates/project/`  
**Destination:** `project/`  
**Template owner:** GF Wordbench maintainers  
**Project owner after initialization:** `<PROJECT_OWNER>`  
**Template version:** `1.0.0`  
**Last reviewed:** `<YYYY-MM-DD>`

---

## 1. Purpose

This directory is the canonical starting point for one active GF project.

It provides a language-neutral structure for:

- project identity;
- GF source selection;
- module entrypoints and checkpoints;
- project architecture documentation;
- interfile contracts;
- validation scenarios;
- reviewed gold output;
- scenario input fixtures;
- status and known-issue tracking;
- release criteria.

The template is intentionally incomplete.

It contains placeholders that must be replaced when creating an active project.

The central rule is:

> Copy or render this template into `project/`, replace every required placeholder, remove non-applicable examples, and validate the complete project before treating it as active.

---

## 2. Template versus active project

The two directories have different roles.

| Directory | Role | Placeholder policy | Runtime use |
|---|---|---|---|
| `templates/project/` | Generic source for new projects | Placeholders required where project facts are unknown | Never treated as the active project |
| `project/` | One initialized active GF project | Unresolved required placeholders prohibited | Read by GF Wordbench |

The template may be updated by framework maintainers.

Template updates MUST NOT overwrite an initialized active project automatically.

An active project may selectively adopt later template improvements through an explicit reviewed migration.

---

## 3. Core invariants

The project template MUST remain:

```text
language-neutral
project-neutral
path-neutral
machine-neutral
free of active run history
free of local tool paths
free of copied gold from another language
safe to copy
complete enough to initialize
```

The template MUST NOT contain:

- the active project's language name;
- the active project's language code;
- an active module suffix;
- another project's module names;
- another project's source path;
- a local `gf.exe` path;
- a local RGL path;
- an output-root path;
- a run ID;
- generated `.gfo` or `.pgf` files;
- generated reports;
- accepted project-specific warnings;
- completed project-specific decisions.

Intentional placeholders are not drift.

Unintended concrete project identity is drift.

---

# 4. Directory structure

Canonical template layout:

```text
templates/project/
├── README.md
├── project.toml
├── docs/
│   ├── 00_PROJECT_START_HERE.md
│   ├── INTERFILE_CONTRACT_LOCK.md
│   ├── LANGUAGE_ARCHITECTURE.md
│   ├── MODULE_DEPENDENCY_MAP.md
│   ├── CATEGORY_AND_LINCAT_CONTRACT.md
│   ├── MORPHOLOGY_SPEC.md
│   ├── SYNTAX_AND_CONSTRUCTOR_RULES.md
│   ├── VALIDATION_SPEC.md
│   ├── TEST_COVERAGE_MATRIX.md
│   ├── STATUS_LEDGER.md
│   ├── DECISION_LOG.md
│   ├── KNOWN_ISSUES.md
│   └── RELEASE_CRITERIA.md
└── validation/
    ├── scenarios/
    ├── gold/
    └── inputs/
```

The initialized project may also contain its GF source tree.

Example shape:

```text
project/
├── README.md
├── project.toml
├── docs/
├── validation/
└── lib/
    └── src/
        └── <LANGUAGE_DIRECTORY>/
            ├── <CHECKPOINT_MODULE>.gf
            └── <ENTRYPOINT_MODULE>.gf
```

The exact source location is declared in:

```text
project/project.toml
```

---

# 5. Initialization methods

A new project may be created by:

1. a future `gf-wordbench project init` command;
2. a reviewed copy of `templates/project/`;
3. another explicit initializer that preserves this contract.

Manual copying is allowed.

A partial copy is not considered initialization.

---

## 5.1 Destination safety

Before initialization, inspect:

```text
project/
```

Do not overwrite an existing initialized project.

If `project/` already contains project-owned files:

- stop;
- identify the existing project;
- preserve it;
- choose a new repository copy or perform an explicit migration.

Initialization MUST NOT silently merge two GF projects.

---

## 5.2 Copy operation

Conceptual operation:

```text
templates/project/
    → project/
```

The copy must include:

```text
README.md
project.toml
docs/
validation/scenarios/
validation/gold/
validation/inputs/
```

Empty validation directories must be preserved.

When the version-control system does not preserve empty directories, include a documented placeholder file such as:

```text
.gitkeep
```

Remove directory placeholder files when real assets are added if project policy requires it.

---

# 6. Required project decisions

Before replacing placeholders, determine:

| Decision | Required output |
|---|---|
| Project owner | Maintainer role or team |
| Language name | Human-readable name |
| Language code | Stable project language identifier |
| Project ID | Stable path-safe identifier |
| GF module suffix | Consistent suffix used by project modules |
| Source directory | Project-relative source root |
| Abstract providers | Upstream abstract syntax or project abstract modules |
| Concrete entrypoint | Primary grammar entrypoint |
| API entrypoint | Syntax/application entrypoint or explicit absence |
| Checkpoints | Ordered dependency-oriented compile targets |
| Required scenarios | Release-gating scenario IDs |
| Optional scenarios | Non-gating or conditional scenario IDs |
| Expected PGF | Stable release artifact identity |
| GF path parts | Ordered project and RGL path components |
| Minimum GF version | Empty or documented minimum |
| Release PGF policy | `true` or justified `false` |

Do not infer these values from another GF project.

---

# 7. Placeholder policy

## 7.1 Intentional placeholders

Template files may use placeholders such as:

```text
<PROJECT_ID>
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<LANGUAGE_DIRECTORY>
<SOURCE_DIR>
<ABSTRACT_ENTRYPOINT>
<CONCRETE_ENTRYPOINT>
<SYNTAX_ENTRYPOINT>
<LANGUAGE_ENTRYPOINT>
<API_ENTRYPOINT_OR_NONE>
<CHECKPOINT_MODULE>
<ENTRYPOINT_MODULE>
<EXPECTED_PGF>
<SCENARIO_ID>
<YYYY-MM-DD>
```

Each placeholder must communicate one concrete replacement decision.

Avoid vague placeholders such as:

```text
<THING>
<DATA>
<OTHER>
```

---

## 7.2 Active-project prohibition

After initialization, the active project MUST NOT contain unresolved required placeholders.

The project checker should detect patterns including:

```text
<...>
REPLACE_ME
TODO_PROJECT
LANGUAGE_NAME
PROJECT_ID
GF_SUFFIX
```

A placeholder may remain only when:

- the containing section is explicitly an example;
- the example is clearly marked non-executable;
- the placeholder cannot be confused with an active value.

---

## 7.3 Placeholder replacement is not enough

Replacing text mechanically does not complete initialization.

The initializer must also:

- remove non-applicable contracts;
- add missing project-specific contracts;
- verify actual module paths;
- verify actual import relationships;
- define scenario assertions;
- define gold policy;
- define release criteria;
- execute baseline validation.

---

# 8. `project.toml`

The template project file follows:

```text
schema_id = gf-wordbench.project
schema_version = 1.0
```

Canonical template shape:

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "<PROJECT_ID>"
name = "<LANGUAGE_NAME>"
language_code = "<LANGUAGE_CODE>"
root = "."

[sources]
directory = "<SOURCE_DIR>"
glob = "*.gf"
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "( - Copy\\.gf$|\\.bak\\.gf$|\\.tmp\\.gf$|\\.disabled\\.gf$)"

[gf]
path_parts = [
  "<PROJECT_RELATIVE_OR_RGL_PATH>",
]
minimum_version = ""

[modules]
entrypoints = [
  "<ENTRYPOINT_MODULE>.gf",
]
checkpoints = []

[validation]
required_scenarios = []
optional_scenarios = []
release_requires_pgf = true
```

Detailed field semantics are defined in:

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
```

---

## 8.1 Values that belong in `project.toml`

Store stable project facts:

```text
project identity
source location
source selection policy
GF path parts
entrypoints
checkpoints
required scenarios
optional scenarios
release PGF requirement
```

---

## 8.2 Values that do not belong in `project.toml`

Do not store:

```text
absolute GF executable path
absolute RGL root
output root
timeout
selected runtime mode
quick target
GUI window state
recent run path
last result
credentials
secrets
```

These are machine-specific, run-specific, application-state, or secret values.

---

## 8.3 Path rules

Canonical project-owned paths:

- are relative;
- use `/`;
- resolve from the project root;
- do not escape the project;
- do not contain drive letters;
- do not depend on shell variable expansion;
- preserve actual case.

Invalid canonical examples:

```text
C:\local\grammar
..\another-project
%USERPROFILE%\gf
${RGL_ROOT}
```

---

## 8.4 Source filters

The template source filter is only a generic starting point.

Review it for:

- Unicode module filenames;
- project naming conventions;
- backup-file conventions;
- disabled-file conventions;
- nested source directories.

Required entrypoints and checkpoints must not be excluded.

Exclude matching takes precedence over include matching.

---

# 9. GF source tree

The template does not prescribe one universal GF module hierarchy.

The initialized project must document its actual architecture.

A common direction is:

```text
resources and morphology
    → category implementations
    → syntax modules
    → structural and extension modules
    → grammar and API entrypoints
    → PGF
```

Lower layers MUST NOT import higher-level entrypoints merely for convenience.

Circular imports are prohibited.

---

## 9.1 Module filenames

Project GF filenames should be coherent with declared module names.

Common convention:

```text
<ROLE><GF_SUFFIX>.gf
```

Examples as patterns only:

```text
Morpho<GF_SUFFIX>.gf
Noun<GF_SUFFIX>.gf
Verb<GF_SUFFIX>.gf
Grammar<GF_SUFFIX>.gf
Syntax<GF_SUFFIX>.gf
```

These are naming patterns, not required module inventories.

The active project must use its actual source architecture.

---

## 9.2 Checkpoints

Checkpoints are ordered modules whose successful compilation proves development layers.

Choose checkpoints that:

- reveal low-level failures before entrypoint failures;
- follow dependency order;
- cover critical provider layers;
- remain stable enough for repeated validation;
- are not redundant aliases of the same module.

Checkpoint mode must not silently truncate the configured list.

---

## 9.3 Entrypoints

Entrypoints are top-level modules used for:

```text
final compilation
GF shell loading
scenario execution
PGF construction
application/API use
```

Every initialized release-oriented project needs at least one entrypoint.

Entrypoints must:

- exist;
- be unique;
- use source-root-relative paths;
- compile from a clean artifact directory;
- be documented in the dependency map;
- be exercised by required scenarios where applicable.

---

# 10. Documentation initialization order

Complete project documentation in this order:

```text
1. 00_PROJECT_START_HERE.md
2. project.toml
3. LANGUAGE_ARCHITECTURE.md
4. MODULE_DEPENDENCY_MAP.md
5. CATEGORY_AND_LINCAT_CONTRACT.md
6. MORPHOLOGY_SPEC.md
7. SYNTAX_AND_CONSTRUCTOR_RULES.md
8. INTERFILE_CONTRACT_LOCK.md
9. VALIDATION_SPEC.md
10. TEST_COVERAGE_MATRIX.md
11. STATUS_LEDGER.md
12. KNOWN_ISSUES.md
13. DECISION_LOG.md
14. RELEASE_CRITERIA.md
```

This order reduces circular documentation assumptions.

---

# 11. `00_PROJECT_START_HERE.md`

This is the entry document for project maintainers.

It should state:

- project purpose;
- current development state;
- primary entrypoints;
- source root;
- first documents to read;
- first validation commands;
- location of known issues;
- location of release criteria.

It must not claim that the template is already a completed project.

---

# 12. `LANGUAGE_ARCHITECTURE.md`

Document:

```text
major source layers
module ownership
expected dependency directions
abstract/concrete relationships
entrypoint roles
extension strategy
structural module strategy
lexicon strategy
PGF surface
```

Every major source layer must have one authoritative owner.

Historical architecture must not be presented as the current target.

---

# 13. `MODULE_DEPENDENCY_MAP.md`

Record:

- direct GF imports;
- provider-to-consumer relationships;
- checkpoint dependency chains;
- entrypoint closure;
- external RGL dependencies;
- scenario-to-entrypoint relationships.

The map must match source reality.

It is not a speculative desired architecture unless explicitly marked as such.

---

# 14. `CATEGORY_AND_LINCAT_CONTRACT.md`

Document every cross-module dependency on:

```text
lincat fields
record shapes
table shapes
parameter values
agreement dimensions
shared constructors
coercions
```

A consumer must not depend on an undocumented field.

Changing a consumed lincat field is a coordinated contract change.

---

# 15. `MORPHOLOGY_SPEC.md`

Document:

```text
nominal inflection
verbal inflection
adjectival inflection
agreement parameters
case or equivalent dimensions
definiteness
irregular forms
normalization
paradigm ownership
fallback behavior
```

Incomplete or fallback paradigms must be distinguishable from stable paradigms.

---

# 16. `SYNTAX_AND_CONSTRUCTOR_RULES.md`

Document:

```text
constructor ownership
argument order
word order
agreement propagation
complement structure
polarity
coordination
relative constructions
question constructions
extension behavior
API expectations
```

Do not duplicate morphology rules here unless syntax depends on a specific morphological contract.

Cross-reference the morphology specification.

---

# 17. `INTERFILE_CONTRACT_LOCK.md`

This file prevents drift across project-owned boundaries.

For each active contract, define:

```text
stable contract ID
status
provider
consumers
provided element
request
response
invariants
allowed variation
breaking changes
validation evidence
documentation owner
last reviewed
```

Allowed lifecycle statuses:

```text
active
experimental
deprecated
blocked
retired
```

Template placeholders must be replaced or the non-applicable contract removed.

Every locked contract needs at least one proof:

- direct compile;
- consumer compile;
- entrypoint compile;
- scenario;
- gold comparison;
- generated artifact;
- documented manual review when automation is impossible.

---

# 18. `VALIDATION_SPEC.md`

Define the project-specific meaning of success.

Document:

```text
validation modes used by the project
checkpoint criteria
release criteria
scenario purposes
scenario inputs
scenario assertions
allowed ambiguity
missing-linearization threshold
gold policy
PGF policy
manual criteria
failure severity
```

The validation specification owns linguistic expectations.

Framework documentation owns execution mechanics.

---

# 19. `TEST_COVERAGE_MATRIX.md`

Map every important requirement to retained evidence.

Include:

```text
configuration checks
module compile checks
entrypoint load checks
linguistic capability checks
scenario assertions
gold comparisons
artifact checks
manual reviews
release gates
```

Do not store transient run statuses in the matrix.

The latest execution result belongs in run artifacts and the status ledger.

---

# 20. `STATUS_LEDGER.md`

Register temporary and incomplete states.

Examples:

```text
temporary
fallback
warning
blocked
disabled
experimental
retired
```

Every open entry should include:

- stable ID;
- affected file or contract;
- current state;
- impact;
- owner;
- next action;
- exit condition;
- release-blocking decision;
- last reviewed date.

Resolved entries retain a resolution record.

---

# 21. `DECISION_LOG.md`

Record decisions that affect:

```text
project identity
module ownership
public GF surface
lincat shape
inheritance and overrides
entrypoints
scenario IDs
gold normalization
expected PGF
accepted release exceptions
toolchain compatibility
```

A breaking contract change requires a decision entry.

---

# 22. `KNOWN_ISSUES.md`

Track user-visible or release-significant issues.

Every issue should state:

- stable ID;
- summary;
- affected capability;
- current evidence;
- workaround, if any;
- release impact;
- owner;
- target resolution;
- relationship to the status ledger.

Do not use known issues to hide undocumented failures.

---

# 23. `RELEASE_CRITERIA.md`

Define the project release gates.

At minimum review:

```text
strict configuration validity
checkpoint compilation
entrypoint compilation
required scenario success
required gold success
PGF construction when configured
artifact manifest completeness
status-ledger blockers
known issues
manual linguistic reviews
clean source and toolchain identity
```

A project cannot declare release readiness while required criteria remain unproven.

---

# 24. Scenario directory

Canonical location:

```text
project/validation/scenarios/
```

Scenario files use:

```text
<scenario-id>.gfs
```

Each scenario should:

- have one unique ID;
- be registered in `project.toml`;
- load a configured entrypoint;
- use supported GF commands;
- use stable output markers;
- define finite execution;
- terminate explicitly where required;
- keep data separate from shell fragments;
- preserve reproducibility;
- state its assertions in `VALIDATION_SPEC.md`.

Scenario files remain external project assets.

GF Wordbench executes GF; it does not reinterpret GF command syntax.

---

## 24.1 Marker contract

Preferred conceptual markers:

```text
GF_WORDBENCH_BEGIN <SECTION_ID>
GF_WORDBENCH_END <SECTION_ID>
```

The exact syntax is defined by:

```text
docs/scenarios/SCENARIO_FORMAT.md
```

Marker identifiers must be unique within a scenario.

A missing required end marker is a scenario failure.

Zero process exit is not sufficient when markers or assertions fail.

---

## 24.2 Scenario ordering

Scenario order is declared by:

```text
validation.required_scenarios
validation.optional_scenarios
```

in `project.toml`.

Do not infer order from filesystem enumeration.

Required and optional scenarios remain distinct.

---

## 24.3 Required scenarios

A required scenario:

- must exist;
- must be registered;
- must be executable;
- must produce complete evidence;
- must pass its assertions;
- must pass required gold comparison;
- blocks the relevant gate when absent, failed, errored, or unjustifiably skipped.

---

## 24.4 Optional scenarios

An optional scenario:

- remains registered;
- remains visible;
- still requires deterministic execution and evidence;
- may warn or gate according to explicit release policy;
- is not silently treated as success when skipped.

---

# 25. Gold directory

Canonical location:

```text
project/validation/gold/
```

Gold files use:

```text
<scenario-id>.gold
```

A gold file is reviewed expected normalized output.

It is source, not generated run state.

Gold rules:

- compare after normalization;
- preserve raw output separately;
- retain linguistically meaningful content;
- normalize only documented unstable noise;
- record normalization version;
- never rewrite during normal validation;
- require explicit update operation;
- require human review;
- associate every update with an intentional source or specification change.

A missing required gold file is a failure.

---

# 26. Input directory

Canonical location:

```text
project/validation/inputs/
```

Use it for:

```text
UTF-8 phrases
tree lists
lexical fixtures
morphology inputs
scenario-specific configuration
bounded generation seeds or projections
```

Input files must:

- be versioned with the project;
- have stable paths;
- be referenced by registered scenarios;
- avoid secrets;
- avoid machine-specific absolute paths;
- use documented encoding;
- remain bounded for automated validation.

Unused input files should be removed or documented.

---

# 27. Baseline scenarios

The template does not force one scenario inventory.

A release-oriented project will commonly consider:

| Scenario | Typical purpose |
|---|---|
| `load` | Import or load the primary grammar |
| `missing` | Inspect missing linearizations |
| `linearize` | Validate representative trees |
| `parse` | Validate representative phrases |
| `generation` | Exercise bounded generation |
| `morphology` | Validate inflection or analysis |

These are recommended IDs, not mandatory names.

When different IDs are used:

- register them in `project.toml`;
- document their purposes;
- provide corresponding scripts;
- define gold or assertion policy;
- update coverage and release documents.

---

# 28. Initial validation sequence

After filling project files, run validation in increasing scope.

Conceptual sequence:

```text
project check
    → one quick source target
    → checkpoint mode
    → required load scenario
    → required behavioral scenarios
    → diagnostic mode
    → release mode
```

Recommended commands are defined by:

```text
docs/usage/CLI_REFERENCE.md
```

Do not preserve commands in this README that disagree with the implemented parser.

---

## 28.1 Project check

Preferred command:

```text
gf-wordbench project check --strict
```

Expected checks:

```text
schema identity
required fields
placeholder absence
source-root containment
regex validity
entrypoint existence
checkpoint existence
scenario registry
gold mapping
required documentation
identifier consistency
```

---

## 28.2 Contract check

Preferred command:

```text
gf-wordbench project contracts check --strict
```

Expected checks:

```text
module existence
module-name/file-name consistency
dependency-map consistency
scenario-to-entrypoint mapping
scenario-to-gold mapping
duplicate helper ownership
temporary status registration
release artifact identity
```

---

## 28.3 Baseline run

The first complete baseline should record:

```text
GF Wordbench version
GF version
RGL release or commit
project configuration hash
source commit
selected modules
scenario results
artifact manifest
run ID
known limitations
```

Record the baseline run ID in project documentation or release evidence.

Do not put the run ID into the template.

---

# 29. Initialization checklist

```text
[ ] Destination project directory is safe
[ ] Complete template copied or rendered
[ ] Project owner assigned
[ ] Project ID selected
[ ] Language name selected
[ ] Language code selected
[ ] GF module suffix selected
[ ] Source root created
[ ] Source filters reviewed
[ ] GF path parts defined
[ ] Entrypoints registered
[ ] Checkpoints registered in dependency order
[ ] Required scenarios registered
[ ] Optional scenarios registered
[ ] PGF release policy selected
[ ] Every required placeholder replaced
[ ] Non-applicable example contracts removed
[ ] Language architecture documented
[ ] Dependency map matches source
[ ] Lincat contracts documented
[ ] Morphology specification completed
[ ] Syntax rules completed
[ ] Interfile contracts registered
[ ] Validation specification completed
[ ] Coverage matrix completed
[ ] Temporary states entered in ledger
[ ] Known issues recorded
[ ] Decisions recorded
[ ] Release criteria completed
[ ] Scenario scripts created
[ ] Input fixtures created
[ ] Gold policy defined
[ ] Required gold files created and reviewed
[ ] Strict project check passes
[ ] Contract check passes
[ ] Quick validation passes for a valid target
[ ] Checkpoint validation executed
[ ] Required scenarios executed
[ ] Diagnostic baseline executed
[ ] Release baseline executed when project is ready
[ ] Baseline evidence retained
```

---

# 30. Initialization is complete when

The active project is initialized only when:

```text
project.toml is valid
project identity is real
source root exists
entrypoints exist
checkpoints are deliberate
required scenarios exist
documentation reflects source reality
contracts have evidence
temporary states are explicit
gold policy is explicit
release criteria are explicit
no unresolved required placeholder remains
```

A structurally valid project may still be incomplete or non-release-ready.

Initialization and release readiness are separate states.

---

# 31. Change discipline after initialization

A project is a network of contracts.

When a provider changes, review:

```text
direct consumers
downstream entrypoints
project configuration
scenarios
input files
gold files
dependency map
coverage matrix
status ledger
known issues
decision log
release criteria
```

No cross-file contract may be changed through an isolated edit.

Internal refactoring is allowed when every externally visible promise remains compatible.

---

# 32. Template maintenance rules

Framework maintainers may update the template to:

- add a compatible optional document;
- clarify initialization;
- add generic contract examples;
- add a new optional scenario pattern;
- align with a new compatible project schema;
- remove obsolete framework terminology.

A template change must remain language-neutral.

---

## 32.1 Compatible template update

Examples:

- clarify placeholder instructions;
- add an optional checklist;
- add a generic optional contract;
- add an empty validation subdirectory;
- add cross-references.

Review:

```text
initializer
template tests
project schema
template lock
documentation
```

---

## 32.2 Breaking template update

Examples:

- change required project schema;
- rename required documents;
- change path bases;
- change scenario-format requirements;
- change required contract fields;
- change initialized directory layout.

Requirements:

```text
schema or contract version review
migration documentation
initializer update
template tests
active-project adoption guidance
release notes
```

Existing projects are not rewritten automatically.

---

# 33. Template validation

The framework test suite should verify:

```text
all required template files exist
project.toml parses as a template
only approved placeholders appear
no project-specific identifier appears
no absolute machine path appears
documentation paths are internally coherent
required validation directories exist
template lock remains normative
active project and template schemas agree
initialization replaces required placeholders
initialized output passes strict project check
```

A template is not validated by compiling its placeholder modules.

The template becomes executable only after initialization.

---

# 34. Security

Template and initialized project assets may influence external GF execution.

Rules:

- review `.gfs` scripts before execution;
- do not include secrets in project files;
- do not expand arbitrary shell variables;
- do not execute scenario input as shell fragments;
- keep paths project-relative where required;
- preserve raw process evidence;
- use finite scenario timeouts;
- prohibit unbounded generation;
- do not trust copied gold without review;
- do not use another project's scripts blindly.

---

# 35. Common initialization errors

## 35.1 Copying only `project.toml`

Result:

- missing documentation;
- missing scenarios;
- missing gold/input structure;
- incomplete project contract.

Fix:

```text
copy or render the complete template
```

---

## 35.2 Leaving placeholders

Result:

```text
configuration or contract-check failure
```

Fix:

- replace required placeholders;
- remove non-applicable example sections;
- rerun strict checks.

---

## 35.3 Copying another language's identity

Symptoms:

- wrong module suffix;
- old source directory;
- stale scenario imports;
- incorrect gold;
- wrong language code.

Fix:

- return to the generic template;
- initialize identity deliberately;
- scan all active project files for stale identifiers.

---

## 35.4 Storing local GF paths in `project.toml`

Result:

- non-portable project;
- machine-specific drift.

Fix:

```text
move tool paths to environment or application configuration
```

---

## 35.5 Treating empty scenario lists as release-ready

An empty scenario list may be valid during bootstrap.

It does not prove release readiness.

Define required scenarios before release.

---

## 35.6 Generating gold automatically during normal validation

This destroys the independence of expected output.

Fix:

- restore reviewed gold;
- use explicit gold-update workflow;
- preserve the diff;
- record the reason.

---

## 35.7 Keeping every example contract

Template examples may not apply.

Delete or rewrite non-applicable entries.

Do not present a fictional provider/consumer relationship as active.

---

## 35.8 Marking incomplete behavior as active

Use:

```text
experimental
blocked
deprecated
```

or ledger states such as:

```text
temporary
fallback
warning
disabled
```

Do not label unproven behavior as active or stable.

---

# 36. Anti-drift indicators

Template drift exists when:

- a real language name appears outside a clearly generic example;
- a real language code becomes a default;
- a concrete module suffix is embedded;
- an active project source path appears;
- local GF, RGL, or output paths appear;
- generated runs appear under the template;
- scenario IDs are presented as mandatory when they are only examples;
- template gold contains another language's reviewed output;
- template status ledger contains another project's issues;
- template decision log contains completed project decisions;
- active project and template use incompatible schemas without migration;
- an initializer copies only part of the template;
- template updates silently rewrite `project/`;
- placeholder policy is not testable;
- required documents are missing.

Any detected template drift must be corrected before the template is used for a new project.

---

# 37. Cross-references

| Topic | Document |
|---|---|
| Project schema | `docs/configuration/PROJECT_TOML_REFERENCE.md` |
| Project model | `docs/projects/PROJECT_MODEL.md` |
| Project creation | `docs/projects/CREATING_A_LANGUAGE_PROJECT.md` |
| Project cloning | `docs/projects/CLONING_AN_EXISTING_PROJECT.md` |
| Project validation | `docs/projects/VALIDATING_A_PROJECT.md` |
| Scenario format | `docs/scenarios/SCENARIO_FORMAT.md` |
| Gold updates | `docs/scenarios/UPDATING_GOLD_FILES.md` |
| Validation modes | `docs/validation/VALIDATION_MODES.md` |
| File selection | `docs/validation/FILE_SELECTION.md` |
| Release gates | `docs/validation/RELEASE_GATES.md` |
| Framework dependency contracts | `docs/architecture/DEPENDENCY_RULES.md` |
| Persisted schemas | `docs/reference/SCHEMA_INDEX.md` |
| Template project lock | `templates/project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Active project start | `project/docs/00_PROJECT_START_HERE__PROJECT_DOCS.md` |

---

# 38. Final rule

> The template is generic source material, not an active GF project.

It becomes an active project only after identity, source architecture, contracts, scenarios, gold policy, coverage, status, and release criteria have been completed and validated.

Copy deliberately. Replace completely. Validate before use.
