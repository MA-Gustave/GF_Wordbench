# GF Wordbench — Raw Logs Reference

**Document ID:** `GF-WB-RAW-LOGS-REFERENCE`  
**Status:** Normative reporting and evidence reference  
**Applies to:** Every GF Wordbench validation run  
**Owner:** GF Wordbench maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Canonical path:** `docs/reports/RAW_LOGS_REFERENCE.md`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This document defines the raw-log and aggregate-log model used by GF Wordbench.

It specifies:

- which log files exist;
- where each file is stored;
- which component owns each file;
- which files contain primary raw evidence;
- which files are derived aggregates;
- how stdout and stderr are captured;
- how scan logs are written;
- how scenario logs are represented;
- how the master lifecycle log is formatted;
- how aggregate files are assembled;
- how encoding, timestamps, newlines, ordering, truncation, redaction, and atomic writes are handled;
- how logs relate to `summary.json`, reports, detail files, and `manifest.json`;
- how incomplete and failed runs remain diagnosable;
- how the legacy GF Audit layout migrates to the canonical GF Wordbench layout.

The central rule is:

> Individual operation logs are the authoritative evidence; aggregate logs are reproducible convenience views.

Raw logs do not replace structured run results.

The primary machine-readable source of truth remains:

```text
run_<run-id>/summary.json
```

The artifact-integrity source remains:

```text
run_<run-id>/manifest.json
```

---

## 2. Related normative documents

This document must be read with:

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/validation/VALIDATION_PIPELINE.md
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
docs/reports/REPORTING_OVERVIEW.md
docs/reports/ARTIFACT_MANIFEST.md
```

When this document conflicts with a lock file, the lock file governs.

---

## 3. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **PRIMARY RAW EVIDENCE**: bytes or faithfully decoded text captured directly from one operation.
- **LIFECYCLE LOG**: framework-generated chronological record of run events.
- **DERIVED AGGREGATE**: reproducible concatenation of other log files.
- **NORMALIZED OUTPUT**: versioned stable representation derived from raw evidence.
- **DETAIL REPORT**: focused human-readable explanation derived from structured results and evidence.
- **AUTHORITATIVE**: source that must be consulted before any copied or summarized representation.
- **FINALIZED**: no further writes are permitted except through an explicitly documented repair workflow.
- **TRUNCATED**: incomplete evidence retained under an explicit size policy.
- **REDACTED**: content intentionally removed under a documented security policy.

---

## 4. Scope

This document governs:

- `raw/master.log`;
- `raw/ALL_SCAN_LOGS.TXT`;
- `raw/ALL_LOGS.TXT`;
- GF version-probe stdout and stderr;
- per-file scan logs;
- per-file compile stdout and stderr;
- PGF-build stdout and stderr;
- scenario stdout and stderr;
- normalized scenario `.out` files as related derived evidence;
- process metadata represented in log headers;
- aggregate section formats;
- log ordering;
- log finalization;
- log references from reports and manifests.

This document does not define:

- the complete `summary.json` schema;
- Markdown report prose;
- diagnostic classification rules;
- GF command syntax;
- project-specific gold content;
- run-retention duration;
- archive file formats.

---

## 5. Evidence hierarchy

GF Wordbench uses this hierarchy:

1. individual primary raw operation logs;
2. verified process metadata;
3. tool-generated artifacts;
4. normalized derived output;
5. structured `RunResult` and `summary.json`;
6. aggregate log bundles;
7. detail reports;
8. human summary reports.

An aggregate copy must not override the corresponding individual file.

When an aggregate and an individual file differ:

```text
individual file wins
```

When raw evidence and a human report differ:

```text
raw evidence plus structured result wins
```

When raw evidence is missing:

```text
the report must state that evidence is missing
```

It must not reconstruct raw output from a summary.

---

## 6. Canonical run layout

The canonical run layout is:

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
│   ├── gf_version.out.txt
│   ├── gf_version.err.txt
│   ├── compile/
│   │   ├── <subject-key>.out.txt
│   │   └── <subject-key>.err.txt
│   ├── scan/
│   │   └── <subject-key>.scan.txt
│   └── scenarios/
│       ├── <scenario-id>.out.txt
│       ├── <scenario-id>.err.txt
│       └── <scenario-id>.out
└── artifacts/
    ├── gfo/
    ├── out/
    └── pgf/
```

Additional raw files may be added only when:

- ownership is defined;
- naming is deterministic;
- the artifact manifest can identify them;
- no existing semantic role is duplicated;
- persisted-schema implications are reviewed.

---

## 7. Log categories

GF Wordbench distinguishes five categories.

### 7.1 Lifecycle log

```text
raw/master.log
```

Framework-generated chronological run events.

### 7.2 Primary external-process logs

Examples:

```text
raw/gf_version.out.txt
raw/gf_version.err.txt
raw/compile/<subject-key>.out.txt
raw/compile/<subject-key>.err.txt
raw/scenarios/<scenario-id>.out.txt
raw/scenarios/<scenario-id>.err.txt
```

These preserve external process streams.

### 7.3 Primary static-scan logs

```text
raw/scan/<subject-key>.scan.txt
```

These preserve scanner findings and scan metadata.

### 7.4 Derived normalized outputs

```text
raw/scenarios/<scenario-id>.out
```

These are not raw process streams.

They are versioned derived evidence used for markers and gold comparison.

### 7.5 Derived aggregate logs

```text
raw/ALL_SCAN_LOGS.TXT
raw/ALL_LOGS.TXT
```

These concatenate selected authoritative files for convenient inspection.

They are never the sole copy of required evidence.

---

## 8. Ownership map

| Artifact | Writer | Primary readers |
|---|---|---|
| `raw/master.log` | audit orchestrator / lifecycle logger | humans, diagnostics, aggregate writer |
| version stdout/stderr | GF toolchain adapter / process runner | compatibility checker, diagnostics |
| compile stdout/stderr | compiler through process runner | diagnostic parser, reports |
| scan logs | scanner | reports, aggregate writer |
| scenario stdout/stderr | scenario runner through process runner | marker verifier, diagnostics |
| normalized scenario `.out` | normalizer / scenario runner | gold comparator, reports |
| `ALL_SCAN_LOGS.TXT` | aggregate log writer | humans, AI-assisted debugging |
| `ALL_LOGS.TXT` | aggregate log writer | humans, AI-assisted debugging |
| `details/*` | detail report writer | humans, AI systems |
| `summary.json` | JSON report writer | automation, GUI, diff loader |
| `manifest.json` | manifest writer | integrity verifier, archive tooling |

A reader must not rewrite an artifact owned by another component.

---

## 9. Common text rules

All canonical text logs MUST use:

```text
UTF-8 without BOM
```

Canonical newlines:

```text
LF
```

Readers MUST accept:

```text
LF
CRLF
```

Writers MUST:

- end finalized text logs with one newline;
- preserve Unicode;
- avoid `NaN`-like textual metadata where a stable token is available;
- avoid unbounded accidental binary decoding;
- preserve empty stdout or stderr files when the process produced no content;
- use atomic replacement for fully generated aggregate files where supported.

Primary process logs may be written incrementally.

---

## 10. Empty-file policy

An empty raw stream is valid evidence.

Examples:

```text
stdout empty, stderr contains diagnostic
stdout contains result, stderr empty
both streams empty, exit code recorded separately
```

GF Wordbench MUST preserve empty stream files for required external operations when the operation launched.

An absent file and an empty file are not equivalent.

```text
empty file = captured stream contained zero decoded characters
missing file = evidence capture failed, operation was skipped, or file contract was violated
```

Structured metadata must distinguish these cases.

---

## 11. Path representation

### 11.1 On disk

Files use native host paths.

### 11.2 In persisted records

Run-owned paths are serialized relative to the run directory with `/`.

Example:

```text
raw/compile/GrammarFre.out.txt
```

### 11.3 Inside raw tool output

Raw stdout and stderr preserve tool-emitted paths.

They may contain:

- absolute Windows paths;
- POSIX paths;
- RGL paths;
- project-relative paths.

Raw tool output must not be rewritten solely for portability.

### 11.4 In normalized or aggregate headers

Aggregate headers should use portable run-relative paths.

Optional environment display fields may use normalized `/` separators.

---

## 12. Safe subject keys

Per-subject filenames use a deterministic safe key.

The key should be derived from:

```text
stable subject identity
```

Examples:

```text
GrammarFre
lib__src__french__GrammarFre
scenario__linearize
pgf__French
```

### 12.1 Required properties

A safe key MUST:

- be deterministic;
- be unique within its log namespace;
- avoid path separators;
- avoid Windows-reserved filename characters;
- avoid `.` and `..` as complete names;
- avoid control characters;
- avoid trailing spaces or dots;
- remain bounded in length;
- resolve collisions deterministically.

### 12.2 Collision suffix

Recommended collision suffix:

```text
--<first-12-sha256>
```

Example:

```text
GrammarFre--a18c5b9120d4.out.txt
```

### 12.3 Identity preservation

The full original subject identity must appear in:

- structured result fields;
- aggregate section header;
- optional individual log metadata header.

The safe filename is not the authoritative subject identity.

---

# 13. `raw/master.log`

## 13.1 Purpose

`master.log` records the GF Wordbench run lifecycle.

It answers:

- when the run started;
- which configuration was resolved;
- which stage started and ended;
- which subjects were processed;
- which warnings occurred;
- whether cancellation or fatal failure occurred;
- when finalization completed.

It is not a substitute for `summary.json`.

## 13.2 Owner

```text
audit orchestrator
lifecycle logging service
```

Stage components may emit structured events through the orchestrator.

They should not open and append to `master.log` independently.

## 13.3 Canonical path

```text
raw/master.log
```

## 13.4 Recommended line format

```text
<RFC3339-UTC> <LEVEL> <EVENT> [key=value ...]
```

Example:

```text
2026-07-21T16:32:10.142Z INFO run_started run_id=20260721_163210 mode=release
2026-07-21T16:32:10.210Z INFO stage_started stage=VAL-070 name=gf_version_probe
2026-07-21T16:32:10.398Z INFO stage_completed stage=VAL-070 status=OK duration_ms=188
2026-07-21T16:32:11.011Z WARN diff_unavailable reason=no_compatible_previous_run
2026-07-21T16:32:14.825Z ERROR scenario_failed scenario=parse status=FAIL
2026-07-21T16:32:15.003Z INFO run_completed overall_status=FAIL duration_ms=4861
```

### 13.4.1 Timestamp

Timestamp MUST be:

- UTC;
- RFC 3339 compatible;
- millisecond precision recommended;
- monotonic ordering preserved by event sequence where wall-clock resolution ties.

### 13.4.2 Level

Canonical lifecycle levels:

```text
DEBUG
INFO
WARN
ERROR
FATAL
```

`DEBUG` emission may be configurable.

### 13.4.3 Event

Event names should use:

```text
lower_snake_case
```

### 13.4.4 Key-value fields

Keys should use:

```text
lower_snake_case
```

Values containing whitespace or control characters must be escaped or JSON-quoted consistently.

The master log is semi-structured.

Automation must use `summary.json`, not depend on parsing every master-log line.

---

## 13.5 Required lifecycle events

A completed run should include applicable events for:

```text
run_started
configuration_resolved
run_directory_created
gf_probe_started
gf_probe_completed
selection_completed
stage_started
stage_completed
subject_started
subject_completed
warning
cancellation_requested
fatal_error
reports_started
reports_completed
manifest_started
manifest_completed
run_finalizing
run_completed
```

Exact event vocabulary may expand without changing the run-summary schema.

Removing or redefining established event meaning requires documentation and test review.

---

## 13.6 Required run-start information

The run-start section should identify:

```text
run_id
mode
project_id
workspace_root
gf_executable
output_root
strict flag
```

Sensitive environment variables must not be logged.

The full GF path may be logged when required for reproducibility, but secrets and unrelated environment data must not be included.

---

## 13.7 Required operation events

For external operations, the master log should record references, not duplicate full streams.

Example:

```text
2026-07-21T16:32:12.110Z INFO process_completed operation=compile subject=lib/src/french/GrammarFre.gf exit_code=1 execution_state=completed stdout=raw/compile/GrammarFre.out.txt stderr=raw/compile/GrammarFre.err.txt
```

The full command may be represented in a dedicated structured request record or safely rendered lifecycle field.

It must not replace structured command metadata.

---

## 13.8 Append and finalization

`master.log` is append-oriented during execution.

Requirements:

- each append must preserve prior content;
- a failed append must not truncate the file;
- messages should be flushed at meaningful boundaries;
- fatal-error handling should attempt a completion append;
- after manifest publication, the log becomes finalized.

If finalization discovers a late failure:

1. append the failure;
2. update structured status;
3. regenerate affected aggregate/report artifacts;
4. regenerate the manifest;
5. write the completion event.

---

## 13.9 Legacy timestamp migration

The legacy implementation may prefix messages with local time at write time.

GF Wordbench uses UTC timestamps associated with event creation.

A report rewrite must not assign a new timestamp to an old event.

---

# 14. GF version logs

## 14.1 Canonical paths

```text
raw/gf_version.out.txt
raw/gf_version.err.txt
```

## 14.2 Content

These files contain the exact captured text streams from the version probe.

They must not contain:

- interpreted compatibility status;
- normalized version alone;
- report prose.

Parsed version information belongs in structured results.

## 14.3 Empty and missing behavior

- empty stream: valid captured evidence;
- missing both after a claimed launched probe: evidence error;
- skipped probe: files may be absent, but structured result must say `SKIPPED`;
- launch failure: files may exist as empty captures, with launch error stored structurally.

## 14.4 Aggregation

`ALL_LOGS.TXT` may include both version files when they exist.

---

# 15. Compile stdout and stderr logs

## 15.1 Canonical paths

```text
raw/compile/<subject-key>.out.txt
raw/compile/<subject-key>.err.txt
```

## 15.2 Authority

These are the authoritative captured streams for one GF compile or build operation.

The diagnostic parser consumes them but must not alter them.

## 15.3 One operation, one pair

Each external GF operation gets its own unique pair.

Do not reuse one file pair for:

- multiple source files;
- retries;
- module compile and PGF build;
- two different GF versions.

### 15.3.1 Retry naming

Recommended:

```text
<subject-key>--attempt-01.out.txt
<subject-key>--attempt-01.err.txt
<subject-key>--attempt-02.out.txt
<subject-key>--attempt-02.err.txt
```

The structured result identifies the authoritative attempt.

Retries must be explicit.

---

## 15.4 PGF-build logs

Until a dedicated persisted `raw/pgf/` directory is introduced, PGF build logs belong under:

```text
raw/compile/
```

Recommended names:

```text
pgf__<target-key>.out.txt
pgf__<target-key>.err.txt
```

Example:

```text
raw/compile/pgf__French.out.txt
raw/compile/pgf__French.err.txt
```

Creating a required `raw/pgf/` directory is a persisted-layout change and requires updating the schema lock.

---

## 15.5 Optional individual metadata header

Primary external stdout and stderr should normally contain only captured stream content.

A metadata header MAY be added only when:

- raw bytes are stored separately; or
- the contract explicitly defines the text file as an envelope rather than an exact stream.

The preferred model is:

```text
stream file = captured stream only
metadata = structured result / master log / operation record
```

This preserves fidelity.

---

## 15.6 Stream decoding

Preferred policy:

1. capture bytes;
2. retain bytes temporarily until successful persistence;
3. decode as UTF-8 strictly;
4. if decoding fails, preserve a byte artifact or explicit binary-safe representation;
5. create a diagnostic text view using replacement characters;
6. record decode failure structurally.

Silently dropping invalid bytes is prohibited.

---

## 15.7 Timeout and partial output

On timeout:

- preserve all available stdout;
- preserve all available stderr;
- record `timed_out=true`;
- do not append a fabricated timeout message into the captured stream;
- place framework timeout explanation in structured metadata and `master.log`.

Partial output remains authoritative for what was received.

---

# 16. Static scan logs

## 16.1 Canonical path

```text
raw/scan/<subject-key>.scan.txt
```

## 16.2 Purpose

A scan log records:

- scanned file identity;
- scanner version or rule-set version;
- rules evaluated;
- findings;
- locations;
- counts;
- scanner warnings or errors.

It is framework-generated evidence, not GF output.

## 16.3 Recommended format

```text
GF_WORDBENCH_SCAN_LOG 1.0
subject: lib/src/french/GrammarFre.gf
scanner_version: 1.0
status: OK
findings: 2

[GFSCAN-RUNTIME-STR-MATCH]
line: 42
severity: warning
message: Runtime string matching detected.
excerpt: ...

[GFSCAN-TRAILING-SPACE]
line: 88
severity: info
message: Trailing whitespace detected.
```

This format is reviewable text.

If external automation begins parsing it as a strict schema, the format must be formally versioned in `PERSISTED_SCHEMA_LOCK.md`.

## 16.4 No-finding behavior

A successful scan with no findings should still produce a file when the file was scanned.

Example:

```text
status: OK
findings: 0
```

## 16.5 Scanner failure

A scanner failure log should contain a bounded framework explanation.

The structured file result must use:

```text
validation_status = ERROR
error_kind = IO, CONFIG, or INTERNAL
```

as applicable.

## 16.6 Source excerpts

Excerpts must:

- be bounded;
- preserve Unicode;
- include line identity;
- avoid copying unrelated source;
- not become a substitute for the source file.

---

# 17. Scenario stdout and stderr logs

## 17.1 Canonical paths

```text
raw/scenarios/<scenario-id>.out.txt
raw/scenarios/<scenario-id>.err.txt
```

## 17.2 Authority

These files preserve GF shell process streams.

They must be written before:

- marker verification;
- output normalization;
- gold comparison;
- scenario detail reporting.

## 17.3 Scenario identity

Scenario IDs must be unique and path-safe.

If the ID is not safe as a filename, a safe key is used while the full ID remains in structured metadata.

## 17.4 Required separation

Do not combine stdout and stderr into one primary scenario log.

GF versions and platforms may emit diagnostics on either stream.

## 17.5 Missing markers

Marker failures belong in:

- structured scenario result;
- master lifecycle log;
- detail report;
- optional diagnostic aggregate section.

They must not modify the captured stdout or stderr.

## 17.6 Normalized scenario output

Canonical path:

```text
raw/scenarios/<scenario-id>.out
```

This file:

- is derived;
- has a normalization version;
- uses UTF-8 and LF;
- may replace approved unstable paths;
- must preserve linguistic content;
- is the input to gold comparison.

It is not named `.out.txt` because `.out.txt` is reserved for primary stdout capture.

---

# 18. `raw/ALL_SCAN_LOGS.TXT`

## 18.1 Purpose

`ALL_SCAN_LOGS.TXT` concatenates all available individual scan logs in deterministic file-result order.

It provides one convenient scan-only packet.

## 18.2 Authority

It is a derived aggregate.

Individual files under:

```text
raw/scan/
```

remain authoritative.

## 18.3 Canonical path

```text
raw/ALL_SCAN_LOGS.TXT
```

## 18.4 Generation time

Generate near finalization, after:

- all selected scans have completed or been represented;
- file-result ordering is fixed;
- scan log paths are stable.

## 18.5 Header

Recommended file header:

```text
GF WORDBENCH — ALL SCAN LOGS
Run ID: <run-id>
Project: <project-id>
Generated: <RFC3339-UTC>
Source count: <integer>
Included sections: <integer>
Authoritative source: individual files under raw/scan/
```

## 18.6 Section format

Recommended:

```text
================================================================================
BEGIN SCAN LOG
subject: lib/src/french/GrammarFre.gf
path: raw/scan/GrammarFre.scan.txt
status: OK
sha256: <hash-or-pending>
--------------------------------------------------------------------------------
<exact individual scan-log content>
--------------------------------------------------------------------------------
END SCAN LOG
================================================================================
```

## 18.7 Section order

Use canonical `file_results` order:

```text
normalized project-relative file path
```

## 18.8 Missing individual scan log

When a selected result has no scan log:

- do not invent one;
- optionally include a metadata-only missing section;
- record the missing evidence in the structured result;
- required missing evidence affects run status.

Recommended metadata-only section:

```text
BEGIN SCAN LOG
subject: ...
path: null
status: MISSING
reason: <structured reason>
END SCAN LOG
```

## 18.9 Aggregate rebuild

The file may be regenerated from individual scan logs and structured identities.

Its hash changes when:

- source log content changes;
- section order changes;
- header metadata changes.

A finalized run must not regenerate it silently.

---

# 19. `raw/ALL_LOGS.TXT`

## 19.1 Purpose

`ALL_LOGS.TXT` provides a single operational evidence packet.

It is intended for:

- manual diagnosis;
- AI-assisted investigation;
- archive inspection;
- environments where browsing many files is inconvenient.

## 19.2 Authority

It is a derived aggregate.

It must not be the only copy of any required raw stream.

## 19.3 Canonical path

```text
raw/ALL_LOGS.TXT
```

## 19.4 Canonical content

The canonical aggregate includes, when available:

1. `raw/master.log`;
2. GF version stdout;
3. GF version stderr;
4. individual compile/PGF stdout logs;
5. individual compile/PGF stderr logs;
6. individual scenario stdout logs;
7. individual scenario stderr logs;
8. optionally a reference to `ALL_SCAN_LOGS.TXT`, not a second embedded copy;
9. explicit missing-evidence notices.

It MUST NOT embed full copies of:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
details/*
```

Those are reports or manifests, not primary operational logs.

This avoids:

- large duplication;
- stale copies;
- recursive report bundles;
- confusing report prose with raw evidence;
- unnecessary secret/path replication;
- manifest instability.

## 19.5 Legacy behavior

The legacy GF Audit implementation may concatenate:

- `master.log`;
- `ALL_SCAN_LOGS.TXT`;
- `top_errors.txt`;
- `AI_READY.md`;
- `summary.md`;
- `summary.json`;
- detail logs;
- per-file logs.

GF Wordbench narrows `ALL_LOGS.TXT` to operational evidence.

Reports remain separate top-level artifacts.

## 19.6 Header

Recommended:

```text
GF WORDBENCH — ALL OPERATION LOGS
Run ID: <run-id>
Project: <project-id>
Mode: <mode>
Generated: <RFC3339-UTC>
Authoritative source: individual files under raw/
Reports: see ../summary.json, ../summary.md, ../AI_READY.md
Scan aggregate: ALL_SCAN_LOGS.TXT
```

## 19.7 Section format

Recommended:

```text
================================================================================
BEGIN LOG
role: compile_stderr
subject: lib/src/french/GrammarFre.gf
path: raw/compile/GrammarFre.err.txt
encoding: UTF-8
size_bytes: 412
sha256: <hash-or-pending>
--------------------------------------------------------------------------------
<exact decoded log content>
--------------------------------------------------------------------------------
END LOG
================================================================================
```

## 19.8 Empty stream section

An empty stream may be represented as:

```text
<EMPTY STREAM>
```

This marker exists only in the aggregate.

The authoritative individual stream file remains empty.

## 19.9 Missing stream section

A missing expected file may be represented as:

```text
<MISSING EVIDENCE: raw/compile/GrammarFre.err.txt>
```

The aggregate must not create a replacement individual file.

## 19.10 Order

Canonical order:

1. lifecycle log;
2. version probe;
3. compile/PGF operations in selected subject order;
4. scenarios in configured execution order;
5. other explicitly registered raw process logs in stable role/path order.

Within one operation:

```text
stdout
stderr
```

unless a contract explicitly requires another order.

---

## 19.11 Scan-log inclusion policy

`ALL_LOGS.TXT` should not embed the entire `ALL_SCAN_LOGS.TXT` by default.

It should include a reference section:

```text
SCAN LOGS
Aggregate: raw/ALL_SCAN_LOGS.TXT
Individual directory: raw/scan/
Sections: <count>
```

A diagnostic export command MAY create a separate fully self-contained bundle that embeds both.

That export must use another filename and role.

---

# 20. Aggregate section fidelity

Aggregate writers must copy source text without semantic rewriting.

Allowed aggregate-only transformations:

- normalize the terminal newline;
- add section boundary markers;
- render `<EMPTY STREAM>`;
- render `<MISSING EVIDENCE>`;
- escape section-boundary collision if required;
- normalize path display in metadata headers.

Not allowed:

- remove GF diagnostics;
- rewrite source filenames;
- reorder lines inside one source file;
- merge stdout and stderr line-by-line;
- strip linguistically meaningful Unicode;
- redact without recording redaction;
- replace the individual source file.

---

## 21. Section-boundary collision

A raw log may naturally contain text resembling an aggregate marker.

The aggregate format must remain unambiguous.

Recommended strategy:

- marker lines use a long fixed prefix;
- source content is length-delimited in metadata; or
- exact marker collisions are escaped in the aggregate only.

Example escape:

```text
\================================================================================
```

The individual raw log is unchanged.

A machine parser must not depend on aggregate sections unless the format becomes a formally versioned schema.

---

## 22. Log writing sequence

The canonical sequence is:

```text
create empty lifecycle and aggregate placeholders
→ append lifecycle events
→ execute operation
→ persist stdout/stderr immediately
→ record structured process result
→ append lifecycle completion event
→ repeat for all operations
→ write structured RunResult
→ write reports
→ append report-write warnings to master.log
→ finalize master.log
→ build ALL_SCAN_LOGS.TXT
→ build ALL_LOGS.TXT
→ compute manifest hashes
→ verify manifest
→ publish completion state
```

No aggregate should be generated before its source list is stable unless it is explicitly marked provisional.

---

## 23. Crash resilience

### 23.1 Primary logs

Primary stdout/stderr and scan logs should be persisted as soon as the operation completes or streams close.

### 23.2 Lifecycle log

`master.log` should be flushed at stage boundaries and after errors.

### 23.3 Aggregates

Aggregate generation may fail without destroying primary evidence.

### 23.4 Partial run

A partial run may contain:

```text
master.log
some individual logs
no aggregates
no manifest
```

This must be identifiable as incomplete.

Automation must not treat the directory as a completed successful run.

### 23.5 Recovery

A repair tool may rebuild aggregates and reports only when:

- source evidence is intact;
- structured result can be recovered;
- repair is explicitly requested;
- repaired artifacts are marked or recorded;
- manifest is regenerated.

It must not invent missing raw streams.

---

## 24. Atomicity

### 24.1 Individual process logs

For captured completed streams:

1. write temporary sibling file;
2. flush and close;
3. atomically replace canonical path.

For streaming capture, write to a temporary path and rename after stream completion.

### 24.2 Aggregate logs

Aggregates must use atomic replacement where supported.

### 24.3 Master log

Append semantics are acceptable during execution.

Canonicalization may copy the append file atomically to a finalized path only if no evidence is lost.

### 24.4 Failure

A failed rewrite must not replace the last complete aggregate with a partial file.

---

## 25. Concurrency

Parallel operations require isolated log files.

### 25.1 Required rules

- each operation writes a unique pair;
- shared aggregate files are not appended by worker processes;
- workers emit lifecycle events through a synchronized channel;
- aggregate ordering is independent of completion order;
- aggregate generation occurs after result ordering is known;
- master-log event sequence remains coherent.

### 25.2 Completion order

The master log may reflect real completion order.

Aggregates reflect canonical subject order.

This distinction is intentional.

---

## 26. Timestamps

### 26.1 Lifecycle timestamps

Use UTC RFC 3339.

### 26.2 Raw external streams

Do not prepend framework timestamps to captured tool lines.

### 26.3 Scan log timestamps

A scan log may contain:

```text
started_at
finished_at
duration_ms
```

in a metadata header.

### 26.4 Aggregate generation timestamp

Aggregate headers may record generation time.

This timestamp is metadata and may vary across a deliberate rebuild.

### 26.5 Reproducibility

Exact aggregate hashes may vary if generation timestamps vary.

For deterministic archival builds, use:

- run finalization timestamp; or
- omit aggregate generation timestamp from hashed content.

Canonical policy:

```text
Generated = run finished_at
```

This makes deterministic rebuilds possible.

---

## 27. Commands and environment in logs

### 27.1 Structured command

The exact executable and ordered arguments belong in structured process metadata.

### 27.2 Human-rendered command

`master.log` may include a safely rendered display command.

It must not be used to re-execute untrusted project content.

### 27.3 Environment overrides

Only relevant non-secret overrides may be logged.

Examples:

```text
locale
GF-specific path variable
temporary output directory
```

Do not log the full inherited environment.

### 27.4 Secret arguments

Before logging:

- identify secret-bearing options;
- redact their values;
- preserve an explicit `<REDACTED>` marker;
- keep the secret out of reports and aggregates.

GF Wordbench should avoid secret-bearing GF operations entirely.

---

## 28. Redaction

### 28.1 Raw-evidence principle

Raw evidence should be preserved locally whenever safe.

### 28.2 Required redaction

Redact:

- passwords;
- tokens;
- private keys;
- authentication cookies;
- secret environment values;
- explicitly configured sensitive paths when export policy requires it.

### 28.3 Redaction marker

Use:

```text
<REDACTED reason="<reason>">
```

### 28.4 Redaction record

When redaction occurs, record:

```text
artifact path
redaction policy
fields or patterns affected
whether local unredacted evidence exists
```

### 28.5 Export versus local run

The local run directory may retain diagnostic absolute paths.

A portable export may use redacted copies.

The export must not replace local authoritative evidence while claiming to be raw.

---

## 29. Output-size limits

Unbounded logs can exhaust disk or memory.

### 29.1 Operation-specific limits

Configurable limits should exist for:

```text
version probe
compile stdout
compile stderr
scenario stdout
scenario stderr
generation output
aggregate bundle
AI excerpt
```

### 29.2 Preferred behavior

Prefer:

1. bounded test commands;
2. streamed disk capture;
3. process termination on policy violation;
4. explicit truncation only as a last resort.

### 29.3 Truncation metadata

A truncated log must record outside the captured content:

```text
truncated = true
original_or_observed_bytes
retained_bytes
retention_strategy
reason
```

### 29.4 Aggregate marker

The aggregate may display:

```text
<TRUNCATED: retained 1048576 of at least 8388608 bytes>
```

### 29.5 Validation impact

Truncation is `ERROR` when removed content could affect:

- fatal-diagnostic detection;
- marker verification;
- gold comparison;
- required release evidence.

It may be a warning only for explicitly non-semantic verbose output.

---

## 30. Binary and non-text output

GF Wordbench log paths ending in `.txt` are text views.

If an external tool emits binary data to a captured stream:

- preserve bytes in a `.bin` or equivalent artifact;
- create a bounded diagnostic text view;
- record media type and decode status;
- do not place uncontrolled binary data into aggregate text files.

Adding a required binary-log artifact role must be documented in the manifest reference.

---

## 31. Duplicate output

GF or wrappers may emit the same diagnostic to stdout and stderr.

GF Wordbench must preserve both streams.

Diagnostic grouping may identify duplicates.

The aggregate must not silently remove duplicate raw lines.

A human report may state:

```text
same diagnostic observed in stdout and stderr
```

---

## 32. Line endings and terminal newline

### 32.1 Primary raw streams

Canonical persisted text uses LF.

If exact byte preservation is required, retain a byte artifact in addition to the normalized text view.

### 32.2 Aggregate logs

Use LF.

Every section and file ends with a newline.

### 32.3 Gold comparison

Scenario normalized `.out` follows its own versioned normalization rules.

Aggregate line-ending normalization does not alter the gold input file.

---

## 33. Log roles in `manifest.json`

Recommended manifest roles:

```text
master_log
version_stdout
version_stderr
scan_log
compile_stdout
compile_stderr
pgf_stdout
pgf_stderr
scenario_stdout
scenario_stderr
scenario_output
aggregate_scan_log
aggregate_operation_log
```

Each entry should include:

```text
path
role
media_type
required
size_bytes
sha256
created_by
```

### 33.1 Requiredness

Requiredness depends on mode and operation.

Examples:

- master log: required for all finalized runs;
- compile streams: required for each launched required compile;
- scenario streams: required for each launched required scenario;
- aggregates: required in checkpoint/release, configurable in quick mode;
- normalized scenario output: required when assertions or gold comparison use it.

### 33.2 Empty streams

An empty stream file is still included with:

```text
size_bytes = 0
sha256 = SHA-256 of empty bytes
```

---

## 34. References from `summary.json`

`summary.json` should reference logs through run-relative paths.

Examples:

```json
{
  "compile_summary": {
    "stdout_path": "raw/compile/GrammarFre.out.txt",
    "stderr_path": "raw/compile/GrammarFre.err.txt"
  },
  "scan_log_path": "raw/scan/GrammarFre.scan.txt"
}
```

Scenario results similarly reference:

```text
stdout_path
stderr_path
normalized_output_path
```

Readers must use these fields rather than reconstruct filenames.

---

## 35. References from human reports

Human reports should link or display:

- relevant individual raw logs;
- normalized scenario output;
- aggregate logs;
- manifest;
- summary JSON.

Reports should not inline unlimited raw content.

Recommended excerpt policy:

```text
bounded first-error context
bounded trailing context
explicit path to full log
```

The excerpt must state when it is truncated.

---

## 36. `details/` relationship

Detail reports are derived explanations.

They may contain:

- subject identity;
- status;
- diagnostic class;
- error kind;
- first error;
- blockers;
- scan counts;
- bounded stdout/stderr excerpts;
- raw evidence paths.

They must not be placed under `raw/`.

They must not be embedded by default in `ALL_LOGS.TXT`.

---

## 37. `top_errors.txt` relationship

`top_errors.txt` is a report.

It is not a raw log.

It contains grouped diagnostic summaries.

It must not be treated as proof that an individual operation emitted a message.

The authoritative source remains the individual result and raw evidence.

---

## 38. `AI_READY.md` relationship

`AI_READY.md` is a bounded handoff report.

It may refer to:

```text
raw/master.log
raw/ALL_SCAN_LOGS.TXT
raw/ALL_LOGS.TXT
individual evidence paths
```

It must not be copied into `ALL_LOGS.TXT`.

This prevents recursive or stale evidence packets.

---

## 39. `summary.md` and `summary.json` relationship

`summary.json` is the machine source.

`summary.md` is a human view.

Neither belongs inside canonical `ALL_LOGS.TXT`.

The aggregate header may reference their relative paths.

---

## 40. Missing-log behavior

A missing log must be evaluated against whether the corresponding operation:

```text
was not selected
was intentionally skipped
was blocked
failed to launch
launched and produced an empty stream
launched but capture failed
completed and the file was later lost
```

These cases are distinct.

### 40.1 Not selected

No log required.

### 40.2 Intentionally skipped

No stream required, but structured `SKIPPED` result required.

### 40.3 Blocked

No stream required if process never launched.

`blocked_by` must be recorded.

### 40.4 Launch failed

Stream files may be empty or absent according to process-runner contract.

Launch error metadata is required.

### 40.5 Empty stream

File required and empty.

### 40.6 Capture failed

Validation `ERROR`.

### 40.7 File lost after capture

Artifact-integrity `ERROR`.

---

## 41. Log integrity

### 41.1 Hashing

Finalized logs are hashed with SHA-256 in the manifest.

### 41.2 Modification

A hash mismatch after finalization indicates:

- corruption;
- manual modification;
- incomplete archive;
- unauthorized rewrite.

### 41.3 Repair

A repair operation must:

- preserve the damaged original when possible;
- record the repair;
- regenerate derived aggregates only from verified sources;
- never reconstruct missing primary streams from aggregates;
- regenerate manifest hashes.

---

## 42. Retention

Run retention policy is defined in:

```text
docs/operations/RUN_DIRECTORY_LIFECYCLE.md
```

Raw-log reference rules:

- deleting an individual log makes the run incomplete for that evidence;
- aggregate logs may be deleted and regenerated before archival finalization;
- after archival, manifest and retained-file policy must agree;
- release evidence should retain all required primary logs;
- quick-run retention may be shorter;
- secret-bearing runs require controlled storage.

---

## 43. Compression and archives

A run may be archived after finalization.

Archive rules:

- preserve relative paths;
- preserve UTF-8 bytes;
- preserve zero-byte files;
- include `manifest.json`;
- verify hashes before and after archive creation;
- do not replace logs with only aggregate bundles;
- document compression format and tool.

Compressed logs inside the live run directory are not canonical unless explicitly added to the schema.

---

## 44. Human reading workflow

Recommended order:

1. `summary.md`;
2. `AI_READY.md`;
3. `top_errors.txt`;
4. relevant individual raw log;
5. `ALL_LOGS.TXT` for broad context;
6. `ALL_SCAN_LOGS.TXT` for scan-wide review;
7. `manifest.json` for integrity.

For root-cause work, inspect individual direct-failure logs before downstream logs.

---

## 45. AI-assisted workflow

Recommended packet:

```text
AI_READY.md
summary.json
selected individual raw logs
optional ALL_LOGS.TXT
optional ALL_SCAN_LOGS.TXT
```

Do not provide only `ALL_LOGS.TXT` when structured result context is available.

An AI system should be instructed that:

- aggregate sections are copies;
- individual paths are authoritative;
- scan findings are not GF compiler truth;
- downstream failures are not independent root causes;
- missing evidence must not be guessed.

---

## 46. Automation workflow

Automation must consume:

```text
summary.json
manifest.json
```

Automation may use raw logs for:

- artifact upload;
- diagnostic excerpts;
- audit trails;
- failure attachments.

Automation must not determine run success by searching `ALL_LOGS.TXT` for words such as:

```text
error
failed
timeout
```

Structured statuses govern.

---

## 47. Legacy GF Audit migration

The earlier implementation may use:

```text
raw/logs/compile/
raw/logs/scan/
raw/artifacts/gfo/
raw/artifacts/out/
```

and may create aggregate files by copying reports and detail artifacts.

The canonical layout is:

```text
raw/compile/
raw/scan/
raw/scenarios/
artifacts/gfo/
artifacts/out/
artifacts/pgf/
```

### 47.1 Legacy path handling

Legacy summary readers may retain old paths.

Canonical writers must use canonical paths.

Migration may:

- recognize old paths;
- convert them to canonical run-relative references when files are moved;
- leave historical runs unchanged;
- avoid claiming that old aggregates satisfy the canonical aggregate contract.

### 47.2 Legacy `master.log`

Legacy local-time timestamps remain valid historical evidence.

They are not rewritten as UTC unless the original timezone is known.

### 47.3 Legacy `ALL_LOGS.TXT`

Historical bundles may contain reports.

Readers should treat them as legacy aggregates.

New writers must use the optimized operational-only composition.

### 47.4 Legacy top-error format

Legacy top-error content remains a report and is not promoted to raw evidence.

---

## 48. Component ownership

| Responsibility | Owner component |
|---|---|
| lifecycle event model | `app/audit/audit_core.py` or logging service |
| process stream capture | `app/utils/process_utils.py` |
| compile stream paths | `app/audit/compiler.py` / `RunPaths` |
| scan log creation | `app/audit/scanner.py` |
| scenario stream paths | `app/audit/scenario_runner.py` |
| normalized scenario output | `app/audit/normalization.py` |
| aggregate generation | `app/reports/report_logs.py` |
| atomic text IO | `app/utils/io_utils.py` |
| path containment | `app/utils/path_utils.py` |
| manifest hashing | manifest writer |
| report evidence links | `app/reports/` |

`report_logs.py` must not execute GF or rerun scans.

---

## 49. Conceptual writer APIs

Conceptual APIs:

```python
write_master_event(event: LifecycleEvent) -> None
write_stream_capture(result: ProcessCapture) -> StreamPaths
write_scan_log(result: ScanResult) -> Path
write_all_scan_logs(run_result: RunResult) -> Path
write_all_logs(run_result: RunResult) -> Path
verify_log_artifacts(run_result: RunResult) -> list[ArtifactCheck]
```

These signatures are illustrative.

Actual public signatures remain governed by the interfile contract lock.

---

## 50. Testing requirements

Recommended tests:

```text
tests/reports/test_master_log.py
tests/reports/test_raw_stream_logs.py
tests/reports/test_scan_logs.py
tests/reports/test_all_scan_logs.py
tests/reports/test_all_logs.py
tests/reports/test_log_redaction.py
tests/reports/test_log_truncation.py
tests/reports/test_log_manifest.py
tests/reports/test_log_migration.py
```

### 50.1 Master-log tests

- UTC timestamp;
- stable level/event format;
- path with spaces;
- Unicode value;
- newline escaping;
- append preserves prior events;
- fatal append;
- no secrets;
- deterministic event field rendering.

### 50.2 Stream-log tests

- stdout only;
- stderr only;
- both empty;
- non-zero exit;
- timeout with partial output;
- launch failure;
- invalid UTF-8;
- zero-byte file hash;
- retry isolation;
- path collision.

### 50.3 Scan-log tests

- no findings;
- multiple findings;
- scanner error;
- Unicode excerpt;
- bounded excerpt;
- deterministic rule order.

### 50.4 Aggregate tests

- deterministic section order;
- exact copied source content;
- empty stream marker;
- missing evidence marker;
- no embedded summary JSON;
- no embedded AI report;
- scan aggregate referenced, not duplicated;
- marker collision handling;
- atomic replacement;
- terminal newline;
- Windows and POSIX paths.

### 50.5 Manifest tests

- every required log registered;
- size and SHA-256 match;
- zero-byte stream included;
- aggregate role correct;
- modified file detected;
- missing required log fails;
- manifest excludes itself from hashing.

### 50.6 Crash tests

- interruption before aggregates;
- interruption during aggregate temp write;
- partial master log;
- finalization recovery;
- no partial canonical aggregate replacement.

---

## 51. Drift indicators

Raw-log drift likely exists when:

- stdout and stderr are merged into one primary file;
- a report overwrites a raw log;
- `ALL_LOGS.TXT` becomes the only copy of evidence;
- `summary.json` is embedded into the canonical aggregate;
- CLI and GUI use different raw directories;
- one component invents log filenames instead of reading `RunPaths`;
- logs move back under `raw/logs/` without schema migration;
- PGF logs have no distinct operation identity;
- a timeout message is inserted into captured GF stderr as though GF emitted it;
- empty stream files are omitted after a launched operation;
- a missing file is treated as an empty stream;
- aggregate order depends on filesystem enumeration;
- parallel workers append directly to aggregate files;
- local timestamps are assigned during report-time rewrite;
- invalid bytes are silently dropped;
- truncation is not recorded;
- redaction is invisible;
- aggregate content differs from its source without explanation;
- a report parser treats `ALL_LOGS.TXT` as the machine source;
- manifest hashes are computed before all log writes complete.

Any drift indicator requires contract and test review.

---

## 52. Change workflow

A raw-log contract change is complete only when:

```text
[ ] Artifact role identified
[ ] Writer identified
[ ] Readers identified
[ ] Canonical path reviewed
[ ] Persisted schema reviewed
[ ] RunPaths reviewed
[ ] Encoding reviewed
[ ] Newline policy reviewed
[ ] Ordering reviewed
[ ] Security/redaction reviewed
[ ] Truncation behavior reviewed
[ ] Aggregate composition reviewed
[ ] Manifest role reviewed
[ ] Migration behavior reviewed
[ ] Unit tests updated
[ ] Integration tests updated
[ ] Documentation updated
[ ] Contract locks updated when required
```

Examples of contract changes:

- renaming `master.log`;
- moving compile logs;
- adding `raw/pgf/`;
- changing aggregate composition;
- changing lifecycle timestamp format;
- adding a binary evidence artifact;
- making an aggregate required;
- changing truncation semantics;
- changing redaction policy;
- adding a machine parser for aggregate sections.

No such change may be implemented in one file only.

---

## 53. Canonical quick reference

### Primary lifecycle log

```text
raw/master.log
```

### Version probe

```text
raw/gf_version.out.txt
raw/gf_version.err.txt
```

### File/module compilation

```text
raw/compile/<subject-key>.out.txt
raw/compile/<subject-key>.err.txt
```

### PGF build

```text
raw/compile/pgf__<target-key>.out.txt
raw/compile/pgf__<target-key>.err.txt
```

### Static scan

```text
raw/scan/<subject-key>.scan.txt
```

### Scenario process output

```text
raw/scenarios/<scenario-id>.out.txt
raw/scenarios/<scenario-id>.err.txt
```

### Scenario normalized output

```text
raw/scenarios/<scenario-id>.out
```

### Scan aggregate

```text
raw/ALL_SCAN_LOGS.TXT
```

### Operational aggregate

```text
raw/ALL_LOGS.TXT
```

### Machine result

```text
summary.json
```

### Integrity record

```text
manifest.json
```

---

## 54. Core rule

Raw logs exist to preserve what actually happened.

> GF Wordbench must capture each operation separately, retain empty and partial streams faithfully, keep framework messages outside tool output, generate aggregates only as reproducible views, and make every report conclusion traceable to individual evidence files.

`ALL_LOGS.TXT` is useful because it gathers evidence.

It is not authoritative because it copies evidence.

`summary.json` explains the structured result.

`manifest.json` proves artifact integrity.

The individual files under `raw/` remain the primary record of execution.
