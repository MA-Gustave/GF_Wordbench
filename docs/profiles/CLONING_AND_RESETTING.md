# GF Wordbench — Cloning and Resetting

**Document ID:** `GF-WB-PROJECTS-CLONING-RESETTING`  
**Status:** Normative  
**Document version:** `2.0.0`  
**Applies to:** workspace duplication, active-project replacement, generated-evidence cleanup, application-state reset, archival, rollback, and project initialization  
**Owner:** GF Wordbench maintainers  
**Functional owner:** `projects` module  
**Related owners:** `runs` for run evidence, `reporting` for artifact manifests, and bootstrap for environment wiring  
**Project schema:** `gf-wordbench.project/1.0`  
**Application-state schema:** `gf-wordbench.app-state/1.0`  
**Last reviewed:** `2026-07-24`  
**Target path:** `docs/projects/CLONING_AND_RESETTING.md`

---

## 1. Purpose

This document defines the safe lifecycle for:

- creating an isolated GF Wordbench workspace;
- replacing the workspace's active GF language project;
- copying the reusable project template;
- archiving project-owned content before replacement;
- cleaning run evidence and local application state;
- initializing a new active project;
- detecting stale project identity;
- rolling back a failed replacement;
- validating the workspace after each lifecycle operation.

The central rule is:

> One GF Wordbench workspace contains one active GF language project, and project replacement occurs only through an explicit, reviewable, path-safe, and recoverable lifecycle operation.

Cloning and resetting do not create portfolio behavior inside Wordbench. Managing several Wordbench workspaces, comparing them, or aggregating their results belongs to `gf-portfolio`.

---

## 2. Scope

This document governs:

- Git clones;
- Git worktrees;
- controlled filesystem duplication;
- workspace preflight;
- project archival;
- project reset from `templates/project/`;
- project initialization;
- generated run cleanup;
- application-state reset;
- destructive authorization;
- dry-run planning;
- staging and transactional swap;
- rollback;
- template validation;
- stale-language identifier checks;
- absolute-path checks;
- external GF source protection;
- post-operation validation.

This document does not govern:

- ordinary GF source editing;
- migration of a valuable existing language implementation;
- framework upgrade procedures;
- release publication;
- general Git branching policy;
- GF language semantics;
- exact project schema field definitions;
- general run-retention policy;
- application-state field definitions;
- operating-system backup products;
- multi-workspace inventory or aggregation.

---

## 3. Related normative documents

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/REPOSITORY_STRUCTURE.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/DEPENDENCY_RULES.md
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

`CLI_REFERENCE.md` owns exact command names and options.

This document owns lifecycle semantics and safety invariants.

---

## 4. Terminology

- **WORKSPACE**: one isolated GF Wordbench working directory containing the framework, one active project, one reusable project template, local state, and generated runs.
- **ACTIVE PROJECT**: the single GF language project under `project/`.
- **PROJECT TEMPLATE**: the reusable language-neutral structure under `templates/project/`.
- **CLONE**: creation of a separate workspace through Git clone, Git worktree, or controlled filesystem duplication.
- **RESET**: replacement of `project/` with a clean copy of `templates/project/`.
- **NEW-PROJECT RESET**: reset that also removes stale run evidence and local application state from the workspace.
- **PROJECT-ONLY RESET**: reset of `project/` while intentionally retaining local run evidence or state.
- **GENERATED-EVIDENCE CLEANUP**: removal of selected or all canonical `run_<run-id>/` directories without replacing `project/`.
- **STATE RESET**: removal of `.gf_wordbench_state.json` without changing project or run evidence.
- **MIGRATION**: coordinated preservation and transformation of an existing project.
- **ARCHIVE**: verified copy retained outside the destructive replacement boundary.
- **EXTERNAL SOURCE TREE**: GF source root referenced by the project but located outside `project/`.
- **STAGED PROJECT**: temporary validated copy of the template prepared before the active-project swap.
- **RESET PLAN**: deterministic description of paths to preserve, archive, stage, replace, remove, and validate.
- **DRY RUN**: complete planning and non-mutating validation.
- **DISCARD**: explicit authorization to replace project content without creating an archive.
- **ROLLBACK**: restoration of the previous active project after a failed replacement.
- **LIFECYCLE LOCK**: temporary coordination mechanism preventing concurrent project-changing operations.

---

## 5. Workspace and active-project rule

One workspace contains:

```text
framework code
framework tests
framework documentation
one active GF language project
one reusable generic project template
zero or more generated run_<run-id>/ directories
one optional local application-state file
```

Canonical ownership:

```text
app/                        framework runtime
tests/                      framework verification
docs/                       framework documentation
templates/project/          reusable project template
project/                    active GF language project
run_<run-id>/               generated evidence for one run
.gf_wordbench_state.json    disposable local state
```

### 5.1 Independent projects require independent workspaces

Two independently active projects must not share one `project/` boundary.

Supported workspace isolation models include:

```text
separate Git clone
separate Git worktree
controlled filesystem duplicate
```

Each workspace owns its own:

```text
project/
run_<run-id>/
.gf_wordbench_state.json
environment binding
lifecycle lock
```

### 5.2 A branch alone is not workspace isolation

A Git branch in one working directory does not isolate:

- untracked run directories;
- local application state;
- virtual environments;
- temporary files;
- editor state;
- lifecycle locks;
- external source bindings.

Use separate worktrees or clones when two projects must remain available concurrently.

### 5.3 Framework identity remains stable

A cloned workspace remains:

```text
package: gf-wordbench
CLI: gf-wordbench
product: GF Wordbench
```

The active language identity belongs to:

```text
project/project.toml
project/docs/
project/validation/
the configured GF source tree
```

Do not rename the Python package or framework modules for each language.

### 5.4 Portfolio boundary

`gf-portfolio` may register and observe several completed Wordbench workspaces through public artifacts.

GF Wordbench must not:

- register itself in Portfolio as an implicit reset side effect;
- require Portfolio to clone or reset a workspace;
- read Portfolio private state;
- place portfolio fields in `project.toml`;
- use Portfolio identity as active-project authority.

---

## 6. Choose the correct operation

| Goal | Operation |
|---|---|
| Start an independent active project | Create an isolated workspace, reset its project, then initialize |
| Replace the active project with a clean scaffold | Project reset |
| Preserve and transform an existing project | Migration |
| Remove old generated runs | Generated-evidence cleanup |
| Forget local UI or path preferences | State reset |
| Update framework source | Framework upgrade or source-control integration |
| Rename module families while preserving work | Breaking project migration |
| Rebuild evidence | New validation run |
| Update reviewed expected output | Explicit gold-update workflow |
| Repair a project document | Normal project edit |
| Observe several workspaces | `gf-portfolio`, outside Wordbench |

### 6.1 Reset is not migration

Use migration when existing work must survive in transformed form, including:

- moving a source tree;
- renaming a module suffix;
- changing project schema versions;
- restructuring project documentation;
- adopting a new scenario registry;
- changing entrypoints while retaining implementation.

A reset intentionally creates a template-derived scaffold.

### 6.2 Reset is not cleanup

Deleting `run_<run-id>/` directories does not reset `project/`.

Deleting `.gf_wordbench_state.json` does not reset `project/`.

Replacing `project/` does not modify an external GF source tree.

---

## 7. Canonical new-project workflow

```text
source workspace
    ↓
create isolated clone, worktree, or duplicate
    ↓
workspace preflight
    ↓
project reset
    ↓
template-derived staged project
    ↓
transactional project swap
    ↓
project initialization
    ↓
source and entrypoint configuration
    ↓
project contract population
    ↓
workspace and project checks
    ↓
first validation run
```

Required phases:

1. create an isolated workspace;
2. verify repository boundaries;
3. archive valuable project content or authorize discard;
4. stage and validate a clean project;
5. swap transactionally;
6. remove stale generated state when requested;
7. initialize project identity;
8. configure source roots, entrypoints, checkpoints, and scenarios;
9. validate structure and contracts;
10. begin project development or migration.

---

# Part I — Creating an isolated workspace

## 8. Preferred methods

Priority:

```text
1. Git clone
2. Git worktree
3. controlled filesystem duplicate
```

Git-based methods are preferred because they:

- preserve tracked content;
- normally exclude ignored local state;
- preserve revision identity;
- expose uncommitted changes;
- support later framework updates.

---

## 9. Git clone

Conceptual operation:

```text
git clone <repository> <destination>
```

The exact remote and destination are user choices.

### 9.1 Destination requirements

The destination must:

- differ from the source workspace;
- be absent or explicitly approved and empty;
- not be inside `project/`;
- not be inside `templates/project/`;
- not be inside a run directory;
- not overlap an external GF source tree;
- provide required filesystem behavior;
- have sufficient space.

### 9.2 Post-clone state

A Git clone may contain the committed active project.

Before assigning a different project identity:

1. inspect `project/project.toml`;
2. inspect the active project lock;
3. run workspace preflight;
4. reset the project;
5. initialize the new project.

A clone is not automatically a clean project template.

### 9.3 Local files

A clean Git clone should not contain:

```text
.gf_wordbench_state.json
run_<run-id>/
.venv/
__pycache__/
.pytest_cache/
build/
dist/
```

Unexpected generated or local files must be reviewed before reset.

---

## 10. Git worktrees

A Git worktree is an independent Wordbench workspace.

Each worktree has its own:

```text
project/
run_<run-id>/
local application state
environment binding
temporary lifecycle artifacts
```

Worktrees share Git history. Lifecycle operations must not assume `.git` is a directory.

A reset inside one worktree must not:

- modify sibling worktrees;
- remove shared Git metadata;
- clean untracked files globally;
- derive the workspace root from the parent of the common Git directory.

---

## 11. Controlled filesystem duplication

Filesystem duplication is appropriate when Git is unavailable or uncommitted framework work must be preserved.

### 11.1 Exclude local and generated content

A clean duplicate should exclude:

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
run_<run-id>/
.gf_wordbench_state.json
temporary lifecycle paths
editor caches
```

### 11.2 Include repository-owned content

The duplicate includes:

```text
app/
tests/
docs/
project/
templates/
pyproject.toml
README.md
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
LICENSE.md
supported launchers
maintenance code owned by the repository
```

### 11.3 Links and junctions

The default policy is:

```text
preserve a known safe link
or reject it
do not recursively follow unknown links
```

Unknown symlinks and Windows junctions can copy or later expose content outside the workspace.

### 11.4 Validation

After duplication, verify:

- repository root;
- template structure;
- active-project identity;
- generated-file absence;
- path non-overlap;
- old-language identifiers;
- environment-specific absolute paths.

---

## 12. Workspace identity

A directory name does not define:

```text
project ID
language code
module suffix
entrypoint
release artifact identity
```

Those values come from `project/project.toml` and project-owned contracts.

Renaming the workspace directory does not change project identity, but local environment paths must be revalidated.

---

## 13. Workspace preflight

Before reset or initialization, verify:

```text
repository root resolved
pyproject.toml present
app/ present
docs/ present
templates/project/ present
template lock present
project/ present or intentionally absent
Git or worktree boundary understood
destination differs from source
no active lifecycle writer
no active run in this workspace
no unsafe path overlap
```

The exact validation command belongs to `CLI_REFERENCE.md`.

---

## 14. Workspace cleanliness

Check for:

- stale application state;
- old `run_<run-id>/` directories;
- generated `.gfo` or `.pgf` files outside approved run roots;
- generated normalized output outside approved run roots;
- old compile and scenario logs;
- local absolute paths;
- old-language identifiers;
- old scenario and gold mappings;
- old project decisions;
- old project-lock values;
- stale staging or rollback directories.

Tracked active-project content is expected before reset. Generated local content should be absent or intentionally handled.

---

## 15. Virtual environments

A Python virtual environment is local machine state and should be recreated.

Do not rely on copying `.venv/` or `venv/` because:

- interpreter paths may be absolute;
- platform binaries may differ;
- editable-install paths may reference the source workspace;
- dependencies may be stale.

Each workspace validates its environment independently.

---

# Part II — Reset scopes

## 16. New-project reset

Default scope for repurposing a workspace:

```text
replace project/
remove local run_<run-id>/ directories
remove .gf_wordbench_state.json
preserve framework
preserve templates/project/
preserve external GF source trees
```

---

## 17. Project-only reset

Scope:

```text
replace project/
retain run_<run-id>/ directories intentionally
retain local application state intentionally
```

This scope is exceptional because retained evidence and state may refer to the previous project.

It requires explicit authorization and must prevent retained runs from becoming automatic regression baselines for the new project.

---

## 18. Generated-evidence cleanup

Scope:

```text
remove selected or all canonical run_<run-id>/ directories
preserve project/
preserve application state unless separately reset
```

Cleanup follows `RUN_DIRECTORY_LIFECYCLE.md`.

It must not search the repository broadly for extensions such as `.gfo`, `.pgf`, or `.out`.

---

## 19. State reset

Scope:

```text
remove .gf_wordbench_state.json
preserve project/
preserve run_<run-id>/ directories
```

State reset follows `APPLICATION_STATE_REFERENCE.md`.

A missing state file is a successful no-op.

---

## 20. Preserved and replaced paths

### Replaced or removed during new-project reset

```text
project/
run_<run-id>/ directories owned by this workspace
.gf_wordbench_state.json
temporary lifecycle artifacts created by the operation
```

### Preserved

```text
app/
tests/
docs/
templates/
pyproject.toml
README.md
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
LICENSE.md
Git metadata
supported launchers
external GF source trees
```

A missing state file or missing run directories is normal.

A successful reset recreates a structurally valid `project/`.

---

## 21. Active-project structure

The reset target mirrors the reusable project template:

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

The reset copies structure and generic guidance. It does not invent language-specific source, scenarios, inputs, golds, or release evidence.

---

## 22. Template invariants

`templates/project/` contains:

- language-neutral instructions;
- explicit placeholders;
- generic validation guidance;
- empty or example-only registries;
- no active-language identity;
- no generated evidence;
- no local absolute paths;
- no Portfolio configuration;
- no completed project decisions presented as active facts;
- no populated release evidence.

Required relative paths in `project/` and `templates/project/` match by role.

The template is read-only during reset. If it fails validation, reset stops before changing `project/`.

---

# Part III — Reset safety

## 23. Preconditions

Before mutation, the reset operation verifies:

```text
workspace root
project path
template path
path containment
path non-overlap
template completeness
template cleanliness
active-operation state
archive or discard policy
write permissions
staging capability
rollback capability
external source protection
```

### 23.1 Workspace-root proof

The root is verified through several stable markers, for example:

```text
pyproject.toml
app/
docs/REPOSITORY_STRUCTURE.md
docs/PERSISTED_SCHEMA_LOCK.md
templates/project/
```

Current working directory alone is insufficient.

### 23.2 Exact project path

The resolved active-project path is:

```text
<workspace-root>/project
```

Reset rejects:

- the workspace root;
- a parent of the workspace;
- `templates/project/`;
- `app/`;
- `tests/`;
- `docs/`;
- filesystem or drive roots;
- user home;
- external source roots;
- run directories.

### 23.3 Non-overlap

After link and junction resolution, the following are distinct:

```text
workspace root
active project
project template
archive destination
external source roots
staging path
rollback path
run directories
```

### 23.4 Active operations

Reset must not begin while the same workspace has:

- an active validation run;
- another reset;
- project initialization;
- migration;
- generated-evidence cleanup affecting the same paths.

A temporary lifecycle lock coordinates writers.

---

## 24. Git preflight

When Git metadata is available, planning identifies:

- modified tracked files;
- untracked files;
- ignored generated files;
- current branch;
- worktree root.

If `project/` contains uncommitted changes, the operation requires:

- a verified archive; or
- explicit discard authorization.

Framework changes outside reset scope do not automatically block reset, but they appear in the plan.

Reset must not silently run:

```text
git reset --hard
git clean -fdx
git checkout .
git restore .
git stash
git commit
```

---

## 25. Dry run

Every destructive reset supports a dry-run equivalent.

The dry run performs all non-mutating checks and returns a deterministic reset plan containing:

```text
workspace root
project path
template path
archive destination or discard mode
preserve set
replace set
removal set
external source roots
run directories and approximate size
state-file presence
Git summary when available
staging and rollback strategy
validation steps
warnings
```

Dry run must not:

- create a staged project;
- create an archive;
- delete files;
- replace `project/`;
- remove run directories;
- remove application state;
- write `project.toml`;
- modify Git state.

A temporary write-capability probe may be used only when necessary and must be removed immediately.

---

## 26. Destructive authorization

Replacing non-template project content requires:

```text
verified archive
or explicit discard authorization
```

### 26.1 Interactive authorization

The confirmation shows:

- workspace root;
- current project ID when readable;
- paths affected;
- archive behavior;
- run cleanup behavior;
- state reset behavior;
- external paths that remain untouched.

Confirmation should require a specific token such as the current project ID.

### 26.2 Non-interactive authorization

Automation must provide explicit authorization for destruction and archive or discard behavior.

It must not prompt and must fail when authorization is incomplete.

### 26.3 Preservation by default

Without a verified archive or explicit discard:

```text
do not reset
```

---

# Part IV — Archival

## 27. Archive content

The required archive contains the complete current:

```text
project/
```

including project configuration, documentation, scenarios, inputs, golds, project lock, and project README.

At explicit request, it may also contain:

- selected release-significant run directories;
- migration notes;
- Git status text;
- framework revision identity.

Excluded by default:

- application state;
- every local run;
- virtual environments;
- Python caches;
- build output;
- external source trees;
- credentials;
- complete environment dumps.

If project configuration references an external source tree, the plan states that archiving `project/` does not preserve those sources.

---

## 28. Archive destination

The destination should be outside the workspace being reset.

Allowed forms include:

```text
external directory
external ZIP archive
approved backup location
source-control preservation performed outside reset
```

Reject destinations inside:

```text
project/
templates/project/
a run directory scheduled for removal
staging path
rollback path
```

An archive inside the workspace root is discouraged and must not overlap any reset scope.

---

## 29. Archive verification

Before replacement, verify:

```text
all required project paths copied
file count consistent
file sizes consistent
content hashes consistent where practical
archive can be reopened
destination differs from source
no copy errors remain
```

A failed or incomplete archive blocks reset.

The archive follows the declared link policy and must not unexpectedly copy external trees.

After verification, the archive is treated as read-only evidence for the operation.

---

## 30. Discard mode

Discard mode is valid only when:

- explicitly authorized;
- the plan identifies what will be lost;
- no archive-complete claim is emitted;
- external source trees remain untouched;
- staging, validation, swap, and rollback protections remain active.

Discard never authorizes broad repository deletion.

---

# Part V — Transactional replacement

## 31. Reset phases

```text
PLAN
PREFLIGHT
ARCHIVE_OR_AUTHORIZE_DISCARD
STAGE
VALIDATE_STAGE
SWAP
VALIDATE_ACTIVE_PROJECT
CLEAN_GENERATED_STATE
COMPLETE
```

Each phase returns an explicit result.

---

## 32. Plan and preflight

Planning resolves:

```text
workspace root
active project path
template path
staging path
rollback path
archive path
run paths
state path
external source roots
preserve set
replace set
removal set
```

Preflight validates:

- path safety;
- template completeness;
- write capability;
- archive or discard authorization;
- lifecycle concurrency;
- project structure;
- source-tree protection.

A planning or preflight failure causes no mutation.

---

## 33. Stage

The operation copies:

```text
templates/project/
```

to a temporary sibling staging path on the same filesystem when atomic rename is required.

The staged project:

- does not overwrite `project/`;
- preserves required content and permissions;
- contains no active-language additions;
- contains no generated artifacts;
- contains no Portfolio state;
- remains separate from initialization unless one explicit transaction combines them.

---

## 34. Validate the staged project

Before swap, validate:

```text
required relative paths
template-form project.toml
template contract lock
absence of local absolute paths
absence of active-language identifiers
absence of generated evidence
absence of invalid link escapes
UTF-8 text where required
project/template mirror contract
```

A validation failure removes or preserves the stage according to recovery policy and leaves `project/` unchanged.

---

## 35. Swap

Preferred same-filesystem sequence:

1. rename current `project/` to a rollback path;
2. rename staged project to `project/`;
3. verify that the new `project/` exists;
4. retain rollback material until active-project validation succeeds.

The delete-first strategy is prohibited:

```text
delete project/
then copy template
```

When atomic rename is unavailable, use the safest platform-supported equivalent and preserve rollback material until validation succeeds.

Windows behavior must be tested explicitly.

---

## 36. Validate the active project

After swap, verify:

```text
required structure
project schema parseability
placeholder policy
contract-lock presence
path containment
absence of previous project-only files
absence of generated evidence
template unchanged
```

A clean reset scaffold may contain explicit placeholders and may not yet be executable. Initialization resolves required project identity and contracts.

---

## 37. Clean generated state

For a new-project reset, after project replacement succeeds:

```text
remove canonical run_<run-id>/ directories selected by the reset plan
remove .gf_wordbench_state.json
```

Cleanup occurs while rollback remains available.

Only run directories owned by this workspace and identified through canonical run semantics may be removed.

A missing state file is not an error.

If project replacement succeeds but cleanup fails:

- report partial completion;
- keep the valid new `project/`;
- identify stale paths;
- allow explicit cleanup retry;
- do not claim a completely cleaned workspace.

---

## 38. Complete or roll back

After successful validation and required cleanup:

1. remove the rollback directory;
2. remove staging artifacts;
3. release the lifecycle lock;
4. emit an operation summary;
5. list project initialization steps.

### 38.1 Failure before swap

The active project remains unchanged.

### 38.2 Failure during swap

Restore the rollback project.

### 38.3 Failure after swap but before validation

1. move the invalid new project aside or remove it safely;
2. restore the rollback project;
3. verify the restored project;
4. preserve diagnostic evidence;
5. report rollback outcome.

### 38.4 Rollback failure

Rollback failure is a critical lifecycle error.

Report:

```text
current project-path state
rollback path
archive path
manual recovery actions
paths that must not be deleted
```

Do not continue with run or state cleanup.

---

## 39. Temporary artifacts

Staging, rollback, and lifecycle-lock paths are private operation artifacts.

They are removed after success.

After failure, they may remain when required for recovery. The next lifecycle operation detects stale artifacts and refuses unsafe reuse until they are resolved.

---

# Part VI — Project initialization

## 40. Reset scaffold and initialized project

```text
template-derived scaffold
    ↓
project initialization
    ↓
configured active project
```

Reset does not guess:

```text
project ID
language name
language code
module suffix
source root
entrypoints
checkpoints
scenario IDs
release entrypoint
expected PGF
```

Initialization receives these decisions explicitly.

---

## 41. Initialization responsibilities

The `projects` module:

1. verifies the scaffold;
2. accepts required project identity;
3. writes `project/project.toml`;
4. replaces required project-document placeholders;
5. populates the active project lock;
6. validates path relationships;
7. preserves empty scenario, input, and gold registries until explicitly defined;
8. rejects unresolved required placeholders;
9. writes atomically;
10. runs project checks.

Exact project fields belong to `PROJECT_TOML_REFERENCE.md`.

---

## 42. Initialization input

Required identity includes, as applicable:

```text
project ID
display name
language name
language code
module suffix
source-root relationship
project owner
```

Validation configuration includes:

```text
source directory
source selection
GF path additions
entrypoints
checkpoints
required scenarios
optional scenarios
release entrypoint
expected artifacts
```

Initialization does not create Portfolio identity.

---

## 43. Placeholder policy

Placeholders are allowed in:

```text
templates/project/
a fresh scaffold before initialization
```

Required placeholders are not allowed in a configured active project.

The initializer reports every unresolved required placeholder.

---

## 44. Scenarios, inputs, and golds

Initialization must not invent linguistic expectations.

It may create:

- empty registries;
- disabled examples;
- README guidance;
- placeholder-free directory structure.

It must not create passing gold files without executed and reviewed scenario output.

Golds are added only through the explicit gold workflow.

---

## 45. External GF source trees

A project may reference a source tree outside the workspace.

Reset never deletes or rewrites that tree.

Initialization records the source relationship through project configuration.

Before validation, verify:

```text
source root exists
source root is explicitly approved
entrypoints exist
path policy is satisfied
GF search paths resolve
```

When sources intentionally reside inside `project/`, they are project-owned and are included in archive and replacement scope. The reset plan states this consequence explicitly.

---

# Part VII — Retained evidence and identity

## 46. Previous-project runs

Runs from the previous active project must not become evidence for the new project.

A new-project reset removes local canonical run directories after archival decisions.

When runs are intentionally retained, they:

- remain immutable;
- preserve their original project identity;
- are not selected automatically as a regression baseline;
- do not define the active project;
- may contain previous local paths and language identifiers.

Release-significant runs should be archived outside the repurposed workspace.

---

## 47. Previous application state

Application state may contain:

```text
old project path
old target
old GF or RGL path
old output root
old run pointer
old mode preference
UI preferences
```

A new-project reset removes `.gf_wordbench_state.json`.

Application state never supplies language identity, required entrypoints, scenarios, or release policy.

---

## 48. Git history

Reset changes the working tree but does not erase Git history.

Recommended sequence:

1. commit or archive valuable work;
2. create the isolated workspace;
3. reset;
4. inspect changes;
5. commit the clean scaffold;
6. initialize and commit project identity.

GF Wordbench does not create commits automatically.

---

## 49. Stale-language identifier removal

After reset and initialization, inspect:

```text
project/project.toml
project/README.md
project/docs/
project/validation/
scenario filenames
input filenames
gold filenames
project lock
```

Framework and template paths are also checked for accidental project-specific drift:

```text
app/
tests/
docs/
templates/
```

Previous language names may remain only in clearly identified migration fixtures, compatibility tests, archives, or Git history.

---

## 50. Absolute-path removal

Tracked project and template content must not inherit:

- Windows drive paths;
- UNC paths;
- POSIX home paths;
- user-specific directories;
- previous workspace roots;
- local RGL roots;
- local GF executable paths.

Portable project paths remain project-relative. Environment-specific paths belong to approved local configuration or application state.

---

# Part VIII — Cleanup and state reset

## 51. Generated-evidence cleanup

Cleanup removes only approved run-owned content.

It must not remove:

```text
project/
templates/
GF source
gold files
project inputs
framework tests
framework documentation
public archives outside selected run roots
```

Run cleanup uses canonical run identity and lifecycle rules, not broad extension or filename searches.

---

## 52. Application-state reset

A state reset:

- removes only `.gf_wordbench_state.json`;
- is idempotent;
- preserves project configuration;
- preserves run evidence;
- preserves external sources;
- does not alter release policy.

---

## 53. Template direction

The supported copy direction is:

```text
templates/project/
    ↓
project/
```

Copying the active project back into the template as a reset mechanism is prohibited because it can introduce:

- active-language identity;
- local paths;
- project scenarios;
- gold expectations;
- project decisions;
- generated evidence;
- Portfolio identifiers.

Template changes are framework-maintainer changes and require template review.

---

# Part IX — Command surface

## 54. Lifecycle operations

The CLI provides operations for:

```text
workspace or repository check
project reset
project initialization
project check
generated-evidence cleanup
application-state reset
```

Exact spelling and options belong to `CLI_REFERENCE.md`.

The reset surface supports:

- dry run;
- archive destination;
- explicit discard;
- generated-evidence cleanup;
- project-only retention;
- non-interactive authorization.

GF Wordbench does not implement a second Git client. Cloning remains a Git or filesystem operation.

---

## 55. Command examples

Examples in this document are conceptual. `CLI_REFERENCE.md` owns executable syntax.

```text
project reset --dry-run --archive <external-path>
project reset --archive <external-path>
project initialize
project check
```

```text
project reset --dry-run --discard
project reset --discard --yes
```

```text
state reset
```

---

# Part X — Validation

## 56. Post-clone checks

Verify:

```text
workspace root
framework imports
template structure
project/template mirror
state absent or valid
runs absent or intentionally retained
environment recreated
GF executable resolved
RGL path resolved
```

---

## 57. Post-reset checks

Verify:

```text
project/ exists
project/ derives from current template
required paths exist
previous project-only files are absent
template remains unchanged
selected runs were removed
state was removed when requested
external sources remain untouched
no stale staging or rollback path
archive was verified when requested
```

---

## 58. Post-initialization checks

Verify:

```text
project schema
project identity
required placeholders
source-root relationship
entrypoints and checkpoints
scenario ID uniqueness
input and gold mappings
project lock
documentation identity
absence of stale-language identifiers
absence of Portfolio fields
```

A configured project may begin validation only after required project contracts are resolved.

---

## 59. First validation run

After initialization and source configuration:

1. run project checks;
2. run quick validation;
3. validate checkpoints;
4. register required scenarios;
5. execute and review scenario evidence;
6. add golds through the explicit workflow;
7. run release validation when release criteria are defined.

Do not create empty passing evidence to satisfy structure.

---

# Part XI — Errors and operation results

## 60. Error categories

Lifecycle operations distinguish:

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

These are lifecycle errors, not GF linguistic validation failures.

---

## 61. Fail before mutation

The operation fails without mutation when:

- workspace root is uncertain;
- project path is unsafe;
- template is missing or invalid;
- archive destination is unsafe;
- archive verification fails;
- destructive authorization is missing;
- an active run or lifecycle writer exists;
- link layout is unsupported;
- required permissions are unavailable.

---

## 62. Structured operation result

A lifecycle result reports:

```text
plan created
archive completed or not requested
project staged
project replacement completed
active-project validation completed
rollback completed or not required
run cleanup completed or not requested
state reset completed or not requested
remaining recovery or initialization actions
```

Partial completion must not be represented as complete success.

Exit codes remain owned by `docs/reference/EXIT_CODES.md`.

---

# Part XII — Security

## 63. Filesystem security

Every path is untrusted until normalized and resolved.

Required controls:

- canonical workspace-root verification;
- containment checks;
- traversal rejection;
- drive-root and filesystem-root rejection;
- user-home rejection when unintended;
- symlink and junction policy;
- archive overlap rejection;
- stage and rollback overlap rejection;
- external-source protection;
- no shell interpolation for copy or deletion;
- bounded error reporting;
- credential exclusion.

---

## 64. Deletion policy

Deletion is restricted to exact approved roots from the reset plan.

Prohibited approaches:

```text
recursive deletion from current working directory
searching for every directory named project
deleting every .gfo, .pgf, or .out in the repository
global Git clean
following arbitrary links
deleting a directory only because its name resembles run_*
```

The operation determines canonical run ownership before deletion.

---

## 65. Windows safety

Lifecycle operations handle:

- drive-letter paths;
- UNC paths;
- case-insensitive comparisons;
- junctions and reparse points;
- read-only files;
- antivirus locks;
- open editor handles;
- long paths;
- atomic rename limitations.

Paths differing only by case may identify the same location.

A locked file blocks the affected phase. The operation does not silently skip it.

---

## 66. Secrets and private data

Plans, archives, and logs must not capture:

```text
passwords
tokens
private keys
credential files
complete environment dumps
secret command arguments
Portfolio private state
```

Local absolute paths may be required for safety reports, but support exports may redact them.

---

# Part XIII — Concurrency

## 67. One lifecycle writer

Only one project-changing lifecycle operation may modify a workspace at a time.

A lifecycle lock may contain bounded metadata:

```text
operation ID
process ID
start time
workspace root
operation type
```

It contains no secrets or complete project configuration.

A stale lock is not removed blindly. Ownership and process state are checked first.

An active validation run blocks reset. Read-only checks may run concurrently only when they cannot observe an intermediate swap state.

---

# Part XIV — Functional ownership

## 68. `projects` module

The `projects` module owns:

```text
workspace and project preflight
reset planning
path-safety validation
archive coordination
template staging
staged-project validation
transactional swap
rollback
project initialization
project schema population
placeholder resolution
post-initialization validation
structured lifecycle result
```

It does not:

- clone Git repositories;
- modify GF language semantics;
- update golds;
- run destructive Git commands;
- rewrite framework files;
- mutate the project template during reset;
- delete external source trees;
- publish Portfolio state.

---

## 69. `runs` and `reporting`

`runs` owns identification and lifecycle of canonical `run_<run-id>/` directories.

The `projects` reset use case requests cleanup through the public run-lifecycle contract rather than reconstructing run semantics independently.

`reporting` may render a bounded lifecycle-operation summary, but lifecycle operations do not create:

- fake `summary.json`;
- release evidence;
- GF diagnostics;
- PGF artifacts;
- normal validation manifests.

A validation run remains a separate operation.

---

## 70. CLI, GUI, and maintenance entrypoints

CLI, GUI, and maintenance entrypoints call the same project lifecycle application services.

They may:

- collect input;
- render the reset plan;
- request confirmation;
- display archive and rollback paths;
- render the structured operation result.

They must not:

- traverse and delete paths directly;
- implement independent reset algorithms;
- bypass path safety;
- create a second schema writer;
- infer project identity from widget state.

---

# Part XV — Tests

## 71. Planning and path-safety tests

Required cases include:

```text
valid workspace root
missing root markers
project path equals workspace root
template path equals project path
archive inside project
archive inside selected run
external source overlap
missing template
incomplete template
template with active-language identity
template with absolute path
dry run performs no mutation
archive required by default
discard requires explicit authorization
missing runs accepted
missing state accepted
project-only reset plan
new-project reset plan
```

---

## 72. Staging, swap, and rollback tests

Required cases include:

```text
stage copied completely
stage validation failure leaves project unchanged
current project moved to rollback
staged project becomes active
active validation succeeds
active validation fails and restores rollback
rename failure restores original state
stale staging path detected
stale rollback path detected
temporary paths removed after success
recovery paths preserved after failure
Windows fallback behavior
```

---

## 73. Archive tests

Required cases include:

```text
complete project archived
nested files preserved
missing archive file detected
changed archive content detected
ZIP archive reopens
destination collision
destination inside reset scope
link policy
external source excluded by default
selected runs included only explicitly
application state excluded by default
archive failure blocks reset
```

---

## 74. Cleanup and initialization tests

Required cases include:

```text
new-project reset removes canonical runs
new-project reset removes state
project-only reset retains runs
project-only reset retains state
cleanup failure reported as partial
external source unchanged
template unchanged
framework unchanged
Git metadata unchanged
clean scaffold accepted
project identity populated
project.toml validates
project lock populated
required placeholders resolved
unresolved placeholders rejected
gold evidence not invented
atomic project write
initialization rollback after failure
```

---

## 75. Contract and integration tests

Contract tests verify:

- one active project per workspace;
- template-to-project copy direction;
- project/template role mirror;
- framework directories preserved;
- template never mutated by reset;
- external source never deleted;
- archive or discard required;
- dry run performs no mutation;
- replacement is staged;
- delete-first replacement is absent;
- rollback is available;
- all entrypoints use the same application services;
- run and state cleanup follow declared scope;
- stale identity scanning occurs;
- canonical project schema is used;
- no destructive Git command is invoked implicitly;
- no Portfolio dependency is introduced.

Integration tests use temporary clones, worktrees, and filesystem duplicates.

They must verify real filesystem behavior on Windows and a supported POSIX environment.

---

## 76. Property tests

Path-safety property tests should generate:

- relative and absolute paths;
- `..` traversal;
- case variants;
- symlink and junction layouts;
- workspace-prefix collisions;
- archive and run overlaps;
- drive and UNC paths where supported.

Required properties:

```text
no approved deletion escapes its owner root
no project swap targets templates/project/
no archive destination overlaps replacement or cleanup scope
no external source is selected for deletion
dry run leaves the filesystem unchanged
```

---

# Part XVI — Change control

## 77. Drift indicators

Review is required when:

- reset code deletes before staging;
- project identity comes from directory name or UI state;
- run cleanup searches by extension;
- template content is modified during reset;
- a lifecycle entrypoint performs its own filesystem traversal;
- reset uses broad Git cleanup;
- archive verification is omitted;
- rollback material is deleted before active-project validation;
- external source paths overlap deletion scope;
- project-only reset silently reuses old runs;
- application state defines project identity;
- active-language names appear in the template;
- absolute machine paths appear in reusable project content;
- lifecycle operations write validation reports;
- concrete source paths are treated as permanent architectural contracts instead of functional-module ownership;
- a competing run-root convention is introduced alongside `run_<run-id>/`;
- Wordbench registers or mutates `gf-portfolio` state.

Resolution restores the documented contract or adopts a new accepted architectural decision.

---

## 78. Change workflow

A lifecycle-contract change updates together:

1. `projects` module request and result contracts;
2. project schema references;
3. run cleanup integration;
4. state reset integration;
5. template and active-project locks;
6. CLI and GUI surfaces;
7. path-safety and rollback tests;
8. security documentation;
9. migration or compatibility guidance;
10. this document and related owner documents.

---

## 79. New-project checklist

```text
[ ] isolated workspace created
[ ] workspace preflight passes
[ ] valuable project content archived or discard explicitly authorized
[ ] template validates
[ ] dry-run plan reviewed
[ ] project staged
[ ] staged project validates
[ ] transactional swap succeeds
[ ] active scaffold validates
[ ] old runs removed or intentionally retained
[ ] application state removed or intentionally retained
[ ] external sources untouched
[ ] project initialized
[ ] required placeholders resolved
[ ] source relationship configured
[ ] entrypoints and checkpoints configured
[ ] stale-language identifiers absent
[ ] absolute reusable paths absent
[ ] project lock and documentation agree
[ ] project checks pass
[ ] first validation run produces current evidence
```

---

## 80. Enforcement rule

GF Wordbench project lifecycle operations preserve this boundary:

```text
isolated workspace
    → one active project
    → template-derived staged replacement
    → validated transactional swap
    → explicit initialization
    → independent validation evidence
```

Therefore:

> No reset may guess project identity, delete before staging, escape approved paths, modify external sources, mutate the reusable template, reuse stale evidence as current truth, or create a dependency on `gf-portfolio`.
