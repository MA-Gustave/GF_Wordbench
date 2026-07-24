# GF Wordbench — Reporting Overview

**Document ID:** `GF-WB-REPORTING-OVERVIEW`  
**Status:** Normative  
**Applies to:** Every terminal GF Wordbench run  
**Owner:** Reporting module and run orchestration  
**Reporting model version:** `2.0`  
**Last reviewed:** `2026-07-24`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related locks:** `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/PERSISTED_SCHEMA_LOCK.md`

---

## 1. Purpose

This document defines the reporting architecture of GF Wordbench.

It establishes:

- which reports and evidence artifacts exist;
- which artifact is authoritative for each use;
- which component owns each path;
- what report writers may consume;
- report-generation order;
- report-failure behavior;
- path, timestamp, status and diagnostic presentation;
- deterministic serialization;
- artifact integrity;
- security and size limits.

The reporting system transforms one terminal run result into durable, reviewable evidence.

It does not perform validation again.

---

## 2. Core rule

> Reports describe captured evidence; they do not create, repair, reinterpret or rerun that evidence.

A report writer may:

- serialize structured results;
- select and order existing facts;
- render human-readable explanations;
- aggregate existing logs into an owned destination;
- calculate presentation-only summaries;
- catalog completed artifacts.

A report writer must not:

- launch GF;
- rerun static scanning;
- rerun compilation;
- rerun scenarios;
- rebuild a PGF;
- change validation status;
- assign causal ownership;
- normalize scenario output independently;
- update gold files;
- reconstruct machine facts from another human report;
- rewrite raw evidence owned by another component.

---

## 3. Product boundary

Reporting concerns one active Wordbench project and one run.

GF Wordbench reports do not own:

- a registry of several Wordbench workspaces;
- multilingual portfolio aggregation;
- cross-project trend analysis;
- portfolio readiness scoring;
- companion-product state or storage.

The independent product `gf-portfolio` may consume public versioned Wordbench artifacts.

Allowed direction:

```text
gf-portfolio -> public versioned GF Wordbench artifacts
```

Prohibited direction:

```text
GF Wordbench -> gf-portfolio runtime
GF Wordbench -> gf-portfolio private schemas
GF Wordbench -> gf-portfolio storage or services
```

Wordbench reporting remains complete and usable when `gf-portfolio` is absent.

---

## 4. Related authorities

| Topic | Authority |
|---|---|
| Cross-document alignment | `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` |
| Framework component boundaries | `docs/INTERFILE_CONTRACT_LOCK.md` |
| Persisted schemas and stable paths | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Architecture | `docs/architecture/ARCHITECTURE_OVERVIEW.md` |
| Data model | `docs/architecture/DATA_MODEL.md` |
| Artifact lifecycle | `docs/architecture/ARTIFACT_MODEL.md` |
| Error handling | `docs/architecture/ERROR_HANDLING_MODEL.md` |
| Process evidence | `docs/architecture/PROCESS_EXECUTION_MODEL.md` |
| JSON summary | `docs/reports/SUMMARY_JSON_REFERENCE.md` |
| Markdown summary | `docs/reports/SUMMARY_MARKDOWN_REFERENCE.md` |
| AI packet | `docs/reports/AI_READY_REFERENCE.md` |
| Raw logs | `docs/reports/RAW_LOGS_REFERENCE.md` |
| Manifest | `docs/reports/ARTIFACT_MANIFEST.md` |
| Status values | `docs/reference/STATUS_VALUES.md` |
| Diagnostic kinds | `docs/reference/DIAGNOSTIC_KINDS.md` |

When rules overlap, the specialized owner document governs its field-level contract.

---

## 5. Reporting goals

The reporting system provides:

### Machine usability

Automation loads one versioned structured record without parsing Markdown.

### Human review

A maintainer can understand the outcome and evidence paths without opening every raw file.

### AI handoff

A bounded evidence packet supports assisted diagnosis without another validation run.

### Traceability

Every material claim points to structured data or owned evidence.

### Reproducibility

Reports identify the run, active project, GF version, validation mode, timestamps and artifacts.

### Anti-drift

Each artifact has one purpose, one path owner and one writer.

### Failure preservation

A report failure never destroys evidence already captured.

---

## 6. Non-goals

The reporting subsystem is not:

- a database;
- a telemetry service;
- a remote dashboard;
- a log-shipping platform;
- a generic analytics engine;
- a live process monitor;
- an unrestricted report-plugin framework;
- a replacement for GF diagnostics;
- a replacement for project documentation;
- a portfolio product.

Additional formats require explicit ownership and contracts.

---

## 7. Report families

GF Wordbench produces four report families.

### 7.1 Machine record

```text
summary.json
```

### 7.2 Human-facing reports

```text
summary.md
AI_READY.md
top_errors.txt
```

### 7.3 Evidence and detail artifacts

```text
raw/master.log
raw/ALL_SCAN_LOGS.TXT
raw/ALL_LOGS.TXT
raw/compile/
raw/scan/
raw/scenarios/
details/
```

### 7.4 Artifact integrity record

```text
manifest.json
```

No artifact is forced to serve every audience.

---

## 8. Run layout

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

Paths come from the run-path owner or artifact registry.

Report writers do not reconstruct canonical filenames independently.

---

## 9. Source-of-truth hierarchy

```text
raw process and scan evidence
        ↓
structured stage results
        ↓
RunResult
        ↓
summary.json
        ↓
human reports and external consumers
```

Interpretation:

- raw evidence is authoritative for what tools emitted;
- structured stage results are authoritative for Wordbench interpretation;
- `RunResult` is authoritative in memory;
- `summary.json` is authoritative after persistence;
- Markdown reports are human projections;
- `manifest.json` is authoritative for artifact inventory and integrity metadata.

No human report is used to reconstruct `RunResult`.

---

## 10. `summary.json`

Canonical path:

```text
summary.json
```

Schema:

```text
schema_id = gf-wordbench.run-summary
schema_version = 1.0
```

Owner:

```text
reporting JSON writer
```

Conceptual public responsibility:

```python
write_summary_json(run_result: RunResult) -> Path
```

It provides structured information for:

- previous-run comparison;
- GUI result loading;
- CLI and automation;
- release-gate verification;
- migration;
- artifact discovery;
- diagnostic aggregation;
- optional read-only Portfolio ingestion.

It includes, as applicable:

```text
schema identity
producer identity
run metadata
resolved execution context
overall status
totals
artifact references
file results
scenario results
PGF or entrypoint results
diff entries
top errors
release gates
framework errors
```

The writer must not:

- serialize arbitrary object internals;
- depend on incidental Python field ordering;
- emit unversioned canonical output;
- emit wrong path bases or separators;
- serialize enum objects directly;
- emit naive timestamps;
- emit `NaN` or infinity;
- copy undocumented legacy fields;
- derive facts from Markdown.

Serialization is explicit and schema-owned.

---

## 11. `summary.md`

Canonical path:

```text
summary.md
```

Owner:

```text
reporting Markdown-summary writer
```

Conceptual responsibilities:

```python
build_summary_md(run_result: RunResult) -> str
write_summary_md(run_result: RunResult) -> Path
```

Purpose:

- summarize the run for human review;
- expose outcome, totals and release gates;
- distinguish direct, ambiguous and downstream failures;
- show scenario failures and regressions;
- link to artifacts and raw evidence.

It is not a machine schema.

Minimum content, when applicable:

```text
Run
Outcome
Totals
Release Gates
Framework Errors
Direct Failures
Required Scenario Failures
Ambiguous Failures
Downstream Failures
Successful Validation
Skipped Validation
Top Errors
Heuristic Scan Findings
Changes Since Previous Run
Artifacts and Evidence
```

The outcome appears near the beginning.

Stable groups use deterministic ordering.

---

## 12. `AI_READY.md`

Canonical path:

```text
AI_READY.md
```

Owner:

```text
reporting AI-packet writer
```

Conceptual public responsibility:

```python
write_ai_ready(run_result: RunResult) -> Path
```

Required first heading:

```text
# AI Ready Packet
```

Purpose:

- provide a bounded diagnostic handoff;
- foreground likely root failures;
- distinguish direct, ambiguous and downstream failures;
- include failing scenarios;
- include bounded evidence excerpts;
- retain complete evidence paths;
- avoid any second execution.

Required sections:

```text
Run Summary
Outcome
Diagnosis Snapshot
Failing Files
Failing Scenarios
Evidence
Artifacts
Ready Prompt For AI
```

Evidence may include bounded excerpts from:

- primary diagnostics;
- compiler stdout and stderr;
- scenario stdout and stderr;
- normalized output;
- gold diffs;
- scan findings;
- blocker relationships.

Rules:

- source paths remain visible;
- truncation is explicit;
- unsupported diagnosis is prohibited;
- secrets are excluded;
- complete large logs are referenced;
- downstream failures are not presented as independent root causes;
- missing evidence is identified honestly.

Detailed behavior is governed by ADR-0006 and `AI_READY_REFERENCE.md`.

---

## 13. `top_errors.txt`

Canonical path:

```text
top_errors.txt
```

Owner:

```text
reporting compact-error writer
```

Canonical line format:

```text
<count>\t<error-kind>\t<message>
```

Example:

```text
3	TYPE	type mismatch
```

Aggregation key:

```text
error kind + normalized primary message
```

Rules:

- counts are positive integers;
- tabs and newlines in messages become spaces;
- distinct error kinds remain distinct;
- order is descending count, then stable message order;
- an empty file is valid;
- encoding is UTF-8 with LF and a trailing newline.

Detailed diagnostic identity remains in `summary.json`.

---

## 14. `manifest.json`

Canonical path:

```text
manifest.json
```

Schema:

```text
schema_id = gf-wordbench.artifact-manifest
schema_version = 1.0
```

Owner:

```text
manifest writer
```

Purpose:

- list retained run artifacts;
- identify role and producer;
- record required or optional policy;
- record media type, size and SHA-256;
- support verification, cleanup, export and release evidence.

The manifest is written after the artifacts it catalogs are stable.

It must not:

- claim absent files exist;
- hash an artifact before writing completes;
- modify an artifact to satisfy a hash;
- catalog temporary files as stable artifacts;
- hide required missing artifacts;
- invent a recursive self-hash.

---

## 15. Raw logs

Canonical raw paths include:

```text
raw/master.log
raw/ALL_SCAN_LOGS.TXT
raw/ALL_LOGS.TXT
raw/compile/
raw/scan/
raw/scenarios/
```

Ownership:

- process adapters own per-operation streams;
- scanner owns per-file scan evidence;
- scenario runner owns scenario streams and normalized outputs;
- run orchestration owns chronological master-log events;
- log aggregation owns aggregate views.

Aggregate logs are derived evidence. They never replace original files.

---

## 16. Master log

Canonical path:

```text
raw/master.log
```

It records:

- run and stage lifecycle;
- process and artifact events;
- report-generation warnings;
- terminal run context;
- framework failures.

The master log is not a persisted machine schema.

Automation must not parse it as the canonical run record.

---

## 17. Aggregate logs

Canonical paths:

```text
raw/ALL_SCAN_LOGS.TXT
raw/ALL_LOGS.TXT
```

Each section identifies:

```text
artifact role
subject
source path
content
```

Aggregate logs:

- use deterministic source ordering;
- preserve original evidence;
- identify missing referenced sources;
- use explicit truncation policy;
- avoid ambiguous concatenation.

---

## 18. Detail artifacts

Canonical directory:

```text
details/
```

Purpose:

- gather focused evidence for failed or selected subjects;
- reduce navigation;
- provide per-file or per-scenario review packets.

Detail artifacts may copy existing evidence into owned files.

They do not alter source evidence.

Retention may depend on:

- validation status;
- diagnostic class;
- scenario outcome;
- keep-all policy;
- release evidence requirements.

Retention never changes validation results.

---

## 19. Reporting module

Reporting belongs to the `reporting` module of the modular monolith.

Conceptual responsibilities include:

```text
JSON serialization
human Markdown rendering
AI packet rendering
compact error index
detail artifacts
aggregate logs
manifest construction
report coordination
```

Internal filenames may vary, but ownership and public contracts remain stable.

No general runtime plugin registry is required.

A public facade may expose stable writer functions while private helpers remain private.

---

## 20. Report inputs

Primary input:

```text
RunResult
```

Additional narrowly owned inputs may include:

- master-log events;
- artifact records;
- report-write outcomes;
- producer metadata.

Report writers do not reload project configuration or application state to reconstruct execution facts.

A missing cross-component fact requires a model change, not dynamic attributes or prose parsing.

---

## 21. Report purity

A report builder follows:

```text
structured input
        → deterministic document value
```

A writer's permitted side effect is:

```text
write its owned artifact
```

Pure build functions are preferred where useful:

```python
build_summary_md(run_result) -> str
build_ai_ready(run_result) -> str
build_summary_document(run_result) -> dict[str, object]
```

The input model is not mutated.

---

## 22. Dependency graph

```text
RunResult
 ├── summary.json
 ├── summary.md
 ├── AI_READY.md
 ├── top_errors.txt
 ├── details/
 └── aggregate logs

all stable retained artifacts
        ↓
manifest.json
```

No canonical report parses another human report.

Shared facts come from shared structured models.

---

## 23. Generation lifecycle

Canonical lifecycle:

```text
1. finalize stage evidence
2. finalize RunResult
3. write detail and aggregate evidence
4. write top_errors.txt
5. write summary.md
6. write AI_READY.md
7. write summary.json
8. record report outcomes
9. write manifest.json
10. finalize master.log
11. verify required outputs
```

The internal order may vary when explicit dependencies require it.

Locked rules:

- writers consume a terminal structured validation result;
- manifest generation follows cataloged artifacts;
- no writer reruns validation;
- missing report artifacts remain visible;
- required release evidence is verified before release success.

---

## 24. Immutability

Report writers do not mutate:

- file or scenario status;
- diagnostic class;
- blocker relationships;
- totals;
- diff entries;
- release gates;
- raw evidence paths;
- source or gold files.

Presentation-only local values may be computed without changing the model.

Invalid model invariants produce explicit reporting errors rather than silent repair.

---

## 25. Report-write outcomes

The coordinator records, at minimum:

```text
report ID
target path
required policy
success
error kind
error message
```

A simple ordered collection is sufficient.

A generic report-job engine is not required.

---

## 26. Failure semantics

A report failure is a framework reporting error.

It is not:

- a GF syntax or type failure;
- a scenario failure;
- a gold mismatch;
- a downstream language failure.

Captured validation evidence remains available.

A missing required report or integrity artifact may block release.

One writer failure does not prevent independent writers from being attempted when safe.

Example:

```text
summary.md fails
AI_READY.md is attempted
summary.json is attempted
manifest records actual presence
master.log records the reporting error
```

Dependencies still apply.

---

## 27. Terminal recovery

After a run directory exists, a terminal framework failure triggers best-effort production of a bounded evidence set when possible:

```text
master.log
summary.json
summary.md
AI_READY.md
manifest.json
```

Recovered reports identify:

- the terminal framework error;
- retained completed evidence;
- incomplete stages;
- unavailable artifacts;
- reporting failures;
- absence of any unsupported success claim.

Recovery does not recurse indefinitely.

---

## 28. Required artifacts

A normal terminal run produces:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
raw/master.log
```

Stage-specific raw evidence depends on executed stages.

Detail and aggregate artifacts follow their retention policy.

A release run satisfies its required artifact manifest.

---

## 29. Atomic writes

Stable reports use atomic replacement where supported:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
```

Process:

1. write a sibling temporary file;
2. flush and close;
3. validate content;
4. atomically replace the destination.

A failed write must not leave a complete-looking partial artifact.

Streaming raw logs are exempt during capture.

---

## 30. Encoding and newlines

Canonical text encoding:

```text
UTF-8 without BOM
```

Canonical newline:

```text
LF
```

Text reports end with one newline.

JSON is valid UTF-8 and follows the JSON writer's stable formatting policy.

Readers may accept CRLF for legacy input.

---

## 31. Determinism

Determinism requires:

- stable subject order;
- stable artifact order;
- stable section order;
- stable top-error ordering;
- stable JSON indentation;
- stable Unicode handling;
- explicit sorting where unordered collections exist;
- no filesystem-enumeration dependence;
- no locale-dependent sorting;
- timezone-aware timestamps.

Timestamps and measured durations legitimately vary between runs.

---

## 32. Path rendering

Paths retain their base.

### Project-relative

```text
lib/src/language/GrammarX.gf
validation/scenarios/parse.gfs
```

### Run-relative

```text
raw/compile/GrammarX.out.txt
artifacts/pgf/Grammar.pgf
```

### Environment-specific

```text
C:/tools/gf/gf.exe
C:/work/gf-rgl/src
```

Persisted project-relative and run-relative paths use `/`.

Human reports may show environment paths when diagnostically necessary.

Report writers must not:

- follow unvalidated paths from diagnostics;
- copy arbitrary files;
- escape the run root;
- overwrite source or gold files;
- create reports outside the active run directory;
- derive filenames from untrusted free text.

---

## 33. Timestamps

Persisted timestamps use RFC 3339-compatible UTC.

Example:

```text
2026-07-22T18:25:43Z
```

Local time may appear only as secondary display with an explicit timezone.

Durations use integer milliseconds.

---

## 34. Status and diagnostic rendering

Validation status:

```text
OK
FAIL
ERROR
SKIPPED
```

Diagnostic class:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Execution state:

```text
completed
timed_out
cancelled
launch_failed
```

Error kind is a separate technical dimension.

Reports keep all dimensions distinct.

A non-zero process exit is not automatically a direct failure.

---

## 35. Failure grouping

Human and AI reports order failures by causal usefulness:

```text
framework errors
direct language failures
required scenario failures
ambiguous failures
downstream failures
warnings and noise
```

Downstream items show `blocked_by` relationships.

The same subject is not presented as both an independent root and downstream without explicit explanation.

---

## 36. Static scan rendering

Static findings are labeled:

```text
heuristic scan findings
```

They are not presented as authoritative GF syntax or type errors.

This state remains representable:

```text
compile OK
scan findings present
```

---

## 37. Scenario rendering

Scenario sections show, when available:

```text
scenario ID
required or optional policy
validation status
execution state
duration
primary message
failed assertions or sections
gold result
blocked_by
stdout and stderr paths
normalized output
gold diff
produced artifacts
```

Order follows project configuration.

Reports do not reparse markers or recompute gold comparison.

---

## 38. Release-gate rendering

Release reports show each gate:

```text
gate ID
status
criterion
evidence
blocking subjects
```

Release readiness is explicit and comes from structured gate results.

It is not inferred from file compile totals.

---

## 39. Regression rendering

Canonical change kinds:

```text
regressed
new
improved
removed
unchanged
```

Display order follows that severity order.

Reports consume structured diff entries and do not compare Markdown text.

---

## 40. Artifact references

Human reports prefer relative artifact paths.

Benefits include:

- portability;
- archive compatibility;
- shorter reports;
- safer handoff;
- independence from local clone paths.

The manifest remains the artifact inventory authority.

---

## 41. Security and privacy

Reports must not contain:

- passwords;
- access tokens;
- private keys;
- cookies;
- complete environment dumps;
- secret command arguments;
- unrelated user-home inventories;
- arbitrary unrelated file contents.

Redaction follows process-request policy.

Local absolute paths are not automatically secrets, but export tooling may redact them.

Raw evidence is not silently rewritten for presentation convenience.

---

## 42. Size policy

Reports remain bounded.

Controls include:

- bounded evidence excerpts;
- explicit truncation markers;
- limits on repeated downstream failures;
- references to complete logs;
- per-subject excerpt limits;
- no binary embedding;
- no complete aggregate-log embedding in Markdown.

`summary.json` retains complete structured records required by its schema.

---

## 43. Large, empty and partial runs

### Large runs

- `summary.md` remains a summary;
- `AI_READY.md` foregrounds root failures;
- `top_errors.txt` remains compact;
- full structured results remain in `summary.json`;
- raw evidence remains in owned directories;
- the manifest lists retained artifacts.

### Empty selection

Reports state:

```text
No validation subjects were included.
```

An empty release selection is not presented as normal release success.

### Partial run

Reports preserve completed facts, identify incomplete stages, distinguish skipped from not reached and state the terminal cause.

Absent results are never treated as passed.

---

## 44. Compatibility

Canonical writers emit only current Wordbench formats.

Documented legacy GF Audit inputs may be read through isolated migration code.

Examples include:

```text
unversioned summary.json
legacy flat or nested summaries
legacy artifact aliases
absolute artifact paths
mode=file
mode=all
```

Legacy names do not appear in canonical output.

A public report change is classified as:

### Internal

No public output or contract changes.

### Compatible extension

Examples:

- optional JSON field with a default;
- optional Markdown section;
- optional manifest role;
- additional bounded AI evidence.

### Breaking change

Examples:

- filename change;
- field removal or rename;
- path-base change;
- status semantic change;
- required heading removal;
- ownership transfer;
- ordering semantic change;
- timestamp semantic change;
- top-error format change;
- artifact-role redefinition.

Breaking changes require coordinated schema, writer, reader, migration, test, lock and release-note updates.

---

## 45. Adding report content

### New field

A new field requires:

```text
[ ] producer identified
[ ] meaning documented
[ ] consumers reviewed
[ ] schema impact classified
[ ] default defined
[ ] path semantics reviewed
[ ] enum semantics reviewed
[ ] tests added
[ ] migration added when required
[ ] owner reference updated
```

A writer must not invent a field with no guaranteed producer.

### New section

An optional human section is compatible when it uses existing facts, preserves required headings, remains bounded and has tests.

### New format

A new format defines:

```text
purpose
owner
audience
source data
path
schema or soft schema
security policy
size policy
failure behavior
retention
tests
```

It does not replace `summary.json` without an architectural decision.

---

## 46. Testing

Tests cover:

### JSON

```text
schema identity and version
Unicode
UTC timestamps
path bases
file and scenario results
empty collections
top errors
diff entries
release gates
framework errors
enum validation
deterministic ordering
legacy migration
atomic write
round-trip loading
```

### Markdown summary

```text
success
direct, ambiguous and downstream failures
framework error
scan findings with compile success
scenario failure
gold mismatch
release-gate failure
regression
empty optional sections
Unicode
trailing newline
no machine parsing dependency
```

### AI packet

```text
no failures
direct and downstream failures
ambiguous failure
scenario failure
bounded evidence
truncation marker
missing evidence
artifact links
secret exclusion
no second execution
required heading
deterministic investigation order
```

### Manifest

```text
required and optional artifacts
missing required artifact
hash and size
deterministic paths
containment
post-write hashing
modification detection
self-entry policy
atomic write
```

### Failure isolation

Simulate failure of every writer and verify:

- independent writers continue when safe;
- original evidence survives;
- errors remain visible;
- release is blocked when required output is missing;
- manifest reflects actual files;
- recovery does not recurse.

### Security and determinism

Verify:

- secret redaction;
- no environment dump;
- safe Markdown rendering;
- path containment;
- bounded large logs;
- no binary embedding;
- no command execution;
- byte-stable output for equivalent structured input except documented variable fields.

---

## 47. Performance

Report generation remains small relative to GF execution.

Requirements:

- no second GF run;
- no repeated complete log parsing by every writer;
- shared structured results;
- bounded excerpts;
- streaming or bounded copying;
- one hash computation per manifest artifact;
- no complete binary reads;
- no unbounded recursive serialization.

Correctness and traceability take precedence over minor rendering speed.

---

## 48. Drift indicators

Reporting drift exists when:

- a report launches GF or another validator;
- two writers own the same path;
- Markdown becomes a machine source;
- `summary.json` changes without schema versioning;
- reports disagree with structured status;
- top-error aggregation differs between writers;
- AI reporting reclassifies failures;
- paths are reconstructed instead of consumed from owners;
- one raw stream is omitted silently;
- raw evidence or gold files are modified;
- manifest hashes unstable content;
- missing required reports are hidden;
- report generation mutates `RunResult`;
- CLI and GUI produce different semantics from equivalent results;
- a field has no producer;
- canonical output contains legacy aliases;
- Wordbench reporting depends on `gf-portfolio`.

Any drift indicator requires coordinated correction.

---

## 49. Compliance checklist

```text
[ ] summary.json validates against its schema
[ ] summary.md derives from RunResult
[ ] AI_READY.md derives from RunResult and bounded evidence
[ ] top_errors.txt uses canonical aggregation
[ ] manifest.json catalogs stable artifacts
[ ] master.log records orchestration and reporting errors
[ ] every artifact has one writer
[ ] no report launches validation
[ ] no report changes validation semantics
[ ] no report modifies raw evidence or golds
[ ] stdout and stderr remain separately discoverable
[ ] path bases are explicit
[ ] timestamps use UTC
[ ] text uses UTF-8 and LF
[ ] text reports end with a newline
[ ] machine schemas are versioned
[ ] automation does not parse Markdown
[ ] required report failures block release
[ ] reporting errors remain visible
[ ] secrets are excluded
[ ] deterministic ordering is tested
[ ] atomic writes are used where required
[ ] legacy reading is isolated
[ ] Wordbench remains independent from gf-portfolio
```

---

## 50. Invariants

1. `RunResult` is the in-memory reporting source.
2. `summary.json` is the persisted machine record.
3. `summary.md` is the general human summary.
4. `AI_READY.md` is the bounded AI handoff.
5. `top_errors.txt` is the compact error index.
6. `manifest.json` is the artifact inventory.
7. Raw evidence remains owned by the capturing stage.
8. Aggregate logs never replace raw evidence.
9. Every artifact has one writer.
10. Report writers never execute GF, scanning or scenarios.
11. Report writers never change validation semantics.
12. Report writers never update gold files.
13. Human reports derive from structured results.
14. Machine consumers do not depend on Markdown.
15. Paths retain explicit bases.
16. Status, execution state, error kind and causal class remain distinct.
17. Both stdout and stderr remain discoverable.
18. Required writer failure remains visible.
19. Earlier evidence survives later report failure.
20. Machine output is versioned.
21. Manifest hashes stable artifacts.
22. Changes are coordinated with models, schemas, readers and tests.
23. Reporting has no dependency on `gf-portfolio`.

---

## 51. Enforcement

GF Wordbench reporting follows this evidence-preserving transformation:

```text
captured validation evidence
        → terminal RunResult
        → versioned machine record
        → bounded human and AI views
        → artifact manifest
```

Every report claim must be traceable through that chain.

A claim without structured support or identifiable evidence is omitted or marked unavailable.
