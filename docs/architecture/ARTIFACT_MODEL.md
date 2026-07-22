# GF Wordbench — Artifact Model

**Document ID:** `GF-WB-ARCH-ARTIFACT-MODEL`  
**Status:** Normative architecture  
**Applies to:** GF Wordbench framework, active project validation and generated run directories  
**Owner:** GF Wordbench maintainers  
**Primary implementation owners:** audit orchestration, stage owners, report writers and manifest writer  
**Related schema authority:** `docs/PERSISTED_SCHEMA_LOCK.md`  
**Related external boundary:** `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Related interfile authority:** `docs/INTERFILE_CONTRACT_LOCK.md`

---

## 1. Purpose

This document defines the architectural model for every file created, copied, catalogued, compared, retained or exposed by GF Wordbench.

It answers:

- what counts as an artifact;
- which artifacts belong to the project and which belong to a run;
- which component owns each artifact;
- how artifacts move from temporary to finalized state;
- which files are raw evidence and which are derived interpretations;
- how artifacts are named and addressed;
- how `RunPaths`, structured results, `summary.json` and `manifest.json` relate;
- when artifacts may be modified, copied, published, retained or deleted;
- how missing, stale, corrupt or untrusted artifacts affect validation;
- which rules prevent path, ownership and evidence drift.

The core rule is:

> Every persisted artifact has one owner, one defined path base, one lifecycle and one documented set of observers.

No consumer may silently reconstruct, relocate or rewrite an artifact owned by another component.

---

## 2. Scope

This model governs:

- project-owned configuration and validation assets;
- application state;
- run directories;
- raw process evidence;
- static scan logs;
- compile logs;
- scenario transcripts;
- normalized scenario output;
- gold-comparison diffs;
- `.gfo` files;
- `.pgf` files;
- other GF-generated outputs;
- structured run reports;
- human-readable reports;
- AI-ready reports;
- aggregate logs;
- per-result detail files;
- artifact manifests;
- migration outputs;
- exported or published run bundles;
- cleanup, retention and recovery behavior.

This model does not define:

- the complete JSON field schema of persisted formats;
- the internal binary format of `.gfo` or `.pgf`;
- GF command-line semantics;
- language-specific module contracts;
- operating-system backup implementations;
- user-interface layout.

Those topics belong to their dedicated specifications and contract locks.

---

## 3. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless an explicit exception is documented.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **ARTIFACT**: a persisted file or directory with a defined role in the system.
- **PROJECT ASSET**: a maintained input belonging to the active project.
- **RUN ARTIFACT**: output created or captured for one run.
- **RAW EVIDENCE**: unmodified evidence received from a source, process or filesystem observation.
- **DERIVED ARTIFACT**: output computed from other artifacts or structured results.
- **REPORT**: user- or machine-facing representation of a completed result.
- **OWNER**: component exclusively responsible for the artifact's location, format and write lifecycle.
- **OBSERVER**: component permitted to read but not redefine or rewrite an artifact.
- **PRODUCER**: component or external tool that creates bytes.
- **CATALOGUER**: component that records metadata about an artifact without owning its contents.
- **FINALIZED**: no longer writable during normal run execution.
- **REQUIRED ARTIFACT**: artifact whose absence invalidates a stage, run or release criterion.
- **OPTIONAL ARTIFACT**: artifact that may be absent without invalidating the run.
- **EPHEMERAL FILE**: temporary implementation file that is not part of the finalized artifact set.
- **PATH BASE**: authoritative directory against which a relative artifact path is resolved.
- **PROVENANCE**: information connecting an artifact to its producer, inputs and operation.

---

## 4. Fundamental distinctions

## 4.1 Source, project asset and run artifact

GF Wordbench distinguishes three primary file domains.

### Source files

Language implementation files consumed by GF:

```text
*.gf
```

Source files are inputs. A normal audit MUST NOT modify them.

### Project assets

Reviewed maintained inputs owned by the active language project:

```text
project/project.toml
project/docs/
project/validation/scenarios/*.gfs
project/validation/inputs/
project/validation/gold/*.gold
```

Project assets may be changed only through deliberate project-development workflows.

They are not generated run artifacts.

### Run artifacts

Files created or captured for one audit run:

```text
run_<run-id>/
```

Run artifacts are owned by the run and MUST NOT be written into project source or project validation directories.

---

## 4.2 Raw, normalized and interpreted evidence

The evidence chain is:

```text
external or source observation
    → raw evidence
    → normalized evidence
    → structured result
    → report
```

Each layer has different authority.

### Raw evidence

Examples:

- process stdout;
- process stderr;
- process command record;
- static scan hit log;
- original tool-generated `.gfo`;
- original tool-generated `.pgf`;
- filesystem metadata observed at execution time.

Raw evidence MUST remain unmodified after capture.

### Normalized evidence

Examples:

- normalized scenario output;
- path-normalized diagnostic text;
- newline-normalized comparison material;
- a bounded stable representation used for gold comparison.

Normalized evidence MUST retain a traceable relationship to its raw source.

### Structured result

Examples:

- `FileResult`;
- `ScenarioResult`;
- `CompileSummary`;
- `DiffEntry`;
- `RunResult`.

Structured results interpret evidence into typed fields.

They do not replace raw evidence.

### Report

Examples:

- `summary.json`;
- `summary.md`;
- `AI_READY.md`;
- `top_errors.txt`;
- detail pages.

Reports project structured results for specific consumers.

A report MUST NOT rerun validation or recover facts by parsing another human report.

---

## 4.3 Tool-generated and framework-generated artifacts

### Tool-generated

Produced by GF or another external executable:

```text
.gfo
.pgf
.dot
tool exports
stdout
stderr
```

The external tool produces the bytes.

GF Wordbench owns capture, placement, cataloguing and interpretation inside the run.

### Framework-generated

Produced directly by GF Wordbench:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
normalized scenario output
gold diffs
aggregate logs
detail reports
```

The designated framework component owns both production and lifecycle.

---

## 5. Artifact design principles

## 5.1 Single ownership

Every artifact MUST have one authoritative owner.

The owner defines:

- canonical location;
- canonical filename;
- format or schema;
- creation conditions;
- write timing;
- finalization timing;
- replacement policy;
- required or optional status;
- cleanup eligibility.

Observers MUST NOT redefine these properties.

---

## 5.2 Explicit path model

Artifact paths MUST be supplied by an explicit path model such as `RunPaths`, `ProjectConfig` or a dedicated artifact record.

Consumers MUST NOT construct owned artifact paths by repeating filename constants.

Prohibited:

```python
summary_path = run_dir / "summary.json"
```

inside an arbitrary consumer.

Expected:

```python
summary_path = run_paths.summary_json_path
```

The owner of path construction may use filename constants internally.

---

## 5.3 Evidence preservation

Interpretation failures MUST NOT erase valid evidence.

If diagnostic parsing, classification, comparison or report generation fails:

- existing raw stdout and stderr remain;
- already-produced tool artifacts remain;
- the secondary failure is recorded separately;
- the run may finalize as `ERROR`;
- cleanup MUST NOT remove evidence required to diagnose the failure.

---

## 5.4 No duplicate execution

Report and manifest components consume completed outputs.

They MUST NOT:

- compile GF modules;
- run `.gfs` scripts;
- rebuild PGF;
- repeat static scans;
- modify source fingerprints;
- regenerate missing raw evidence.

A missing required artifact is a contract failure, not permission for an observer to rerun its producing stage.

---

## 5.5 Deterministic layout

Given the same output root and run identifier, path construction MUST be deterministic.

The same semantic artifact role MUST resolve to the same relative location.

Artifact inventories MUST use deterministic ordering.

---

## 5.6 Portable references

References between run artifacts SHOULD use paths relative to the run directory.

References to project-owned assets SHOULD use paths relative to the project root.

Local environment paths may be absolute when required, but portable reports SHOULD clearly distinguish them.

---

## 5.7 Finalized-run immutability

After successful finalization:

- raw evidence MUST NOT change;
- `summary.json` MUST NOT change;
- `manifest.json` MUST NOT change;
- hashes MUST remain valid;
- reports SHOULD NOT change;
- generated grammar artifacts MUST NOT be replaced in place.

Corrections require a new run or an explicit migration/repair operation that records the change.

---

## 6. Artifact domains

GF Wordbench uses five artifact domains.

| Domain | Path base | Normal owner | Mutability |
|---|---|---|---|
| Source domain | language source root | project maintainers | editable outside validation |
| Project domain | project root | project maintainers | reviewed edits |
| State domain | configured state location | state manager | replaceable |
| Run domain | run directory | run-stage owners | mutable until finalization |
| Export domain | configured export destination | export/publish operation | operation-specific |

Artifacts MUST NOT cross domains implicitly.

---

## 7. Canonical run directory

## 7.1 Directory identity

Canonical pattern:

```text
run_<run-id>
```

Recommended identifier:

```text
YYYYMMDD_HHMMSS
```

UTC is required for the timestamp component.

Collision suffix:

```text
run_20260721_163210_02
```

A run ID MUST remain stable for the lifetime of the run.

---

## 7.2 Canonical layout

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
│   ├── process/
│   ├── compile/
│   ├── scan/
│   └── scenarios/
└── artifacts/
    ├── gfo/
    ├── out/
    ├── pgf/
    └── other/
```

`raw/process/` and `artifacts/other/` MAY be absent when unused.

Additional subdirectories require:

- one stable responsibility;
- one designated owner;
- documentation;
- path-model support;
- manifest role support where persisted;
- tests.

---

## 7.3 Directory rules

- The run directory MUST be created before stage output is written.
- Every run-owned file MUST remain under the resolved run directory.
- Path traversal outside the run directory is prohibited.
- The run directory MUST NOT be the active project source directory.
- A run MUST NOT reuse another run's mutable workspace.
- Existing finalized runs MUST NOT be overwritten.
- A failed run MAY still be finalized with partial evidence.
- Empty planned directories MAY be omitted unless a consumer requires them.
- Directory presence alone MUST NOT be interpreted as stage success.

---

## 8. `RunPaths` model

## 8.1 Purpose

`RunPaths` is the in-memory authoritative path registry for one run.

It prevents:

- duplicated path constants;
- report-specific path reconstruction;
- disagreement between writers and observers;
- mixed absolute and relative path semantics;
- accidental writes outside the run root.

## 8.2 Canonical responsibilities

`RunPaths` should resolve at least:

```text
run_id
run_dir
master_log_path
all_scan_logs_path
all_logs_path
summary_json_path
summary_md_path
ai_ready_path
top_errors_path
manifest_path
details_dir
raw_dir
process_logs_dir
compile_logs_dir
scan_logs_dir
scenario_logs_dir
artifacts_dir
gfo_dir
out_dir
pgf_dir
other_artifacts_dir
```

Fields may be added compatibly only when:

- the new artifact class has a distinct responsibility;
- a safe default or migration exists;
- all writers and readers are updated;
- persisted schemas are updated when the field is serialized.

## 8.3 Path invariants

- `run_dir` is the path base for all run-owned paths.
- Every run-owned path resolves inside `run_dir`.
- Path fields use one consistent internal type.
- Serialized run-owned paths are run-relative where the schema requires portability.
- No consumer derives a sibling path by renaming a supplied path.
- The path model is built before audit stages execute.
- Run paths do not encode active-language defaults.
- Path validation occurs before external execution.

---

## 9. Artifact taxonomy

## 9.1 Control artifacts

Control artifacts describe the run itself.

Examples:

```text
summary.json
manifest.json
master.log
```

They coordinate readers and provide run-level identity.

---

## 9.2 Raw process artifacts

Examples:

```text
raw/process/gf_version.out.txt
raw/process/gf_version.err.txt
raw/compile/<safe-key>.out.txt
raw/compile/<safe-key>.err.txt
raw/scenarios/<scenario-id>.stdout.txt
raw/scenarios/<scenario-id>.stderr.txt
```

Required properties:

- stdout and stderr are separate;
- bytes are captured before normalization;
- decoding policy is explicit;
- truncation is explicit and recorded;
- command and execution metadata remain available;
- files become immutable after capture.

---

## 9.3 Static scan artifacts

Examples:

```text
raw/scan/<safe-file-key>.scan.txt
raw/ALL_SCAN_LOGS.TXT
```

The scanner owns per-file scan logs.

Aggregate scan reports observe and concatenate or summarize them without changing the originals.

Static scan artifacts MUST distinguish source observations from native GF results.

---

## 9.4 Scenario artifacts

Examples:

```text
raw/scenarios/<scenario-id>.stdout.txt
raw/scenarios/<scenario-id>.stderr.txt
raw/scenarios/<scenario-id>.out
raw/scenarios/<scenario-id>.gold.diff
```

Roles:

- `.stdout.txt`: raw standard output;
- `.stderr.txt`: raw standard error;
- `.out`: normalized comparison material;
- `.gold.diff`: derived mismatch evidence.

The normalized output MUST reference its source transcript in the structured scenario result.

A gold diff MUST identify:

- scenario ID;
- gold path;
- actual normalized output path;
- comparison result;
- normalization version.

---

## 9.5 GF compilation artifacts

Examples:

```text
artifacts/gfo/*.gfo
artifacts/pgf/*.pgf
artifacts/out/*
artifacts/other/*
```

Rules:

- GF produces the bytes;
- the stage owner controls the approved destination;
- required artifacts are checked after process completion;
- stale pre-existing files MUST NOT count as current success;
- source fingerprint or run provenance SHOULD link the artifact to the current source state;
- copied artifacts retain their raw identity and are not rewritten;
- binary grammar artifacts are not parsed as a substitute for GF validation unless a separate supported tool contract exists.

---

## 9.6 Report artifacts

### Machine report

```text
summary.json
```

This is the primary machine-readable run record.

### Human report

```text
summary.md
```

This is a readable projection of the structured run result.

### AI-ready report

```text
AI_READY.md
```

This is a bounded evidence packet, not a separate diagnosis engine.

### Error summary

```text
top_errors.txt
```

This is a stable textual ranking of normalized error buckets.

### Details

```text
details/
```

Detail files may expose focused copies, excerpts or structured views.

They MUST reference original evidence and MUST NOT replace it.

---

## 9.7 Aggregate artifacts

Examples:

```text
raw/ALL_SCAN_LOGS.TXT
raw/ALL_LOGS.TXT
```

Aggregate files are derived convenience artifacts.

Rules:

- source ordering is deterministic;
- source file boundaries are explicit;
- aggregation does not modify source logs;
- failure to build an aggregate file does not erase source evidence;
- aggregate logs are not authoritative when source logs are present.

---

## 9.8 Manifest artifact

```text
manifest.json
```

The manifest catalogs finalized artifacts.

It is a control artifact and a cataloguer, not the owner of catalogued bytes.

The manifest MUST NOT:

- rewrite an artifact;
- infer success from filename alone;
- include itself in its own hash inventory;
- replace `summary.json`;
- invent missing producer metadata.

---

## 9.9 Application-state artifact

Canonical:

```text
.gf_wordbench_state.json
```

Legacy readable input:

```text
.gf_audit_state.json
```

Application state:

- is outside the run artifact set;
- stores convenience and local-environment data;
- is disposable;
- is not release evidence;
- is not project identity;
- MUST NOT store run results;
- MUST NOT store credentials;
- is replaced atomically.

---

## 9.10 Project validation assets

### Scenarios

```text
project/validation/scenarios/*.gfs
```

Executable project inputs.

### Inputs

```text
project/validation/inputs/
```

Reviewed canonical test data.

### Gold files

```text
project/validation/gold/*.gold
```

Reviewed expected normalized output.

These are project assets, not run outputs.

Normal validation MUST NOT modify them.

---

## 10. Artifact ownership registry

| Artifact or family | Owner | Allowed observers |
|---|---|---|
| `project/project.toml` | project maintainers / project initializer | project loader, bootstrap, validators |
| `.gf_wordbench_state.json` | state manager | GUI, bootstrap |
| source `*.gf` | language project maintainers | selector, scanner, compiler, fingerprint stage |
| scenario `*.gfs` | project maintainers | project loader, scenario runner, security checks |
| validation inputs | project maintainers | scenario runner |
| gold `*.gold` | project maintainers / explicit gold updater | comparator, reports |
| run directory | audit orchestration | all run components |
| `master.log` | audit orchestration or log owner | report aggregation, users |
| per-file scan log | scanner | result builder, details, reports |
| compile stdout/stderr | compiler | diagnostic parser, classifier, details, reports |
| scenario stdout/stderr | scenario runner | normalizer, assertions, reports |
| normalized scenario `.out` | scenario runner / normalizer | gold comparator, reports |
| gold diff | gold comparator | scenario result, reports |
| `.gfo` | GF compile stage | manifest, reports, release checks |
| `.pgf` | GF PGF build stage | manifest, release checks, approved export |
| `summary.json` | JSON report writer | diff loader, GUI, CLI, automation, verifier |
| `summary.md` | Markdown report writer | users, GUI |
| `AI_READY.md` | AI-ready report writer | users, AI systems |
| `top_errors.txt` | log/report writer | users, automation where documented |
| `details/` | detail report writer | users, GUI |
| aggregate logs | aggregate log writer | users, reports |
| `manifest.json` | manifest writer | verifier, cleanup, export, automation |

An observer MUST NOT rewrite an artifact owned by another component.

---

## 11. Producer, owner and cataloguer

These roles may differ.

Example for a PGF:

```text
producer   = GF executable
owner      = PGF build stage
cataloguer = manifest writer
observer   = release verifier
```

Example for compile stderr:

```text
producer   = GF executable
owner      = compiler capture stage
cataloguer = manifest writer
observer   = diagnostic parser
```

Example for `summary.json`:

```text
producer   = JSON report writer
owner      = JSON report writer
cataloguer = manifest writer
observer   = GUI, diff loader, automation
```

The cataloguer records metadata but cannot change the artifact's semantics or lifecycle.

---

## 12. Artifact provenance

Every process-backed artifact SHOULD be traceable to:

```text
run_id
stage
contract_id
producer
command
working_directory
effective_environment_overrides
started_at
finished_at
duration_ms
exit_code
execution_state
input identities
source fingerprints
artifact path
artifact role
```

Provenance may be distributed across:

- structured process result;
- file or scenario result;
- run metadata;
- raw log;
- manifest;
- `summary.json`.

No single human report is required to repeat all provenance.

Required provenance MUST remain machine-readable.

---

## 13. Safe artifact keys

File and scenario paths may contain separators, spaces, punctuation or platform-specific syntax.

A run artifact filename that represents another path MUST use a deterministic safe key.

A safe-key algorithm MUST:

- produce filesystem-safe text;
- avoid path traversal;
- be deterministic;
- distinguish different normalized source paths;
- have a collision policy;
- preserve the original source identity elsewhere;
- be tested on Windows and POSIX paths.

A safe key MUST NOT become the canonical source identity.

Canonical identity remains the normalized project-relative source path or configured scenario ID.

---

## 14. Lifecycle states

Every run moves through lifecycle phases.

```text
planned
    → initialized
    → executing
    → assembling
    → finalizing
    → finalized
```

Failure may produce:

```text
failed-partial
```

Cancellation may produce:

```text
cancelled-partial
```

## 14.1 Planned

Configuration and path models are resolved.

No run-owned output is assumed to exist.

## 14.2 Initialized

The run directory and required writable directories exist.

Initial metadata and master logging may begin.

## 14.3 Executing

Stage owners write their assigned artifacts.

Only the owner of an artifact may modify it.

## 14.4 Assembling

Structured results are complete enough for reports.

Raw evidence is already closed and immutable.

Report writers generate their outputs.

## 14.5 Finalizing

The system:

1. closes remaining writers;
2. validates required paths;
3. computes final sizes and hashes;
4. writes `manifest.json`;
5. verifies consistency;
6. marks the run finalized.

## 14.6 Finalized

Normal mutation is prohibited.

The run may be read, compared, exported, backed up or deleted through explicit operations.

## 14.7 Partial terminal states

A failed or cancelled run may still retain evidence.

It SHOULD contain:

- run identity;
- partial raw evidence;
- explicit failure or cancellation state;
- available structured results;
- a partial summary where possible;
- a manifest or partial inventory if safely producible.

A partial run MUST NOT be presented as complete release evidence.

---

## 15. Write protocol

## 15.1 Direct raw capture

Raw stdout and stderr may be streamed directly to final raw paths when:

- the file is owned exclusively by the active stage;
- no reader observes it before closure;
- closure occurs before parsing;
- partial capture remains diagnostically useful.

## 15.2 Atomic replacement

Atomic replacement SHOULD be used for:

- `summary.json`;
- application state;
- `manifest.json`;
- migrated configuration;
- gold updates;
- compact reports where partial files are misleading.

Protocol:

1. write sibling temporary file;
2. flush;
3. close;
4. validate;
5. atomically replace destination where supported.

## 15.3 Append-only artifacts

Append-only behavior is appropriate for:

- `master.log`;
- live operation logs.

Append-only files MUST be closed before final hashing.

After finalization, append is prohibited.

## 15.4 Partial files

Temporary or incomplete filenames SHOULD be distinguishable:

```text
<name>.tmp
<name>.partial
```

Partial files:

- are not canonical artifacts;
- MUST NOT appear as successful required artifacts;
- SHOULD be removed after successful replacement;
- MAY be retained after catastrophic failure only when clearly marked and useful for recovery.

---

## 16. Finalization protocol

A run is finalized only when all applicable steps complete.

```text
[ ] All stages stopped writing
[ ] All process streams closed
[ ] Required raw evidence checked
[ ] Required GF artifacts checked
[ ] Structured results completed
[ ] Count invariants validated
[ ] Reports written
[ ] Run-relative paths validated
[ ] Artifact sizes computed
[ ] SHA-256 hashes computed
[ ] Manifest written
[ ] Manifest consistency verified
[ ] Final run status recorded
```

Finalization MUST NOT convert a failed validation into an error merely because expected success artifacts are absent.

The distinction is:

- validation failure: expected failure evidence exists;
- artifact failure: a required artifact contract was violated;
- report failure: evidence exists but a report could not be generated;
- manifest failure: final artifact inventory could not be trusted.

---

## 17. Manifest model

## 17.1 Purpose

The manifest answers:

- which files belong to the finalized run;
- what role each file has;
- whether it is required;
- which component created or captured it;
- its media type;
- its byte size;
- its SHA-256 hash.

## 17.2 Required artifact record

Conceptual fields:

```text
path
role
media_type
required
size_bytes
sha256
created_by
```

Additional compatible fields may include:

```text
stage
contract_id
source_artifact
producer
```

The persisted schema authority remains `docs/PERSISTED_SCHEMA_LOCK.md`.

## 17.3 Manifest rules

- Paths are relative to the run directory.
- Paths are unique.
- Directories are not entries.
- Entries are sorted deterministically.
- Hashes are computed from finalized bytes.
- The manifest excludes itself.
- A required summary artifact must appear.
- A missing required file invalidates verification.
- An unexpected file MAY be recorded as `other` or reported as untracked according to strictness policy.
- Symlinks SHOULD be rejected in strict mode.
- Paths escaping the run root are prohibited.

## 17.4 Partial manifests

A partial terminal run MAY have:

```text
manifest.partial.json
```

A partial manifest MUST NOT use the canonical finalized schema identity without an explicit completion-state field.

The preferred approach is to write the canonical manifest only when final inventory is reliable.

---

## 18. Artifact roles

Recommended manifest roles:

```text
machine_summary
human_summary
ai_handoff
top_errors
master_log
aggregate_log
scan_log
compile_stdout
compile_stderr
scenario_stdout
scenario_stderr
scenario_output
gold_diff
detail
gfo
pgf
tool_output
migration_record
other
```

A role:

- describes semantic purpose;
- does not determine ownership by itself;
- must not be reused with a different meaning;
- may be extended through schema-compatible versioning;
- should correspond to one documented artifact family.

---

## 19. Required versus optional artifacts

Requiredness depends on mode, stage and configuration.

## 19.1 Always required for a finalized normal run

Expected baseline:

```text
summary.json
summary.md
manifest.json
master.log
```

`AI_READY.md` and `top_errors.txt` are required when enabled by the final product contract.

The definitive required set is controlled by the persisted schema and release policy.

## 19.2 Conditionally required

Examples:

- compile stdout/stderr when compilation executes;
- normalized scenario output when a scenario executes;
- gold diff when a gold mismatch occurs;
- `.gfo` when a compile contract requires it;
- `.pgf` in release mode when configured;
- `AI_READY.md` when AI handoff reporting is enabled;
- detail files when retained by configuration.

## 19.3 Optional

Examples:

- stdout file for a process that produced no stdout, if empty streams are represented another documented way;
- optional scenario artifacts;
- CPU statistics;
- Graphviz output;
- exported formats;
- extra diagnostic details.

Optional MUST NOT mean undocumented.

---

## 20. Mode-specific artifact expectations

## 20.1 Quick mode

Typical required outputs:

- selected-file scan evidence;
- selected-file compile evidence when enabled;
- quick result;
- normal run reports;
- manifest.

PGF is normally not required.

## 20.2 Checkpoint mode

Typical required outputs:

- checkpoint compile evidence;
- required checkpoint scenario evidence;
- applicable normalized outputs and comparisons;
- regression comparison;
- normal run reports;
- manifest.

## 20.3 Release mode

Typical required outputs:

- all release-gate evidence;
- final entrypoint compile or load evidence;
- required scenario outputs;
- gold comparisons;
- final `.pgf`;
- release reports;
- complete verified manifest.

A release run with a missing required PGF is not release-ready.

## 20.4 Diagnostic mode

Diagnostic mode may retain additional:

- detailed scan evidence;
- optional scenario output;
- introspection output;
- extended process metadata;
- per-result detail files.

Additional retention does not change the authority of raw versus derived artifacts.

---

## 21. Missing artifact semantics

A missing artifact is classified according to its contract.

### Required process output missing

Example:

```text
required PGF absent after successful exit
```

Result:

```text
artifact_failure
```

### Optional output missing

Record absence where relevant.

Do not fail solely due to optional absence.

### Report missing

If raw evidence and structured results exist but a required report fails:

- preserve evidence;
- record report failure;
- set run status according to error policy;
- do not label GF validation itself as failed unless it failed independently.

### Manifest missing

A run without a required manifest is not fully finalized.

It MAY remain usable as partial evidence but is not a verified finalized run.

---

## 22. Stale artifact prevention

A stale artifact from an earlier operation MUST NOT count as current success.

Prevention strategies include:

- unique run directories;
- empty owned output directories at initialization;
- before/after filesystem snapshots;
- process start timestamps;
- expected output path checks;
- source fingerprints;
- artifact modification-time checks;
- manifest provenance;
- removal of pre-existing files from the active run workspace.

Release success MUST verify that the PGF belongs to the current run.

---

## 23. Artifact integrity

## 23.1 Hashing

Canonical manifest hashing uses:

```text
SHA-256
```

Hashes are lowercase hexadecimal.

## 23.2 Integrity verification

Verification checks:

- file exists;
- path remains under run root;
- size matches;
- hash matches;
- required role is present;
- duplicate entries do not exist;
- canonical reports parse successfully;
- manifest does not include itself.

## 23.3 Integrity failure

An integrity failure means the finalized artifact set cannot be trusted as recorded.

The verifier MUST:

- identify the affected artifact;
- preserve the file;
- distinguish missing from modified;
- avoid silently rewriting the manifest;
- return a structured verification failure.

---

## 24. Relationships between `summary.json` and `manifest.json`

`summary.json` answers:

```text
What happened?
What were the results?
Where are the important artifacts?
```

`manifest.json` answers:

```text
Which finalized files exist?
What are their roles, sizes and hashes?
```

Rules:

- `summary.json` is the primary machine result.
- `manifest.json` is the primary finalized file inventory.
- The manifest includes `summary.json`.
- The manifest excludes itself.
- `summary.json` references `manifest.json`.
- Neither file replaces the other.
- Shared paths and run IDs MUST agree.
- Verification SHOULD detect disagreement.

---

## 25. Relationships between reports and evidence

```text
raw evidence
    → typed result
        → summary.json
        → summary.md
        → AI_READY.md
        → top_errors.txt
        → details/
```

Reports MUST derive factual claims from typed results and explicit artifact references.

Reports MUST NOT:

- parse `summary.md` to recover structured fields;
- use `AI_READY.md` as the source of run status;
- infer missing stdout from aggregate logs;
- present excerpts without referencing source evidence;
- modify source logs while formatting.

---

## 26. Gold artifacts and comparison

Gold files are project assets.

Actual normalized output is a run artifact.

The comparison relationship is:

```text
project gold
    ↔ normalized run output
    → structured comparison result
    → optional diff artifact
```

Normal validation:

- reads gold;
- writes actual output to the run;
- writes diff to the run when useful;
- never edits gold.

Explicit gold update:

- is a separate operation;
- shows or stores the diff;
- writes atomically;
- changes the project asset;
- requires project review;
- is not disguised as run finalization.

---

## 27. Export and publication

An export is a copy of selected finalized artifacts.

Export MUST NOT mutate the source run.

An export policy defines:

- selected roles;
- destination;
- archive format if any;
- redaction rules;
- preservation of relative paths;
- inclusion of manifest;
- integrity verification before and after export;
- handling of absolute environment paths;
- handling of sensitive excerpts.

Recommended export sets:

### Minimal diagnostic packet

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
selected raw evidence
manifest.json
```

### Complete run archive

```text
entire finalized run directory
```

### Release package

```text
verified PGF
release summary
manifest
license and provenance metadata
```

A release package is not automatically the same as a complete audit archive.

---

## 28. Security boundaries

Artifacts may contain:

- source paths;
- diagnostics;
- command arguments;
- environment-specific locations;
- linguistic test data;
- generated grammar content.

Artifacts MUST NOT contain:

- access tokens;
- passwords;
- private keys;
- authentication cookies;
- complete environment dumps;
- secret command-line arguments.

Before publication:

- inspect environment paths;
- apply documented redaction;
- preserve diagnostic meaning;
- do not modify raw evidence while continuing to label it raw;
- create a redacted derived copy when necessary;
- record that redaction occurred.

Untrusted run artifacts MUST NOT be executed.

`.gfs` files are project executable inputs, not safe passive reports.

---

## 29. Retention classes

Recommended retention classes:

| Class | Examples | Default intent |
|---|---|---|
| `project` | scenarios, inputs, gold, project docs | version-controlled |
| `release` | release run, PGF, manifest | long-term |
| `baseline` | selected comparison runs | retained until superseded deliberately |
| `diagnostic` | investigation runs | medium-term |
| `development` | quick/checkpoint runs | short-term |
| `ephemeral` | temporary files | delete after completion |

Retention policy MUST be documented separately in operations documentation.

Cleanup MUST use artifact metadata and finalized run identity rather than filename age alone where possible.

---

## 30. Cleanup rules

Cleanup may remove a run only when:

- it is not active;
- no writer holds it open;
- it is not protected as release or baseline evidence;
- retention policy allows removal;
- the target path is confirmed inside the approved output root;
- the operation is explicit or policy-driven;
- deletion failure is reported.

Cleanup MUST NOT:

- delete project sources;
- delete project gold files;
- delete the active run;
- follow unsafe symlinks;
- treat an unverified path as a run;
- partially delete a protected release run without an explicit repair procedure.

---

## 31. Recovery rules

Recovery addresses interrupted writes or partial runs.

Possible recoverable evidence:

- closed raw stdout/stderr;
- completed scan logs;
- completed tool artifacts;
- temporary report files;
- partial structured state.

Recovery SHOULD:

1. identify the run state;
2. avoid resuming external execution implicitly;
3. preserve existing raw evidence;
4. quarantine corrupt control files;
5. rebuild only derived artifacts when source evidence and structured data are sufficient;
6. create a new manifest after explicit repair;
7. record that repair occurred.

A repair operation MUST NOT pretend the original finalization succeeded unchanged.

---

## 32. Backward compatibility

Legacy artifacts may use:

- different filenames;
- absolute paths;
- `ai_brief_path`;
- `ai_ready_path`;
- flat summary structure;
- unversioned state;
- legacy run layouts.

Compatibility readers MAY resolve these forms through documented migrations.

Canonical writers MUST emit only the current artifact model.

A layout change is breaking when it changes:

- an owned filename;
- a path base;
- a required artifact;
- artifact role semantics;
- observer expectations;
- manifest interpretation.

Such changes require:

- schema version review;
- path migration;
- reader updates;
- tests;
- documentation updates.

---

## 33. Artifact contract tests

Recommended test modules:

```text
tests/artifacts/
├── test_run_paths.py
├── test_run_directory.py
├── test_artifact_ownership.py
├── test_raw_evidence.py
├── test_artifact_finalization.py
├── test_manifest_generation.py
├── test_manifest_verification.py
├── test_required_artifacts.py
├── test_stale_artifact_detection.py
├── test_artifact_export.py
├── test_artifact_cleanup.py
└── test_artifact_recovery.py
```

Required test cases include:

### Paths

- Windows paths with spaces;
- POSIX paths;
- run-root escape attempt;
- duplicate safe-key collision;
- deterministic path construction;
- run-relative serialization.

### Raw evidence

- stdout only;
- stderr only;
- both streams;
- empty streams;
- decoding error;
- explicit truncation;
- parser failure after capture.

### Required artifacts

- expected `.gfo` present;
- expected `.gfo` missing;
- expected `.pgf` present;
- expected `.pgf` stale;
- expected `.pgf` empty;
- optional artifact absent.

### Finalization

- successful finalization;
- report failure;
- manifest write failure;
- open stream detected;
- partial run;
- cancelled run.

### Manifest

- deterministic ordering;
- correct SHA-256;
- changed file;
- missing required file;
- duplicate path;
- path traversal;
- self-entry rejection;
- untracked file policy.

### Ownership

- observer cannot rewrite;
- report does not invoke compiler;
- manifest does not modify artifacts;
- gold remains unchanged in normal validation.

---

## 34. Automated artifact checks

Recommended command:

```text
gf-wordbench artifacts check <run-dir>
```

Strict mode:

```text
gf-wordbench artifacts check <run-dir> --strict
```

The checker should verify:

1. run directory identity;
2. canonical control files;
3. run-root containment;
4. required artifacts by mode;
5. summary/manifest agreement;
6. manifest uniqueness;
7. size and SHA-256 integrity;
8. canonical schema readability;
9. absence of manifest self-entry;
10. raw evidence references;
11. normalized-to-raw provenance;
12. no unexpected mutable partial files;
13. no project asset inside the run presented as authoritative source;
14. no run artifact written into project validation directories;
15. finalization state consistency.

---

## 35. Drift indicators

Artifact-model drift exists when:

- two components define the same filename;
- a report reconstructs a path instead of using `RunPaths`;
- an observer rewrites an artifact;
- stdout and stderr are merged before raw capture;
- normalization changes raw evidence;
- a report reruns GF;
- a missing required artifact is ignored;
- a stale PGF counts as release success;
- a run-owned path is serialized sometimes absolute and sometimes relative;
- manifest and summary disagree;
- a file moves without updating schemas and consumers;
- gold changes during normal validation;
- a temporary file is mistaken for a finalized artifact;
- a partial run is presented as complete;
- an untracked file becomes silently required;
- cleanup deletes a protected baseline;
- a new artifact family lacks an owner;
- a manifest role is reused with different semantics.

Every drift indicator requires restoration of the model or a coordinated contract change.

---

## 36. Change workflow

An artifact change is complete only when all applicable items are addressed.

```text
[ ] Artifact role identified
[ ] Owner identified
[ ] Producer identified
[ ] Observers identified
[ ] Path base identified
[ ] RunPaths updated
[ ] Requiredness classified
[ ] Raw/derived/report class identified
[ ] Lifecycle defined
[ ] Finalization behavior defined
[ ] Manifest role defined
[ ] Schema impact reviewed
[ ] Security impact reviewed
[ ] Retention impact reviewed
[ ] Cleanup impact reviewed
[ ] Recovery impact reviewed
[ ] Writers updated
[ ] Readers updated
[ ] Tests updated
[ ] Contract locks updated
[ ] Documentation updated
```

Change record template:

```text
Artifact:
Current path:
New path:
Owner:
Producer:
Observers:
Role:
Required:
Raw or derived:
Lifecycle:
Schema impact:
Compatibility:
Migration:
Security:
Retention:
Tests:
```

---

## 37. Responsibility boundaries

### Audit orchestration

Owns:

- run identity;
- run directory initialization;
- stage order;
- lifecycle transition;
- finalization coordination.

Does not own:

- stage-specific raw bytes;
- report schemas;
- GF artifact contents.

### Stage owner

Owns:

- stage-specific paths supplied through the path model;
- capture and closure;
- stage result references;
- required artifact checks for that stage.

Does not own:

- cross-stage classification;
- user-facing reports;
- manifest semantics.

### Result builder

Owns:

- typed assembly;
- count consistency;
- artifact references in results.

Does not own artifact bytes.

### Report writer

Owns one report format and path.

Consumes completed structured data.

Does not execute validation.

### Manifest writer

Owns the manifest format and write lifecycle.

Catalogues other artifacts.

Does not own their bytes.

### Verifier

Reads finalized artifacts and manifest.

Does not silently repair them.

### Cleanup operation

Applies explicit retention policy.

Does not redefine artifact ownership or success.

---

## 38. Related documents

### Normative locks

- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`

### Architecture

- `docs/architecture/ARCHITECTURE_OVERVIEW.md`
- `docs/architecture/COMPONENT_MAP.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/PROCESS_EXECUTION_MODEL.md`
- `docs/architecture/ERROR_HANDLING_MODEL.md`

### Reports and operations

- `docs/reports/REPORTING_OVERVIEW.md`
- `docs/reports/ARTIFACT_MANIFEST.md`
- `docs/reports/RAW_LOGS_REFERENCE.md`
- `docs/operations/RUN_DIRECTORY_LIFECYCLE.md`
- `docs/operations/CLEANUP_BACKUP_AND_RECOVERY.md`

### Validation and GF

- `docs/validation/VALIDATION_PIPELINE.md`
- `docs/validation/RELEASE_GATES.md`
- `docs/gf/GF_COMPILATION.md`
- `docs/gf/GF_PGF_BUILD.md`
- `docs/scenarios/OUTPUT_NORMALIZATION.md`

---

## 39. Final enforcement rule

Artifacts are not incidental files.

They are the durable evidence, machine contracts and review surfaces through which GF Wordbench proves what it executed and why it reached a result.

Therefore:

> No artifact path, role, owner, requiredness, lifecycle, schema or retention meaning may change through an isolated implementation edit.

Every artifact-model change must update its producer, owner, observers, path model, schema, manifest behavior, tests and documentation as one coordinated change.
