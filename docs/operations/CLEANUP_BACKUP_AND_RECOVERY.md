# GF Wordbench — Cleanup, Backup and Recovery

**Document ID:** `GF-WB-OPS-CLEANUP-BACKUP-RECOVERY`  
**Status:** Normative operational guide  
**Applies to:** Active project, local application state, generated run directories, reports, raw evidence, GF artifacts, archives, migrations, CLI, GUI, automation, and maintainers  
**Owner:** GF Wordbench maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\operations\CLEANUP_BACKUP_AND_RECOVERY.md`  
**Operations contract:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This document defines safe operational procedures for:

- cleaning temporary and generated content;
- retaining useful run evidence;
- deleting obsolete runs;
- archiving validated runs;
- backing up the active language project;
- backing up local environment configuration when appropriate;
- verifying backups and archives;
- restoring a project or run;
- recovering from interrupted writes;
- recovering from malformed application state;
- recovering from damaged run directories;
- recovering after failed migration;
- preventing cleanup from deleting authoritative project assets.

The operational objective is:

> Remove disposable data without destroying project truth, and preserve enough verified evidence to reproduce, diagnose, or release the active language project.

---

## 2. Core safety rule

> Cleanup may delete only content whose ownership and disposability are proven.

A path must not be deleted merely because:

- its name appears generated;
- it is old;
- it is large;
- it contains `.gfo`, `.pgf`, `.out`, `.err`, `.json`, or `.log`;
- it resembles a run directory;
- it is not referenced by the current GUI state.

Before deletion, GF Wordbench must determine:

1. which ownership class the path belongs to;
2. whether an active process owns it;
3. whether it is required by project or release policy;
4. whether it is referenced by a protected baseline;
5. whether it is covered by a verified backup or archive;
6. whether the requested operation explicitly includes it.

Unknown paths are preserved by default.

---

## 3. Operational asset classes

GF Wordbench distinguishes five asset classes.

```text
authoritative project assets
local disposable state
generated run evidence
development caches and build products
external environment assets
```

Each class has different cleanup and recovery rules.

---

# 4. Authoritative project assets

Authoritative project assets define the active language project or its accepted behavior.

Examples:

```text
project/project.toml
project/docs/
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
active GF source tree
templates/project/
framework source under app/
framework tests under tests/
normative documentation under docs/
pyproject.toml
```

These assets are not generated run output.

## 4.1 Default cleanup policy

Normal cleanup must not delete, rewrite, truncate, move, or regenerate authoritative project assets.

## 4.2 Explicit mutation only

Changes to authoritative assets require an explicit project, migration, gold-update, or source-editing operation.

## 4.3 Version-control expectation

Authoritative text assets should normally be protected by version control.

Version control is part of backup strategy, but it is not the only release-evidence archive.

## 4.4 Gold protection

Normal cleanup and validation must never modify:

```text
project/validation/gold/*.gold
```

Gold files may change only through the explicit reviewed gold-update workflow.

---

# 5. Local disposable state

Canonical local state:

```text
.gf_wordbench_state.json
```

Legacy state:

```text
.gf_audit_state.json
```

State may contain:

- local GF executable path;
- local RGL root;
- output root;
- last selected mode;
- last selected target;
- last-run pointers;
- GUI preferences.

State is not authoritative project truth.

## 5.1 Safe deletion

Deleting `.gf_wordbench_state.json` must not damage the active project.

After deletion, the user may need to reselect local paths and preferences.

## 5.2 Backup requirement

Application state does not normally require long-term backup.

It may be included in a machine-local backup for convenience.

A portable project backup should exclude it by default.

## 5.3 Corruption recovery

When state is malformed:

1. stop writing to the malformed file;
2. preserve a diagnostic copy;
3. load safe defaults;
4. request or resolve required local paths again;
5. write a new canonical state atomically;
6. retain the original until the new state is validated.

Recommended preserved name:

```text
.gf_wordbench_state.invalid.<UTC-TIMESTAMP>.json
```

## 5.4 Legacy migration

A successfully migrated legacy state may be retained temporarily.

It should not remain an active writer target.

Canonical writers must write only:

```text
.gf_wordbench_state.json
```

---

# 6. Generated run evidence

Each validation run owns one run directory:

```text
<output-root>/run_<run-id>/
```

Canonical structure:

```text
run_<run-id>/
├── summary.json
├── summary.md
├── AI_READY.md
├── top_errors.txt
├── manifest.json
├── details/
├── raw/
│   ├── master.log
│   ├── ALL_SCAN_LOGS.TXT
│   ├── ALL_LOGS.TXT
│   ├── compile/
│   ├── scan/
│   └── scenarios/
└── artifacts/
    ├── gfo/
    ├── out/
    └── pgf/
```

Generated run evidence is not active project configuration.

It may be deleted under retention policy, but only after protection rules are applied.

---

## 6.1 Run ownership

The run directory is owned by GF Wordbench.

Within it, individual writers own specific paths.

| Path | Writer |
|---|---|
| `summary.json` | JSON report writer |
| `summary.md` | Markdown report writer |
| `AI_READY.md` | AI report writer |
| `top_errors.txt` | report/log writer |
| `manifest.json` | manifest writer |
| `details/` | detail report writer |
| `raw/compile/` | compiler |
| `raw/scan/` | scanner |
| `raw/scenarios/` | scenario runner |
| `artifacts/gfo/` | GF compilation stage |
| `artifacts/out/` | tool-output stage |
| `artifacts/pgf/` | PGF build stage |

A cleanup component is an observer and remover.

It must not rewrite another owner’s artifact while presenting it as original evidence.

---

## 6.2 Complete run

A run is operationally complete when:

```text
execution has stopped
summary.json is finalized or a terminal recovery record exists
manifest.json is finalized when required
no run lock remains active
all writers have closed their files
```

A complete run may have validation status:

```text
OK
FAIL
ERROR
```

Validation failure does not make a run incomplete.

---

## 6.3 Partial run

A run is partial when:

- execution was cancelled;
- a process timed out;
- GF Wordbench crashed;
- the operating system stopped the process;
- report generation failed;
- the manifest was not finalized;
- a writer left a temporary file;
- the terminal execution state was not persisted.

Partial runs may contain valuable diagnostics.

They must not be automatically deleted merely because they are incomplete.

---

## 6.4 Active run

An active run is currently being written.

Cleanup must never delete an active run.

The final implementation should use an explicit active-run indicator such as:

```text
.run.lock
```

or another documented ownership mechanism.

The indicator should include bounded metadata such as:

```text
run ID
process ID
host identifier
start timestamp
application version
```

A lock file is evidence, not absolute proof that the process still exists.

Stale-lock handling requires verification.

---

# 7. Development caches and build products

Examples:

```text
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
build/
dist/
*.egg-info/
temporary wheel-test environments
temporary fixture outputs
```

These are disposable when no process is using them.

They are not GF Wordbench run evidence unless explicitly stored inside a run.

## 7.1 Default cleanup

Development-cache cleanup may remove these paths from the repository workspace.

## 7.2 Source protection

Cleanup must not use an unrestricted recursive extension rule such as:

```text
delete every *.json
delete every *.out
delete every *.gf
delete every directory named artifacts
```

Deletion must use explicit known roots and path classes.

## 7.3 Virtual environment

`.venv/` is disposable but expensive to reconstruct.

Deleting it requires an explicit environment-clean operation.

Normal cache cleanup should not delete it.

---

# 8. External environment assets

External assets include:

```text
GF installation
RGL checkout or installation
Python installation
system package cache
CI tool cache
external output archive
external backup destination
```

GF Wordbench may validate or reference these assets.

It does not own them.

Normal GF Wordbench cleanup must not delete them.

External environment cleanup belongs to the operating system, package manager, repository owner, or infrastructure administrator.

---

# 9. Cleanup operation classes

The final product should expose distinct cleanup classes.

```text
cache cleanup
state reset
run cleanup
run pruning
partial-run cleanup
artifact-only cleanup
project reset
environment cleanup
```

These operations must not be merged into one unsafe “clean everything” action.

---

# 10. Cache cleanup

Purpose:

```text
remove reconstructible developer and application caches
```

May include:

```text
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
build/
dist/
*.egg-info/
validated temporary files
```

Must not include:

```text
project/
docs/
app/
tests/
templates/
run directories
application state unless requested
virtual environment unless requested
```

Conceptual command:

```text
gf-wordbench cleanup caches
```

Preview:

```text
gf-wordbench cleanup caches --dry-run
```

---

# 11. State reset

Purpose:

```text
remove disposable local preferences without touching project truth
```

Conceptual command:

```text
gf-wordbench cleanup state
```

The operation should:

1. show the state path;
2. confirm that the file is application state;
3. optionally preserve a timestamped copy;
4. delete or reset the canonical state;
5. leave `project.toml` untouched;
6. leave all runs untouched.

Recommended default:

```text
backup state before deletion
```

A `--no-backup` option may exist for explicit local use.

---

# 12. Run cleanup

Purpose:

```text
delete one explicitly selected run directory
```

Conceptual command:

```text
gf-wordbench runs delete <run-id>
```

Required checks:

```text
run ID resolves under configured output root
path is a directory
path does not escape output root
run is not active
run is not protected
run is not a required baseline
run is not a release archive
user or automation supplied explicit deletion authorization
```

Default behavior should be preview plus confirmation for interactive use.

Automation must use an explicit noninteractive confirmation flag.

---

# 13. Run pruning

Purpose:

```text
remove older unprotected runs according to retention policy
```

Conceptual commands:

```text
gf-wordbench runs prune --dry-run
gf-wordbench runs prune --apply
```

Pruning must evaluate structured metadata where available.

Directory timestamp alone is insufficient when:

- a run was copied;
- a run was restored;
- directory metadata changed;
- the run ID uses a legacy naming format.

Preferred age source:

```text
summary.json run timestamp
```

Fallback:

```text
validated run ID timestamp
```

Last fallback:

```text
filesystem timestamp with warning
```

---

# 14. Partial-run cleanup

Purpose:

```text
remove abandoned partial runs after preserving useful diagnostics
```

A partial run must not be deleted automatically until:

- no active process owns it;
- stale-lock policy confirms abandonment;
- minimum grace period elapsed;
- required crash evidence was preserved or explicitly waived.

A partial run may be:

```text
kept
archived
quarantined
deleted
```

Quarantine is preferred when status is uncertain.

Recommended quarantine root:

```text
<output-root>/quarantine/
```

A quarantined run must not be treated as a normal comparison baseline.

---

# 15. Artifact-only cleanup

Deleting only `artifacts/gfo/` or other subtrees can make a run internally inconsistent.

Artifact-only cleanup is therefore restricted.

It may occur only when:

- the run is not release evidence;
- the manifest is updated to a new derived archive form, or the run is explicitly marked incomplete;
- report references remain valid or are marked unavailable;
- cleanup does not present modified evidence as original.

Default policy:

```text
delete the entire disposable run instead of partially stripping it
```

For archival compression, use the archive workflow rather than ad hoc subdirectory deletion.

---

# 16. Project reset

Project reset is not ordinary cleanup.

It may remove active-language project assets and replace them from the clean template.

It requires a dedicated explicit workflow governed by:

```text
docs/projects/CLONING_AND_RESETTING.md
```

Before project reset:

```text
[ ] project backup created
[ ] backup verified
[ ] uncommitted changes reviewed
[ ] active runs stopped
[ ] current project ID recorded
[ ] external source locations reviewed
[ ] reset scope displayed
[ ] explicit destructive confirmation received
```

Normal cleanup commands must not perform a project reset.

---

# 17. Environment cleanup

Deleting the virtual environment or external tool installations is separate from run cleanup.

Examples:

```text
delete .venv
remove local GF installation
remove local RGL checkout
clear external package caches
```

GF Wordbench may document these operations.

It must not execute them as part of normal run pruning.

---

# 18. Protected runs

A protected run must not be pruned automatically.

A run is protected when any applicable condition holds:

```text
explicit user protection
current last successful release
current release candidate
configured comparison baseline
referenced by a decision record
referenced by an issue or regression investigation
referenced by project status ledger
retention hold
legal or research hold
archive not yet verified
active export operation
```

Protection should be represented structurally rather than inferred only from a filename.

Possible metadata:

```text
protected = true
protection_reason
protected_at
protected_by
```

The final schema owner determines the exact persisted form.

---

# 19. Minimum retained runs

A safe default local policy should retain at least:

```text
latest completed run
latest successful quick run
latest successful checkpoint run per checkpoint
latest diagnostic run with unresolved direct failure
latest successful release run
latest failed release run
current comparison baseline
all protected runs
```

A project or organization may retain more.

The system must not assume every old run is useless.

---

# 20. Recommended retention profiles

Retention policy should be configurable.

The framework may provide named profiles.

## 20.1 Developer profile

Recommended intent:

```text
keep recent focused evidence
keep checkpoint milestones
keep release evidence indefinitely until archived
```

Example policy:

```text
quick:
  keep successful runs for 14 days
  keep failed runs for 30 days
  keep at least 5 recent runs

checkpoint:
  keep successful runs for 90 days
  keep failed runs for 90 days
  keep latest per checkpoint

diagnostic:
  keep for 30 days
  keep unresolved-failure runs until issue closure

release:
  never auto-delete
```

## 20.2 CI profile

Example policy:

```text
successful quick/checkpoint:
  retain according to CI artifact policy

failed validation:
  retain longer than successful validation

release:
  archive externally and verify before local deletion
```

## 20.3 Research profile

Example policy:

```text
retain all runs linked to experiments, publications, decisions, or accepted baselines
```

## 20.4 Minimal-disk profile

May prune aggressively, but must still preserve:

```text
protected runs
latest release
current baseline
minimum recent run set
unresolved failure evidence
```

Retention durations are policy defaults, not persisted-schema guarantees.

---

# 21. Retention precedence

When multiple rules apply, the most protective rule wins.

Example:

```text
quick run older than 14 days
+ explicitly protected
= keep
```

Recommended precedence:

```text
active
→ hold/protected
→ release evidence
→ current baseline
→ unresolved failure
→ minimum retained set
→ age/count policy
→ delete candidate
```

No age rule may override protection.

---

# 22. Dry-run requirement

Every bulk cleanup or pruning operation must support dry-run mode.

Dry-run output should include:

```text
candidate path
run ID
mode
status
age
size
protection state
baseline state
archive state
proposed action
reason
```

Dry-run must not:

- delete;
- move;
- truncate;
- rewrite manifests;
- create replacement state;
- update protection flags.

A dry-run report may be written to a separate operational log.

---

# 23. Confirmation requirements

Interactive destructive operations should require confirmation.

The confirmation must display:

```text
operation
root
candidate count
total size
protected exclusions
irreversible effects
backup or archive state
```

Automation may bypass interactive confirmation only with an explicit flag such as:

```text
--apply
--yes
```

A general environment variable must not silently enable destructive mode.

---

# 24. Path-safety rules

Before deletion, every candidate path must satisfy:

```text
resolved absolute path is known
candidate is inside the expected owned root
candidate is not the owned root itself unless explicitly authorized
candidate contains no unresolved .. segments
candidate is not a symlink escape
candidate type matches expected asset class
candidate identity matches structured metadata where available
```

## 24.1 Symlinks and junctions

Cleanup must not follow a symlink, Windows junction, or reparse point outside the owned root.

Default policy:

```text
remove the link itself only when it is an owned generated link
never recurse through an unknown link target
```

## 24.2 Output-root protection

A command targeting the output root itself must require a stronger explicit confirmation than deleting one run.

## 24.3 Source-root separation

If output root overlaps a source root, cleanup should fail by default.

The configuration should be corrected before cleanup proceeds.

---

# 25. Active-process protection

Before deleting a run, verify that no active writer owns it.

Possible evidence:

- active-run lock;
- process ID;
- process start time;
- host identifier;
- open-file or platform-specific check where available;
- current application registry.

A process ID alone may be reused by the operating system.

Stronger stale-lock validation compares:

```text
PID
process start time
host
run ID
lock creation time
```

When ownership remains uncertain, quarantine or preserve the run.

---

# 26. Cleanup logging

A cleanup operation should create an operational record outside deleted runs.

Recommended fields:

```text
operation ID
timestamp
tool version
user or automation identity where available
configured roots
dry-run or apply
candidate inventory
excluded protected inventory
deleted paths
moved paths
bytes reclaimed
errors
final status
```

The log must not contain secrets.

A cleanup log is not a replacement for a deleted run archive.

---

# 27. Failure behavior during cleanup

Cleanup must be best-effort but honest.

For each candidate:

```text
deleted
skipped
failed
quarantined
```

One deletion failure must not cause unrelated candidates to be falsely reported as deleted.

When a bulk operation partially succeeds:

```text
overall operation status = partial failure
```

The tool must preserve a retryable inventory.

---

# 28. Secure deletion

GF Wordbench normal cleanup performs filesystem deletion.

It does not guarantee forensic secure erasure.

Secure erasure depends on:

- filesystem;
- storage device;
- encryption;
- operating-system behavior;
- backup and snapshot systems.

Projects handling sensitive data should use encrypted storage and organization-approved disposal procedures.

GF Wordbench reports must avoid persisting secrets in the first place.

---

# 29. Backup strategy overview

A complete backup strategy separates:

```text
project backup
release-evidence archive
local-state backup
environment reconstruction record
```

One archive does not need to contain every class.

---

# 30. Project backup

A project backup preserves authoritative project assets.

Minimum content:

```text
project/project.toml
project/docs/
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
active GF source tree
project-relevant framework version reference
```

Recommended additional content:

```text
repository commit ID
dirty-worktree patch when applicable
pyproject.toml
lock or dependency metadata
normative contract documents
release criteria
status ledger
decision log
known issues
```

Default exclusions:

```text
.venv/
application state
tool caches
unprotected run directories
local absolute-path configuration
secrets
```

---

# 31. Version control as project backup

A clean pushed Git repository provides important protection for authoritative text assets.

Before relying on Git:

```text
[ ] all intended files tracked
[ ] current branch known
[ ] commits pushed to a separate remote
[ ] tags or release references pushed
[ ] large required assets covered
[ ] ignored project inputs reviewed
[ ] no uncommitted critical changes
```

Git alone may not preserve:

- uncommitted work;
- ignored inputs;
- generated release evidence;
- external RGL version;
- local toolchain installation;
- large binary artifacts outside the repository.

---

# 32. Snapshot backup

Before a risky migration or reset, create a point-in-time project snapshot.

Recommended archive name:

```text
gf-wordbench-project_<project-id>_<UTC-TIMESTAMP>.zip
```

or:

```text
gf-wordbench-project_<project-id>_<UTC-TIMESTAMP>.tar.gz
```

The archive should include a metadata record:

```text
backup_schema
backup_id
created_at
project_id
project_schema_version
gf_wordbench_version
repository_commit
working_tree_status
included_roots
excluded_roots
file_count
total_size
hash_algorithm
archive_hash
```

The exact backup metadata schema may be introduced as a versioned persisted schema if automated recovery depends on it.

---

# 33. Release-evidence archive

A release-evidence archive preserves one complete successful release run.

Minimum content:

```text
complete run directory
summary.json
summary.md
AI_READY.md
manifest.json
raw evidence required by release policy
PGF and other required artifacts
project configuration snapshot
release criteria snapshot or references
GF version
effective GF path metadata
source fingerprints
repository commit ID
```

The archive must preserve relative run paths.

It must not flatten files in a way that breaks manifest references.

---

# 34. Release archive naming

Recommended:

```text
gf-wordbench-release_<project-id>_<release-id>_<run-id>.zip
```

The release ID may be:

```text
semantic version
tag
release candidate ID
project-defined milestone
```

Filename sanitization must preserve identity without unsafe characters.

---

# 35. Archive creation flow

Conceptual command:

```text
gf-wordbench runs archive <run-id> --output <archive-path>
```

Required steps:

1. resolve the run under the configured output root;
2. reject active runs;
3. validate `summary.json`;
4. validate `manifest.json`;
5. verify required manifest entries;
6. identify run mode and release eligibility;
7. include required run files;
8. include declared project snapshot metadata;
9. create archive in a temporary sibling path;
10. close and flush the archive;
11. calculate archive hash;
12. verify archive contents;
13. atomically rename to final archive path;
14. record archive result.

A release archive command should reject a non-release run unless an explicit generic-run archive option is used.

---

# 36. Archive integrity

Use:

```text
SHA-256
```

for archive integrity unless the schema defines a stronger supported algorithm.

Record:

```text
archive filename
archive byte size
archive SHA-256
creation timestamp
source run ID
source manifest hash
```

A hash detects change.

It does not prove trusted authorship unless combined with a trusted signature or secure publication process.

---

# 37. Archive verification

Conceptual command:

```text
gf-wordbench archive verify <archive-path>
```

Verification should check:

```text
archive readable
no unsafe extraction paths
metadata present
expected run root present
summary schema valid
manifest schema valid
manifest entries present
manifest hashes match
archive hash matches external record when supplied
project ID matches metadata
run ID matches metadata
required release artifacts exist
```

Verification must not extract over an active project.

Use a temporary verification directory.

---

# 38. Backup destination rules

A backup is not reliable when stored only on the same disk and inside the same workspace as the source.

Recommended protection:

```text
primary working copy
+ independent local or network backup
+ remote version-control copy
+ verified release archive
```

At least one copy should be outside the machine hosting the working copy.

Backup destinations must be:

- writable;
- capacity-checked;
- access-controlled;
- monitored according to organizational policy;
- protected from accidental cleanup targeting the working output root.

---

# 39. Backup confidentiality

Backups may contain:

- proprietary GF source;
- research data;
- unpublished linguistic examples;
- absolute local paths;
- diagnostic excerpts.

Before external transfer:

```text
[ ] secrets scan complete
[ ] access policy known
[ ] encryption policy applied
[ ] destination authorized
[ ] retention policy known
```

Portable exports may redact local absolute paths where permitted.

Raw evidence required for release reproducibility should not be altered without recording the transformation.

---

# 40. Backup schedule

Recommended minimum schedule:

```text
authoritative project:
  continuously through version control
  snapshot before migration or reset
  snapshot before major contract change

release evidence:
  archive after every successful accepted release

active investigation:
  preserve diagnostic run before destructive cleanup

local state:
  no mandatory schedule

external environment record:
  update when GF, RGL, Python, or dependency versions change
```

Organizations may define stricter schedules.

---

# 41. Environment reconstruction record

GF installations and virtual environments are normally reconstructed rather than backed up byte-for-byte.

Preserve enough information to reconstruct:

```text
operating system
Python version
GF Wordbench version or commit
GF executable version
GF installation source
RGL commit or release
Python dependency metadata
project schema version
project configuration
relevant environment variables
```

Do not persist complete environment dumps.

---

# 42. Recovery principles

Recovery should restore the smallest authoritative layer needed.

Preferred order:

```text
restore configuration
→ restore project assets
→ restore run evidence
→ reconstruct local environment
→ rerun validation
```

Do not restore generated artifacts into source directories.

A restored `.gfo` or `.pgf` is evidence or release output.

It is not a substitute for rebuilding when current-source validation is required.

---

# 43. Recovery from missing application state

Symptoms:

```text
GUI paths reset
last run not shown
local executable path forgotten
```

Procedure:

1. leave project files unchanged;
2. start GF Wordbench with explicit local paths;
3. validate `project/project.toml`;
4. run `config check`;
5. allow canonical state to be recreated;
6. verify the state contains only local preferences.

No project restore is required.

---

# 44. Recovery from malformed application state

Procedure:

1. stop GF Wordbench writers;
2. copy the malformed file to a diagnostic name;
3. validate that project configuration remains intact;
4. start with state ignored;
5. re-enter local paths;
6. save new state atomically;
7. compare only required convenience fields;
8. do not copy legacy project-owned fields into new state.

---

# 45. Recovery from interrupted atomic write

Canonical writers should use a sibling temporary file followed by atomic replacement.

Possible remnants:

```text
<name>.tmp
<name>.new
<name>.bak
implementation-specific temporary sibling
```

Recovery procedure:

1. identify the canonical destination;
2. validate the existing canonical file;
3. validate each temporary candidate;
4. compare timestamps and producer metadata;
5. prefer the last valid canonical file;
6. promote a temporary file only through an explicit recovery action;
7. preserve rejected candidates;
8. record the decision.

Newest timestamp alone is not sufficient.

Schema validity and ownership take precedence.

---

# 46. Recovery from missing `project.toml`

`project.toml` is authoritative project configuration.

Recovery sources, in preferred order:

```text
version control
verified project backup
verified pre-migration snapshot
clean project template plus documented reconstruction
```

Do not reconstruct project identity solely from:

- application state;
- an old report;
- run directory name;
- source filename conventions;
- GUI labels.

Old run summaries may provide evidence, but the recovered project configuration must be reviewed and validated.

---

# 47. Recovery from malformed `project.toml`

Procedure:

1. preserve the malformed file;
2. locate the last valid version from version control or backup;
3. inspect intended uncommitted changes;
4. merge only understood project-owned values;
5. validate schema;
6. validate paths and references;
7. run `config check`;
8. run quick validation;
9. run affected checkpoints;
10. run release when release readiness must be restored.

Opening the project must not silently rewrite a malformed `project.toml`.

---

# 48. Recovery from deleted scenario or gold

Preferred sources:

```text
version control
verified project backup
reviewed release archive project snapshot
```

A run’s normalized output may help reconstruct evidence.

It must not be copied automatically into a new gold file.

For gold recovery:

1. restore the reviewed historical gold when available;
2. verify scenario and normalization versions;
3. inspect any intended behavior change;
4. use explicit gold update only when accepting new behavior;
5. rerun the proving mode.

---

# 49. Recovery from deleted GF source

Restore from:

```text
version control
verified project snapshot
authorized external source repository
```

Do not use `.gfo` as a source-code reconstruction mechanism.

Compiled artifacts do not preserve the complete maintainable source contract.

After restoration:

```text
run static scan
run focused compile
run dependent checkpoint
run affected scenarios
run release when required
```

---

# 50. Recovery from damaged run directory

Classify the damage.

## 50.1 Missing human report only

When `summary.json` and raw evidence are valid, a supported explicit report-regeneration command may regenerate derived human reports.

The regeneration must:

- use existing structured evidence;
- not rerun GF;
- record regeneration metadata;
- avoid presenting regenerated files as original bytes;
- preserve the original manifest or create a derived manifest version.

## 50.2 Missing `summary.json`

The run lacks its primary machine-readable record.

Do not parse `summary.md` as an automatic authoritative replacement.

Possible actions:

```text
restore summary.json from archive
retain run as raw partial evidence
rerun validation
perform explicit legacy recovery tool with warnings
```

## 50.3 Missing raw evidence

A summary without required raw evidence may remain useful historically.

It is not complete release evidence when policy requires the missing files.

Restore from archive or rerun.

## 50.4 Manifest mismatch

Do not modify files merely to make the manifest pass.

Procedure:

1. preserve current directory;
2. verify whether files changed or manifest is damaged;
3. compare with archive or backup;
4. restore exact originals when available;
5. otherwise mark the run altered or incomplete;
6. rerun release if trusted release proof is required.

---

# 51. Recovery from a failed release archive

When archive creation fails:

- keep the source run unchanged;
- keep the incomplete archive under a temporary name;
- report the failure;
- do not mark the run archived;
- do not permit pruning based on the failed archive;
- retry after correcting capacity, permissions, path, or integrity problems.

A run becomes archive-protected only after archive verification succeeds.

---

# 52. Recovery from failed migration

A migration must preserve the source until the canonical destination is validated.

Recovery procedure:

1. stop automatic migration retries;
2. preserve source and failed destination;
3. inspect migration log;
4. identify last valid schema;
5. correct migrator or input;
6. rerun in dry-run mode;
7. validate proposed output;
8. write to a temporary destination;
9. validate again;
10. atomically promote;
11. retain source according to migration policy.

Never overwrite the only readable legacy source before successful validation.

---

# 53. Recovery from output-root loss

When the run output root is deleted or unavailable:

```text
active project remains authoritative
application state may contain an obsolete pointer
historical evidence may be lost unless backed up
```

Procedure:

1. select or recreate a writable output root;
2. clear obsolete last-run pointers;
3. restore protected archives if needed;
4. run `config check`;
5. rerun required validation;
6. archive new release evidence.

GF Wordbench must not redirect output into the source tree as a silent fallback.

---

# 54. Recovery from GF or RGL change

When local GF or RGL changes unexpectedly:

1. record the new versions;
2. preserve the last known successful run;
3. run version compatibility check;
4. run a neutral GF integration test;
5. run project quick validation;
6. run checkpoints;
7. inspect gold differences;
8. run release if accepting the environment change;
9. archive the accepted release evidence.

Do not update gold before determining whether differences are semantic regressions or toolchain changes.

---

# 55. Disaster recovery order

For complete workstation loss:

```text
1. restore or clone framework repository
2. restore authoritative active project
3. create clean Python environment
4. install GF Wordbench
5. install or locate supported GF
6. restore or locate correct RGL revision
7. validate project configuration
8. restore optional local state or re-enter paths
9. restore protected release archives
10. run quick validation
11. run checkpoints
12. run release validation
13. compare with restored release evidence
```

A restored archive does not eliminate the need to validate the reconstructed environment.

---

# 56. Recovery point objectives

GF Wordbench itself does not impose organization-wide recovery objectives.

A project should define:

```text
maximum acceptable project work loss
maximum acceptable release-evidence loss
maximum acceptable restoration time
backup frequency
archive destination
responsible owner
```

Recommended baseline:

```text
authoritative source loss:
  limited to uncommitted work since last snapshot or push

accepted release evidence:
  no accepted release should exist only on one local disk
```

---

# 57. Restore verification

A restore is not complete when files merely exist.

Verify:

```text
project schema
project ID
source inventory
scenario inventory
gold inventory
entrypoint existence
checkpoint existence
hashes where available
repository status
GF version
RGL version
effective GF path
quick validation
checkpoint validation
release validation where applicable
```

Restored release archives should pass archive verification before use.

---

# 58. Backup verification schedule

Backups and archives should be tested periodically.

Recommended checks:

```text
archive can be read
hash record matches
manifest verifies
sample project files extract correctly
project configuration validates
critical scenarios and gold files exist
release PGF exists
restore procedure is documented
```

An untested backup is only a backup candidate.

---

# 59. Cleanup and backup CLI surface

The final CLI may expose the following command families:

```text
gf-wordbench cleanup caches
gf-wordbench cleanup state
gf-wordbench runs list
gf-wordbench runs inspect <run-id>
gf-wordbench runs protect <run-id>
gf-wordbench runs unprotect <run-id>
gf-wordbench runs delete <run-id>
gf-wordbench runs prune
gf-wordbench runs archive <run-id>
gf-wordbench archive verify <archive-path>
gf-wordbench project backup
gf-wordbench project restore
gf-wordbench recovery inspect
```

Exact syntax belongs to:

```text
docs/usage/CLI_REFERENCE.md
```

The operational semantics in this document remain authoritative.

---

# 60. Run inventory

Before pruning, the system should build a structured run inventory.

Recommended fields:

```text
run_id
path
project_id
mode
validation_status
execution_state
partial
started_at
finished_at
age
size_bytes
schema_version
manifest_present
manifest_verified
release_eligible
protected
protection_reason
baseline_reference
archive_status
active_lock_status
cleanup_eligibility
cleanup_reason
```

Missing metadata should reduce deletion confidence.

Unknown runs should not be auto-deleted.

---

# 61. Run size calculation

Size calculation should:

- remain under the owned run root;
- not follow external symlink targets;
- handle inaccessible files explicitly;
- use integer bytes;
- detect changes during calculation where practical;
- report an estimate when exact calculation is impossible.

Cleanup summaries may display human-readable units.

Structured logs should retain byte counts.

---

# 62. Baseline protection

Previous-run comparison may depend on an older run.

Before deletion, inspect structured references from:

```text
application state
project configuration where applicable
current run summaries
protection registry
release metadata
```

A current baseline should be protected until replaced by another compatible baseline.

Deleting a baseline must require explicit acknowledgement.

---

# 63. Release protection

The latest successful release run must not be auto-deleted.

Older successful release runs should not be auto-deleted until:

- an archive exists;
- the archive verifies;
- project retention policy permits deletion;
- no hold or decision record references the run.

Default final policy:

```text
release runs are excluded from automatic local pruning
```

Organizations may explicitly configure archive-then-prune behavior.

---

# 64. Failed-run retention

Failed runs often contain the most useful diagnostics.

Recommended rules:

- retain latest direct failure per target;
- retain latest failed checkpoint;
- retain latest failed release;
- retain runs linked to unresolved issues;
- allow shorter retention for duplicate downstream-only failures;
- never discard the only raw evidence for an unresolved regression automatically.

Failure status alone is not a reason for immediate deletion.

---

# 65. Duplicate run detection

Two runs may be semantically equivalent when they share:

```text
project ID
mode
target
source fingerprints
GF version
effective GF path
scenario hashes
normalization version
result status
```

Duplicate detection may help retention.

It must not automatically delete:

- protected runs;
- releases;
- runs with different raw diagnostics;
- runs from different environments;
- runs referenced by decisions;
- runs whose equivalence is uncertain.

---

# 66. Compression policy

Archives may compress run directories.

Compression must not:

- alter file contents;
- normalize raw evidence;
- discard empty required files;
- flatten relative paths;
- change filename casing on case-sensitive contracts;
- omit manifest-declared artifacts.

Compression format support must be documented and tested.

Portable ZIP support is recommended on Windows.

---

# 67. Extraction safety

Archive restore or verification must reject:

```text
absolute archive paths
drive-letter archive entries
.. traversal
symlink escape
duplicate conflicting entries
unsupported special device files
case-collision ambiguity on Windows
```

Extract into a new temporary directory.

Never extract directly over:

```text
project/
app/
docs/
tests/
existing run directory
```

until validation and explicit promotion complete.

---

# 68. Restore destination policy

Restored project backup:

```text
new empty directory by default
```

Restored run archive:

```text
new run or archive-inspection root by default
```

Overwrite requires explicit conflict policy:

```text
fail
replace after backup
merge only for approved project restore
```

Default:

```text
fail on conflict
```

---

# 69. Quarantine policy

Quarantine is used when a path is owned but unsafe to delete or trust.

Examples:

- stale active lock;
- malformed summary;
- invalid manifest;
- unknown schema;
- interrupted migration;
- suspicious path structure;
- partial archive;
- run modified after finalization.

Quarantine should:

- move within the same filesystem when atomic move is possible;
- preserve original relative structure;
- record reason;
- avoid automatic baseline use;
- avoid automatic pruning until reviewed.

---

# 70. Recovery logs

Every explicit recovery should record:

```text
recovery ID
timestamp
source path
destination path
reason
operator or automation identity where available
validation performed
files promoted
files preserved
files rejected
hashes
final status
follow-up validation required
```

Recovery logs must not claim full success until validation completes.

---

# 71. GUI requirements

The GUI may expose safe operations such as:

```text
view run inventory
protect run
archive run
delete selected run
preview pruning
reset local state
verify archive
```

The GUI must:

- show exact selected paths;
- separate preview from apply;
- disable deletion of active or protected runs;
- display release and baseline protection;
- require confirmation;
- show partial failures;
- never hide exclusions.

A single “clean all” button is prohibited.

---

# 72. Automation requirements

Automated cleanup must use:

```text
explicit output root
explicit policy
dry-run test in deployment
noninteractive authorization
structured operation log
protected-run enforcement
archive verification before release pruning
```

Automation must not rely on:

- current working directory;
- newest directory name alone;
- GUI state;
- unrestricted wildcards;
- shell deletion strings assembled from untrusted paths.

---

# 73. CI cleanup

CI workspaces are often ephemeral.

Even so, CI should upload required evidence before workspace destruction.

Order:

```text
validation completes
→ reports finalize
→ manifest verifies
→ required artifacts upload
→ upload verification
→ workspace cleanup
```

On failure, preserve:

```text
summary.json when available
raw logs
failed scenario evidence
configuration diagnostics
manifest or partial artifact inventory
```

A failed upload must not be reported as successful archival.

---

# 74. Storage-pressure behavior

Low disk space must not trigger silent deletion.

When storage pressure is detected:

1. stop or avoid starting space-intensive stages when unsafe;
2. report available and required estimates;
3. identify cleanup candidates;
4. preserve protected runs;
5. request or apply configured pruning policy;
6. record deleted candidates;
7. retry only after sufficient space exists.

The system must not delete the active run while writing it.

---

# 75. Pre-cleanup checklist

```text
[ ] Correct output root selected
[ ] No required validation process active
[ ] Run inventory built
[ ] Protected runs identified
[ ] Release runs excluded or archived
[ ] Baselines identified
[ ] Unresolved failure evidence identified
[ ] Dry-run reviewed
[ ] Candidate count reviewed
[ ] Candidate size reviewed
[ ] Symlink or junction safety checked
[ ] Backup or archive requirement satisfied
[ ] Explicit apply confirmation supplied
```

---

# 76. Project-backup checklist

```text
[ ] Project ID confirmed
[ ] project.toml included
[ ] Active GF sources included
[ ] Project docs included
[ ] Scenarios included
[ ] Inputs included
[ ] Gold files included
[ ] Contract locks included or referenced
[ ] Release criteria included
[ ] Repository commit recorded
[ ] Uncommitted changes recorded
[ ] Secrets excluded
[ ] Archive created through temporary path
[ ] Archive hash recorded
[ ] Archive verified
[ ] Independent destination confirmed
```

---

# 77. Release-archive checklist

```text
[ ] Run mode is release
[ ] Run execution completed
[ ] Overall validation status is OK
[ ] Release gates passed
[ ] summary.json validates
[ ] manifest.json validates
[ ] Manifest hashes verify
[ ] Required PGF exists
[ ] Required raw evidence exists
[ ] Project ID matches
[ ] GF version recorded
[ ] Source fingerprints recorded
[ ] Repository commit recorded
[ ] Archive created
[ ] Archive hash recorded
[ ] Archive verification passes
[ ] Archive stored independently
[ ] Run marked archived
```

---

# 78. Restore checklist

```text
[ ] Restore source identified
[ ] Source hash verified
[ ] Archive path safety checked
[ ] Empty destination selected
[ ] Existing destination protected
[ ] Files extracted
[ ] Schema versions checked
[ ] Project ID checked
[ ] Manifest checked
[ ] Required assets present
[ ] Local environment reconstructed
[ ] Configuration check passes
[ ] Quick validation passes
[ ] Required checkpoints pass
[ ] Release rerun when required
[ ] Recovery log finalized
```

---

# 79. Required tests

Recommended test files:

```text
tests/operations/test_cleanup_inventory.py
tests/operations/test_cleanup_paths.py
tests/operations/test_cleanup_protection.py
tests/operations/test_run_pruning.py
tests/operations/test_state_reset.py
tests/operations/test_archive_creation.py
tests/operations/test_archive_verification.py
tests/operations/test_project_backup.py
tests/operations/test_restore.py
tests/operations/test_recovery.py
tests/operations/test_quarantine.py
```

## 79.1 Cleanup tests

- dry-run changes nothing;
- active run rejected;
- protected run rejected;
- baseline run rejected;
- release run rejected by auto-prune;
- unprotected old quick run selected;
- unknown directory preserved;
- output-root escape rejected;
- symlink escape rejected;
- path containing spaces;
- partial bulk failure logged;
- deterministic candidate ordering.

## 79.2 State tests

- missing state;
- valid state reset;
- malformed state preserved;
- backup before reset;
- project configuration untouched;
- legacy state migration source preserved.

## 79.3 Archive tests

- successful archive;
- temporary archive cleanup after failure;
- manifest mismatch;
- missing artifact;
- archive hash;
- path traversal entry rejection;
- duplicate entry rejection;
- Windows case collision;
- extraction to empty directory;
- conflict failure.

## 79.4 Recovery tests

- interrupted atomic write;
- valid temporary promoted;
- invalid temporary rejected;
- malformed project configuration;
- missing summary;
- damaged manifest;
- failed migration preserving source;
- output-root loss;
- quarantine creation.

---

# 80. Contract checks

Recommended checks:

```text
gf-wordbench contracts check
```

Operational checks should verify:

1. cleanup cannot target project roots by default;
2. run deletion remains inside output root;
3. active-run lock is respected;
4. release runs are excluded from auto-prune;
5. protected and baseline runs are excluded;
6. dry-run has no mutation;
7. archive creation verifies the manifest;
8. archive extraction rejects traversal;
9. application-state reset cannot delete `project.toml`;
10. normal cleanup cannot modify gold;
11. readers do not rewrite owned evidence;
12. unknown run schemas are preserved or quarantined.

---

# 81. Anti-patterns

Prohibited:

```text
Remove-Item -Recurse *run*
delete oldest directories without reading metadata
delete every .gfo under the repository
clean output by writing into the source root
treat missing manifest as permission to delete
delete failed runs first
delete release run after unverified archive creation
restore archive directly over project/
copy normalized output into gold automatically
use application state as the only backup of project identity
follow junctions outside output root
mark a partial cleanup as complete success
```

---

# 82. Manual Windows cleanup examples

Manual commands are useful for development caches, but must be reviewed before execution.

PowerShell cache cleanup:

```powershell
Remove-Item -Recurse -Force .pytest_cache, .mypy_cache, .ruff_cache, htmlcov -ErrorAction SilentlyContinue
Remove-Item -Force .coverage -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter __pycache__ |
    Remove-Item -Recurse -Force
```

These commands do not implement run-retention policy.

Do not manually delete run directories with a broad wildcard when protected evidence may exist.

Use the structured run-cleanup command.

---

# 83. Manual state reset example

PowerShell:

```powershell
Copy-Item ".gf_wordbench_state.json" ".gf_wordbench_state.backup.json"
Remove-Item ".gf_wordbench_state.json"
```

Use only when the application is not writing state.

The preferred final workflow is the dedicated state-reset command because it can validate paths and record the operation.

---

# 84. Manual project backup example

A simple manual ZIP may be suitable before implementation of the final backup command.

PowerShell example:

```powershell
Compress-Archive `
  -Path "project", "app", "docs", "templates", "tests", "pyproject.toml", "README.md" `
  -DestinationPath "gf-wordbench-project-backup.zip"
```

Limitations:

- may include unnecessary files;
- may omit active GF sources stored elsewhere;
- does not create canonical backup metadata;
- does not calculate or store a verified external hash automatically;
- does not prove restore success.

Use the final structured backup workflow for release or migration protection.

---

# 85. Ownership summary

```text
project maintainer:
    owns project source, scenarios, inputs, gold and project docs

state service:
    owns .gf_wordbench_state.json

run writers:
    own their run artifacts

manifest writer:
    owns manifest.json

cleanup service:
    may remove verified disposable assets
    must not rewrite evidence

archive service:
    owns archive construction and verification records

recovery service:
    may promote validated backups through explicit operations

external administrator:
    owns GF, RGL, system backups and storage infrastructure
```

---

# 86. Change policy

A cleanup, backup, or recovery contract change requires:

```text
[ ] Asset class identified
[ ] Owner identified
[ ] Default safety behavior defined
[ ] Dry-run behavior defined
[ ] Confirmation behavior defined
[ ] Path containment reviewed
[ ] Symlink and junction behavior reviewed
[ ] Active-run behavior reviewed
[ ] Release protection reviewed
[ ] Baseline protection reviewed
[ ] Retention impact reviewed
[ ] Archive schema impact reviewed
[ ] Migration impact reviewed
[ ] CLI and GUI impact reviewed
[ ] Tests updated
[ ] Security impact reviewed
[ ] Documentation updated
```

A change that permits automatic deletion of a previously protected class requires an ADR.

---

# 87. Final operational contract

GF Wordbench must preserve the following invariants:

```text
authoritative project assets are never normal cleanup targets
application state is disposable and separate from project truth
active runs are never deleted
protected runs are never auto-pruned
release runs are never auto-pruned by default
current baselines are protected
unknown paths are preserved
bulk deletion supports dry-run
all destructive paths are containment-checked
archives are verified before they justify deletion
normal validation and cleanup never modify gold
failed migration preserves its source
recovery restores into a safe destination before promotion
```

The final operating sequence is:

```text
inventory
→ classify ownership
→ protect required evidence
→ preview
→ confirm
→ apply
→ verify
→ record
```

The final backup sequence is:

```text
select authoritative assets
→ snapshot
→ hash
→ verify
→ store independently
→ test restore
```

The final recovery sequence is:

```text
preserve damaged state
→ select trusted source
→ restore to a safe destination
→ validate schemas and manifests
→ promote explicitly
→ rerun required validation
```

Cleanup is successful only when space is reclaimed without weakening project truth, release evidence, or future diagnosis.
