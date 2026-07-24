# GF Wordbench — Run Directory Lifecycle

**Document ID:** `GF-WB-RUN-DIRECTORY-LIFECYCLE`  
**Status:** Normative specification  
**Applies to:** Creation, use, finalization, verification, recovery, retention, archival, restoration, and deletion of GF Wordbench run directories  
**Owner:** GF Wordbench maintainers  
**Run-layout contract:** `gf-wordbench.run-layout/1.0`  
**Normative counterparts:**
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`
- `docs/architecture/ARTIFACT_MODEL.md`
- `docs/architecture/PROCESS_EXECUTION_MODEL.md`
- `docs/reports/ARTIFACT_MANIFEST.md`
- `docs/reports/RAW_LOGS_REFERENCE.md`
- `docs/reports/SUMMARY_JSON_REFERENCE.md`
- `docs/validation/RELEASE_GATES.md`

**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

Every GF Wordbench validation creates evidence.

That evidence must remain:

- isolated from other runs;
- attributable to one project and configuration;
- writable only by its owning stages;
- useful after partial failure;
- finalizable without circular rewrites;
- verifiable after copying or archival;
- removable without risking project source or another run.

This document defines the complete operational lifecycle of the directory that owns that evidence.

> A run directory is an append-then-finalize evidence container. It is not a working copy of the project and it is not a shared cache.

A run directory may contain a successful result, a validation failure, a tool error, or partial evidence from an interrupted execution. Its lifecycle state and its validation outcome are separate concepts.

### 1.1 Workspace and product boundary

Each run belongs to one GF Wordbench workspace, one active project, and one resolved normative language target.

Run directories do not form a multi-project registry and do not store cross-workspace portfolio state. The independent `gf-portfolio` product may consume public, versioned Wordbench artifacts. GF Wordbench does not depend on Portfolio runtime, code, storage, or configuration.

---

## 2. Scope

This specification governs:

- output-root validation;
- run identifier generation;
- collision handling;
- directory creation;
- canonical directory layout;
- `RunPaths`;
- directory and file ownership;
- stage write boundaries;
- concurrent-run isolation;
- raw-evidence preservation;
- artifact collection;
- report generation;
- manifest generation;
- finalization;
- interrupted and incomplete runs;
- cancellation;
- corruption detection;
- previous-run eligibility;
- read-only inspection;
- archival and restoration;
- cleanup and deletion;
- Windows and POSIX behavior;
- security and path containment;
- migration from legacy GF Audit runs;
- lifecycle diagnostics;
- tests.

This specification does not govern:

- project-source lifecycle;
- source-control history;
- project initialization or reset;
- detailed report content;
- GF command semantics;
- detailed retention periods;
- external archive-service configuration;
- linguistic release acceptance.

---

## 3. Core separation

GF Wordbench distinguishes four independent concepts.

### 3.1 Lifecycle state

Describes what happened to the run directory operationally.

Examples:

```text
allocated
initialized
executing
finalizing
finalized
incomplete
corrupt
archived
deleted
```

### 3.2 Validation status

Describes whether a validation criterion passed.

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

### 3.3 Execution state

Describes a process or run-control condition.

Examples:

```text
completed
timed_out
cancelled
launch_failed
terminated
```

### 3.4 Release decision

For release mode:

```text
READY
NOT_READY
ERROR
```

### 3.5 Independence rule

A finalized run may have:

```text
validation status = FAIL
```

or:

```text
validation status = ERROR
```

and still be a structurally complete, useful, manifest-verified run.

Conversely, a directory containing many successful artifacts may remain incomplete when completed reports or the manifest were never safely finalized.

---

## 4. Lifecycle states

The lifecycle state names in this section describe the operational model.

They do not become persisted `summary.json` enum values unless added through a schema revision.

### 4.1 `allocated`

A unique run ID and intended path have been selected in memory.

The directory does not yet exist.

### 4.2 `initialized`

The run root and required standard subdirectories exist.

No validation stage has started.

### 4.3 `executing`

One or more validation stages are running or have run.

Stage-owned evidence may exist.

### 4.4 `finalizing`

Validation stages have stopped.

Structured results, reports, artifact declarations, and the manifest are being completed.

### 4.5 `finalized`

Required finalization completed.

At minimum:

- canonical `summary.json` exists and validates;
- required human-facing reports exist according to policy;
- canonical `manifest.json` exists and verifies;
- no listed artifact is still open for writing;
- the run is no longer mutable under normal operation.

`finalized` does not mean the validation passed.

### 4.6 `incomplete`

The directory exists, but normal finalization did not complete.

Typical causes:

- process crash;
- forced termination;
- host shutdown;
- cancellation before safe finalization;
- unrecoverable report-writing failure;
- manifest generation failure;
- manual interruption;
- filesystem exhaustion.

### 4.7 `corrupt`

The directory claims or appears to be finalized, but integrity checks fail.

Examples:

- invalid `summary.json`;
- invalid `manifest.json`;
- missing required manifested artifact;
- size mismatch;
- SHA-256 mismatch;
- unsafe manifest path;
- run-ID contradiction.

### 4.8 `archived`

A verified copy of the run has been placed in an archive or archival location.

The original run may remain present.

Archival is an external lifecycle condition; the canonical manifest schema does not require an `archived` field.

### 4.9 `deleted`

The run directory no longer exists at its former location after an explicit cleanup operation.

Deletion is not represented by a file inside the deleted directory.

---

## 5. Lifecycle transitions

Canonical transitions:

```text
allocated
  → initialized
  → executing
  → finalizing
  → finalized
```

Failure transitions:

```text
initialized → incomplete
executing   → incomplete
finalizing  → incomplete
finalized   → corrupt
```

Operational transitions:

```text
finalized  → archived
incomplete → archived
corrupt    → archived
finalized  → deleted
incomplete → deleted
corrupt    → deleted
archived   → restored copy
```

### 5.1 Prohibited transitions

The following are prohibited under normal operation:

```text
finalized → executing
corrupt   → finalized by silent rewrite
deleted   → restored without an archive or source copy
incomplete → executing through implicit cross-process resume
```

### 5.2 New run after failure

An incomplete or corrupt run is not silently reused.

A new validation creates a new run ID and directory.

---

## 6. Run identity

### 6.1 Canonical directory name

```text
run_<run-id>
```

### 6.2 Recommended schema `1.0` run ID

```text
YYYYMMDD_HHMMSS
```

The timestamp represents UTC.

Example:

```text
run_20260722_163210
```

### 6.3 Collision suffix

When the base directory already exists, append a deterministic numeric suffix:

```text
run_20260722_163210_02
run_20260722_163210_03
```

The selected suffix becomes part of `run_id`.

### 6.4 Run-ID pattern

Canonical pattern:

```text
^\d{8}_\d{6}(?:_\d{2,})?$
```

### 6.5 Atomic uniqueness

Uniqueness MUST be established through atomic directory creation.

The run allocator MUST NOT:

1. check that a path is absent;
2. wait;
3. create it without collision handling.

Canonical allocation behavior:

```python
candidate.mkdir(parents=False, exist_ok=False)
```

with deterministic retry on `FileExistsError`.

### 6.6 Identity agreement

The following must agree:

```text
directory name
RunPaths.run_id
RunResult.run_id
summary.json run_id
manifest.json run_id
```

A disagreement is a contract error.

### 6.7 No intentional reuse

A run ID used by a finalized or retained historical run must not be intentionally reassigned to another execution.

---

## 7. Output root

### 7.1 Definition

The output root is the parent directory under which GF Wordbench creates run directories.

### 7.2 Environment ownership

The output root is machine-local environment configuration.

It does not belong in portable `project/project.toml`.

### 7.3 Required properties

Before allocation, GF Wordbench MUST validate that the output root:

- resolves to an intended directory;
- is writable;
- is not a regular file;
- is not the active source directory;
- is not `project/validation/gold`;
- is not a required project-document directory;
- can contain a new child directory;
- has acceptable symlink/reparse-point behavior;
- does not escape an explicitly permitted root policy.

### 7.4 Repository-local output

The output root MAY be a dedicated directory under the repository root.

It MUST remain separate from active GF source and project-validation assets.

### 7.5 Existing output root

GF Wordbench MAY create the output root when:

- its parent exists or can be created safely;
- configuration permits creation;
- the path is not ambiguous;
- no project asset would be overwritten.

### 7.6 No implicit current-directory fallback

A missing output root MUST NOT silently become the terminal or GUI process current directory.

---

## 8. Canonical layout

Schema `1.0` canonical layout:

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

### 8.1 Empty directories

Standard subdirectories SHOULD be created during initialization even when the selected mode may leave some empty.

This gives every stage stable owned locations.

### 8.2 Optional files

Not every listed file must contain stage evidence in every mode.

Requiredness is determined by:

- selected mode;
- executed stages;
- report policy;
- project release policy;
- artifact manifest declarations.

### 8.3 Additional subdirectories

A new persistent subdirectory requires coordinated updates to:

- `RunPaths`;
- persisted layout documentation;
- artifact ownership;
- manifest roles;
- cleanup and archive behavior;
- tests.

### 8.4 Temporary files

Sibling temporary files used for atomic writes may exist during execution/finalization.

They MUST:

- remain inside the run root;
- use collision-safe names;
- not be treated as published artifacts;
- be removed after successful replacement;
- be ignored or quarantined after failed writes;
- not appear in `manifest.json`.

---

## 9. RunPaths ownership

### 9.1 Single builder

The functional `runs` module owns construction of run paths.

Bootstrap supplies the resolved run configuration and receives the resulting `RunPaths`. It does not define, duplicate, or reconstruct run-directory names and paths.

The callable boundary and model ownership are governed by `docs/INTERFILE_CONTRACT_LOCK.md`.

### 9.2 Consumer rule

Stages consume paths from `RunPaths`.

They MUST NOT independently reconstruct standard run filenames or subdirectories.

### 9.3 Recommended RunPaths model

```python
@dataclass(frozen=True, slots=True)
class RunPaths:
    run_id: str
    run_dir: Path

    summary_json: Path
    summary_md: Path
    ai_ready_md: Path
    top_errors_txt: Path
    manifest_json: Path

    details_dir: Path

    raw_dir: Path
    master_log: Path
    all_scan_logs: Path
    all_logs: Path
    raw_compile_dir: Path
    raw_scan_dir: Path
    raw_scenarios_dir: Path

    artifacts_dir: Path
    gfo_dir: Path
    out_dir: Path
    pgf_dir: Path
```

### 9.4 Immutability

`RunPaths` SHOULD be immutable after creation.

### 9.5 Containment invariant

Every owned path must resolve beneath `run_dir`.

### 9.6 Absolute internal paths

In-memory `RunPaths` fields may be absolute `Path` values.

Persisted run-owned paths use run-relative `/` form.

---

## 10. Directory creation

### 10.1 Creation order

Canonical sequence:

```text
1. validate output root
2. allocate run ID
3. atomically create run root
4. create standard subdirectories
5. validate containment and write access
6. initialize master log
7. expose RunPaths to the orchestrator
```

### 10.2 Failure during initialization

If creation fails before any useful evidence exists:

- return a configuration/filesystem error;
- do not claim a run was started;
- remove an empty partially created directory when safe.

If useful evidence already exists:

- preserve the directory;
- classify it as incomplete;
- report the path.

### 10.3 Directory permissions

The process must have:

- create permission on output root;
- read/write permission on the run root;
- create/write permission in stage-owned subdirectories;
- rename permission for atomic replacement;
- delete permission only when cleanup is requested.

### 10.4 Source permissions

Normal validation does not require write permission to project source or gold files.

---

## 11. Master log initialization

### 11.1 Canonical path

```text
raw/master.log
```

### 11.2 Timing

The master log SHOULD be available before the first validation stage begins.

### 11.3 Initial evidence

Initial records include:

```text
run ID
run start timestamp
GF Wordbench version
project ID
mode
resolved workspace and project roots
resolved output root
```

Sensitive values and complete environment dumps are prohibited.

### 11.4 Ownership

The audit orchestrator or designated run logger owns `master.log`.

### 11.5 Failure

Failure to create required run-level logging before stage execution is a run initialization error.

---

## 12. Stage ownership

Canonical ownership:

| Location | Owner |
|---|---|
| `summary.json` | JSON report writer |
| `summary.md` | Markdown report writer |
| `AI_READY.md` | AI-ready report writer |
| `top_errors.txt` | log/report writer |
| `manifest.json` | manifest writer |
| `details/` | detail report writer |
| `raw/master.log` | audit orchestrator/logger |
| `raw/compile/` | compiler/process evidence stage |
| `raw/scan/` | scanner |
| `raw/scenarios/` | scenario runner/normalizer |
| `artifacts/gfo/` | GF compilation stage |
| `artifacts/out/` | designated tool-output stage |
| `artifacts/pgf/` | PGF build stage |

### 12.1 No cross-owner rewrite

An observer may read another stage's artifact.

It may not silently modify it.

### 12.2 Derived artifacts

A derived artifact must reference its raw source evidence through structured results or documented paths.

### 12.3 File collision prevention

Owners must use deterministic collision-safe names.

Two source files with the same stem must not overwrite one another's logs or details.

---

## 13. Safe file keys

### 13.1 Purpose

Per-source and per-scenario artifacts require filesystem-safe unique names.

### 13.2 Properties

A safe key SHOULD be:

- deterministic;
- recoverably associated with source identity;
- free of path separators;
- free of reserved Windows characters;
- collision-resistant;
- bounded in length.

### 13.3 Duplicate stems

Duplicate stems must be disambiguated using normalized relative path information or a stable hash suffix.

### 13.4 Prohibited method

Using only:

```text
Path(file_path).stem
```

is insufficient when selected files can share a stem.

### 13.5 Stability

Changing safe-key generation changes artifact paths and requires contract/migration review.

---

## 14. Execution phase

### 14.1 Mutation policy

During `executing`, only owning stages may create or append their owned files.

### 14.2 Raw evidence first

External process stdout and stderr must be captured separately before normalization or aggregation.

### 14.3 GF-generated artifacts

GF may write tool artifacts only to designated run-owned output locations when supported.

When GF writes elsewhere temporarily, GF Wordbench must copy/catalogue the exact resulting bytes into an owned run location before finalization.

### 14.4 No project mutation

Normal execution MUST NOT modify:

- `.gf` source;
- `.gfs` scenarios;
- `.gold` files;
- project documentation;
- `project.toml`.

### 14.5 Partial evidence

A failed stage must preserve evidence captured before failure.

### 14.6 Timeouts

Timeout handling must preserve:

- timeout state;
- available stdout;
- available stderr;
- termination result;
- partial artifacts;
- duration.

---

## 15. Concurrent runs

### 15.1 Isolation

Multiple runs may execute concurrently only when each has:

- unique run root;
- independent raw directories;
- independent `.gfo`/`.pgf` output directories;
- independent report files;
- independent manifest.

### 15.2 Shared read-only inputs

Concurrent runs may read the same project source and scenarios.

### 15.3 Shared mutable outputs

Concurrent runs MUST NOT share:

- GFO output directory;
- PGF target path;
- normalized-output path;
- raw-log path;
- report path;
- manifest path.

### 15.4 Application state

`last_run` state is convenience data.

Concurrent runs may update it with atomic last-writer-wins behavior, but state ordering must not affect either run's correctness.

### 15.5 Cleanup exclusion

Cleanup must not delete a run known to be active.

Active-run protection SHOULD use an OS-level exclusive lock or an equivalent controlled mechanism.

Any temporary lock representation:

- is internal;
- is not a stable artifact;
- is removed before finalization;
- must not be listed in the manifest.

### 15.6 Project mutation conflict

A project-writing operation, such as gold update or project migration, must not run concurrently with a read-only release validation unless explicit locking guarantees a coherent source snapshot.

---

## 16. Source snapshot association

### 16.1 Evidence requirement

A run must associate results with the source content it validated.

### 16.2 Fingerprints

Relevant source files SHOULD have fingerprints stored in `summary.json`.

### 16.3 No implicit snapshot copy

The canonical run layout does not require copying the complete source tree into every run.

### 16.4 Source changes during execution

When a source file changes after fingerprinting but before its dependent operation finishes, GF Wordbench SHOULD detect the inconsistency when feasible.

Strict release mode MUST fail when it detects that one run combined multiple source states.

### 16.5 Historical rebuild

Rebuilding a run requires the archived source revision and toolchain identity.

The run directory alone may not contain all project source bytes.

---

## 17. Aggregation

### 17.1 Aggregate logs

Canonical aggregate files:

```text
raw/ALL_SCAN_LOGS.TXT
raw/ALL_LOGS.TXT
```

### 17.2 Role

Aggregate logs are convenience artifacts.

They are not primary structured sources of truth.

### 17.3 Source preservation

Aggregation must not delete or rewrite original per-stage evidence.

### 17.4 Missing optional inputs

An absent optional log must not crash aggregation.

### 17.5 Determinism

Aggregation order must be deterministic and preserve source attribution.

---

## 18. Details

### 18.1 Canonical location

```text
details/
```

### 18.2 Purpose

Detail files provide focused human- or AI-readable evidence for files, scenarios, gates, or failures.

### 18.3 Source authority

Details derive from structured results and existing evidence.

They do not rerun GF.

### 18.4 Collision safety

Detail filenames must preserve unique result identity.

### 18.5 Raw evidence

A detail file may quote bounded excerpts but must reference full raw paths.

---

## 19. Artifact collection

### 19.1 Canonical roots

```text
artifacts/gfo/
artifacts/out/
artifacts/pgf/
```

### 19.2 Current-run requirement

A tool-generated artifact counts as current-run evidence only when its production can be associated with:

- current run;
- current command;
- current source/entrypoint;
- current toolchain;
- current artifact path.

### 19.3 Stale artifact prevention

Required target directories should be empty at initialization.

Pre-existing files in a newly created run root are a contract violation.

### 19.4 Non-empty requirement

Required PGF artifacts must be non-empty.

Other artifacts follow their owning contracts.

### 19.5 Cataloguing

Every required finalized artifact appears in `manifest.json`.

---

## 20. Finalization preconditions

Finalization begins only after:

- no new validation stage will start;
- active external processes have exited or been terminated;
- stage results have been collected;
- stage writers have flushed and closed files;
- source fingerprints and configuration evidence are finalized;
- artifact declarations are available;
- no gold update is in progress;
- run outcome can be computed.

### 20.1 Failed stages

Validation failures do not prevent finalization.

### 20.2 Execution errors

Tool, timeout, and launch errors should still permit best-effort finalization when evidence can be written safely.

### 20.3 Catastrophic filesystem failure

When finalization storage is impossible, retain whatever exists and report the directory as incomplete.

---

## 21. Finalization order

Canonical successful sequence:

```text
1. stop stage execution
2. close all stage writers
3. finalize FileResult and ScenarioResult objects
4. finalize diff and diagnostic classifications
5. finalize release gates not dependent on physical manifest writing
6. resolve prospective artifact declarations
7. validate required prospective artifacts
8. finalize the success-path RunResult in memory
9. atomically write summary.json
10. write summary.md
11. write AI_READY.md
12. write top_errors.txt
13. write aggregate/detail artifacts not yet finalized
14. close every non-manifest writer
15. calculate published artifact sizes and SHA-256 values
16. atomically write manifest.json
17. re-read and verify manifest.json
18. freeze the run directory against normal writes
19. update disposable last-run state
20. return RunResult and artifact paths
```

### 21.1 Manifest self-exclusion

`manifest.json` does not hash itself.

### 21.2 Summary-manifest relationship

`summary.json` may reference `manifest.json`.

The manifest hashes the published `summary.json`.

### 21.3 No post-manifest writes

After successful manifest verification, no listed artifact may be modified.

### 21.4 Console output

Console/UI completion messages are emitted after finalization state is known.

---

## 22. Finalization failure

### 22.1 Report failure before manifest

When a required report cannot be written:

- run outcome becomes `ERROR`;
- preserve existing evidence;
- do not create a success manifest;
- attempt a bounded failure summary when possible;
- classify the directory as incomplete if canonical finalization cannot complete.

### 22.2 Manifest write or verification failure

When manifest creation fails:

1. release decision becomes `ERROR`;
2. invalid or partial canonical manifest is removed or quarantined;
3. summary and human reports may be rewritten to record the failure;
4. no valid manifest is claimed;
5. directory is incomplete, not finalized.

### 22.3 Failure after manifest verification

A write attempted after manifest verification is a contract violation.

If bytes changed:

- manifest verification fails;
- lifecycle state becomes corrupt;
- the run must not be reported as intact.

### 22.4 Best-effort diagnostics

Failure reporting must not destroy the previous valid file during atomic replacement.

---

## 23. Atomic writes

### 23.1 Required targets

Atomic replacement is required where supported for:

```text
summary.json
manifest.json
application state
migration outputs
```

It SHOULD also be used for completed Markdown/text reports.

### 23.2 Procedure

```text
write sibling temporary file
→ flush
→ close
→ validate
→ atomically replace destination
```

### 23.3 Temporary file failure

A failed temporary write must not destroy the last valid destination.

### 23.4 Run-local temporary files

Temporary files remain run-owned but are not published artifacts.

### 23.5 Directory creation

Directory creation uses atomic filesystem semantics and collision handling, not temporary-directory renaming from an unsafe root.

---

## 24. Finalized run invariants

A finalized run satisfies:

1. run root exists;
2. run ID is internally consistent;
3. `summary.json` validates;
4. required reports exist;
5. `manifest.json` validates;
6. all required manifest entries exist;
7. every manifest size matches;
8. every manifest SHA-256 matches;
9. manifest does not list itself;
10. listed paths remain inside the run root;
11. no stage writer remains active;
12. no required temporary file remains;
13. no listed artifact is modified after verification;
14. result outcome is explicit;
15. project and toolchain identity are recorded.

---

## 25. Incomplete runs

### 25.1 Detection

A run directory is incomplete when it lacks the evidence required to establish finalized state.

Typical indicators:

- no valid `summary.json`;
- no valid `manifest.json`;
- temporary report files remain;
- stage logs exist without completed result;
- manifest path referenced but absent;
- process ended during finalization.

### 25.2 Value

Incomplete runs may still contain useful diagnostic evidence.

They must not be silently deleted.

### 25.3 Inspection

Inspection tools should label them clearly:

```text
INCOMPLETE — not a finalized run
```

### 25.4 Previous-run comparison

Incomplete runs are not eligible as canonical previous-run baselines.

### 25.5 Release use

An incomplete run can never prove release readiness.

### 25.6 Resume policy

Schema/lifecycle `1.0` does not support implicit cross-process resume.

A new execution creates a new run.

### 25.7 Manual recovery

Files may be copied for investigation.

A recovered report package must not be represented as the original run's successful finalization unless a versioned recovery schema and audit trail explicitly define that operation.

---

## 26. Cancellation

### 26.1 Request

Cancellation asks the orchestrator to stop starting new stages and terminate owned processes safely.

### 26.2 Execution state

Cancellation is recorded as an execution state.

It is not added to the canonical validation-status enum.

### 26.3 Safe finalization

When possible, a cancelled run should:

- preserve completed results;
- preserve partial raw evidence;
- record cancellation;
- produce an `ERROR` or otherwise policy-defined non-success outcome;
- finalize reports and manifest.

Such a directory may be structurally finalized even though the run was cancelled.

### 26.4 Unsafe interruption

When cancellation prevents safe finalization, the directory remains incomplete.

### 26.5 Release

A cancelled release run cannot produce `READY`.

---

## 27. Crashes and abrupt termination

### 27.1 Crash before run creation

No run directory is expected.

### 27.2 Crash after initialization

The empty or near-empty directory is incomplete.

### 27.3 Crash during a stage

Captured files remain.

Open files may be truncated.

### 27.4 Crash during report writing

Atomic destinations protect previous valid files when available.

Temporary files may remain.

### 27.5 Crash during manifest writing

A valid canonical manifest should either be fully replaced or absent.

A partial manifest at the canonical path indicates a platform/filesystem failure and must be treated as corrupt/incomplete.

### 27.6 Next startup

GF Wordbench MAY scan run directories and classify obvious incomplete/corrupt runs.

It must not modify them during read-only discovery.

---

## 28. Corrupt runs

### 28.1 Definition

A corrupt run fails integrity or schema verification after appearing finalized.

### 28.2 Causes

- manual edit;
- disk corruption;
- partial copy;
- antivirus/quarantine action;
- failed synchronization;
- cleanup of individual files;
- unsafe archive extraction;
- post-finalization report rewrite.

### 28.3 Response

GF Wordbench must:

- report exact mismatch;
- preserve the directory;
- avoid using it as a trusted baseline;
- avoid rewriting the manifest to accept changed bytes;
- permit archival for forensic review.

### 28.4 Repair prohibition

Normal verification never repairs a corrupt manifest by recalculating hashes.

A deliberate re-manifest operation creates a new trust statement and must not be confused with verification of the original run.

---

## 29. Previous-run selection

### 29.1 Eligible canonical baseline

A previous run SHOULD satisfy:

- finalized lifecycle;
- valid supported `summary.json`;
- same compatible project identity;
- compatible summary schema;
- compatible validation semantics;
- relevant mode/scope;
- no integrity failure;
- not the current run.

### 29.2 Manifest preference

A valid manifest is preferred and SHOULD be required in strict/release comparison policy.

### 29.3 Legacy baseline

A legacy GF Audit run without a manifest may be readable through migration policy.

It must be labelled legacy/unverified and must not silently become equivalent to a canonical finalized run.

### 29.4 Selection order

Select deterministically using:

1. compatible run timestamp;
2. run ID;
3. collision suffix;
4. explicit user selection when supplied.

### 29.5 State pointer

The application state's last-run pointer is only a candidate.

The target must still be validated.

### 29.6 Exclusions

Exclude:

- incomplete runs;
- corrupt runs;
- other project IDs;
- unsupported schema versions;
- incompatible modes/scopes;
- directories with ambiguous identity.

---

## 30. Read-only inspection

### 30.1 Default

Opening, listing, viewing, diffing, and verifying a finalized run are read-only.

### 30.2 No report regeneration

A viewer must not regenerate missing reports automatically.

### 30.3 No timestamp touch

Inspection should avoid changing artifact modification timestamps.

### 30.4 Evidence paths

Readers use paths recorded in `summary.json` and `manifest.json`.

They do not reconstruct stage filenames when recorded paths exist.

### 30.5 Unknown files

Unknown files may be displayed as unmanifested.

They are not automatically trusted.

---

## 31. Retention policy

### 31.1 Safe default

GF Wordbench's default policy is:

```text
do not automatically delete run directories
```

### 31.2 Explicit cleanup

Deletion requires:

- explicit user command;
- explicit automation policy;
- or documented retention configuration.

### 31.3 Retention dimensions

A configurable policy may consider:

```text
age
run count
total size
project ID
mode
outcome
release status
archive status
baseline protection
```

Such configuration requires its own documented schema/contract.

### 31.4 Release protection

A `READY` release run SHOULD be archived before deletion.

### 31.5 Baseline protection

The current selected regression baseline SHOULD be protected unless deletion is explicitly forced or a replacement baseline is selected.

---

## 32. Cleanup eligibility

A run may be considered for cleanup only when:

- path is an immediate permitted descendant of the output root;
- normalized basename matches the run naming contract or a recognized legacy contract;
- it is not known active;
- no owning process holds an active lifecycle lock;
- requested scope is explicit;
- symlink/path checks pass;
- user or automation policy permits its state/outcome.

### 32.1 Finalized run

May be deleted explicitly after warning about loss of evidence.

### 32.2 Incomplete run

May be deleted explicitly after showing available evidence and age.

### 32.3 Corrupt run

May be deleted explicitly, but archival for diagnosis is recommended.

### 32.4 Active run

Must not be deleted.

### 32.5 Unknown directory

Must not be treated as a run solely because its name begins with `run_`.

Strict identity checks are required before recursive deletion.

---

## 33. Safe deletion

### 33.1 Containment

Before deletion:

```text
resolved candidate parent == resolved output root
```

or equivalent approved direct-child rule.

### 33.2 Symlink handling

Cleanup must not follow directory symlinks or unsafe reparse points outside the candidate.

### 33.3 Project protection

Cleanup must refuse any path resolving to:

- workspace root;
- source root;
- project validation root;
- project gold root;
- framework root;
- output root itself.

### 33.4 No wildcard deletion

User-supplied wildcard paths must be expanded and validated item by item.

### 33.5 Manifest-aware summary

Before deletion, show or record:

```text
run ID
project ID
mode
outcome
release decision
size
finalized/incomplete/corrupt state
archive status when known
```

### 33.6 Deletion failure

A partial deletion must be reported.

Remaining content must not be represented as intact.

### 33.7 Windows handles

On Windows, open handles may prevent deletion.

GF Wordbench should leave the remaining directory in place and report the blocking path rather than repeatedly forcing removal.

---

## 34. Bulk cleanup

### 34.1 Planning phase

Bulk cleanup SHOULD produce a plan before deleting.

The plan separates:

```text
selected
protected
ineligible
unknown
```

### 34.2 Dry run

The cleanup interface MUST provide a read-only planning operation before deletion. Exact CLI syntax belongs to `docs/usage/CLI_REFERENCE.md`.

### 34.3 Deterministic order

Delete oldest eligible runs first unless policy states otherwise.

### 34.4 Failure isolation

Failure to delete one run must not cause unsafe assumptions about another.

### 34.5 Audit record

Automation SHOULD preserve a cleanup log outside directories being deleted.

The cleanup log must not contain secrets.

---

## 35. Archival

### 35.1 Purpose

Archival preserves run evidence outside the active output root.

### 35.2 Pre-archive verification

A finalized run SHOULD pass manifest verification before archival.

Incomplete/corrupt runs may be archived, but their state must be labelled.

### 35.3 Byte preservation

Archive creation must preserve:

- relative paths;
- exact artifact bytes;
- `manifest.json`;
- Unicode filenames;
- required metadata needed for extraction.

### 35.4 No in-place normalization

Archival must not rewrite reports, paths, line endings, or binary artifacts.

### 35.5 Archive digest

The archive file may have an external SHA-256.

This is separate from the internal artifact manifest.

### 35.6 Archive format

The framework may support ZIP, TAR, or another documented format.

Making an archive format required needs an external-tool or standard-library contract.

### 35.7 Original directory

Archival does not imply deletion.

Deletion after archival requires a separate explicit decision.

---

## 36. Archive verification

Archive verification sequence:

```text
1. verify source run manifest
2. create archive
3. compute archive digest
4. extract to isolated temporary location
5. verify extracted run manifest
6. compare expected run ID and entry count
7. publish/archive
8. remove temporary extraction
```

### 36.1 Failure

If extracted verification fails:

- archive is invalid;
- original run remains authoritative;
- do not mark archival successful.

### 36.2 Incomplete archive

An archive of an incomplete run must not be relabelled finalized.

---

## 37. Restoration

### 37.1 Source

Restore from a trusted archive or verified copy.

### 37.2 Collision policy

If the original run-directory name already exists:

- do not merge directories;
- do not overwrite;
- do not silently rename while retaining contradictory run identity.

Use another output root or require an explicit restore destination.

### 37.3 Verification

After restoration:

- validate directory name/run ID agreement;
- validate summary;
- validate manifest;
- verify artifact hashes.

### 37.4 Read-only historical use

A restored run is normally historical evidence.

It is not resumed for execution.

### 37.5 Application state

Restoration does not automatically replace the active last-run pointer unless explicitly selected.

---

## 38. Copying

### 38.1 Complete copy

A copied finalized run should preserve the directory name and every manifested file byte.

### 38.2 Verification

Verify source before copy and destination after copy.

### 38.3 Partial copy

A partial copy is not a finalized run unless packaged under a separate export contract and manifest.

### 38.4 Cloud synchronization

Synchronizing a directory while it is executing/finalizing can expose inconsistent intermediate states.

Prefer synchronization after finalization.

### 38.5 Portable paths

Run-owned persisted paths are relative, allowing relocation of the complete directory.

Environment paths inside reports may remain absolute evidence.

---

## 39. Export packages

### 39.1 Reduced package

A reduced support or AI package is a new artifact set.

It does not reuse the original run manifest after removing files.

### 39.2 New manifest

A reduced package requires its own package/export manifest.

### 39.3 Redaction

Redacted files are new derived artifacts.

Do not modify the original manifested run in place.

### 39.4 Source evidence

An export references the original run ID and manifest hash through its own versioned export contract.

---

## 40. Disk-space behavior

### 40.1 Before run

GF Wordbench SHOULD check that the output root appears writable.

A reliable exact required-space prediction is not generally possible.

### 40.2 During run

Disk-full errors must:

- stop unsafe writes;
- preserve existing files;
- avoid destroying valid atomic destinations;
- produce an error when possible;
- leave the run incomplete if finalization cannot finish.

### 40.3 Large diagnostics

Output-size limits and truncation must be explicit.

### 40.4 Cleanup suggestion

The framework may suggest cleanup after a space error.

It must not delete runs automatically without policy.

---

## 41. Security

### 41.1 Untrusted paths

Output-root and run paths are untrusted until resolved and validated.

### 41.2 Path traversal

Run-owned relative paths must not contain traversal outside run root.

### 41.3 Symlinks

Strict release policy rejects manifested symlinks.

### 41.4 Secrets

Run artifacts must not contain:

- passwords;
- tokens;
- private keys;
- authentication cookies;
- complete environment dumps;
- secret command arguments.

### 41.5 Permissions

Sensitive environments SHOULD restrict run-directory access to intended users.

### 41.6 Executable artifacts

Do not execute files discovered in a historical run during inspection or verification.

### 41.7 Cleanup attack resistance

Recursive deletion requires containment checks on the resolved path, not only string-prefix checks.

---

## 42. Windows behavior

### 42.1 Supported paths

Run roots must support:

- drive letters;
- spaces;
- Unicode;
- long names within platform/tool limits.

### 42.2 Reserved characters

Generated filenames must avoid:

```text
< > : " / \ | ? *
```

and reserved device names.

### 42.3 Case-insensitive identity

Duplicate path detection should use case-insensitive comparison where the filesystem is case-insensitive while preserving canonical display casing.

### 42.4 Atomic replacement

Use Windows-compatible atomic replacement where supported.

### 42.5 Open handles

Close files and subprocess pipes before finalization, verification, archive, or cleanup.

### 42.6 Antivirus/indexing interference

Transient access errors should be retried only through a bounded documented policy.

They must not be hidden.

### 42.7 Path length

GF Wordbench SHOULD detect likely path-length problems before stage execution.

Safe keys and bounded run-root depth reduce risk.

---

## 43. POSIX behavior

### 43.1 Case sensitivity

Path identity normally remains case-sensitive.

### 43.2 Permissions

Respect umask and explicit permission policy.

### 43.3 Process children

Timeout/cancellation should terminate owned process groups where applicable.

### 43.4 Atomic rename

Atomic replacement normally requires temporary and destination files on the same filesystem.

### 43.5 Symlinks

Containment must be checked after symlink resolution according to strictness policy.

---

## 44. Network and removable storage

### 44.1 Support level

Network and removable output roots may be supported but are less reliable for:

- atomic replacement;
- file locking;
- timestamp precision;
- disconnect handling;
- concurrent access.

### 44.2 Strict release recommendation

Release runs SHOULD use a local stable filesystem, then archive/copy after manifest verification.

### 44.3 Capability check

When used, filesystem capabilities should be tested or warnings recorded.

### 44.4 Disconnect

A disconnect during execution/finalization leaves the run incomplete until integrity can be assessed.

---

## 45. Run discovery

### 45.1 Scope

Discovery scans immediate children of the configured output root.

### 45.2 Candidate rule

A candidate name matches:

```text
run_<run-id>
```

or a documented legacy naming pattern.

### 45.3 Classification

For each candidate, discovery may classify:

```text
finalized
incomplete
corrupt
legacy
unknown
```

### 45.4 Read-only

Discovery does not repair, delete, rename, or migrate by default.

### 45.5 Unknown children

Non-run directories remain untouched.

---

## 46. Run index

### 46.1 No required global index in schema `1.0`

The canonical model does not require one global run-index file.

### 46.2 Discovery source

The output-root directory plus each run's `summary.json`/`manifest.json` is sufficient.

### 46.3 Optional persistent index

A persistent index may improve performance, but it would require:

- schema identity/version;
- atomic updates;
- rebuild strategy;
- stale-entry policy;
- concurrency handling;
- tests.

### 46.4 Cache semantics

Any persistent index must be rebuildable and must not replace run-local evidence as authority.

---

## 47. Legacy GF Audit runs

### 47.1 Typical legacy layout

Legacy runs may include:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
details/
raw/
```

and may lack:

```text
manifest.json
artifacts/
scenario evidence
canonical schema IDs
```

### 47.2 Read policy

Legacy runs may be discovered and loaded through documented migration readers.

### 47.3 Identity

They are labelled legacy and unverified unless migrated.

### 47.4 No silent mutation

Discovery and comparison do not rewrite legacy directories.

### 47.5 Migration copy

A migration may create a new canonical copy or migration output.

It must preserve the legacy source directory untouched.

### 47.6 Missing evidence

A migrated legacy run cannot invent:

- scenario results;
- gold comparisons;
- PGF evidence;
- original manifest integrity.

Losses and unknowns must be reported.

---

## 48. Cleanup of legacy runs

### 48.1 Recognition

Legacy deletion requires a recognized legacy structure, not only a matching name.

### 48.2 Confirmation

Display:

- legacy status;
- available summary identity;
- missing manifest warning;
- age and size;
- selected path.

### 48.3 Archive first

Archival is recommended before deleting unique historical runs.

### 48.4 No canonical claim

Archiving a legacy directory does not make it canonical.

---

## 49. Operational diagnostics

Stable diagnostic codes:

```text
RUN_OUTPUT_ROOT_INVALID
RUN_OUTPUT_ROOT_NOT_WRITABLE
RUN_OUTPUT_ROOT_UNSAFE
RUN_ID_INVALID
RUN_ID_COLLISION_EXHAUSTED
RUN_DIRECTORY_CREATE_FAILED
RUN_DIRECTORY_LAYOUT_FAILED
RUN_PATH_OUTSIDE_ROOT
RUN_PATH_DUPLICATE
RUN_MASTER_LOG_CREATE_FAILED
RUN_STAGE_WRITE_FAILED
RUN_STAGE_PATH_COLLISION
RUN_FINALIZATION_FAILED
RUN_SUMMARY_WRITE_FAILED
RUN_REPORT_WRITE_FAILED
RUN_MANIFEST_WRITE_FAILED
RUN_MANIFEST_VERIFY_FAILED
RUN_POST_FINALIZATION_MUTATION
RUN_INCOMPLETE
RUN_CORRUPT
RUN_ACTIVE_CLEANUP_FORBIDDEN
RUN_CLEANUP_PATH_UNSAFE
RUN_CLEANUP_PARTIAL
RUN_ARCHIVE_FAILED
RUN_ARCHIVE_VERIFY_FAILED
RUN_RESTORE_COLLISION
RUN_RESTORE_VERIFY_FAILED
RUN_DISK_FULL
RUN_FILESYSTEM_CAPABILITY_UNSUPPORTED
RUN_LEGACY_UNVERIFIED
```

### 49.1 Error classification

Lifecycle/configuration failures normally use:

```text
error_kind = IO
```

or:

```text
error_kind = CONFIG
```

Tool-stage failures preserve their own error kinds.

---

## 50. CLI behavior

The CLI exposes operations to:

- list discovered runs;
- inspect one run;
- verify schemas and artifact integrity;
- archive a run;
- restore a verified archive;
- preview cleanup;
- delete explicitly selected eligible runs.

Exact command names, arguments, and exit codes belong to `docs/usage/CLI_REFERENCE.md`.

### 50.1 `runs list`

Shows:

```text
run ID
project ID
mode
outcome
lifecycle classification
release decision
start time
size
```

### 50.2 `runs show`

Reads canonical summary/manifest and displays artifact links.

### 50.3 `runs verify`

Performs read-only schema and integrity verification.

### 50.4 `runs archive`

Verifies, archives, extracts to a temporary location, and re-verifies when strict policy applies.

### 50.5 `runs clean`

Requires explicit selection or retention policy.

It does not delete active runs.

CLI syntax is defined in `docs/usage/CLI_REFERENCE.md`.

---

## 51. GUI behavior

The GUI SHOULD provide:

- current run directory;
- lifecycle state;
- run outcome;
- report links;
- manifest verification status;
- historical run list;
- incomplete/corrupt warning;
- archive action;
- cleanup preview.

The GUI MUST NOT:

- hide an incomplete run as completed;
- infer success from directory existence;
- resume an old run silently;
- delete an active run;
- rewrite historical reports during viewing;
- merge runs;
- use application state as run evidence.

---

## 52. CI behavior

A CI run SHOULD:

1. create a unique run directory;
2. preserve it after validation;
3. finalize reports;
4. verify manifest;
5. publish the run directory or archive;
6. fail release publication when finalization/integrity fails.

### 52.1 Workspace cleanup

CI may clean old workspace runs through explicit job policy.

### 52.2 Publication

Publish PGF only when release decision is `READY`.

### 52.3 Interrupted job

An interrupted job may leave an incomplete directory.

CI artifact upload may preserve it for diagnosis, clearly labelled incomplete.

### 52.4 Parallel jobs

Parallel jobs require distinct output roots or collision-safe run allocation.

---

## 53. Runs module ownership

The functional `runs` module owns the run-directory lifecycle within the hexagonal modular monolith.

Its responsibilities are separated by architectural ring:

### 53.1 Domain

The domain defines:

- run identity;
- lifecycle states and allowed transitions;
- containment and immutability invariants;
- cleanup eligibility;
- archive and restoration invariants.

### 53.2 Application

Application services coordinate:

- allocation and initialization;
- read-only discovery;
- finalization;
- verification;
- cleanup planning and deletion;
- archival and restoration.

### 53.3 Ports

Ports define required external capabilities for:

- filesystem operations;
- clocks and run identifiers;
- active-run locking;
- hashing;
- archive creation and extraction.

### 53.4 Adapters

Adapters implement operating-system and archive behavior while preserving the domain invariants in this document.

### 53.5 Entrypoints and bootstrap

CLI and GUI invoke the same application services. Bootstrap assembles the services and adapters but does not own lifecycle policy or path semantics.

---

## 54. Run models

```python
@dataclass(frozen=True, slots=True)
class RunAllocation:
    run_id: str
    run_dir: Path
    collision_index: int
```

```python
@dataclass(frozen=True, slots=True)
class RunDirectoryInfo:
    run_id: str | None
    path: Path
    lifecycle_state: str
    project_id: str | None
    mode: str | None
    outcome: str | None
    release_decision: str | None
    size_bytes: int | None
    warnings: tuple[str, ...]
```

```python
@dataclass(frozen=True, slots=True)
class CleanupCandidate:
    run_info: RunDirectoryInfo
    eligible: bool
    protected: bool
    reasons: tuple[str, ...]
```

```python
@dataclass(frozen=True, slots=True)
class RunFinalizationResult:
    status: str
    lifecycle_state: str
    summary_path: Path | None
    manifest_path: Path | None
    warnings: tuple[str, ...]
    message: str
```

### 54.1 Persisted boundary

These models are internal unless serialized.

Serializing them requires schema coordination.

---

## 55. Prohibited behavior

The following are prohibited:

- reusing one run directory for multiple executions;
- using a run directory as a shared compiler cache;
- writing GF artifacts into another run;
- reconstructing standard paths independently of `RunPaths`;
- writing reports before stage evidence is closed;
- hashing files while owners are still writing;
- modifying manifested artifacts after verification;
- considering a failed validation run incomplete solely because status is `FAIL`;
- considering a directory finalized solely because `summary.json` exists;
- silently resuming an incomplete run;
- repairing a manifest during verification;
- deleting runs automatically without policy;
- deleting a path based only on string prefix;
- following symlinks outside run root during cleanup;
- merging restored files into an existing run;
- renaming a restored run while leaving contradictory run IDs;
- treating aggregate logs as structured truth;
- deleting raw logs after creating details;
- copying project gold files into the run and presenting them as generated output;
- using application state as historical run authority;
- allowing GUI and CLI to create different layouts.

---

## 56. Drift indicators

Run-lifecycle drift is likely when:

- a stage invents a new standard path;
- two owners write the same file;
- a report is written outside the run root;
- a required subdirectory is missing in one interface;
- run ID differs between directory and summary;
- a new run omits `manifest.json`;
- a manifest lists a temporary file;
- report bytes change after manifest creation;
- a failed run loses raw evidence;
- a `FAIL` run is labelled incomplete despite successful finalization;
- an incomplete run is selected as previous baseline;
- cleanup can target project source;
- archive extraction cannot verify;
- run-owned paths are absolute in portable manifest fields;
- Windows and POSIX safe keys differ without reason;
- concurrent runs share `.gfo` output;
- state points to a run and the pointer is trusted without validation;
- legacy runs are silently rewritten;
- finalization changes between CLI and GUI.

Every indicator requires restoring the contract or performing a coordinated versioned change.

---

## 57. Required tests

Test files:

```text
tests/runs/test_run_id.py
tests/runs/test_run_paths.py
tests/runs/test_run_creation.py
tests/runs/test_run_lifecycle.py
tests/runs/test_run_finalization.py
tests/runs/test_run_discovery.py
tests/runs/test_run_cleanup.py
tests/runs/test_run_archive.py
tests/contracts/test_run_directory_contract.py
tests/integration/test_run_directory_lifecycle.py
tests/migrations/test_legacy_run_directory.py
```

### 57.1 Allocation tests

- UTC base ID;
- no collision;
- `_02` collision;
- multiple collisions;
- concurrent atomic creation;
- invalid output root;
- output root is file;
- output root not writable;
- output root inside source/gold;
- paths containing spaces;
- Unicode output root.

### 57.2 Layout tests

- all canonical directories created;
- every RunPaths value contained;
- no duplicate path;
- correct report filenames;
- correct raw directories;
- correct artifact directories;
- deterministic safe keys;
- duplicate stems disambiguated.

### 57.3 Execution tests

- raw stdout/stderr separate;
- timeout preserves partial evidence;
- failed compile preserves logs;
- failed scenario preserves logs;
- concurrent runs isolated;
- source remains unchanged;
- gold remains unchanged.

### 57.4 Finalization tests

- successful `OK` run finalizes;
- successful `FAIL` run finalizes;
- successful `ERROR` run finalizes when evidence permits;
- writers closed before hashing;
- summary atomic write;
- manifest atomic write;
- manifest self-exclusion;
- no post-manifest write;
- report failure;
- manifest failure;
- disk-full simulation;
- cancellation with safe finalization;
- cancellation leaving incomplete run.

### 57.5 Discovery tests

- canonical finalized run;
- incomplete run;
- corrupt run;
- legacy run;
- unknown directory;
- run-ID mismatch;
- unsupported summary schema;
- previous-run eligibility;
- state pointer validation.

### 57.6 Cleanup tests

- dry run;
- finalized deletion;
- incomplete deletion;
- active-run protection;
- source-root protection;
- output-root protection;
- traversal rejection;
- symlink rejection;
- partial deletion;
- Windows open-handle failure;
- baseline protection.

### 57.7 Archive tests

- verified archive;
- archive digest;
- extraction verification;
- Unicode filenames;
- corrupt archive;
- incomplete-run archive label;
- restore collision;
- no directory merge;
- restored manifest verification.

### 57.8 Legacy tests

- legacy layout detection;
- no manifest;
- unversioned summary;
- read-only discovery;
- migration preserves source;
- missing scenario evidence remains unknown.

---

## 58. Operational checklist

Before execution:

```text
[ ] Output root resolved
[ ] Output root safe and writable
[ ] Run ID allocated in UTC
[ ] Collision handled atomically
[ ] Run root created
[ ] Canonical directories created
[ ] RunPaths containment verified
[ ] Master log initialized
```

During execution:

```text
[ ] Stages use RunPaths
[ ] Raw streams captured separately
[ ] Stage ownership respected
[ ] Source and gold remain read-only
[ ] Timeouts preserve partial evidence
[ ] Generated artifacts stay run-owned
```

Before finalization:

```text
[ ] External processes stopped
[ ] Stage writers closed
[ ] Results collected
[ ] Required artifacts identified
[ ] No project-writing operation active
```

Finalization:

```text
[ ] summary.json written atomically
[ ] Human reports written
[ ] Aggregate/detail artifacts complete
[ ] All non-manifest writers closed
[ ] Artifact sizes and SHA-256 computed
[ ] manifest.json written atomically
[ ] Manifest re-read and verified
[ ] No post-manifest write
[ ] Last-run state updated
```

Retention:

```text
[ ] Run classified before cleanup
[ ] Active/baseline/release protections checked
[ ] Archive verified when required
[ ] Deletion path containment verified
[ ] Cleanup outcome recorded
```

---

## 59. Change policy

A run-directory change is contract-significant when it changes:

- run-ID format;
- collision suffix;
- output-root semantics;
- canonical directory layout;
- standard filenames;
- RunPaths public fields;
- path ownership;
- lifecycle-state interpretation;
- finalization order;
- manifest relationship;
- incomplete-run policy;
- previous-run eligibility;
- cleanup containment;
- archive/restore semantics.

A coordinated change MUST update:

1. persisted-schema lock;
2. interfile contract lock;
3. RunPaths;
4. run allocator;
5. audit orchestrator;
6. stage writers;
7. report writers;
8. manifest writer/verifier;
9. diff/previous-run loader;
10. state last-run handling;
11. CLI and GUI;
12. cleanup/archive tooling;
13. unit, contract, integration, and migration tests;
14. this document;
15. release and migration notes.

---

## 60. Enforcement rule

A run directory begins mutable, gathers evidence, and becomes immutable only through verified finalization.

Its operational completeness is independent from whether the language validation passed.

> Every execution receives one unique run directory; every stage writes only to its owned paths; every captured failure remains available; and no finalized artifact changes after the manifest verifies it.

Incomplete and corrupt runs remain visible and diagnosable. They are never silently resumed, repaired, selected as trusted baselines, or deleted without explicit policy.
