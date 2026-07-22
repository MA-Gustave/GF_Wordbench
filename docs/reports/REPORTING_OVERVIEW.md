# GF Wordbench — Reporting Overview

**Document ID:** `GF-WB-REPORTING-OVERVIEW`  
**Status:** Normative reporting architecture  
**Applies to:** Every completed or terminal GF Wordbench run  
**Primary owners:** `app/reports/` and the run orchestrator  
**Reporting model version:** `1.0`  
**Target product state:** Final architecture  
**Last reviewed:** 2026-07-22  

---

## 1. Purpose

This document defines the final reporting system for GF Wordbench.

It explains:

- which reports exist;
- which report is authoritative for each use;
- which component owns each artifact;
- what information report writers may consume;
- how report writers are ordered;
- how report failures are handled;
- how paths, timestamps, statuses, diagnostics, and artifacts are presented;
- how reports remain deterministic and safe;
- how current GF Audit reporting migrates to GF Wordbench.

The reporting system converts one completed validation result into durable, reviewable evidence.

It must not perform a second validation.

---

## 2. Core rule

> Reports describe completed evidence; they do not create, repair, reinterpret, or rerun that evidence.

A report writer may:

- serialize structured results;
- select and order existing facts;
- render human-readable explanations;
- copy or aggregate existing logs when it owns the destination;
- calculate presentation-only summaries from `RunResult`;
- catalog completed artifacts.

A report writer must not:

- launch GF;
- rerun a scanner;
- rerun a scenario;
- rebuild a PGF;
- change a validation status;
- assign direct or downstream causality;
- normalize scenario output independently;
- update a `.gold` file;
- infer missing machine fields from another human report;
- rewrite raw evidence owned by another component.

---

## 3. Related authority

The following documents remain authoritative for their domains:

```text
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/SUMMARY_MARKDOWN_REFERENCE.md
docs/reports/AI_READY_REFERENCE.md
docs/reports/RAW_LOGS_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
docs/reference/STATUS_VALUES.md
docs/reference/DIAGNOSTIC_KINDS.md
```

Priority when rules overlap:

1. `PERSISTED_SCHEMA_LOCK.md` governs machine schemas, path bases, versions, and stable report identities;
2. `INTERFILE_CONTRACT_LOCK.md` governs Python provider-consumer boundaries and artifact ownership;
3. `ARTIFACT_MODEL.md` governs artifact classes and lifecycle;
4. this document governs the overall reporting architecture;
5. each report-specific reference governs that report’s detailed layout.

---

## 4. Reporting goals

The final reporting system must provide:

### 4.1 Machine usability

Automation must be able to load one versioned structured run record without parsing Markdown.

### 4.2 Human review

A developer must be able to understand the outcome quickly without opening every raw log.

### 4.3 AI handoff

An AI system must receive bounded, explicit evidence without requiring a second run.

### 4.4 Traceability

Every important claim must be traceable to structured results or owned evidence paths.

### 4.5 Reproducibility

Reports must identify the run, project, GF version, mode, configuration, timestamps, and artifacts needed to understand the execution context.

### 4.6 Anti-drift

Each report has one writer, one stable purpose, and no competing source of truth.

### 4.7 Failure preservation

A report failure must not destroy validation evidence already captured.

---

## 5. Reporting non-goals

The core reporting system is not:

- a database;
- a telemetry service;
- a remote dashboard;
- a log-shipping platform;
- a general analytics engine;
- a replacement for version control;
- a replacement for GF diagnostics;
- a replacement for project documentation;
- a live process monitor;
- an HTML publishing system;
- an unrestricted report-plugin framework.

Additional export formats may be introduced through explicit contracts, but they must not weaken the canonical reports.

---

## 6. Report families

GF Wordbench produces four report families.

### 6.1 Canonical machine record

```text
summary.json
```

### 6.2 Canonical human reports

```text
summary.md
AI_READY.md
top_errors.txt
```

### 6.3 Evidence and detail artifacts

```text
master.log
ALL_SCAN_LOGS.TXT
ALL_LOGS.TXT
details/
raw/
```

### 6.4 Artifact integrity record

```text
manifest.json
```

These families have different purposes.

No family should be forced to serve all audiences.

---

## 7. Canonical run layout

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

The schema lock defines the canonical path contract.

A report writer must obtain its path from `RunPaths` or the designated artifact-path owner.

It must not reconstruct the same filename independently.

---

## 8. Source-of-truth hierarchy

The source hierarchy is:

```text
raw tool and scan evidence
        ↓
structured stage results
        ↓
RunResult
        ↓
summary.json
        ↓
human reports and external consumers
```

Clarifications:

- raw evidence is authoritative for what the external tool emitted;
- structured results are authoritative for GF Wordbench’s normalized interpretation;
- `RunResult` is authoritative during the current process;
- `summary.json` is authoritative after persistence;
- Markdown reports are authoritative only as human presentations of those facts;
- `manifest.json` is authoritative for final artifact inventory and integrity metadata.

A human report must not become the input used to reconstruct `RunResult`.

---

## 9. Primary machine-readable report

Canonical path:

```text
summary.json
```

Canonical schema:

```text
schema_id: gf-wordbench.run-summary
schema_version: 1.0
```

Primary owner:

```text
app/reports/report_json.py
```

Primary public symbol:

```python
write_summary_json(run_result: RunResult) -> Path
```

Detailed field definitions belong to:

```text
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/PERSISTED_SCHEMA_LOCK.md
```

---

## 10. `summary.json` responsibilities

`summary.json` must preserve enough structured information for:

- previous-run comparison;
- GUI result loading;
- CLI or automation inspection;
- release-gate verification;
- historical analysis;
- migration;
- report verification;
- AI handoff metadata;
- artifact discovery;
- diagnostic aggregation.

It normally includes:

```text
schema identity
producer identity
run metadata
resolved execution context
overall status
totals
artifact paths
file results
scenario results
PGF or entrypoint results when applicable
diff entries
top errors
release-gate outcomes
framework errors
```

The exact canonical shape is governed by the schema lock.

---

## 11. `summary.json` restrictions

The JSON writer must not:

- serialize arbitrary object internals through uncontrolled recursion;
- depend on Python object field order as semantic order;
- write unversioned canonical output;
- emit absolute project paths where project-relative paths are required;
- emit Windows-only separators in canonical project or run-relative paths;
- serialize enum objects directly;
- serialize timestamps without timezone semantics;
- emit `NaN` or infinity;
- silently rename legacy fields into canonical output without migration rules;
- copy unknown legacy fields into a new canonical document;
- use Markdown prose as a source.

Serialization must be deliberate and schema-owned.

---

## 12. Human summary

Canonical path:

```text
summary.md
```

Owner:

```text
app/reports/report_md.py
```

Primary public symbols:

```python
build_summary_md(run_result: RunResult) -> str
write_summary_md(run_result: RunResult) -> Path
```

Purpose:

- provide a concise but complete human review of the run;
- expose outcome, totals, root failures, downstream failures, scenarios, changes, and artifact links;
- help a developer decide what to inspect next.

It is not a machine schema.

---

## 13. Human-summary minimum content

The final human summary should cover, when applicable:

```text
Run
Outcome
Totals
Release gates
Direct failures
Downstream failures
Ambiguous failures
Framework errors
Failing scenarios
Successful validation
Skipped validation
Top errors
Heuristic scan notes
Changes since previous run
Artifacts and evidence
```

Empty sections may be omitted when the report-specific reference permits it.

The top-level outcome must remain visible near the beginning.

---

## 14. Human-summary ordering

Recommended failure order:

```text
framework errors
direct failures
required scenario failures
ambiguous failures
downstream failures
warnings and scan notes
```

Within stable groups:

- file results use normalized project-relative path order;
- scenario results use declared scenario order;
- diagnostics use severity and stable subject order;
- diff entries use change severity, then subject identity;
- artifacts use normalized path order.

Report order must not depend on filesystem enumeration.

---

## 15. AI handoff report

Canonical path:

```text
AI_READY.md
```

Owner:

```text
app/reports/report_ai_ready.py
```

Primary public symbol:

```python
write_ai_ready(run_result: RunResult) -> Path
```

Required first heading:

```text
# AI Ready Packet
```

Purpose:

- provide a bounded self-contained handoff;
- foreground likely root failures;
- distinguish direct, downstream, and ambiguous failures;
- include failing scenarios;
- include relevant excerpts and artifact paths;
- avoid requiring the AI system to rerun GF.

---

## 16. AI handoff minimum sections

When applicable:

```text
Run Summary
Outcome
Diagnosis Snapshot
Failing Files
Failing Scenarios
Evidence
Artifacts
```

Optional sections may include:

```text
Changes Since Previous Run
Heuristic Scan Notes
Suggested Investigation Order
Known Limitations of This Packet
```

A suggested investigation order must be derived from structured classification, not invented linguistic advice.

---

## 17. AI handoff evidence policy

The AI packet may inline bounded evidence from:

- primary diagnostic messages;
- diagnostic details;
- compiler stdout/stderr excerpts;
- scenario stdout/stderr excerpts;
- gold diffs;
- scan findings;
- blocker relationships.

Rules:

- raw artifact paths remain visible;
- excerpts are bounded;
- truncation is explicit;
- no unsupported diagnosis is added;
- no secret values are included;
- complete large logs are referenced instead of copied;
- downstream failures are not presented as independent root causes;
- missing evidence is stated honestly.

The packet must not silently rewrite evidence for narrative convenience.

---

## 18. Top-error report

Canonical path:

```text
top_errors.txt
```

Owner:

```text
app/reports/report_logs.py
```

Primary public symbol:

```python
write_top_errors(run_result: RunResult) -> Path
```

Canonical line format:

```text
<count>\t<error-kind>\t<message>
```

Example:

```text
3	TYPE	type mismatch
```

Purpose:

- provide a compact deterministic error-frequency index;
- support quick review and simple tooling;
- avoid opening the entire summary.

---

## 19. Top-error aggregation

Recommended aggregation key:

```text
error kind + normalized primary message
```

Rules:

- counts are positive integers;
- embedded tabs and newlines in messages become spaces;
- messages are not reduced to an empty value;
- distinct error kinds are not merged merely because text matches;
- order is descending count, then case-insensitive message;
- an empty file is valid when no errors exist;
- the file uses UTF-8, LF, and a final newline.

Detailed diagnostic identity remains in `summary.json`.

---

## 20. Artifact manifest

Canonical path:

```text
manifest.json
```

Owner:

```text
app/reports/report_manifest.py
```

or the final designated manifest writer.

Canonical schema:

```text
schema_id: gf-wordbench.artifact-manifest
schema_version: 1.0
```

Purpose:

- list finalized run artifacts;
- identify each artifact’s role and owner;
- record required/optional status;
- record size and SHA-256;
- support verification, cleanup, export, and release evidence.

Detailed fields belong to:

```text
docs/reports/ARTIFACT_MANIFEST.md
docs/PERSISTED_SCHEMA_LOCK.md
```

---

## 21. Manifest timing

The manifest is written after all other final artifact writers have completed or failed.

It must describe actual final state.

The manifest writer must not:

- claim an absent artifact exists;
- hash a file before its final write completes;
- modify a file to make its hash match;
- catalog temporary files as final artifacts;
- conceal required missing artifacts.

If the manifest catalogs itself, its self-entry must follow the explicit manifest schema policy. A recursive self-hash must not be invented.

---

## 22. Raw logs

Canonical raw logs include:

```text
raw/master.log
raw/ALL_SCAN_LOGS.TXT
raw/ALL_LOGS.TXT
raw/compile/
raw/scan/
raw/scenarios/
```

Raw-log responsibilities are divided:

- compiler owns per-operation compile streams;
- scanner owns per-file scan logs;
- scenario runner owns scenario streams and normalized scenario output;
- orchestration/log owner owns `master.log`;
- report/log aggregation owner owns aggregate views.

An aggregate log is derived evidence.

It must not replace the original files.

---

## 23. Master log

Canonical path:

```text
raw/master.log
```

Purpose:

- provide chronological orchestration evidence;
- record stage starts and completions;
- record report-generation warnings;
- record terminal run context;
- aid investigation of framework failures.

The master log is not the primary machine result.

It must not be parsed as the canonical run schema.

---

## 24. Aggregate logs

Canonical aggregate views:

```text
raw/ALL_SCAN_LOGS.TXT
raw/ALL_LOGS.TXT
```

Purpose:

- provide convenient combined evidence;
- preserve source section boundaries;
- support manual and AI review.

Each section should identify:

```text
artifact role
source subject
source path
content
```

Aggregate logs must:

- use deterministic source ordering;
- preserve original source files;
- identify missing referenced sources;
- bound content only under an explicit recorded policy;
- avoid ambiguous concatenation.

---

## 25. Detail files

Canonical destination:

```text
details/
```

Owner:

```text
app/reports/report_details.py
```

Purpose:

- gather focused evidence for failed or selected subjects;
- reduce navigation across many raw directories;
- provide per-file or per-scenario review packets.

Detail files are derived artifacts.

They may copy existing evidence but must not alter the original evidence.

---

## 26. Detail retention

Detail-retention policy may depend on:

```text
failure status
diagnostic class
scenario failure
explicit keep-all option
release evidence requirements
```

A successful subject may omit duplicated detail output when:

- raw evidence remains available;
- the omission is documented;
- summary and manifest paths remain correct.

Retention policy must not alter validation results.

---

## 27. Report writer architecture

Recommended final report modules:

```text
app/reports/
├── __init__.py
├── report_json.py
├── report_md.py
├── report_ai_ready.py
├── report_logs.py
├── report_details.py
└── report_manifest.py
```

A separate coordinator module may be introduced only if orchestration logic becomes substantial:

```text
app/reports/report_coordinator.py
```

The audit orchestrator may also remain the coordinator when the logic is small and explicit.

No general report-plugin registry is required.

---

## 28. Shared report facade

`app/reports/__init__.py` may export the stable public report functions.

Expected public exports:

```python
write_summary_json
write_summary_md
write_ai_ready
write_top_errors
write_master_log
write_all_scan_logs
write_all_logs
write_file_detail_logs
write_manifest
```

Private formatting helpers must remain private.

Consumers must not import private helpers from another report module.

---

## 29. Report inputs

Canonical report input:

```text
RunResult
```

Additional allowed inputs are narrowly owned:

- `master_log_lines` for the master-log writer;
- explicit artifact records for the manifest writer;
- report-generation warnings collected by the coordinator;
- schema producer metadata from application configuration.

Report writers should not independently reload project configuration or application state.

All execution-relevant facts must already be resolved.

---

## 30. Required `RunResult` domains

Reporting may depend on documented fields for:

```text
run configuration
run paths
overall status
timestamps
duration
GF version
project identity
validation mode
file results
scenario results
entrypoint or PGF results
totals
diagnostic groups
top errors
diff entries
release gates
artifact records
framework errors
```

A report that needs a missing cross-component field must request a model change.

It must not attach dynamic attributes or recover the value from prose.

---

## 31. Report purity

A report builder should behave like:

```text
structured input
        → deterministic text or JSON value
```

Allowed side effect for a writer:

```text
write only its owned artifact
```

A pure build function is preferred where useful:

```python
build_summary_md(run_result) -> str
build_ai_ready(run_result) -> str
build_summary_document(run_result) -> dict
```

The build function supports testing without filesystem writes.

---

## 32. Report-generation dependency graph

```text
RunResult
 ├── top_errors.txt
 ├── summary.md
 ├── AI_READY.md
 ├── details/
 ├── aggregate logs
 └── summary.json

all finalized artifacts
        ↓
manifest.json
```

No canonical report depends on parsing another human-facing report.

Permitted dependency:

- `AI_READY.md` may use structured fields also rendered in `summary.md`;
- it should not read `summary.md` to recover them.

---

## 33. Report-generation lifecycle

Recommended lifecycle:

```text
1. finalize stage evidence
2. finalize RunResult
3. finalize master-log content available so far
4. write detail and aggregate evidence
5. write top_errors.txt
6. write summary.md
7. write AI_READY.md
8. write summary.json
9. write manifest.json
10. append or finalize report warnings in master.log
11. verify required outputs
```

The exact internal order may change when dependencies require it.

Locked ordering rules:

- writers consume a finalized validation result;
- `manifest.json` is written after the artifacts it catalogs;
- no report writer reruns validation;
- missing report artifacts remain visible;
- required release evidence is verified before release success.

---

## 34. Finalization and immutability

`RunResult` should be logically finalized before report generation.

Report writers must not mutate:

- file status;
- scenario status;
- diagnostic class;
- blocker lists;
- counts;
- diff entries;
- release-gate results;
- raw artifact paths.

Presentation-only local values may be computed without modifying the model.

If a report writer discovers an invalid model invariant, it should fail explicitly rather than repair the result silently.

---

## 35. Report write results

The coordinator should track each write attempt with minimal structured facts:

```text
report ID
target path
required flag
success flag
error kind
error message
```

This may remain an internal model unless persisted-schema requirements add it to `summary.json` or `manifest.json`.

The system does not need a complex report job engine.

A simple ordered collection of report write outcomes is sufficient.

---

## 36. Report failure semantics

A report write failure is a framework reporting error.

It is not:

- a GF syntax failure;
- a type error;
- a scenario failure;
- a gold mismatch;
- a downstream language failure.

The original validation outcome remains available.

However, release success may be blocked when a required report or integrity artifact is missing.

---

## 37. Required versus optional reports

Final required reports for a normal completed run:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
master.log
```

Required raw stage evidence depends on the stages executed.

Detail and aggregate artifacts may be optional by policy, except where release criteria require them.

A release run must satisfy its required artifact manifest.

---

## 38. Best-effort recovery

When the run terminates through a framework exception after the run directory exists, GF Wordbench should attempt to write a bounded terminal evidence set:

```text
master.log
summary.json
summary.md
AI_READY.md
manifest.json when possible
```

The recovered reports must state:

- terminal framework error;
- completed evidence retained;
- incomplete stages;
- unavailable reports;
- no unsupported success claim.

Best-effort writing must not hide its own failures.

---

## 39. Failure isolation

One report writer should not prevent all remaining independent writers from being attempted.

Example:

```text
summary.md write fails
AI_READY.md may still be attempted
summary.json may still be attempted
manifest records actual presence
master.log records warnings
```

Dependencies must still be respected.

The manifest cannot accurately catalog a report that has not finished.

---

## 40. Overall status and reporting failure

Recommended run semantics:

- validation `OK` plus missing required report → overall `ERROR` or release gate failure;
- validation `FAIL` plus report failure → validation remains `FAIL`, with additional framework reporting error;
- validation `ERROR` plus report failure → retain both errors;
- optional report failure → warning unless project or mode makes it required.

The centralized error-handling model owns the final status-combination rule.

Reports themselves do not calculate the overall status.

---

## 41. Atomic-write policy

Canonical machine and stable human reports should use atomic replacement where supported.

Required candidates:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
```

Recommended process:

1. write a sibling temporary file;
2. flush and close it;
3. validate the generated content;
4. replace the destination atomically.

A failed write must not destroy a previously valid destination.

Streaming raw logs are exempt from final atomic replacement during capture.

---

## 42. Encoding and newlines

Canonical report encoding:

```text
UTF-8 without BOM
```

Canonical newline:

```text
LF
```

A final newline is required for:

```text
summary.md
AI_READY.md
top_errors.txt
master.log
aggregate text logs
detail text reports
```

JSON must be valid UTF-8 and end consistently according to the JSON writer policy.

Readers may accept CRLF for legacy compatibility.

---

## 43. Deterministic serialization

Determinism requirements include:

- stable subject ordering;
- stable artifact ordering;
- stable top-error ordering;
- stable section order;
- stable JSON indentation;
- stable Unicode emission;
- no set iteration without sorting;
- no dependence on dictionary insertion created from filesystem order;
- no locale-dependent sorting;
- no local-time ambiguity.

Timestamps and durations are expected to vary between runs.

---

## 44. Path rendering

Paths are classified as:

```text
project-relative
run-relative
environment-specific
```

Reports must preserve the correct base.

### Project-relative

Examples:

```text
lib/src/language/GrammarX.gf
validation/scenarios/parse.gfs
```

### Run-relative

Examples:

```text
raw/compile/GrammarX.stdout.txt
artifacts/pgf/Grammar.pgf
```

### Environment-specific

Examples:

```text
C:/tools/gf/gf.exe
C:/work/gf-rgl/src
```

Canonical persisted separators use `/`.

Human reports may show environment paths when needed for diagnosis.

---

## 45. Path safety

Report writers must not:

- follow a diagnostic-mentioned path outside allowed roots without validation;
- copy arbitrary files into `details/`;
- resolve `..` outside the run root;
- overwrite source or gold assets;
- create report files outside the active run directory;
- infer a path by concatenating untrusted subject text.

Safe artifact names must use the shared path utility.

---

## 46. Timestamp policy

Canonical persisted timestamps use RFC 3339-compatible UTC text.

Example:

```text
2026-07-22T18:25:43Z
```

Human reports may show the same UTC time.

Local time may be added only as secondary display text with an explicit timezone.

Naive timestamps are prohibited in canonical machine reports.

Durations use integer milliseconds.

---

## 47. Status rendering

Canonical validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

Canonical diagnostic classes:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Canonical execution states:

```text
completed
timed_out
cancelled
launch_failed
```

Reports must keep these dimensions separate.

A report must not label every non-zero exit as direct.

---

## 48. Failure grouping

Human and AI reports should group failures by causal usefulness.

Recommended groups:

```text
framework errors
direct language failures
required scenario failures
ambiguous failures
downstream failures
warnings/noise
```

`blocked_by` relationships should be shown for downstream subjects.

The same subject should not appear as an independent root failure and as downstream without explicit explanation.

---

## 49. Diagnostic rendering

For each significant failure, reports may show:

```text
subject
status
diagnostic class
error kind
primary message
pattern ID when available
blocked_by
raw evidence paths
detail path
```

A human report may omit empty fields.

It must not change normalized diagnostic meaning.

---

## 50. Scan-result rendering

Static scan findings are separate from GF execution diagnostics.

Reports should label them as:

```text
heuristic scan findings
```

They must not present scan findings as authoritative GF type or syntax errors.

A file may be:

```text
compile OK
scan findings present
```

This state must remain representable.

---

## 51. Scenario rendering

Scenario reports should show:

```text
scenario ID
required or optional
status
execution state
duration
primary message
failed sections or assertions
gold result
blocked_by
raw stdout/stderr
normalized output
gold diff
produced artifacts
```

Scenario order follows project configuration.

Reports must not reparse markers or recompute gold comparison.

---

## 52. Release-gate rendering

Release reports should show each required gate:

```text
gate ID
status
criterion
evidence
blocking subjects
```

The final release decision must be explicit.

Example:

```text
Release readiness: FAIL
```

It must not be inferred only from file compile totals.

---

## 53. Regression rendering

Previous-run comparison uses structured diff entries.

Canonical change kinds:

```text
regressed
new
improved
removed
unchanged
```

Recommended report order:

```text
regressed
new
improved
removed
unchanged
```

A report must not compare Markdown text to determine these changes.

---

## 54. Artifact links

Human reports should use relative artifact paths where practical.

Benefits:

- portability;
- clone-independent review;
- archive compatibility;
- shorter text;
- safer AI handoff.

A report may show an environment path when the artifact is external and cannot be represented run-relatively.

The manifest remains the canonical artifact inventory.

---

## 55. Secret and privacy policy

Reports must not contain:

- passwords;
- access tokens;
- private keys;
- cookies;
- complete environment dumps;
- secret command arguments;
- unrestricted user-home inventories;
- unrelated file contents.

Command and environment evidence must use redaction declared by the process request.

Local absolute paths are not automatically secrets, but export tooling may redact them.

Redaction must not change the stored raw GF output unless the raw output itself contains a secret and an explicit secure-handling policy applies.

---

## 56. Output-size policy

Reports must remain bounded.

Recommended controls:

- limit inlined raw excerpts;
- limit repeated downstream failures in AI summaries while preserving full structured results;
- reference full logs;
- cap per-subject excerpt size;
- make truncation explicit;
- avoid embedding complete PGF or GFO binary content;
- avoid copying full aggregate logs into Markdown.

`summary.json` must still retain complete structured records required by its schema.

---

## 57. Large-run behavior

For large projects:

- `summary.md` remains a summary;
- `AI_READY.md` foregrounds root failures and bounded evidence;
- `top_errors.txt` remains compact;
- full file and scenario results remain in `summary.json`;
- raw evidence remains in owned directories;
- manifest lists all final artifacts.

Pagination is a presentation concern for GUI or external tooling.

The persisted schema should not be split into undocumented fragments solely because a run is large.

---

## 58. Empty-run behavior

A run with no included validation subjects must not be presented as a normal successful release.

Reports should state:

```text
No validation subjects were included.
```

The overall status follows validation-mode policy.

Reports must still be valid and loadable when the run terminates cleanly with an empty selection.

---

## 59. Partial-run behavior

A partial run may contain:

- completed file results;
- incomplete later stages;
- terminal framework error;
- cancelled scenario;
- missing final PGF;
- report warnings.

Reports must:

- preserve completed facts;
- identify incomplete stages;
- avoid treating absent results as passed;
- distinguish skipped from not reached;
- identify terminal cause.

---

## 60. Legacy compatibility

GF Wordbench must read documented legacy GF Audit summaries during migration.

Legacy elements may include:

```text
unversioned summary.json
flat summary shape
nested unversioned summary shape
ai_brief_path
ai_ready_path alias
top_errors mapping
absolute artifact paths
mode=file
mode=all
```

Canonical writers emit only the current GF Wordbench schema.

Human reports should use canonical product naming after migration.

---

## 61. Current GF Audit reporting baseline

The inherited baseline already includes:

```text
app/reports/report_json.py
app/reports/report_md.py
app/reports/report_ai_ready.py
app/reports/report_logs.py
app/reports/report_details.py
```

It produces:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
master.log
ALL_SCAN_LOGS.TXT
ALL_LOGS.TXT
per-file details
```

It already separates:

- structured JSON;
- human summary;
- AI handoff;
- aggregate logs;
- detail artifacts.

This separation is retained.

---

## 62. Baseline strengths retained

The final design retains:

- one run directory per execution;
- `summary.json` for tooling;
- `summary.md` for humans;
- `AI_READY.md` for AI handoff;
- grouped top errors;
- direct/downstream/ambiguous sections;
- scan and compile distinction;
- detail retention policy;
- aggregate log convenience;
- best-effort terminal reporting.

These are valid foundations.

---

## 63. Baseline migration requirements

Migration to the final reporting model requires:

1. rename GF Audit product headings to GF Wordbench;
2. add schema identity and version;
3. replace uncontrolled dataclass serialization with explicit schema builders;
4. normalize project-relative and run-relative paths;
5. add scenario results;
6. add release-gate results;
7. add PGF and manifest artifacts;
8. add framework `ERROR` semantics;
9. add canonical report-generation warnings;
10. add `manifest.json`;
11. migrate legacy top-error mappings to canonical records;
12. remove legacy aliases from canonical output;
13. keep old readers isolated in migration code;
14. update report tests and fixtures.

---

## 64. Explicit JSON construction

The final JSON writer should construct the canonical object explicitly.

Preferred pattern:

```python
def build_summary_document(run_result: RunResult) -> dict[str, object]:
    return {
        "schema_id": "gf-wordbench.run-summary",
        "schema_version": "1.0",
        "producer": build_producer(...),
        "metadata": build_metadata(run_result),
        "totals": build_totals(run_result),
        "artifacts": build_artifact_paths(run_result),
        "file_results": build_file_results(run_result),
        "scenario_results": build_scenario_results(run_result),
        "diff_entries": build_diff_entries(run_result),
        "top_errors": build_top_errors(run_result),
    }
```

Generic recursion may remain a private helper for leaf values.

It must not define the schema accidentally.

---

## 65. Report-specific references

This overview intentionally does not duplicate complete layouts.

Detailed ownership:

```text
SUMMARY_JSON_REFERENCE.md
    field-by-field JSON schema explanation

SUMMARY_MARKDOWN_REFERENCE.md
    required headings and human rendering

AI_READY_REFERENCE.md
    AI packet structure, excerpt policy, and limits

RAW_LOGS_REFERENCE.md
    raw and aggregate log formats

ARTIFACT_MANIFEST.md
    manifest schema, roles, and verification
```

A detailed rule belongs in one report-specific reference.

This overview should contain only cross-report architecture.

---

## 66. Testing strategy

Recommended test structure:

```text
tests/reports/
├── test_summary_json.py
├── test_summary_markdown.py
├── test_ai_ready.py
├── test_top_errors.py
├── test_raw_logs.py
├── test_details.py
├── test_manifest.py
├── test_report_failures.py
├── test_report_determinism.py
├── test_report_security.py
└── test_report_migration.py
```

Schema-specific tests remain under:

```text
tests/schemas/
```

Contract tests remain under:

```text
tests/contracts/
```

---

## 67. JSON tests

Required cases:

```text
valid schema identity
valid schema version
Unicode preservation
UTC timestamps
project-relative paths
run-relative artifact paths
environment paths
file results
scenario results
empty lists
top errors
diff entries
release gates
framework errors
unknown enum rejection
deterministic ordering
legacy migration
atomic write
```

A round-trip test should load the generated summary through the canonical reader.

---

## 68. Markdown-summary tests

Required cases:

- complete successful run;
- direct failure;
- downstream failure with blocker;
- ambiguous failure;
- framework error;
- scan finding with compile success;
- required scenario failure;
- gold mismatch;
- release gate failure;
- previous-run regression;
- empty optional sections;
- Unicode paths and text;
- final newline;
- no machine parsing dependency.

Golden text fixtures may be used for stable report layouts, but changes must be deliberate.

---

## 69. AI report tests

Required cases:

- no failures;
- one direct failure;
- many downstream failures;
- ambiguous failure;
- failing scenario;
- bounded excerpt;
- truncated excerpt marker;
- missing raw evidence;
- artifact links;
- no secrets;
- no second execution;
- correct first heading;
- deterministic investigation order.

The AI packet must not claim certainty absent from `RunResult`.

---

## 70. Top-error tests

Required cases:

- empty errors;
- one error;
- duplicate normalized errors;
- same message with different kinds;
- tabs and newlines in message;
- deterministic count order;
- deterministic message tie-break;
- Unicode message;
- final newline.

---

## 71. Manifest tests

Required cases:

- required report exists;
- optional artifact absent;
- missing required artifact;
- SHA-256 correctness;
- size correctness;
- deterministic path ordering;
- no path escape;
- hash after final write;
- verifier detects modification;
- self-entry policy;
- atomic write.

---

## 72. Report-failure tests

Simulate failure of:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
detail writer
aggregate log writer
manifest writer
master log writer
```

Verify:

- independent writers are attempted when safe;
- original evidence remains;
- reporting error is visible;
- missing required report blocks release;
- no language status is rewritten incorrectly;
- manifest reflects actual files;
- recovery does not recurse indefinitely.

---

## 73. Determinism tests

Equivalent structured input must produce byte-identical reports except for fields explicitly expected to vary.

Test:

- shuffled input collection normalized into canonical order;
- filesystem enumeration differences;
- Windows versus POSIX path inputs normalized correctly;
- dictionary insertion differences;
- Unicode sort behavior under the documented policy;
- stable headings;
- stable JSON indentation.

---

## 74. Security tests

Verify:

- secret arguments are redacted;
- environment dump is absent;
- ANSI control sequences do not affect displayed Markdown;
- malicious filenames cannot escape the run directory;
- Markdown text does not create unsafe local path writes;
- detail copying enforces containment;
- large logs are bounded in AI report;
- binary artifacts are not embedded;
- report writers do not execute commands.

---

## 75. Performance expectations

Report generation should be small relative to GF execution.

Requirements:

- no second GF run;
- no repeated full-log parsing by each report;
- shared structured results;
- bounded excerpts;
- streaming or bounded copying for large logs;
- SHA-256 computed once per manifest artifact;
- no complete binary artifact reads into memory;
- no unbounded recursive serialization.

Correctness remains more important than minor rendering speed.

---

## 76. Report API compatibility

A public report writer should:

- accept the documented result model;
- return the path written;
- create required parent directories;
- write only its owned destination;
- raise a documented exception on failure;
- avoid modifying its input;
- produce a final newline for text reports.

Changing a public signature requires coordinated migration.

---

## 77. Adding a report field

A new field requires:

```text
[ ] source model owner identified
[ ] field meaning documented
[ ] producer updated
[ ] every report consumer reviewed
[ ] JSON schema impact classified
[ ] default behavior defined
[ ] path semantics reviewed
[ ] enum semantics reviewed
[ ] tests added
[ ] migration added when required
[ ] report-specific reference updated
```

A report writer must not invent a field that no producer guarantees.

---

## 78. Adding a report section

A new optional human section is normally compatible when:

- its facts already exist;
- existing required headings remain;
- no machine consumer depends on heading order;
- report size remains bounded;
- tests are updated.

Changing or removing a required soft-schema heading requires a major soft-schema revision.

---

## 79. Adding a report format

A new format is justified only when it serves a distinct stable consumer.

Before adding it, define:

```text
purpose
owner
audience
source data
canonical or optional status
path
schema or soft schema
security policy
size policy
failure behavior
tests
retention policy
```

The new format must not replace `summary.json` without a major architectural decision.

---

## 80. Change classification

### 80.1 Internal compatible change

Examples:

- private formatting helper;
- improved implementation with identical output;
- performance improvement;
- internal test refactor.

### 80.2 Compatible report extension

Examples:

- optional JSON field with a documented default;
- optional Markdown section;
- optional manifest role;
- additional bounded AI evidence.

Requires a minor schema change when persisted machine structure changes.

### 80.3 Breaking change

Examples:

- report filename change;
- field removal or rename;
- path-base change;
- status meaning change;
- required heading removal;
- ownership transfer;
- array ordering change;
- timestamp semantic change;
- top-error line-format change;
- artifact role redefinition.

Requires:

1. impact analysis;
2. schema or soft-schema version update;
3. writer update;
4. reader update;
5. migration;
6. fixtures and tests;
7. changelog;
8. contract-lock review.

---

## 81. Drift indicators

Reporting drift exists when:

- a report reruns GF;
- a report reruns the scanner;
- two writers own the same path;
- a reader rewrites another owner’s artifact;
- Markdown becomes the source for machine comparison;
- `summary.json` changes without a schema version;
- report and JSON show different statuses;
- top errors use different aggregation rules in different reports;
- AI report classifies a failure differently from `RunResult`;
- a report reconstructs artifact paths instead of using owned fields;
- stdout is shown while stderr is silently ignored;
- a report modifies a raw log;
- a gold file changes during report generation;
- manifest hashes pre-final content;
- required missing reports are not visible;
- report generation mutates `RunResult`;
- GUI and CLI produce different reports from equivalent results;
- absolute project paths become canonical accidentally;
- a new report field has no documented producer;
- legacy aliases appear in canonical output.

Any drift indicator requires coordinated review.

---

## 82. Reporting compliance checklist

```text
[ ] summary.json exists and validates
[ ] summary.md derives from RunResult
[ ] AI_READY.md derives from RunResult and bounded evidence
[ ] top_errors.txt uses canonical ordering
[ ] manifest.json catalogs finalized artifacts
[ ] master.log records orchestration and report warnings
[ ] every artifact has one writer
[ ] no report launches GF
[ ] no report reruns scanning
[ ] no report changes validation status
[ ] no report modifies raw evidence
[ ] no report modifies gold
[ ] stdout and stderr references remain distinct
[ ] project and run paths use correct bases
[ ] timestamps use UTC
[ ] text uses UTF-8 and LF
[ ] text reports have final newline
[ ] machine schemas are versioned
[ ] human reports remain non-authoritative for automation
[ ] missing required reports block release
[ ] report errors remain visible
[ ] secrets are redacted
[ ] deterministic ordering is tested
[ ] atomic writes are used where required
[ ] legacy reading is isolated from canonical writing
```

---

## 83. Final invariants

1. `RunResult` is the single in-memory source for final reporting.
2. `summary.json` is the primary persisted machine record.
3. `summary.md` is the primary human summary.
4. `AI_READY.md` is the bounded AI handoff.
5. `top_errors.txt` is the compact frequency index.
6. `manifest.json` is the final artifact inventory.
7. Raw evidence remains owned by the stage that captured it.
8. Aggregate logs never replace raw evidence.
9. Every report artifact has one writer.
10. Report writers never launch GF.
11. Report writers never rerun scans or scenarios.
12. Report writers never change validation semantics.
13. Report writers never update gold files.
14. Human reports derive from structured results.
15. Machine consumers never depend on Markdown parsing.
16. Paths retain explicit project, run, or environment bases.
17. Status, execution state, error kind, and causal class remain distinct.
18. Both stdout and stderr remain discoverable.
19. Required report failure remains visible.
20. Earlier evidence survives later report failure.
21. Text output is UTF-8, deterministic, and reviewable.
22. Machine output is explicitly versioned.
23. Manifest hashes finalized artifacts.
24. Report changes are coordinated with models, schemas, readers, and tests.
25. Complexity is added only for a stable audience, artifact, or integrity requirement.

---

## 84. Final rule

GF Wordbench reporting follows one evidence-preserving transformation:

```text
completed validation evidence
        → finalized RunResult
        → canonical machine record
        → bounded human and AI views
        → final artifact manifest
```

Every report must be traceable backward through that chain.

A report that cannot identify the structured fact or raw evidence supporting a claim must omit the claim or mark it as unavailable.
