# GF Wordbench — Error Classification

**Document ID:** `GF-WB-DIAGNOSTICS-ERROR-CLASSIFICATION`  
**Status:** Normative  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\diagnostics\ERROR_CLASSIFICATION.md`  
**Applies to:** File results, scenario results, diagnostic causality, blocker relationships, aggregate diagnostic counts, and report consumption  
**Owner:** GF Wordbench maintainers  
**Contract references:** `IFC-AUDIT-008`, `IFC-AUDIT-009`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This document defines how GF Wordbench classifies validation outcomes and diagnostic causality.

Error classification converts already captured and normalized evidence into stable structured fields.

It answers four different questions:

1. **Did the validation criterion pass?**
2. **Did the external process execute normally?**
3. **What technical kind of error occurred?**
4. **Is the current subject a likely local failure, blocked by another subject, or unresolved?**

These questions MUST remain separate.

The central rule is:

> Validation status, execution state, error kind, and diagnostic class are independent dimensions and must never be collapsed into one label.

This document defines:

- canonical values;
- coherence rules;
- evidence precedence;
- direct, downstream, ambiguous, noise, and skipped classification;
- blocker resolution;
- classification order;
- deterministic behavior;
- handling of framework and process errors;
- migration from the earlier GF Audit classifier;
- tests and acceptance criteria.

---

## 2. Scope

This document governs classification of:

- selected GF source-file results;
- compile failures;
- compile execution errors;
- scenario results;
- gold mismatches;
- process timeouts;
- launch failures;
- configuration and I/O errors;
- direct and downstream relationships;
- ambiguous failures;
- explicit noise or excluded-result records;
- intentionally skipped validations;
- `blocked_by`;
- `is_direct`;
- aggregate diagnostic counts;
- report-facing classification data.

This document does not govern:

- raw GF diagnostic parsing syntax;
- static scan pattern detection;
- file selection;
- process launch implementation;
- source dependency discovery through a custom GF parser;
- report formatting;
- regression comparison;
- project-specific linguistic correctness.

---

## 3. Authority boundaries

### 3.1 Stage owners determine validation status

The stage that executes a criterion owns its primary validation status.

Examples:

- compiler owns compile execution outcome;
- scenario runner owns scenario execution outcome;
- gold comparator owns comparison outcome;
- file selector owns selection errors;
- schema validator owns schema outcome.

The classifier validates and refines causal fields. It MUST NOT silently convert a valid `ERROR` into `FAIL`, or a valid `SKIPPED` into `OK`.

### 3.2 Process runner determines execution state

The process runner owns:

```text
completed
timed_out
cancelled
launch_failed
```

The classifier consumes execution state as evidence.

### 3.3 Diagnostic parser determines error kind

The diagnostic parser or stage adapter owns normalized technical error kind.

Canonical values:

```text
OK
OTHER
TYPE
SYNTAX
INTERNAL
TIMEOUT
SCRIPT
CONFIG
IO
TOOL
```

The classifier may validate coherence but MUST NOT independently reparse raw logs with a competing rule set.

### 3.4 Classifier determines diagnostic class

The classifier owns:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

It also owns:

```text
is_direct
blocked_by
```

### 3.5 Reports are observers

Report writers consume classification.

They MUST NOT:

- rerun classification;
- infer a different root cause;
- rewrite `blocked_by`;
- treat `error_kind` as `diagnostic_class`;
- parse raw logs to override structured fields.

---

## 4. Canonical dimensions

## 4.1 Validation status

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

Meaning:

| Value | Meaning |
|---|---|
| `OK` | criterion executed and passed |
| `FAIL` | criterion executed correctly but was not satisfied |
| `ERROR` | criterion could not be executed or interpreted reliably |
| `SKIPPED` | criterion was intentionally not executed |

## 4.2 Execution state

Canonical values:

```text
completed
timed_out
cancelled
launch_failed
```

Execution state may be absent for a non-process criterion or an intentional skip.

## 4.3 Error kind

Canonical values:

```text
OK
OTHER
TYPE
SYNTAX
INTERNAL
TIMEOUT
SCRIPT
CONFIG
IO
TOOL
```

Error kind describes technical nature.

## 4.4 Diagnostic class

Canonical values:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Diagnostic class describes causal relation.

## 4.5 Blocker relationship

Canonical field:

```text
blocked_by
```

It contains stable project-relative identifiers of known blocking subjects.

## 4.6 Compatibility field

Canonical compatibility field:

```text
is_direct
```

It is derived from:

```text
diagnostic_class == "direct"
```

It MUST NOT be an independent source of truth.

---

## 5. Required separation

The following are not synonyms.

### 5.1 `FAIL` versus `direct`

`FAIL` states that a criterion failed.

`direct` states that available evidence points to the current subject as a likely local or root failure.

A failed subject may be:

```text
direct
downstream
ambiguous
```

### 5.2 `ERROR` versus `ambiguous`

`ERROR` states that execution or interpretation was unreliable.

`ambiguous` states that causality is unresolved.

Many execution errors are ambiguous, but the terms are not equivalent.

### 5.3 `TYPE` versus `direct`

`TYPE` describes a technical GF type error.

A type error is usually direct when no failed dependency is referenced, but it can be downstream when the diagnostic clearly points to another selected failing module.

### 5.4 `TIMEOUT` versus `direct`

`TIMEOUT` describes process behavior.

A timeout does not prove a source defect and MUST NOT become `direct` solely because its error kind is `TIMEOUT`.

### 5.5 `noise` versus `skipped`

`noise` means the subject is outside meaningful validation scope by policy.

`skipped` means the subject is in scope but the criterion was intentionally not executed.

---

## 6. Classification subject

A classification subject is the entity whose result is being classified.

Canonical subject kinds:

```text
file
scenario
run
```

The v1 file classifier operates primarily on:

```text
FileResult
```

The same causal principles apply to `ScenarioResult`.

Run-level status is aggregated and is not normally assigned a direct/downstream class.

---

## 7. Input evidence

The classifier consumes structured evidence already present in result objects.

Minimum file evidence:

```text
file_path
module_name
status
compile_summary.exit_code
compile_summary.timed_out
compile_summary.error_kind
compile_summary.first_error
compile_summary.error_detail
```

Optional evidence:

```text
execution_state
normalized diagnostic references
dependency references
artifact-check result
selection metadata
stage error metadata
existing blocked_by
```

The classifier may also consume the complete deterministic list of peer results from the same stage.

---

## 8. Evidence hierarchy

When evidence conflicts, use this precedence:

```text
1. explicit structured blocker references
2. normalized diagnostic references resolved to selected results
3. explicit self-reference or current-subject source location
4. stage-specific structured failure metadata
5. normalized error kind
6. generic first-error text
7. exit code alone
8. heuristic inference
```

Raw human-readable report prose is never classification evidence.

Static scan findings are not compile-causality evidence.

---

## 9. Strong and weak evidence

## 9.1 Strong direct evidence

Strong direct evidence includes:

- normalized diagnostic explicitly names the current file;
- normalized diagnostic explicitly names the current module;
- source location belongs to the current file;
- structured stage metadata marks the current subject as the failing provider;
- `TYPE` or `SYNTAX` error is attached to the current subject and no failed external blocker is referenced;
- a scenario assertion explicitly fails inside the current scenario rather than in a prerequisite.

## 9.2 Strong downstream evidence

Strong downstream evidence includes:

- structured blocker field points to another failing selected subject;
- normalized diagnostic references another selected subject whose status is `FAIL` or `ERROR`;
- a dependency load failure identifies another selected failed module;
- a scenario cannot run because its configured entrypoint failed;
- a release stage fails because a required earlier stage failed and no independent local failure occurred.

## 9.3 Ambiguous evidence

Ambiguous evidence includes:

- generic non-zero exit without usable diagnostic;
- only unknown external file references;
- references to successful selected subjects;
- conflicting self and external references without a reliable precedence signal;
- timeout with no identified blocker;
- launch failure;
- configuration failure not attributable to one source subject;
- internal GF failure that identifies no current source or failed dependency;
- diagnostic parser failure;
- dependency cycle with no resolvable root.

## 9.4 Weak evidence

Weak evidence MUST NOT alone establish `direct` or `downstream`.

Examples:

- module-name substring appearing in unrelated prose;
- path fragment without `.gf`;
- generic phrase such as “while compiling”;
- file order;
- previous-run classification;
- static scan hit;
- elapsed duration;
- artifact filename without current-run provenance.

---

# 10. Classification lifecycle

Classification occurs after stage execution has produced initial results.

Canonical lifecycle:

```text
stage execution
    → raw evidence preservation
    → diagnostic normalization
    → primary status assignment
    → peer-result collection
    → causal classification
    → blocker-root normalization
    → aggregate counts
    → reports
```

Classification MUST NOT occur before all peer results required for dependency comparison are available.

A quick single-file run may classify against one result only.

---

# 11. Primary status preservation

The final classifier MUST treat valid stage status as authoritative.

It may normalize only when a result is explicitly marked as provisional or legacy.

## 11.1 Canonical behavior

```python
if status in {"OK", "FAIL", "ERROR", "SKIPPED"}:
    preserve(status)
else:
    raise_or_normalize_legacy_status()
```

## 11.2 Forbidden behavior

The classifier MUST NOT:

- infer `OK` solely from `error_kind = OK`;
- infer `FAIL` for every non-zero exit without considering launch or framework error;
- convert timeout `ERROR` into `FAIL`;
- treat missing compile summary as a successful skip automatically;
- overwrite explicit scenario status with compile logic.

## 11.3 Legacy compatibility

The earlier classifier rebuilds file status from `CompileSummary`.

During migration, a compatibility adapter may normalize legacy provisional results before the canonical classifier runs.

That adapter must be separate and tested.

---

# 12. Coherence matrix

## 12.1 Status and diagnostic class

| Validation status | Allowed diagnostic classes |
|---|---|
| `OK` | `ok` |
| `FAIL` | `direct`, `downstream`, `ambiguous` |
| `ERROR` | `direct`, `downstream`, `ambiguous` |
| `SKIPPED` | `skipped`, `noise` |

`ERROR + direct` is allowed only when evidence clearly locates the error at the current subject.

Example:

```text
scenario script itself is malformed
```

An infrastructure-wide launch failure is normally:

```text
ERROR + ambiguous
```

## 12.2 Diagnostic class and fields

| Diagnostic class | `is_direct` | `blocked_by` |
|---|---:|---|
| `ok` | `false` | empty |
| `direct` | `true` | empty |
| `downstream` | `false` | non-empty |
| `ambiguous` | `false` | empty unless unresolved known blockers are retained by explicit policy |
| `noise` | `false` | empty |
| `skipped` | `false` | empty |

Canonical v1 policy:

```text
ambiguous.blocked_by = []
```

Known blockers imply `downstream`.

## 12.3 Error kind and status

| Error kind | Normal status expectation |
|---|---|
| `OK` | `OK` or legacy-compatible `SKIPPED` |
| `TYPE` | `FAIL` |
| `SYNTAX` | `FAIL` |
| `INTERNAL` | `FAIL` or `ERROR` by stage policy |
| `TIMEOUT` | `ERROR` |
| `SCRIPT` | `FAIL` or `ERROR` |
| `CONFIG` | `ERROR` |
| `IO` | `ERROR` |
| `TOOL` | `ERROR` |
| `OTHER` | `FAIL` or `ERROR` |

A mismatch must be corrected by the stage owner or reported as a model-contract error.

---

# 13. `ok`

A result is classified:

```text
diagnostic_class = ok
```

when:

```text
status = OK
```

Required fields:

```text
is_direct = false
blocked_by = []
error_kind = OK
```

A successful compile with static scan findings remains:

```text
status = OK
diagnostic_class = ok
```

Scan findings are reported independently.

---

# 14. `skipped`

A result is classified:

```text
diagnostic_class = skipped
```

when:

- the subject belongs to validation scope;
- the criterion was intentionally not executed;
- the skip reason is explicit.

Required fields:

```text
status = SKIPPED
is_direct = false
blocked_by = []
```

Examples:

- compile disabled by explicit `no_compile`;
- optional scenario omitted by mode;
- stage disabled by documented configuration.

A missing executable is not a skip.

A timeout is not a skip.

---

# 15. `noise`

A result is classified:

```text
diagnostic_class = noise
```

only when a result record is intentionally retained for an excluded or non-meaningful candidate.

Required fields:

```text
status = SKIPPED
is_direct = false
blocked_by = []
```

Examples:

- backup source file explicitly represented in a result model;
- generated copy excluded from meaningful analysis;
- out-of-scope candidate preserved for accounting.

Preferred architecture:

```text
ordinary exclusions remain ExcludedFileEntry records,
not FileResult records
```

Therefore, `noise` should be uncommon in canonical file results.

---

# 16. `direct`

A result is classified:

```text
diagnostic_class = direct
```

when the strongest available evidence points to the current subject as a likely local or root failure.

Required fields:

```text
is_direct = true
blocked_by = []
```

## 16.1 Direct does not mean blame

`direct` means:

```text
first locally evidenced failure in the observed result graph
```

It does not prove:

- the source author is at fault;
- GF has no internal bug;
- the current module is the ultimate semantic cause;
- no unselected external dependency contributed.

Reports SHOULD use:

```text
likely direct failure
```

or:

```text
directly evidenced failure
```

rather than claiming certainty.

## 16.2 Direct decision rules

A failing or error result becomes direct when:

1. no stronger failed external blocker exists; and
2. one of the following holds:
   - diagnostic explicitly identifies the current file;
   - diagnostic explicitly identifies the current module;
   - structured source location belongs to the current file;
   - stage metadata marks a local assertion or local script defect;
   - error kind is `TYPE` or `SYNTAX` and no external failed reference exists;
   - another documented high-confidence local rule matches.

## 16.3 Error kinds that may support direct classification

Strong local kinds:

```text
TYPE
SYNTAX
```

Conditional local kinds:

```text
INTERNAL
SCRIPT
OTHER
```

These conditional kinds require explicit local evidence.

## 16.4 Error kinds that do not establish direct classification alone

```text
TIMEOUT
CONFIG
IO
TOOL
```

They may be direct only when additional strong subject-local evidence exists.

Example:

```text
scenario-local input file missing
```

may be direct to that scenario if the scenario owns the file contract.

A global `gf.exe` launch failure is not direct to every selected source file.

---

# 17. `downstream`

A result is classified:

```text
diagnostic_class = downstream
```

when it failed because one or more known peer subjects failed earlier or provide a required dependency.

Required fields:

```text
is_direct = false
blocked_by = [one or more stable identifiers]
```

## 17.1 Blocker eligibility

A referenced peer may block the current subject when its status is:

```text
FAIL
ERROR
```

A peer with:

```text
OK
SKIPPED
```

does not become a blocker solely because its name appears in diagnostic text.

## 17.2 Downstream precedence

A resolved failed external blocker has priority over local-kind heuristics.

Example:

```text
current result:
  error_kind = TYPE
  diagnostic references failed GrammarX.gf
```

When the diagnostic clearly attributes failure to `GrammarX.gf`, classify:

```text
downstream
```

not automatically `direct`.

## 17.3 Self-reference exclusion

A result cannot block itself.

References resolving to the current file or module are removed from `blocked_by`.

Self-reference may support direct classification.

## 17.4 Multiple blockers

Several blockers are permitted.

Canonical order:

```text
normalized project-relative path order
```

or stable first-evidence order if the classifier contract explicitly chooses that model.

GF Wordbench v1 uses:

```text
deterministic normalized path order
```

## 17.5 Downstream chain

Example:

```text
A = direct
B = blocked by A
C = blocked by B
```

Canonical final result:

```text
A: direct,     blocked_by=[]
B: downstream, blocked_by=["A"]
C: downstream, blocked_by=["A"]
```

The classifier collapses known chains to terminal root blockers.

---

# 18. `ambiguous`

A result is classified:

```text
diagnostic_class = ambiguous
```

when failure exists but available evidence cannot establish direct or downstream causality safely.

Required fields:

```text
is_direct = false
blocked_by = []
```

Examples:

- generic non-zero exit;
- no diagnostic text;
- unknown referenced module;
- only successful peer references;
- timeout without a failed dependency;
- tool launch failure repeated across files;
- internal GF error without subject location;
- conflicting blocker evidence;
- unresolved dependency cycle;
- parser fallback classified as `OTHER`.

Ambiguous is a valid final answer.

The classifier MUST NOT force a direct root merely to simplify reports.

---

# 19. Blocker identity

Canonical blocker identifiers are project-relative POSIX paths.

Example:

```text
lib/src/example/GrammarX.gf
```

They MUST NOT be:

- localized labels;
- raw absolute machine paths in canonical persistence;
- module names when a file path is available;
- report headings;
- arbitrary diagnostic fragments.

Runtime models may use `Path` or normalized strings.

Persisted models use strings.

---

# 20. Result indexing

The classifier builds deterministic indexes.

Recommended indexes:

```python
results_by_file: dict[str, Result]
results_by_module: dict[str, Result]
failing_results_by_file: dict[str, Result]
failing_results_by_module: dict[str, Result]
```

## 20.1 Path key

Canonical conceptual normalization:

```python
Path(value).as_posix()
```

Comparison behavior should follow documented platform identity.

For persisted project-relative paths:

```text
case-preserving value
normalized comparison key
```

## 20.2 Module key

Canonical conceptual normalization:

```python
module_name.strip()
```

Comparison may use `casefold()` for Windows compatibility, but actual GF module casing remains preserved.

## 20.3 Duplicate identity

Two selected results MUST NOT share one canonical file identity.

A duplicate identity is a model or selection error.

The classifier MUST NOT silently keep the first result without reporting the inconsistency.

---

# 21. Diagnostic reference extraction

## 21.1 Preferred input

Preferred reference input is structured normalized diagnostics.

Example:

```json
{
  "referenced_files": [
    "lib/src/example/GrammarX.gf"
  ],
  "referenced_modules": [
    "GrammarX"
  ]
}
```

## 21.2 Compatibility input

During migration, references may be extracted from:

```text
first_error
error_detail
```

A compatibility regex may recognize `.gf` paths.

Conceptual pattern:

```text
<path-or-name>.gf
```

## 21.3 Extraction rules

- preserve exact candidate text for evidence;
- normalize for identity lookup;
- remove trailing punctuation;
- deduplicate;
- resolve file path before module stem fallback;
- never match arbitrary words lacking a `.gf` suffix as file paths;
- never treat a module substring as a blocker without boundary matching;
- ignore self-reference for blocker resolution;
- retain unknown references only as diagnostic evidence, not `blocked_by`.

## 21.4 Parser limitation

Text extraction is heuristic.

It MUST NOT replace structured references when structured references exist.

---

# 22. Reference resolution

For each normalized reference:

```text
1. resolve exact project-relative file identity
2. resolve normalized file identity
3. resolve module identity
4. reject self
5. inspect referenced result status
6. retain only failing or error peers as blocker candidates
```

Resolution MUST be deterministic.

When a module name maps to more than one result, the reference is ambiguous unless a file path disambiguates it.

The classifier MUST NOT choose an arbitrary duplicate module result.

---

# 23. Blocker graph

Downstream relations form a directed graph.

Conceptual edge:

```text
current subject → blocker
```

Example:

```text
LangX.gf → GrammarX.gf
GrammarX.gf → NounX.gf
```

## 23.1 Graph requirements

- nodes use stable identities;
- self-edges are removed;
- duplicate edges are removed;
- traversal is deterministic;
- cycles are detected;
- traversal is bounded;
- raw immediate references remain available in evidence.

## 23.2 Root blocker

A root blocker is a terminal blocker that is:

- classified `direct`; or
- classified `ambiguous` with no further known blocker; or
- external and unresolved under an explicit external-blocker policy.

Canonical v1 `blocked_by` prefers selected peer paths.

## 23.3 Chain collapse

Known acyclic chains collapse to roots.

The classifier must not duplicate intermediate blockers when a safe root is known.

## 23.4 Cycle handling

Example:

```text
A → B
B → A
```

A cycle without independent direct evidence cannot produce a trustworthy root.

Canonical behavior:

```text
A = ambiguous
B = ambiguous
blocked_by = []
```

A diagnostic note may record the cycle separately.

The classifier MUST NOT recurse indefinitely.

## 23.5 Mixed cycle with direct root

Example:

```text
A → B
B → A
B → C
C = direct
```

When evidence supports `C` as an independent blocker:

```text
A = downstream, blocked_by=["C"]
B = downstream, blocked_by=["C"]
C = direct
```

Cycle handling must remain deterministic.

---

# 24. Canonical classification algorithm

Conceptual algorithm:

```python
def classify_results(results):
    validate_unique_identities(results)
    preserve_primary_statuses(results)

    indexes = build_indexes(results)
    evidence_by_subject = extract_and_resolve_references(results, indexes)

    for result in deterministic_order(results):
        classify_terminal_status(result)

    for result in deterministic_order(results):
        if result.status not in {"FAIL", "ERROR"}:
            continue

        evidence = evidence_by_subject[result.identity]

        if evidence.failed_external_blockers:
            set_downstream(result, evidence.failed_external_blockers)
            continue

        if has_strong_local_evidence(result, evidence):
            set_direct(result)
            continue

        set_ambiguous(result)

    resolve_blocker_graph(results)
    enforce_field_coherence(results)
    return results
```

## 24.1 Terminal status classification

```python
if status == "OK":
    diagnostic_class = "ok"

elif status == "SKIPPED" and exclusion_policy:
    diagnostic_class = "noise"

elif status == "SKIPPED":
    diagnostic_class = "skipped"
```

## 24.2 Failure classification order

Canonical precedence:

```text
known failed external blocker
    → downstream

otherwise strong local evidence
    → direct

otherwise
    → ambiguous
```

This precedence prevents a local error-kind heuristic from hiding a known dependency failure.

---

# 25. Detailed decision table

| Status | Evidence | Class |
|---|---|---|
| `OK` | any coherent success evidence | `ok` |
| `SKIPPED` | intentionally in-scope skip | `skipped` |
| `SKIPPED` | explicitly retained exclusion/noise | `noise` |
| `FAIL` | failed selected dependency referenced | `downstream` |
| `ERROR` | failed selected prerequisite referenced | `downstream` |
| `FAIL` | self file/module explicitly referenced | `direct` |
| `FAIL` | `TYPE` or `SYNTAX`, no blocker | `direct` |
| `FAIL` | generic `OTHER`, no local evidence | `ambiguous` |
| `FAIL` | unknown external reference only | `ambiguous` |
| `ERROR` | timeout without blocker | `ambiguous` |
| `ERROR` | global launch failure | `ambiguous` |
| `ERROR` | configuration error without local owner | `ambiguous` |
| `ERROR` | malformed current scenario script | `direct` |
| `FAIL` | gold mismatch in current scenario | `direct` |
| `FAIL` | scenario blocked by failed entrypoint | `downstream` |

---

# 26. Error-kind guidance

## 26.1 `OK`

Expected classification:

```text
ok
```

When status is `SKIPPED`, legacy `error_kind = OK` does not make the result successful.

## 26.2 `TYPE`

Default high-confidence local signal.

Classification:

```text
direct
```

unless a failed external blocker is clearly referenced.

## 26.3 `SYNTAX`

Default high-confidence local signal.

Classification:

```text
direct
```

unless the syntax error is attached to another failed selected source.

## 26.4 `INTERNAL`

An internal GF or framework error is not automatically a source-local defect.

Classification:

- `downstream` when a failed dependency is identified;
- `direct` when current subject is explicitly identified as the triggering location;
- `ambiguous` otherwise.

## 26.5 `TIMEOUT`

Classification:

- `downstream` only when a known failed prerequisite caused the timeout stage not to proceed normally;
- `direct` only with additional strong subject-local evidence;
- `ambiguous` by default.

## 26.6 `SCRIPT`

For scenarios:

- malformed current `.gfs` script: `direct`;
- unsupported command caused by project scenario: `direct`;
- scenario blocked by failed grammar load: `downstream`;
- framework scenario-runner exception: `ambiguous`.

For file compilation, `SCRIPT` normally represents compatibility or framework error and is not automatically direct.

## 26.7 `CONFIG`

Classification:

- direct when configuration belongs uniquely to the current subject;
- downstream when current subject depends on another failed configured subject;
- ambiguous for global configuration errors.

## 26.8 `IO`

Classification:

- direct when current subject-owned file is missing or unreadable;
- downstream when a required failed input subject is known;
- ambiguous for output-root or global filesystem failure.

## 26.9 `TOOL`

Classification:

- direct only when a subject-specific tool contract failed;
- downstream when a prerequisite tool result is known;
- ambiguous for missing executable, unsupported global option, or launch failure.

## 26.10 `OTHER`

Classification relies entirely on references and local evidence.

Default:

```text
ambiguous
```

---

# 27. File-result rules

Canonical file result fields:

```text
file_path
module_name
status
diagnostic_class
is_direct
blocked_by
compile_summary
```

## 27.1 Successful file

```json
{
  "status": "OK",
  "diagnostic_class": "ok",
  "is_direct": false,
  "blocked_by": []
}
```

## 27.2 Direct file failure

```json
{
  "status": "FAIL",
  "diagnostic_class": "direct",
  "is_direct": true,
  "blocked_by": []
}
```

## 27.3 Downstream file failure

```json
{
  "status": "FAIL",
  "diagnostic_class": "downstream",
  "is_direct": false,
  "blocked_by": [
    "lib/src/example/GrammarX.gf"
  ]
}
```

## 27.4 Ambiguous file error

```json
{
  "status": "ERROR",
  "diagnostic_class": "ambiguous",
  "is_direct": false,
  "blocked_by": []
}
```

---

# 28. Scenario-result rules

Scenario classification follows the same causal classes.

## 28.1 Scenario success

```text
status = OK
diagnostic_class = ok
```

## 28.2 Local scenario assertion failure

Examples:

- required marker missing;
- normalized output mismatches gold;
- parse result violates assertion;
- script syntax is invalid.

Classification:

```text
status = FAIL or ERROR
diagnostic_class = direct
```

## 28.3 Scenario blocked by grammar

Example:

```text
scenario cannot import configured entrypoint
entrypoint file result is already FAIL
```

Classification:

```text
status = FAIL
diagnostic_class = downstream
blocked_by = ["<entrypoint-path>"]
```

## 28.4 Scenario timeout

Without a known prerequisite failure:

```text
status = ERROR
diagnostic_class = ambiguous
error_kind = TIMEOUT
```

## 28.5 Gold mismatch

A completed scenario whose normalized output differs from reviewed gold is:

```text
status = FAIL
diagnostic_class = direct
```

The result is direct to the scenario acceptance contract, not necessarily proof of a specific source module defect.

---

# 29. Run-level aggregation

Run-level overall status:

```text
OK
FAIL
ERROR
```

Recommended precedence:

```text
ERROR > FAIL > OK
```

Meaning:

- any required `ERROR` makes overall status `ERROR`;
- otherwise any required `FAIL` makes overall status `FAIL`;
- otherwise overall status is `OK`.

Optional scenario failures may affect overall status only according to validation-mode policy.

Run-level totals must be derived from final classified results.

---

# 30. Aggregate counts

Canonical file counts include:

```text
files_ok
files_fail
files_error
files_skipped
direct_fail
downstream_fail
ambiguous_fail
excluded_noise
```

Recommended causal counts include both `FAIL` and `ERROR` subjects when named generically:

```text
direct_count
downstream_count
ambiguous_count
```

If fields retain names such as `direct_fail`, their schema must state whether `ERROR` is included.

Final recommendation:

```text
direct_count
downstream_count
ambiguous_count
```

with separate validation-status counts.

Until schema migration, legacy `*_fail_count` fields must remain consistently defined and tested.

---

# 31. `is_direct`

`is_direct` is retained for compatibility.

Canonical invariant:

```python
is_direct == (diagnostic_class == "direct")
```

The classifier sets it after diagnostic class.

No consumer may use `is_direct` to override `diagnostic_class`.

A persisted mismatch is a schema validation error.

A future major schema may remove `is_direct` after all consumers migrate.

---

# 32. `blocked_by`

## 32.1 Required semantics

`blocked_by` lists known causal blocker subjects.

It MUST:

- be an ordered array;
- contain unique identifiers;
- exclude self;
- contain project-relative POSIX paths for file blockers;
- be non-empty for `downstream`;
- be empty for other canonical diagnostic classes.

## 32.2 Ordering

Canonical ordering:

```text
normalized project-relative path
```

## 32.3 Root normalization

Known acyclic chains collapse to root blockers.

## 32.4 Unknown external references

An unknown referenced `.gf` file is retained in diagnostic evidence but not canonical `blocked_by` unless an explicit external-subject schema exists.

## 32.5 Missing selected dependency

When project architecture proves that a missing configured dependency blocks the subject, the missing dependency may be represented through a structured project-level blocker record.

Do not invent a file result solely to populate `blocked_by`.

---

# 33. Static scan findings

Static scan findings do not determine compile diagnostic class.

Rules:

- compile `OK` with scan hits remains `ok`;
- scan hits do not make a file `direct`;
- scan hits do not establish a dependency;
- scan hits may appear as supplementary diagnostic notes;
- scan failure due to I/O may produce a separate stage `ERROR`;
- compiler success does not erase scan findings.

The scanner and classifier remain separate components.

---

# 34. Artifact failures

An expected artifact may be missing despite process success.

Example:

```text
GF exit code = 0
required target `.gfo` missing
```

Status:

```text
FAIL or ERROR according to artifact contract
```

Diagnostic class:

- `direct` when artifact expectation belongs to the current target;
- `downstream` when missing artifact is from a known failed prerequisite;
- `ambiguous` when artifact ownership cannot be resolved.

Artifact existence alone never establishes direct source correctness.

---

# 35. Framework and infrastructure errors

Framework errors use:

```text
status = ERROR
```

and an appropriate error kind.

They do not use:

```text
diagnostic_class = framework_error
```

because `framework_error` is not canonical.

Typical mappings:

| Condition | Error kind | Diagnostic class |
|---|---|---|
| invalid global config | `CONFIG` | `ambiguous` |
| output root unavailable | `IO` | `ambiguous` |
| GF executable missing | `TOOL` | `ambiguous` |
| classifier internal exception for one subject | `INTERNAL` | `ambiguous` |
| malformed current scenario script | `SCRIPT` | `direct` |
| failed required entrypoint blocks scenario | inherited kind | `downstream` |

---

# 36. Error handling inside classifier

The classifier itself must not destroy valid stage results.

## 36.1 Subject-local classifier failure

When classification fails for one subject:

- preserve original status;
- preserve raw evidence;
- set or retain `diagnostic_class = ambiguous`;
- record classifier error separately;
- continue other subjects when safe.

## 36.2 Global classifier failure

When indexes or graph integrity are invalid:

- mark run classification stage `ERROR`;
- preserve all pre-classification results;
- do not emit false direct roots;
- reports expose the classifier failure.

## 36.3 Invalid field combination

Examples:

```text
status = OK, diagnostic_class = downstream
status = SKIPPED, is_direct = true
diagnostic_class = direct, blocked_by non-empty
diagnostic_class = downstream, blocked_by empty
```

Strict mode rejects the model.

Compatibility mode may repair only through documented deterministic rules.

---

# 37. Determinism

Given identical structured input results, classification must be identical.

Required deterministic elements:

- result identity normalization;
- peer indexes;
- reference extraction;
- blocker ordering;
- graph traversal;
- cycle handling;
- root collapse;
- aggregate counts.

Classification MUST NOT depend on:

- dictionary insertion from uncontrolled sources;
- filesystem traversal order;
- report ordering;
- current time;
- random choice;
- prior run classification;
- localized diagnostic headings.

---

# 38. Mutation policy

The current API mutates `FileResult` objects in place and returns the list.

Current contract:

```python
def classify_file_results(
    file_results: list[FileResult],
) -> list[FileResult]:
    ...
```

Final implementation may retain this approach or return immutable replacements.

Whichever model is chosen must be consistent.

## 38.1 In-place requirements

If mutating:

- list order remains unchanged;
- only classification-owned fields change;
- raw evidence fields remain unchanged;
- source paths remain unchanged;
- compile summary remains unchanged;
- function returns the same logical collection.

## 38.2 Immutable requirements

If replacing:

- all consumers migrate together;
- result identity remains stable;
- no mixed mutable and immutable behavior;
- tests verify no evidence loss.

A half-migration is prohibited.

---

# 39. Public API

Canonical public function:

```python
def classify_file_results(
    file_results: list[FileResult],
) -> list[FileResult]:
    ...
```

Optional focused helper:

```python
def classify_single_result(
    file_result: FileResult,
    file_results: list[FileResult],
) -> FileResult:
    ...
```

Optional blocker helper:

```python
def resolve_blocked_by(
    file_result: FileResult,
    file_results: list[FileResult],
) -> list[str]:
    ...
```

The all-results function is authoritative because causal classification requires peer context.

---

# 40. Recommended implementation decomposition

A balanced implementation may use:

```text
classifier.py
    classify_file_results(...)
    classify_single_result(...)
    resolve_blocked_by(...)
    build_result_indexes(...)
    resolve_diagnostic_references(...)
    collapse_blocker_graph(...)
    enforce_classification_coherence(...)
```

Diagnostic text parsing belongs in:

```text
diagnostics parser or GF normalization utility
```

Avoid unnecessary complexity such as:

- probabilistic root-cause scoring;
- machine-learning classification;
- a generic graph database;
- one class per diagnostic class;
- a rule-engine plugin system;
- parsing full GF source dependency syntax in Python;
- automatically editing source from classifications.

The v1 deterministic rule set is sufficient.

---

# 41. Migration from current classifier

The existing GF Audit classifier already provides useful behavior:

- `OK` and `SKIPPED` normalization;
- self-reference detection;
- file and module indexes;
- `.gf` reference extraction;
- failed-peer blocker detection;
- `direct`, `downstream`, and `ambiguous`;
- blocker-chain collapse;
- deterministic path normalization.

The final GF Wordbench model changes several behaviors.

## 41.1 Remove non-canonical diagnostic classes

Remove:

```text
script_error
framework_error
```

Use:

```text
error_kind = SCRIPT
status = ERROR
```

or another appropriate canonical combination.

## 41.2 Preserve `ERROR`

Current logic derives only:

```text
OK
FAIL
SKIPPED
```

Final logic preserves canonical:

```text
OK
FAIL
ERROR
SKIPPED
```

## 41.3 Do not treat timeout as direct automatically

Current direct-kind set includes:

```text
INTERNAL
TIMEOUT
SCRIPT
```

Final policy:

- `TIMEOUT` is ambiguous by default;
- `INTERNAL` requires local evidence;
- `SCRIPT` depends on whether the current scenario/script owns the defect.

## 41.4 Failed dependency takes precedence

Final policy resolves known failed external blockers before error-kind direct heuristics.

## 41.5 Separate legacy status initialization

Current `_initialize_status` mixes stage-status derivation and causal classification.

Final architecture separates:

```text
legacy result normalization
```

from:

```text
canonical causal classification
```

## 41.6 Detect duplicate identities

Current indexes retain the first identity silently.

Final strict mode treats duplicates as a model error.

## 41.7 Improve cycle handling

Final blocker-graph handling explicitly detects cycles and avoids false roots.

---

# 42. Compatibility adapter

During migration, a compatibility adapter may accept legacy file results.

Example:

```python
def normalize_legacy_file_result(result: FileResult) -> FileResult:
    if compile_is_explicitly_skipped(result):
        result.status = "SKIPPED"
    elif result.compile_summary.timed_out:
        result.status = "ERROR"
    elif result.compile_summary.exit_code == 0 and result.compile_summary.error_kind == "OK":
        result.status = "OK"
    else:
        result.status = "FAIL"
    return result
```

This adapter:

- runs before classification;
- is documented;
- has dedicated tests;
- does not become part of canonical result semantics;
- is removed after legacy migration support expires.

---

# 43. File examples

## 43.1 Successful file

Evidence:

```text
exit = 0
error_kind = OK
```

Result:

```text
status = OK
diagnostic_class = ok
is_direct = false
blocked_by = []
```

## 43.2 Self-referenced type error

Evidence:

```text
error_kind = TYPE
first_error references current GrammarX.gf
```

Result:

```text
status = FAIL
diagnostic_class = direct
is_direct = true
blocked_by = []
```

## 43.3 Dependency failure

Evidence:

```text
LangX.gf diagnostic references GrammarX.gf
GrammarX.gf status = FAIL
```

Result:

```text
LangX.gf:
  status = FAIL
  diagnostic_class = downstream
  blocked_by = ["GrammarX.gf"]
```

## 43.4 Unknown reference

Evidence:

```text
diagnostic references External.gf
no selected result resolves to External.gf
```

Result:

```text
status = FAIL
diagnostic_class = ambiguous
blocked_by = []
```

## 43.5 Timeout

Evidence:

```text
execution_state = timed_out
error_kind = TIMEOUT
no known blocker
```

Result:

```text
status = ERROR
diagnostic_class = ambiguous
```

## 43.6 Internal GF error with current source location

Evidence:

```text
error_kind = INTERNAL
diagnostic explicitly identifies StructuralX.gf
```

Result:

```text
status = FAIL or ERROR by stage policy
diagnostic_class = direct
```

## 43.7 Global executable failure

Evidence:

```text
GF executable cannot launch
```

For every attempted file:

```text
status = ERROR
diagnostic_class = ambiguous
error_kind = TOOL
```

Prefer a run-level tool error instead of duplicating identical fabricated local roots.

---

# 44. Scenario examples

## 44.1 Gold mismatch

```text
scenario completed
normalized output != gold
```

Result:

```text
status = FAIL
diagnostic_class = direct
```

## 44.2 Missing marker

```text
scenario completed
required section marker absent
```

Result:

```text
status = FAIL
diagnostic_class = direct
error_kind = SCRIPT or OTHER
```

## 44.3 Failed entrypoint

```text
scenario import fails
entrypoint file result = FAIL
```

Result:

```text
status = FAIL
diagnostic_class = downstream
blocked_by = ["<entrypoint-file>"]
```

## 44.4 Scenario timeout

```text
process timed out
no known failed prerequisite
```

Result:

```text
status = ERROR
diagnostic_class = ambiguous
error_kind = TIMEOUT
```

---

# 45. Reporting rules

Reports present, but do not redefine, classification.

Recommended headings:

```text
Direct failures
Downstream failures
Ambiguous failures
Execution errors
Skipped checks
Excluded noise
```

Required wording rules:

- `direct` is described as likely or directly evidenced;
- downstream results show blockers;
- ambiguous results state that evidence is insufficient;
- execution errors are not blamed on source automatically;
- raw evidence paths remain accessible;
- report order is deterministic.

Reports MUST NOT claim:

```text
definitive root cause
```

unless the evidence contract explicitly supports that certainty.

---

# 46. AI-ready reporting

`AI_READY.md` may prioritize:

1. direct failures;
2. ambiguous execution errors;
3. downstream failures grouped by blocker;
4. relevant raw evidence;
5. scan notes separately.

The AI packet must preserve the distinction:

```text
likely root evidence
known cascade
unresolved evidence
```

It MUST NOT instruct an AI to fix downstream files before known blockers without explaining the dependency.

---

# 47. Regression comparison

Regression comparison uses validation status as its primary axis.

A diagnostic-class change may provide secondary meaning.

Examples:

```text
FAIL/direct → FAIL/downstream
```

Status unchanged, but causal understanding changed.

```text
ERROR/ambiguous → FAIL/direct
```

Execution reliability improved, but project criterion still fails.

```text
FAIL/downstream → OK/ok
```

Improved.

Diff logic must not assume that `direct` is more severe than `downstream`.

---

# 48. Required unit tests

Minimum tests:

```text
test_ok_result_is_ok
test_skipped_result_is_skipped
test_noise_result_is_noise
test_fail_self_reference_is_direct
test_type_error_without_blocker_is_direct
test_syntax_error_without_blocker_is_direct
test_failed_dependency_is_downstream
test_failed_dependency_precedes_type_heuristic
test_successful_reference_is_not_blocker
test_unknown_reference_is_ambiguous
test_generic_nonzero_is_ambiguous
test_timeout_without_blocker_is_ambiguous
test_timeout_with_failed_prerequisite_is_downstream
test_internal_without_local_reference_is_ambiguous
test_internal_with_self_reference_is_direct
test_global_tool_failure_is_ambiguous
test_local_scenario_script_error_is_direct
test_framework_script_error_is_ambiguous
test_downstream_requires_blocked_by
test_direct_clears_blocked_by
test_ok_clears_blocked_by
test_skipped_clears_blocked_by
test_is_direct_is_derived
test_self_is_not_blocker
test_duplicate_references_are_removed
test_blockers_are_sorted_deterministically
test_chain_collapses_to_direct_root
test_cycle_without_root_becomes_ambiguous
test_cycle_with_external_direct_root_collapses
test_duplicate_file_identity_is_error
test_duplicate_module_identity_is_ambiguous_when_reference_only
test_classifier_preserves_file_order
test_classifier_preserves_raw_evidence
test_classifier_preserves_compile_summary
test_empty_input_returns_empty
```

---

# 49. Legacy migration tests

```text
test_legacy_timeout_fail_becomes_error
test_legacy_compile_skipped_becomes_skipped
test_legacy_ok_exit_becomes_ok
test_legacy_nonzero_becomes_fail
test_legacy_script_error_class_migrates_to_error_kind
test_legacy_framework_error_class_migrates_to_error_status
test_legacy_is_direct_mismatch_is_repaired
test_legacy_absolute_blocked_by_becomes_project_relative
```

Migration repairs must be deterministic and recorded.

---

# 50. Property invariants

For every final result:

```python
if diagnostic_class == "direct":
    assert is_direct is True
    assert blocked_by == []

if diagnostic_class == "downstream":
    assert is_direct is False
    assert blocked_by

if diagnostic_class in {"ok", "ambiguous", "noise", "skipped"}:
    assert is_direct is False
    assert blocked_by == []
```

Additional invariants:

```text
status OK implies diagnostic_class ok
status FAIL implies direct/downstream/ambiguous
status ERROR implies direct/downstream/ambiguous
status SKIPPED implies skipped/noise
blocked_by excludes self
blocked_by is unique
blocked_by order is deterministic
raw evidence is unchanged
```

---

# 51. Integration tests

Integration tests should build result graphs for:

```text
single direct failure
one root with several downstream failures
multi-level chain
several independent roots
one downstream result with several roots
unknown external dependency
duplicate basename in different directories
module-name-only reference
Windows path reference
POSIX path reference
mixed slash reference
cyclic dependency
timeout cascade
global executable failure
scenario blocked by entrypoint
gold mismatch
```

No real GF process is required for classifier unit integration tests.

Real-GF fixtures belong to diagnostic parsing and compilation integration suites.

---

# 52. Acceptance criteria

The classification subsystem is complete when:

```text
[ ] status, execution state, error kind, and class are separate
[ ] canonical classes contain no script_error or framework_error
[ ] ERROR is preserved
[ ] known failed dependencies take precedence
[ ] TIMEOUT is not direct by default
[ ] CONFIG, IO, and TOOL are not direct by default
[ ] TYPE and SYNTAX support direct classification
[ ] unknown evidence remains ambiguous
[ ] downstream always has blockers
[ ] blockers exclude self
[ ] chains collapse deterministically
[ ] cycles terminate safely
[ ] is_direct is derived
[ ] raw evidence is unchanged
[ ] classifier does not invoke GF
[ ] classifier does not parse reports
[ ] reports do not reclassify
[ ] aggregate counts derive from final results
[ ] legacy behavior has an explicit adapter
[ ] unit and graph tests pass
[ ] lock files and schemas agree
```

---

# 53. Troubleshooting order

When a result is misclassified, inspect:

1. primary validation status;
2. execution state;
3. error kind;
4. normalized first error;
5. structured referenced files;
6. current file and module identity;
7. peer result statuses;
8. failed-reference resolution;
9. self-reference filtering;
10. blocker graph;
11. cycle handling;
12. final coherence enforcement;
13. report consumption.

Do not begin by modifying report formatting.

---

# 54. Anti-drift indicators

Classification drift exists when:

- one component uses `script_error` as a diagnostic class;
- one schema uses `framework_error`;
- timeout becomes direct solely from `TIMEOUT`;
- classifier converts `ERROR` into `FAIL`;
- report code reclassifies failures;
- `is_direct` disagrees with `diagnostic_class`;
- downstream has empty `blocked_by`;
- blockers use absolute paths in canonical JSON;
- blocker ordering changes between runs;
- a successful peer is treated as a blocker;
- self appears in `blocked_by`;
- classifier mutates raw diagnostics;
- static scan hits determine directness;
- duplicate identities are silently ignored;
- a dependency cycle causes recursion failure;
- a generic error is forced to direct instead of ambiguous;
- previous-run classification influences current causality.

Any such change requires coordinated review of:

```text
classifier
result models
diagnostic parser
compiler
scenario runner
result builder
JSON schema
reports
tests
INTERFILE_CONTRACT_LOCK.md
PERSISTED_SCHEMA_LOCK.md
GLOSSARY.md
this document
```

---

# 55. Cross-references

| Topic | Document |
|---|---|
| Canonical terminology | `docs/GLOSSARY.md` |
| Framework classifier contract | `docs/INTERFILE_CONTRACT_LOCK.md` |
| Persisted result schema | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Diagnostic overview | `docs/diagnostics/DIAGNOSTIC_OVERVIEW.md` |
| Direct and downstream details | `docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md` |
| GF diagnostic parsing | `docs/diagnostics/GF_DIAGNOSTIC_PARSING.md` |
| Known patterns | `docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md` |
| Process failures | `docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md` |
| Compilation | `docs/gf/GF_COMPILATION.md` |
| Static scanning | `docs/validation/STATIC_SCANNING.md` |
| Scenario validation | `docs/validation/SCENARIO_VALIDATION.md` |
| Status reference | `docs/reference/STATUS_VALUES.md` |
| Diagnostic kinds reference | `docs/reference/DIAGNOSTIC_KINDS.md` |

---

# 56. Final rule

> The classifier may state only what the evidence supports.

When a failed dependency is known, classify the current subject as downstream.

When strong local evidence exists and no stronger blocker exists, classify it as direct.

When evidence is insufficient, preserve ambiguity.

False certainty is a diagnostic defect.
