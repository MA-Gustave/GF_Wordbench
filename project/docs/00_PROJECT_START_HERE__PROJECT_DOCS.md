# GF Wordbench Project — Start Here

**Document ID:** `GF-WB-PROJECT-START-HERE`  
**Status:** Normative project entry point  
**Canonical path:** `project/docs/00_PROJECT_START_HERE__PROJECT_DOCS.md`  
**Applies to:** The single active GF language project in one GF Wordbench workspace  
**Project identity authority:** `project/project.toml`  
**Project contract authority:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Documentation alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Document owner:** Active project maintainers  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This is the first document to read when working on the active language project.

It provides:

- the project documentation map;
- the authority of each project file;
- the reading order;
- the standard source-change workflow;
- the validation workflow;
- the rules for changing GF module contracts;
- the rules for scenarios and gold files;
- the release workflow;
- the minimum handoff information required when work changes owners.

This page is a navigation and operating guide.

It does not duplicate the detailed rules owned by:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

The central rule is:

> Begin with the authoritative project configuration and contracts, then change providers, consumers, validation evidence and release obligations as one coordinated unit.

---

## 2. Project boundary

One GF Wordbench workspace contains exactly one active GF language project.

Project-owned content belongs in:

```text
project/project.toml
project/README.md
project/docs/
project/validation/
the GF source tree referenced by project.toml
```

Framework-owned content belongs in:

```text
app/
tests/
docs/
templates/
scripts/
```

Generated run evidence belongs under the configured run-output root.

### 2.1 Project-specific information

Language-specific information belongs only in project-owned files or the referenced GF source tree.

Examples:

```text
language identity
module suffix
source root
entrypoints
checkpoints
lincat shapes
morphological decisions
syntax decisions
scenario IDs
gold expectations
release targets
known linguistic limitations
```

### 2.2 Framework neutrality

Do not place active-language assumptions in:

```text
app/
tests/
docs/
templates/
scripts/
```

except in explicitly identified migration fixtures or documentation examples.

### 2.3 Generated evidence

Do not edit generated run evidence as project source.

A run directory records what happened for one resolved project and target. It does not define what the project is.

### 2.4 Portfolio boundary

Cross-workspace discovery, multilingual aggregation, portfolio dashboards and comparison across project identities belong to the independent `gf-portfolio` product.

The allowed dependency direction is:

```text
gf-portfolio -> public versioned GF Wordbench artifacts
```

GF Wordbench does not read Portfolio configuration, persist Portfolio registry state, or require Portfolio to validate or release the active project.

---

## 3. Authoritative project identity

The active project identity is defined by:

```text
project/project.toml
```

Do not infer identity from:

```text
workspace folder name
old run directories
application state
GUI selections
scenario filenames alone
module names alone
documentation examples
```

### 3.1 Identity fields to verify

Before beginning project work, verify that `project.toml` defines or resolves:

```text
project ID
project display name
language code
source root
source glob
GF path parts
entrypoints
checkpoints
required scenarios
optional scenarios
release requirements
expected artifacts
```

Exact field names and schema semantics belong to:

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/PERSISTED_SCHEMA_LOCK.md
```

### 3.2 No duplicated identity table

This page intentionally does not repeat project-specific identity values.

Use:

```text
project/project.toml
```

for machine-readable identity and:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

for reviewed project-level relationships.

---

## 4. Reading order

Read these files in order when joining or resuming the project.

### 4.1 Identity and orientation

```text
project/project.toml
project/README.md
project/docs/00_PROJECT_START_HERE__PROJECT_DOCS.md
project/docs/LANGUAGE_OVERVIEW.md
```

Purpose:

```text
identify the project
understand the declared language scope
locate the source tree
identify the public release surface
```

### 4.2 Architecture and dependency boundaries

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Purpose:

```text
understand module layers
identify providers and consumers
locate entrypoints and checkpoints
avoid circular or hidden dependencies
```

### 4.3 Public linguistic structures

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
```

Purpose:

```text
understand category shapes
understand public lincat fields
understand morphology providers
understand syntax and constructor guarantees
avoid incompatible cross-module changes
```

### 4.4 Validation and evidence

```text
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
project/validation/README.md
```

Purpose:

```text
understand required checkpoints
understand scenario coverage
understand gold ownership
understand release-blocking evidence
```

### 4.5 Decisions, limitations and research

```text
project/docs/KNOWN_ISSUES.md
project/docs/DECISION_LOG.md
project/docs/RESEARCH_EVIDENCE.md
```

Purpose:

```text
identify confirmed defects and limitations
understand retained project decisions
review supporting linguistic evidence
```

### 4.6 Release acceptance

```text
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
project/docs/KNOWN_ISSUES.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Purpose:

```text
identify release gates
confirm evidence coverage
review accepted limitations
confirm artifact expectations
```

---

## 5. Project documentation map

| File | Primary responsibility |
|---|---|
| `00_PROJECT_START_HERE__PROJECT_DOCS.md` | Project navigation and operating workflow |
| `INTERFILE_CONTRACT_LOCK.md` | Normative relationships between project files |
| `LANGUAGE_OVERVIEW.md` | Language scope, goals and supported coverage |
| `LANGUAGE_ARCHITECTURE.md` | GF architecture and layering |
| `MODULE_DEPENDENCY_MAP.md` | Provider, consumer and import relationships |
| `CATEGORY_AND_LINCAT_CONTRACT.md` | Public category and lincat shapes |
| `MORPHOLOGY_SPEC.md` | Morphological system and paradigm guarantees |
| `SYNTAX_AND_CONSTRUCTOR_RULES.md` | Syntax, constructor and composition rules |
| `VALIDATION_SPEC__PROJECT_DOCS.md` | Required validation stages and scenario policy |
| `TEST_COVERAGE_MATRIX__PROJECT_DOCS.md` | Requirement-to-evidence mapping |
| `DECISION_LOG.md` | Project-level decisions and rationale |
| `KNOWN_ISSUES.md` | Confirmed defects, limitations and workarounds |
| `RELEASE_CRITERIA__PROJECT_DOCS.md` | Conditions required for project release |
| `RESEARCH_EVIDENCE.md` | Sources supporting linguistic decisions |

### 5.1 One owner per rule

Each rule has one normative owner. Other documents link to that owner and do not redefine the contract independently.

```text
project identity
    → project/project.toml

module-to-module behavior
    → INTERFILE_CONTRACT_LOCK.md

dependency direction
    → MODULE_DEPENDENCY_MAP.md

lincat field shape
    → CATEGORY_AND_LINCAT_CONTRACT.md

morphological behavior
    → MORPHOLOGY_SPEC.md

syntax construction
    → SYNTAX_AND_CONSTRUCTOR_RULES.md

required scenario behavior
    → VALIDATION_SPEC__PROJECT_DOCS.md

evidence coverage
    → TEST_COVERAGE_MATRIX__PROJECT_DOCS.md

release acceptance
    → RELEASE_CRITERIA__PROJECT_DOCS.md
```

---

## 6. Active project structure

Canonical project-owned structure:

```text
project/
├── README.md
├── project.toml
├── docs/
│   ├── 00_PROJECT_START_HERE__PROJECT_DOCS.md
│   ├── INTERFILE_CONTRACT_LOCK.md
│   ├── LANGUAGE_OVERVIEW.md
│   ├── LANGUAGE_ARCHITECTURE.md
│   ├── MODULE_DEPENDENCY_MAP.md
│   ├── CATEGORY_AND_LINCAT_CONTRACT.md
│   ├── MORPHOLOGY_SPEC.md
│   ├── SYNTAX_AND_CONSTRUCTOR_RULES.md
│   ├── VALIDATION_SPEC__PROJECT_DOCS.md
│   ├── TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
│   ├── DECISION_LOG.md
│   ├── KNOWN_ISSUES.md
│   ├── RELEASE_CRITERIA__PROJECT_DOCS.md
│   └── RESEARCH_EVIDENCE.md
└── validation/
    ├── README.md
    ├── scenarios/
    ├── gold/
    └── inputs/
```

The GF source tree may be inside or outside `project/` according to the approved path contract. Its portable location is declared by `project.toml`.

---

## 7. Source architecture rule

The detailed architecture belongs to:

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
```

Expected dependency direction is generally:

```text
morphology and low-level resources
        ↓
category implementations
        ↓
syntax, structural and extension modules
        ↓
grammar and language entrypoints
        ↓
API or PGF entrypoint
```

Lower-level modules must not import higher-level entrypoints.

Circular imports are prohibited.

### 7.1 Provider and consumer rule

A provider exposes a symbol, field, structure, module or artifact.

A consumer imports, calls, reads or assumes it.

A provider and all consumers form one coordinated change unit.

### 7.2 Hidden dependencies

Document cross-file assumptions involving:

```text
record fields
lincat fields
table shapes
parameter values
constructor order
helper meanings
entrypoint imports
scenario-loaded modules
artifact names
```

GF compilation proves GF syntax and type correctness. It does not replace explicit ownership of cross-file contracts.

---

## 8. Project contract lock

The normative project contract file is:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

It owns relationships such as:

```text
GF module → GF module
abstract syntax → concrete syntax
category → lincat shape
resource provider → syntax consumer
scenario → grammar entrypoint
scenario → validation input
scenario → gold file
entrypoint → .gfo
entrypoint → .pgf
project document → source contract
```

### 8.1 Contract entry requirements

Every active cross-file contract identifies the fields required by the project lock, including:

```text
stable contract ID
provider
consumers
public surface
request or input
response or output
type or shape
ordering
side effects
failure behavior
locked invariants
forbidden behavior
validation evidence
documentation links
review date
```

### 8.2 Contract changes

A contract-changing edit is complete only when all affected elements are reviewed:

```text
provider
direct consumers
downstream entrypoints
project.toml
validation scenarios
gold expectations
dependency map
contract lock
release evidence when applicable
```

A contradiction that cannot be resolved from retained decisions or evidence must be marked `BLOCKED` or `REVIEW_REQUIRED` in the owning contract or issue record.

---

## 9. Category and lincat workflow

Before changing a category or lincat:

1. read `CATEGORY_AND_LINCAT_CONTRACT.md`;
2. identify every provider;
3. identify every consumer;
4. search all field accesses;
5. identify constructors that build the value;
6. identify syntax modules that consume the value;
7. identify scenarios proving the behavior;
8. determine compatibility impact;
9. update the contract with the source change;
10. validate downstream entrypoints.

### 9.1 No silent flattening

Do not replace a structured value with `Str` merely to satisfy one local consumer.

Examples of structured values requiring deliberate contract treatment include:

```text
NP
AP
CN
VP
Cl
Prep
Pron
language-specific records
inflection tables
agreement records
```

### 9.2 Field additions

A new field requires review of:

```text
all constructors
all record extensions
all pattern matches
all projections
all table values
all scenarios
all gold files
```

### 9.3 Field removals or renames

Removing or renaming a consumed field is a breaking project contract change and requires coordinated migration.

---

## 10. Morphology workflow

Before changing morphology:

1. read `MORPHOLOGY_SPEC.md`;
2. identify the owning paradigm or resource;
3. identify categories and lexicons using it;
4. identify irregular or fallback behavior;
5. review relevant known issues;
6. review relevant research evidence;
7. add or update bounded tests;
8. compile the provider;
9. compile direct consumers;
10. validate relevant entrypoints;
11. run scenarios;
12. review gold changes explicitly.

Useful evidence includes:

```text
paradigm compilation
representative inflection tables
irregular-form tests
agreement scenarios
linearization scenarios
generation scenarios
gold comparison
research citation
```

A fallback must be documented in the owning specification or issue record with its scope, risk, validation impact and release disposition. It must not be described as broader support than the declared project scope.

---

## 11. Syntax and constructor workflow

Before changing syntax or constructors:

1. read `SYNTAX_AND_CONSTRUCTOR_RULES.md`;
2. identify the public abstract function or concrete `lin`;
3. identify required lincat fields;
4. identify lower-level providers;
5. identify extension and structural consumers;
6. check import direction;
7. review relevant scenarios;
8. add a focused scenario when behavior changes;
9. compile the narrowest provider;
10. compile downstream checkpoints;
11. compare expected output;
12. update contracts and specifications.

### 11.1 Smallest coherent change

Prefer the smallest change that preserves architecture.

Do not duplicate a provider merely to avoid updating a consumer.

### 11.2 Constructor compatibility

A constructor change may be breaking when it changes:

```text
GF type
argument order
result category
record shape
agreement requirements
word-order guarantees
polarity behavior
tense behavior
case assignment
preposition behavior
linearization output relied on by consumers
```

---

## 12. Validation authority

The project validation contract is defined by:

```text
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/project.toml
project/validation/
```

GF Wordbench provides language-neutral orchestration.

The project defines what proves that its declared language scope is acceptable.

### 12.1 Validation layers

Typical validation layers are:

```text
static scanning
provider compilation
checkpoint compilation
entrypoint compilation
PGF build
scenario execution
gold comparison
release-gate evaluation
```

### 12.2 Compilation authority

GF compilation is authoritative for GF syntax and type correctness.

Static scanning remains separate supplementary evidence.

### 12.3 Runtime authority

Scenarios are authoritative for the runtime behavior they explicitly test.

A compiled grammar is not automatically behaviorally complete.

---

## 13. Validation modes

Canonical framework modes:

```text
quick
checkpoint
diagnostic
release
```

Project policy supplies project-owned content without redefining the framework meaning of these modes.

### 13.1 Quick

Use for a bounded local change.

```text
one target
required local context
fast feedback
```

### 13.2 Checkpoint

Use to validate one declared architectural layer.

```text
checkpoint provider layer
prerequisite layers
configured consumers
applicable scenarios
```

### 13.3 Diagnostic

Use for broad evidence and root-cause analysis.

```text
selected source set
classification
scenario evidence
detailed reports
previous-run comparison
```

### 13.4 Release

Use to evaluate the complete declared release contract.

```text
all required checkpoints
release entrypoints
required scenarios
gold comparison
PGF artifact when required
manifest
known-issue disposition
```

Exact CLI syntax belongs to `docs/usage/CLI_REFERENCE.md`.

---

## 14. Local development loop

For a focused change:

```text
1. identify the owning specification
2. identify the contract entry
3. identify provider and consumers
4. inspect known issues and retained decisions
5. make the smallest coherent source change
6. compile the changed provider
7. compile direct consumers
8. run the nearest checkpoint
9. run focused scenarios
10. inspect normalized output
11. update gold only through explicit review
12. update project documentation
13. run broader diagnostic validation when needed
```

A successful provider compilation does not prove that all consumers remain compatible.

---

## 15. Scenario structure

Scenario source files belong in:

```text
project/validation/scenarios/
```

Canonical extension:

```text
.gfs
```

Stable inputs belong in:

```text
project/validation/inputs/
```

Reviewed expected output belongs in:

```text
project/validation/gold/
```

### 15.1 Scenario identity

Every scenario ID must be unique.

Its configured identity, filename, markers and gold mapping must agree.

### 15.2 Scenario purpose

Every scenario has one bounded purpose, such as:

```text
load one entrypoint
parse representative sentences
linearize representative trees
test morphology
test agreement
test word order
test ambiguity
test bounded generation
test missing linearizations
test PGF loading
```

### 15.3 Scenario boundaries

Use the marker contract documented by GF Wordbench.

Do not create ad hoc output-parsing rules inside the project.

### 15.4 Determinism

Scenario output used for gold comparison must be:

```text
bounded
ordered
normalized
repeatable under the declared environment
```

---

## 16. Gold-file policy

Gold files belong in:

```text
project/validation/gold/
```

They are reviewed source assets, not disposable run output.

### 16.1 Normal validation

Normal validation must not modify gold files.

### 16.2 Updating gold

Gold creation or update is a separate reviewed operation.

Review:

```text
why output changed
whether the change is intended
which contract changed
which scenario changed
which linguistic behavior changed
whether normalization changed
whether unrelated output changed
```

### 16.3 Gold mismatch

A mismatch is evidence. Review the grammar, specification, scenario, normalization, GF version and gold expectation before deciding what must change.

---

## 17. Test coverage matrix

The coverage matrix is:

```text
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
```

It maps requirements to evidence.

Recommended columns:

```text
requirement ID
feature or contract
provider
consumer
checkpoint
scenario
gold
required evidence
release relevance
known gap or limitation
```

### 17.1 Coverage rule

A documented feature requires defined evidence.

### 17.2 Release coverage

Every release-critical contract maps to at least one proof such as:

```text
direct compile
checkpoint compile
entrypoint compile
scenario
gold comparison
PGF artifact
documented manual inspection when automation is impossible
```

---

## 18. Known issues

Confirmed defects and limitations belong in:

```text
project/docs/KNOWN_ISSUES.md
```

Each issue should include:

```text
stable issue ID
summary
affected modules
affected behavior
severity
release disposition
workaround
validation evidence
owner
resolution condition
```

Every issue affecting release must be fixed, explicitly accepted within the declared scope, deferred by a retained decision, or treated as release-blocking.

One issue has one authoritative record. Source comments and other documents may reference its ID without duplicating the full record.

---

## 19. Decision log

Project-level decisions belong in:

```text
project/docs/DECISION_LOG.md
```

Record decisions involving:

```text
linguistic model
module ownership
lincat shape
morphological representation
syntax strategy
word order
case system
agreement model
accepted limitation
entrypoint structure
scenario strategy
release scope
```

A useful decision entry includes:

```text
decision ID
date
decision state
context
decision
alternatives
consequences
affected contracts
affected source files
validation
migration
```

Framework architecture decisions belong in:

```text
docs/decisions/
```

Do not place Python framework architecture in the project decision log.

---

## 20. Research evidence

Linguistic evidence belongs in:

```text
project/docs/RESEARCH_EVIDENCE.md
```

Use it to support:

```text
morphological classes
agreement behavior
case assignment
word-order decisions
clitic behavior
determiner behavior
pronoun behavior
preposition behavior
irregular forms
orthographic rules
dialect or register scope
```

Distinguish:

```text
documented linguistic evidence
retained project decision
source representation
accepted limitation
hypothesis requiring review
```

A source-backed project rule should link:

```text
research evidence
→ specification
→ source provider
→ scenario
→ gold evidence
```

---

## 21. Project README

`project/README.md` is the short project entry point.

It should provide:

```text
project name
language scope
source-root overview
primary entrypoints
basic validation commands
links to this document
```

This document owns the deeper operating workflow.

---

## 22. Before editing GF source

```text
[ ] authoritative specification identified
[ ] provider identified
[ ] consumers identified
[ ] project contract entry identified
[ ] dependency map reviewed
[ ] lincat contract reviewed when relevant
[ ] morphology or syntax specification reviewed
[ ] known issues reviewed
[ ] retained decisions reviewed
[ ] existing validation evidence identified
[ ] compatibility impact classified
```

If no contract exists for a cross-file dependency, document the contract before relying on it further.

---

## 23. During a source change

```text
[ ] change remains inside project scope
[ ] import direction remains valid
[ ] no circular dependency introduced
[ ] no public field changed silently
[ ] no duplicated provider introduced
[ ] no structured value flattened without decision
[ ] no undocumented fallback introduced
[ ] source remains UTF-8
[ ] file naming matches project conventions
[ ] focused validation remains available
```

---

## 24. After a source change

```text
[ ] changed provider compiles
[ ] direct consumers compile
[ ] downstream checkpoint compiles
[ ] relevant entrypoint compiles
[ ] required scenario passes
[ ] normalized output reviewed
[ ] gold diff reviewed
[ ] project contract updated
[ ] dependency map updated
[ ] specification updated
[ ] coverage matrix updated
[ ] known issues updated when applicable
[ ] decision log updated when applicable
[ ] research evidence updated when applicable
```

---

## 25. Compatibility classification

Classify the change before merging or releasing.

### 25.1 Internal compatible change

Examples:

```text
private helper refactor
performance improvement
local naming cleanup
source change preserving all public behavior
```

Required:

```text
focused tests
no public contract change
```

### 25.2 Compatible project extension

Examples:

```text
new optional lexical item
new compatible abstract function
new optional scenario
new optional concrete syntax
new compatible morphology coverage
```

Required:

```text
contract review
consumer review
new evidence
release-impact review
```

### 25.3 Breaking project change

Examples:

```text
public function rename
category type change
lincat field removal
constructor argument change
entrypoint rename
module suffix rename
PGF API change
scenario identity change
gold semantics change
```

Required:

```text
breaking contract update
migration plan
all consumers updated
project configuration updated
scenarios updated
gold reviewed
release version impact assessed
```

---

## 26. Entrypoints and checkpoints

The authoritative ordered lists are in:

```text
project/project.toml
```

Their project-level meaning is documented in:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
```

### 26.1 Entrypoint

An entrypoint is a top-level GF module used for:

```text
release compilation
grammar loading
scenario execution
PGF construction
external runtime use
```

### 26.2 Checkpoint

A checkpoint proves one architectural layer is coherent.

Examples may include:

```text
morphology
categories
syntax
structural modules
extensions
language module
API module
```

### 26.3 Ordering

Entrypoints and checkpoints are deterministic ordered lists.

Do not depend on filesystem discovery order.

---

## 27. PGF and release artifacts

Expected release artifacts are declared by:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

A PGF build proves linking of the declared target. It does not by itself prove:

```text
scenario correctness
gold stability
coverage completeness
linguistic scope
release acceptance
```

### 27.1 Artifact identity

Do not accept an arbitrary `.pgf` found in the source tree.

The expected artifact name and release entrypoints must be explicit.

### 27.2 Current-run evidence

Release artifacts must be attributable to the validated run, source fingerprints, command and toolchain.

Stale artifacts do not satisfy release criteria.

---

## 28. Release workflow

Before declaring the project releasable:

1. read `RELEASE_CRITERIA__PROJECT_DOCS.md`;
2. verify `project.toml`;
3. review all active contracts;
4. review all release-critical coverage rows;
5. resolve or explicitly disposition all release blockers;
6. review accepted limitations;
7. run required checkpoints;
8. build required entrypoints;
9. build the expected PGF when required;
10. run all required scenarios;
11. compare all required gold files;
12. review regressions;
13. verify artifacts and manifest;
14. record GF and RGL identity;
15. record accepted known issues;
16. preserve release evidence.

A failed required gate remains failed. A retained decision may defer release; it must not relabel failure as success.

---

## 29. Standard sources of truth

| Question | Read this |
|---|---|
| What project is active? | `project/project.toml` |
| What modules are entrypoints? | `project/project.toml` and `INTERFILE_CONTRACT_LOCK.md` |
| What imports what? | `MODULE_DEPENDENCY_MAP.md` |
| What does this public field mean? | `CATEGORY_AND_LINCAT_CONTRACT.md` |
| How should this form inflect? | `MORPHOLOGY_SPEC.md` |
| How should this constructor behave? | `SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| What must be validated? | `VALIDATION_SPEC__PROJECT_DOCS.md` |
| Which evidence proves it? | `TEST_COVERAGE_MATRIX__PROJECT_DOCS.md` |
| Is the limitation known? | `KNOWN_ISSUES.md` |
| Why was this design chosen? | `DECISION_LOG.md` |
| Which linguistic source supports it? | `RESEARCH_EVIDENCE.md` |
| Can it be released? | `RELEASE_CRITERIA__PROJECT_DOCS.md` |
| Which cross-file promises are locked? | `INTERFILE_CONTRACT_LOCK.md` |

---

## 30. Prohibited practices

Do not:

```text
change project identity in application state
hardcode language paths in framework code
edit the template to change the active project
use old run output as current configuration
modify gold during a normal validation run
accept a matching filename as proof of artifact freshness
hide a fallback or limitation
change a public field without updating consumers
add a circular import
duplicate a provider to avoid a contract change
treat scan success as compile success
treat compile success as scenario success
treat scenario success as release acceptance
treat documentation as proof without validation
parse human reports as machine configuration
leave project placeholders unresolved
store Portfolio registry state in Wordbench
```

---

## 31. Working with generated reports

A run may produce:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
raw logs
detail artifacts
compiled artifacts
```

Use:

```text
summary.json
manifest.json
```

for machine-readable run facts and integrity.

Use:

```text
summary.md
AI_READY.md
```

for human and diagnostic handoff.

Use:

```text
raw/
details/
artifacts/
```

for detailed evidence.

Generated reports do not replace project documentation.

---

## 32. Resuming work after interruption

Use this sequence:

1. open `project/project.toml`;
2. open this file;
3. open the relevant specifications and contract entries;
4. open `KNOWN_ISSUES.md`;
5. inspect the latest relevant decision;
6. inspect the most recent compatible run evidence;
7. verify that source, configuration and documentation agree;
8. run a focused checkpoint before continuing.

Do not rely only on a chat transcript or task description. The repository contains the governing truth.

---

## 33. Handoff between maintainers

A project handoff should include:

```text
project ID
branch or commit
task
affected provider
affected consumers
contract IDs
known blockers
last validation run
failing checkpoints
failing scenarios
gold changes
uncommitted changes
next smallest action
```

Before handoff, update when applicable:

```text
KNOWN_ISSUES.md
DECISION_LOG.md
TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
INTERFILE_CONTRACT_LOCK.md
the owning specification
```

A handoff message is not a substitute for repository updates.

---

## 34. Review workflow

A project review should ask:

```text
Does project.toml match the source tree?
Does the dependency map match imports?
Do contract providers exist?
Do listed consumers still depend on the provider?
Do public lincat fields match source behavior?
Do specifications match source?
Do scenarios load the intended entrypoints?
Do gold files map to the intended scenarios?
Are known issues still accurate?
Do release criteria map to evidence?
```

---

## 35. Anti-drift checks

The framework contract may expose checks equivalent to project, contract and repository validation. Exact command spelling belongs to `docs/usage/CLI_REFERENCE.md`.

Expected checks include:

```text
project schema valid
required project documents present
entrypoints exist
checkpoints exist
scenario IDs unique
scenario files exist
gold mappings valid
project/template required-path mirror valid
contract providers exist
contract consumers exist
dependency map is current
no unresolved required placeholders
no stale language identifiers
no absolute local paths in reusable files
no generated files in project source areas
```

---

## 36. Project placeholders

The reusable template may contain placeholders.

The active project must not retain unresolved placeholders in required identity or contract fields.

Examples:

```text
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<SOURCE_DIR>
<ENTRYPOINT>
<EXPECTED_PGF>
<YYYY-MM-DD>
```

A placeholder in an explanatory example must be clearly identified as an example.

---

## 37. Document maintenance

Update this page when:

```text
a required project document is added or removed
the project operating workflow changes
the source-of-truth map changes
the project structure changes
the standard handoff changes
release navigation changes
```

Do not repeat a detailed rule owned elsewhere. Link to its authority.

---

## 38. New maintainer checklist

```text
[ ] project.toml read
[ ] project README read
[ ] language overview read
[ ] architecture read
[ ] dependency map read
[ ] contract lock read
[ ] lincat contract read
[ ] morphology spec read
[ ] syntax rules read
[ ] validation spec read
[ ] coverage matrix reviewed
[ ] known issues reviewed
[ ] decision log reviewed
[ ] release criteria reviewed
[ ] source root located
[ ] entrypoints located
[ ] checkpoints located
[ ] scenarios located
[ ] latest compatible run inspected
```

---

## 39. New feature checklist

```text
[ ] feature scope documented
[ ] linguistic evidence identified
[ ] provider selected
[ ] consumers identified
[ ] category/lincat impact reviewed
[ ] morphology impact reviewed
[ ] syntax impact reviewed
[ ] dependency direction reviewed
[ ] project contract added or updated
[ ] focused compile target identified
[ ] checkpoint identified
[ ] scenario added or updated
[ ] gold reviewed
[ ] coverage matrix updated
[ ] release impact assessed
```

---

## 40. Bug-fix checklist

```text
[ ] defect reproduced
[ ] direct provider identified
[ ] downstream symptoms separated
[ ] known issue identified or added
[ ] smallest coherent fix selected
[ ] public contract impact classified
[ ] regression scenario added
[ ] relevant gold reviewed
[ ] provider compiles
[ ] consumers compile
[ ] checkpoint passes
[ ] known issue updated
```

---

## 41. Breaking-change checklist

```text
[ ] breaking surface identified
[ ] project contract impact reviewed
[ ] all consumers enumerated
[ ] migration plan written
[ ] project.toml updated
[ ] dependency map updated
[ ] specifications updated
[ ] scenarios migrated
[ ] gold files reviewed
[ ] release artifact names reviewed
[ ] project release version impact assessed
[ ] compatibility notes written
[ ] old identifiers removed
[ ] diagnostic validation completed
[ ] release criteria re-evaluated
```

---

## 42. Scenario-change checklist

```text
[ ] scenario purpose remains bounded
[ ] scenario ID remains unique
[ ] configured entrypoint is correct
[ ] required inputs exist
[ ] markers are correct
[ ] output is bounded
[ ] output is deterministic
[ ] normalization assumptions are unchanged or reviewed
[ ] matching gold exists when required
[ ] gold update is explicit
[ ] coverage matrix updated
[ ] validation spec updated when behavior changed
```

---

## 43. Release checklist

```text
[ ] project identity valid
[ ] no required placeholders
[ ] no stale language identifiers
[ ] no undocumented project decisions
[ ] active contracts reviewed
[ ] dependency map reviewed
[ ] known issues reviewed
[ ] release criteria reviewed
[ ] all release checkpoints pass
[ ] all release entrypoints pass
[ ] expected PGF built when required
[ ] all required scenarios pass
[ ] all required gold comparisons pass
[ ] no unexplained regression
[ ] artifact manifest valid
[ ] GF version recorded
[ ] RGL identity recorded
[ ] release evidence preserved
```

---

## 44. Minimum project invariants

The active project always satisfies:

```text
[ ] one authoritative project identity
[ ] one active language
[ ] one documented source root
[ ] one normative language target per run
[ ] deterministic entrypoint order
[ ] deterministic checkpoint order
[ ] explicit module ownership
[ ] documented public lincat fields
[ ] documented morphology strategy
[ ] documented syntax strategy
[ ] no circular imports
[ ] no undocumented fallback
[ ] unique scenario IDs
[ ] explicit scenario-to-gold relationships
[ ] normal validation never modifies gold
[ ] release targets are explicit
[ ] every release-critical contract has evidence
[ ] no dependency on gf-portfolio runtime or private state
```

---

## 45. Navigation rule

When unsure where to record information:

```text
identity or project policy
    → project.toml

cross-file promise
    → INTERFILE_CONTRACT_LOCK.md

architecture
    → LANGUAGE_ARCHITECTURE.md

dependency relationship
    → MODULE_DEPENDENCY_MAP.md

public category or field
    → CATEGORY_AND_LINCAT_CONTRACT.md

morphology
    → MORPHOLOGY_SPEC.md

syntax or constructor behavior
    → SYNTAX_AND_CONSTRUCTOR_RULES.md

validation requirement
    → VALIDATION_SPEC__PROJECT_DOCS.md

evidence coverage
    → TEST_COVERAGE_MATRIX__PROJECT_DOCS.md

confirmed defect or limitation
    → KNOWN_ISSUES.md

retained design rationale
    → DECISION_LOG.md

linguistic source
    → RESEARCH_EVIDENCE.md

release acceptance
    → RELEASE_CRITERIA__PROJECT_DOCS.md
```

---

## 46. Enforcement rule

This page starts the workflow but does not replace the project authorities.

> No project change is complete until authoritative configuration, provider and consumer contracts, validation evidence, known limitations and release impact agree with the GF source.
