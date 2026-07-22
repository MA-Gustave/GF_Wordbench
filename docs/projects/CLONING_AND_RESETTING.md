# GF Wordbench — Cloning and Resetting

**Document ID:** `GF-WB-PROJECTS-CLONING-RESETTING`  
**Status:** Normative  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\projects\CLONING_AND_RESETTING.md`  
**Applies to:** Repository duplication, active-project replacement, generated-evidence cleanup and local-state reset  
**Owner:** GF Wordbench maintainers  
**Primary implementation owners:** `app/project/initializer.py`, `app/project/reset.py`  
**Maintenance entry points:** `scripts/init_project.py`, `scripts/reset_project.py`  
**Project schema:** `gf-wordbench.project/1.0`  
**Application-state schema:** `gf-wordbench.app-state/1.0`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This document defines the safe lifecycle for creating another GF Wordbench working copy and replacing its active language project.

It specifies:

- what a clone contains;
- why one working copy represents one active language project;
- when to clone, reset, clean or migrate;
- how the clean project template is used;
- what must be archived before destructive replacement;
- which paths may be removed;
- which paths must always be preserved;
- how external GF source trees are protected;
- how a reset remains transactional;
- how stale language identity is detected;
- how the result is validated.

The central rule is:

> Create a separate GF Wordbench working copy for a separate active language, and replace project-owned content only through a planned, reviewable and reversible lifecycle operation.

---

## 2. Scope

This document governs:

- Git cloning;
- filesystem duplication;
- Git worktree use;
- clean-clone preparation;
- active-project archival;
- active-project reset from `templates/project/`;
- local run-evidence removal during a new-language reset;
- local application-state removal during a new-language reset;
- project initialization after reset;
- destructive confirmation;
- transactional replacement;
- rollback;
- template-integrity checks;
- old-language identifier checks;
- repository and project validation after cloning or reset.

This document does not govern:

- ordinary source-file editing;
- migration of an existing language implementation;
- framework upgrades;
- release-archive publication;
- source-control branching policy beyond working-copy isolation;
- GF source semantics;
- project configuration field definitions;
- run-retention policy in general;
- application-state field definitions;
- operating-system backup systems.

---

## 3. Related normative documents

```text
docs/REPOSITORY_STRUCTURE.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/projects/PROJECT_MODEL.md
docs/projects/CREATING_A_PROJECT.md
docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md
docs/projects/PROJECT_COMPLETION_CHECKLIST.md
docs/operations/RUN_DIRECTORY_LIFECYCLE.md
docs/operations/CLEANUP_BACKUP_AND_RECOVERY.md
docs/usage/CLI_REFERENCE.md
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

`CLI_REFERENCE.md` owns exact command-line spelling.

This document owns lifecycle semantics and safety invariants.

---

## 4. Normative terminology

- **REPOSITORY COPY**: one filesystem working copy of GF Wordbench.
- **ACTIVE PROJECT**: the language-specific content under `project/`.
- **PROJECT TEMPLATE**: the generic reusable structure under `templates/project/`.
- **CLONE**: creation of a separate repository working copy through Git, a Git worktree or controlled filesystem duplication.
- **RESET**: replacement of the active project with a fresh copy of the project template.
- **NEW-LANGUAGE RESET**: reset that also removes old run evidence and local application state from the new working copy.
- **PROJECT-ONLY RESET**: reset of `project/` while intentionally retaining run evidence or local state.
- **CLEANUP**: removal of generated artifacts without replacing the active project.
- **STATE RESET**: removal of `.gf_wordbench_state.json` only.
- **MIGRATION**: coordinated preservation and transformation of an existing language project.
- **ARCHIVE**: verified copy of content preserved outside the reset destination before destructive replacement.
- **EXTERNAL SOURCE TREE**: GF source root referenced by the project but located outside `project/`.
- **STAGED PROJECT**: temporary validated copy of `templates/project/` prepared before replacing `project/`.
- **RESET PLAN**: deterministic description of every path to copy, preserve, archive, replace or delete.
- **DRY RUN**: plan generation and validation without filesystem mutation.
- **DISCARD**: explicit authorization to replace project content without creating an archive.
- **ROLLBACK**: restoration of the pre-reset active project after a failed replacement.

---

## 5. Single-active-project rule

One GF Wordbench repository copy represents one active language project.

The copy contains:

```text
framework code
framework tests
framework documentation
one active language project
one clean project template
local validation evidence
```

Canonical ownership:

```text
app/                  framework runtime
tests/                framework verification
docs/                 framework documentation
scripts/              maintenance entry points
templates/project/    clean generic project model
project/              active language project
runs/                 generated local evidence
.gf_wordbench_state.json
                      disposable local state
```

### 5.1 Separate languages require separate working copies

Two independently active language projects MUST NOT share one `project/` directory.

Supported isolation models:

```text
separate Git clone
separate Git worktree
controlled filesystem duplicate
```

Each model creates a separate working directory with its own:

```text
project/
runs/
.gf_wordbench_state.json
```

### 5.2 A Git branch is not sufficient by itself

A branch in one working directory does not provide simultaneous filesystem isolation.

Switching branches in one working directory can replace project files while leaving:

```text
untracked runs
local state
virtual environment state
temporary files
editor state
```

For concurrently maintained languages, use separate clones or worktrees.

### 5.3 Package identity does not change per language

A cloned repository remains:

```text
package: gf-wordbench
CLI:     gf-wordbench
framework name: GF Wordbench
```

The active language identity belongs only to:

```text
project/project.toml
project/docs/
project/validation/
referenced GF source
```

Do not rename the Python package, CLI or framework modules for each language.

---

## 6. Choose the correct operation

| Goal | Correct operation |
|---|---|
| Start a separate active language | Clone or create a worktree, then perform a new-language reset and initialize |
| Replace the active project with a blank template | Project reset |
| Preserve and transform the current language | Migration |
| Remove old run directories | Generated-evidence cleanup |
| Forget GUI/local preferences | State reset |
| Update GF Wordbench framework code | Framework upgrade or Git merge/rebase |
| Rename module suffixes while preserving implementation | Breaking project migration |
| Rebuild validation evidence | New validation run |
| Update expected scenario output | Explicit gold-update workflow |
| Repair one project document | Normal project edit, not reset |

### 6.1 Reset is not migration

Use migration when the existing language work remains valuable and must survive in transformed form.

Examples:

```text
move existing source tree
rename language module suffix
convert project.toml schema
adopt a new scenario registry
restructure project documentation
change entrypoints while preserving implementation
```

A reset intentionally creates a clean active-project scaffold.

### 6.2 Reset is not cleanup

Deleting `runs/` does not reset `project/`.

Deleting `.gf_wordbench_state.json` does not reset `project/`.

Replacing `project/` does not automatically modify an external GF source tree.

---

## 7. Canonical new-language workflow

```text
source GF Wordbench repository
             ↓
separate clone or worktree
             ↓
repository preflight
             ↓
new-language reset
             ↓
clean project copied from template
             ↓
project initialization
             ↓
external or internal GF source configuration
             ↓
project contract population
             ↓
repository and project checks
             ↓
first validation run
```

Required phases:

1. create an isolated working copy;
2. verify the clone;
3. preserve old active-project content when required;
4. reset project-owned and local generated content;
5. initialize the new project identity;
6. configure source roots and entrypoints;
7. populate project documentation and contracts;
8. validate structure;
9. begin implementation or migration.

---

# Part I — Cloning

## 8. Preferred cloning methods

Priority:

```text
1. Git clone
2. Git worktree
3. controlled filesystem duplicate
```

Git-based methods are preferred because they:

- preserve tracked content accurately;
- omit ignored local state by default;
- preserve commit identity;
- expose uncommitted changes;
- make later framework updates manageable.

---

## 9. Git clone workflow

Conceptual command:

```text
git clone <gf-wordbench-repository> <destination>
```

Example:

```text
git clone <repository-url> GF_Wordbench_NewLanguage
```

The exact remote and destination are user choices.

### 9.1 Destination requirements

The destination MUST:

- differ from the source working directory;
- not exist, or be an empty approved directory;
- not be inside `project/`;
- not be inside `templates/`;
- not be inside `runs/`;
- not overlap an external GF source tree;
- reside on a filesystem that supports required path operations;
- have enough space for source, tests and future run evidence.

### 9.2 After clone

A Git clone may contain the currently committed active project.

Before assigning another language identity:

1. inspect `project/project.toml`;
2. inspect `project/docs/INTERFILE_CONTRACT_LOCK.md`;
3. run repository preflight;
4. perform a new-language reset;
5. initialize the new project.

A clone is not automatically a clean language template.

### 9.3 Ignored files

A normal Git clone should not contain:

```text
.gf_wordbench_state.json
runs/
.venv/
__pycache__/
.pytest_cache/
build/
dist/
```

Their presence after cloning indicates they are tracked, copied separately or recreated locally and must be reviewed.

---

## 10. Git worktree workflow

A Git worktree is an acceptable separate GF Wordbench copy.

Conceptual command:

```text
git worktree add <destination> <branch-or-commit>
```

### 10.1 Worktree invariants

Each worktree must have its own:

```text
project/
runs/
local state
virtual environment or environment binding
```

### 10.2 Shared Git metadata

Worktrees share repository history.

Lifecycle scripts MUST NOT assume `.git` is always a directory; in a worktree it may be a file that points to shared Git metadata.

### 10.3 Destructive safety

Reset operations must remain inside the selected worktree.

They MUST NOT:

- modify sibling worktrees;
- remove shared Git metadata;
- infer the repository root from the parent of the common Git directory;
- clean untracked files globally across worktrees.

---

## 11. Controlled filesystem duplication

Filesystem duplication is supported when Git is unavailable or the source includes uncommitted framework work that must be preserved.

### 11.1 Required exclusions

A clean duplicate SHOULD exclude:

```text
.venv/
venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
build/
dist/
coverage/
htmlcov/
runs/
.gf_wordbench_state.json
temporary files
editor caches
```

### 11.2 Required inclusions

The duplicate MUST include:

```text
app/
tests/
docs/
project/
templates/
scripts/
pyproject.toml
README.md
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
LICENSE.md
launchers when supported
repository metadata when intentionally copied
```

### 11.3 Symlinks and junctions

Filesystem duplication must handle symlinks and Windows junctions deliberately.

Default safe policy:

```text
preserve link identity or reject
do not recursively follow unknown links
```

Following a link can copy or later delete content outside the intended repository.

### 11.4 Post-copy validation

A filesystem duplicate requires:

```text
repository root validation
template validation
old-language identifier scan
generated-file scan
path-overlap check
strict repository check
```

---

## 12. Clone identity

The working-copy directory name is not the active project ID.

Example:

```text
C:\work\GF_Wordbench_French
```

does not define:

```text
project.id
language code
module suffix
entrypoint
```

Those values come from `project/project.toml`.

The clone destination may be renamed without changing project identity, provided local paths and tools are revalidated.

---

## 13. Clone preflight

Before resetting or initializing a clone, verify:

```text
repository root found
pyproject.toml found
app/ found
docs/ found
templates/project/ found
template contract lock found
project/ found or intentionally absent
Git/worktree boundaries understood
destination differs from source
no active lifecycle operation
no running audit owned by this copy
no unsafe path overlap
```

Recommended structural check:

```text
gf-wordbench repository check --strict
```

Exact syntax belongs to `CLI_REFERENCE.md`.

---

## 14. Clone cleanliness check

A clone intended for a new language should be checked for:

```text
old `.gf_wordbench_state.json`
old `runs/`
old generated `.gfo`
old generated `.pgf`
old normalized `.out`
old compile and scenario logs
old absolute local paths
old-language identifiers
old project decisions
old scenario IDs
old gold files
old project lock values
```

Tracked active-project content is expected before reset.

Generated and local content should normally be absent.

---

## 15. Virtual environment policy

A Python virtual environment is local machine state.

It SHOULD be recreated in the clone.

Do not rely on copying:

```text
.venv/
venv/
```

Reasons:

- interpreter paths may be absolute;
- platform binaries may differ;
- editable-install paths may point to the source copy;
- dependency state may be stale.

The clone’s environment is validated independently.

---

# Part II — Reset scopes

## 16. Canonical reset scopes

GF Wordbench distinguishes four independent operations.

### 16.1 New-language reset

Default scope for repurposing a clone:

```text
replace project/
remove local runs/
remove local application state
preserve framework and template
preserve external GF source tree
```

### 16.2 Project-only reset

Scope:

```text
replace project/
retain runs/ intentionally
retain application state intentionally
```

This is exceptional.

It requires explicit flags or equivalent confirmation because retained evidence may refer to the previous active project.

### 16.3 Generated-evidence cleanup

Scope:

```text
remove selected or all generated run directories
preserve project/
preserve state unless cleanup policy says otherwise
```

This is governed primarily by operations documentation.

### 16.4 State reset

Scope:

```text
remove `.gf_wordbench_state.json`
preserve project/
preserve runs/
```

This is governed by `APPLICATION_STATE_REFERENCE.md`.

---

## 17. Canonical new-language reset boundary

Paths replaced or removed:

```text
project/
runs/
.gf_wordbench_state.json
```

Paths preserved:

```text
app/
tests/
docs/
templates/
scripts/
pyproject.toml
README.md
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
LICENSE.md
Git metadata
launchers
external GF source trees
```

### 17.1 Optional absent paths

A missing:

```text
runs/
.gf_wordbench_state.json
```

is normal.

Reset remains idempotent for these paths.

### 17.2 `project/` must be recreated

After a successful reset:

```text
project/
```

exists and is structurally valid as a clean template copy.

---

## 18. Active project structure

The reset target mirrors the required template structure:

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
    ├── gold/
    │   └── README.md
    └── inputs/
        └── README.md
```

A reset copies the template structure.

It does not invent language-specific scenario, gold or input content.

---

## 19. Template source

Canonical source:

```text
templates/project/
```

### 19.1 Template invariants

The template must contain:

- generic instructions;
- placeholders;
- empty registries;
- generic validation guidance;
- no active-language identity;
- no old-language identity;
- no generated evidence;
- no local absolute paths;
- no completed project decisions presented as current;
- no populated release evidence.

### 19.2 Mirror invariants

Required relative paths in:

```text
project/
templates/project/
```

must match.

Content differs:

```text
template = generic
active project = populated
```

### 19.3 Template immutability during reset

A project reset reads from `templates/project/`.

It MUST NOT modify the template.

If template validation fails, reset stops before changing `project/`.

---

# Part III — Reset safety

## 20. Reset preconditions

Before filesystem mutation, the reset operation MUST verify:

```text
repository root
active project path
template project path
path containment
path non-overlap
template completeness
template cleanliness
active-operation state
archive or discard policy
destination write permissions
temporary staging capability
rollback capability
```

### 20.1 Repository root proof

The root SHOULD be verified through multiple stable markers, such as:

```text
pyproject.toml
app/
docs/REPOSITORY_STRUCTURE.md
docs/PERSISTED_SCHEMA_LOCK.md
templates/project/
```

Current working directory alone is insufficient.

### 20.2 Path containment

The resolved project path MUST be exactly:

```text
<repository-root>/project
```

unless a future project model explicitly supports another canonical location.

The reset operation must reject:

```text
repository root itself
repository parent
templates/project/
app/
tests/
docs/
scripts/
filesystem root
drive root
user home
external source root
```

### 20.3 Path overlap

After resolving symlinks or junction policy, these must be distinct:

```text
repository root
project path
template path
archive destination
external source roots
temporary staging path
```

### 20.4 Active audit

Reset MUST NOT begin while the same working copy has an active audit or lifecycle operation.

Runtime coordination may use a temporary lock.

A temporary lock is not a persisted project contract and must be removed after completion or safely recognized as stale.

---

## 21. Git working-tree preflight

When Git metadata is available, the reset planner SHOULD identify:

```text
modified tracked files
untracked files
ignored generated files
current branch
worktree root
```

### 21.1 Uncommitted active-project changes

If `project/` contains uncommitted changes:

- archive is required; or
- explicit discard confirmation is required.

### 21.2 Framework changes

Uncommitted changes outside reset scope do not need to block reset automatically.

They MUST be listed in the plan so the user knows the working copy is not clean.

### 21.3 No automatic Git commands

Reset MUST NOT silently:

```text
git reset --hard
git clean -fdx
git checkout .
git restore .
git stash
git commit
```

GF Wordbench owns only its explicit filesystem plan.

---

## 22. Dry-run requirement

A destructive reset must support an equivalent of:

```text
gf-wordbench project reset --dry-run
```

The dry run performs all non-mutating validations and prints or returns a deterministic plan.

### 22.1 Dry-run output

The plan includes:

```text
repository root
project path
template path
archive destination or discard mode
paths to preserve
paths to replace
paths to delete
external source roots detected
run count and approximate size
state-file presence
Git-change summary when available
validation steps
rollback strategy
warnings
```

### 22.2 Dry-run invariants

Dry run MUST NOT:

```text
create the staged project
create an archive
delete files
replace project/
clear runs/
clear state
write project.toml
modify Git state
```

A harmless temporary probe file MAY be used only when necessary to test write capability and must be removed immediately.

---

## 23. Destructive authorization

A reset that would replace non-template project content requires one of:

```text
verified archive destination
explicit discard authorization
```

### 23.1 Interactive confirmation

The confirmation SHOULD show:

- repository root;
- active project ID when readable;
- paths affected;
- whether an archive will be created;
- whether runs will be removed;
- whether state will be removed;
- external paths that will not be touched.

The user SHOULD confirm with the current project ID or another specific token, not a generic accidental Enter.

### 23.2 Non-interactive confirmation

Automation requires explicit destructive flags equivalent to:

```text
--yes
```

and either:

```text
--archive <path>
```

or:

```text
--discard
```

A non-interactive reset must not prompt and must fail when authorization is incomplete.

### 23.3 Default behavior

The default must favor preservation.

Absence of archive and absence of explicit discard means:

```text
do not reset
```

---

# Part IV — Archival

## 24. Archive purpose

An archive preserves active-project work before reset.

It is not a release package and does not make uncommitted work valid.

### 24.1 Required archive content

The project archive contains the complete current:

```text
project/
```

including:

```text
project.toml
project documentation
scenario files
gold files
input files
project README
project contract lock
```

### 24.2 Optional archive content

At explicit request, an archive may also contain selected:

```text
release-significant run directories
migration notes
Git status text
framework commit identifier
```

### 24.3 Excluded by default

Do not archive by default:

```text
.gf_wordbench_state.json
all runs/
virtual environments
Python caches
build output
external GF source tree
credentials
environment dumps
```

### 24.4 External source warning

If `project.toml` references an external GF source tree, archiving `project/` alone does not preserve that source.

The reset plan must state this clearly.

Backing up the external source is a separate explicit operation.

---

## 25. Archive destination

The archive destination SHOULD be outside the repository being reset.

Reasons:

- it must survive repository cleanup;
- it must not become active project content;
- it must not be copied back from the template;
- it must not become a generated run artifact;
- it must not create a new permanent top-level repository boundary.

Allowed forms:

```text
external directory
external ZIP archive
approved backup location
version-control commit outside the reset operation
```

### 25.1 Destination restrictions

Reject an archive destination that resolves inside:

```text
project/
templates/project/
runs/ scheduled for deletion
temporary staging directory
```

An archive inside the repository root is discouraged and must not overlap reset scope.

---

## 26. Archive verification

Before destructive replacement, archive creation MUST be verified.

Verification includes:

```text
every required project path copied
file count compared
file sizes compared
content hashes compared where practical
archive can be reopened
destination differs from source
no copy errors remain
```

A failed or incomplete archive blocks reset.

### 26.1 Symlink behavior

The archive operation follows the declared symlink policy.

It must not unexpectedly copy linked external trees.

### 26.2 Archive immutability

After verification and before reset, the archive is treated as read-only evidence for the operation.

GF Wordbench does not continue writing project changes into it.

---

## 27. Discard mode

Discard mode replaces the active project without creating an archive.

It is valid only when:

- the user explicitly authorizes it;
- the plan identifies exactly what is lost;
- no misleading “backup complete” status is shown;
- external source trees remain untouched;
- transactional replacement still protects against partial reset.

Discard mode does not permit broad repository deletion.

---

# Part V — Transactional replacement

## 28. Reset phases

Canonical reset phases:

```text
PLAN
PREFLIGHT
ARCHIVE_OR_AUTHORIZE_DISCARD
STAGE
VALIDATE_STAGE
SWAP
VALIDATE_ACTIVE_PROJECT
CLEAN_LOCAL_GENERATED_STATE
FINALIZE
```

Each phase has an explicit result.

---

## 29. Phase 1 — Plan

The reset planner resolves:

```text
repository root
active project
template project
staging path
rollback path
archive path
runs path
state path
external source roots
preserve set
replace set
delete set
```

No mutation occurs.

---

## 30. Phase 2 — Preflight

Preflight validates:

- path safety;
- template completeness;
- write capability;
- archive policy;
- concurrency;
- Git information when available;
- project structure;
- source-tree protection.

A preflight error produces no mutation.

---

## 31. Phase 3 — Archive or discard authorization

When archive mode is selected:

1. create archive;
2. verify archive;
3. record verification result.

When discard mode is selected:

1. verify explicit authorization;
2. record discard mode in operation output.

No project replacement begins before this phase succeeds.

---

## 32. Phase 4 — Stage

The reset operation copies:

```text
templates/project/
```

to a temporary sibling staging path.

Example conceptual path:

```text
.<project-reset-stage>-<operation-id>/
```

The exact temporary name is private implementation detail.

### 32.1 Staging rules

The staged copy:

- resides on the same filesystem when atomic rename is required;
- does not overwrite `project/`;
- preserves required file content and permissions where appropriate;
- contains no active-language additions;
- contains no generated artifacts;
- receives no project identity yet unless reset and initialization are one explicitly coordinated transaction.

---

## 33. Phase 5 — Validate staged project

Before swap, validate:

```text
all required relative paths exist
project.toml parses as the template form
template contract lock exists
no local absolute paths
no known active-language identifiers
no generated scenario output
no run artifacts
no invalid symlink escapes
UTF-8 text where required
project/template mirror rules
```

A staged validation failure removes the stage and leaves `project/` unchanged.

---

## 34. Phase 6 — Swap

Preferred same-filesystem sequence:

1. rename existing `project/` to a temporary rollback path;
2. rename staged project to `project/`;
3. verify `project/` exists;
4. retain rollback path until active-project validation succeeds.

### 34.1 No delete-first strategy

The following is prohibited:

```text
delete project/
then copy template
```

A copy failure would leave no active project.

### 34.2 Platform limitations

When atomic directory rename is unavailable, the implementation must use the safest supported equivalent and retain rollback material until validation succeeds.

The fallback must be documented and tested for Windows.

---

## 35. Phase 7 — Validate active project

Validate the newly active:

```text
project/
```

Checks include:

```text
required structure
project schema parseability
template placeholder policy
contract lock presence
path containment
no old active-project files
no generated evidence
no template mutation
```

The clean reset project may still contain required placeholders and therefore may not yet be runnable.

That is valid before initialization.

---

## 36. Phase 8 — Clean local generated state

For a new-language reset, after project replacement succeeds:

```text
remove runs/
remove `.gf_wordbench_state.json`
```

### 36.1 Ordering

Generated cleanup occurs after the project swap has succeeded and rollback remains available.

### 36.2 Run deletion

Run removal follows run-cleanup path safety.

Only the canonical run root for this repository copy is affected.

### 36.3 State deletion

State deletion follows the application-state reset contract.

A missing state file is not an error.

### 36.4 Cleanup failure

If project reset succeeds but generated cleanup fails:

- report partial completion clearly;
- do not claim a fully clean new-language reset;
- preserve the valid new `project/`;
- identify remaining stale paths;
- permit explicit cleanup retry.

Rollback of the new project is not automatically required for a failed non-authoritative cleanup unless policy defines a single all-or-nothing transaction.

---

## 37. Phase 9 — Finalize

After all required validation succeeds:

1. delete the temporary rollback directory;
2. delete remaining staging artifacts;
3. release lifecycle lock;
4. emit operation summary;
5. list next initialization steps;
6. return success.

If an external archive was created, it remains untouched.

---

## 38. Rollback behavior

### 38.1 Before swap

Failure leaves active project unchanged.

### 38.2 During swap

If the staged project cannot become active, restore the rollback directory to `project/`.

### 38.3 After swap but before validation

If active-project validation fails:

1. move invalid new project aside or remove it safely;
2. restore rollback project;
3. verify restored project;
4. report rollback success or failure;
5. preserve diagnostic evidence.

### 38.4 Rollback failure

Rollback failure is a critical lifecycle error.

The operation must report:

```text
current project path state
rollback path
archive path
manual recovery instructions
paths not to delete
```

It MUST NOT continue with run or state cleanup.

---

## 39. Temporary artifact cleanup

Temporary staging and rollback paths are private operation artifacts.

They SHOULD be removed after success.

After failure, a path may be retained when required for recovery.

The next lifecycle operation must detect stale temporary paths and refuse unsafe reuse until they are resolved.

---

# Part VI — Project initialization

## 40. Reset output versus initialized project

A reset produces a clean template-derived project.

An initialized project has populated identity and validated paths.

These are separate states:

```text
clean scaffold
      ↓
initialization
      ↓
active project
```

### 40.1 Why separation matters

Reset should not guess:

```text
project ID
language name
language code
module suffix
source root
entrypoints
scenario IDs
expected PGF
```

Initialization receives those decisions explicitly.

---

## 41. Canonical initialization flow

Conceptual operation:

```text
gf-wordbench project init
```

The exact CLI parameters belong to `CLI_REFERENCE.md`.

The initializer must:

1. verify a clean or explicitly allowed project scaffold;
2. collect required project identity;
3. populate `project/project.toml`;
4. populate project documentation identity fields;
5. populate the active project contract lock;
6. validate paths;
7. preserve empty scenario/gold registries until explicitly defined;
8. reject unresolved required placeholders;
9. write atomically;
10. run project checks.

---

## 42. Initialization input

Required identity normally includes:

```text
project ID
display name
language name
language code
module suffix where used
source-root relationship
project owner
```

Required validation configuration is added when known:

```text
source directory
source glob
GF path parts
entrypoints
checkpoints
required scenarios
optional scenarios
release targets
expected artifacts
```

The project schema reference owns exact field names.

---

## 43. Placeholder policy

Placeholders are valid in:

```text
templates/project/
fresh reset scaffold before initialization
```

Placeholders are not valid in a fully initialized active project when they affect required contracts.

Examples:

```text
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<PROJECT_ROOT>
<SOURCE_DIR>
<ENTRYPOINT>
<EXPECTED_PGF>
```

The initializer must report unresolved placeholders.

---

## 44. Scenario and gold initialization

Initialization MUST NOT invent linguistic expectations.

It may create:

```text
empty scenario registry
documented example disabled by default
README guidance
```

It MUST NOT create passing gold files without executed and reviewed scenario output.

A required gold is added only through the explicit scenario and gold workflow.

---

## 45. External GF source tree

The GF source tree may be external to GF Wordbench.

Example relationship:

```text
GF Wordbench clone
    project/project.toml
        → external GF source root
```

### 45.1 Reset rule

Project reset never deletes or rewrites the external source tree.

### 45.2 Initialization rule

Initialization stores or resolves the source relationship through project configuration.

### 45.3 Validation rule

Before use, GF Wordbench validates:

```text
source root exists
source root is approved
entrypoints exist
path containment policy is satisfied
GF path resolution is valid
```

### 45.4 Source inside `project/`

When language source is intentionally stored inside `project/`, it is project-owned and will be archived and replaced by reset.

The reset plan must detect and state this consequence.

---

# Part VII — Retained evidence and identity

## 46. Runs from the previous active project

Old runs are evidence for the previous project identity.

They must not become evidence for the new active language.

Default new-language reset removes local:

```text
runs/
```

after archival decisions.

### 46.1 Retaining runs

Retaining old runs requires explicit project-only reset behavior.

Retained runs:

- remain immutable;
- must be labeled as previous-project evidence;
- must not be selected as the new project’s regression baseline automatically;
- must not define active language identity;
- may contain absolute paths and old identifiers.

### 46.2 Recommended preservation

Release-significant old runs should be archived outside the new-language working copy before deletion.

---

## 47. Application state from the previous project

Old application state may contain:

```text
old project root
old target file
old RGL path
old GF executable path
old output root
old last-run pointer
old mode preference
```

Default new-language reset removes:

```text
.gf_wordbench_state.json
```

The new application session starts with safe defaults.

State must never supply old language identity.

---

## 48. Git history

A clone normally preserves repository history.

Project reset changes the working tree; it does not erase history.

Recommended workflow:

1. commit or archive valuable active-project work;
2. create the new working copy;
3. perform reset;
4. inspect changes;
5. commit the clean new-language baseline;
6. initialize and commit project identity separately when useful.

Separating reset and initialization commits makes review easier.

GF Wordbench MUST NOT create commits automatically.

---

## 49. Old-language identifier removal

After a new-language reset and initialization, active-project paths must contain no stale language identity from the previous project.

Scan at least:

```text
project/project.toml
project/README.md
project/docs/
project/validation/
scenario filenames
gold filenames
input filenames
active project lock
```

Framework directories should also be checked for accidental language drift:

```text
app/
tests/
docs/
templates/
scripts/
```

Historical names may remain only in:

```text
documented legacy fixtures
migration tests
historical decision records where clearly historical
external archives
Git history
```

---

## 50. Absolute path removal

A new-language clone must not inherit local absolute paths in tracked project or template content.

Check for:

```text
Windows drive paths
UNC paths
POSIX home paths
user-specific directories
old repository roots
old RGL roots
old GF executable paths
```

Local paths belong in disposable application state or explicit local configuration policy, not the reusable template.

---

# Part VIII — Project-only reset

## 51. When project-only reset is valid

Project-only reset may be used when:

- rebuilding the active project scaffold for the same working copy;
- preserving old runs for forensic comparison;
- preserving local environment selections intentionally;
- testing initializer behavior;
- operating in an isolated test fixture.

### 51.1 Required warning

The operation must warn that retained runs and state may refer to replaced project content.

### 51.2 Regression baseline

After project-only reset, previous runs are not eligible as regression baselines until project identity and compatibility are revalidated.

### 51.3 State reconciliation

At next startup, state values pass through normal validation.

Invalid paths fall back safely.

---

# Part IX — Cleanup and state reset

## 52. Generated-evidence cleanup

Generated cleanup removes only approved run-owned content.

It MUST NOT remove:

```text
project/
templates/
GF source
gold files
project inputs
framework tests
framework docs
```

Run cleanup uses the run directory lifecycle and retention contract.

It is not implemented by broad filename searches for `.gfo`, `.pgf` or `.out` across the repository.

---

## 53. Application-state reset

Canonical artifact:

```text
.gf_wordbench_state.json
```

A state reset:

- removes or replaces only application state;
- is idempotent;
- does not remove runs;
- does not replace the project;
- does not change project configuration;
- does not delete external source.

Exact behavior is defined by `APPLICATION_STATE_REFERENCE.md`.

---

## 54. Template reset

There is no normal user operation that resets `templates/project/` from `project/`.

The direction is one-way:

```text
templates/project/
        ↓
project/
```

Copying the active project back into the template is prohibited because it can introduce:

```text
active-language identity
local paths
scenarios
gold expectations
temporary decisions
generated evidence
```

Template changes are framework-maintainer changes and require template review.

---

# Part X — Command surface

## 55. Logical lifecycle operations

The final CLI should expose operations equivalent to:

```text
gf-wordbench repository check
gf-wordbench project reset
gf-wordbench project init
gf-wordbench project check
gf-wordbench state reset
```

Exact flags and spelling belong to `CLI_REFERENCE.md`.

### 55.1 Reset capabilities

The project reset operation must support logical equivalents of:

```text
dry run
archive destination
explicit discard
new-language cleanup
project-only retention
non-interactive confirmation
```

### 55.2 No clone wrapper required

GF Wordbench does not need to implement a second Git client.

Repository cloning remains a Git or filesystem operation.

GF Wordbench provides:

```text
clone preflight
reset
initialization
validation
```

This avoids unnecessary source-control complexity.

---

## 56. Conceptual command examples

Safe archive flow:

```text
gf-wordbench project reset --dry-run --archive <external-path>
gf-wordbench project reset --archive <external-path>
gf-wordbench project init
gf-wordbench project check
```

Explicit discard flow:

```text
gf-wordbench project reset --dry-run --discard
gf-wordbench project reset --discard --yes
```

State-only reset:

```text
gf-wordbench state reset
```

These examples define intent.

`CLI_REFERENCE.md` owns final syntax.

---

# Part XI — Validation after cloning and reset

## 57. Post-clone validation

After creating the working copy, verify:

```text
repository root valid
framework imports valid
template structure valid
project/template mirror valid
state absent or valid
runs absent or intentionally retained
virtual environment recreated
GF executable resolved
RGL path resolved
```

---

## 58. Post-reset validation

A clean reset must prove:

```text
project/ exists
project/ derives from the current template
required project paths exist
old project-only files are absent
template remains unchanged
runs removed when requested
state removed when requested
external source untouched
no stale staging path
no stale rollback path
archive verified when requested
```

---

## 59. Post-initialization validation

An initialized project must prove:

```text
project schema valid
project identity complete
required placeholders resolved
source root valid or explicitly pending
entrypoints registered when required
checkpoints registered when required
scenario IDs unique
gold mappings valid
project contract lock populated
documentation identity consistent
no old-language identifiers
```

---

## 60. Repository checks

Recommended strict checks:

```text
gf-wordbench repository check --strict
gf-wordbench project check
```

The checks should detect:

- missing required paths;
- project/template structural mismatch;
- active-language identifiers in the template;
- old-language identifiers in the active project;
- absolute paths in reusable files;
- generated artifacts in source-owned directories;
- unresolved required placeholders;
- missing project lock;
- invalid project schema;
- missing scenario or gold mappings;
- stale artifact names;
- unexpected top-level directories.

---

## 61. First validation run

A freshly reset but uninitialized scaffold is not expected to compile.

After initialization and source configuration:

1. run project checks;
2. run a quick validation;
3. validate configured checkpoints;
4. add required scenarios;
5. review gold output explicitly;
6. run release validation only after release criteria are defined.

Do not create empty passing evidence merely to satisfy the structure.

---

# Part XII — Error handling

## 62. Error categories

Lifecycle operations should distinguish:

```text
configuration error
path-safety error
template error
archive error
authorization error
concurrency error
staging error
swap error
rollback error
cleanup error
validation error
```

These are lifecycle errors, not GF language-validation failures.

---

## 63. No-mutation failures

The following must fail before mutation:

```text
repository root uncertain
project path unsafe
template missing
template invalid
archive destination unsafe
archive creation failed
explicit authorization missing
active audit detected
unsupported symlink layout
insufficient permissions detected
```

---

## 64. Partial-completion reporting

A lifecycle operation may partially complete only at well-defined boundaries.

The final result must report:

```text
project replacement completed: yes/no
rollback completed: yes/no/not-needed
archive completed: yes/no/not-requested
runs cleanup completed: yes/no/not-requested
state reset completed: yes/no/not-requested
post-validation completed: yes/no
remaining manual actions
```

A partial result must not be labeled simply `success`.

---

## 65. Exit behavior

Recommended command result categories:

```text
0  operation completed
1  operation refused or validation failed
2  invalid arguments or unsafe plan
3  filesystem or runtime error
4  rollback required or failed
```

The definitive exit-code registry belongs to `docs/reference/EXIT_CODES.md`.

This document does not create a competing global registry.

---

# Part XIII — Security

## 66. Filesystem security

Reset code must treat every path as untrusted until resolved.

Required controls:

- canonical root verification;
- containment checks;
- `..` rejection after normalization;
- drive-root rejection;
- filesystem-root rejection;
- user-home rejection when unintended;
- symlink/junction policy;
- archive overlap rejection;
- stage overlap rejection;
- external-source protection;
- no shell interpolation for copy/delete commands;
- bounded error messages;
- no credential capture.

---

## 67. Deletion policy

Deletion is restricted to exact approved roots.

Prohibited approaches:

```text
recursive delete from current working directory
glob-based deletion of every `project` directory
recursive search and delete of `.gfo` or `.pgf`
Git clean across the whole repository
following arbitrary symlinks
deleting a path because its name contains `run_`
```

The reset plan provides the exact deletion set before execution.

---

## 68. Windows-specific safety

The implementation must handle:

```text
drive-letter paths
UNC paths
junctions
reparse points
read-only files
antivirus file locks
open editor handles
case-insensitive path comparison
long paths
atomic rename limitations
```

### 68.1 Case-insensitive comparison

On Windows, paths that differ only by case may identify the same location.

Containment and overlap checks must account for this.

### 68.2 Locked files

A locked file blocks the affected phase.

The operation must not continue by skipping the file silently.

---

## 69. Secrets

Archives, plans and logs MUST NOT capture:

```text
passwords
tokens
private keys
credential files
complete environment dumps
secret command arguments
```

Local absolute paths may be recorded because they are required for safety, but support exports may redact them.

---

# Part XIV — Concurrency

## 70. One lifecycle writer

Only one project lifecycle operation may modify a working copy at a time.

The operation may use a temporary lock containing bounded metadata such as:

```text
operation ID
process ID
start time
repository root
operation type
```

The lock must not contain secrets or project configuration.

### 70.1 Stale lock

A stale lock is not removed blindly.

The implementation verifies that no owning process or operation remains before cleanup.

### 70.2 Audit coordination

A running audit blocks reset.

A read-only repository check may run concurrently when it does not observe an intermediate swap state.

---

# Part XV — Implementation boundaries

## 71. `app/project/initializer.py`

Owns:

```text
clean scaffold verification
identity population
project.toml creation or update
project-document placeholder population
project-lock initialization
post-initialization validation
```

It does not clone Git repositories.

---

## 72. `app/project/reset.py`

Owns:

```text
reset planning
path-safety validation
archive coordination
staging
stage validation
transactional swap
rollback
new-language generated cleanup coordination
operation result
```

It does not:

```text
modify GF source semantics
update gold expectations
run Git reset/clean
rewrite framework files
modify template content
delete external source trees
```

---

## 73. Maintenance scripts

```text
scripts/init_project.py
scripts/reset_project.py
```

are thin wrappers around reusable application services.

They must not contain a second reset or initialization implementation.

They:

- parse maintenance arguments;
- call project services;
- render plans and results;
- preserve exit semantics.

---

## 74. GUI integration

A GUI may expose clone guidance, reset planning and initialization.

The GUI must:

- call the same project services as the CLI;
- show the exact plan;
- require explicit confirmation;
- remain responsive without hiding operation state;
- display archive and rollback paths;
- never delete by directly traversing widgets’ path text.

A GUI must not implement independent reset logic.

---

## 75. Report and audit separation

Project lifecycle operations do not create normal audit reports.

They may create a bounded operation log.

They MUST NOT:

```text
write fake summary.json
write release evidence
classify GF failures
update gold files
publish PGF artifacts
```

A first audit is a separate post-initialization operation.

---

# Part XVI — Tests

## 76. Unit tests

Recommended file:

```text
tests/unit/project/test_reset.py
```

Required cases:

```text
valid repository root
missing repository root markers
project path equals repository root
template path equals project path
archive path inside project
archive path inside runs scheduled for deletion
external source overlap
missing template
incomplete template
template with active-language identity
template with absolute path
dry-run no mutation
archive required by default
discard requires explicit authorization
missing runs accepted
missing state accepted
project-only reset plan
new-language reset plan
```

---

## 77. Staging and swap tests

Required cases:

```text
stage copied completely
stage validation failure leaves project unchanged
existing project renamed to rollback
staged project becomes active
active validation succeeds
active validation fails and restores rollback
rename failure restores original state
stale staging path detected
stale rollback path detected
temporary paths cleaned after success
temporary recovery path preserved after failure
```

---

## 78. Archive tests

Required cases:

```text
archive complete project
archive preserves nested files
archive verification detects missing file
archive verification detects changed content
ZIP archive can be reopened
archive destination collision
archive destination inside reset scope
symlink policy
external source excluded by default
optional selected runs included explicitly
legacy/local state excluded by default
failed archive blocks reset
```

---

## 79. Cleanup tests

Required cases:

```text
new-language reset removes runs
new-language reset removes state
project-only reset retains runs
project-only reset retains state
cleanup failure reported as partial
external source unchanged
template unchanged
framework files unchanged
Git metadata unchanged
```

---

## 80. Initialization tests

Recommended file:

```text
tests/unit/project/test_initializer.py
```

Required cases:

```text
clean scaffold accepted
non-clean scaffold rejected or explicitly handled
project ID populated
language identity populated
project.toml validates
project lock populated
required document placeholders populated
unresolved required placeholders detected
scenario gold not invented
atomic project.toml write
initialization rollback after write failure
```

---

## 81. Contract tests

Recommended file:

```text
tests/contracts/test_project_lifecycle_contract.py
```

Contract tests MUST verify:

- one active project per working copy;
- template-to-project copy direction;
- project/template required path mirror;
- reset preserves framework directories;
- reset never writes template;
- reset never deletes external source;
- reset requires archive or explicit discard;
- dry run performs no mutation;
- project replacement is staged;
- delete-first replacement is absent;
- rollback exists;
- CLI and GUI use the same service;
- scripts are thin wrappers;
- state and runs follow declared scope;
- old-language identity scan runs;
- canonical project schema is used;
- no Git destructive commands are invoked implicitly.

---

## 82. Integration tests

Use temporary repositories.

Required cases:

```text
Git clone then new-language reset
Git worktree reset
filesystem duplicate reset
Windows path containing spaces
Unicode repository path
read-only project file
open/locked file failure where testable
external source outside repository
source inside project
uncommitted project changes
archive and reset
discard and reset
rollback after injected swap failure
post-reset strict repository check
post-initialization project check
```

Integration tests must never target the developer’s real repository.

---

## 83. Property tests

Useful bounded properties:

```text
dry run never changes filesystem state
preserve-set hashes remain unchanged
template hashes remain unchanged
external-source hashes remain unchanged
successful reset project tree equals template tree before initialization
failed preflight leaves all hashes unchanged
failed stage validation leaves active project unchanged
successful rollback restores active-project hashes
delete set is always inside approved reset roots
archive destination never overlaps delete set
```

---

# Part XVII — Drift prevention

## 84. Drift indicators

Probable lifecycle drift exists when:

- one repository copy contains several active project configurations;
- project identity is inferred from the clone folder name;
- a branch switch is treated as safe simultaneous project isolation;
- the Python package is renamed per language;
- the active project is copied back into the template;
- reset modifies `templates/project/`;
- reset deletes before staging succeeds;
- reset deletes external GF source;
- reset silently runs `git clean`;
- reset proceeds without archive or explicit discard;
- dry run creates or deletes files;
- old runs become new-project regression evidence;
- old state supplies new language identity;
- project and template required paths differ;
- the template contains absolute local paths;
- the template contains a populated language lock;
- old-language names remain in active project files;
- reset invents scenario or gold content;
- initialization guesses entrypoints;
- archive verification is skipped;
- rollback material is deleted before validation;
- project replacement logic exists in both script and service;
- GUI performs direct recursive deletion;
- temporary reset artifacts remain after success;
- a partial cleanup is reported as full success;
- state reset deletes run evidence;
- project reset is used instead of required migration.

Detected drift must be resolved through coordinated lifecycle, schema and documentation changes.

---

## 85. Change workflow

A cloning or reset contract change is complete only when all applicable items are checked:

```text
[ ] operation scope reviewed
[ ] repository-root proof reviewed
[ ] project/template boundaries reviewed
[ ] external-source protection reviewed
[ ] archive policy reviewed
[ ] discard policy reviewed
[ ] dry-run behavior reviewed
[ ] symlink/junction policy reviewed
[ ] staging strategy reviewed
[ ] atomic swap behavior reviewed
[ ] rollback behavior reviewed
[ ] run cleanup reviewed
[ ] state reset reviewed
[ ] Git/worktree behavior reviewed
[ ] CLI integration reviewed
[ ] GUI integration reviewed
[ ] initializer integration reviewed
[ ] reset service updated
[ ] scripts updated
[ ] repository structure updated when required
[ ] project model updated when required
[ ] schema locks reviewed
[ ] unit tests updated
[ ] contract tests updated
[ ] integration tests updated
[ ] migration guidance updated
[ ] this document updated
```

---

## 86. New-language checklist

```text
[ ] separate clone or worktree created
[ ] destination verified
[ ] ignored local files absent or reviewed
[ ] virtual environment recreated
[ ] repository strict check completed
[ ] old active project archived or explicitly discarded
[ ] reset dry run reviewed
[ ] project replaced from template
[ ] runs cleared
[ ] application state cleared
[ ] external GF source confirmed untouched
[ ] template confirmed unchanged
[ ] project initialized
[ ] project.toml valid
[ ] project lock populated
[ ] required placeholders resolved
[ ] old-language identifier scan clean
[ ] source root configured
[ ] entrypoints configured
[ ] checkpoints configured
[ ] scenarios added deliberately
[ ] gold files created only through review
[ ] project check passes
[ ] first validation evidence created
```

---

## 87. Reset implementation checklist

```text
[ ] one reset service owns mutation
[ ] exact repository root verified
[ ] exact project path verified
[ ] exact template path verified
[ ] path overlaps rejected
[ ] external source protected
[ ] active audit blocked
[ ] deterministic plan produced
[ ] dry run supported
[ ] archive or discard required
[ ] archive verified
[ ] stage created outside project
[ ] stage validated
[ ] existing project retained for rollback
[ ] staged project swapped safely
[ ] active project validated
[ ] rollback tested
[ ] runs removed only under declared scope
[ ] state removed only under declared scope
[ ] framework files preserved
[ ] template preserved
[ ] Git metadata preserved
[ ] partial completion reported accurately
[ ] temporary artifacts cleaned
[ ] post-reset checks run
```

---

## 88. Final enforcement rule

Cloning and resetting are repository-lifecycle operations, not convenience copies and deletes.

Therefore:

> No active project may be replaced until the repository boundary, template source, archive or discard policy, external source protection, staged replacement, rollback path and post-reset validation have all been resolved as one explicit operation.
