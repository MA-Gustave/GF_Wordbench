# GF Wordbench Project Template — Start Here

**Document ID:** `GF-WB-TEMPLATE-PROJECT-START`  
**Status:** Normative template onboarding guide  
**Template version:** `2.0.0`  
**Applies to:** A new active GF language project initialized from `templates/project/`  
**Template owner:** GF Wordbench maintainers  
**Project owner after initialization:** `<PROJECT_OWNER>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**GF module suffix:** `<GF_SUFFIX>`  
**Last reviewed:** `<YYYY-MM-DD>`  
**Target path:** `templates/project/docs/00_PROJECT_START_HERE__TEMPLATES_PROJECT_DOCS.md`

---

## 1. Purpose

This is the first document to read when creating an active GF language project from the GF Wordbench project template.

It explains:

- what belongs in the reusable template;
- what belongs in the active project;
- which file owns each project fact;
- how to establish project identity;
- how to inventory GF source modules;
- how to define entrypoints and checkpoints;
- how to document project contracts;
- how to register native `.gfs` scenarios;
- how to manage reviewed gold files;
- how to establish reproducible validation evidence;
- how to prepare a release PGF and artifact manifest;
- how to keep the project independent from machine-local configuration and `gf-portfolio`.

This file is not a linguistic specification.

It is the operational entrypoint for turning the reusable project template into one real GF language project.

---

## 2. Core rules

> Define one authoritative project identity, then make configuration, source, documentation, scenarios, golds, entrypoints, checkpoints, and release artifacts agree with it.

A project initialization is one coordinated change across:

```text
project.toml
GF source modules
project documentation
validation scenarios
validation inputs
gold files
entrypoints
checkpoints
release artifacts
```

Do not initialize these areas independently.

Additional rules:

1. one GF Wordbench workspace contains one active GF language project;
2. `project/project.toml` owns machine-readable project identity and registries;
3. project documentation owns language-specific design and contracts;
4. machine-local paths remain outside portable project configuration;
5. normal validation never modifies scenarios, inputs, or golds;
6. GF remains authoritative for grammar parsing, typing, compilation, and runtime behavior;
7. `gf-portfolio` may consume public Wordbench artifacts but is not part of project initialization.

---

## 3. Template and active project

GF Wordbench contains two distinct project trees.

### 3.1 Reusable template

```text
templates/project/
```

Purpose:

- initialize future projects;
- retain generic placeholders;
- remain language-neutral;
- define required structure;
- provide reusable instructions;
- provide empty validation directories;
- provide generic contract templates.

### 3.2 Active project

```text
project/
```

Purpose:

- represent one real language project;
- contain concrete identity values;
- define active GF source configuration;
- define entrypoints and checkpoints;
- contain project documentation;
- contain active scenarios, inputs, and golds;
- define release criteria and expected artifacts.

The template is not an active project.

The active project must not retain unresolved required placeholders.

---

## 4. Reusable-template invariants

Files under:

```text
templates/project/
```

must not contain:

- a real active-language name;
- an active language code;
- an active GF suffix;
- active module names;
- a developer username;
- a local repository path;
- a local RGL path;
- a local GF executable path;
- a local output root;
- application state;
- run directories;
- generated `.gfo` files;
- generated `.pgf` files;
- active-project scenarios presented as current;
- active-project gold output;
- active-project decisions;
- active-project known issues;
- Portfolio registry identifiers;
- claims that a real project passed validation.

The template may contain documented placeholders such as:

```text
<PROJECT_ID>
<PROJECT_NAME>
<PROJECT_OWNER>
<PROJECT_VERSION>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<SOURCE_DIR>
<SOURCE_GLOB>
<ABSTRACT_ENTRYPOINT>
<CONCRETE_ENTRYPOINT>
<SYNTAX_ENTRYPOINT>
<LANGUAGE_ENTRYPOINT>
<API_ENTRYPOINT_OR_NONE>
<RELEASE_ENTRYPOINT>
<EXPECTED_PGF>
<NORMALIZATION_VERSION>
<YYYY-MM-DD>
```

Each placeholder has one meaning.

Do not create several placeholders for the same project fact.

---

## 5. Active-project invariants

After copying the template into:

```text
project/
```

replace every required placeholder with a concrete project value.

The active project must not contain declarations such as:

```text
<ENTRYPOINT>
option A | option B
choose later
temporary placeholder
```

For an optional concept that does not apply, use an explicit value defined by the owning schema or document, such as:

```text
None
Not applicable
[]
```

Do not use implementation-status labels to compensate for missing project decisions.

When a required fact is not yet known, resolve the fact before treating the project as configured.

---

## 6. Project identity

Define project identity before editing source architecture or validation assets.

Required identity values:

| Field | Value |
|---|---|
| Project ID | `<PROJECT_ID>` |
| Project display name | `<PROJECT_NAME>` |
| Project version | `<PROJECT_VERSION>` |
| Project owner | `<PROJECT_OWNER>` |
| Language name | `<LANGUAGE_NAME>` |
| Language code | `<LANGUAGE_CODE>` |
| GF suffix | `<GF_SUFFIX>` |
| Source directory | `<SOURCE_DIR>` |
| Source glob | `<SOURCE_GLOB>` |
| Release entrypoint | `<RELEASE_ENTRYPOINT>` |
| Expected PGF | `<EXPECTED_PGF>` |

Identity must be coherent enough to name and resolve:

- GF modules;
- source roots;
- scenarios;
- report subjects;
- release artifacts;
- project documentation;
- public exported artifacts.

Changing the project ID, language code, or GF suffix after source and validation assets depend on them requires a coordinated migration.

---

## 7. Authoritative configuration

The authoritative project configuration is:

```text
project/project.toml
```

It owns or resolves:

```text
project ID
project display name
project version
language name
language code
GF module suffix
source directory
source selection
GF path additions
entrypoints
checkpoints
required scenarios
optional scenarios
release entrypoint
expected release artifacts
```

Do not keep machine-readable project facts only in prose.

Documentation explains project meaning and design.

`project.toml` supplies project facts to GF Wordbench.

Exact fields and schema behavior belong to:

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/PERSISTED_SCHEMA_LOCK.md
```

---

## 8. Machine-local values

Do not store these machine-local values in portable project configuration:

```text
GF executable
RGL installation root
output root
application-state path
developer home directory
absolute workspace path
temporary directory
editor path
Portfolio installation path
```

These values belong to:

- explicit CLI or GUI input;
- supported local environment configuration;
- disposable application state;
- resolved run configuration.

Project-owned paths are relative to the project root unless the project model explicitly defines a controlled external source relationship.

---

## 9. Canonical project layout

The initialized project follows this structure:

```text
project/
├── README.md
├── project.toml
├── docs/
│   ├── 00_PROJECT_START_HERE__TEMPLATES_PROJECT_DOCS.md
│   ├── INTERFILE_CONTRACT_LOCK.md
│   ├── LANGUAGE_OVERVIEW.md
│   ├── LANGUAGE_ARCHITECTURE.md
│   ├── MODULE_DEPENDENCY_MAP.md
│   ├── CATEGORY_AND_LINCAT_CONTRACT.md
│   ├── MORPHOLOGY_SPEC.md
│   ├── SYNTAX_AND_CONSTRUCTOR_RULES.md
│   ├── VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md
│   ├── TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md
│   ├── DECISION_LOG.md
│   ├── KNOWN_ISSUES.md
│   ├── RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md
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

The active GF source directory is configured by `project.toml`.

It may be:

- inside `project/`; or
- outside `project/` through a documented and validated source-root relationship.

The configured path remains authoritative.

---

## 10. Document ownership map

Each project document has one primary purpose.

| Document | Primary purpose |
|---|---|
| `README.md` | Concise project identity and navigation |
| `00_PROJECT_START_HERE__TEMPLATES_PROJECT_DOCS.md` | Initialization and project onboarding |
| `LANGUAGE_OVERVIEW.md` | Linguistic scope, target language, orthography, and intended use |
| `LANGUAGE_ARCHITECTURE.md` | GF module responsibilities and project architecture |
| `MODULE_DEPENDENCY_MAP.md` | Exact GF provider, consumer, and import graph |
| `CATEGORY_AND_LINCAT_CONTRACT.md` | Public categories, lincats, parameters, and invariants |
| `MORPHOLOGY_SPEC.md` | Paradigms, inflectional domains, and morphology rules |
| `SYNTAX_AND_CONSTRUCTOR_RULES.md` | Syntax, constructors, agreement, and word-order rules |
| `VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md` | Required validation behavior and scenario contracts |
| `TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md` | Feature-to-test and feature-to-evidence mapping |
| `DECISION_LOG.md` | Deliberate linguistic and architectural decisions |
| `KNOWN_ISSUES.md` | Confirmed issues, limitations, risks, and evidence gaps |
| `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md` | Project release gates |
| `RESEARCH_EVIDENCE.md` | Sources supporting linguistic decisions |
| `INTERFILE_CONTRACT_LOCK.md` | Cross-file project contracts |

Do not make several documents authoritative for the same fact.

Cross-reference the owner document.

---

## 11. Initialization sequence

Use this order:

```text
1. copy and protect
2. define project identity
3. configure project.toml
4. inventory GF source
5. define module architecture
6. define public contracts
7. register entrypoints and checkpoints
8. configure scenarios, inputs, and golds
9. establish a reproducible baseline
10. resolve root issues
11. establish release evidence
```

Skipping directly to broad release validation usually creates ambiguous failures.

---

# Part I — Copy and protect

## 12. Copy the template

Copy:

```text
templates/project/
```

to:

```text
project/
```

through the project initialization workflow.

Do not edit `templates/project/` as if it were the active project.

The template-to-project direction is one-way during initialization:

```text
templates/project/
    → project/
```

---

## 13. Preserve existing work

When migrating an existing language project:

- do not overwrite source files automatically;
- use version control or a verified archive;
- inventory existing modules;
- preserve existing scenarios and inputs;
- preserve reviewed gold files;
- preserve relevant historical evidence;
- record migration decisions;
- identify schema or naming transformations.

Project reset and project migration are different operations.

Use migration when existing project meaning must survive.

---

## 14. Remove stale generated artifacts

An initialized active project must not begin with stale generated evidence under source-owned directories.

Remove or relocate stale:

```text
.gfo
.pgf
summary.json
manifest.json
temporary logs
normalized output
run_<run-id>/
```

Generated artifacts belong to controlled run directories.

Do not delete source-owned gold files during generated-evidence cleanup.

---

## 15. Confirm a recoverable working state

Before editing project identity:

```text
[ ] project source is preserved
[ ] reusable template is preserved
[ ] generated artifacts are distinguishable from source
[ ] version-control state is understood
[ ] archive or rollback material exists when replacement is destructive
[ ] external GF source roots are identified
```

---

# Part II — Identity and configuration

## 16. Configure `project.toml`

Populate the authoritative project values before changing the rest of the project documentation.

Resolve, as applicable:

```text
project.id
project.name
project.version
project.language_name
project.language_code
project.gf_suffix
sources.directory
sources.glob
modules.entrypoints
modules.checkpoints
gf.path_parts
validation.required_scenarios
validation.optional_scenarios
release.entrypoint
release.expected_artifacts
```

Exact names belong to the project schema reference.

Do not invent fields in this guide.

---

## 17. Use portable paths

Correct portable project path:

```toml
directory = "lib/src/<language-directory>"
```

Incorrect portable project path:

```toml
directory = "C:/Users/name/workspace/lib/src/language"
```

When the GF source tree is external, represent the relationship through the approved configuration model and local environment resolution.

Do not embed one developer's absolute source root in the reusable project.

---

## 18. Define one GF suffix

Every suffix-dependent active concrete module must agree with:

```text
<GF_SUFFIX>
```

Illustrative derived names:

```text
Res<GF_SUFFIX>.gf
Noun<GF_SUFFIX>.gf
Grammar<GF_SUFFIX>.gf
Lang<GF_SUFFIX>.gf
```

These examples do not require those exact files.

The source inventory determines which modules exist.

---

## 19. Define entrypoint roles

Do not provide one unordered list without semantics.

Distinguish, where applicable:

```text
abstract entrypoint
concrete grammar entrypoint
syntax entrypoint
language composition entrypoint
API entrypoint
diagnostic aggregate entrypoint
release PGF entrypoint
```

One module may fill more than one role only when that relationship is documented.

The release entrypoint is explicit.

It must not be guessed from the most recently compiled module.

---

## 20. Define checkpoints

Checkpoints are ordered project-defined validation surfaces.

A common progression is:

```text
resources and parameters
    → morphology
    → categories and paradigms
    → core syntax
    → structural and extension modules
    → grammar entrypoint
    → language or API entrypoint
    → release entrypoint
```

Use only checkpoints that exist in the project architecture.

Checkpoint order comes from project configuration, not CLI argument order.

---

# Part III — Source inventory

## 21. Build the source inventory

For every active `.gf` file, record:

```text
path
module name
module kind
responsibility
direct imports
direct consumers
checkpoint role
entrypoint role
release relevance
```

The authoritative detailed location is:

```text
project/docs/MODULE_DEPENDENCY_MAP.md
```

Do not maintain a separate implementation-state column.

The inventory describes the project that exists and the contracts it must satisfy.

---

## 22. Validate filename and module identity

A file named:

```text
Foo<GF_SUFFIX>.gf
```

must declare the expected GF module identity unless a deliberate exception is documented.

Check:

- filename;
- GF module declaration;
- suffix;
- module kind;
- import targets;
- source selection;
- entrypoint registration.

---

## 23. Classify module responsibilities

Useful responsibility categories include:

```text
abstract API
resource
interface
instance
parameter domain
morphology
paradigm
category implementation
syntax
structural vocabulary
extension
lexicon
helper
grammar entrypoint
language entrypoint
API entrypoint
release aggregate
```

Use categories that match the actual source tree.

Do not create empty modules only to fill a template category.

---

## 24. Resolve orphan files

Review a file when it is:

- not selected by the source configuration;
- imported by no active consumer;
- absent from the dependency map;
- excluded by a stale pattern;
- a duplicate or backup file;
- generated rather than authored;
- an old module left on an active source path.

An intentional standalone module must have a documented role.

---

## 25. Resolve missing references

Configuration drift exists when:

- `project.toml` names an absent module;
- a checkpoint does not exist;
- a scenario loads an absent entrypoint;
- a gold file references an unknown scenario;
- release configuration names an absent artifact;
- documentation names a module no longer in the source tree.

Resolve configuration drift before broad validation.

---

# Part IV — Architecture and contracts

## 26. Complete `LANGUAGE_OVERVIEW.md`

Document:

```text
language identity
dialect or standard
orthography
linguistic scope
supported domains
excluded domains
RGL relationship
intended users
release purpose
```

Do not claim linguistic coverage that source and validation evidence do not support.

---

## 27. Complete `LANGUAGE_ARCHITECTURE.md`

Define the real module ownership model.

A common conceptual order is:

```text
abstract API
parameters and resources
morphology
category implementations
syntax
structural vocabulary
extensions
lexicon
entrypoints
validation and release
```

The physical graph may differ.

Document the project that is actually configured.

---

## 28. Complete `MODULE_DEPENDENCY_MAP.md`

For every public relationship, identify:

```text
provider
consumer
import direction
public symbols or assumptions
affected scenarios
validation evidence
```

Circular imports are prohibited.

Lower-level modules must not import top-level entrypoints merely to obtain a helper.

---

## 29. Complete `CATEGORY_AND_LINCAT_CONTRACT.md`

For every public concrete category, document:

```text
provider module
lincat shape
public fields
parameter domains
table indices
construction invariants
direct consumers
validation evidence
```

A consumer must not depend on an undocumented field.

A lincat change is a coordinated provider-consumer contract change.

---

## 30. Complete `MORPHOLOGY_SPEC.md`

Document only distinctions required or intentionally supported by the project.

Examples may include:

```text
number
gender
case
definiteness
person
tense
anteriority
polarity
verb form
adjective agreement
pronoun form
clitic form
inflection class
```

Do not invent distinctions to fill the template.

For excluded linguistic domains, state the project boundary directly.

---

## 31. Complete `SYNTAX_AND_CONSTRUCTOR_RULES.md`

Document:

```text
phrase composition
word order
agreement
case selection
valency
clitic placement
tense and polarity composition
question formation
relative clauses
coordination
subordination
punctuation
variation
```

Identify the owning module or contract for each rule.

---

## 32. Customize the project contract lock

Update:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Populate project identity and register stable project contracts using project contract IDs such as:

```text
PIFC-CONFIG-...
PIFC-MODULE-...
PIFC-LINCAT-...
PIFC-HELPER-...
PIFC-ENTRY-...
PIFC-SCENARIO-...
PIFC-GOLD-...
PIFC-ARTIFACT-...
PIFC-DOC-...
PIFC-RELEASE-...
```

Each contract identifies:

```text
owner
provider
consumers
inputs
outputs
invariants
evidence
coordinated changes
```

Do not add implementation-status labels to project contracts.

---

## 33. Record project decisions

Use:

```text
project/docs/DECISION_LOG.md
```

for deliberate choices between meaningful alternatives.

Examples:

- lincat representation;
- parameter domains;
- case strategy;
- clitic strategy;
- word-order strategy;
- entrypoint layout;
- source-root relationship;
- accepted linguistic limitation;
- module rename;
- normalization change.

A decision record explains what governs the project.

It does not track coding progress.

---

## 34. Record known issues

Use:

```text
project/docs/KNOWN_ISSUES.md
```

for confirmed defects, limitations, risks, or evidence gaps that affect project behavior or release evaluation.

Each issue should include:

```text
issue ID
affected area
evidence
reproduction
expected behavior
observed behavior
impact
resolution criteria
owner
```

Do not create issue entries merely to track ordinary implementation progress.

---

# Part V — Validation configuration

## 35. Validation asset layout

Use:

```text
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

Normal validation reads these assets.

It does not modify them.

---

## 36. Scenario registry

Every scenario has:

```text
unique scenario ID
script path
required or optional role
entrypoint
operation scope
timeout class
expected markers
assertions
input references
normalization version
gold requirement
expected artifacts
```

The machine-readable registry belongs to `project.toml`.

Detailed behavior belongs to `VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md`.

---

## 37. Scenario families

Select scenario families required by the project.

Common families include:

```text
grammar load
missing linearizations
linearization
parsing
bounded generation
morphology
grammar introspection
PGF-facing behavior
```

A successful compile alone does not prove runtime grammar behavior.

---

## 38. Native `.gfs` scenarios

Scenarios remain native GF shell scripts.

They must be:

- UTF-8;
- project-owned;
- deterministic;
- bounded;
- explicit about the loaded entrypoint;
- free of unauthorized host-shell execution;
- compatible with the supported GF profile;
- structured for marker, assertion, and normalization checks.

Python orchestrates GF execution and evaluates observable results.

Python does not reimplement scenario logic.

---

## 39. Validation inputs

Input files contain stable project test data.

They must not contain:

- machine-local absolute paths;
- secrets;
- uncontrolled random input;
- environment-dependent text unless explicitly normalized;
- hidden executable instructions outside the scenario contract.

Each input has one owning scenario or documented consumer set.

---

## 40. Gold files

Gold files are reviewed normalized expectations.

Rules:

- one authoritative gold per scenario variant;
- scenario ID agrees with the registry;
- normalization version agrees with the scenario;
- UTF-8 encoding;
- canonical line endings;
- no automatic update during normal validation;
- deliberate review before replacement;
- old and new evidence remain inspectable during an update.

A missing required gold is a validation failure.

It is not an instruction to create one automatically.

---

## 41. Markers and assertions

Use markers when section completeness matters.

A zero GF exit code does not override:

- missing begin marker;
- missing end marker;
- incomplete section;
- failed assertion;
- missing expected artifact;
- failed gold comparison.

Scenario success requires every configured criterion.

---

## 42. Complete `VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md`

Document:

```text
validation modes
file selection
checkpoints
entrypoints
static-scan policy
compilation policy
scenario registry
assertions
normalization
gold policy
regression comparison
release gates
evidence paths
failure and continuation behavior
```

Avoid duplicating exact CLI spelling.

`docs/usage/CLI_REFERENCE.md` owns command syntax.

---

## 43. Complete `TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md`

Map each release-relevant linguistic or architectural feature to:

```text
owning module
unit or component tests
GF compile target
scenario
input fixture
gold evidence
release gate
known issue when evidence is absent
```

The matrix records evidence relationships.

It is not an implementation-status ledger.

---

# Part VI — Establish a reproducible baseline

## 44. Validate configuration

Before GF execution, verify:

```text
[ ] project.toml parses
[ ] schema identity and version are supported
[ ] required project fields are present
[ ] portable paths are relative
[ ] external source relationships are approved
[ ] source directory exists
[ ] source selection matches intended files
[ ] entrypoints exist
[ ] checkpoints exist
[ ] scenario IDs are unique
[ ] scenario files exist
[ ] required input files exist
[ ] required gold files exist
[ ] expected artifact paths are safe
[ ] project documents agree with configuration
```

---

## 45. Resolve the local environment

Supply machine-local values through supported local configuration:

```text
GF executable
RGL root
output root
local application state
optional local source-root binding
```

The resolved GF executable and GF path must be known before required GF execution.

---

## 46. Probe GF

Record:

```text
resolved GF executable
raw version output
normalized GF version
compatibility interpretation
platform
probe evidence
```

Unknown version output remains unknown.

Do not silently assume compatibility.

---

## 47. Run focused validation

Begin with a selected low-level provider or another configured target.

Purpose:

- verify source selection;
- verify GF path resolution;
- verify process execution;
- verify stdout and stderr capture;
- verify run evidence;
- identify the earliest direct failure.

A focused pass does not prove release readiness.

---

## 48. Run checkpoints

For each configured checkpoint:

1. validate the provider;
2. validate direct consumers;
3. preserve raw evidence;
4. interpret diagnostics;
5. distinguish direct and downstream failures;
6. repair the root issue;
7. rerun affected consumers;
8. update project contracts when behavior changed.

Do not fix downstream modules before identifying whether they have an independent defect.

---

## 49. Run diagnostic validation

Diagnostic validation establishes broad evidence across the active project.

It may include:

- the configured source inventory;
- static scan;
- per-file GF compilation;
- detailed diagnostic interpretation;
- optional scenarios;
- bounded generation;
- previous-run comparison.

Diagnostic validation remains bounded.

It does not replace release validation.

---

## 50. Preserve baseline evidence

A baseline run should produce, when required by the run mode:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
master.log
raw compile stdout and stderr
raw scenario stdout and stderr
normalized scenario output
gold diffs
GF artifacts
```

The baseline may contain failures.

Its purpose is to establish reproducible current evidence.

---

# Part VII — Resolve project issues

## 51. Root-cause order

Triage in this order:

```text
configuration errors
    ↓
launch and environment errors
    ↓
direct low-level provider errors
    ↓
category and lincat errors
    ↓
syntax provider errors
    ↓
structural and extension errors
    ↓
entrypoint errors
    ↓
scenario and gold failures
    ↓
downstream failures
```

---

## 52. Evidence levels

Distinguish:

```text
unverified assertion
historical evidence
synthetic fixture evidence
current static finding
current reproducible GF failure
current scenario or gold failure
release-run or artifact failure
```

Do not declare a current defect solely because an old fixture contains a similar message.

---

## 53. Preserve structured categories

Do not replace structured categories with raw `Str` only to make compilation proceed.

A representation change affecting consumers requires:

- a project decision;
- provider updates;
- consumer updates;
- contract updates;
- scenario review;
- gold review;
- release-gate review.

---

## 54. Revalidate consumers

A provider change is complete only when:

- direct consumers pass;
- downstream entrypoints are reviewed;
- affected scenarios pass;
- affected golds are reviewed;
- dependency and lincat contracts agree;
- release evidence is refreshed where required.

---

# Part VIII — Release evidence

## 55. Complete `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md`

Required gates normally include:

```text
project configuration valid
source inventory coherent
required checkpoints pass
required entrypoints pass
missing-linearization checks pass
required scenarios pass
required gold comparisons pass
required PGF exists
required PGF is non-empty
manifest verifies
no blocking known issue remains
versions and source revision are recorded
```

The project may define additional language-specific gates.

---

## 56. Run release validation

Release validation must not silently omit required work.

A required skipped operation is not a passing release result.

Release validation consumes the configured project contract.

It must not infer missing entrypoints or create missing golds.

---

## 57. Verify the PGF

Verify:

```text
expected filename
expected entrypoint
file exists
file is non-empty
artifact belongs to the current run
GF version is recorded
SHA-256 is recorded
manifest entry exists
published hash matches the retained artifact
```

---

## 58. Verify the manifest

Verify:

```text
schema identity
run identity
required artifact roles
paths
sizes
SHA-256 values
containment
self-exclusion
summary consistency
post-manifest modification
```

A report file alone does not prove artifact integrity.

---

## 59. Record release identity

A release record includes:

```text
project ID
project version
source revision
GF Wordbench version
GF version
project schema version
normalization version
required scenario set
release entrypoint
PGF hash
manifest hash
```

Project version, GF Wordbench version, GF version, schema version, and normalization version remain separate identities.

---

# Part IX — Placeholder policy

## 60. Placeholder replacement matrix

| Placeholder | Replace with |
|---|---|
| `<PROJECT_ID>` | Stable project identifier |
| `<PROJECT_NAME>` | Human-readable project name |
| `<PROJECT_OWNER>` | Maintainer or team |
| `<PROJECT_VERSION>` | Project semantic version |
| `<LANGUAGE_NAME>` | Full language name |
| `<LANGUAGE_CODE>` | ISO or project language code |
| `<GF_SUFFIX>` | GF module suffix |
| `<SOURCE_DIR>` | Project-relative GF source directory |
| `<SOURCE_GLOB>` | Source selection pattern |
| `<ABSTRACT_ENTRYPOINT>` | Active abstract module |
| `<CONCRETE_ENTRYPOINT>` | Main concrete module |
| `<SYNTAX_ENTRYPOINT>` | Syntax entrypoint or `None` |
| `<LANGUAGE_ENTRYPOINT>` | Language composition module |
| `<API_ENTRYPOINT_OR_NONE>` | Application API module or `None` |
| `<RELEASE_ENTRYPOINT>` | PGF-producing entrypoint |
| `<EXPECTED_PGF>` | Expected PGF filename |
| `<NORMALIZATION_VERSION>` | Scenario normalization version |
| `<YYYY-MM-DD>` | Actual review or decision date |

Additional placeholders must be documented by their owning file.

---

## 61. Placeholder scan

Before considering the active project configured, scan project-owned files for unresolved placeholders.

Recommended pattern:

```regex
<[A-Z][A-Z0-9_ -]*>
```

Review every match manually.

Do not evaluate `templates/project/` with the active-project placeholder rule.

The reusable template intentionally contains placeholders.

---

# Part X — Source and contract discipline

## 62. Source naming

Recommended GF naming form:

```text
<Responsibility><GF_SUFFIX>.gf
```

Illustrative examples:

```text
Res<GF_SUFFIX>.gf
Noun<GF_SUFFIX>.gf
Verb<GF_SUFFIX>.gf
Grammar<GF_SUFFIX>.gf
Lang<GF_SUFFIX>.gf
```

Names must follow:

- the real project architecture;
- GF and RGL interfaces;
- documented module roles;
- project suffix conventions.

---

## 63. Import discipline

Expected conceptual direction:

```text
resources and parameters
    → morphology
    → category implementations
    → syntax
    → structural vocabulary and extensions
    → lexicon
    → grammar, language, and API entrypoints
    → PGF
```

Prohibited:

```text
low-level provider → top-level entrypoint
morphology → lexicon merely to reuse a helper
category provider → aggregate module
circular import
consumer → undocumented provider field
```

Move shared helpers to the legitimate lower-level owner.

---

## 64. Public GF contracts

A GF detail is contractual when another file depends on it.

Examples:

```text
public oper
public constructor
lincat field
parameter constructor
table shape
module name
entrypoint
scenario marker
gold section
expected artifact
```

A contract change updates:

```text
provider
direct consumers
downstream entrypoints
project configuration
scenarios
gold expectations
dependency map
project contract lock
release evidence
```

---

# Part XI — Validation semantics

## 65. Validation modes

Canonical GF Wordbench modes:

```text
quick
checkpoint
diagnostic
release
```

Legacy aliases, when accepted, are handled by compatibility code.

Active project configuration and documentation use canonical mode names.

---

## 66. Validation outcomes

Validation outcome, process state, diagnostic class, issue identity, regression change, and release decision remain separate concepts.

Use the canonical vocabularies defined by:

```text
docs/reference/STATUS_VALUES.md
docs/reference/DIAGNOSTIC_KINDS.md
docs/GLOSSARY.md
```

This separation is about runtime evidence, not implementation progress tracking.

---

## 67. Direct and downstream failures

A direct failure is a likely root failure in the evaluated subject.

A downstream failure is blocked by another failed provider.

During project repair:

- address direct low-level providers first;
- rerun downstream modules after provider repair;
- create separate known issues only for independent failures;
- preserve blocker relationships.

Many downstream failures may represent one provider contract break.

---

## 68. Raw and normalized evidence

Raw evidence includes:

```text
stdout
stderr
exit code
execution state
command request
working directory
produced artifacts
```

Normalized evidence includes:

```text
diagnostic records
scenario sections
normalized output
gold diff
structured validation results
```

Do not replace raw evidence with normalized text.

Do not infer success from stdout alone.

---

## 69. Exit-code caution

The child GF exit code is evidence.

It is not the complete project result.

A zero GF exit code does not override:

- missing required markers;
- failed assertions;
- missing required artifacts;
- fatal diagnostics;
- incomplete scenarios;
- gold mismatches;
- manifest failures.

GF Wordbench maps the complete structured result to its own command exit code.

---

# Part XII — Completion criteria

## 70. Project configuration criteria

The active project is configured when:

```text
[ ] template copied into project/
[ ] project identity defined
[ ] project.toml validates
[ ] required placeholders replaced
[ ] source relationship resolves
[ ] source selection matches intended files
[ ] source inventory documented
[ ] dependency map documented
[ ] category and lincat contract documented
[ ] morphology scope documented
[ ] syntax and constructor rules documented
[ ] entrypoint roles explicit
[ ] checkpoints ordered
[ ] scenarios registered
[ ] required inputs exist
[ ] required golds exist
[ ] project contract lock customized
[ ] project documents agree
[ ] reproducible baseline run exists
[ ] GF and environment evidence is recorded
```

---

## 71. Release criteria

The project is release-ready only when:

```text
[ ] project configuration criteria remain satisfied
[ ] release criteria are defined
[ ] required checkpoints pass
[ ] required entrypoints pass
[ ] missing-linearization checks pass
[ ] required scenarios pass
[ ] required golds match
[ ] required PGF exists
[ ] required PGF is non-empty
[ ] manifest verifies
[ ] no blocking known issue remains
[ ] source revision is identified
[ ] GF Wordbench version is recorded
[ ] GF version is recorded
[ ] release evidence is retained
```

---

# Part XIII — Common mistakes

## 72. Editing documentation before identity

Result:

- inconsistent language codes;
- inconsistent suffixes;
- stale entrypoint examples.

Correction:

- establish `project.toml` identity first.

---

## 73. Copying local paths into project configuration

Result:

- the project works only on one machine.

Correction:

- use project-relative paths;
- keep GF, RGL, output, and local source bindings in approved environment configuration.

---

## 74. Treating every module as an entrypoint

Result:

- unclear release target;
- unstable scenario loading;
- noisy diagnostics.

Correction:

- assign explicit module roles.

---

## 75. Fixing downstream failures first

Result:

- duplicated workarounds;
- hidden provider defects;
- broken contract ownership.

Correction:

- repair the earliest direct provider.

---

## 76. Creating gold before review

Result:

- incorrect behavior becomes an accepted expectation.

Correction:

- inspect raw output;
- inspect normalized output;
- review the diff;
- update gold explicitly.

---

## 77. Leaving placeholders in active files

Result:

- ambiguous project identity and incomplete contracts.

Correction:

- run the placeholder scan;
- resolve every required value.

---

## 78. Editing the template with active-project values

Result:

- future projects inherit incorrect identity and evidence.

Correction:

- restore generic placeholders in `templates/project/`;
- keep active values under `project/`.

---

## 79. Adding Portfolio fields to the project

Result:

- Wordbench project configuration becomes coupled to another product.

Correction:

- keep Portfolio registration and aggregation in `gf-portfolio`;
- expose only public versioned Wordbench artifacts.

---

# Part XIV — Project maintenance

## 80. Template maintenance

When project structure changes, review both:

```text
project/
templates/project/
```

A template change is complete when:

- the project loader accepts it;
- placeholders are documented;
- active-language data is absent;
- required files exist;
- initialization instructions agree;
- template and active-project lock roles agree;
- template tests pass.

---

## 81. Adding a project document

A new required document needs:

```text
purpose
owner
relationship to existing documents
template path
active-project path
initialization instructions
release relevance
consistency checks
```

Do not add a document that duplicates an existing owner.

---

## 82. Adding a project field

A new `project.toml` field requires:

```text
schema definition
required or optional behavior
path semantics
loader support
validation
migration behavior
template update
documentation
tests
consumer review
```

Do not add a field understood by only one undocumented consumer.

---

## 83. Adding a scenario

Before registering a scenario, define:

```text
scenario ID
purpose
required or optional role
entrypoint
script path
input references
timeout
markers
assertions
normalization version
gold requirement
expected artifacts
release impact
```

Then update:

```text
project.toml
VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md
TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md
scenario README
gold README when applicable
project contract lock
```

---

## 84. Adding an entrypoint

Before registering an entrypoint, define:

```text
module
role
abstract API
direct imports
consumers
checkpoint position
scenario users
PGF role
release requirement
```

Then validate:

```text
direct compilation
consumer compilation
scenario load
missing linearizations
PGF construction when applicable
```

---

## 85. Renaming a module or suffix

A rename is a coordinated migration.

Review:

```text
source filename
GF module declaration
imports
project.toml
entrypoints
checkpoints
scenarios
inputs
gold headers
expected PGF
dependency map
architecture documents
contract lock
known issues
release criteria
previous-run compatibility
```

Do not leave the old name active in current project paths or current documentation.

---

## 86. Gold-update workflow

```text
1. run the focused scenario
2. inspect raw stdout and stderr
3. inspect normalized output
4. classify the change
5. confirm normalization version
6. update implementation or gold deliberately
7. review the diff
8. record a project decision when contract meaning changed
9. rerun the scenario
10. rerun affected release gates
```

Normal validation never performs step 6 automatically.

---

## 87. Project versioning

The active project uses:

```text
MAJOR.MINOR.PATCH
```

Typical interpretation:

- `MAJOR`: incompatible public grammar or project contract;
- `MINOR`: compatible linguistic or grammar expansion;
- `PATCH`: compatible correction.

Project version is independent of:

```text
GF Wordbench version
GF version
schema version
normalization version
template version
```

---

## 88. Command references

Use the canonical CLI reference:

```text
docs/usage/CLI_REFERENCE.md
```

Do not copy command spelling from old GF Audit documents.

Conceptual workflow:

```text
inspect resolved project configuration
check paths and contracts
run focused validation
run configured checkpoints
run diagnostic validation
run release validation
verify the release run and artifacts
```

---

## 89. Evidence to retain

Retain:

```text
project configuration revision
source revision
resolved GF executable
GF version
RGL identity
focused run evidence
checkpoint evidence
diagnostic evidence
release evidence
direct error evidence
scenario output
gold diffs
project decisions
migration notes
```

Do not retain credentials or complete environment dumps.

---

## 90. Research evidence

Use:

```text
project/docs/RESEARCH_EVIDENCE.md
```

to record sources supporting language-specific decisions.

Useful fields:

```text
claim
source
date accessed
relevant summary
project decision supported
limitations
affected modules
```

Do not use unsourced intuition as the sole support for a contested linguistic rule.

---

# Part XV — Verification checklists

## 91. Template verification checklist

Use for `templates/project/`.

```text
[ ] no active-language name
[ ] no active language code
[ ] no active GF suffix
[ ] no active module name
[ ] no developer username
[ ] no absolute local path
[ ] no GF executable path
[ ] no RGL path
[ ] no output root
[ ] no application state
[ ] no run directory
[ ] no generated .gfo
[ ] no generated .pgf
[ ] no project gold presented as template data
[ ] no Portfolio registry identity
[ ] placeholders documented
[ ] placeholder names consistent
[ ] required files present
[ ] links use template-relative structure
[ ] project loader contract current
[ ] template contract lock current
[ ] initialization tests pass
```

---

## 92. Active-project configuration checklist

```text
Identity
[ ] project ID selected
[ ] project name selected
[ ] project owner recorded
[ ] project version selected
[ ] language name selected
[ ] language code selected
[ ] GF suffix selected
[ ] source relationship selected
[ ] release entrypoint selected
[ ] expected PGF selected

Configuration
[ ] project.toml validates
[ ] portable paths are relative
[ ] source selection is correct
[ ] GF path additions are ordered
[ ] entrypoint roles are explicit
[ ] checkpoints are ordered
[ ] scenarios are registered
[ ] release artifacts are declared

Source
[ ] source inventory complete
[ ] filenames match module declarations
[ ] duplicates and backups excluded
[ ] dependency map complete
[ ] circular imports absent
[ ] public providers identified

Contracts
[ ] lincat contracts documented
[ ] morphology contracts documented
[ ] syntax ownership documented
[ ] helpers have one owner
[ ] project interfile lock customized

Validation
[ ] scenario files exist
[ ] input files exist
[ ] required golds exist
[ ] normalization version selected
[ ] placeholder scan passes
[ ] project configuration check passes
[ ] focused validation completed
[ ] checkpoints completed
[ ] diagnostic baseline retained

Governance
[ ] known issues document reviewed
[ ] decision log reviewed
[ ] coverage matrix reviewed
[ ] release criteria reviewed
[ ] research evidence reviewed
```

---

## 93. Release checklist

```text
[ ] active-project configuration checks remain valid
[ ] project version recorded
[ ] required checkpoints pass
[ ] required entrypoints pass
[ ] missing-linearization checks pass
[ ] required scenarios pass
[ ] required golds match
[ ] release entrypoint builds
[ ] expected PGF exists
[ ] expected PGF is non-empty
[ ] PGF hash recorded
[ ] manifest verifies
[ ] no blocking known issue remains
[ ] source revision identified
[ ] GF Wordbench version recorded
[ ] GF version recorded
[ ] release notes prepared
[ ] release evidence retained
```

---

# Part XVI — Anti-drift rules

## 94. Drift indicators

Project-template or initialization drift exists when:

- active values appear in `templates/project/`;
- required placeholders remain in `project/`;
- `project.toml` and documentation disagree;
- source identity is inferred from old run output;
- a scenario loads an unregistered module;
- a gold identifies another scenario;
- release entrypoints differ across configuration and documents;
- expected PGF names differ;
- a public lincat field is undocumented;
- two modules own the same helper;
- a required scenario is silently optional;
- a required scenario is skipped in a passing release;
- generated artifacts appear in the template;
- a machine-local path enters portable configuration;
- a provider changes without consumer review;
- framework production code contains the active-language identity;
- a current defect is inferred only from synthetic evidence;
- a Portfolio registry field appears in Wordbench project configuration;
- project documents reintroduce an implementation-status ledger.

Resolve drift by restoring the owning contract or recording a deliberate project decision when the contract itself changes.

---

## 95. Prohibited behavior

The following are prohibited:

- treating the template as the active project;
- editing the template with real project identity;
- leaving required placeholders unresolved;
- storing local GF or RGL paths in portable project configuration;
- using unmanaged absolute source paths;
- inferring language identity from GUI state or previous runs;
- creating scenarios before defining entrypoint contracts;
- generating gold during normal validation;
- treating required skipped validation as success;
- fixing downstream consumers before identifying the provider cause;
- flattening structured categories to `Str` without a project decision;
- hiding known issues or evidence gaps;
- presenting old fixtures as current release evidence;
- claiming a PGF release without artifact and manifest verification;
- coupling Wordbench initialization to `gf-portfolio`;
- maintaining implementation progress through a project status ledger.

---

## 96. Invariants

1. `templates/project/` remains generic.
2. `project/` represents one active GF language project.
3. `project.toml` owns machine-readable project identity and registries.
4. Machine-local values remain outside portable project configuration.
5. Project-owned portable paths are relative.
6. Required placeholders are replaced in the active project.
7. The source inventory reflects the configured source tree.
8. The dependency map owns GF import relationships.
9. The category contract owns public lincat structures.
10. The morphology specification owns morphology requirements.
11. The syntax specification owns constructor and word-order rules.
12. The project lock owns cross-file contracts.
13. Every public responsibility has one provider.
14. Lower-level modules do not import top-level entrypoints.
15. Confirmed project problems remain visible in known issues.
16. Scenarios use registered entrypoints.
17. Golds use the declared normalization version.
18. Normal validation never modifies gold.
19. Baseline runs preserve raw and structured evidence.
20. Direct and downstream failures remain distinct.
21. Required skipped work is not release success.
22. Release requires verified required entrypoints and scenarios.
23. Release requires the expected non-empty PGF.
24. Release requires a verified manifest.
25. Project, GF Wordbench, GF, schema, normalization, and template versions remain distinct.
26. Active-language values do not leak into the reusable template.
27. Project configuration and release readiness remain separate criteria.
28. Documentation describes project contracts directly.
29. `gf-portfolio` remains an optional external consumer of public Wordbench artifacts.
30. A project change is complete only when providers, consumers, configuration, scenarios, golds, documentation, and evidence agree.

---

## 97. Enforcement rule

Initialize the project in one controlled direction:

```text
generic template
    → authoritative project identity
    → exact source inventory
    → explicit architecture and contracts
    → registered entrypoints and checkpoints
    → bounded scenarios and reviewed golds
    → reproducible baseline evidence
    → resolved root issues
    → verified release PGF and manifest
```

Do not proceed while the preceding contract remains ambiguous.

The active project is ready for development when it is explicit, coherent, and reproducible.

It is ready for release when every required gate is supported by current validation evidence.
