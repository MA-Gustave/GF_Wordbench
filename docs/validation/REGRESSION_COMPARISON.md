# GF Wordbench — Regression Comparison

**Document ID:** `GF-WB-VALIDATION-REGRESSION-COMPARISON`  
**Status:** Normative validation specification  
**Applies to:** Comparison between finalized GF Wordbench runs  
**Primary implementation:** `app/audit/diff.py`  
**Primary input:** `run_<run-id>/summary.json`  
**Primary output:** `RunResult.diff_entries` and `summary.json::diff_entries`  
**Owner:** GF Wordbench maintainers  
**Schema dependency:** `gf-wordbench.run-summary/1.x`  
**Last structural review:** 2026-07-22  

---

## 1. Purpose

Regression comparison answers one focused question:

> What validation outcomes changed between the current run and one earlier comparable run?

It identifies:

- results that improved;
- results that regressed;
- newly observed subjects;
- removed subjects;
- results whose primary status remained unchanged;
- meaningful detail changes that occurred without a primary status transition.

The comparison is designed for:

- development feedback;
- checkpoint tracking;
- release review;
- CI summaries;
- GUI history;
- AI-assisted diagnosis;
- migration from the earlier GF audit tool.

It is not a source-control diff and it does not compare arbitrary file contents.

---

## 2. Core rule

Regression comparison consumes structured run summaries.

Canonical source:

```text
run_<run-id>/summary.json
```

The comparison must not derive machine meaning from:

```text
summary.md
AI_READY.md
top_errors.txt
master.log
ALL_LOGS.TXT
console output
GUI text
```

Human reports may display the comparison.

They are not the source of comparison truth.

---

## 3. Design goals

The comparison system must be:

- deterministic;
- explainable;
- schema-aware;
- path-stable;
- tolerant of a missing baseline;
- safe when a prior run is damaged;
- compatible with documented legacy summaries;
- independent of report prose;
- usable for files and scenarios;
- conservative when evidence is insufficient;
- small enough to remain trustworthy.

---

## 4. Non-goals

Regression comparison does not:

- compare source text line by line;
- replace Git;
- compare binary `.gfo` or `.pgf` bytes as its primary function;
- replace scenario gold comparison;
- decide whether a linguistic output is correct without project assertions;
- rerun GF;
- rescan files;
- rebuild results;
- update gold files;
- modify a prior run;
- infer project history from filenames alone;
- compare every possible performance metric;
- create a general time-series analytics platform;
- make incompatible runs appear equivalent.

A future analytics subsystem may consume run summaries, but it remains separate from this validation comparison.

---

## 5. Terminology

- **Current run**: the run being finalized.
- **Baseline run**: the earlier run selected for comparison.
- **Candidate run**: an earlier run considered during baseline discovery.
- **Comparable run**: a candidate whose identity and execution scope are compatible enough for meaningful comparison.
- **Subject**: one compared entity, such as a file, scenario, or run-level result.
- **Subject identity**: `subject_kind + subject_id`.
- **Primary status**: the canonical validation status used for transition classification.
- **Detail change**: a meaningful change that does not alter the primary status.
- **Regression**: a transition from an acceptable result to a failing or unusable result.
- **Improvement**: a transition from a failing or unusable result to an acceptable result.
- **Inventory change**: a subject becoming `new` or `removed`.
- **Legacy summary**: a supported older `summary.json` shape migrated during reading.

---

## 6. Separation from other comparison systems

## 6.1 Regression comparison versus Git diff

Regression comparison compares validation outcomes:

```text
previous status -> current status
```

Git compares repository content.

A file may:

- change in Git while validation remains unchanged;
- remain unchanged in Git while validation changes because a dependency or GF version changed.

Both forms of evidence are useful and distinct.

## 6.2 Regression comparison versus gold comparison

Gold comparison evaluates:

```text
current normalized scenario output
    versus
reviewed expected output
```

Regression comparison evaluates:

```text
current ScenarioResult
    versus
previous ScenarioResult
```

A scenario may fail gold in both runs and therefore remain `unchanged` in regression comparison.

A scenario may change from gold failure to gold success and therefore be `improved`.

## 6.3 Regression comparison versus source fingerprinting

A fingerprint answers whether source content identity changed.

Regression comparison answers whether validation outcome changed.

Fingerprint changes may enrich a diff message, but they do not define `improved` or `regressed`.

## 6.4 Regression comparison versus release gates

Release gates decide whether the current project is release-ready.

Regression comparison provides historical context.

By default, the absence of a baseline does not fail release validation.

A project may add an explicit no-regression release policy, but that policy must be separately documented and configured.

---

# 7. Execution position

Regression comparison occurs after current structured results are coherent and before final report serialization.

Canonical order:

```text
file validation
    -> file classification
    -> scenario validation
    -> release artifact checks
    -> RunResult aggregation
    -> top-error aggregation
    -> baseline discovery
    -> baseline loading
    -> compatibility check
    -> diff construction
    -> attach diff_entries to RunResult
    -> reports
    -> manifest
```

The current result remains valid when regression comparison cannot be completed.

---

# 8. Public component contract

## 8.1 Component

```text
app/audit/diff.py
```

## 8.2 Public responsibilities

The component owns:

```python
find_previous_run_dir(...)
load_previous_summary(...)
build_diff_entries(...)
```

The final implementation may refine signatures, but these logical responsibilities remain separate:

1. discover;
2. load and migrate;
3. compare.

## 8.3 Forbidden responsibilities

The diff component must not:

- launch GF;
- scan source;
- compile source;
- execute scenarios;
- write human reports;
- modify prior summaries;
- update project configuration;
- update gold files;
- choose artifact filenames outside `RunPaths`;
- reclassify file failures;
- reinterpret GF diagnostics using an independent parser.

---

# 9. Enabling comparison

## 9.1 Configuration

Regression comparison is controlled by a resolved run option logically equivalent to:

```text
diff_previous = true | false
```

## 9.2 Default

Recommended default:

```text
true
```

for checkpoint, release, and diagnostic modes.

Quick mode may enable it when a comparable target baseline can be found.

## 9.3 Disabled comparison

When disabled:

```text
diff_entries = []
```

No previous run is loaded.

Reports state that comparison was disabled only when that information is useful.

## 9.4 Explicit baseline

A future or final CLI may allow:

```text
--compare-to <run-directory-or-summary.json>
```

An explicit baseline:

- bypasses automatic discovery;
- still undergoes schema validation;
- still undergoes comparability validation;
- must not be modified;
- must be recorded in current-run metadata or comparison evidence.

Adding the persisted baseline-reference field requires coordination with `PERSISTED_SCHEMA_LOCK.md`.

---

# 10. Baseline discovery

## 10.1 Automatic discovery root

Automatic discovery searches the current run's configured output root.

Example:

```text
<out-root>/
├── run_20260720_090000/
├── run_20260721_120000/
└── run_20260722_150000/   <- current
```

## 10.2 Candidate directory

A directory is an initial candidate when:

- it is a directory;
- its name begins with `run_`;
- it is not the current run directory;
- it contains or may contain `summary.json`;
- it is ordered earlier than the current run by the run-order policy.

## 10.3 Finalized candidate

The preferred baseline must be finalized.

A run is finalized when:

- its `summary.json` is readable;
- its required summary structure is valid;
- its run identity is coherent;
- it is not marked incomplete;
- its final status is available;
- manifest requirements are satisfied when the run's schema and mode require them.

Legacy runs created before manifest support may remain eligible through compatibility policy.

## 10.4 Selection rule

Automatic selection chooses:

```text
the most recent eligible comparable earlier run
```

It must not simply choose the lexically previous directory if that directory is:

- malformed;
- incomplete;
- for another project;
- for an incompatible validation scope;
- newer than the current run by metadata;
- the current run under another path alias.

## 10.5 Current implementation baseline

The earlier implementation discovers the lexically most recent `run_*` directory whose name sorts before the current run.

The final implementation preserves compatibility with that layout while adding explicit eligibility checks.

## 10.6 No candidate

When no eligible prior run exists:

```text
diff_entries = []
```

This is not a validation error.

The current run may record:

```text
comparison_status = no_baseline
```

only if such a field is added through the persisted-schema process.

Without that field, a report may state the condition from in-memory comparison context.

---

# 11. Comparability

## 11.1 Required comparability checks

An automatic baseline must match the current run on:

```text
project identity
canonical validation mode or explicitly compatible scope
target identity when target-specific
subject identity conventions
supported summary schema
status vocabulary
```

## 11.2 Project identity

Canonical match:

```text
previous.metadata.project_id
==
current.metadata.project_id
```

Legacy runs without `project_id` may use a documented migration inference from:

- normalized project root;
- legacy project fields;
- an explicit user-selected baseline.

Inference must be visible and tested.

## 11.3 Mode compatibility

Default automatic comparison requires the same canonical mode:

```text
quick      <-> quick
checkpoint <-> checkpoint
release    <-> release
diagnostic <-> diagnostic
```

This avoids misleading comparisons such as:

```text
quick target run
versus
complete release run
```

## 11.4 Legacy modes

Migration aliases:

```text
file -> quick
all  -> diagnostic
```

Aliases are normalized before comparability checks.

## 11.5 Quick target compatibility

Two quick runs are automatically comparable only when they target the same stable target identity.

Canonical target identity is project-relative.

## 11.6 Checkpoint compatibility

Two checkpoint runs should compare the same checkpoint scope.

Until an explicit checkpoint ID is persisted, automatic comparison may require equivalent selected subject sets or an explicit baseline.

## 11.7 Release compatibility

Release runs are comparable when:

- project ID matches;
- mode is `release`;
- summary schema is supported;
- required status semantics are compatible.

Changes to project release requirements must be surfaced as context, not silently ignored.

## 11.8 Diagnostic compatibility

Diagnostic runs are comparable when project ID and canonical mode match.

Newly added optional diagnostics appear as `new`.

Removed diagnostics appear as `removed`.

## 11.9 GF version difference

Different GF versions do not automatically make runs incomparable.

The comparison must disclose the version change.

A version change may explain outcome changes but does not erase them.

## 11.10 Normalization-version difference

Scenario output comparisons across different normalization versions require caution.

Scenario primary statuses may still be compared.

Gold-detail comparison must be marked as potentially incompatible when normalization meaning changed.

## 11.11 Incompatible baseline

An automatically discovered incompatible candidate is skipped and discovery continues to older candidates.

An explicitly selected incompatible baseline produces a clear comparison error or requires an explicit force policy.

It must not silently produce authoritative diff entries.

---

# 12. Baseline loading

## 12.1 Accepted input

The loader accepts:

```text
path to summary.json
```

or:

```text
path to a run directory containing summary.json
```

## 12.2 Canonical encoding

```text
UTF-8 JSON
```

## 12.3 Root type

The JSON root must be an object.

## 12.4 Supported forms

The loader supports:

- canonical `gf-wordbench.run-summary/1.x`;
- the documented unversioned nested summary;
- the documented older flat summary;
- supported legacy artifact aliases.

## 12.5 Legacy migration

Legacy loading may normalize:

```text
mode=file -> quick
mode=all -> diagnostic
ai_brief_path -> artifacts.ai_ready
file_path -> subject_id for legacy DiffEntry
legacy totals -> canonical totals
absolute project paths -> project-relative paths when safely resolvable
```

## 12.6 Read-only behavior

Loading a baseline must not rewrite:

- `summary.json`;
- its run directory;
- its manifest;
- its reports;
- its artifacts.

Migration occurs in memory unless an explicit migration command is invoked.

## 12.7 Invalid summary

An invalid automatically discovered summary:

- is skipped;
- creates a current-run warning;
- does not corrupt current results;
- does not become the comparison source.

If all candidates are invalid:

```text
diff_entries = []
```

## 12.8 Unsupported schema

An unsupported major schema is not loaded as if compatible.

The loader may report:

```text
comparison unavailable: unsupported baseline schema
```

---

# 13. Subject model

## 13.1 Canonical identity

Every diff subject is identified by:

```text
subject_kind + subject_id
```

## 13.2 Subject kinds

Canonical values:

```text
file
scenario
run
```

## 13.3 File subject ID

Canonical file identity:

```text
normalized project-relative path using /
```

Example:

```text
lib/src/french/GrammarFre.gf
```

## 13.4 Scenario subject ID

Canonical scenario identity:

```text
scenario_id
```

Example:

```text
linearize-basic
```

## 13.5 Run subject ID

Run-level comparisons use stable metric identifiers rather than the run ID.

Examples:

```text
overall-status
required-scenarios
release-pgf
```

Run-level subject IDs must be documented before use.

## 13.6 Legacy file identity

Legacy `DiffEntry.file_path` migrates to:

```text
subject_kind = file
subject_id = normalized file_path
```

## 13.7 Duplicate identity

A single run must not contain duplicate canonical identities.

Duplicate identity is a schema or result-model error.

The comparison must not choose one duplicate silently.

---

# 14. Path normalization

## 14.1 Canonical file path

Persisted canonical file paths are:

- relative to the active project root;
- separated with `/`;
- free of `.` and `..` segments;
- free of drive letters;
- stable across developer machines.

## 14.2 Legacy absolute paths

A legacy absolute path may be converted to project-relative form when:

- the previous project root is known;
- containment is verified;
- relative identity is unambiguous.

## 14.3 Case policy

Path case comparison follows the project identity policy.

Recommended canonical policy:

- preserve original path case for display;
- use normalized comparison keys;
- account for case-insensitive Windows filesystems;
- avoid collapsing two legitimately distinct case-sensitive paths without warning.

## 14.4 Separators

Input may contain:

```text
\
/
```

Canonical comparison key uses:

```text
/
```

## 14.5 Symlinks

Persisted identity is logical project-relative identity, not a machine-specific resolved symlink target.

Security containment remains the responsibility of path validation.

## 14.6 Rename behavior

Without an explicit rename map:

```text
old path -> removed
new path -> new
```

Regression comparison does not guess renames from hashes.

This avoids false identity merges.

A report may note equal fingerprints as a possible rename, but `change_kind` remains canonical.

---

# 15. Primary statuses

## 15.1 Subject validation statuses

Canonical statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

## 15.2 Run overall statuses

Canonical run statuses:

```text
OK
FAIL
ERROR
```

## 15.3 Meaning

- `OK`: required validation passed.
- `FAIL`: validation executed sufficiently and a criterion failed.
- `ERROR`: validation could not execute or be interpreted reliably.
- `SKIPPED`: subject was intentionally not executed.

## 15.4 Empty status

Canonical v1 `DiffEntry` should use `null` for a missing side if the schema is revised accordingly.

The locked v1 example currently uses status strings.

During migration compatibility, an absent previous or current subject may be represented internally by no result and serialized according to the active schema.

Legacy empty strings are accepted only for migration.

## 15.5 No status invention

The comparison component must not create new validation statuses.

---

# 16. Change kinds

Canonical values:

```text
unchanged
improved
regressed
new
removed
```

No other value may be emitted without a schema change.

---

# 17. Transition semantics

## 17.1 Conservative principle

Only clear status transitions become `improved` or `regressed`.

Inventory changes remain `new` or `removed`.

Ambiguous transitions remain `unchanged` with a detail message unless a documented transition rule applies.

## 17.2 Canonical transition matrix

For subjects present in both runs:

| Previous | Current | Change kind |
|---|---|---|
| `OK` | `OK` | `unchanged` |
| `OK` | `FAIL` | `regressed` |
| `OK` | `ERROR` | `regressed` |
| `OK` | `SKIPPED` | `regressed` when previously required; otherwise `unchanged` with detail |
| `FAIL` | `OK` | `improved` |
| `FAIL` | `FAIL` | `unchanged` |
| `FAIL` | `ERROR` | `regressed` |
| `FAIL` | `SKIPPED` | `unchanged` with unresolved detail |
| `ERROR` | `OK` | `improved` |
| `ERROR` | `FAIL` | `improved` only when the validation now executes reliably; otherwise `unchanged` with detail |
| `ERROR` | `ERROR` | `unchanged` |
| `ERROR` | `SKIPPED` | `unchanged` with unresolved detail |
| `SKIPPED` | `OK` | `improved` only when the subject is required in both scopes; otherwise `unchanged` with detail |
| `SKIPPED` | `FAIL` | `regressed` only when newly required and comparable; otherwise `unchanged` with detail |
| `SKIPPED` | `ERROR` | `regressed` only when newly required and comparable; otherwise `unchanged` with detail |
| `SKIPPED` | `SKIPPED` | `unchanged` |

## 17.3 Required flag context

Scenario transitions involving `SKIPPED` require the previous and current `required` flags.

The comparison must not label an optional unselected scenario as a regression merely because another run selected it.

## 17.4 Baseline implementation compatibility

The original implementation defines the minimal transitions:

```text
FAIL -> OK = improved
OK -> FAIL = regressed
```

The final implementation extends this safely to canonical `ERROR` and `SKIPPED` states while preserving the original cases.

## 17.5 Same status, changed meaning

The primary `change_kind` remains `unchanged` when status is the same.

The message may report:

- error kind changed;
- first error changed;
- diagnostic class changed;
- blocker set changed;
- gold mismatch changed;
- required flag changed;
- source fingerprint changed;
- GF version changed;
- normalization version changed.

`unchanged` means the primary validation status is unchanged, not that every detail is identical.

---

# 18. New subjects

## 18.1 Definition

A subject is `new` when:

```text
absent in baseline
present in current run
```

## 18.2 Meaning

`new` is an inventory change.

It is not automatically an improvement or regression.

Examples:

- new file with `OK`;
- new file with `FAIL`;
- newly registered scenario;
- newly required release gate.

## 18.3 Message

The message must include the current status.

Examples:

```text
New file passes validation.
New required scenario fails.
New optional scenario was skipped.
```

## 18.4 Release impact

A new required failing subject affects current release status through normal validation gates.

The `new` change kind does not need to duplicate that gate logic.

---

# 19. Removed subjects

## 19.1 Definition

A subject is `removed` when:

```text
present in baseline
absent in current run
```

## 19.2 Meaning

`removed` is an inventory change.

It may mean:

- intentional deletion;
- rename;
- changed selection scope;
- removed scenario registration;
- configuration drift;
- accidental omission.

## 19.3 Comparability safeguard

Before reporting `removed`, the runs must be scope-compatible.

Otherwise broad differences in selected subjects could create false removals.

## 19.4 Message

The message includes the previous status.

Example:

```text
Removed file; previous status was OK.
```

## 19.5 Release impact

Removing a required file or scenario is handled by project configuration and release gates.

Regression comparison reports the inventory change but does not independently decide project correctness.

---

# 20. File comparison

## 20.1 Primary fields

File transition classification uses:

```text
status
```

## 20.2 Detail fields

Messages may compare:

```text
diagnostic_class
is_direct
blocked_by
compile_summary.error_kind
compile_summary.first_error
compile_summary.timed_out
compile_summary.exit_code
fingerprint.hash
scan_counts
```

## 20.3 Detail priority

Recommended detail-message priority:

1. primary status transition;
2. error kind changed;
3. direct/downstream class changed;
4. blocker roots changed;
5. timeout state changed;
6. first error changed;
7. source fingerprint changed;
8. scan findings changed.

A message should remain concise.

Detailed field-by-field evidence remains in the two summaries.

## 20.4 Fingerprint use

Fingerprint equality may support:

```text
same source, different validation outcome
```

This can indicate:

- dependency change;
- GF version change;
- configuration change;
- environment change.

Fingerprint inequality may support:

```text
source changed
```

It does not prove causality.

## 20.5 Scan-count changes

Static scan counts are secondary details.

A scan-count change does not independently redefine file compile status.

## 20.6 Direct/downstream transition

Examples:

```text
FAIL/direct -> FAIL/downstream
FAIL/downstream -> FAIL/direct
```

Primary change kind:

```text
unchanged
```

Detail message reports the causal-class change.

This preserves the distinction between status and diagnosis.

---

# 21. Scenario comparison

## 21.1 Primary identity

```text
scenario_id
```

## 21.2 Primary field

```text
status
```

## 21.3 Detail fields

Messages may compare:

```text
required
execution_state
error_kind
diagnostic_class
gold_match
normalization_version
script_hash
timed_out
section completion
produced artifact set
```

## 21.4 Gold transition examples

| Previous | Current | Primary result |
|---|---|---|
| Gold matched | Gold mismatched | normally `regressed` through `OK -> FAIL` |
| Gold mismatched | Gold matched | normally `improved` through `FAIL -> OK` |
| Both mismatched, output changed | `unchanged`, detail changed |
| No gold in either run | compare other assertions |
| Gold policy added | scenario may be `new` or detail changed depending on identity and scope |

## 21.5 Required flag change

A scenario changing from optional to required is a material detail.

If its status remains `OK`:

```text
change_kind = unchanged
message = required flag changed: false -> true
```

If it is now required and fails, current validation and release gates handle the failure.

## 21.6 Script hash change

A changed `.gfs` script hash is useful context.

It does not create a separate change kind.

## 21.7 Normalization-version change

A changed normalization version must be disclosed.

Exact output-detail comparison may be considered non-equivalent, but primary status transition remains reportable.

---

# 22. Run-level comparison

## 22.1 Purpose

Run-level entries summarize a small number of stable outcomes.

They must not duplicate every total.

## 22.2 Recommended run subjects

```text
overall-status
release-pgf
required-scenarios
```

## 22.3 Overall status

Example:

```json
{
  "subject_kind": "run",
  "subject_id": "overall-status",
  "previous_status": "OK",
  "current_status": "FAIL",
  "change_kind": "regressed",
  "message": "Overall required validation regressed."
}
```

## 22.4 Count changes

Counts may be reported in summaries, but they should not generate separate `DiffEntry` records for every integer by default.

Avoid noisy subjects such as:

```text
files_seen
files_included
files_excluded
duration_ms
```

## 22.5 Duration

Duration is not a validation regression in this subsystem.

Performance regression analysis requires a separate policy with repeatability controls.

## 22.6 GF version

GF version change is comparison context.

It is not a `DiffEntry` subject unless a future policy explicitly defines one.

---

# 23. DiffEntry schema

Canonical persisted structure:

```json
{
  "subject_kind": "file",
  "subject_id": "lib/src/french/GrammarFre.gf",
  "previous_status": "FAIL",
  "current_status": "OK",
  "change_kind": "improved",
  "message": "Compilation now succeeds."
}
```

## 23.1 Required fields

```text
subject_kind
subject_id
previous_status
current_status
change_kind
message
```

## 23.2 Legacy structure

Legacy entries may use:

```json
{
  "file_path": "lib/src/albanian/GrammarSqi.gf",
  "previous_status": "FAIL",
  "current_status": "OK",
  "change_kind": "improved",
  "message": "..."
}
```

Migration:

```text
subject_kind = file
subject_id = file_path
```

## 23.3 Message role

`message` is human-readable context.

Consumers must use structured fields for logic.

They must not parse `message` to recover:

- subject identity;
- statuses;
- change kind.

## 23.4 Extension policy

New optional fields require a compatible schema update.

Possible future fields:

```text
detail_changes
baseline_run_id
current_run_id
comparison_confidence
```

They must not be added ad hoc.

---

# 24. Deterministic ordering

Canonical severity order:

```text
regressed
new
improved
removed
unchanged
```

Within one change kind:

```text
subject_kind order
then normalized subject_id
```

Recommended subject-kind order:

```text
run
file
scenario
```

A project may display files before scenarios in a human report, but persisted canonical ordering must remain documented and deterministic.

No ordering may depend on:

- dictionary insertion accidents;
- filesystem enumeration;
- locale-specific collation;
- hash iteration order.

---

# 25. Message construction

## 25.1 Requirements

Messages must be:

- deterministic;
- concise;
- factual;
- based on structured evidence;
- free of unsupported causal claims.

## 25.2 Examples

```text
Status changed: FAIL -> OK.
Status changed: OK -> ERROR.
New scenario with status FAIL.
Removed file; previous status was OK.
Status unchanged at FAIL; error kind changed: TYPE -> SYNTAX.
Status unchanged at FAIL; diagnostic class changed: downstream -> direct.
Status unchanged at OK; source fingerprint changed.
```

## 25.3 Prohibited message claims

Do not write:

```text
Fixed by the latest code.
GF caused the regression.
This file was renamed.
The new grammar is better.
The dependency definitely caused the failure.
```

unless the structured evidence explicitly proves the claim.

## 25.4 Error text

Full raw GF errors should not be duplicated into every message.

Use concise summaries and preserve raw evidence paths elsewhere.

---

# 26. Comparison outcome

## 26.1 Successful comparison

A successful comparison may produce:

```text
zero or more DiffEntry records
```

Zero entries can mean:

- no comparable subjects;
- an empty equivalent scope;
- comparison disabled;
- no baseline;
- identical subject inventories with filtering configured to omit unchanged entries.

The implementation and report must distinguish these conditions internally where necessary.

## 26.2 Filtering unchanged entries

Canonical `summary.json` may retain all entries, including `unchanged`.

A UI or human report may hide unchanged entries by default.

Filtering display must not mutate stored diff data.

## 26.3 Comparison warning

Warnings may include:

```text
baseline used legacy schema
GF version changed
normalization version changed
baseline manifest unavailable
candidate run skipped as incompatible
detail comparison partially unavailable
```

Warnings do not automatically change validation status.

## 26.4 Comparison error

Comparison errors include:

```text
explicit baseline unreadable
unsupported explicit baseline schema
duplicate subject identity
invalid canonical path identity
corrupt required comparison data
```

By default, they do not invalidate current language-validation results.

Strict CI may choose to fail the command when an explicitly required comparison cannot run.

---

# 27. Release and CI policy

## 27.1 Informational default

Regression comparison is informational by default.

Current validation truth remains primary.

## 27.2 Optional no-regression gate

A project or CI policy may require:

```text
no regressed required subjects
```

Such a gate must define:

- eligible subject kinds;
- required versus optional behavior;
- handling of `ERROR`;
- handling of `SKIPPED`;
- handling of `new`;
- handling of `removed`;
- baseline selection;
- baseline compatibility;
- behavior when no baseline exists.

## 27.3 Recommended release gate

Balanced recommendation:

```text
fail release comparison gate when:
  a required file or required scenario is regressed
  and a compatible finalized release baseline exists
```

Do not fail solely because:

- no prior release exists;
- an optional diagnostic regressed;
- a new passing subject appears;
- an intentionally removed subject appears.

## 27.4 CI explicit baseline

CI should prefer an explicit known baseline artifact when deterministic release comparison is required.

Automatic "previous directory" discovery is more suitable for local development history.

## 27.5 Branch awareness

GF Wordbench does not infer Git branches from run directories.

CI is responsible for supplying the intended baseline when branch context matters.

---

# 28. Failure resilience

## 28.1 Missing output root

No baseline is available.

Return an empty diff.

## 28.2 Missing summary

Skip the candidate.

## 28.3 Invalid JSON

Skip automatic candidate and record warning.

## 28.4 Invalid previous result

Do not mutate the current result.

## 28.5 Diff algorithm exception

The orchestrator:

- records a warning;
- keeps `diff_entries = []`;
- continues report generation;
- preserves current validation status unless comparison was explicitly required.

## 28.6 Partial current run

A partial current run may be compared only when its structured results are coherent.

The diff must not compare uninitialized placeholders as real statuses.

## 28.7 Cancelled current run

A cancelled run may produce historical context, but reports must clearly identify it as partial.

It must not be selected automatically as a future finalized baseline unless finalization policy explicitly permits partial baselines.

---

# 29. Security and integrity

## 29.1 Read-only baseline

The baseline is opened read-only.

## 29.2 Path containment

Automatic discovery remains inside the configured output root.

Explicit baseline paths undergo normal path and permission validation.

## 29.3 Symlinks and junctions

Strict mode should reject a baseline path that escapes the approved root through:

- symlink;
- junction;
- reparse point.

Explicit external baselines require deliberate policy.

## 29.4 Untrusted JSON

Summary loading uses safe JSON parsing.

No arbitrary object deserialization is permitted.

## 29.5 Resource limits

A baseline summary should have a reasonable size limit.

A maliciously large summary must not exhaust memory.

## 29.6 Manifest verification

When a baseline includes a canonical manifest, strict comparison may verify the summary hash before loading.

Legacy runs without manifests remain usable only under legacy compatibility policy.

## 29.7 Secrets

Diff messages must not expose secrets from:

- paths;
- environment values;
- raw diagnostics;
- project data.

---

# 30. Canonical algorithm

```python
def compare_with_previous(current_run_result):
    if not current_run_result.run_config.diff_previous:
        return []

    baseline_path = resolve_explicit_baseline(current_run_result)

    if baseline_path is None:
        candidates = discover_previous_run_candidates(
            out_root=current_run_result.run_config.out_root,
            current_run_dir=current_run_result.run_paths.run_dir,
        )

        baseline_result = None
        for candidate in candidates_from_newest_to_oldest(candidates):
            loaded = load_previous_summary(candidate)
            if loaded is None:
                record_comparison_warning(candidate, "unreadable")
                continue
            if not runs_are_comparable(loaded, current_run_result):
                record_comparison_warning(candidate, "incompatible")
                continue
            baseline_result = loaded
            break
    else:
        baseline_result = load_previous_summary(baseline_path)
        require_explicit_baseline_compatibility(
            baseline_result,
            current_run_result,
        )

    if baseline_result is None:
        return []

    return build_diff_entries(
        previous_run_result=baseline_result,
        current_run_result=current_run_result,
    )
```

Core diff construction:

```python
def build_diff_entries(previous_run_result, current_run_result):
    previous_subjects = index_comparable_subjects(previous_run_result)
    current_subjects = index_comparable_subjects(current_run_result)

    entries = []

    for identity in sorted(previous_subjects.keys() | current_subjects.keys()):
        previous = previous_subjects.get(identity)
        current = current_subjects.get(identity)

        if previous is None:
            entries.append(build_new_entry(current))
        elif current is None:
            entries.append(build_removed_entry(previous))
        else:
            entries.append(build_transition_entry(previous, current))

    return sort_diff_entries(entries)
```

Private helper names may differ.

The behavior is normative.

---

# 31. Current-to-final migration

## 31.1 Existing file-only model

The earlier implementation uses:

```python
DiffEntry(
    file_path,
    previous_status,
    current_status,
    change_kind,
    message,
)
```

It compares `FileResult` maps keyed by normalized file path.

## 31.2 Final generalized model

The final model uses:

```python
DiffEntry(
    subject_kind,
    subject_id,
    previous_status,
    current_status,
    change_kind,
    message,
)
```

This supports:

- files;
- scenarios;
- selected run-level outcomes.

## 31.3 Required migration work

```text
[ ] update DiffEntry model
[ ] add legacy file_path reader
[ ] update JSON writer
[ ] update JSON loader
[ ] update Markdown report
[ ] update AI report
[ ] update GUI display
[ ] add scenario indexing
[ ] add run-level subject policy
[ ] update tests
[ ] increment schema minor version if required
```

## 31.4 Compatibility

Canonical writers must emit the generalized shape.

Readers continue accepting legacy file-only entries during the support window.

---

# 32. Reporting requirements

## 32.1 Summary JSON

`summary.json` stores canonical `diff_entries`.

## 32.2 Markdown summary

Recommended sections:

```text
Regressions
New subjects
Improvements
Removed subjects
Unchanged details
Comparison warnings
```

Empty low-value sections may be omitted or state `None`.

## 32.3 AI packet

`AI_READY.md` should prioritize:

1. regressions;
2. new failing subjects;
3. changed direct failures;
4. improvements;
5. comparison warnings.

It must link to current evidence.

It must not quote an entire previous run unnecessarily.

## 32.4 GUI

The GUI may provide filters for:

```text
regressed
new
improved
removed
unchanged
file
scenario
run
```

GUI filtering does not alter `RunResult`.

## 32.5 Console

The CLI should print concise counts rather than every unchanged entry by default.

Example:

```text
regressed: 2
new: 3
improved: 1
removed: 0
unchanged: 27
```

---

# 33. Deterministic test fixtures

Fixtures should include:

```text
baseline summary
current summary
expected diff entries
```

They should avoid machine-specific absolute paths in canonical cases.

Legacy fixtures may include Windows absolute paths to validate migration.

---

# 34. Required tests

Recommended structure:

```text
tests/regression/
├── test_baseline_discovery.py
├── test_baseline_compatibility.py
├── test_summary_loading.py
├── test_legacy_summary_loading.py
├── test_subject_identity.py
├── test_path_normalization.py
├── test_status_transitions.py
├── test_file_diff.py
├── test_scenario_diff.py
├── test_run_diff.py
├── test_detail_messages.py
├── test_diff_ordering.py
├── test_diff_resilience.py
├── test_diff_security.py
└── test_diff_reporting.py
```

## 34.1 Discovery tests

Verify:

- no output root;
- no prior runs;
- current run excluded;
- newest valid prior run selected;
- malformed newest candidate skipped;
- incompatible candidate skipped;
- incomplete run skipped;
- collision-suffixed run IDs;
- explicit baseline used.

## 34.2 Compatibility tests

Verify:

- same project and mode;
- different project;
- legacy mode alias;
- quick target mismatch;
- release versus diagnostic mismatch;
- GF version difference warning;
- normalization-version difference warning;
- unsupported schema.

## 34.3 Loading tests

Verify:

- direct `summary.json` path;
- run-directory path;
- canonical summary;
- nested legacy summary;
- flat legacy summary;
- invalid JSON;
- non-object root;
- missing file;
- unknown major schema;
- legacy `ai_brief_path`;
- legacy `file_path` diff entry.

## 34.4 Identity tests

Verify:

- project-relative path;
- Windows separator normalization;
- case policy;
- duplicate file identity;
- duplicate scenario ID;
- file and scenario with same text remain distinct;
- rename becomes removed plus new.

## 34.5 Transition tests

Verify every canonical transition in the matrix.

At minimum preserve original tests:

```text
FAIL -> OK = improved
OK -> FAIL = regressed
same status = unchanged
absent -> present = new
present -> absent = removed
```

## 34.6 File-detail tests

Verify:

- error kind changed;
- first error changed;
- diagnostic class changed;
- blocker set changed;
- timeout changed;
- fingerprint changed;
- scan counts changed;
- no unsupported causal claim.

## 34.7 Scenario tests

Verify:

- scenario added;
- scenario removed;
- gold failure to success;
- gold success to failure;
- required flag changed;
- script hash changed;
- normalization version changed;
- marker failure detail changed.

## 34.8 Ordering tests

Verify canonical order:

```text
regressed
new
improved
removed
unchanged
```

Then subject kind and subject ID.

## 34.9 Resilience tests

Verify:

- baseline parse failure leaves current result intact;
- diff exception leaves current result intact;
- report generation continues;
- comparison warning recorded;
- comparison-required policy can fail explicitly.

## 34.10 Security tests

Verify:

- output-root containment;
- symlink escape policy;
- oversized summary limit;
- no unsafe deserialization;
- baseline remains unchanged;
- manifest mismatch in strict mode.

---

# 35. Acceptance examples

## 35.1 File improvement

Previous:

```text
file GrammarFre.gf = FAIL
```

Current:

```text
file GrammarFre.gf = OK
```

Diff:

```json
{
  "subject_kind": "file",
  "subject_id": "lib/src/french/GrammarFre.gf",
  "previous_status": "FAIL",
  "current_status": "OK",
  "change_kind": "improved",
  "message": "Status changed: FAIL -> OK."
}
```

## 35.2 File regression

Previous:

```text
file LangFre.gf = OK
```

Current:

```text
file LangFre.gf = FAIL
```

Result:

```text
regressed
```

## 35.3 Same failure, different error

Previous:

```text
FAIL / TYPE
```

Current:

```text
FAIL / SYNTAX
```

Result:

```text
change_kind = unchanged
message = Status unchanged at FAIL; error kind changed: TYPE -> SYNTAX.
```

## 35.4 New failing scenario

Previous:

```text
scenario absent
```

Current:

```text
scenario parse-negation = FAIL
```

Result:

```text
change_kind = new
```

Current validation still fails through normal required-scenario logic.

## 35.5 Removed passing file

Previous:

```text
file MorphoFre.gf = OK
```

Current:

```text
file absent
```

Result:

```text
change_kind = removed
```

The comparison does not guess whether the file was renamed.

## 35.6 GF version changed

Previous:

```text
GF version A
file X = OK
```

Current:

```text
GF version B
file X = FAIL
```

Result:

```text
file X = regressed
comparison warning = GF version changed
```

The message must not state that GF version B caused the regression.

---

# 36. Performance constraints

The algorithm should be:

```text
O(P + C)
```

for indexing previous and current subjects, plus deterministic sorting:

```text
O(N log N)
```

where:

- `P` is previous subject count;
- `C` is current subject count;
- `N` is union subject count.

The implementation should not perform nested full-list comparisons.

Baseline discovery should stop after finding the newest eligible baseline.

No external process is launched.

---

# 37. Logging and observability

Recommended master-log events:

```text
diff_disabled
diff_discovery_start
diff_candidate
diff_candidate_invalid
diff_candidate_incompatible
diff_baseline_selected
diff_load_warning
diff_build_start
diff_build_done
diff_failed
```

Recommended structured context:

```text
baseline run ID
baseline summary path
baseline schema
baseline project ID
baseline mode
current run ID
entry counts by change kind
warnings
```

Do not log full baseline JSON.

---

# 38. Anti-drift rules

The following indicate regression-comparison drift:

- diff reads `summary.md`;
- GUI and CLI select different baselines;
- one caller compares absolute paths and another relative paths;
- `file_path` remains canonical after generalized subjects are implemented;
- a new change kind appears without schema update;
- status transition rules exist only inside report code;
- scenario comparison uses filename instead of scenario ID;
- same project-relative file produces two identities;
- a missing baseline becomes a validation failure by accident;
- an invalid prior run corrupts current results;
- diff generation reruns GF;
- message text is parsed by automation;
- unchanged entries are ordered nondeterministically;
- quick runs compare automatically with full diagnostic runs;
- gold comparison and run regression are conflated;
- report filtering mutates stored diff entries;
- baseline loading rewrites the baseline;
- a schema migration silently loses subject identity.

Any indicator requires coordinated review.

---

# 39. Contract-change workflow

A comparison-contract change must state:

```text
Affected subject kind:
Current identity:
New identity:
Current transition rule:
New transition rule:
Baseline selection impact:
Schema impact:
Legacy impact:
Report impact:
CI impact:
Security impact:
Migration:
Tests:
```

Required checklist:

```text
[ ] diff model reviewed
[ ] baseline discovery reviewed
[ ] summary loader reviewed
[ ] path normalization reviewed
[ ] status reference reviewed
[ ] persisted schema reviewed
[ ] interfile lock reviewed
[ ] report writers updated
[ ] GUI updated
[ ] CLI updated
[ ] legacy fixtures updated
[ ] transition tests updated
[ ] ordering tests updated
[ ] migration documented
```

---

# 40. Implementation completion checklist

The final regression-comparison system is complete when:

```text
[ ] comparison uses summary.json only
[ ] current run is excluded from discovery
[ ] newest eligible comparable baseline is selected
[ ] project identity is checked
[ ] canonical mode compatibility is checked
[ ] quick target identity is checked
[ ] malformed candidates are skipped safely
[ ] canonical schema is validated
[ ] supported legacy summaries load
[ ] canonical subject identity is implemented
[ ] file identities are project-relative
[ ] scenario identities use scenario_id
[ ] duplicate identities fail clearly
[ ] five canonical change kinds are implemented
[ ] status transition matrix is tested
[ ] original FAIL->OK and OK->FAIL behavior is preserved
[ ] detail changes do not overwrite primary status semantics
[ ] deterministic ordering is implemented
[ ] missing baseline returns empty diff
[ ] diff failure preserves current result
[ ] reports consume structured DiffEntry
[ ] automation does not parse messages
[ ] baseline is never modified
[ ] strict manifest verification is supported
[ ] no-regression gate is explicit, not implicit
[ ] unit tests pass
[ ] legacy migration tests pass
[ ] Windows path tests pass
```

---

# 41. Related documents

```text
docs/architecture/EXECUTION_FLOW.md
docs/architecture/DATA_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
docs/validation/SCENARIO_VALIDATION.md
docs/validation/RELEASE_GATES.md
docs/scenarios/GOLDEN_TESTS.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/SUMMARY_MARKDOWN_REFERENCE.md
docs/reports/AI_READY_REFERENCE.md
docs/reference/STATUS_VALUES.md
docs/reference/SCHEMA_INDEX.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
SECURITY.md
```

---

# 42. Final rule

Regression comparison is historical context built from structured validation evidence.

It must remain conservative.

Therefore:

> Compare only compatible finalized runs, identify subjects by stable canonical identity, classify only documented status transitions, preserve inventory changes as `new` or `removed`, and never let a missing or damaged baseline corrupt the current run.
