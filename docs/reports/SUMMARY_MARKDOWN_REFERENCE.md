# GF Wordbench — Summary Markdown Reference

**Document ID:** `GF-WB-REPORT-SUMMARY-MARKDOWN`  
**Status:** Normative human-report reference  
**Applies to:** `run_<run-id>/summary.md`  
**Primary writer:** `app/reports/report_md.py`  
**Primary input:** `RunResult`  
**Machine source of truth:** `run_<run-id>/summary.json`  
**Owner:** GF Wordbench maintainers  
**Soft-schema version:** `1.0`  
**Last structural review:** 2026-07-22  

---

## 1. Purpose

`summary.md` is the primary human-readable report for one GF Wordbench run.

It provides a compact, navigable explanation of:

- what was executed;
- whether required validation passed;
- which files failed directly;
- which files failed downstream;
- which failures remain ambiguous;
- which scenarios passed or failed;
- what changed since the selected baseline;
- where detailed and raw evidence is stored;
- which release gates passed or failed.

The report is intended for:

- developers;
- language-project maintainers;
- reviewers;
- release managers;
- CI artifact browsing;
- GUI “open report” actions;
- issue attachments after privacy review.

The report must be understandable without reading the implementation.

It must remain traceable to structured evidence.

---

## 2. Core rule

> `summary.md` explains `RunResult`; it does not reconstruct, reinterpret, or replace it.

Every factual claim in the report must derive from:

```text
RunResult
```

or from a run artifact referenced by `RunResult` where the report is explicitly allowed to display a bounded excerpt.

The writer must not:

- rerun GF;
- rescan source;
- execute scenarios;
- compare gold files;
- recompute causal classification independently;
- parse `summary.json` when the in-memory `RunResult` is already available;
- derive machine state from report prose;
- modify source files;
- modify `.gold` files;
- modify raw evidence;
- modify another report writer’s artifact.

---

## 3. Role among run artifacts

Canonical run artifacts include:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
details/
raw/
artifacts/
```

Their roles differ.

| Artifact | Primary role | Primary readers |
|---|---|---|
| `summary.json` | Canonical machine-readable run record | Framework, GUI, automation, diff loader |
| `summary.md` | Human-readable run report | Developers and reviewers |
| `AI_READY.md` | Bounded AI handoff packet | Humans and AI systems |
| `top_errors.txt` | Compact grouped error inventory | Humans and optional tooling |
| `manifest.json` | Artifact identity and integrity | Verifier and tooling |
| `details/` | Per-subject detail reports | Developers |
| `raw/` | Unmodified execution evidence | Diagnostic investigation |
| `artifacts/` | Generated GF and derived outputs | Developers and release tooling |

`summary.md` must not duplicate the full purpose of `AI_READY.md`.

`summary.md` emphasizes human review and navigation.

`AI_READY.md` emphasizes bounded diagnostic context suitable for an AI handoff.

---

## 4. Canonical identity

## 4.1 Path

```text
run_<run-id>/summary.md
```

## 4.2 Encoding

```text
UTF-8
```

Canonical repository-independent output should use:

```text
LF
```

## 4.3 Final newline

The file must end with exactly one newline.

## 4.4 First heading

Required:

```text
# GF Wordbench Audit Summary
```

Legacy:

```text
# GF Audit Summary
```

may be read by humans but must not be emitted by the final canonical writer.

## 4.5 Soft-schema version

The report does not need an inline machine schema identifier in every release.

The report structure is governed by:

```text
soft-schema version 1.0
```

A visible generator-version line is required in the run summary.

---

## 5. Required top-level sections

The following level-two headings are required and appear in this order:

```text
## Run Summary
## Outcome
## File Results
## Scenario Results
## Regression Comparison
## Artifacts
```

A required section may contain:

```text
None.
```

when no applicable data exists.

Required headings must not be omitted merely because their contents are empty.

This stable outline supports:

- predictable human navigation;
- documentation;
- screenshot review;
- issue templates;
- simple non-authoritative text search;
- future accessibility tooling.

Machine consumers must still use `summary.json`.

---

## 6. Optional top-level sections

The writer may add these sections after the required core sections or at their documented insertion points:

```text
## Release Gates
## Top Errors
## Static Scan Notes
## Warnings
## Report Generation
```

Rules:

- optional sections must derive from structured evidence;
- their order must be deterministic;
- they must not replace required sections;
- a minor soft-schema revision may add an optional section;
- removing or renaming a required heading requires a major soft-schema revision.

Recommended final order:

```text
# GF Wordbench Audit Summary

## Run Summary
## Outcome
## Release Gates
## File Results
## Scenario Results
## Top Errors
## Static Scan Notes
## Regression Comparison
## Artifacts
## Warnings
## Report Generation
```

`Release Gates`, `Top Errors`, `Static Scan Notes`, `Warnings`, and `Report Generation` may be omitted when not applicable.

---

# 7. Report generation contract

## 7.1 Public writer

Canonical logical API:

```python
write_summary_md(run_result: RunResult) -> Path
```

Recommended pure builder:

```python
build_summary_md(run_result: RunResult) -> str
```

## 7.2 Output ownership

The Markdown writer owns:

```text
summary.md
```

It does not own:

```text
summary.json
AI_READY.md
top_errors.txt
manifest.json
raw/*
details/*
artifacts/*
```

## 7.3 Write behavior

The writer must:

1. validate enough model invariants to avoid misleading output;
2. build deterministic Markdown;
3. write UTF-8;
4. use atomic replacement where supported;
5. return the written path;
6. leave the prior valid file intact if replacement fails.

## 7.4 Read-only input

The writer must treat `RunResult` and nested results as read-only.

It must not mutate:

```text
status
diagnostic_class
blocked_by
top_errors
diff_entries
scenario_results
artifact paths
counts
```

## 7.5 Failure behavior

A writer failure:

- must be recorded by orchestration;
- must not destroy `summary.json`;
- must not prevent independent report writers from being attempted;
- may change the run to `ERROR` if the report is required by the active mode;
- must preserve already written raw evidence.

---

# 8. Source model

The final report consumes these logical domains from `RunResult`:

```text
run metadata
resolved configuration summary
overall status
file totals
scenario totals
release gates
file results
scenario results
top errors
diff entries
artifact references
warnings
report-generation results
```

A field absent from the current implementation may be rendered as:

```text
Unknown
```

only when the field is optional.

A missing required model field is a framework error, not an invitation to invent a value.

---

# 9. Rendering principles

## 9.1 Human-first

The report should answer important questions near the top:

1. Did the run pass?
2. What failed?
3. Which failures are likely roots?
4. Which required scenarios failed?
5. What changed?
6. Where is the evidence?

## 9.2 Structured but not machine-canonical

Use:

- headings;
- bullets;
- small tables;
- inline code;
- short explanatory sentences.

Avoid:

- giant JSON blocks;
- full raw logs;
- repeated stack traces;
- machine-only numeric identifiers without context;
- tables too wide for common Markdown viewers.

## 9.3 Concise evidence

The report contains summaries and paths.

Full evidence remains under:

```text
raw/
details/
```

## 9.4 Stable terminology

Use canonical terms:

```text
GF Wordbench
quick
checkpoint
release
diagnostic
OK
FAIL
ERROR
SKIPPED
direct
downstream
ambiguous
noise
skipped
```

Do not emit legacy mode names:

```text
file
all
```

except inside an explicitly labeled migration warning.

## 9.5 No unsupported diagnosis

Allowed:

```text
The first diagnostic points to GrammarFre.gf.
```

Not allowed without proof:

```text
GrammarFre.gf definitely caused every failure.
```

## 9.6 Empty content

Canonical empty marker:

```text
None.
```

Do not alternate unpredictably between:

```text
none
-
N/A
No items
```

A field inside a table may use:

```text
—
```

for not applicable.

---

# 10. Markdown safety

## 10.1 Untrusted text

The following may contain Markdown control characters:

- GF diagnostics;
- filenames;
- module names;
- scenario messages;
- project names;
- warnings;
- tool output.

The writer must render them safely.

## 10.2 Inline code

Paths, IDs, enum values, commands, and concise diagnostic fragments should normally use inline code:

```markdown
`lib/src/french/GrammarFre.gf`
```

## 10.3 Backticks inside values

A value containing a backtick must not be inserted into a single-backtick code span unchanged.

Use:

- a longer code-span delimiter;
- escaped plain text;
- a fenced block when multiline.

## 10.4 Pipes in tables

Escape:

```text
|
```

inside table cells.

## 10.5 Newlines

Untrusted multiline values must not be inserted directly into one bullet label or table cell.

Use:

- first normalized line;
- a bounded fenced block;
- a detail artifact link/path.

## 10.6 HTML

Raw HTML from diagnostics must not be passed through as active HTML.

Escape it or place it in a code block.

## 10.7 Control characters

Remove or visibly encode unsafe control characters except:

```text
tab where explicitly rendered
LF
```

## 10.8 ANSI sequences

ANSI color/control sequences must not appear in the final report.

Raw logs may preserve original bytes according to their own contract.

---

# 11. Path rendering

## 11.1 Project assets

Project file paths are displayed project-relative with `/`.

Example:

```text
lib/src/french/GrammarFre.gf
```

## 11.2 Run artifacts

Run artifact paths should be displayed run-relative whenever possible.

Examples:

```text
summary.json
raw/compile/GrammarFre.stdout.txt
details/GrammarFre.md
```

## 11.3 External environment paths

External paths may be absolute when necessary:

```text
GF executable
RGL root
project root
output root
```

The report should avoid repeating them in every row.

## 11.4 Links

Relative Markdown links are recommended for run-owned artifacts:

```markdown
[Open JSON summary](summary.json)
```

Link destinations must be URL-encoded or safely constructed.

When reliable clickable links cannot be guaranteed across viewers, include the run-relative code path.

## 11.5 Privacy

Absolute paths can expose usernames and workstation layouts.

A portable/redacted export may replace stable prefixes with:

```text
<PROJECT_ROOT>
<RGL_ROOT>
<OUT_ROOT>
```

The standard local report may retain resolved paths.

Redaction must be explicit.

---

# 12. Date, time, and duration rendering

## 12.1 Timestamps

Display canonical UTC timestamps in ISO 8601 form.

Example:

```text
2026-07-22T18:15:42Z
```

## 12.2 Duration

The structured model retains:

```text
duration_ms
```

Human display should include a readable duration:

```text
12.438 s
```

and may include the exact milliseconds:

```text
12.438 s (`12438 ms`)
```

## 12.3 Unknown value

Use:

```text
Unknown
```

Do not substitute the current clock time.

---

# 13. Ordering

## 13.1 General rule

Rendering order must match structured canonical order whenever defined.

## 13.2 File results

Canonical:

```text
normalized file_path
```

Within failure summaries, presentation may group by diagnostic class while preserving path order inside each class.

## 13.3 Scenario results

Canonical:

```text
scenario execution order from project configuration
```

Do not sort scenarios alphabetically if that would lose declared order.

## 13.4 Top errors

Canonical:

```text
descending count
then case-insensitive message
then error kind
```

## 13.5 Regression entries

Canonical:

```text
regressed
new
improved
removed
unchanged
```

Then:

```text
subject kind
subject ID
```

## 13.6 Artifacts

Canonical:

```text
role order
then normalized path
```

Recommended role order:

```text
machine summary
human summary
AI packet
manifest
top errors
aggregate logs
details
raw compile
raw scan
raw scenarios
generated artifacts
```

---

# 14. Required section: Run Summary

## 14.1 Purpose

Identify the exact run, project, mode, toolchain, and timing.

## 14.2 Required fields

Display:

```text
Run ID
GF Wordbench version
Project ID
Project name
Language code
Mode
Target or checkpoint
Started
Finished
Duration
GF version
Run directory
```

## 14.3 Conditional fields

Display when applicable:

```text
Strict mode
Checkpoint ID
Explicit baseline
GF executable
RGL root
Normalization version
Project configuration schema
Run summary schema
```

## 14.4 Recommended format

A compact two-column table:

```markdown
## Run Summary

| Field | Value |
|---|---|
| Run ID | `20260722_181542` |
| GF Wordbench | `1.0.0` |
| Project | `fre` — French |
| Language code | `fre` |
| Mode | `release` |
| Started | `2026-07-22T18:15:42Z` |
| Finished | `2026-07-22T18:15:55Z` |
| Duration | 13.021 s |
| GF version | `3.x` |
| Run directory | `run_20260722_181542` |
```

## 14.5 Target rendering

Quick mode:

```text
Target = project-relative file
```

Checkpoint mode:

```text
Checkpoint = configured checkpoint ID
```

Release and diagnostic modes:

```text
Target = —
```

unless an explicit supported subset is used.

## 14.6 Legacy fields

Do not emit legacy labels as canonical fields:

```text
scan_dir
scan_glob
gf_path raw string
no_compile
```

Relevant configuration may appear in an optional technical details subsection.

---

# 15. Required section: Outcome

## 15.1 Purpose

State the result immediately and summarize important counts.

## 15.2 First line

Recommended:

```markdown
**Overall status: `OK`**
```

or:

```markdown
**Overall status: `FAIL`**
```

or:

```markdown
**Overall status: `ERROR`**
```

## 15.3 Required explanation

Follow with one concise sentence.

Examples:

```text
All required validation checks passed.
```

```text
Required validation completed, but one or more checks failed.
```

```text
The run could not complete reliably because a required execution stage errored.
```

## 15.4 Required count table

Display at least:

```text
Files included
Files OK
Files failed
Files errored
Files skipped
Direct failures
Downstream failures
Ambiguous failures
Scenarios seen
Scenarios OK
Scenarios failed
Scenarios errored
Scenarios skipped
```

Fields not applicable to an older model may display:

```text
Unknown
```

during transition, but the final model should provide them.

## 15.5 Recommended format

```markdown
| Measure | Count |
|---|---:|
| Files included | 42 |
| Files OK | 39 |
| Files failed | 3 |
| Files errored | 0 |
| Files skipped | 0 |
| Direct failures | 1 |
| Downstream failures | 2 |
| Ambiguous failures | 0 |
| Scenarios seen | 6 |
| Scenarios OK | 5 |
| Scenarios failed | 1 |
| Scenarios errored | 0 |
| Scenarios skipped | 0 |
```

## 15.6 Main blockers

When failures exist, include a short list:

```markdown
### Main blockers

- `lib/src/french/GrammarFre.gf` — `TYPE`: cannot unify ...
- `linearize-basic` — gold output mismatch
```

Only direct and important ambiguous failures belong here.

Do not repeat every downstream failure.

## 15.7 Successful outcome

When status is `OK`, `Main blockers` is omitted.

---

# 16. Optional section: Release Gates

## 16.1 When present

Required in:

```text
release mode
```

Recommended in other modes when release gates were explicitly evaluated.

## 16.2 Fields

Each gate displays:

```text
Gate ID
Required
Status
Message
Evidence
```

## 16.3 Format

```markdown
## Release Gates

| Gate | Required | Status | Evidence |
|---|:---:|---|---|
| Required file compilation | Yes | `OK` | 42/42 passed |
| Required scenarios | Yes | `FAIL` | `linearize-basic` |
| PGF build | Yes | `OK` | `artifacts/pgf/GrammarFre.pgf` |
| Manifest validation | Yes | `OK` | `manifest.json` |
```

## 16.4 Overall consistency

The report must not show:

```text
Overall status = OK
```

while a required release gate displays:

```text
FAIL
```

Such inconsistency is a model or writer error.

---

# 17. Required section: File Results

## 17.1 Purpose

Present file validation outcomes while prioritizing root-like failures.

## 17.2 Required subsections

Use in this order:

```text
### Direct Failures
### Ambiguous Failures
### Downstream Failures
### Errored Files
### Skipped Files
### Successful Files
### Excluded or Noise Files
```

A subsection may be omitted when empty, except that the section itself remains.

Recommended concise empty behavior:

```text
None.
```

when all file collections are empty.

## 17.3 Direct failures

Each entry displays:

```text
file path
module name
status
error kind
first error
duration
timeout state
raw evidence
detail report
```

Example:

```markdown
### Direct Failures

#### `lib/src/french/GrammarFre.gf`

- Module: `GrammarFre`
- Status: `FAIL`
- Error kind: `TYPE`
- First error: `cannot unify ...`
- Duration: 1.284 s
- Timed out: No
- Evidence:
  - [stdout](raw/compile/GrammarFre.stdout.txt)
  - [stderr](raw/compile/GrammarFre.stderr.txt)
  - [scan](raw/scan/GrammarFre.scan.txt)
  - [details](details/GrammarFre.md)
```

## 17.4 Technical direct failures

A timeout, I/O error, or tool error must be labeled accurately.

Example:

```text
Direct technical failure: compilation timed out.
```

Do not describe it as a proven grammar defect.

## 17.5 Ambiguous failures

Show the same core fields plus:

```text
Reason classification remains ambiguous
```

Example:

```text
The diagnostic references a file that passed in this run.
```

## 17.6 Downstream failures

Each entry displays:

```text
file path
status
blocked_by
concise immediate message
evidence paths
```

Example:

```markdown
#### `lib/src/french/LangFre.gf`

- Status: `FAIL`
- Blocked by:
  - `lib/src/french/GrammarFre.gf`
- First error: `dependency GrammarFre failed`
- Evidence:
  - [stderr](raw/compile/LangFre.stderr.txt)
```

Do not duplicate the blocker’s full error block.

## 17.7 Errored files

Use for:

```text
status = ERROR
```

when not already grouped clearly by causal class.

The final writer should preferably group by causal class and label status explicitly, avoiding duplicate entries.

A file must appear once in the detailed file outcome groups.

## 17.8 Skipped files

Display:

```text
path
skip reason
required/optional relevance where modeled
```

Example:

```markdown
- `lib/src/french/ExtraFre.gf` — compilation disabled by the resolved diagnostic plan.
```

## 17.9 Successful files

A compact table is preferred.

```markdown
### Successful Files

| File | Module | Duration | Scan hits |
|---|---|---:|---:|
| `lib/src/french/NounFre.gf` | `NounFre` | 0.812 s | 0 |
```

## 17.10 Large successful set

To keep the report useful:

- list every successful file in release mode when the project is reasonably sized;
- for very large projects, show a deterministic bounded list plus total and artifact path;
- never silently truncate;
- record:

```text
Showing 100 of 642 successful files.
```

The complete machine list remains in `summary.json`.

## 17.11 Noise results

Show excluded/noise files only when they are represented as result objects or when the selection summary exposes them.

Do not invent per-file exclusion reasons from counts alone.

---

# 18. File status consistency

Required combinations:

```text
OK      -> diagnostic_class = ok
SKIPPED -> diagnostic_class = skipped
FAIL    -> direct | downstream | ambiguous
ERROR   -> direct | downstream | ambiguous
```

Noise follows selection policy.

The report writer must detect impossible combinations before rendering misleading prose.

Examples of invalid combinations:

```text
status = OK, diagnostic_class = downstream
status = SKIPPED, diagnostic_class = direct
diagnostic_class = downstream, blocked_by = []
```

The writer may:

- raise a report-model validation error;
- render an explicit framework warning in best-effort mode.

It must not silently repair the model.

---

# 19. Required section: Scenario Results

## 19.1 Purpose

Report native GF scenario execution, marker completion, assertions, gold comparison, and artifacts.

## 19.2 Empty state

When no scenarios were selected:

```markdown
## Scenario Results

None.
```

Do not omit the section.

## 19.3 Summary table

Recommended:

```markdown
| Scenario | Required | Status | Execution | Gold | Duration |
|---|:---:|---|---|---|---:|
| `load` | Yes | `OK` | `completed` | — | 0.834 s |
| `linearize-basic` | Yes | `FAIL` | `completed` | Mismatch | 1.121 s |
| `generation-smoke` | No | `SKIPPED` | `not_started` | — | 0 s |
```

## 19.4 Failed scenario details

For each failed or errored scenario display:

```text
scenario ID
required flag
status
execution state
error kind
primary message
marker/section failures
gold state
script path
stdout path
stderr path
normalized output path
gold path
diff path
produced artifacts
```

## 19.5 Gold values

Canonical human labels:

```text
Match
Mismatch
Not required
Missing
Not compared
```

They derive from structured fields.

## 19.6 Marker failures

Example:

```text
Required end marker missing: linearize-basic
```

Do not describe a zero-exit process as scenario success when markers failed.

## 19.7 Scenario order

Preserve project-declared execution order.

## 19.8 Optional failures

Clearly label optional scenarios.

An optional scenario failure may coexist with overall `OK` only when project policy explicitly allows it.

The report should state:

```text
Optional diagnostic failure; does not affect overall required validation.
```

---

# 20. Optional section: Top Errors

## 20.1 Purpose

Show grouped recurring primary errors without replacing subject-level details.

## 20.2 Source

Use:

```text
RunResult.top_errors
```

Do not regroup raw logs in the Markdown writer.

## 20.3 Recommended table

```markdown
| Count | Kind | Message |
|---:|---|---|
| 3 | `TYPE` | `cannot unify ...` |
| 1 | `INTERNAL` | `Internal error in GeneratePMCFG` |
```

## 20.4 Limit

A bounded display is recommended:

```text
top 20
```

If truncated, state:

```text
Showing 20 of 37 grouped errors.
```

## 20.5 Empty state

```text
None.
```

---

# 21. Optional section: Static Scan Notes

## 21.1 Purpose

Show heuristic source findings separately from GF validation outcomes.

## 21.2 Separation rule

Static scan findings must not be presented as GF compile failures.

Use wording such as:

```text
Heuristic scan finding
```

not:

```text
Compiler error
```

## 21.3 Grouping

Recommended groups:

```text
failed files with scan findings
errored files with scan findings
successful files with scan findings
skipped files with scan findings
```

## 21.4 Fields

Display:

```text
file path
status
finding kind
count
scan artifact
```

## 21.5 Example

```markdown
| File | File status | Finding | Count |
|---|---|---|---:|
| `lib/src/french/MorphoFre.gf` | `OK` | `runtime_str_match` | 2 |
```

## 21.6 Zero findings

Omit the optional section when there are no scan findings.

---

# 22. Required section: Regression Comparison

## 22.1 Purpose

Summarize changes against the selected compatible baseline.

## 22.2 No baseline

Render:

```markdown
## Regression Comparison

No compatible baseline was available.
```

## 22.3 Disabled comparison

Render:

```text
Comparison was disabled for this run.
```

only when that state is available in structured comparison context.

## 22.4 Summary counts

Display:

```text
regressed
new
improved
removed
unchanged
```

## 22.5 Group order

```text
### Regressions
### New Subjects
### Improvements
### Removed Subjects
### Unchanged Details
### Comparison Warnings
```

Empty low-priority groups may be omitted.

## 22.6 Diff entry format

Generalized final model:

```markdown
- `file` `lib/src/french/GrammarFre.gf`: `FAIL` → `OK` — **improved**
  - Compilation now succeeds.
```

Scenario example:

```markdown
- `scenario` `linearize-basic`: `OK` → `FAIL` — **regressed**
  - Gold comparison now mismatches.
```

## 22.7 Unchanged entries

The human report should normally omit unchanged entries without meaningful detail changes.

If included, place them last.

The complete canonical list remains in `summary.json`.

## 22.8 Legacy `file_path`

During migration, a legacy file-only diff entry is rendered as:

```text
subject_kind = file
subject_id = file_path
```

The final writer should not emit the legacy shape into structured output.

## 22.9 Baseline context

Display when known:

```text
Baseline run ID
Baseline mode
Baseline GF version
Compatibility warnings
```

Do not claim that a GF version change caused a regression.

---

# 23. Required section: Artifacts

## 23.1 Purpose

Provide a stable navigation index.

## 23.2 Required entries

Display when available:

```text
JSON summary
Markdown summary
AI-ready report
Top-errors report
Manifest
Master log
Aggregate scan log
Aggregate execution log
Details directory
Raw directory
Compile logs directory
Scan logs directory
Scenario logs directory
GFO artifacts directory
Output artifacts directory
PGF artifacts directory
```

## 23.3 Recommended format

```markdown
## Artifacts

| Role | Path |
|---|---|
| Machine summary | [summary.json](summary.json) |
| Human summary | `summary.md` |
| AI packet | [AI_READY.md](AI_READY.md) |
| Manifest | [manifest.json](manifest.json) |
| Top errors | [top_errors.txt](top_errors.txt) |
| Master log | [raw/master.log](raw/master.log) |
| Details | [details/](details/) |
| Scenario logs | [raw/scenarios/](raw/scenarios/) |
| PGF artifacts | [artifacts/pgf/](artifacts/pgf/) |
```

## 23.4 Self-link

The `summary.md` row may use code text rather than a self-link.

## 23.5 Missing artifact

When a normally expected artifact is missing:

```text
Missing
```

and include a report-generation warning.

Do not create a fake link.

## 23.6 Manifest timing

`summary.md` is normally written before `manifest.json`.

The report may still show the canonical manifest path.

The manifest writer later verifies final artifact bytes.

---

# 24. Optional section: Warnings

## 24.1 Purpose

Display non-fatal conditions that affect interpretation.

Examples:

```text
GF version is newer than the tested compatibility range.
Previous run used a legacy summary schema.
Scenario normalization version changed.
Some stdout was truncated.
Classification remained incomplete.
Optional scenario failed.
```

## 24.2 Source

Warnings must come from structured run warnings or controlled writer validation.

Do not mine arbitrary lines from raw logs.

## 24.3 Severity

Recommended labels:

```text
Info
Warning
```

Errors that affect overall reliability belong in `Outcome`.

---

# 25. Optional section: Report Generation

## 25.1 Purpose

Show report-writer failures in partial/error runs.

## 25.2 Example

```markdown
## Report Generation

- `summary.json`: `OK`
- `summary.md`: `OK`
- `AI_READY.md`: `ERROR` — permission denied
- `manifest.json`: `SKIPPED` — run not finalized
```

## 25.3 Self-report limitation

The Markdown writer cannot reliably report its own final write success inside the content before the write occurs.

The orchestration layer may update a separate finalization artifact or master log.

Avoid recursive rewriting solely to record that `summary.md` was written.

---

# 26. Canonical complete example

```markdown
# GF Wordbench Audit Summary

## Run Summary

| Field | Value |
|---|---|
| Run ID | `20260722_181542` |
| GF Wordbench | `1.0.0` |
| Project | `fre` — French |
| Language code | `fre` |
| Mode | `release` |
| Started | `2026-07-22T18:15:42Z` |
| Finished | `2026-07-22T18:15:55Z` |
| Duration | 13.021 s |
| GF version | `3.x` |
| Run directory | `run_20260722_181542` |

## Outcome

**Overall status: `FAIL`**

Required validation completed, but one or more checks failed.

| Measure | Count |
|---|---:|
| Files included | 42 |
| Files OK | 39 |
| Files failed | 3 |
| Files errored | 0 |
| Files skipped | 0 |
| Direct failures | 1 |
| Downstream failures | 2 |
| Ambiguous failures | 0 |
| Scenarios seen | 6 |
| Scenarios OK | 5 |
| Scenarios failed | 1 |
| Scenarios errored | 0 |
| Scenarios skipped | 0 |

### Main Blockers

- `lib/src/french/GrammarFre.gf` — `TYPE`: `cannot unify ...`
- `linearize-basic` — normalized output does not match gold

## Release Gates

| Gate | Required | Status | Evidence |
|---|:---:|---|---|
| Required file compilation | Yes | `FAIL` | 3 files failed |
| Required scenarios | Yes | `FAIL` | `linearize-basic` |
| PGF build | Yes | `OK` | `artifacts/pgf/GrammarFre.pgf` |
| Manifest validation | Yes | `OK` | `manifest.json` |

## File Results

### Direct Failures

#### `lib/src/french/GrammarFre.gf`

- Module: `GrammarFre`
- Status: `FAIL`
- Error kind: `TYPE`
- First error: `cannot unify ...`
- Duration: 1.284 s
- Timed out: No
- Evidence:
  - [stdout](raw/compile/GrammarFre.stdout.txt)
  - [stderr](raw/compile/GrammarFre.stderr.txt)
  - [scan](raw/scan/GrammarFre.scan.txt)
  - [details](details/GrammarFre.md)

### Downstream Failures

#### `lib/src/french/LangFre.gf`

- Status: `FAIL`
- Blocked by:
  - `lib/src/french/GrammarFre.gf`
- First error: `dependency GrammarFre failed`
- Evidence:
  - [stderr](raw/compile/LangFre.stderr.txt)

#### `lib/src/french/AllFre.gf`

- Status: `FAIL`
- Blocked by:
  - `lib/src/french/GrammarFre.gf`
- Evidence:
  - [stderr](raw/compile/AllFre.stderr.txt)

### Successful Files

39 files passed.

[See complete structured results](summary.json).

## Scenario Results

| Scenario | Required | Status | Execution | Gold | Duration |
|---|:---:|---|---|---|---:|
| `load` | Yes | `OK` | `completed` | — | 0.834 s |
| `missing` | Yes | `OK` | `completed` | Match | 0.731 s |
| `linearize-basic` | Yes | `FAIL` | `completed` | Mismatch | 1.121 s |
| `parse-basic` | Yes | `OK` | `completed` | Match | 0.942 s |
| `generation-smoke` | Yes | `OK` | `completed` | — | 1.402 s |
| `morphology-basic` | Yes | `OK` | `completed` | Match | 0.811 s |

### Failed Scenarios

#### `linearize-basic`

- Required: Yes
- Error kind: `OTHER`
- Message: Normalized output does not match gold.
- Script: `project/validation/scenarios/linearize-basic.gfs`
- Actual: `raw/scenarios/linearize-basic.out`
- Expected: `project/validation/gold/linearize-basic.gold`
- Evidence:
  - [stdout](raw/scenarios/linearize-basic.stdout.txt)
  - [stderr](raw/scenarios/linearize-basic.stderr.txt)

## Top Errors

| Count | Kind | Message |
|---:|---|---|
| 3 | `TYPE` | `cannot unify ...` |

## Regression Comparison

Baseline: `run_20260721_161005`

| Change | Count |
|---|---:|
| Regressed | 2 |
| New | 0 |
| Improved | 1 |
| Removed | 0 |
| Unchanged | 45 |

### Regressions

- `file` `lib/src/french/GrammarFre.gf`: `OK` → `FAIL`
- `scenario` `linearize-basic`: `OK` → `FAIL`

### Improvements

- `file` `lib/src/french/MorphoFre.gf`: `FAIL` → `OK`

## Artifacts

| Role | Path |
|---|---|
| Machine summary | [summary.json](summary.json) |
| Human summary | `summary.md` |
| AI packet | [AI_READY.md](AI_READY.md) |
| Manifest | [manifest.json](manifest.json) |
| Top errors | [top_errors.txt](top_errors.txt) |
| Master log | [raw/master.log](raw/master.log) |
| Details | [details/](details/) |
| Scenario logs | [raw/scenarios/](raw/scenarios/) |
| PGF artifacts | [artifacts/pgf/](artifacts/pgf/) |
```

The example is illustrative.

Actual language-specific values come from the active project.

---

# 27. Minimal successful example

```markdown
# GF Wordbench Audit Summary

## Run Summary

| Field | Value |
|---|---|
| Run ID | `20260722_181542` |
| GF Wordbench | `1.0.0` |
| Project | `fre` — French |
| Mode | `quick` |
| Target | `lib/src/french/NounFre.gf` |
| GF version | `3.x` |
| Duration | 0.842 s |

## Outcome

**Overall status: `OK`**

All required validation checks passed.

| Measure | Count |
|---|---:|
| Files included | 1 |
| Files OK | 1 |
| Files failed | 0 |
| Files errored | 0 |
| Files skipped | 0 |
| Direct failures | 0 |
| Downstream failures | 0 |
| Ambiguous failures | 0 |
| Scenarios seen | 0 |
| Scenarios OK | 0 |
| Scenarios failed | 0 |
| Scenarios errored | 0 |
| Scenarios skipped | 0 |

## File Results

### Successful Files

| File | Module | Duration | Scan hits |
|---|---|---:|---:|
| `lib/src/french/NounFre.gf` | `NounFre` | 0.811 s | 0 |

## Scenario Results

None.

## Regression Comparison

No compatible baseline was available.

## Artifacts

| Role | Path |
|---|---|
| Machine summary | [summary.json](summary.json) |
| Human summary | `summary.md` |
| AI packet | [AI_READY.md](AI_READY.md) |
| Manifest | [manifest.json](manifest.json) |
```

---

# 28. Partial/error example

```markdown
# GF Wordbench Audit Summary

## Run Summary

| Field | Value |
|---|---|
| Run ID | `20260722_183100` |
| GF Wordbench | `1.0.0` |
| Project | `fre` — French |
| Mode | `diagnostic` |
| Started | `2026-07-22T18:31:00Z` |
| Finished | `2026-07-22T18:31:02Z` |
| Duration | 2.004 s |
| GF version | Unknown |

## Outcome

**Overall status: `ERROR`**

GF Wordbench could not launch the configured GF executable. File and scenario validation did not start.

## File Results

None.

## Scenario Results

None.

## Regression Comparison

No comparison was performed because the current run did not produce comparable subject results.

## Artifacts

| Role | Path |
|---|---|
| Machine summary | [summary.json](summary.json) |
| Human summary | `summary.md` |
| Master log | [raw/master.log](raw/master.log) |

## Warnings

- GF executable: `C:/tools/gf.exe`
- Launch error: file not found
```

---

# 29. Current writer compatibility

The inherited writer currently emits:

```text
# GF Audit Summary
## Run
## Totals
## Direct failures
## Downstream failures
## Ambiguous failures
## Successful files
## Top errors
## Heuristic scan notes
## Changes since previous run
## Detail files
```

It already has useful properties:

- derives content from `RunResult`;
- separates direct, downstream, and ambiguous failures;
- lists successful and skipped files;
- displays scan findings separately;
- renders regression entries;
- lists evidence paths;
- uses deterministic file sorting;
- uses canonical regression severity order.

The final writer must retain those useful behaviors while migrating to the final soft schema.

---

# 30. Current-to-final migration

## 30.1 Heading changes

```text
# GF Audit Summary
->
# GF Wordbench Audit Summary
```

```text
## Run
->
## Run Summary
```

```text
## Totals
->
part of ## Outcome
```

```text
## Changes since previous run
->
## Regression Comparison
```

```text
## Detail files
->
integrated evidence links under File Results and Artifacts
```

## 30.2 Failure-section changes

Current separate top-level headings:

```text
Direct failures
Downstream failures
Ambiguous failures
Successful files
Skipped files
Excluded or noise files
```

become subsections of:

```text
## File Results
```

## 30.3 Scenario section

Add required:

```text
## Scenario Results
```

even when no scenarios ran.

## 30.4 Artifact section

Add required:

```text
## Artifacts
```

with run-relative navigation.

## 30.5 Overall status

Add an explicit canonical overall status in:

```text
## Outcome
```

The final report must not force readers to infer success from counts.

## 30.6 Top-error model

The inherited writer expects a mapping:

```text
message -> count
```

The final model uses structured top-error entries:

```text
error_kind
message
count
```

The writer must support migration input but render the canonical structured model.

## 30.7 Diff model

The inherited writer uses:

```text
file_path
```

The final model uses:

```text
subject_kind
subject_id
```

The writer accepts legacy file entries during migration and renders generalized entries.

## 30.8 Paths

The inherited writer may show absolute paths.

The final writer should prefer:

- project-relative source paths;
- run-relative artifact paths;
- absolute environment paths only in the run summary.

---

# 31. Suggested final builder structure

```python
def build_summary_md(run_result: RunResult) -> str:
    validate_summary_report_input(run_result)

    sections = [
        build_title(),
        build_run_summary(run_result),
        build_outcome(run_result),
    ]

    if should_render_release_gates(run_result):
        sections.append(build_release_gates(run_result))

    sections.extend(
        [
            build_file_results(run_result),
            build_scenario_results(run_result),
        ]
    )

    if run_result.top_errors:
        sections.append(build_top_errors(run_result))

    if has_scan_findings(run_result):
        sections.append(build_static_scan_notes(run_result))

    sections.extend(
        [
            build_regression_comparison(run_result),
            build_artifacts(run_result),
        ]
    )

    if run_result.warnings:
        sections.append(build_warnings(run_result))

    return join_sections(sections)
```

Private helper names may differ.

Section identity, ordering, and source ownership are normative.

---

# 32. Suggested rendering helpers

Recommended responsibilities:

```text
build_title
build_run_summary
build_outcome
build_release_gates
build_file_results
build_direct_failures
build_ambiguous_failures
build_downstream_failures
build_successful_files
build_skipped_files
build_noise_files
build_scenario_results
build_failed_scenarios
build_top_errors
build_static_scan_notes
build_regression_comparison
build_artifacts
build_warnings
render_duration
render_status
render_path
render_inline_code
escape_table_cell
safe_markdown_link
```

Avoid one monolithic writer.

Do not duplicate status logic across helpers.

---

# 33. Status rendering

## 33.1 Canonical text

Always show status in inline code:

```markdown
`OK`
`FAIL`
`ERROR`
`SKIPPED`
```

## 33.2 Icons

Emoji or symbolic icons are not canonical requirements.

A UI may decorate statuses separately.

The Markdown report should remain readable in plain text.

## 33.3 Boolean values

Use human labels:

```text
Yes
No
```

for required flags.

For exact technical fields, these may be used:

```text
true
false
```

Consistency within a table is required.

---

# 34. Error rendering

## 34.1 First error

Display one concise normalized first error.

## 34.2 Multiline diagnostics

Do not place full multiline diagnostics in a table.

Use:

```markdown
<details>
<summary>Diagnostic excerpt</summary>

```text
bounded excerpt
```

</details>
```

only when the report policy allows excerpts.

The default summary report should normally link to raw evidence instead.

## 34.3 Truncation

When text is truncated:

```text
… [truncated; see raw evidence]
```

## 34.4 Secret review

Do not include bounded raw excerpts if they may expose project secrets and no redaction policy is active.

---

# 35. Artifact link policy

## 35.1 Existing path

Create a Markdown link only when the target exists at writer time or is a canonical artifact expected to be written later in the same finalization sequence.

## 35.2 Missing target

Render:

```text
Missing: `path`
```

## 35.3 Directory links

Directory links are viewer-dependent.

Provide both:

```markdown
[details/](details/) — `details/`
```

when useful.

## 35.4 External absolute paths

Do not create `file://` links by default.

Render the path as inline code.

## 35.5 Link labels

Use semantic labels:

```text
stdout
stderr
scan
details
normalized output
gold
diff
manifest
```

not:

```text
click here
```

---

# 36. Large report controls

## 36.1 Need

Diagnostic runs may contain hundreds of files and scenarios.

## 36.2 Bounded human report

The report may bound low-priority lists.

Recommended defaults:

```text
direct failures: all
ambiguous failures: all
downstream failures: first 100 with explicit truncation
errored files: all
failed scenarios: all
successful files: first 100 with explicit truncation
top errors: first 20
unchanged diff entries: omit unless detailed mode
scan notes: first 100 with explicit truncation
```

## 36.3 No hidden truncation

Every bounded list states:

```text
Showing <shown> of <total>.
```

## 36.4 Complete data

Point to:

```text
summary.json
```

for complete structured data.

## 36.5 Configuration

Display limits may be framework constants or report options.

They must not change validation semantics.

---

# 37. Deterministic output

Equivalent `RunResult` content must produce equivalent report content except for values explicitly present in the model, such as:

- timestamps;
- run ID;
- durations;
- paths.

Do not include:

- current rendering time unless persisted in `RunResult`;
- random identifiers;
- unordered set iteration;
- environment values not in resolved configuration;
- platform-dependent separators for canonical project/run paths.

---

# 38. Accessibility and readability

The report should:

- use descriptive headings;
- avoid heading-level jumps;
- include text labels for statuses;
- avoid color-only meaning;
- keep tables narrow;
- use lists for complex nested data;
- use meaningful link labels;
- avoid extremely long inline code spans where a wrapped bullet is clearer;
- keep one blank line between Markdown blocks.

---

# 39. Localization

Canonical reports are written in English.

Reasons:

- shared status vocabulary;
- stable documentation;
- reproducible test fixtures;
- cross-team issue handling;
- AI interoperability.

A future localized report must:

- preserve canonical machine values;
- identify locale;
- have separate golden fixtures;
- not alter `summary.json`;
- not replace the canonical English report without explicit policy.

---

# 40. Security and privacy

## 40.1 Sensitive content

Reports may expose:

- project paths;
- usernames inside paths;
- source filenames;
- diagnostics;
- language examples;
- GF versions;
- project structure.

## 40.2 Secrets

The report must not include:

- passwords;
- tokens;
- private keys;
- complete environment dumps;
- authentication cookies;
- secret command arguments.

## 40.3 Markdown injection

Escape untrusted content.

## 40.4 Sharing

Review `summary.md` before posting it publicly.

## 40.5 Raw evidence

Do not inline full raw logs merely for convenience.

---

# 41. Manifest integration

`summary.md` is listed in:

```text
manifest.json
```

Recommended manifest role:

```text
summary_markdown
```

The manifest records:

- path;
- size;
- SHA-256;
- media type;
- writer identity;
- required flag.

Recommended media type:

```text
text/markdown; charset=utf-8
```

The Markdown writer does not write or update the manifest.

---

# 42. Release requirements

In release mode, `summary.md` is required unless the release policy explicitly marks human reports optional.

A release report must include:

```text
Run Summary
Outcome
Release Gates
File Results
Scenario Results
Regression Comparison
Artifacts
```

It must clearly identify:

- release status;
- required gate failures;
- produced PGF artifacts;
- manifest state;
- required scenario failures;
- gold mismatches.

---

# 43. Test requirements

Recommended test structure:

```text
tests/reports/
├── test_summary_md_title.py
├── test_summary_md_required_sections.py
├── test_summary_md_run_summary.py
├── test_summary_md_outcome.py
├── test_summary_md_release_gates.py
├── test_summary_md_files.py
├── test_summary_md_scenarios.py
├── test_summary_md_top_errors.py
├── test_summary_md_scans.py
├── test_summary_md_regression.py
├── test_summary_md_artifacts.py
├── test_summary_md_warnings.py
├── test_summary_md_markdown_safety.py
├── test_summary_md_determinism.py
├── test_summary_md_large_run.py
├── test_summary_md_partial_run.py
└── test_summary_md_legacy_compatibility.py
```

## 43.1 Identity tests

Verify:

```text
path = summary.md
UTF-8
final newline
first heading = # GF Wordbench Audit Summary
```

## 43.2 Required-section tests

Verify exact top-level required order.

## 43.3 Source tests

Verify the writer:

- consumes `RunResult`;
- does not launch GF;
- does not invoke scanner;
- does not run diff;
- does not compare gold;
- does not mutate input.

## 43.4 Outcome tests

Verify:

- `OK`;
- `FAIL`;
- `ERROR`;
- count consistency;
- main blockers;
- no blockers on successful run.

## 43.5 File tests

Verify:

- direct;
- ambiguous;
- downstream;
- error;
- skipped;
- successful;
- noise;
- blocker list;
- evidence links;
- no duplicate subject rendering.

## 43.6 Scenario tests

Verify:

- no scenarios;
- all successful;
- required failure;
- optional failure;
- timeout;
- marker failure;
- gold match;
- gold mismatch;
- missing gold;
- artifact paths;
- declared order.

## 43.7 Regression tests

Verify:

- no baseline;
- disabled;
- regressed;
- new;
- improved;
- removed;
- meaningful unchanged detail;
- generalized subject;
- legacy file-only entry;
- canonical ordering.

## 43.8 Safety tests

Use values containing:

```text
`
|
[
]
<
>
&
newlines
ANSI escapes
Unicode
```

Verify valid readable Markdown and no active raw HTML.

## 43.9 Large-run tests

Verify:

- deterministic bounds;
- explicit truncation counts;
- complete high-priority failures;
- link to `summary.json`.

## 43.10 Determinism tests

Equivalent shuffled input collections must render canonical equivalent output where the model contract defines order-independent data.

## 43.11 Atomic-write tests

Verify failed replacement does not destroy a prior valid report.

---

# 44. Golden report fixtures

Markdown report tests may use golden files.

Rules:

- golden fixtures contain no machine-specific absolute paths unless the test targets path rendering;
- timestamps and run IDs are fixed;
- ordering is deterministic;
- updates require explicit review;
- a generic report change must not silently update all goldens;
- fixtures cover successful, failing, error, scenario, release, and legacy cases.

Suggested fixtures:

```text
tests/fixtures/reports/summary_ok.md
tests/fixtures/reports/summary_fail.md
tests/fixtures/reports/summary_error.md
tests/fixtures/reports/summary_release.md
tests/fixtures/reports/summary_scenarios.md
tests/fixtures/reports/summary_large.md
tests/fixtures/reports/summary_legacy.md
```

---

# 45. Contract checker

Suggested command:

```text
gf-wordbench reports check <run-dir>
```

Checks:

```text
summary.md exists
UTF-8 decode succeeds
first heading is canonical
required headings exist
required heading order is valid
summary.json exists
run ID agrees
overall status agrees
file counts agree
scenario counts agree
direct/downstream/ambiguous counts agree
artifact paths are valid
no forbidden legacy heading is emitted
manifest entry agrees when available
```

The checker must use `summary.json` as truth.

It must not treat Markdown prose as a replacement schema.

---

# 46. Anti-drift indicators

Probable drift exists when:

- the title reverts to `GF Audit Summary`;
- a required top-level section disappears;
- `summary.md` becomes a diff-loader input;
- report code reruns validation;
- report code reclassifies failures;
- direct, ambiguous, and downstream failures are merged;
- scenario failures are omitted;
- a zero-exit incomplete scenario is shown as successful;
- gold mismatch is hidden;
- overall status is inferred from prose;
- counts disagree with `RunResult`;
- legacy modes are emitted canonically;
- top errors are regrouped differently from `RunResult`;
- paths use inconsistent separators;
- report order depends on set or dictionary accidents;
- raw logs are inlined without bounds;
- downstream errors duplicate entire root diagnostics;
- an absent baseline is shown as a regression failure;
- a missing artifact receives a fake link;
- report writing mutates `RunResult`;
- writer failure prevents unrelated report writers from running;
- Markdown is parsed to migrate historical runs;
- required heading changes without soft-schema review.

Any indicator requires coordinated review.

---

# 47. Change control

A report-contract change must identify:

```text
Soft-schema version:
Current heading or field:
New heading or field:
Required or optional:
Source model field:
Ordering impact:
CLI impact:
GUI impact:
Documentation impact:
Golden-fixture impact:
Backward compatibility:
Migration:
Tests:
```

Required checklist:

```text
[ ] report_md.py updated
[ ] RunResult reviewed
[ ] summary.json schema reviewed
[ ] persisted-schema lock reviewed
[ ] interfile lock reviewed
[ ] documentation map updated
[ ] GUI open-report behavior reviewed
[ ] CLI output reviewed
[ ] manifest role reviewed
[ ] golden fixtures updated explicitly
[ ] required-section tests updated
[ ] legacy compatibility tested
[ ] security/privacy impact reviewed
```

---

# 48. Compatibility policy

## 48.1 Minor soft-schema change

May:

- add optional subsection;
- add optional table column;
- improve wording;
- add safe artifact links;
- add optional warnings;
- add bounded display metadata.

Must not:

- remove required headings;
- change required heading meanings;
- make Markdown machine-authoritative;
- change canonical status meanings.

## 48.2 Major soft-schema change

Required for:

- removing a required section;
- renaming a required section;
- changing first heading;
- changing core section meaning;
- replacing subject identities;
- making the report serve a new authoritative role.

## 48.3 Reader compatibility

Humans may read older reports.

Automated verification may recognize older soft schemas only to report compatibility.

Automation must use `summary.json` for actual run data.

---

# 49. Implementation completion checklist

The final `summary.md` system is complete when:

```text
[ ] writer owns only summary.md
[ ] writer consumes RunResult
[ ] canonical title is emitted
[ ] all six required sections are always emitted
[ ] overall status is explicit
[ ] canonical modes are emitted
[ ] run metadata is complete
[ ] file counts are coherent
[ ] scenario counts are coherent
[ ] direct failures are prioritized
[ ] ambiguous failures remain visible
[ ] downstream blockers are listed
[ ] technical roots are labeled accurately
[ ] successful files render deterministically
[ ] skipped and noise files are represented correctly
[ ] scenario order follows project configuration
[ ] marker failures are visible
[ ] gold results are visible
[ ] release gates are visible in release mode
[ ] top errors use structured entries
[ ] scan notes remain separate
[ ] generalized regression subjects render
[ ] no-baseline state is explicit
[ ] artifacts use run-relative paths
[ ] missing artifacts are not falsely linked
[ ] Markdown control characters are safe
[ ] multiline diagnostic text is bounded
[ ] large lists declare truncation
[ ] output is UTF-8 with one final newline
[ ] writing is atomic
[ ] input models are not mutated
[ ] report failure is isolated
[ ] manifest includes summary.md
[ ] canonical and legacy tests pass
[ ] golden fixtures pass
```

---

# 50. Related documents

```text
docs/architecture/EXECUTION_FLOW.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/REGRESSION_COMPARISON.md
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
docs/reports/REPORTING_OVERVIEW.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/AI_READY_REFERENCE.md
docs/reports/RAW_LOGS_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
docs/reference/STATUS_VALUES.md
docs/reference/DIAGNOSTIC_KINDS.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
SECURITY.md
```

---

# 51. Final rule

`summary.md` is a stable human explanation of one completed or partial GF Wordbench run.

Therefore:

> Render every claim from structured evidence, keep the canonical outline stable, prioritize direct and required failures, preserve scenario and regression visibility, link to owned evidence, and never turn Markdown prose into the machine source of truth.
