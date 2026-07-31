# GF Wordbench — Migrating an Existing Language

**Document ID:** `GF-WB-PROJECT-MIGRATION`  
**Status:** Normative project-lifecycle procedure  
**Applies to:** Existing Grammatical Framework language implementations being adopted as the single active GF Wordbench project  
**Primary owners:** Language maintainers and GF Wordbench maintainers  
**Canonical active project:** `project/`  
**Canonical project configuration:** `project/project.toml`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Target architecture:** GF Wordbench architecture  
**Last structural review:** 2026-07-24

---

## 1. Purpose

This document defines how to migrate an existing GF language implementation into GF Wordbench without losing source history, changing linguistic behavior accidentally, or introducing undocumented cross-file drift.

The migration must establish:

- one authoritative active language identity;
- one authoritative source root;
- valid project configuration;
- explicit module ownership;
- documented provider/consumer contracts;
- deterministic entrypoints and checkpoints;
- reproducible GF path resolution;
- native `.gfs` validation scenarios;
- reviewed inputs and gold files;
- a clean baseline run;
- release criteria;
- rollback capability.

Migration is complete only when GF Wordbench can reproduce the language project's expected validation and release behavior from documented configuration and source-controlled assets.

---

## 2. Core migration rule

> Migration must preserve the old project as recoverable evidence until the new GF Wordbench project has passed its declared release gates.

The migration process is non-destructive by default.

It must not:

- overwrite the only copy of existing source;
- rename modules before recording dependencies;
- generate new gold files automatically;
- accept failed scenarios as a baseline;
- copy stale `.gfo` or `.pgf` artifacts as proof;
- silently reuse old absolute paths;
- infer language identity from old run directories;
- mix two active languages in one project;
- treat a partial compile as a completed migration.

---

## 3. Related normative documents

This procedure must remain consistent with:

```text
docs/PERSISTED_SCHEMA_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/gf/GF_PATH_RESOLUTION.md
docs/gf/GF_COMPILATION.md
docs/gf/GF_PGF_BUILD.md
docs/gf/GF_VERSION_COMPATIBILITY.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
docs/validation/COMPILATION_VALIDATION.md
docs/validation/SCENARIO_VALIDATION.md
docs/validation/RELEASE_GATES.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/projects/PROJECT_MODEL.md
docs/projects/CREATING_A_PROJECT.md
docs/projects/PROJECT_COMPLETION_CHECKLIST.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

The migration also follows:

```text
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md
docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md
```

Migration concerns one active Wordbench project. Multi-workspace aggregation belongs to the independent `gf-portfolio` product and does not alter Wordbench project configuration, run identity or release evidence.

Project-specific authoritative documents created or completed during migration include:

```text
project/docs/LANGUAGE_OVERVIEW.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
project/docs/DECISION_LOG.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/docs/RESEARCH_EVIDENCE.md
```

---

## 4. Migration outcomes

A successful migration produces:

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
    ├── inputs/
    └── gold/
```

The configured source tree may be physically inside or outside `project/`, but it must have one declared authoritative location.

---

## 5. Migration strategies

Choose one strategy before moving files.

## 5.1 Strategy A — Managed source copy

Copy the active language source into a project-controlled source tree.

Example:

```text
project/
└── lib/
    └── src/
        └── <language>/
            ├── GrammarXxx.gf
            ├── SyntaxXxx.gf
            ├── MorphoXxx.gf
            └── ...
```

Use when:

- GF Wordbench becomes the main development repository;
- the language can be maintained independently;
- source history is migrated or preserved separately;
- relative project paths are preferred;
- release reproducibility should not depend on another mutable checkout.

Advantages:

- self-contained project;
- portable configuration;
- clear ownership;
- simpler backup and cloning;
- reduced environmental drift.

Risks:

- source may diverge from an upstream RGL copy;
- history can be lost if copied without version-control migration;
- duplicate active sources may remain unintentionally.

Required control:

```text
Declare which copy is authoritative immediately after cutover.
```

---

## 5.2 Strategy B — Existing source root

Keep the source in its existing repository and configure GF Wordbench to use that project-relative or documented external root.

Use when:

- the language is maintained directly inside a larger GF/RGL repository;
- moving source would break upstream workflows;
- preserving exact repository history is essential;
- GF Wordbench is an orchestration layer rather than the source owner.

Advantages:

- no source duplication;
- upstream history remains intact;
- existing build workflows remain available.

Risks:

- clone portability may decrease;
- environment configuration becomes more important;
- external checkout changes can affect validation;
- project and source roots can be confused.

Required controls:

- document the external source relationship;
- record the expected repository and revision;
- keep environment-specific absolute paths out of `project.toml`;
- validate root containment and path resolution;
- preserve one authoritative source declaration.

---

## 5.3 Strategy C — Repository import with history

Import the existing language subtree into the GF Wordbench repository while preserving version history.

Possible version-control techniques include:

```text
subtree import
filtered repository history
submodule
vendor branch
documented manual import with source commit reference
```

GF Wordbench does not mandate one version-control tool.

Use when both self-containment and traceable history matter.

Required documentation:

```text
source repository
source revision
import method
import date
preserved path mapping
upstream synchronization policy
```

---

## 5.4 Strategy selection rule

Do not select a strategy merely because it is easiest to copy files.

Choose based on:

```text
future source ownership
upstream synchronization
release reproducibility
history preservation
clone portability
maintainer workflow
legal/licensing constraints
```

Record the decision in:

```text
project/docs/DECISION_LOG.md
```

---

## 6. Migration phases

The canonical migration phases are:

```text
0. authorize and freeze
1. preserve the source baseline
2. inventory the existing language
3. choose project layout
4. initialize project structure
5. establish project identity
6. configure source selection and GF paths
7. map modules and dependencies
8. define public contracts
9. classify incomplete and legacy behavior
10. validate source files progressively
11. define entrypoints and checkpoints
12. create scenarios and inputs
13. establish gold baselines
14. build release PGF
15. produce baseline evidence
16. perform cutover
17. archive migration records
```

Each phase has an explicit exit condition.

---

# 7. Phase 0 — Authorize and freeze

Before migration begins:

```text
[ ] Migration owner identified
[ ] Active language identified
[ ] Source repository identified
[ ] Source branch/revision identified
[ ] Migration strategy selected provisionally
[ ] Release or development freeze window defined
[ ] Backup location verified
[ ] Licensing reviewed
[ ] Upstream synchronization policy identified
```

A temporary freeze is recommended for module renames, lincat changes, scenario changes, and release-entrypoint changes during inventory.

The freeze need not block unrelated work, but the migration baseline must remain reproducible.

Exit condition:

```text
The exact source state to be migrated is identified and recoverable.
```

---

# 8. Phase 1 — Preserve the source baseline

Create a recoverable baseline before any transformation.

Record:

```text
source repository URL or local identity
branch
commit or revision
dirty-worktree status
untracked source files
GF version
RGL version or revision
working build command
existing entrypoints
existing PGF name
known test commands
```

Canonical baseline record:

```text
project/docs/RESEARCH_EVIDENCE.md
```

Minimum source snapshot evidence:

```text
migration_source_revision
migration_source_tree_hash or inventory
migration_started_at
migration_owner
```

If the working tree is dirty:

- record every relevant modification;
- commit, stash, or copy it deliberately;
- do not claim the repository revision alone represents the source.

Exit condition:

```text
The pre-migration source can be restored independently of GF Wordbench.
```

---

# 9. Phase 2 — Inventory the existing language

Do not begin with module renaming.

First inventory what exists.

## 9.1 Source inventory

Record every relevant file:

```text
*.gf
*.gfs
*.pgf
*.gfo
input corpora
manual test scripts
expected-output files
build scripts
launchers
language notes
research references
```

Generated `.gfo` and `.pgf` files are evidence only.

They are not authoritative source.

## 9.2 Module inventory

For every `.gf` file, record:

```text
path
declared module name
module kind
extends/opens/imports
public categories
public functions
public oper values
public parameters
lincat definitions
interfaces and instances
entrypoint role
known consumers
known constraints
```

Recommended module kinds:

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
extension
lexicon
grammar entrypoint
API entrypoint
test support
legacy
```

## 9.3 Existing validation inventory

Record:

```text
manual GF shell commands
compile commands
missing-linearization checks
linearization examples
parse examples
generation commands
morphology tables
external scripts
expected output files
known release checks
```

## 9.4 Existing defect inventory

Record:

```text
known compile failures
known downstream failures
missing linearizations
temporary fallbacks
disabled functions
inherited placeholders
string-based substitutes
duplicated helpers
stale modules
unused modules
nondeterministic tests
unsupported GF commands
```

Use:

```text
project/docs/KNOWN_ISSUES.md
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
```

Exit condition:

```text
Every relevant source, module, validation asset, and known incomplete state has an owner or disposition.
```

---

# 10. Phase 3 — Choose the project layout

Define:

```text
project root
source root
validation root
documentation root
artifact output root
RGL relationship
upstream relationship
```

Canonical project-relative paths use `/`.

The recommended project root is:

```text
project/
```

Recommended source directory when managed inside the project:

```text
lib/src/<language-directory>
```

The exact path is project data, not a framework constant.

## 10.1 Path rules

Project-owned paths must:

- be relative to the project root;
- use `/` in canonical configuration;
- contain no drive letters;
- contain no unresolved `..`;
- remain stable after baseline publication.

Environment paths such as GF executable and local RGL checkout must not be stored in `project.toml`.

## 10.2 Duplicate-source prevention

If source is copied:

```text
[ ] Old source marked read-only or archived after cutover
[ ] New source declared authoritative
[ ] Build scripts updated
[ ] Scenarios load only the authoritative source
[ ] Documentation names only one active source root
[ ] CI validates only the authoritative source
```

Exit condition:

```text
One authoritative source root is selected and documented.
```

---

# 11. Phase 4 — Initialize the project structure

Initialize from:

```text
templates/project/
```

Canonical operation:

```text
gf-wordbench project init
```

Initialization must not overwrite an existing non-empty `project/` without explicit authorization.

Required immediate actions:

```text
[ ] Copy template files
[ ] Preserve template contract lock
[ ] Remove irrelevant examples
[ ] Keep required placeholders visible
[ ] Add validation directories
[ ] Add project README
[ ] Commit the initialized skeleton separately when practical
```

The project must not remain an unresolved template after migration.

Exit condition:

```text
The complete required project structure exists and is version-controlled.
```

---

# 12. Phase 5 — Establish project identity

Edit:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_OVERVIEW.md
```

Required identity:

```text
project id
project display name
language code
language name
module suffix
project root
source root
maintainer
```

Canonical `project.toml` identity:

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "<stable-lowercase-id>"
name = "<language-name>"
language_code = "<language-code>"
root = "."
```

Rules:

- `project.id` is stable after published runs;
- one GF Wordbench copy represents one active language;
- module suffix must agree across source, scenarios, gold, and docs;
- old language identifiers may remain only in migration history;
- GUI state is not project identity;
- old run directories are not project identity.

Exit condition:

```text
Every active project identity reference agrees.
```

---

# 13. Phase 6 — Configure source selection

Canonical table:

```toml
[sources]
directory = "<project-relative-source-directory>"
glob = "*.gf"
include_regex = "<valid-include-regex>"
exclude_regex = "<valid-exclude-regex-or-empty>"
```

## 13.1 Include policy

Include only intended GF source files.

Review:

```text
module naming convention
backup files
copies
temporary files
disabled files
generated files
files containing spaces
case sensitivity
nested directories
```

## 13.2 Exclude policy

Common exclusions may include:

```text
*.bak.gf
*.tmp.gf
*.disabled.gf
copy files
editor recovery files
generated mirrors
archived source
```

Do not exclude a failing source merely to make migration pass.

Every excluded active-looking file needs a reason.

## 13.3 Selection validation

Required checks:

```text
source directory exists
glob is valid
regexes compile
selected files are inside source root
selected ordering is deterministic
entrypoints are selected or intentionally separate
no duplicate normalized paths
```

Exit condition:

```text
GF Wordbench selects exactly the intended source inventory.
```

---

# 14. Phase 7 — Configure GF path resolution

Canonical table:

```toml
[gf]
path_parts = [
  "<ordered-project-path-1>",
  "<ordered-project-path-2>",
  "<RGL-alias-or-project-path>"
]
minimum_version = "<optional-minimum-version>"
```

Path order is semantically significant.

Record all directories required for:

```text
active language modules
abstract grammar modules
common RGL modules
prelude
shared resources
project-local support modules
```

Do not store:

```text
C:/tools/gf/gf.exe
C:/users/<name>/rgl
developer-specific output roots
```

These belong to environment state.

## 14.1 Existing `GF_LIB_PATH`

If the old workflow depends on `GF_LIB_PATH`:

1. record its effective value;
2. identify which path parts are actually required;
3. move project-owned path knowledge into `project.toml`;
4. keep local RGL/tool locations in environment configuration;
5. verify that a clean shell produces the same effective GF path.

## 14.2 GF version

Record:

```text
previous GF version
target supported GF version
minimum project version if needed
known compatibility differences
```

Exit condition:

```text
The effective GF path and version policy are reproducible without hidden shell state.
```

---

# 15. Phase 8 — Map module dependencies

Create:

```text
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/LANGUAGE_ARCHITECTURE.md
```

For each module, record:

```text
provider role
direct imports
direct consumers
architectural layer
entrypoint reachability
checkpoint reachability
scenario reachability
status
```

Expected broad direction:

```text
resource and morphology
→ category implementations
→ syntax and structural modules
→ extension modules
→ grammar or API entrypoints
→ PGF
```

Detect:

```text
cycles
lower-level imports of entrypoints
duplicate providers
hidden helper dependencies
stale imports
module/file name mismatch
unreachable modules
multiple competing entrypoints
```

## 15.1 Module rename policy

Do not rename modules merely for stylistic consistency during initial migration.

Rename only when needed for:

- identity correction;
- collision removal;
- invalid GF naming;
- active-language suffix migration;
- explicit architectural cleanup.

A rename requires updates to:

```text
file name
module declaration
imports
consumers
entrypoints
checkpoints
scenarios
gold metadata
documentation
contract lock
```

Exit condition:

```text
Every active module has a documented layer and dependency relationship.
```

---

# 16. Phase 9 — Define public contracts

Complete:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
```

For every cross-file relationship, identify:

```text
contract ID
provider
consumers
provided symbol or structure
request
response
invariants
allowed variation
breaking changes
validation evidence
documentation owner
last reviewed
```

Recommended contract domains:

```text
PIFC-CONFIG
PIFC-MODULE
PIFC-LINCAT
PIFC-HELPER
PIFC-ENTRY
PIFC-SCENARIO
PIFC-GOLD
PIFC-ARTIFACT
PIFC-DOC
PIFC-RELEASE
```

## 16.1 Contract priority

Document first:

1. project identity to module suffix;
2. abstract to concrete syntax;
3. category/lincat providers;
4. morphology to paradigms;
5. paradigms to lexicon;
6. syntax resources to concrete modules;
7. structural providers to entrypoints;
8. extension ownership;
9. entrypoints to scenarios;
10. entrypoints to PGF build.

## 16.2 No placeholder completion by guess

Do not fill contract fields with assumed providers.

Use:

```text
blocked
experimental
temporary
unknown pending inventory
```

when evidence is incomplete.

Then add an exit condition in `STATUS_LEDGER.md`.

Exit condition:

```text
Every active cross-file dependency has an authoritative provider or an explicit unresolved status.
```

---

# 17. Phase 10 — Record known issues and constraints

Migration often reveals behavior that compiles but still violates a linguistic, architectural or release contract.

Record every relevant issue, including:

```text
fallback
placeholder
warning
blocked subsystem
disabled function
partial paradigm
shallow constructor
string-based substitute
unresolved inheritance
known missing linearization
obsolete module
duplicate provider
```

Use:

```text
project/docs/KNOWN_ISSUES.md
```

Each entry defines:

```text
stable issue ID
owner
module or symbol
reason
consumer impact
validation impact
required correction
release impact
```

A migration baseline must not hide a known issue or weaken a release gate to accommodate it.

Exit condition:

```text
Every known issue affecting active behavior is documented and correctly gated.
```

---

# 18. Phase 11 — Define entrypoints and checkpoints

Canonical configuration:

```toml
[modules]
entrypoints = [
  "<entrypoint-1>.gf"
]
checkpoints = [
  "<checkpoint-1>.gf",
  "<checkpoint-2>.gf"
]
```

## 18.1 Entrypoints

An entrypoint is a top-level module used by:

```text
final compile
scenario loading
PGF build
release validation
```

Required checks:

- file exists;
- module name matches file/configuration;
- imports required components;
- compiles from clean artifacts;
- loads in required scenarios;
- expected `.gfo` is produced;
- expected PGF relationship is documented.

## 18.2 Checkpoints

Choose checkpoints that prove meaningful architectural layers.

Good checkpoint candidates:

```text
morphology provider
noun implementation
verb implementation
syntax integration
extension layer
structural layer
concrete grammar
API syntax layer
```

Do not create one checkpoint per file without a validation purpose.

Order checkpoints according to dependency progression.

## 18.3 Baseline with failing checkpoints

A migration may temporarily retain failing checkpoints only when:

- failure is documented;
- status is not release-ready;
- expected failure is visible;
- exit condition exists;
- release criteria forbid passing with the failure.

Exit condition:

```text
Entrypoints and checkpoints are declared, ordered, and linked to documented architecture.
```

---

# 19. Phase 12 — Progressive compilation validation

Compile progressively.

Recommended order:

```text
1. low-level resource/morphology providers
2. paradigms
3. category implementations
4. syntax and structural layers
5. extension layers
6. checkpoints
7. top-level entrypoints
8. PGF target
```

For every compile:

```text
record command
record GF version
record effective GF path
capture stdout and stderr
record timeout
verify required artifacts
classify FAIL versus ERROR
preserve raw evidence
```

Do not accept:

- zero exit with missing required artifact;
- stale `.gfo` as current evidence;
- timeout as ordinary type failure;
- skipped compile as success;
- source-adjacent old artifacts as release proof.

## 19.1 Provider-first debugging

When a consumer fails:

1. validate the provider;
2. inspect provider public contract;
3. validate direct consumers;
4. classify downstream failures;
5. avoid patching each downstream consumer independently when one provider is wrong.

## 19.2 Compilation baseline

Record:

```text
modules OK
modules FAIL
modules ERROR
modules SKIPPED
direct failures
downstream failures
ambiguous failures
```

Exit condition:

```text
Every configured checkpoint and entrypoint has reproducible structured compile evidence.
```

---

# 20. Phase 13 — Create validation scenarios

Canonical directories:

```text
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

Recommended baseline scenarios:

```text
load
missing
linearize
parse
generation
morphology
```

Not every project must use all scenarios.

Required/optional status belongs in `project.toml`.

## 20.1 Scenario registry

Example:

```toml
[validation]
required_scenarios = [
  "load",
  "missing",
  "linearize",
  "parse"
]
optional_scenarios = [
  "generation",
  "morphology"
]
release_requires_pgf = true
```

Scenario IDs are stable contracts.

## 20.2 Scenario migration from old scripts

For each old test script:

1. identify its purpose;
2. remove shell/environment assumptions;
3. convert it to native `.gfs` where appropriate;
4. add stable begin/end markers;
5. declare its entrypoint;
6. move reusable inputs to `validation/inputs/`;
7. define timeout;
8. define assertion or gold policy;
9. verify explicit GF termination where required.

## 20.3 Unsupported commands

Do not mark a migrated scenario successful merely because GF ignores an unsupported command.

The scenario must prove that every required section completed.

Exit condition:

```text
Every required validation purpose has a registered deterministic scenario or an explicitly documented alternative.
```

---

# 21. Phase 14 — Migrate validation inputs

Inputs should be source-controlled, bounded, and attributable.

Examples:

```text
representative abstract trees
representative surface phrases
morphology lemmas
parse categories
generation seeds or bounded expressions
known regression cases
```

For each input file, record:

```text
owning scenario
encoding
ordering semantics
language
category
expected interpretation
source or research basis
```

Do not include:

```text
secret data
unbounded corpora
machine-local paths
unreviewed scraped text
copyright-restricted data without permission
```

Exit condition:

```text
Every scenario input is intentional, bounded, documented, and reproducible.
```

---

# 22. Phase 15 — Establish gold baselines

Gold files are reviewed expected outputs.

Do not copy old expected output directly without running the current migrated scenario.

Canonical operation:

```text
gf-wordbench gold update <scenario-id>
```

Required workflow:

```text
run scenario
→ preserve raw output
→ verify markers
→ normalize output
→ build candidate gold
→ show or save diff
→ review linguistic meaning
→ explicitly accept
→ write atomically
→ commit
```

## 22.1 Existing expected-output files

When migrating old expected outputs:

- preserve the old file;
- identify its scenario;
- run the new scenario;
- compare old expectation with normalized candidate;
- explain differences;
- do not silently wrap legacy text in a new header;
- record losses and normalization effects.

## 22.2 Missing required gold

A missing required gold is an error.

It is not automatically created by ordinary validation.

## 22.3 Nondeterministic output

Do not use exact gold for:

```text
unbounded generation
unstable ordering
timestamp-bearing output
random output without stable seed
environment-dependent paths
```

Use assertions or redesign the scenario.

Exit condition:

```text
Every required gold is canonical, reviewed, version-controlled, and reproducible.
```

---

# 23. Phase 16 — Define validation coverage

Complete:

```text
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
```

Coverage should map:

```text
module or subsystem
contract
checkpoint
scenario
input
gold
release criterion
known gap
```

Minimum areas to consider:

```text
module loading
missing linearizations
noun morphology
verb morphology
adjective morphology
pronouns
determiners
structural lexicon
basic clause construction
questions
relatives
coordination
extensions
linearization
parsing
bounded generation
release PGF
```

Do not claim coverage merely because a file compiles.

Exit condition:

```text
Every declared release requirement has explicit validation evidence.
```

---

# 24. Phase 17 — Build the PGF target

When release requires a PGF:

```toml
[validation]
release_requires_pgf = true
```

Document:

```text
entrypoint or entrypoints
expected PGF filename
expected concrete languages
build command policy
artifact directory
timeout
manifest role
runtime/load validation
```

Required success criteria:

```text
process launches
no timeout
successful exit
no fatal diagnostic
expected PGF exists
PGF is non-empty
artifact is current
artifact is inside owned output
artifact is registered in manifest
required scenarios can use it where applicable
```

Do not declare release readiness from `.gfo` success alone.

Exit condition:

```text
The expected current PGF can be built reproducibly from the migrated source.
```

---

# 25. Phase 18 — Documentation completion

Complete every active-project document.

## 25.1 `LANGUAGE_OVERVIEW.md`

Document:

```text
language identity
scope
supported orthography
grammar coverage
entrypoints
major limitations
maintainers
```

## 25.2 `LANGUAGE_ARCHITECTURE.md`

Document:

```text
module layers
dependency direction
ownership
entrypoints
extension strategy
inheritance strategy
```

## 25.3 `MODULE_DEPENDENCY_MAP.md`

Document actual imports and consumers.

## 25.4 `CATEGORY_AND_LINCAT_CONTRACT.md`

Document category structures and cross-file fields.

## 25.5 `MORPHOLOGY_SPEC.md`

Document paradigms, features, irregularity, and ownership.

## 25.6 `SYNTAX_AND_CONSTRUCTOR_RULES.md`

Document constructor behavior, order, agreement, and restrictions.

## 25.7 `VALIDATION_SPEC.md`

Document modes, required stages, scenarios, and expected evidence.

## 25.8 `STATUS_LEDGER.md`

Document known issues, blockers, retired behavior and release impact.

## 25.9 `DECISION_LOG.md`

Document migration strategy and architectural decisions.

## 25.10 `RELEASE_CRITERIA.md`

Document exact gates.

Exit condition:

```text
No active contract, limitation or release requirement exists only in maintainer memory.
```

---

# 26. Legacy identifier cleanup

Search the active project for identifiers belonging to:

```text
old language
old module suffix
old project ID
old source path
old entrypoints
old PGF name
old scenario IDs
old gold names
old audit tool
```

Allowed remaining uses:

```text
migration notes
historical evidence
legacy compatibility fixtures
archived documentation clearly marked historical
```

Prohibited active uses:

```text
project.toml
current scenarios
current gold headers
current entrypoints
current contract providers/consumers
current release scripts
current project examples
```

Canonical checker:

```text
gf-wordbench project contracts check
```

Exit condition:

```text
No stale identifier can influence active validation or release behavior.
```

---

# 27. Migration from `gf-audit`

Existing `gf-audit` assets may be imported, but canonical GF Wordbench writers emit only current forms.

## 27.1 Modes

```text
file -> quick
all  -> diagnostic
```

## 27.2 Application state

Legacy:

```text
.gf_audit_state.json
```

Canonical:

```text
.gf_wordbench_state.json
```

Project-specific values such as source directories, entrypoints, and language identity move to:

```text
project/project.toml
```

Disposable environment paths remain application state.

## 27.3 Run summaries

Legacy unversioned flat or nested summaries may be loaded through migration.

Canonical new summaries use:

```text
schema_id = gf-wordbench.run-summary
schema_version = 1.0
```

## 27.4 Fingerprints

Legacy abbreviated SHA-1 may be imported.

Canonical current fingerprints use full SHA-256.

## 27.5 Reports

Legacy aliases such as:

```text
ai_brief_path
```

may be read.

Canonical current output uses:

```text
artifacts.ai_ready
```

## 27.6 Existing audit outputs

Old run directories are historical evidence.

They must not:

- define active project identity;
- provide current artifacts;
- supply current gold automatically;
- satisfy release gates;
- override `project.toml`.

---

# 28. Baseline run sequence

Canonical first complete sequence:

```text
1. project configuration check
2. contract check
3. quick validation of one low-level provider
4. quick validation of one representative category module
5. checkpoint validation
6. entrypoint validation
7. required scenario validation
8. gold comparison
9. PGF build
10. release validation
```

Target commands:

```text
gf-wordbench schemas check project/project.toml
gf-wordbench project contracts check
gf-wordbench quick --target <project-relative-file>
gf-wordbench checkpoint
gf-wordbench release
```


---

# 29. Baseline evidence package

The migration baseline should retain:

```text
summary.json
summary.md
AI_READY.md
manifest.json
master.log
compile stdout/stderr
scan logs
scenario stdout/stderr
normalized scenario output
gold diffs
gfo inventory
PGF artifact
source fingerprints
GF version
project configuration hash
```

Record the baseline run ID in:

```text
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/docs/RESEARCH_EVIDENCE.md
```

A baseline with known failures may be recorded for progress tracking.

It must not be called a release baseline unless release criteria pass.

---

# 30. Cutover criteria

Cutover means GF Wordbench becomes the authoritative validation workflow for the active language.

Required cutover checks:

```text
[ ] Source baseline preserved
[ ] One active source root declared
[ ] Project identity complete
[ ] project.toml validates
[ ] GF path reproducible
[ ] Module inventory complete
[ ] Dependency map complete
[ ] Interfile contract lock populated
[ ] Known issues recorded
[ ] Entrypoints declared
[ ] Checkpoints declared
[ ] Required scenarios registered
[ ] Scenario inputs version-controlled
[ ] Required gold files reviewed
[ ] Checkpoint validation reproducible
[ ] Entrypoint validation reproducible
[ ] PGF build reproducible when required
[ ] Release criteria documented
[ ] Baseline run retained
[ ] Rollback tested or documented
[ ] Maintainers approve cutover
```

Cutover does not require every known language issue to be solved.

It requires every remaining issue to be explicit and correctly gated.

---

# 31. Release-ready migration criteria

A migrated project is release-ready only when:

```text
no required configuration error
no required checkpoint FAIL or ERROR
no required entrypoint FAIL or ERROR
no required scenario FAIL or ERROR
no required scenario SKIPPED
required gold comparisons pass
required PGF builds and is non-empty
required artifacts appear in manifest
no unresolved release-blocking issues
documentation agrees with source
old active identifiers are absent
source fingerprints are valid
run finalization succeeds
```

Release readiness is stricter than migration completion.

---

# 32. Rollback plan

Before cutover, define:

```text
rollback owner
old source location
old source revision
old build command
old validation command
data created during migration
files safe to remove
files that must be preserved
trigger conditions
```

Rollback triggers may include:

```text
source loss
unresolved identity collision
invalid project layout
unreproducible GF path
unexplained semantic changes
missing history
release artifact mismatch
unsafe migration script behavior
```

Rollback must not delete migration evidence.

A failed migration should leave:

```text
old source intact
migration logs
candidate project
known failure record
```

---

# 33. Post-cutover cleanup

After an approved baseline:

```text
[ ] Mark old active source as archived or upstream-only
[ ] Remove duplicated active validation scripts
[ ] Remove stale generated artifacts
[ ] Remove obsolete local launchers
[ ] Update CI
[ ] Update maintainer instructions
[ ] Update release scripts
[ ] Preserve legacy readers only where required
[ ] Document upstream synchronization
[ ] Tag or commit the migration baseline
```

Do not delete historical source until repository and licensing policies permit it.

---

# 34. Upstream synchronization after migration

If the language remains linked to an upstream repository, document:

```text
upstream repository
tracking branch
import direction
export direction
conflict policy
module rename policy
gold update policy
release authority
```

Possible models:

```text
upstream is authoritative
GF Wordbench project is authoritative
bidirectional maintenance with explicit synchronization
vendored snapshot with periodic refresh
```

A project must not silently alternate between authorities.

---

# 35. Migration risks and controls

| Risk | Control |
|---|---|
| Source copied without history | Record revision or import history |
| Two active source copies | Declare one authoritative root |
| Hidden GF path dependency | Record and validate effective path |
| Stale `.gfo` accepted | Use clean run-owned artifacts |
| Old output accepted as gold | Run current scenario and review diff |
| Module rename breaks consumers | Update one coordinated contract unit |
| Known issue is hidden by migration | Record it in `KNOWN_ISSUES.md` and keep the release gate |
| Wrong language identity persists | Scan active project identifiers |
| GUI state overrides project | Keep identity in `project.toml` |
| Old audit mode remains canonical | Migrate to canonical mode names |
| Release succeeds without PGF | Enforce project release gate |
| Scenario silently skips commands | Require completion markers |
| Migration script damages source | Copy first; atomic project writes |
| Environment secrets persist | Exclude environment dumps and tokens |

---

# 36. Migration anti-patterns

Prohibited:

## 36.1 Copy and declare success

```text
copy *.gf
write project.toml
declare migration complete
```

This omits contracts, scenarios, and baseline evidence.

## 36.2 Rename everything first

Renaming before inventory destroys traceability.

## 36.3 Use old generated artifacts

Old `.gfo` and `.pgf` files are not proof of the migrated source.

## 36.4 Auto-create gold

A failing scenario must not become accepted automatically.

## 36.5 Hide known failures

Excluding failing modules without a documented disposition creates drift.

## 36.6 Put local paths in project configuration

Tool and environment paths do not belong in `project.toml`.

## 36.7 Mix framework and language concerns

Language-specific rules belong under `project/`, not in generic Python defaults.

## 36.8 Preserve undocumented duplicate providers

Duplicates require one selection rule or retirement plan.

## 36.9 Flatten structured categories

Do not simplify lincats merely to make migration compile.

## 36.10 Keep template placeholders active

The active project lock must not remain a generic template.

---

# 37. Migration command

The canonical migration command is:

```text
gf-wordbench project migrate <source-root>
```

It supports:

```text
--dry-run
--strategy copy|external|history-import
--project-id
--language-code
--source-directory
--report
```

It must:

- never overwrite source;
- create a migration plan first;
- identify conflicts;
- produce a file inventory;
- preserve original bytes;
- write project files atomically;
- leave placeholders when facts are unknown;
- avoid generating accepted gold;
- avoid claiming release readiness;
- produce a machine-readable migration report.

Automation may reduce manual copying.

It must not replace linguistic and contract review.

---

# 38. Suggested migration report

Recommended run-local or project-local report fields:

```text
migration ID
source repository
source revision
source root
target project root
strategy
files discovered
files copied
files referenced externally
modules discovered
entrypoints proposed
checkpoints proposed
scenarios discovered
legacy expected outputs discovered
conflicts
warnings
losses
manual actions
validation results
baseline run ID
cutover status
```

Persisting a formal migration-report schema requires a schema-lock update.

Until then, use a reviewed Markdown report or internal structure.

---

# 39. Test requirements

Framework migration tests:

```text
tests/projects/test_project_migration.py
tests/projects/test_source_inventory.py
tests/projects/test_identifier_cleanup.py
tests/projects/test_project_layout.py
tests/projects/test_migration_rollback.py
```

Required cases:

```text
source root missing
source root with spaces
Unicode paths
dirty source repository
duplicate modules
module/file mismatch
multiple entrypoint candidates
old language identifiers
external-source strategy
managed-copy strategy
existing non-empty project directory
dry run
atomic project.toml write
migration interruption
rollback preservation
legacy gf-audit state
legacy summary discovery
generated artifact exclusion
scenario/gold discovery
unsafe path rejection
```

Integration tests use a small fixture language, never the active language project.

---

# 40. Migration review checklist

```text
[ ] Source revision is recoverable
[ ] Migration strategy is documented
[ ] One active source root exists
[ ] Project identity is stable
[ ] Module suffix is consistent
[ ] Source selection is exact
[ ] GF path is reproducible
[ ] GF version is recorded
[ ] Module inventory is complete
[ ] Dependency direction is documented
[ ] Public providers are identified
[ ] Consumers are identified
[ ] Lincat contracts are documented
[ ] Known issues are recorded
[ ] Entrypoints are declared
[ ] Checkpoints are meaningful
[ ] Required scenarios exist
[ ] Scenario inputs are reviewed
[ ] Gold files are reviewed
[ ] Gold writes were explicit
[ ] Compile evidence is current
[ ] PGF evidence is current
[ ] Manifest validates
[ ] Legacy identifiers are removed
[ ] Documentation matches source
[ ] Baseline run is retained
[ ] Rollback is documented
[ ] Cutover is approved
```

---

# 41. Migration record template

```text
Migration ID:
Language:
Project ID:
Module suffix:
Migration owner:
Source repository:
Source revision:
Source dirty state:
Migration strategy:
Old source root:
New authoritative source root:
GF version:
RGL revision:
Entrypoints:
Checkpoints:
Required scenarios:
Optional scenarios:
Expected PGF:
Known failures:
Known temporary implementations:
Normalization version:
Baseline run ID:
Release run ID:
Cutover date:
Rollback location:
Approval:
```

---

# 42. Definition of migration complete

Migration is complete when:

1. the source state is recoverable;
2. the active source root is unambiguous;
3. the project configuration validates;
4. the language identity is consistent;
5. module ownership is documented;
6. cross-file contracts are locked;
7. entrypoints and checkpoints are declared;
8. required scenarios exist;
9. required gold files are reviewed;
10. current compile and scenario evidence exists;
11. the PGF requirement is explicit;
12. known incomplete states are visible;
13. project documents agree with source and behavior;
14. a baseline run is retained;
15. rollback remains possible;
16. maintainers approve cutover.

Migration completion does not automatically mean release readiness.

---

# 43. Definition of release-ready migration

Release-ready migration additionally requires:

1. all required checkpoints pass;
2. all required entrypoints pass;
3. all required scenarios pass;
4. no required validation is skipped;
5. all required gold comparisons pass;
6. the required PGF is built and verified;
7. the manifest is valid;
8. no release-blocking ledger item remains;
9. no unresolved identity drift remains;
10. release validation completes with `overall_status = OK`.

---

# 44. Migration invariants

The migration process must preserve:

1. non-destructive source handling;
2. one active language;
3. one authoritative project identity;
4. one authoritative source root;
5. project-relative canonical paths;
6. environment paths outside project configuration;
7. deterministic entrypoint and checkpoint order;
8. explicit provider/consumer ownership;
9. explicit known issues and constraints;
10. current raw GF evidence;
11. separate stdout and stderr;
12. explicit timeout behavior;
13. reviewed scenario inputs;
14. reviewed gold outputs;
15. explicit gold updates;
16. current PGF provenance;
17. versioned persisted schemas;
18. removal of stale active identifiers;
19. documented rollback;
20. retained migration baseline.

---

# 45. Governing rule

> Do not migrate only the files. Migrate the language project's identity, contracts, validation evidence, release expectations, and maintenance workflow.

The old project may be considered replaced only when the new GF Wordbench project can explain and reproduce what the language is, how its modules depend on one another, how it is validated, and what qualifies it for release.
