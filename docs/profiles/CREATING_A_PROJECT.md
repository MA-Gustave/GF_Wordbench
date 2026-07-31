# GF Wordbench — Creating a Project

**Document ID:** `GF-WB-PROJECTS-CREATING-A-PROJECT`  
**Status:** Operational specification  
**Applies to:** Creating one active GF language project from `templates/project/`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** GF Wordbench maintainers  
**Project owner after initialization:** active-language project maintainers  
**Authoritative project identity:** `project/project.toml`  
**Template source:** `templates/project/`  
**Related project model:** `docs/projects/PROJECT_MODEL.md`  
**Completion authority:** `docs/projects/PROJECT_COMPLETION_CHECKLIST.md`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This document defines the complete procedure for creating a new active GF Wordbench language project.

A project is not created merely by copying a directory or pointing the GUI at a source folder.

A complete project establishes a coordinated contract between:

```text
project identity
GF source tree
module architecture
entrypoints
checkpoints
validation scenarios
validation inputs
gold expectations
release artifacts
project documentation
contract locks
```

The core rule is:

> One GF Wordbench workspace contains exactly one active language project, and `project/project.toml` is the authoritative source of that project identity.

Project creation must remove template placeholders and old-language assumptions before the project can be treated as active.

---

## 2. Outcomes

After completing this procedure, the repository should contain:

- one unambiguous active language identity;
- one valid `project/project.toml`;
- one project documentation set;
- one active project interfile contract lock;
- known GF source roots;
- documented module layers;
- configured entrypoints;
- configured checkpoints;
- registered required and optional scenarios;
- reviewed validation inputs;
- reviewed gold files where exact comparison is required;
- explicit release criteria;
- no unresolved template placeholders;
- no stale identity inherited from another project;
- enough evidence to run quick, checkpoint, diagnostic and release validation.

---

## 3. Scope

This procedure covers:

- creating a project from the canonical template;
- assigning project identity;
- connecting an existing or new GF source tree;
- configuring source selection;
- configuring GF path components;
- declaring module suffixes;
- declaring entrypoints and checkpoints;
- creating scenario files;
- creating input and gold assets;
- completing project documentation;
- completing the active project contract lock;
- establishing release criteria;
- performing bootstrap validation;
- promoting the project from template state to active state.

This procedure does not cover:

- migrating historical GF Audit run data;
- converting an already integrated legacy project;
- designing a language grammar from first linguistic principles;
- implementing missing GF modules;
- writing every scenario command in detail;
- installing GF itself;
- releasing GF Wordbench;
- releasing the language project;
- registering several Wordbench workspaces or producing cross-project views.

Multi-workspace discovery, aggregation and comparison belong to the independent `gf-portfolio` product. Project creation must not register the project in Portfolio as an implicit side effect.

For the other tasks, use the dedicated migration, GF, scenario and release documentation.

---

## 4. Preconditions

Before creating a project, confirm:

```text
[ ] GF Wordbench repository exists
[ ] templates/project/ exists
[ ] GF executable is available or its path is known
[ ] RGL source root is available or its path is known
[ ] Active language has a stable name
[ ] Active language has a stable code
[ ] Source tree location is known
[ ] Intended module suffix is known
[ ] Intended top-level grammar entrypoint is identified
[ ] Project owner is identified
[ ] Existing project/ content has been backed up if it contains work
```

Do not overwrite an existing active project without an explicit reset, migration or backup workflow.

---

## 5. Project creation models

GF Wordbench supports two project-creation situations.

## 5.1 Existing GF language source tree

Use this procedure when:

- `.gf` files already exist;
- module names and imports already exist;
- an entrypoint exists or can be identified;
- the main work is integration, validation and documentation.

The source tree may remain outside `project/`.

`project/` describes and validates the source tree; it does not need to contain all GF source files.

## 5.2 New GF language implementation

Use this procedure when:

- the language project is starting from a new or incomplete source tree;
- module architecture is still being established;
- placeholders and incomplete contracts will exist temporarily.

The project may be initialized before all release scenarios and gold files exist.

Its configuration and documentation must remain internally valid, and release validation must reject every missing required contract or criterion.

---

## 6. Canonical directories

Framework template:

```text
templates/project/
```

Active project:

```text
project/
```

Canonical active layout:

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

The project template must mirror this relative structure.

---

## 7. Template-copy rule

Create the active project by copying the contents of:

```text
templates/project/
```

to:

```text
project/
```

Do not move the template.

Do not edit the template to contain active-language facts.

The active project becomes project-specific; the template remains reusable.

---

## 8. Safe copy procedure

Before copying:

```text
[ ] Confirm project/ does not contain unbacked active work
[ ] Confirm template structure is current
[ ] Confirm destination is inside the GF Wordbench repository
[ ] Confirm source and destination are different directories
```

Conceptual PowerShell operation:

```powershell
Copy-Item -Path .\templates\project\* `
          -Destination .\project `
          -Recurse `
          -Force
```

Conceptual POSIX operation:

```bash
cp -R templates/project/. project/
```

The exact command is less important than preserving the complete relative structure.

After copying, compare the template and project path inventories.

Project content values will differ; required relative filenames should initially match.

---

## 9. Initialization command

The canonical initialization operation is:

```text
gf-wordbench project init
```

The exact options, overwrite protections and exit codes are defined by `docs/usage/CLI_REFERENCE.md`.

The initializer must:

- refuse unsafe overwrite by default;
- copy the complete template;
- write only through explicit initialization;
- preserve the reusable template;
- validate the resulting structure;
- report unresolved placeholders;
- avoid inventing language-specific module facts;
- avoid using GUI state as project identity;
- avoid registering the project in `gf-portfolio`.

Manual creation remains valid when it produces the same canonical structure and satisfies the same checks.

---

## 10. Project identity

The active project must have one authoritative identity.

Identity belongs in:

```text
project/project.toml
```

Required identity facts include:

```text
project id
display name
language name
language code
module suffix
project root
source root
entrypoints
checkpoints
required scenarios
optional scenarios
release targets
```

The same facts may be described in project documentation, but documentation must not contradict `project.toml`.

---

## 11. Choosing a project ID

The project ID should be:

- stable;
- short;
- lowercase;
- filesystem-safe;
- meaningful;
- independent of a branch or developer name.

Recommended syntax:

```text
[a-z][a-z0-9-]*
```

Examples:

```text
sqi
fra
eng
my-language
```

Avoid:

```text
test
new
john-copy
project-2
```

Changing the project ID after published runs exist is a breaking project migration.

---

## 12. Choosing a language code

Use one stable code for the active language.

The code should follow the project's chosen standard consistently.

Examples may include ISO language identifiers.

Rules:

- document the selected standard;
- do not alternate between multiple codes without an explicit mapping;
- keep the code stable in configuration, reports and project documentation;
- distinguish language code from GF module suffix;
- do not infer the code from historical directory names.

---

## 13. Choosing a module suffix

The module suffix identifies the active language in GF module names.

Examples:

```text
Fre
Sqi
Eng
```

Rules:

- use the suffix already implemented by the source tree when integrating existing modules;
- ensure configured module names use the same capitalization;
- ensure scenario entrypoints use the same suffix;
- ensure project documentation uses the same suffix;
- treat a suffix rename as a coordinated source and project migration;
- remove old suffix assumptions from active scenarios, golds and documentation.

---

## 14. Canonical `project.toml` identity

Canonical header:

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"
```

Conceptual identity section:

```toml
[project]
id = "<project-id>"
name = "<display-name>"
language_code = "<language-code>"
root = "."
```

The complete field contract is owned by:

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/PERSISTED_SCHEMA_LOCK.md
```

Do not add undocumented fields merely because they seem convenient.

---

## 15. Project root

Canonical project root:

```toml
root = "."
```

This means the directory containing `project.toml`.

The project root is not necessarily the GF source root.

Example:

```text
GF_Wordbench/project/
```

may describe GF sources under:

```text
../gf-rgl/lib/src/language/
```

according to the project configuration contract.

Project-owned paths should remain project-relative where the schema permits.

---

## 16. Local paths versus project facts

Do not store developer-machine tool locations in `project.toml` when they are local environment facts.

Examples of local facts:

```text
C:\Program Files\GF\bin\gf.exe
C:\Users\name\rgl
D:\audit-runs
```

These belong to:

- environment configuration;
- CLI options;
- application state;
- local setup.

Project facts belong to `project.toml`.

Examples:

```text
source directory relative to project/source model
source glob
module suffix
entrypoints
checkpoints
scenario IDs
release requires PGF
```

This distinction preserves portability.

---

## 17. Source-tree discovery

Before configuring source selection, inventory the source tree.

Record:

```text
source root
all .gf files
module declarations
direct imports
abstract modules
concrete modules
resource modules
interface modules
instance modules
morphology modules
syntax modules
lexicon modules
structural modules
extension modules
top-level entrypoints
generated .gfo files
existing .pgf files
```

Do not treat generated `.gfo` or `.pgf` files as source truth.

---

## 18. Source selection

Configure the canonical source directory and glob.

Conceptual fields:

```toml
[sources]
directory = "<project-relative-or-configured-source-directory>"
glob = "**/*.gf"
```

The exact field names are defined by the project schema.

Rules:

- source selection must include intended language files;
- source selection must exclude generated run directories;
- source selection must not depend on old output directories;
- inclusion/exclusion behavior must be documented;
- file order must be deterministic;
- a source path containing spaces must remain supported;
- source files are read-only during normal validation.

---

## 19. Source-root validation

Before continuing:

```text
[ ] Source root exists
[ ] At least one intended .gf file exists
[ ] File encoding is readable
[ ] Module names can be extracted
[ ] Generated artifacts are distinguishable
[ ] No old-language source root remains configured
[ ] Paths resolve from the documented base
```

A missing source root is configuration `ERROR`, not a successful empty project.

---

## 20. Module inventory

Create a reviewed inventory table:

| Module file | GF module name | Kind | Direct imports | Intended role | Notes |
|---|---|---|---|---|---|
| `<file>` | `<module>` | abstract/concrete/resource/etc. | `<imports>` | `<role>` | `<verified facts>` |

Use this inventory to populate:

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

The inventory may later become generated diagnostic data, but the project documents remain reviewed sources of intent.

---

## 21. Module-kind classification

Classify each major module as applicable:

```text
abstract
concrete
resource
interface
instance
morphology
categories
syntax
noun
verb
sentence
question
relative
structural
lexicon
extensions
language entrypoint
API entrypoint
release entrypoint
helper
```

A module may serve more than one role, but one authoritative responsibility should be clear.

Avoid documenting every private helper as a major architectural layer.

---

## 22. Entrypoints

An entrypoint is a top-level module used for:

- grammar loading;
- validation;
- PGF construction;
- API-facing scenarios;
- release evidence.

At least one entrypoint is required before release validation.

Conceptual configuration:

```toml
[modules]
entrypoints = [
  "<GrammarEntrypoint>.gf",
]
```

The exact field names belong to the project schema.

---

## 23. Entrypoint selection

Select entrypoints by actual intended use.

Possible entrypoint types:

```text
concrete grammar entrypoint
language entrypoint
syntax/API entrypoint
application entrypoint
release entrypoint
```

Do not select a lower-level module merely because it compiles.

A successful morphology module does not prove the release grammar loads.

---

## 24. Entrypoint invariants

For every configured entrypoint:

```text
[ ] File exists
[ ] GF module name matches configuration
[ ] Imports are documented
[ ] Source suffix matches project suffix
[ ] It compiles or its incompleteness is recorded
[ ] Required scenarios load it
[ ] Release workflow targets the intended entrypoint
[ ] Expected generated artifact is documented
```

Removing or substituting an entrypoint requires project architectural review.

---

## 25. Checkpoints

Checkpoints are modules whose successful validation proves that a development layer is coherent.

Examples:

```text
morphology
categories
noun syntax
verb syntax
sentence syntax
extensions
structural vocabulary
release grammar
```

Conceptual configuration:

```toml
[modules]
checkpoints = [
  "<MorphologyCheckpoint>.gf",
  "<SyntaxCheckpoint>.gf",
  "<FinalCheckpoint>.gf",
]
```

Declared order is semantically significant.

---

## 26. Checkpoint selection

Choose checkpoints that correspond to real dependency layers.

Good checkpoint characteristics:

- many downstream modules depend on it;
- its success proves a meaningful layer;
- failure can explain downstream cascades;
- it has clear scenario evidence where useful;
- its responsibility is documented.

Avoid using every source file as a checkpoint.

File compilation and checkpoint validation are distinct concepts.

---

## 27. Checkpoint order

Order checkpoints from lower-level providers toward release entrypoints.

Conceptual order:

```text
resource/morphology
    → categories
    → noun/verb syntax
    → sentence-level syntax
    → structural/extensions
    → language/API entrypoint
```

The actual order belongs to the active language architecture.

GF Wordbench must not alphabetically reorder checkpoints.

---

## 28. GF path planning

Identify the GF search-path components required by the project.

Typical components:

```text
active language source directories
RGL abstract/source directories
shared library directories
project helper directories
generated artifact directories when contractually allowed
```

Path order is semantically significant.

Do not duplicate GF path construction inside scenarios.

Compilation and scenario execution must resolve compatible GF paths.

---

## 29. GF version compatibility

Record:

```text
minimum supported GF version
tested GF versions
known incompatible GF versions
required command capabilities
```

Do not claim compatibility based only on one successful compile.

At minimum, test:

- version probe;
- one source compile;
- one entrypoint load;
- required scenario command forms;
- PGF construction when release requires it.

---

## 30. Project documentation initialization

After the source and identity inventory, complete project documents in this order:

```text
1. README.md
2. docs/00_PROJECT_START_HERE.md
3. docs/LANGUAGE_OVERVIEW.md
4. docs/LANGUAGE_ARCHITECTURE.md
5. docs/MODULE_DEPENDENCY_MAP.md
6. docs/CATEGORY_AND_LINCAT_CONTRACT.md
7. docs/MORPHOLOGY_SPEC.md
8. docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
9. docs/VALIDATION_SPEC.md
10. docs/TEST_COVERAGE_MATRIX.md
11. docs/DECISION_LOG.md
12. docs/KNOWN_ISSUES.md
13. docs/RELEASE_CRITERIA.md
14. docs/RESEARCH_EVIDENCE.md
15. docs/INTERFILE_CONTRACT_LOCK.md
```

The exact drafting order may vary.

The contract lock should be finalized after major provider/consumer facts are known.

---

## 31. `project/README.md`

The project README should state:

- active language;
- project purpose;
- source-tree location;
- principal entrypoints;
- validation entry point;
- links to project documents;
- release entrypoint and release criteria.

It must not redefine framework architecture.

It should link to the authoritative project documents.

---

## 32. `00_PROJECT_START_HERE.md`

This file provides the project-specific reading order.

Recommended order:

```text
LANGUAGE_OVERVIEW
LANGUAGE_ARCHITECTURE
MODULE_DEPENDENCY_MAP
CATEGORY_AND_LINCAT_CONTRACT
MORPHOLOGY_SPEC
SYNTAX_AND_CONSTRUCTOR_RULES
VALIDATION_SPEC
RELEASE_CRITERIA
INTERFILE_CONTRACT_LOCK
```

It should identify which documents are normative and which are guidance or evidence.

---

## 33. Language overview

`LANGUAGE_OVERVIEW.md` should define:

- language identity;
- supported writing system;
- target GF/RGL role;
- scope;
- linguistic coverage;
- dialect policy;
- orthographic policy;
- known non-goals;
- major external references;
- release intent.

Do not use this file to duplicate detailed morphology or syntax contracts.

---

## 34. Language architecture

`LANGUAGE_ARCHITECTURE.md` should define:

- module layers;
- authoritative providers;
- top-level entrypoints;
- source-directory organization;
- extension strategy;
- API surface where relevant;
- intended dependency direction;
- release assembly.

Every named module must exist in the source tree or be removed from the architecture document.

---

## 35. Module dependency map

`MODULE_DEPENDENCY_MAP.md` should record:

- direct imports;
- major transitive dependency chains;
- checkpoint order;
- entrypoint dependency chains;
- known cycles;
- generated or inherited modules;
- classifier-relevant relationships.

The map must match current source imports.

It should not claim dependencies that exist only in an old design.

---

## 36. Category and lincat contract

`CATEGORY_AND_LINCAT_CONTRACT.md` should define cross-module structures consumed by more than one file.

Examples:

```text
lincat record fields
agreement dimensions
parameter types
case systems
gender/number/person dimensions
shared constructors
coercions
public helper operations
```

A private local implementation detail does not need to be locked.

It becomes contractual when another module depends on it.

---

## 37. Morphology specification

`MORPHOLOGY_SPEC.md` should define:

- noun paradigms;
- adjective paradigms;
- verb paradigms;
- pronouns;
- determiners;
- inflectional parameters;
- irregularity policy;
- stem formation;
- orthographic transformations;
- fallback policy;
- known incomplete paradigms.

Every unresolved fallback that affects correctness or release must appear in `KNOWN_ISSUES.md`.

---

## 38. Syntax and constructor rules

`SYNTAX_AND_CONSTRUCTOR_RULES.md` should define:

- phrase structure;
- agreement propagation;
- word order;
- negation;
- questions;
- relative clauses;
- coordination;
- complement structure;
- constructor ownership;
- API-facing behavior;
- accepted variation;
- unsupported structures.

It should link to category/lincat and morphology contracts instead of duplicating them.

---

## 39. Validation specification

`VALIDATION_SPEC.md` is the project authority for what must be proven.

It should define:

- required source checks;
- checkpoint criteria;
- entrypoint criteria;
- required scenarios;
- optional scenarios;
- expected outputs;
- negative tests;
- gold-backed tests;
- manual review criteria;
- PGF requirement;
- release-blocking conditions.

Every release criterion should have executable evidence where possible.

---

## 40. Coverage matrix

`TEST_COVERAGE_MATRIX.md` maps:

```text
requirement
    → source provider
    → checkpoint
    → scenario
    → input
    → gold or assertion
    → evidence artifact
    → release criterion
```

A criterion without evidence remains incomplete.

A scenario without a requirement may be redundant or insufficiently documented.

---

## 41. Project issue handling

`KNOWN_ISSUES.md` records unresolved defects, accepted limitations, missing evidence and release blockers that affect the active project.

Each issue should identify:

```text
ID
owner
affected files
problem
risk
validation impact
resolution criteria
```

This document is not used to track routine implementation progress. It records only facts that materially affect correctness, validation, compatibility or release.

---

## 42. Decision log

`DECISION_LOG.md` records project-specific decisions that do not require framework ADRs.

Examples:

- selected dialect;
- chosen orthography;
- module split;
- public API choice;
- accepted variant ordering;
- morphology strategy;
- deliberate incompatibility;
- gold acceptance change.

Significant decisions should record alternatives and consequences.

---

## 43. Known issues

`KNOWN_ISSUES.md` should distinguish:

```text
open defect
accepted limitation
upstream GF issue
missing coverage
documentation gap
performance concern
release blocker
```

A known issue is not automatically acceptable for release.

`RELEASE_CRITERIA.md` determines whether it blocks release.

---

## 44. Release criteria

`RELEASE_CRITERIA.md` should define the project-specific release gate.

Typical criteria:

```text
all configured checkpoints pass
all required scenarios pass
no unresolved release-blocking ledger items
no disallowed missing functions
release entrypoint loads
PGF is produced when required
PGF belongs to current source state
required golds match
known issues reviewed
documentation complete
manifest verifies
```

Release criteria must not depend only on a console statement that was not preserved.

---

## 45. Research evidence

`RESEARCH_EVIDENCE.md` should connect linguistic decisions to:

- grammars;
- dictionaries;
- corpora;
- native-speaker review;
- published references;
- upstream RGL conventions;
- issue discussions;
- evaluation evidence.

It should distinguish source evidence from project interpretation.

It should not contain copyrighted source reproductions beyond permitted excerpts.

---

## 46. Active project contract lock

Copy the template lock to:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Then replace template placeholders with real project facts.

Do not keep two competing active locks.

Template lock:

```text
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

Active lock:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

---

## 47. Required placeholder replacement

Search the active project for placeholders such as:

```text
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<PROJECT_ROOT>
<SOURCE_DIR>
<MODULE_SUFFIX>
<ENTRYPOINT>
<CHECKPOINT>
<SCENARIO>
<GOLD>
<EXPECTED_PGF>
<YYYY-MM-DD>
```

No unresolved placeholder may remain in an active normative document.

Placeholders may remain only when explicitly describing a template or generic example.

---

## 48. Active lock population

At minimum, populate contracts for:

```text
project identity
module providers and consumers
category/lincat providers
morphology providers
syntax consumers
entrypoints
checkpoints
scenario registry
scenario-to-entrypoint mapping
scenario-to-input mapping
scenario markers
scenario-to-gold mapping
expected .gfo artifacts
expected .pgf artifact
validation evidence
documentation-to-source relationships
release criteria
```

Retire or mark not applicable any template contract that does not apply.

Do not delete a contract ID and reuse it for unrelated behavior.

---

## 49. Contract completeness

Every required project contract must be:

- populated with concrete project facts;
- marked not applicable with a rationale when the contract does not apply;
- linked to its provider, consumers and validation evidence;
- free of unresolved template placeholders;
- consistent with current source, scenarios, configuration and release criteria.

A required release contract cannot remain ambiguous. Contract identifiers must not be deleted and reused for unrelated behavior.

---

## 50. Validation directory

Canonical structure:

```text
project/validation/
├── README.md
├── scenarios/
├── gold/
└── inputs/
```

This directory contains maintained validation assets.

Generated run output must not be written here.

---

## 51. Scenario registry design

Start with the minimum scenarios needed to prove the project.

Common scenario IDs:

```text
load
missing
parse
linearize
morphology
generation
```

Do not create a large scenario catalog before the project has clear requirements.

Each scenario should represent one stable purpose.

---

## 52. Required scenarios

Required scenarios are listed in:

```toml
[validation]
required_scenarios = [
  "load",
  "missing",
  "linearize",
  "parse",
]
```

The exact list is project-specific.

Required means:

- file must exist;
- configuration must resolve it;
- it must execute when selected by required modes;
- release policy evaluates its result;
- missing required gold fails when gold-backed;
- its purpose appears in `VALIDATION_SPEC.md`.

---

## 53. Optional scenarios

Optional scenarios may include:

```toml
[validation]
optional_scenarios = [
  "generation",
  "morphology",
]
```

Optional does not mean undocumented.

Optional scenarios:

- have stable IDs;
- have canonical files;
- use the same format contract;
- appear in project documentation;
- remain visible in diagnostic workflows;
- may become required later through coordinated configuration and documentation change.

---

## 54. Scenario filenames

Canonical mapping:

```text
scenario ID        → file
load               → load.gfs
parse-basic        → parse-basic.gfs
linearize          → linearize.gfs
```

Rules:

- lowercase;
- kebab-case;
- `.gfs` extension;
- filename stem equals scenario ID;
- no duplicate IDs;
- no automatic activation from directory presence alone.

---

## 55. Scenario entrypoints

For each scenario, record:

| Scenario ID | Script | Loaded entrypoint | Required | Purpose |
|---|---|---|---:|---|
| `<id>` | `validation/scenarios/<id>.gfs` | `<module>` | yes/no | `<purpose>` |

A scenario must load the documented intended entrypoint.

Loading a lower-level substitute is not equivalent to validating the release grammar.

---

## 56. Scenario format

New scenarios must follow:

```text
docs/scenarios/SCENARIO_FORMAT.md
```

Core requirements:

- UTF-8;
- stable scenario ID;
- deterministic commands;
- explicit grammar load;
- canonical begin/end markers;
- unique section IDs;
- bounded execution;
- explicit termination;
- no unauthorized shell escape;
- raw stdout/stderr preservation;
- central normalization;
- external assertion evaluation.

---

## 57. Minimal load scenario

Conceptual example:

```gf
ps "GF_WORDBENCH_BEGIN load:load-grammar"
i GrammarX
ps "GF_WORDBENCH_END load:load-grammar"

q
```

Replace `GrammarX` with the active configured entrypoint.

The real script must use commands supported by the selected GF version.

---

## 58. Scenario input assets

Store reviewed long or shared inputs under:

```text
project/validation/inputs/
```

For every input, document:

```text
path
format
encoding
line semantics
owner
consumer scenarios
stability
source evidence
```

Inputs used for release should be version-controlled.

Generated input must not silently replace canonical release input.

---

## 59. Gold files

Canonical path:

```text
project/validation/gold/<scenario-id>.gold
```

A gold file represents accepted normalized semantic output.

It is not raw GF output.

It must use the canonical schema defined by the persisted schema lock.

---

## 60. Gold-file creation

Do not write a gold file before reviewing the actual scenario.

Recommended workflow:

1. create the scenario;
2. run it;
3. inspect raw stdout;
4. inspect raw stderr;
5. inspect normalized output;
6. confirm markers and sections;
7. verify normalization did not remove meaning;
8. compare output with project requirements;
9. approve the output;
10. create or update the gold explicitly;
11. commit scenario and gold together.

A gold file must not be accepted merely because the current run produced it.

---

## 61. Missing gold policy

A required gold-backed scenario with no gold file is incomplete.

It must not:

- pass automatically;
- create its own gold silently;
- treat empty output as accepted;
- skip comparison without documentation.

Use a non-gold assertion strategy only when `VALIDATION_SPEC.md` explains why exact comparison is unsuitable.

---

## 62. Gold update policy

Normal validation is read-only.

Conceptual explicit operation:

```text
gf-wordbench gold update <scenario-id>
```

A valid update requires:

- intentional implementation or acceptance change;
- old/new raw evidence review;
- normalized diff review;
- linguistic or architectural rationale;
- validation-spec update when criteria changed;
- decision-log update for significant changes;
- contract-lock update when the relationship changed.

---

## 63. Release artifact

If release requires a PGF:

```toml
[validation]
release_requires_pgf = true
```

The project must define:

```text
release entrypoint
expected PGF filename
required concrete languages
artifact location policy
source fingerprint relationship
release scenarios
```

The exact schema belongs to the project configuration reference.

---

## 64. PGF invariants

A release PGF counts only when:

- built during the current release run;
- built from the configured entrypoint;
- source fingerprint is current;
- process completed normally;
- required artifact exists;
- artifact is non-empty;
- required release scenarios pass;
- manifest records it;
- stale artifacts are excluded.

Artifact existence alone is insufficient.

---

## 65. Initial validation phases

Do not begin with a release run on an uninitialized project.

Use progressive validation.

Recommended sequence:

```text
Phase 1 — structure
Phase 2 — configuration
Phase 3 — source inventory
Phase 4 — quick compile
Phase 5 — checkpoint validation
Phase 6 — scenario validation
Phase 7 — gold validation
Phase 8 — diagnostic run
Phase 9 — release run
```

---

## 66. Phase 1 — Structure validation

Verify:

```text
[ ] project/ exists
[ ] project/project.toml exists
[ ] project/docs/ contains every required permanent document
[ ] project/validation/ exists
[ ] scenario/gold/input directories exist
[ ] template and project relative structures match
[ ] no required template file is missing
```

Recommended conceptual command:

```text
gf-wordbench project check-structure
```

The canonical command surface belongs to the CLI reference.

---

## 67. Phase 2 — Configuration validation

Verify:

```text
[ ] schema_id is correct
[ ] schema_version is supported
[ ] project ID is valid
[ ] language code is valid
[ ] source root resolves
[ ] entrypoint list is non-empty when required
[ ] checkpoint order is valid
[ ] scenario IDs are unique
[ ] required and optional arrays do not overlap
[ ] local absolute tool paths are not stored as project facts
[ ] release_requires_pgf is explicit
```

Recommended conceptual command:

```text
gf-wordbench project check
```

---

## 68. Phase 3 — Source inventory validation

Verify:

```text
[ ] configured source selection finds intended files
[ ] module names are unique
[ ] configured entrypoints exist
[ ] configured checkpoints exist
[ ] module suffix is consistent
[ ] dependency map covers major imports
[ ] generated artifacts are not counted as sources
```

Do not continue to release planning while the source inventory is ambiguous.

---

## 69. Phase 4 — Quick validation

Run quick validation against a representative target.

Conceptual command:

```text
gf-wordbench audit --mode quick
```

Confirm:

- GF executable resolves;
- GF version is recorded;
- source target resolves;
- static scan executes;
- compile request uses the intended path;
- stdout and stderr are preserved;
- run directory is created;
- `summary.json` is produced;
- failures are structured.

Quick success does not prove project completion.

---

## 70. Phase 5 — Checkpoint validation

Run:

```text
gf-wordbench audit --mode checkpoint
```

Confirm:

- checkpoint order matches configuration;
- lower-level providers validate before consumers;
- configured checkpoint scenarios execute;
- direct/downstream relationships are interpretable;
- evidence paths exist;
- unresolved checkpoint defects are recorded in `KNOWN_ISSUES.md`.

---

## 71. Phase 6 — Scenario validation

Before enabling a scenario as required:

```text
[ ] Scenario ID is registered
[ ] File exists
[ ] Entrypoint matches project documentation
[ ] Commands are supported
[ ] Markers are canonical
[ ] Sections are unique
[ ] Timeout is finite
[ ] Output is bounded
[ ] Security check passes
[ ] Raw output is preserved
[ ] Assertion strategy is defined
```

Use scenario-specific validation before release.

---

## 72. Phase 7 — Gold validation

For each gold-backed scenario:

```text
[ ] Actual normalized output exists
[ ] Gold file exists
[ ] Scenario ID matches
[ ] Normalization version matches
[ ] Section identities match
[ ] Semantic differences are reviewed
[ ] Normal validation leaves gold unchanged
```

A normalization-version change requires review of all affected gold files.

---

## 73. Phase 8 — Diagnostic validation

Run:

```text
gf-wordbench audit --mode diagnostic
```

Use this phase to identify:

- broad source failures;
- missing project facts;
- unregistered scenarios;
- unsupported commands;
- incomplete gold coverage;
- direct/downstream ambiguity;
- output-size problems;
- timeout risks;
- incomplete documentation;
- stale assumptions.

Diagnostic mode may produce more evidence.

It does not weaken success criteria.

---

## 74. Phase 9 — Release validation

Run:

```text
gf-wordbench audit --mode release
```

Release validation requires:

```text
[ ] Project schema valid
[ ] Required documents complete
[ ] Contract lock active
[ ] Required checkpoints pass
[ ] Required scenarios pass
[ ] Required golds match
[ ] Missing functions satisfy policy
[ ] Release entrypoint validates
[ ] PGF produced when required
[ ] PGF belongs to current source state
[ ] Manifest verifies
[ ] Release criteria pass
[ ] No unresolved release-blocking known issue
```

---

## 75. Project activation

A copied template becomes the active project only after:

- identity fields are populated;
- active source root is configured;
- placeholders are removed from authoritative files;
- required path references resolve;
- at least one intended entrypoint is configured;
- project structure validation passes;
- no old-language identity remains active.

A template copy with unresolved required placeholders is not an active project.

---

## 76. Projects without release assets

A newly initialized project may exist before it has gold files, a PGF or complete release coverage.

In that condition:

- the project structure and `project.toml` must still be valid;
- at least one intended entrypoint must be configured;
- missing release assets must be recorded in `KNOWN_ISSUES.md` when they block validation or release;
- project documents must describe only modules and contracts that exist;
- release validation must fail when a required asset or criterion is absent.

The project becomes release-ready only by satisfying `RELEASE_CRITERIA.md`; no lifecycle label changes the underlying evidence.

---

## 77. Removing old-language identity

When starting from a copied active project instead of the generic template, search for:

```text
old project ID
old language name
old language code
old module suffix
old entrypoints
old source paths
old scenarios
old gold IDs
old PGF name
old report paths
```

Remove or migrate every active occurrence.

Historical migration notes may retain old names when clearly labeled.

Old identity must not remain in:

- active configuration;
- active scenario markers;
- active gold headers;
- active contract entries;
- current architecture diagrams;
- release criteria.

---

## 78. Placeholder scan

Recommended conceptual command:

```text
gf-wordbench project check --placeholders
```

The check should search active project text assets for:

```text
<UPPERCASE_PLACEHOLDER>
TODO
TBD
REPLACE_ME
EXAMPLE_ONLY
```

Not every `TODO` is automatically invalid, but every occurrence must be reviewed.

Strict release mode should reject unresolved normative placeholders.

---

## 79. Project/template synchronization

The active project and template should share required relative paths.

They should not share active content.

When a new permanent project document is added:

```text
[ ] Add generic template file
[ ] Add or migrate active project file
[ ] Update DOCUMENTATION_MAP.md
[ ] Update project structure checks
[ ] Update creation guide
[ ] Update completion checklist
```

Do not add an active-only structural requirement without updating the template contract.

---

## 80. Version control

Project-maintained assets should be version-controlled:

```text
project/project.toml
project/README.md
project/docs/
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

Generated run directories should follow repository ignore and retention policy.

Before committing a new project:

```text
[ ] No local absolute tool paths committed
[ ] No secrets committed
[ ] No generated run artifacts committed accidentally
[ ] No stale .gfo/.pgf treated as source
[ ] Gold changes reviewed
[ ] Project identity reviewed
```

---

## 81. Security review

A new project must review:

- scenario shell escape;
- untrusted input paths;
- operating-system commands;
- network dependencies;
- absolute path leakage;
- secret environment values;
- output bounds;
- generation bounds;
- executable source;
- writable project assets during validation.

`.gfs` files are executable input.

Do not execute unreviewed scenarios from untrusted sources.

---

## 82. Portability review

Test the project with:

- paths containing spaces;
- project-relative paths;
- UTF-8 language data;
- explicit GF executable;
- explicit RGL root;
- clean output root;
- no dependency on GUI state;
- no dependency on developer current directory.

A portable project does not require editing `project.toml` for every developer's machine paths.

---

## 83. Determinism review

Confirm:

- source selection order is deterministic;
- checkpoint order comes from configuration;
- scenario order comes from configuration;
- entrypoint order remains declared order;
- gold sections follow scenario order;
- generated report ordering is stable;
- no scenario depends on previous process state;
- no random generation is used for exact gold without a controlled policy.

---

## 84. Common failure: copying only `project.toml`

Problem:

```text
project.toml exists
project docs and validation assets are missing
```

Why invalid:

- configuration has no reviewed architecture;
- scenarios may be absent;
- contract lock is absent;
- release criteria are undefined.

Fix:

Copy the complete template structure.

---

## 85. Common failure: treating GUI state as project identity

Problem:

```text
GUI remembers a language directory
project.toml is incomplete or contradictory
```

Why invalid:

- state is local and disposable;
- automation cannot reproduce the project;
- cloned repositories may load a different language.

Fix:

Put authoritative project facts in `project/project.toml`.

---

## 86. Common failure: using a stale run to infer identity

Problem:

```text
old run directory contains previous language names
new project inherits them implicitly
```

Why invalid:

- run directories are evidence, not configuration;
- historical output may belong to another project state.

Fix:

Initialize identity explicitly and remove old active references.

---

## 87. Common failure: using every `.gf` file as an entrypoint

Problem:

- configuration becomes noisy;
- release intent is unclear;
- lower-level modules are mistaken for release-grammar proofs.

Fix:

Use source selection for files, checkpoints for layers and entrypoints for top-level grammar/API targets.

---

## 88. Common failure: no checkpoint design

Problem:

- failures appear only at the release grammar;
- dependency cascades are harder to classify;
- failure localization becomes unnecessarily difficult.

Fix:

Define a small number of meaningful dependency-layer checkpoints.

---

## 89. Common failure: writing gold first

Problem:

- expected output is invented before actual GF behavior is reviewed;
- gold may encode an assumption instead of accepted evidence.

Fix:

Run, inspect raw evidence, normalize, review and then explicitly approve gold.

---

## 90. Common failure: accepting current output automatically

Problem:

```text
implementation produces output
output is copied to gold without review
```

Why invalid:

- a bug becomes accepted behavior;
- regression tests lose independent value.

Fix:

Review against `VALIDATION_SPEC.md`, linguistic evidence and project decisions.

---

## 91. Common failure: copying active language facts into template

Problem:

```text
templates/project/ contains current language names and module paths
```

Why invalid:

- subsequent projects inherit false assumptions;
- template ceases to be reusable.

Fix:

Keep active facts only under `project/`.

---

## 92. Common failure: project paths contain developer-machine absolutes

Problem:

```toml
gf_executable = "C:\\Users\\..."
rgl_root = "D:\\..."
```

Why invalid:

- repository is not portable;
- another developer cannot load it;
- machine configuration becomes project identity.

Fix:

Move local tool paths to environment or application state.

---

## 93. Common failure: scenario exists but is unregistered

Problem:

```text
project/validation/scenarios/test.gfs
```

exists but does not appear in `project.toml`.

Result:

- it is not canonical active evidence;
- release behavior is ambiguous.

Fix:

Register it as required or optional, or remove it.

---

## 94. Common failure: required scenario has no documented purpose

Problem:

- release runs a script;
- no project requirement explains what it proves.

Fix:

Document it in:

```text
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
INTERFILE_CONTRACT_LOCK.md
```

---

## 95. Common failure: missing required gold auto-passes

Problem:

- comparison is skipped because no gold exists;
- release appears successful.

Fix:

A missing required gold is a project failure.

---

## 96. Common failure: stale PGF accepted

Problem:

- old `.pgf` remains in an output directory;
- current build fails;
- stale file is still reported.

Fix:

Use current-run artifact proof, source fingerprint and manifest verification.

---

## 97. Common failure: unresolved placeholders in active lock

Problem:

```text
<ENTRYPOINT>
<SCENARIO>
<EXPECTED_PGF>
```

remain in an active normative file.

Fix:

Replace with real facts or mark the contract not applicable with an explicit rationale.

---

## 98. Common failure: documentation references nonexistent modules

Problem:

- architecture names a module that is absent from the source tree;
- configuration or scenarios reference that module;
- validation cannot resolve the documented dependency.

Fix:

Remove the invalid reference or add the required module and its contracts before integration. Project documentation must describe the actual source architecture.

---

## 99. Common failure: module suffix disagreement

Problem:

```text
project.toml uses X
source modules use Y
scenarios load Z
```

Fix:

Choose one active suffix and migrate configuration, source, scenarios, golds and docs together.

---

## 100. Common failure: release criteria are generic only

Problem:

```text
“Tests pass”
```

does not define project readiness.

Fix:

State concrete project-specific gates, artifacts, scenarios, known-issue policy and missing-function policy.

---

## 101. Creation review roles

Recommended review roles:

| Role | Responsibility |
|---|---|
| Project owner | Approves identity and scope |
| GF maintainer | Confirms module and entrypoint facts |
| Linguistic reviewer | Reviews language expectations and golds |
| Framework maintainer | Reviews schema and integration contracts |
| Release reviewer | Confirms release criteria and evidence |

One person may hold multiple roles.

The responsibilities should still be explicit.

---

## 102. Project initialization record

The project should record initialization in `DECISION_LOG.md` or an equivalent project record.

Suggested fields:

```text
Date
Project ID
Language
Language code
Module suffix
Source root
Primary entrypoint
Initial checkpoints
Initial required scenarios
Initial optional scenarios
GF versions
Project owner
Known bootstrap gaps
```

This is not a replacement for `project.toml`.

---

## 103. Definition of structurally created

A project is structurally created when:

```text
[ ] Complete template copied
[ ] project.toml parses
[ ] Schema identity/version valid
[ ] Project ID assigned
[ ] Language identity assigned
[ ] Source root assigned
[ ] Required relative directories exist
[ ] Active lock exists
[ ] No unsafe overwrite occurred
```

This does not mean validation-complete.

---

## 104. Definition of integrated

A project is integrated when:

```text
[ ] Source inventory resolves
[ ] Module suffix is consistent
[ ] Entrypoints resolve
[ ] Checkpoints resolve
[ ] GF path resolves
[ ] Required scenarios resolve
[ ] Project docs describe actual source
[ ] Quick validation produces structured evidence
```

This does not mean release-ready.

---

## 105. Definition of validation-complete

A project is validation-complete when:

```text
[ ] Required scenario purposes are documented
[ ] Required scenarios execute
[ ] Required golds exist or explicit alternatives are defined
[ ] Coverage matrix maps requirements to evidence
[ ] Checkpoint validation works
[ ] Diagnostic run works
[ ] Raw evidence and reports are preserved
```

---

## 106. Definition of release-ready

A project is release-ready only when:

```text
[ ] Release criteria all pass
[ ] Release run completes
[ ] Required checkpoints pass
[ ] Required scenarios pass
[ ] Required golds match
[ ] Required PGF exists and verifies
[ ] Current source fingerprint is linked
[ ] Manifest verifies
[ ] No unresolved release blocker remains
[ ] Project documents are current
[ ] Active lock contains no unresolved placeholders
```

---

## 107. Recommended project checks

Conceptual commands:

```text
gf-wordbench project check-structure
gf-wordbench project check
gf-wordbench project contracts check
gf-wordbench scenarios check
gf-wordbench normalization check
gf-wordbench audit --mode quick
gf-wordbench audit --mode checkpoint
gf-wordbench audit --mode diagnostic
gf-wordbench audit --mode release
```

Strict variants should be used before release.

The canonical commands are defined in `CLI_REFERENCE.md`.

---

## 108. Minimum viable active project

A minimum active, non-release project needs:

```text
valid project.toml
active language identity
resolvable source root
at least one source file
at least one intended entrypoint or documented bootstrap gap
project README
language overview
architecture
dependency map
validation specification
active project lock
validation directory structure
```

A project may begin without gold files only when no required gold-backed scenario is active yet.

---

## 109. Minimum release-capable project

A release-capable project needs, in addition:

```text
configured release entrypoint
configured checkpoints
required scenarios
scenario inputs
reviewed required golds
missing-function policy
release criteria
expected PGF definition
clean artifact build
manifest verification
no unresolved release blocker
```

---

## 110. Project creation checklist

```text
[ ] Back up existing project/
[ ] Copy templates/project/ to project/
[ ] Validate project/template path inventory
[ ] Assign project ID
[ ] Assign display name
[ ] Assign language code
[ ] Assign module suffix
[ ] Configure source root
[ ] Configure source glob
[ ] Inventory GF modules
[ ] Select entrypoints
[ ] Select checkpoints
[ ] Resolve GF path components
[ ] Record supported GF versions
[ ] Complete project README
[ ] Complete language overview
[ ] Complete language architecture
[ ] Complete dependency map
[ ] Complete category/lincat contract
[ ] Complete morphology specification
[ ] Complete syntax/constructor rules
[ ] Complete validation specification
[ ] Complete coverage matrix
[ ] Complete decision log
[ ] Complete known issues
[ ] Complete release criteria
[ ] Complete research evidence
[ ] Populate active interfile contract lock
[ ] Register required scenarios
[ ] Register optional scenarios
[ ] Create scenario files
[ ] Review scenario security
[ ] Create validation inputs
[ ] Execute scenarios
[ ] Review raw evidence
[ ] Approve required gold files
[ ] Define PGF artifact when required
[ ] Remove old-language identity
[ ] Remove unresolved placeholders
[ ] Run project checks
[ ] Run quick validation
[ ] Run checkpoint validation
[ ] Run diagnostic validation
[ ] Run release validation
[ ] Verify manifest
[ ] Commit project assets
```

---

## 111. Project creation change unit

Creating the project is one coordinated change unit involving:

```text
project/project.toml
project/README.md
project/docs/
project/validation/
GF source entrypoints
scenario files
gold files
release policy
```

Do not merge a project configuration that references nonexistent required assets.

---

## 112. Automation expectations

The project initializer and checker verify mechanically:

1. template inventory exists;
2. project inventory exists;
3. required relative paths match;
4. schema parses;
5. identity values are valid;
6. source root resolves;
7. entrypoints resolve;
8. checkpoints resolve;
9. scenario IDs are unique;
10. scenario files map one-to-one;
11. required golds exist;
12. placeholders are absent in strict mode;
13. active/template content separation holds;
14. no project-local secret values are present;
15. project documents link to existing files.

Automation cannot decide whether linguistic expectations are correct.

Human review remains required.

---

## 113. Project creation and migration distinction

Use project creation when:

- the active project does not yet exist;
- the template is the correct starting point;
- no historical project contract must be preserved.

Use migration when:

- an existing GF Audit project has historical state;
- old report schemas must remain readable;
- module names or suffixes are changing;
- active gold files already exist;
- published runs refer to old IDs;
- project identity already has external consumers.

See:

```text
docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md
```

---

## 114. Project creation and cloning distinction

Use project creation for a new identity.

Use cloning/resetting when:

- duplicating the full repository for another active language;
- removing old active-language facts;
- intentionally preserving framework setup;
- initializing from another completed repository copy.

See:

```text
docs/projects/CLONING_AND_RESETTING.md
```

A clone still requires a new active project identity and a full old-language scan.

---

## 115. Framework/project separation

Framework files:

```text
app/
tests/
docs/
templates/
```

Active-language files:

```text
project/
language GF source tree
```

Framework documentation may describe examples.

It must not contain hidden active-language defaults.

Project documents may contain real module names.

They must not redefine framework Python architecture.

`gf-portfolio` remains outside both boundaries. It may consume public versioned Wordbench artifacts, but project creation must not write Portfolio state or create a Wordbench dependency on Portfolio.

---

## 116. Project review questions

Before declaring the project active, answer:

```text
What is the one authoritative project ID?
What is the one authoritative language code?
What is the module suffix?
Where are source files selected?
Which modules are true entrypoints?
Which modules are checkpoints?
Which scenarios are required?
Which scenarios are optional?
Which inputs are canonical?
Which golds are required?
Which missing functions are acceptable?
Which artifact proves release?
Which known issues block release?
Which required project contracts are satisfied by current evidence?
Can another developer reproduce the project without GUI state?
```

Every answer must point to an authoritative file.

---

## 117. Related documents

### Project lifecycle

- `docs/projects/PROJECT_MODEL.md`
- `docs/projects/CLONING_AND_RESETTING.md`
- `docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md`
- `docs/projects/PROJECT_COMPLETION_CHECKLIST.md`

### Configuration

- `docs/configuration/CONFIGURATION_OVERVIEW.md`
- `docs/configuration/PROJECT_TOML_REFERENCE.md`
- `docs/configuration/ENVIRONMENT_AND_PATHS.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`

### Scenarios and validation

- `docs/scenarios/SCENARIO_FORMAT.md`
- `docs/scenarios/WRITING_GFS_SCENARIOS.md`
- `docs/scenarios/GOLDEN_TESTS.md`
- `docs/scenarios/UPDATING_GOLD_FILES.md`
- `docs/validation/VALIDATION_MODES.md`
- `docs/validation/RELEASE_GATES.md`

### GF and diagnostics

- `docs/gf/GF_PATH_RESOLUTION.md`
- `docs/gf/GF_COMPILATION.md`
- `docs/gf/GF_PGF_BUILD.md`
- `docs/gf/GF_VERSION_COMPATIBILITY.md`
- `docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md`

### Active project

- `project/README.md`
- `project/project.toml`
- `project/docs/00_PROJECT_START_HERE__PROJECT_DOCS.md`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`
- `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md`
- `project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md`
- `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md`

---

## 118. Enforcement rule

Creating a GF Wordbench project is the act of making one language identity, one source architecture and one validation policy reproducible.

Therefore:

> A project is not complete while its identity, entrypoints, checkpoints, scenarios, golds, contracts or release criteria exist only as assumptions.

Every active fact must have one authoritative owner, every required behavior must have evidence, and every required template placeholder must be resolved before release.
