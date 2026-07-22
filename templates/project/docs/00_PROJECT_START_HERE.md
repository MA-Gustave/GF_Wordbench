# GF Wordbench Project Template — Start Here

**Document ID:** `GF-WB-TEMPLATE-PROJECT-START`  
**Status:** Normative template onboarding guide  
**Applies to:** A new active GF language project initialized from `templates/project/`  
**Template owner:** GF Wordbench maintainers  
**Project owner after initialization:** `<PROJECT_OWNER>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**GF module suffix:** `<GF_SUFFIX>`  
**Template guide version:** `1.0`  
**Last reviewed:** `<YYYY-MM-DD>`  

---

## 1. Purpose

This is the first document to read when creating a language project from the GF Wordbench project template.

It explains:

- what the template contains;
- what must remain generic in `templates/project/`;
- what must be customized after copying the template into `project/`;
- which file owns each project fact;
- the required initialization order;
- how GF source modules, entrypoints, checkpoints, scenarios, gold files, project documentation, and release artifacts fit together;
- which validations must pass before the project is considered initialized;
- which evidence is required before a module or feature may be marked stable.

This file is not a language specification.

It is the operational entrypoint for turning the reusable project template into one real, active GF language project.

---

## 2. Core rule

> Configure one authoritative project identity first, then make every source file, scenario, gold file, document, and release target agree with it.

Do not begin by editing files independently.

A language-project initialization is one coordinated change across:

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

---

## 3. Template and active project are different things

GF Wordbench contains two distinct project trees.

### Reusable template

```text
templates/project/
```

Purpose:

- initialize future language projects;
- retain generic placeholders;
- remain language-neutral;
- define the expected directory and documentation structure.

### Active project

```text
project/
```

Purpose:

- represent one real language;
- contain concrete identity values;
- contain the active GF source configuration;
- contain active scenarios and gold files;
- contain current architecture, status, issues, and release evidence.

The template is not the active project.

The active project must not continue to behave like an unfilled template.

---

## 4. Rules for the reusable template

Files under:

```text
templates/project/
```

must not contain:

- a real active-language name;
- an active GF suffix;
- active module names;
- a local machine path;
- a developer username;
- an RGL installation path;
- a GF executable path;
- an output-directory path tied to one computer;
- current project secrets;
- generated `.gfo` files;
- generated `.pgf` files;
- run directories;
- application state;
- current project gold output;
- claims that a real project passed validation.

The template may contain documented placeholders such as:

```text
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<SOURCE_DIR>
<ABSTRACT_ENTRYPOINT>
<CONCRETE_ENTRYPOINT>
<SYNTAX_ENTRYPOINT>
<LANGUAGE_ENTRYPOINT>
<API_ENTRYPOINT_OR_NONE>
<EXPECTED_PGF>
<PROJECT_ROOT>
<YYYY-MM-DD>
```

A placeholder must have one clear meaning.

Do not add several placeholders for the same project fact.

---

## 5. Rules after copying into the active project

After the template is copied into:

```text
project/
```

all required placeholders must be replaced with current project values.

The active project must not contain unresolved required placeholders.

Allowed exception:

- a clearly documented future or optional field may remain explicitly `None`, `Not applicable`, `Planned`, or another approved final status when the owning document permits it.

Do not leave alternatives such as:

```text
Active | Deprecated | Retired
stable | experimental | blocked
<ENTRYPOINT>
```

inside an active-project declaration.

Select the actual value.

---

## 6. First decision: project identity

Before editing source architecture or scenarios, define the project identity.

Required values:

| Field | Value |
|---|---|
| Project ID | `<PROJECT_ID>` |
| Project display name | `<PROJECT_NAME>` |
| Language name | `<LANGUAGE_NAME>` |
| Language code | `<LANGUAGE_CODE>` |
| GF suffix | `<GF_SUFFIX>` |
| Project owner | `<PROJECT_OWNER>` |
| Source directory | `<SOURCE_DIR>` |
| Project version | `<PROJECT_VERSION>` |
| Expected PGF | `<EXPECTED_PGF>` |

Identity must be stable enough to name:

- source directories;
- GF modules;
- scenario entrypoints;
- report subjects;
- release artifacts;
- project documentation.

Renaming the language code or GF suffix later is a breaking project migration.

---

## 7. Authoritative configuration

The authoritative project configuration is:

```text
project/project.toml
```

After initialization, this file owns or resolves:

```text
project ID
project display name
project version
language name
language code
GF module suffix
source directory
source glob
entrypoints
checkpoints
GF path parts
required scenarios
optional scenarios
release entrypoints
expected release artifacts
```

Do not place these facts only in prose.

Documentation explains them.

`project.toml` supplies them to GF Wordbench.

---

## 8. Machine-local values do not belong in `project.toml`

Do not store the following machine-local values in portable project configuration:

```text
GF executable
RGL root
output root
application-state path
developer home directory
absolute project path
temporary directory
```

These values belong to:

- explicit CLI or GUI input;
- supported `GF_WORDBENCH_*` environment variables;
- disposable application state;
- resolved run configuration.

Project-owned paths must remain relative to the project root.

---

## 9. Canonical project layout

The initialized project should follow this structure:

```text
project/
├── README.md
├── project.toml
├── docs/
│   ├── 00_PROJECT_START_HERE.md
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
│   ├── RESEARCH_EVIDENCE.md
│   └── INTERFILE_CONTRACT_LOCK.md
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

It may be inside the project or in the canonical project source layout defined by the repository.

The configured path remains authoritative.

---

## 10. Document ownership map

Each project document has one primary purpose.

| Document | Primary purpose |
|---|---|
| `README.md` | Concise project identity and common entrypoints |
| `00_PROJECT_START_HERE.md` | Initialization and navigation |
| `LANGUAGE_OVERVIEW.md` | Linguistic scope and target language |
| `LANGUAGE_ARCHITECTURE.md` | Layered module and responsibility model |
| `MODULE_DEPENDENCY_MAP.md` | Exact GF import/provider/consumer graph |
| `CATEGORY_AND_LINCAT_CONTRACT.md` | Public category and lincat structures |
| `MORPHOLOGY_SPEC.md` | Inflectional domains, paradigms, and invariants |
| `SYNTAX_AND_CONSTRUCTOR_RULES.md` | Syntax, constructor, and word-order rules |
| `VALIDATION_SPEC.md` | Required validation behavior |
| `TEST_COVERAGE_MATRIX.md` | Linguistic feature-to-evidence mapping |
| `STATUS_LEDGER.md` | Stable, temporary, fallback, blocked, or retired status |
| `DECISION_LOG.md` | Deliberate architecture and linguistic decisions |
| `KNOWN_ISSUES.md` | Confirmed issues, risks, and evidence gaps |
| `RELEASE_CRITERIA.md` | Project release gates |
| `RESEARCH_EVIDENCE.md` | Sources supporting linguistic choices |
| `INTERFILE_CONTRACT_LOCK.md` | Cross-file project contracts |

Do not make several documents authoritative for the same fact.

Cross-reference the owner instead.

---

# 11. Initialization sequence

Use the following order.

```text
Phase 1 — Copy and preserve
Phase 2 — Define identity
Phase 3 — Inventory sources
Phase 4 — Define architecture and contracts
Phase 5 — Configure validation
Phase 6 — Establish the first baseline
Phase 7 — Resolve blockers
Phase 8 — Establish release evidence
```

Skipping directly to release validation usually creates ambiguous failures.

---

# 12. Phase 1 — Copy and preserve

## 12.1 Copy the template

Copy:

```text
templates/project/
```

to:

```text
project/
```

using the project initialization workflow.

Do not edit the reusable template as if it were the active project.

## 12.2 Preserve existing language sources

When migrating an existing language:

- do not overwrite source files automatically;
- create a backup or work from version control;
- inventory the existing modules;
- preserve existing scenarios and gold files;
- preserve historical compile evidence when relevant;
- record migration decisions.

## 12.3 Remove generated artifacts

The initialized active project must not begin with stale:

```text
.gfo
.pgf
run_*
summary.json
manifest.json
temporary logs
```

Generated artifacts belong to controlled run directories.

## 12.4 Confirm a clean working state

Before initialization edits:

```text
[ ] project sources are preserved
[ ] template source is preserved
[ ] no generated artifact will be mistaken for source evidence
[ ] version-control status is understood
[ ] backup or rollback path exists
```

---

# 13. Phase 2 — Define identity

## 13.1 Fill `project.toml` first

Set the authoritative project values before editing the rest of the documentation.

At minimum resolve:

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
release.required_entrypoints
release.expected_artifacts
```

The exact schema is governed by:

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/PERSISTED_SCHEMA_LOCK.md
```

## 13.2 Use relative project paths

Correct:

```toml
directory = "lib/src/<language-directory>"
```

Incorrect:

```toml
directory = "C:/Users/name/repository/lib/src/language"
```

## 13.3 Define one suffix

Every active concrete module suffix must agree with:

```text
<GF_SUFFIX>
```

Examples of derived names:

```text
Res<GF_SUFFIX>.gf
Noun<GF_SUFFIX>.gf
Grammar<GF_SUFFIX>.gf
Lang<GF_SUFFIX>.gf
```

These are examples, not automatically required files.

The source inventory determines which modules actually exist.

## 13.4 Define entrypoint roles

Do not provide one unordered list without meaning.

Distinguish, where applicable:

```text
abstract entrypoint
concrete grammar entrypoint
syntax entrypoint
language entrypoint
API entrypoint
aggregate diagnostic entrypoint
release PGF entrypoint
```

One module may fill more than one role only when documented.

## 13.5 Define checkpoints

Checkpoints are ordered development surfaces.

Recommended progression:

```text
resource/morphology
    → categories/paradigms
    → core syntax
    → structural/extensions
    → grammar entrypoint
    → language/API entrypoint
    → release entrypoint
```

Use only modules that actually exist or are explicitly planned.

---

# 14. Phase 3 — Inventory the GF source tree

## 14.1 Build an exact inventory

For every active `.gf` file, record:

```text
path
module name
module kind
layer
provider role
direct imports
direct consumers
status
checkpoint role
entrypoint role
release relevance
```

The authoritative detailed location is:

```text
project/docs/MODULE_DEPENDENCY_MAP.md
```

## 14.2 Validate filename and module name

A file:

```text
Foo<GF_SUFFIX>.gf
```

must declare the expected GF module identity.

Record any deliberate exception.

## 14.3 Classify modules

Useful module kinds include:

```text
abstract
concrete
resource
interface
instance
morphology
paradigm
syntax
structural
lexicon
extension
helper
entrypoint
aggregate
API
retired
```

Use categories that reflect the real source tree.

## 14.4 Identify orphan files

An active file is suspicious when it is:

- not selected by the source glob;
- imported by no registered consumer;
- absent from the dependency map;
- excluded by a stale pattern;
- generated rather than authored;
- a duplicate or backup file;
- a retired implementation still on the active path.

Resolve or document every orphan.

## 14.5 Identify missing files

Configuration drift exists when `project.toml` or a scenario references a module that is absent.

Treat this as a configuration issue before running broad compilation.

---

# 15. Phase 4 — Define architecture and contracts

## 15.1 Complete `LANGUAGE_OVERVIEW.md`

Document:

```text
language identity
dialect or standard
orthography
linguistic scope
supported and unsupported domains
intended GF/RGL relationship
project audience
release goals
```

Do not claim coverage that scenarios and source do not support.

## 15.2 Complete `LANGUAGE_ARCHITECTURE.md`

Define the project’s layers.

Recommended conceptual order:

```text
abstract API
parameters/resources
morphology
category implementations
syntax
structural vocabulary
extensions
lexicon
entrypoints
validation and release
```

The physical module graph may differ.

Document the actual ownership.

## 15.3 Complete the dependency map

For every public relationship, identify:

```text
provider
consumer
import direction
public symbols or assumptions
validation evidence
status
```

Circular imports are prohibited.

Lower-level modules must not import top-level entrypoints merely to obtain a helper.

## 15.4 Complete the category and lincat contract

For every public concrete category, document:

```text
provider module
lincat shape
public fields
table indices
parameter domains
construction invariants
direct consumers
breaking changes
validation evidence
```

A consumer must not depend on an undocumented field.

## 15.5 Complete morphology specification

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

Do not invent distinctions merely to fill a template.

Mark unsupported or undecided areas explicitly.

## 15.6 Complete syntax and constructor rules

Document:

```text
phrase composition
word order
agreement
case selection
valency
clitic placement
tense/polarity composition
question formation
relative clauses
coordination
subordination
punctuation
variation
```

Each rule should identify its owner.

## 15.7 Customize the project contract lock

Update:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Fill the project identity section.

Register stable project contracts using IDs:

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

Every required contract must have a final status.

## 15.8 Register incomplete work

Use:

```text
project/docs/STATUS_LEDGER.md
```

for:

```text
experimental
temporary
fallback
warning
blocked
disabled
retired
```

Do not hide incomplete behavior in source comments only.

## 15.9 Record decisions

Use:

```text
project/docs/DECISION_LOG.md
```

when selecting between meaningful alternatives.

Examples:

- lincat representation;
- case system;
- clitic strategy;
- word-order strategy;
- entrypoint layout;
- temporary fallback;
- accepted limitation;
- breaking module rename.

---

# 16. Phase 5 — Configure validation

## 16.1 Validation asset layout

Use:

```text
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

## 16.2 Scenario registry

Every scenario must have:

```text
unique scenario ID
script path
required or optional status
entrypoint
operation scope
timeout class
expected markers or assertions
input references
normalization version
gold requirement
expected artifacts
```

The authoritative registry belongs in `project.toml`.

## 16.3 Required scenario families

Select only the families required by the project.

Common families include:

```text
load
missing linearizations
linearize
parse
bounded generation
morphology
grammar introspection
```

A release project normally needs more than one successful compile.

## 16.4 Native `.gfs` files

Scenarios remain native GF shell scripts.

They must be:

- UTF-8;
- project-owned;
- deterministic;
- bounded;
- free of unauthorized operating-system escape commands;
- explicit about entrypoints;
- stable enough for normalization and gold comparison.

## 16.5 Inputs

Input files should contain stable linguistic test data.

They must not contain:

- local absolute paths;
- secrets;
- random uncontrolled input;
- environment-dependent text unless the scenario normalizes it explicitly.

## 16.6 Gold files

Gold files are reviewed expectations.

Rules:

- one authoritative gold per scenario variant;
- correct scenario ID;
- correct gold schema;
- correct normalization version;
- no automatic update during validation;
- deliberate diff review before change;
- UTF-8 and canonical line endings.

## 16.7 Markers and assertions

Use markers when section completeness matters.

A zero GF exit code does not override:

- missing begin/end marker;
- incomplete scenario;
- failed assertion;
- missing required artifact;
- failed gold comparison.

## 16.8 Complete `VALIDATION_SPEC.md`

Document:

```text
required modes
file selection
checkpoints
entrypoints
scenarios
assertions
normalization
gold policy
release gates
evidence paths
failure behavior
```

## 16.9 Complete the coverage matrix

Map each release-relevant linguistic domain to evidence.

Canonical coverage states:

```text
covered
partially covered
not covered
not applicable
blocked
```

Every `partially covered` or `blocked` item needs:

- a status-ledger entry;
- a known issue when corrective work or release treatment is required.

---

# 17. Phase 6 — Establish the first baseline

## 17.1 Configuration check

Before GF execution, verify:

```text
[ ] project.toml parses
[ ] schema identity and version are supported
[ ] required fields are present
[ ] project paths are relative and contained
[ ] source directory exists
[ ] source glob selects intended files
[ ] entrypoints exist
[ ] checkpoints exist
[ ] scenario IDs are unique
[ ] required scenarios exist
[ ] required gold files exist
[ ] expected artifact paths are safe
```

## 17.2 Resolve the local environment

Supply machine-local values through supported configuration:

```text
project root
GF executable
RGL root
output root
state path when customized
```

The resolved GF executable must be explicit before required execution.

## 17.3 Probe GF

Record:

```text
GF executable
raw version output
normalized GF version
compatibility classification
platform
```

An untested version must not be described as tested.

## 17.4 Run a first quick validation

Start with the lowest stable source provider or one selected target.

Purpose:

- verify paths;
- verify GF invocation;
- verify evidence capture;
- verify source selection;
- identify the first direct error.

A quick pass does not establish project release readiness.

## 17.5 Run ordered checkpoints

For each checkpoint:

1. validate the direct provider;
2. validate its known consumers;
3. classify direct and downstream failures;
4. resolve the earliest root issue;
5. rerun affected consumers;
6. record status.

Do not fix downstream modules before proving an independent downstream defect.

## 17.6 Run diagnostic mode

Use diagnostic mode to establish broad evidence.

It may include:

- all configured source files;
- optional scenarios;
- deeper introspection;
- bounded generation;
- comparison with a previous run.

Diagnostic mode may be slower.

It must still be bounded.

## 17.7 Preserve baseline evidence

A baseline run should produce, when supported:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
master.log
raw compiler streams
raw scenario streams
normalized outputs
gold diffs
```

The baseline may fail.

Its purpose is to establish reproducible current evidence.

---

# 18. Phase 7 — Resolve blockers

## 18.1 Root-cause order

Triage in this order:

```text
configuration errors
    ↓
launch or environment errors
    ↓
direct low-level provider errors
    ↓
category/lincat errors
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

## 18.2 Use the known-issues registry

Create project issue IDs:

```text
KI-<LANGUAGE_CODE>-<NUMBER>
```

or the project’s approved equivalent.

Each issue should include:

```text
status
evidence level
severity
priority
release impact
affected area
reproduction
expected behavior
current behavior
dependencies
resolution criteria
owner
```

## 18.3 Distinguish evidence levels

Recommended levels:

```text
assertion only
historical or synthetic
current static evidence
current reproducible GF failure
current scenario or gold failure
release-run or artifact failure
```

Do not declare a current defect only because an old fixture contains a similar message.

## 18.4 Do not flatten structured categories

Do not replace structured records with raw `Str` only to make compilation proceed.

Any deliberate flattening affecting consumers is a breaking architecture decision.

## 18.5 Do not hide fallbacks

Temporary fallback behavior must be:

- documented;
- registered;
- validated;
- assigned release impact;
- given replacement criteria.

## 18.6 Revalidate consumers

A provider fix is incomplete until:

- direct consumers pass;
- downstream entrypoints are reviewed;
- affected scenarios pass;
- affected gold is reviewed;
- contracts are synchronized.

---

# 19. Phase 8 — Establish release evidence

## 19.1 Define release criteria

Complete:

```text
project/docs/RELEASE_CRITERIA.md
```

Required gates normally include:

```text
project configuration valid
required source modules pass
required entrypoints pass
missing-linearization check passes
required PGF exists
required scenarios pass
required gold matches
no required scenario skipped
no blocking known issue remains
manifest verifies
versions and source revision are recorded
```

## 19.2 Run release mode

A release-mode run must not silently omit required work.

Required skipped work is not success.

## 19.3 Verify the PGF

Verify:

```text
expected filename
expected entrypoint
file exists
file is non-empty
path is owned
GF version recorded
SHA-256 recorded
manifest entry exists
published hash matches
```

## 19.4 Verify the manifest

The manifest must describe finalized artifacts.

Verify:

```text
schema
required roles
paths
size
SHA-256
containment
post-manifest modification
```

## 19.5 Record release identity

A project release should record:

```text
project ID
project version
source revision
GF Wordbench version
GF version
project schema version
normalization version
required scenario set
PGF hash
manifest hash
```

## 19.6 Update status documents

Before release:

```text
[ ] STATUS_LEDGER.md is current
[ ] KNOWN_ISSUES.md is current
[ ] DECISION_LOG.md is current
[ ] TEST_COVERAGE_MATRIX.md is current
[ ] RELEASE_CRITERIA.md is current
[ ] INTERFILE_CONTRACT_LOCK.md is current
```

---

# 20. Placeholder replacement matrix

Replace these placeholders in the active project.

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
| `<SOURCE_GLOB>` | Source selection glob |
| `<ABSTRACT_ENTRYPOINT>` | Active abstract module |
| `<CONCRETE_ENTRYPOINT>` | Main concrete module |
| `<SYNTAX_ENTRYPOINT>` | Syntax/API module or `None` |
| `<LANGUAGE_ENTRYPOINT>` | Language composition module |
| `<API_ENTRYPOINT_OR_NONE>` | Application API module or `None` |
| `<RELEASE_ENTRYPOINT>` | PGF-producing entrypoint |
| `<EXPECTED_PGF>` | Final PGF filename |
| `<PROJECT_ROOT>` | Portable project-root description, not a machine path |
| `<NORMALIZATION_VERSION>` | Approved scenario normalization version |
| `<YYYY-MM-DD>` | Actual review or decision date |

A project may define additional placeholders.

Every additional placeholder must be documented here or in the file that owns it.

---

# 21. Placeholder scan

Before declaring initialization complete, scan active project files for unresolved placeholders.

Recommended pattern:

```regex
<[A-Z][A-Z0-9_ -]*>
```

Review matches manually.

Do not run the scan against `templates/project/` when evaluating the active project.

The reusable template is expected to contain placeholders.

---

# 22. Initial project README

`project/README.md` should remain concise.

It should identify:

```text
project name
language
project version
source directory
main entrypoints
validation command
release command
documentation start path
current stability statement
```

It should link to:

```text
project/docs/00_PROJECT_START_HERE.md
```

Detailed architecture belongs in the project docs.

---

# 23. Source naming

Recommended GF naming convention:

```text
<Responsibility><GF_SUFFIX>.gf
```

Examples:

```text
Res<GF_SUFFIX>.gf
Noun<GF_SUFFIX>.gf
Verb<GF_SUFFIX>.gf
Grammar<GF_SUFFIX>.gf
Lang<GF_SUFFIX>.gf
```

These names are illustrative.

Do not create empty modules only to satisfy the example list.

Use names consistent with:

- GF/RGL interfaces;
- actual project architecture;
- documented entrypoint roles.

---

# 24. Import discipline

Expected conceptual direction:

```text
resources and parameters
    → morphology
    → category implementations
    → syntax
    → structural vocabulary and extensions
    → lexicon
    → grammar/language/API entrypoints
    → PGF
```

Prohibited:

```text
low-level resource → final entrypoint
morphology → lexicon for shared helper
category provider → aggregate module
circular import
consumer relying on undocumented provider field
```

Move shared helpers to the correct lower layer.

---

# 25. Public GF contract discipline

A GF detail is project-contractual when another file depends on it.

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

A contract-changing edit must update:

```text
provider
direct consumers
downstream entrypoints
project configuration
scenarios
gold expectations
dependency map
status ledger
contract lock
release evidence
```

---

# 26. Project status vocabulary

Recommended implementation statuses:

```text
stable
experimental
temporary
fallback
warning
blocked
disabled
retired
```

Use one selected status per item.

Do not use `stable` merely because a file exists.

Stable normally requires:

- direct compilation;
- required consumer compilation;
- required scenario evidence;
- no blocking contract issue.

---

# 27. Issue vocabulary

Recommended issue statuses:

```text
Open
Investigating
Blocked
Mitigated
Deferred
Resolved
Closed as not reproducible
Closed as duplicate
Retired
```

Recommended severities:

```text
Critical
High
Medium
Low
Informational
```

Recommended priorities:

```text
P0
P1
P2
P3
```

The project may refine labels, but release criteria must remain unambiguous.

---

# 28. Validation modes

Canonical GF Wordbench modes:

```text
quick
checkpoint
diagnostic
release
```

Legacy aliases may be accepted by compatibility code:

```text
file → quick
all → diagnostic
```

Active project documentation and canonical configuration should use the current names.

---

# 29. Validation statuses

Canonical validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

Keep them distinct from:

```text
process execution state
diagnostic class
error kind
issue status
implementation status
release state
```

---

# 30. Direct and downstream failures

A direct failure is a likely root failure in the subject being evaluated.

A downstream failure is blocked by another failed provider.

During initialization:

- repair direct low-level providers first;
- rerun downstream modules after each provider repair;
- create separate issues only for independent failures;
- preserve `blocked_by` relationships.

A large number of downstream failures may represent one root contract break.

---

# 31. Raw and normalized evidence

Raw evidence includes:

```text
stdout
stderr
exit code
execution state
command
working directory
produced artifacts
```

Normalized evidence includes:

```text
diagnostic records
scenario sections
normalized .out
gold diff
structured results
```

Do not replace raw evidence with normalized text.

Do not infer success from stdout alone.

---

# 32. Exit-code caution

The child GF exit code is evidence.

It is not the complete project result.

A zero GF exit code does not override:

```text
missing required marker
missing required artifact
fatal diagnostic
incomplete scenario
failed assertion
gold mismatch
manifest failure
```

GF Wordbench returns its own command exit code.

---

# 33. Project release blockers

Unless explicitly accepted by `RELEASE_CRITERIA.md`, the following block project release:

```text
invalid project configuration
unresolved required placeholder
missing required source file
required entrypoint failure
required scenario FAIL
required scenario ERROR
required scenario SKIPPED
missing required gold
gold mismatch
unsupported normalization mismatch
missing required PGF
empty required PGF
manifest verification failure
blocking known issue
blocking fallback
unrecorded project/GF/GF Wordbench version
```

---

# 34. Initialization completion criteria

The project is initialized when:

```text
[ ] template copied into project/
[ ] authoritative identity defined
[ ] project.toml validates
[ ] all required placeholders replaced
[ ] source directory exists
[ ] source glob selects intended files
[ ] exact module inventory documented
[ ] dependency map established
[ ] category/lincat contract established
[ ] morphology scope documented
[ ] syntax ownership documented
[ ] entrypoints registered
[ ] checkpoints ordered
[ ] scenarios registered
[ ] required inputs exist
[ ] required gold files exist or are explicitly pending
[ ] status ledger is populated
[ ] known issues are populated
[ ] project contract lock is customized
[ ] first current baseline run exists
[ ] environment and version evidence is recorded
```

Initialization does not require the project to be release-ready.

It requires the project to be coherent, explicit, and testable.

---

# 35. Release-readiness criteria

The project is release-ready only when:

```text
[ ] initialization criteria remain satisfied
[ ] release criteria are final
[ ] required checkpoints pass
[ ] required entrypoints pass
[ ] missing-linearization gate passes
[ ] required scenarios pass
[ ] required gold matches
[ ] required PGF exists and verifies
[ ] manifest verifies
[ ] no blocking issue remains
[ ] no blocking fallback remains
[ ] project version is classified
[ ] source revision is clean
[ ] GF Wordbench version is recorded
[ ] GF version is supported or explicitly approved
[ ] release evidence is retained
```

---

# 36. Common initialization mistakes

## 36.1 Editing documentation before identity

Result:

- conflicting language codes;
- inconsistent suffixes;
- stale entrypoint examples.

Correction:

- finalize `project.toml` identity first.

## 36.2 Copying machine paths into the project

Result:

- project works only on one computer.

Correction:

- use project-relative paths;
- keep GF, RGL, and output roots in local environment configuration.

## 36.3 Treating every source file as an entrypoint

Result:

- unclear release target;
- unstable scenario loading;
- noisy diagnostics.

Correction:

- assign explicit roles.

## 36.4 Fixing downstream failures first

Result:

- duplicated workarounds;
- broken architecture;
- hidden provider errors.

Correction:

- repair the earliest direct provider.

## 36.5 Generating gold before behavior is reviewed

Result:

- regressions become approved accidentally.

Correction:

- inspect raw and normalized output first;
- update gold deliberately.

## 36.6 Marking incomplete modules stable

Result:

- release criteria become unreliable.

Correction:

- use the status ledger.

## 36.7 Leaving placeholders in active files

Result:

- project identity remains ambiguous.

Correction:

- run the placeholder scan and review all matches.

## 36.8 Editing the reusable template with active-language values

Result:

- future projects inherit the wrong identity.

Correction:

- restore generic placeholders in `templates/project/`;
- keep active values under `project/`.

---

# 37. Framework and project boundary

The framework owns:

```text
app/
docs/
tests/
templates/
```

The active language project owns:

```text
project/project.toml
project/docs/
project/validation/
active GF source files
```

Framework code must not contain active-language assumptions except in clearly identified fixtures or historical examples.

Project documentation may and should contain language-specific facts after initialization.

---

# 38. Template maintenance

When the project contract changes, review both:

```text
project/
templates/project/
```

A template change is complete only when:

- the project loader accepts the template;
- placeholders are documented;
- no active-language data leaks into the template;
- new required files are present;
- initialization instructions are updated;
- template contract lock is updated;
- template tests pass.

---

# 39. Adding a new project document

A new required document needs:

```text
purpose
owner
relationship to existing documents
template file
active-project path
initialization instructions
release relevance
tests or consistency checks
```

Do not add a document that duplicates an existing owner.

---

# 40. Adding a new project field

A new `project.toml` field requires:

```text
schema classification
default or required status
path semantics
loader support
validation
migration
template update
documentation
tests
consumer review
```

Do not add an undocumented project field that only one consumer understands.

---

# 41. Adding a new scenario

Before registering a scenario, define:

```text
scenario ID
purpose
required or optional
entrypoint
script path
input path
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
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
scenario README
gold README when applicable
project contract lock
```

---

# 42. Adding a new entrypoint

Before registering an entrypoint, define:

```text
module
role
abstract API
direct imports
consumers
checkpoint order
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
PGF build when applicable
```

---

# 43. Renaming a module or suffix

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
architecture docs
contract lock
known issues
release criteria
previous-run migration
```

Do not leave the old name active in current project paths or documentation.

---

# 44. Gold update workflow

```text
1. run the focused scenario
2. inspect raw stdout and stderr
3. inspect normalized output
4. classify the change
5. confirm normalization version
6. update implementation or gold deliberately
7. review the diff
8. record the issue or decision when material
9. rerun the scenario
10. rerun affected release gates
```

Normal validation must not perform step 6 automatically.

---

# 45. Project versioning

The active project should use:

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

# 46. Recommended first commands

The exact CLI may evolve.

Use the current CLI reference.

Conceptually, initialization should support commands equivalent to:

```text
gf-wordbench config show --resolved
gf-wordbench paths check
gf-wordbench contracts check
gf-wordbench validate --mode quick --target <MODULE>
gf-wordbench validate --mode checkpoint
gf-wordbench validate --mode diagnostic
gf-wordbench validate --mode release
```

Do not copy outdated command names from historical GF Audit documentation.

---

# 47. Evidence to retain during initialization

Retain:

```text
project.toml revision
source revision
resolved GF executable
GF version
RGL identity
first quick run
first checkpoint run
first diagnostic run
first release attempt
direct error evidence
scenario output
gold diffs
architecture decisions
migration notes
```

Do not retain secrets or a complete environment dump.

---

# 48. Initial known-issues policy

At initialization, `KNOWN_ISSUES.md` may begin with evidence gaps.

Examples:

```text
current release baseline not established
entrypoint role not yet verified
required scenario not yet implemented
morphology domain not yet covered
historical failure requires reproduction
PGF target not yet verified
```

Do not convert historical or synthetic fixtures into confirmed current defects without reproduction.

---

# 49. Initial status-ledger policy

Every incomplete public area should be entered.

Example fields:

```text
item ID
module or feature
status
owner
consumers
limitation
release impact
replacement criteria
validation evidence
last reviewed
```

The ledger must be updated as implementation becomes stable.

---

# 50. Research evidence

Use `RESEARCH_EVIDENCE.md` to record sources supporting language-specific decisions.

Useful fields:

```text
claim
source
date accessed
relevant excerpt or summary
project decision supported
limitations
affected modules
```

Do not use unsourced intuition as the only support for a contested linguistic rule.

---

# 51. Review cadence

Review this start guide when:

- project schema changes;
- template structure changes;
- a required project document is added or removed;
- validation modes change;
- scenario contracts change;
- release artifacts change;
- contract-lock structure changes;
- initialization automation changes.

The reusable template may retain `<YYYY-MM-DD>`.

The active copy should use the actual review date.

---

# 52. Template verification checklist

Use this checklist for `templates/project/`.

```text
[ ] no active-language name
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
[ ] no project gold disguised as template data
[ ] placeholders are documented
[ ] placeholder names are consistent
[ ] required files exist
[ ] links use template-relative structure
[ ] project loader contract is current
[ ] template contract lock is current
[ ] initialization tests pass
```

---

# 53. Active-project initialization checklist

Use this checklist after copying into `project/`.

```text
Identity
[ ] project ID selected
[ ] project name selected
[ ] project owner recorded
[ ] project version selected
[ ] language name selected
[ ] language code selected
[ ] GF suffix selected
[ ] source directory selected
[ ] expected PGF selected

Configuration
[ ] project.toml validates
[ ] project paths are relative
[ ] source glob is correct
[ ] GF path parts are ordered
[ ] entrypoint roles are explicit
[ ] checkpoints are ordered
[ ] scenarios are registered
[ ] release artifacts are declared

Source
[ ] source inventory complete
[ ] filenames match module declarations
[ ] duplicate/backup files excluded
[ ] dependency map complete
[ ] circular imports absent
[ ] public providers identified

Contracts
[ ] lincat contracts documented
[ ] morphology contracts documented
[ ] syntax ownership documented
[ ] helpers have one owner
[ ] project interfile lock customized
[ ] incomplete work appears in ledger

Validation
[ ] scenario files exist
[ ] input files exist
[ ] required gold exists or is explicitly pending
[ ] normalization version selected
[ ] placeholder scan passes
[ ] configuration check passes
[ ] first quick run completed
[ ] first checkpoint run completed
[ ] first diagnostic baseline retained

Governance
[ ] known issues initialized
[ ] status ledger initialized
[ ] decision log initialized
[ ] coverage matrix initialized
[ ] release criteria initialized
[ ] research evidence initialized
```

---

# 54. Project release bootstrap checklist

Before the first project release:

```text
[ ] all active-project initialization checks remain valid
[ ] project version classified
[ ] required checkpoints pass
[ ] required entrypoints pass
[ ] missing-linearization check passes
[ ] required scenarios pass
[ ] required gold matches
[ ] release entrypoint builds
[ ] expected PGF exists
[ ] PGF is non-empty
[ ] PGF hash recorded
[ ] manifest verifies
[ ] no blocking known issue
[ ] no blocking fallback
[ ] source revision clean
[ ] GF Wordbench version recorded
[ ] GF version recorded
[ ] project release notes prepared
[ ] release evidence retained
```

---

# 55. Anti-drift indicators

Project-template or initialization drift exists when:

- active values appear in `templates/project/`;
- required placeholders remain in `project/`;
- `project.toml` and documentation disagree;
- source directory is inferred from old run output;
- a scenario loads an unregistered module;
- a gold file identifies a different scenario;
- a release entrypoint differs across configuration and docs;
- expected PGF names differ;
- a public lincat field is undocumented;
- two modules own the same helper;
- a fallback exists only in source comments;
- a required scenario is silently optional;
- a required scenario is skipped in a successful release;
- a template contains generated artifacts;
- a machine-local path enters portable project configuration;
- documentation marks a module stable without evidence;
- a provider changes without consumer review;
- the active project still uses legacy canonical names;
- framework code contains the active language identity;
- a current issue is inferred only from a synthetic fixture.

Any drift indicator requires correction or a deliberate project decision.

---

# 56. Prohibited behavior

The following are prohibited:

- treating the template as the active project;
- editing the reusable template with real project identity;
- leaving required placeholders unresolved in the active project;
- storing local GF or RGL paths in `project.toml`;
- using absolute source paths in portable configuration;
- inferring language identity from GUI state or previous runs;
- creating scenarios before defining their entrypoint contract;
- generating gold automatically during normal validation;
- marking required skipped validation as success;
- fixing downstream consumers before identifying the provider cause;
- flattening structured categories to `Str` without an explicit decision;
- hiding incomplete behavior;
- presenting historical fixtures as current release evidence;
- claiming a PGF release without artifact and manifest verification;
- calling initialization complete without a current baseline run.

---

# 57. Final invariants

1. `templates/project/` remains generic.
2. `project/` represents one active language.
3. `project.toml` owns project identity and registry data.
4. Machine-local paths remain outside portable project configuration.
5. Project-owned paths are relative to the project root.
6. Every required placeholder is replaced in the active project.
7. The exact source tree owns current module inventory.
8. The dependency map owns import relationships.
9. The category contract owns public lincat structure.
10. The morphology specification owns inflectional requirements.
11. The syntax specification owns constructor and word-order rules.
12. The project lock owns cross-file contracts.
13. Every public responsibility has one provider.
14. Lower-level modules do not import top-level entrypoints.
15. Incomplete work remains visible in the status ledger.
16. Confirmed project problems remain visible in known issues.
17. Scenarios use registered entrypoints.
18. Gold files use the declared normalization version.
19. Normal validation never modifies gold.
20. The first baseline preserves raw and structured evidence.
21. Direct and downstream failures remain distinct.
22. Required skipped work is not release success.
23. Release requires verified required entrypoints and scenarios.
24. Release requires a non-empty expected PGF.
25. Release requires a verified manifest.
26. Project, GF Wordbench, GF, schema, and normalization versions remain distinct.
27. Active-language values do not leak back into the reusable template.
28. Initialization and release readiness remain separate milestones.
29. Documentation claims only what current evidence supports.
30. A project change is complete only when providers, consumers, configuration, scenarios, gold, documentation, and evidence agree.

---

# 58. Final rule

Initialize the project in one controlled direction:

```text
generic template
    → authoritative project identity
    → exact source inventory
    → explicit architecture and contracts
    → registered entrypoints and checkpoints
    → bounded scenarios and reviewed gold
    → current baseline evidence
    → resolved root issues
    → verified release PGF and manifest
```

Do not move to the next stage while the previous stage remains ambiguous.

The active project is ready for development when it is explicit and reproducible.

It is ready for release only when every required contract is proven by current validation evidence.
