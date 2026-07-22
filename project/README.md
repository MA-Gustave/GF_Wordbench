# GF Wordbench — Active Language Project

**Status:** Active project entry point  
**Applies to:** The single active GF language project managed by this GF Wordbench copy  
**Project identity:** Defined by `project/project.toml`  
**Project contracts:** Defined by `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Framework documentation:** `../docs/00_START_HERE.md`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This directory contains the project-owned configuration, validation assets, documentation, decisions, status records, and release policy for the active Grammatical Framework language project.

One GF Wordbench copy represents one active language project.

The authoritative project identity is defined in:

```text
project/project.toml
```

This README does not duplicate the project name, language code, module suffix, source root, entrypoints, checkpoints, or scenario inventory.

Those values must be read from the project configuration and the project contract documents.

---

## 2. Start here

For a new checkout or restored workspace:

1. open `project/project.toml`;
2. verify the project identity and source paths;
3. read `project/docs/00_PROJECT_START_HERE.md`;
4. read `project/docs/INTERFILE_CONTRACT_LOCK.md`;
5. verify the local GF executable and RGL root;
6. run the configuration checker;
7. run a focused `quick` validation;
8. run the relevant checkpoint;
9. run `release` only after all project requirements are complete.

Framework-level installation instructions are in:

```text
docs/usage/QUICK_START.md
docs/development/DEVELOPMENT_SETUP.md
```

---

## 3. Project boundary

This directory owns language-project policy and evidence definitions.

It owns:

```text
project configuration
language architecture
module dependency documentation
category and lincat contracts
morphology and syntax specifications
validation scenarios
scenario inputs
reviewed gold output
checkpoint definitions
release criteria
status and known-issue records
project decisions
research evidence
```

It does not own:

```text
Python framework orchestration
GUI implementation
CLI implementation
process execution internals
generic result models
generic report writers
generic schema infrastructure
external GF implementation
RGL implementation
```

Framework behavior belongs under:

```text
app/
docs/
tests/
templates/
```

Language-specific policy must remain under the active project and its GF source tree.

---

## 4. Authoritative project sources

The active project has one authoritative identity.

Source of truth:

```text
project/project.toml
```

It defines or resolves:

```text
project ID
display name
language identity
module suffix
source root
source selection
GF path components
entrypoints
checkpoints
required scenarios
optional scenarios
release targets
PGF requirements
```

The project identity must not be inferred from:

- GUI state;
- application state;
- old run directories;
- report filenames;
- historical language defaults;
- source filename guessing.

Changing the project ID, language identifier, module suffix, or source-root semantics is a project migration, not an ordinary edit.

---

## 5. Directory structure

Canonical active-project structure:

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
│   ├── STATUS_LEDGER.md
│   ├── DECISION_LOG.md
│   ├── KNOWN_ISSUES.md
│   ├── RELEASE_CRITERIA.md
│   └── RESEARCH_EVIDENCE.md
└── validation/
    ├── README.md
    ├── scenarios/
    │   └── README.md
    ├── inputs/
    │   └── README.md
    └── gold/
        └── README.md
```

The active GF source tree may be inside or outside `project/`.

Its project-relative location is defined by `project.toml`.

---

## 6. Project documentation map

### `00_PROJECT_START_HERE.md`

Operational entry point for maintainers of this language project.

It explains the current project state, immediate validation path, and required reading order.

### `INTERFILE_CONTRACT_LOCK.md`

Normative project boundary contract.

It locks relationships between:

```text
GF provider and consumer modules
project configuration and source tree
scenario and entrypoint
scenario and input
scenario and gold
entrypoint and PGF
documentation and implementation
```

A cross-file change is incomplete until every affected provider, consumer, scenario, gold, configuration entry, and document is updated.

### `LANGUAGE_OVERVIEW.md`

Describes the language resource, intended coverage, project goals, major constraints, and external dependencies.

### `LANGUAGE_ARCHITECTURE.md`

Defines the implemented GF layers and their responsibilities.

It must match the real source tree.

### `MODULE_DEPENDENCY_MAP.md`

Records actual module-import direction, entrypoint chains, checkpoint dependencies, and significant provider-consumer relationships.

### `CATEGORY_AND_LINCAT_CONTRACT.md`

Defines public GF categories, lincats, record fields, parameters, invariants, and consumer expectations.

### `MORPHOLOGY_SPEC.md`

Defines the project’s morphology design, paradigms, inflectional dimensions, irregular behavior, and validation evidence.

### `SYNTAX_AND_CONSTRUCTOR_RULES.md`

Defines public constructor behavior, syntax policy, agreement, ordering, composition rules, and known constraints.

### `VALIDATION_SPEC.md`

Defines what must be proven and which evidence proves it.

It connects:

```text
requirements
→ checkpoints
→ scenarios
→ assertions
→ gold
→ artifacts
→ release gates
```

### `TEST_COVERAGE_MATRIX.md`

Maps project contracts and linguistic features to executable or manual evidence.

### `STATUS_LEDGER.md`

Tracks temporary, fallback, blocked, warning, incomplete, deprecated, and resolved implementation states.

### `DECISION_LOG.md`

Records project-specific architectural and linguistic decisions.

Framework ADRs remain under `docs/decisions/`.

### `KNOWN_ISSUES.md`

Records reproducible defects, limitations, compatibility concerns, accepted risks, and release-blocking issues.

### `RELEASE_CRITERIA.md`

Defines the complete project acceptance contract.

A project is not release-ready until these criteria are proven by a successful `release` run and any required manual review.

### `RESEARCH_EVIDENCE.md`

Records external linguistic, corpus, grammar, or implementation evidence used to justify project decisions.

---

## 7. Project configuration

Canonical file:

```text
project/project.toml
```

Canonical schema identity:

```text
gf-wordbench.project
```

The exact schema is defined by:

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/PERSISTED_SCHEMA_LOCK.md
```

Project configuration must remain portable.

It must not store machine-specific absolute paths for:

```text
gf.exe
RGL root
output root
user profile
temporary directories
```

Local environment paths belong to explicit CLI or GUI input, environment resolution, or disposable application state.

Normal validation reads `project.toml`.

It must not rewrite it.

---

## 8. GF source ownership

The language source tree contains the actual GF modules.

Typical logical layers may include:

```text
abstract syntax
resource modules
morphology
paradigms
category implementations
syntax
structural modules
extensions
lexicon
concrete grammar entrypoints
language or API entrypoints
```

The actual layer names and dependency direction are project-specific.

They must be documented in:

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
```

GF source files are authoritative project assets.

They must never be treated as generated cleanup targets.

---

## 9. Interfile change rule

A project contract change must be coordinated.

When one GF file changes what it provides or requires, review:

```text
provider
direct consumers
downstream entrypoints
interfaces and instances
project configuration
scenarios
inputs
gold
dependency map
status ledger
known issues
release criteria
release evidence
```

Examples of project contract changes:

- renaming a GF module;
- renaming a public function or constructor;
- changing a category;
- changing a `lincat` field;
- changing a parameter type or value;
- changing constructor arity;
- changing public operation ownership;
- changing an entrypoint;
- changing a scenario ID;
- changing gold normalization;
- changing the expected PGF name.

An isolated provider edit is not complete when another file depends on the changed contract.

---

## 10. Validation assets

Validation assets are stored under:

```text
project/validation/
```

The project owns:

```text
scenario scripts
scenario inputs
reviewed gold files
scenario-to-entrypoint relationships
scenario-to-gold relationships
release scenario inventory
```

The framework owns:

```text
scenario execution
timeouts
raw evidence capture
marker parsing
normalization mechanism
assertion evaluation
gold comparison
result models
reports
```

---

## 11. Native `.gfs` scenarios

Canonical path:

```text
project/validation/scenarios/<scenario-id>.gfs
```

Scenarios are native GF shell scripts.

GF Wordbench executes them with the real GF executable.

A scenario may validate:

```text
entrypoint loading
missing linearizations
representative linearization
representative parsing
parse-linearize round trips
morphology
bounded generation
retained operations
source interfaces
PGF behavior
```

Every registered scenario must be:

- project-owned;
- registered;
- single-purpose;
- explicit;
- finite;
- fresh-process safe;
- deterministic when used for regression;
- non-destructive;
- compatible with the supported GF range.

Authoring rules are in:

```text
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
```

---

## 12. Scenario inputs

Canonical root:

```text
project/validation/inputs/
```

Use input files when linguistic examples should be reviewed independently from executable commands.

Examples:

```text
sentences
words
abstract trees
expected rejected inputs
ambiguity cases
regression cases
```

Input files must be:

- UTF-8;
- project-relative;
- registered;
- deterministic in ordering;
- reviewed;
- assigned to a scenario;
- protected from normal cleanup.

A scenario must not read arbitrary user files or paths outside approved roots.

---

## 13. Gold files

Canonical root:

```text
project/validation/gold/
```

A gold file contains reviewed expected normalized output.

Gold is a project source asset.

Normal validation must never modify it.

A gold update requires:

1. an intentional implementation or specification change;
2. inspection of raw output;
3. inspection of normalized output;
4. review of the difference;
5. explicit gold-update action;
6. atomic write;
7. rerun of the proving validation mode.

A missing required gold file is a validation failure.

Current output must never be accepted automatically as the new baseline.

---

## 14. Validation modes

Canonical modes:

```text
quick
checkpoint
release
diagnostic
```

### `quick`

Focused development feedback.

Typical purpose:

```text
validate one changed file, module, or small smoke scenario
```

A quick run is not release evidence.

### `checkpoint`

Proof of one configured subsystem boundary.

Typical purpose:

```text
prove morphology, category layer, syntax layer, extension family, or entrypoint milestone
```

A checkpoint includes its configured prerequisites and applicable required scenarios.

### `diagnostic`

Expanded evidence for difficult or cascading failures.

Typical purpose:

```text
identify direct blockers, downstream failures, ambiguous failures, and raw evidence
```

A diagnostic run is not release evidence.

### `release`

Complete project acceptance.

It includes every required checkpoint, entrypoint, scenario, gold comparison, PGF artifact, release gate, report, and manifest check defined by project policy.

Only a completed successful `release` run may be release-eligible.

Detailed mode rules are in:

```text
docs/validation/VALIDATION_MODES.md
```

---

## 15. Recommended working sequence

Normal development sequence:

```text
edit one coherent contract unit
→ quick validation
→ fix direct failures
→ quick validation again
→ relevant checkpoint
→ review scenario and gold impact
→ update status and documentation
→ release validation when the milestone is complete
```

Failure investigation sequence:

```text
quick or checkpoint failure
→ diagnostic run
→ inspect raw evidence
→ fix root cause
→ rerun original proving mode
```

A diagnostic success does not replace the original checkpoint or release proof.

---

## 16. Initial configuration check

From the repository root, validate project configuration before running the language.

Repository root:

```text
C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench
```

Canonical command family:

```text
gf-wordbench config check
```

The exact local invocation must provide or resolve:

```text
project root
GF executable
RGL root
output root
```

See:

```text
docs/usage/QUICK_START.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/usage/CLI_REFERENCE.md
```

The checker should validate:

```text
project schema
source root
entrypoints
checkpoints
scenario registry
input paths
required gold files
GF executable
GF version policy
RGL root
effective GF path
output-root writability
release configuration
```

Correct configuration errors before interpreting failures as GF-language defects.

---

## 17. First validation

Use a small configured target.

Recommended first proof:

```text
quick validation of a low-level source module
```

Then validate:

```text
a load scenario
the relevant checkpoint
the final entrypoint
```

Do not begin with release mode when the project has no known-good focused baseline.

Detailed commands are maintained in:

```text
docs/usage/QUICK_START.md
docs/usage/CLI_REFERENCE.md
```

---

## 18. Checkpoint policy

Checkpoint IDs are project-owned and configured in `project.toml`.

A checkpoint should define:

```text
stable ID
owned modules
prerequisites
entrypoint reachability
required scenarios
required gold
expected artifacts
completion evidence
```

A checkpoint is not an arbitrary group of files.

A module compiling internally is not enough when the checkpoint contract requires downstream use.

Checkpoint completion must prove the configured subsystem boundary.

---

## 19. Entrypoints

Entrypoints are top-level modules used for:

```text
compilation
GF shell loading
scenario execution
PGF construction
release validation
external consumer use
```

Every configured entrypoint must:

- exist;
- match its declared module name;
- compile from clean current-run artifacts;
- use declared GF paths;
- load in required scenarios;
- produce expected artifacts;
- remain documented.

Renaming an entrypoint is a coordinated project migration.

---

## 20. PGF release artifact

When the project requires a final `.pgf`:

- the release entrypoint set must be documented;
- the PGF build must run during the current release validation;
- the expected artifact must exist;
- the artifact must be nonempty;
- the GF version and build command must be recorded;
- the PGF must be registered in the run manifest;
- the PGF hash must be recorded;
- the artifact must be archived with release evidence.

Individual `.gfo` success is not sufficient proof of PGF release readiness.

---

## 21. Project release readiness

The project is release-ready only when all applicable conditions hold:

```text
project configuration is valid
all required source scans satisfy policy
all required checkpoints pass
all required entrypoints compile
required missing-linearization checks pass
required scenarios complete
required assertions pass
required gold comparisons match
required PGF builds succeed
required artifacts exist
blocking status-ledger entries are resolved
blocking known issues are resolved
release criteria pass
summary schema validates
manifest verifies
release evidence is archived
```

The authoritative checklist is:

```text
project/docs/RELEASE_CRITERIA.md
```

---

## 22. Status ledger

Temporary and incomplete implementation states must be recorded in:

```text
project/docs/STATUS_LEDGER.md
```

Examples:

```text
temporary
fallback
blocked
warning
deprecated
incomplete
resolved
```

Each unresolved entry should include:

```text
stable ID
affected files
status
reason
validation impact
release impact
owner
next action
exit condition
```

A release-blocking status must not be ignored silently.

Resolved entries should retain a resolution record.

---

## 23. Known issues

Known defects and limitations belong in:

```text
project/docs/KNOWN_ISSUES.md
```

Each issue should identify:

```text
issue ID
summary
affected modules
reproduction
expected behavior
actual behavior
severity
workaround
validation evidence
release impact
owner
status
```

A warning appearing repeatedly in validation should either be fixed or registered.

Unregistered recurring failures are project drift.

---

## 24. Project decisions

Project-specific decisions belong in:

```text
project/docs/DECISION_LOG.md
```

Record a decision when changing:

- language architecture;
- category ownership;
- lincat shape;
- constructor behavior;
- public helper ownership;
- morphology representation;
- syntax policy;
- entrypoint identity;
- release artifact identity;
- accepted linguistic variation;
- gold interpretation;
- compatibility policy.

Framework architecture decisions remain under:

```text
docs/decisions/
```

---

## 25. Test coverage

Every release requirement should have evidence.

Evidence may be:

```text
static scan
direct module compile
checkpoint compile
entrypoint compile
native GF scenario
assertion
gold comparison
PGF artifact
manual review with named owner and evidence location
```

Coverage mapping belongs in:

```text
project/docs/TEST_COVERAGE_MATRIX.md
```

A requirement without executable evidence must state:

- why automation is not currently possible;
- who performs the review;
- how the review is performed;
- where evidence is stored;
- whether the criterion blocks release.

---

## 26. Reports and run evidence

Run output is generated outside project source assets.

Canonical run directory:

```text
<output-root>/run_<run-id>/
```

Typical files:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
raw/
details/
artifacts/
```

Use:

```text
summary.json
```

as the primary machine-readable result.

Use:

```text
summary.md
```

for human review.

Use:

```text
AI_READY.md
```

for bounded AI-assisted diagnosis.

Use raw files for exact GF evidence.

Reports do not rerun GF and do not own project truth.

---

## 27. Cleanup and retention

Project assets must not be deleted by normal run cleanup.

Protected project assets include:

```text
project.toml
project docs
scenarios
inputs
gold
GF sources
release criteria
decision records
```

Generated runs follow the retention and archive policy in:

```text
docs/operations/CLEANUP_BACKUP_AND_RECOVERY.md
```

Release runs, protected baselines, and unresolved-failure evidence must not be pruned automatically.

---

## 28. Backup

Before a risky migration, project reset, or major contract change, back up:

```text
project/project.toml
project/docs/
project/validation/
active GF source tree
relevant framework commit
uncommitted project changes
```

A release archive should also preserve:

```text
successful release run
summary.json
manifest.json
raw required evidence
PGF artifacts
project configuration snapshot
GF version
RGL revision
source commit
artifact hashes
```

A backup is not complete until it is verified.

---

## 29. Framework separation

Do not place language-specific behavior in:

```text
app/
tests/ framework fixtures
docs/ framework contracts
templates/ generic defaults
```

unless it is:

- an explicitly marked historical migration fixture;
- a clearly labeled example;
- a neutral reusable framework capability.

Do not make project files depend on:

```text
private Python module paths
GUI widget names
report implementation classes
internal process helpers
framework test fixtures
generated run filenames as configuration
```

The project depends only on documented framework contracts.

---

## 30. Project safety rules

The active project must preserve these invariants:

```text
one authoritative project identity
no unresolved required placeholders
no machine-specific paths in portable project config
no hidden entrypoints
no unregistered required scenarios
no missing required gold
no scenario-dependent external shell commands
no automatic gold updates
no source mutation during normal validation
no release based only on .gfo success
no release with blocking ledger or issue entries
```

---

## 31. Common project errors

### Project identity mismatch

Symptoms:

- module suffix differs between configuration and source;
- scenarios load obsolete module names;
- documents reference a previous language.

Resolution:

- stop validation;
- treat the change as a project migration;
- update configuration, sources, scenarios, gold, and documents together.

### Missing entrypoint

Resolution:

- restore the file or correct project configuration;
- do not guess another entrypoint.

### Required scenario missing

Resolution:

- restore or create the registered `.gfs`;
- verify scenario ID, entrypoint, markers, inputs, assertions, and gold mapping.

### Required gold missing

Resolution:

- restore reviewed gold from version control or backup;
- otherwise use the explicit reviewed gold-update workflow;
- never generate it automatically during release.

### Checkpoint passes but release fails

Inspect:

```text
other checkpoints
release entrypoints
PGF build
release-only scenarios
gold comparisons
known issues
status ledger
manifest
```

### Framework test contains project language name

Move the project-specific case into project validation or isolate it as a clearly named migration fixture.

---

## 32. Project maintenance checklist

Before accepting a project change:

```text
[ ] Project identity unchanged or migration documented
[ ] Provider and consumers reviewed
[ ] Module dependency map updated
[ ] Category and lincat contract reviewed
[ ] Morphology specification reviewed
[ ] Syntax rules reviewed
[ ] Entrypoints reviewed
[ ] Checkpoints reviewed
[ ] Scenarios reviewed
[ ] Inputs reviewed
[ ] Gold reviewed
[ ] Validation specification updated
[ ] Coverage matrix updated
[ ] Status ledger updated
[ ] Known issues updated
[ ] Decision log updated when required
[ ] Focused quick validation passed
[ ] Required checkpoint passed
[ ] Release validation passed when applicable
```

---

## 33. New maintainer reading order

Recommended order:

```text
1. project/README.md
2. project/project.toml
3. project/docs/00_PROJECT_START_HERE.md
4. project/docs/LANGUAGE_OVERVIEW.md
5. project/docs/LANGUAGE_ARCHITECTURE.md
6. project/docs/MODULE_DEPENDENCY_MAP.md
7. project/docs/INTERFILE_CONTRACT_LOCK.md
8. project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
9. project/docs/VALIDATION_SPEC.md
10. project/docs/STATUS_LEDGER.md
11. project/docs/KNOWN_ISSUES.md
12. project/docs/RELEASE_CRITERIA.md
```

Then inspect the active GF source tree and validation scenarios.

Documentation must be verified against source reality.

---

## 34. AI-assisted development

AI-assisted work may use:

```text
project architecture
interfile contract lock
validation specification
status ledger
known issues
AI_READY.md
raw evidence references
```

AI suggestions are not project truth.

Before accepting a generated change:

- identify provider and consumers;
- verify GF syntax and types with GF;
- review linguistic behavior;
- run relevant scenarios;
- inspect gold differences;
- update contracts and status records;
- rerun checkpoint or release validation.

Never accept a change only because it appears plausible in prose.

---

## 35. Project completion definition

The active project is complete only according to its documented release contract.

Completion does not mean:

```text
one file compiles
one entrypoint loads
one PGF exists
one scenario passes
no current warning is visible
```

Completion means the declared project scope has complete evidence across:

```text
source integrity
module contracts
checkpoint coherence
entrypoint compilation
PGF construction
scenario behavior
gold stability
known-issue review
release criteria
artifact integrity
```

---

## 36. Related framework documentation

```text
docs/00_START_HERE.md
docs/PRODUCT_OVERVIEW.md
docs/SCOPE_AND_NON_GOALS.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/DEPENDENCY_RULES.md
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/validation/VALIDATION_MODES.md
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/operations/CLEANUP_BACKUP_AND_RECOVERY.md
docs/release/VERSIONING_POLICY.md
docs/usage/QUICK_START.md
```

---

## 37. Final project rule

The active project is governed by this relationship:

```text
project.toml
    defines project identity and validation inventory

GF source files
    implement the language

project documents
    define the intended contracts

.gfs scenarios and inputs
    exercise those contracts through GF

.gold files
    preserve reviewed expected behavior

GF Wordbench
    executes, captures, compares, classifies, and reports

release criteria
    determine whether the project is complete
```

The project remains valid only while configuration, source modules, scenarios, gold files, documentation, and release evidence agree.
