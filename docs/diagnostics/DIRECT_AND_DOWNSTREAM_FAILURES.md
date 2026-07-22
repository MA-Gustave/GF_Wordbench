# GF Wordbench — Direct and Downstream Failures

**Document ID:** `GF-WB-DIAG-DIRECT-DOWNSTREAM`  
**Status:** Normative diagnostic specification  
**Applies to:** Classification of GF Wordbench validation failures  
**Primary implementation:** `app/audit/classifier.py`  
**Primary model:** `FileResult`  
**Primary public function:** `classify_file_results(...)`  
**Owner:** GF Wordbench maintainers  
**Last structural review:** 2026-07-22  

---

## 1. Purpose

A complete GF grammar often compiles through a dependency chain.

When one lower-level module fails, many modules that depend on it may also fail. Reporting every failed module as an independent root cause creates noise and directs maintainers toward the wrong files.

GF Wordbench therefore distinguishes:

- **direct failures**: failures with evidence that the problem is local to the reported subject or is itself an execution-level root failure;
- **downstream failures**: failures caused or blocked by another failed subject;
- **ambiguous failures**: failures for which available evidence does not justify either conclusion.

This document defines:

- the meaning of each diagnostic class;
- the evidence required for classification;
- the classification order;
- how file references are resolved;
- how `blocked_by` is built;
- how dependency chains collapse to root failures;
- how technical failures differ from causal classification;
- how reports must present the result;
- how tests prevent classification drift.

The governing principle is:

> GF Wordbench must prefer an honest ambiguity over an invented root cause.

---

## 2. Scope

This specification governs causal classification for structured validation results, especially:

```text
FileResult
```

It covers:

- `OK`, `FAIL`, `ERROR`, and `SKIPPED` status interaction;
- `direct`, `downstream`, `ambiguous`, `ok`, `noise`, and `skipped`;
- self-referenced diagnostics;
- diagnostics that reference another failed file or module;
- diagnostics that reference a successful file;
- error kinds;
- timeouts and framework execution errors;
- path and module normalization;
- dependency-chain collapse;
- cycles;
- duplicate references;
- deterministic ordering;
- reporting;
- persistence;
- regression comparison;
- test requirements.

The initial production scope is file compilation.

Scenario and release-artifact classification may use the same vocabulary only when they expose equivalent structured dependency evidence.

---

## 3. Non-goals

This classification does not:

- prove the true semantic cause of every GF failure;
- replace the GF diagnostic parser;
- replace the project module dependency map;
- parse the complete GF source language;
- infer arbitrary imports from source text during classification;
- rerun compilation;
- mutate source files;
- repair failed modules;
- decide whether a linguistic analysis is correct;
- replace raw stdout and stderr;
- classify static-scan findings as compile failures;
- rank developer effort;
- assign blame to a person or commit;
- infer a rename;
- claim causality from timing alone.

The classifier operates only on evidence already produced by validation stages.

---

## 4. Core vocabulary

## 4.1 Validation status

Validation status answers:

> Did the requested validation pass, fail, error, or not run?

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

## 4.2 Diagnostic class

Diagnostic class answers:

> What is the causal relationship of this result to the currently observed failure set?

Canonical values:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

## 4.3 Error kind

Error kind answers:

> What technical or GF-reported category best describes the immediate failure?

Canonical values include:

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

## 4.4 Execution state

Execution state answers:

> What happened to the external operation?

Canonical values may include:

```text
completed
timed_out
cancelled
launch_failed
not_started
```

## 4.5 Blocker

A blocker is another failed subject whose failure is supported by available evidence as preventing the current subject from validating successfully.

## 4.6 Root failure

A root failure is a direct failure, or the closest available unresolved failure when a dependency chain cannot be reduced further.

---

## 5. Separation of dimensions

The following dimensions must remain separate:

```text
validation_status
diagnostic_class
error_kind
execution_state
```

Example:

```text
validation_status = FAIL
diagnostic_class  = downstream
error_kind        = TYPE
execution_state   = completed
```

This means:

- GF completed the compile attempt;
- the current file failed;
- the diagnostic was type-related;
- another failed subject is the supported causal blocker.

Another example:

```text
validation_status = ERROR
diagnostic_class  = ambiguous
error_kind        = TOOL
execution_state   = launch_failed
```

This means GF Wordbench could not obtain enough subject-local evidence to assign a source-level cause.

Technical categories must not be added as diagnostic classes.

Therefore, values such as:

```text
script_error
framework_error
timeout
tool_error
```

must not appear in `diagnostic_class`.

They belong to `error_kind` or `execution_state`.

---

# 6. Canonical diagnostic classes

## 6.1 `ok`

Use when the subject passed its requested validation.

Required state:

```text
status = OK
diagnostic_class = ok
is_direct = false
blocked_by = []
```

Static-scan findings may still exist.

A successful GF compilation with scan findings remains:

```text
status = OK
diagnostic_class = ok
```

The findings are reported separately.

## 6.2 `direct`

Use when available evidence supports the current subject as a likely local or root failure.

Required state:

```text
status = FAIL or ERROR
diagnostic_class = direct
is_direct = true
blocked_by = []
```

`direct` means:

```text
best supported root within the observed result set
```

It does not mean mathematical proof that no dependency contributed.

## 6.3 `downstream`

Use when the current subject failed and evidence identifies at least one other failed subject as its blocker.

Required state:

```text
status = FAIL or ERROR
diagnostic_class = downstream
is_direct = false
blocked_by = [one or more stable subject paths]
```

An empty `blocked_by` list is invalid for a final downstream result.

## 6.4 `ambiguous`

Use when the subject failed but evidence is insufficient or conflicting.

Required state:

```text
status = FAIL or ERROR
diagnostic_class = ambiguous
is_direct = false
blocked_by = []
```

An implementation may preserve unresolved references separately, but it must not place unverified successful or unknown subjects in canonical `blocked_by`.

## 6.5 `noise`

Use for an excluded or non-actionable subject represented in result collections by explicit policy.

Typical examples:

- backup source;
- temporary file;
- disabled file;
- copied file excluded by naming policy.

Noise is normally identified during selection, not by compile-failure classification.

Required state:

```text
diagnostic_class = noise
is_direct = false
```

## 6.6 `skipped`

Use when the requested validation was intentionally not executed.

Required state:

```text
status = SKIPPED
diagnostic_class = skipped
is_direct = false
blocked_by = []
```

Skipped must not be represented as successful compilation.

---

# 7. Classification invariants

The final classifier must preserve these invariants:

1. Classification operates on structured results and captured evidence.
2. Classification does not invoke GF.
3. Classification does not modify source files.
4. Classification does not rewrite raw logs.
5. Classification is deterministic.
6. `OK` always maps to `ok`.
7. `SKIPPED` always maps to `skipped`.
8. A final downstream result has at least one blocker.
9. A direct result has no `blocked_by` entries.
10. An ambiguous result does not pretend to know a blocker.
11. Reports do not independently reclassify results.
12. Path identity is normalized consistently.
13. Original diagnostic text remains accessible.
14. Static-scan findings do not determine direct/downstream status.
15. Missing evidence does not become direct evidence.
16. A reference to a successful subject does not establish downstream failure.
17. A reference to the current subject supports direct classification.
18. Known dependency chains collapse toward supported roots.
19. Cycles do not cause recursion failure.
20. Result order does not change classification meaning.

---

# 8. Classification timing

## 8.1 Per-file result creation

Each selected file first produces a provisional `FileResult` containing:

- file identity;
- module identity;
- compile status;
- error kind;
- first error;
- raw evidence paths;
- scan findings;
- fingerprint.

A compile failure may initially be marked:

```text
diagnostic_class = ambiguous
```

or an internal unclassified sentinel.

## 8.2 Cross-file classification

Classification occurs after the relevant file result set is available.

Canonical sequence:

```text
compile selected files
    -> build provisional FileResult objects
    -> initialize statuses
    -> classify each failed result
    -> collapse downstream chains to roots
    -> recompute aggregate counts
    -> generate reports
```

This ordering is necessary because downstream classification requires knowledge of which referenced subjects also failed.

## 8.3 Scope

Classification uses the result set from the current resolved validation scope.

A file absent from the current scope cannot be treated as a confirmed failed blocker unless an explicit external dependency result is provided through a documented contract.

---

# 9. Evidence hierarchy

The classifier uses evidence in a conservative priority order.

## 9.1 Strong direct evidence

Examples:

- the first normalized error references the current file;
- the first normalized error references the current module;
- a subject-local compiler failure is explicitly modeled as the root;
- an error kind is configured as intrinsically local for this result type;
- a project dependency model confirms the failure originates in the current provider and diagnostics are consistent.

## 9.2 Strong downstream evidence

Examples:

- the first normalized error references another subject;
- that referenced subject exists in the current result set;
- the referenced subject has failing status;
- the reference is not merely incidental text;
- the subject is not the current file or module.

## 9.3 Supporting evidence

Examples:

- project module dependency graph;
- compiler trace sequence;
- `blocked_by` already supplied by a trusted stage;
- stable module-name mapping;
- matching source path;
- repeated references across diagnostic lines.

Supporting evidence may strengthen a classification but should not override contradictory stronger evidence silently.

## 9.4 Weak evidence

Examples:

- module name appears in unrelated prose;
- a file appears in a compilation-progress line;
- source fingerprint changed;
- a dependent module failed earlier by timestamp;
- import direction is guessed from naming convention;
- static scan found suspicious text;
- a path fragment cannot be resolved.

Weak evidence must not alone establish downstream causality.

## 9.5 Insufficient evidence

When only weak or unresolved evidence exists:

```text
diagnostic_class = ambiguous
```

---

# 10. Status initialization

Before causal classification, status is normalized from the operation result.

## 10.1 Successful compile

When all applicable conditions hold:

```text
exit_code = 0
timed_out = false
error_kind = OK
compile was executed
```

set:

```text
status = OK
diagnostic_class = ok
is_direct = false
blocked_by = []
```

## 10.2 Skipped compile

When compilation was intentionally skipped:

```text
status = SKIPPED
diagnostic_class = skipped
is_direct = false
blocked_by = []
```

Skipped state should be represented by an explicit field or execution state.

The final implementation should not depend solely on searching human text such as:

```text
"compile skipped"
```

Legacy data may continue to recognize that phrase during migration.

## 10.3 Timed-out compile

Canonical final mapping:

```text
status = ERROR
error_kind = TIMEOUT
execution_state = timed_out
```

Diagnostic class is determined from available causal evidence.

Recommended default when no reliable dependency evidence exists:

```text
diagnostic_class = direct
```

for a timeout scoped to the current file process, because the current validation operation itself is the immediate blocking root.

However, the documentation and implementation must not claim that source content caused the timeout.

The primary message should say:

```text
Compilation timed out for this subject.
```

not:

```text
This file contains the root grammar bug.
```

## 10.4 Launch failure

Canonical mapping:

```text
status = ERROR
error_kind = TOOL
execution_state = launch_failed
```

When the GF executable cannot launch for all files, this is a run-level infrastructure root, not a meaningful file dependency cascade.

The final architecture should avoid classifying every file as a separate source-level direct failure.

Preferred behavior:

- create one run-level tool error;
- mark unstarted file validations as skipped or blocked by the run-level failure according to the result model;
- do not pretend the source files independently failed.

## 10.5 Other compile failure

When compilation executed and did not pass:

```text
status = FAIL
```

then apply the causal classification rules below.

---

# 11. Direct failure rules

A failed file is direct when the first applicable strong rule matches.

## 11.1 Self-path reference

If normalized diagnostic evidence references the current canonical file path:

```text
direct
```

Example:

```text
lib/src/french/GrammarFre.gf: cannot unify ...
```

for:

```text
file_path = lib/src/french/GrammarFre.gf
```

Result:

```text
diagnostic_class = direct
is_direct = true
blocked_by = []
```

## 11.2 Self-module reference

If the diagnostic references the current module identity and resolves unambiguously:

```text
direct
```

Example:

```text
GrammarFre: type mismatch
```

for module:

```text
GrammarFre
```

Module-name matching must not use arbitrary substring tests.

## 11.3 Explicit local diagnostic

A diagnostic parser may expose a structured local subject path.

If that subject is the current file:

```text
direct
```

## 11.4 Intrinsically local operation failure

Some failures are immediate roots for the current operation:

```text
INTERNAL
TIMEOUT
SCRIPT
```

The current baseline classifier treats these as obvious direct kinds.

The final system must preserve the useful behavior while separating technical meaning:

- `error_kind` remains `INTERNAL`, `TIMEOUT`, or `SCRIPT`;
- `diagnostic_class` may be `direct` when the operation was scoped to this file and no broader infrastructure failure exists;
- reports must label them as technical roots, not necessarily source-code roots.

## 11.5 Likely local GF errors

When no resolved other-file reference exists, these kinds may support direct classification:

```text
TYPE
SYNTAX
```

This rule is lower priority than a confirmed failed dependency.

Example:

```text
error_kind = TYPE
no referenced failed subject
```

Result:

```text
direct
```

## 11.6 Explicit trusted root

A trusted result-producing stage may identify the current subject as the root through a documented structured field.

Reports and callers must not set that field casually.

## 11.7 Direct does not imply only failure

Multiple independent direct failures may exist in one run.

The classifier must not force one global root.

---

# 12. Downstream failure rules

A failed file is downstream only when a blocker is supported.

## 12.1 Referenced failed file

If the diagnostic references another file and that file is failing in the current result set:

```text
downstream
```

Example:

```text
current:
  lib/src/french/LangFre.gf = FAIL

diagnostic:
  lib/src/french/GrammarFre.gf: cannot unify ...

other current result:
  lib/src/french/GrammarFre.gf = FAIL
```

Result:

```text
LangFre.gf:
  diagnostic_class = downstream
  blocked_by = ["lib/src/french/GrammarFre.gf"]
```

## 12.2 Referenced failed module

If a diagnostic contains a module identity that maps uniquely to another failing result:

```text
downstream
```

The display blocker uses the canonical project-relative file path.

## 12.3 Existing structured blockers

When a trusted stage already supplies blockers, classification verifies:

- each blocker identity resolves;
- each blocker is failing;
- no blocker is the current subject;
- duplicates are removed;
- paths are canonical.

Verified blockers support downstream classification.

## 12.4 Multiple blockers

A subject may have multiple supported blockers.

Example:

```text
blocked_by = [
  "lib/src/french/MorphoFre.gf",
  "lib/src/french/StructuralFre.gf"
]
```

Ordering must be deterministic.

Recommended ordering:

```text
project-relative path lexical order
```

or dependency-discovery order when that order is explicitly stable.

## 12.5 Failed dependency before likely-direct kind

A confirmed failed dependency takes precedence over generic likely-direct kinds such as `TYPE` or `SYNTAX`.

This avoids classifying every propagated type error as local.

## 12.6 Blocker must fail

A referenced subject with:

```text
status = OK
```

is not a blocker.

The current failure becomes ambiguous unless separate direct evidence exists.

## 12.7 Unknown reference

A referenced `.gf` path not present in the result set does not establish downstream failure.

Possible interpretations:

- excluded dependency;
- RGL file outside scope;
- stale path;
- diagnostic context;
- missing source;
- parser false positive.

Default:

```text
ambiguous
```

A future external-dependency result model may provide stronger evidence.

---

# 13. Ambiguous failure rules

Use `ambiguous` when no strong direct or downstream rule applies.

## 13.1 Reference to successful subject

Example:

```text
AllFre.gf = FAIL
diagnostic references NounFre.gf
NounFre.gf = OK
```

Result:

```text
AllFre.gf = ambiguous
blocked_by = []
```

The reference is evidence context, not a confirmed blocker.

## 13.2 Unresolved file reference

A diagnostic references:

```text
SomeModule.gf
```

but no unique current result matches.

Result:

```text
ambiguous
```

## 13.3 Conflicting evidence

Example:

- self file is referenced;
- another failed file is also referenced;
- diagnostic ordering is unclear;
- parser cannot identify the primary location.

The classifier may choose direct only when the documented primary-error rule resolves the conflict.

Otherwise:

```text
ambiguous
```

## 13.4 Generic failure

Example:

```text
error_kind = OTHER
first_error = "compilation failed"
```

No path, module, or trusted blocker exists.

Result:

```text
ambiguous
```

## 13.5 Missing diagnostic

A non-zero compile result with no usable diagnostic is normally:

```text
ambiguous
```

unless execution state itself provides a technical direct root.

## 13.6 Ambiguity is actionable

Reports should present ambiguous failures after direct failures and before downstream noise where appropriate.

An ambiguous result means:

```text
inspect raw stdout/stderr and dependency context
```

It must not be hidden.

---

# 14. Classification precedence

Canonical precedence for a failed file:

```text
1. normalize status
2. OK -> ok
3. SKIPPED -> skipped
4. validate pre-existing structured evidence
5. detect self-reference or explicit local root
6. detect confirmed other failed blockers
7. inspect all resolved references
8. if references resolve only to successful subjects -> ambiguous
9. apply likely-local error-kind rule
10. otherwise -> ambiguous
```

A compact decision tree:

```text
Passed?
  yes -> ok
  no
    |
Skipped?
  yes -> skipped
  no
    |
Strong self/local evidence?
  yes -> direct
  no
    |
Confirmed other failing subject referenced?
  yes -> downstream
  no
    |
Any resolved non-failing reference?
  yes -> ambiguous
  no
    |
Likely-local GF error kind?
  yes -> direct
  no -> ambiguous
```

Technical run-wide failures must be handled before applying this file-level tree blindly.

---

# 15. File-reference extraction

## 15.1 Purpose

Diagnostic text may contain paths such as:

```text
lib/src/french/GrammarFre.gf
lib\src\french\GrammarFre.gf
GrammarFre.gf
```

The classifier extracts candidate `.gf` references.

## 15.2 Candidate pattern

The current baseline recognizes path-like text ending in:

```text
.gf
```

Candidate extraction must remain conservative.

It should not parse arbitrary words as module paths.

## 15.3 Trailing punctuation

Remove diagnostic punctuation such as:

```text
.
,
;
:
)
]
}
```

without changing the underlying path.

## 15.4 Duplicate references

Duplicate normalized references are collapsed while preserving deterministic first appearance.

## 15.5 Full diagnostic context

The final classifier should consume structured normalized diagnostic locations when available.

Regex extraction from `first_error` remains a fallback.

## 15.6 First error

The current baseline uses:

```text
CompileSummary.first_error
```

The final design keeps the first normalized error as the primary causal clue.

Additional diagnostics may support classification only through a documented deterministic policy.

## 15.7 Progress-line noise

Compiler progress text such as:

```text
compiling Common.gf
```

must not be mistaken for a failure location unless the diagnostic parser marks it as part of the primary error.

---

# 16. File and module identity

## 16.1 Canonical file identity

Use normalized project-relative path:

```text
lib/src/french/GrammarFre.gf
```

## 16.2 Canonical separators

Canonical persisted separator:

```text
/
```

Input may contain Windows backslashes.

## 16.3 Case

The baseline classifier uses case-insensitive keys.

The final policy:

- preserve source case for display;
- use platform/project-aware normalized keys;
- prevent two distinct project files from collapsing silently;
- fail clearly on duplicate normalized identity.

## 16.4 Module identity

Module identity comes from:

```text
FileResult.module_name
```

or, when absent:

```text
Path(file_path).stem
```

The explicit model field is preferred.

## 16.5 Unique mapping

A module reference supports downstream classification only when it maps uniquely.

Duplicate module names in one comparison scope are a configuration or model error.

## 16.6 Display path

`blocked_by` stores canonical display paths, not lowercased internal keys.

---

# 17. `blocked_by` contract

## 17.1 Type

```text
list[str]
```

## 17.2 Path form

Each value is:

- project-relative;
- `/` separated;
- stable;
- non-empty;
- unique.

## 17.3 Meaning

`blocked_by` identifies supported causal blockers.

It is not:

- every imported module;
- every file mentioned in logs;
- a full dependency graph;
- a list of possible guesses;
- an error stack.

## 17.4 Direct result

```text
direct -> blocked_by = []
```

## 17.5 Downstream result

```text
downstream -> blocked_by has at least one value
```

## 17.6 Ambiguous result

Canonical:

```text
ambiguous -> blocked_by = []
```

Possible unresolved references should use a future separate field such as:

```text
referenced_subjects
```

only after a schema change.

## 17.7 Mutation

The classifier owns final `blocked_by` normalization.

Reports are observers.

---

# 18. Root collapse

## 18.1 Purpose

Dependency failures can form chains:

```text
GrammarFre.gf  = direct
LangFre.gf     = downstream of GrammarFre.gf
AllFre.gf      = downstream of LangFre.gf
```

Reporting:

```text
AllFre.gf blocked by LangFre.gf
```

is locally true but less useful than:

```text
AllFre.gf blocked by GrammarFre.gf
```

## 18.2 Canonical collapse

Final downstream blockers should collapse toward direct roots when the chain is known.

Result:

```text
GrammarFre.gf:
  direct

LangFre.gf:
  downstream
  blocked_by = [GrammarFre.gf]

AllFre.gf:
  downstream
  blocked_by = [GrammarFre.gf]
```

## 18.3 Multiple roots

Example:

```text
ApiFre.gf
  -> LangFre.gf -> GrammarFre.gf
  -> ExtraFre.gf -> StructuralFre.gf
```

Final:

```text
ApiFre.gf.blocked_by = [
  GrammarFre.gf,
  StructuralFre.gf
]
```

## 18.4 Unresolved intermediate result

If a referenced blocker is failing but not classified as direct or downstream:

```text
use the closest supported unresolved blocker
```

Do not drop the blocker.

## 18.5 Cycle safety

Example:

```text
A blocked by B
B blocked by A
```

The collapse algorithm must:

- track visited identities;
- terminate;
- avoid duplicate paths;
- preserve a stable unresolved root representation;
- record a warning for the cycle.

A cycle must not cause recursion overflow.

## 18.6 Self-cycle

A self-blocker is invalid and removed.

Self-reference supports direct classification instead.

## 18.7 Determinism

Root order must not depend on dictionary iteration accidents.

---

# 19. Directness compatibility field

## 19.1 `is_direct`

The current model includes:

```text
is_direct: bool
```

Canonical consistency:

```text
diagnostic_class = direct
    -> is_direct = true

all other diagnostic classes
    -> is_direct = false
```

## 19.2 Redundancy

`is_direct` is redundant with `diagnostic_class`.

It remains for compatibility while existing consumers use it.

## 19.3 Final direction

The framework may deprecate `is_direct` in a future major schema.

Until then:

- the result builder and classifier keep it coherent;
- readers must not trust it over a conflicting canonical `diagnostic_class`;
- contract tests reject inconsistency.

---

# 20. Error kinds and causal meaning

## 20.1 `TYPE`

Often local, but may propagate through dependencies.

Rule:

```text
confirmed failed blocker first
otherwise likely direct
```

## 20.2 `SYNTAX`

Usually local to the referenced source.

Self or explicit local path:

```text
direct
```

Other failed referenced file:

```text
downstream
```

No usable location:

```text
direct or ambiguous according to parser confidence
```

Recommended conservative default:

```text
direct
```

only when the compile request directly targeted that source.

## 20.3 `INTERNAL`

Represents a GF internal or framework-normalized internal failure.

For a file-scoped invocation:

```text
technical direct root
```

Do not claim the file is semantically wrong.

## 20.4 `TIMEOUT`

Represents resource or termination failure.

For a file-scoped invocation:

```text
technical direct root
```

unless a run-wide infrastructure timeout invalidated all requests.

## 20.5 `SCRIPT`

Represents orchestration or script-level failure.

The original classifier marks it direct.

Final reporting should say:

```text
direct technical failure
```

not source grammar root.

## 20.6 `CONFIG`

Configuration errors should normally be run- or project-level.

Avoid duplicating one configuration error as many independent direct file failures.

## 20.7 `IO`

An I/O error on one source or one artifact is a direct technical failure for that operation.

A shared output-root failure is run-level.

## 20.8 `TOOL`

A tool launch failure is generally run-level.

A tool-reported subject-specific error may be file-level when structured evidence supports it.

## 20.9 `OTHER`

Requires path, module, or trusted blocker evidence.

Otherwise:

```text
ambiguous
```

---

# 21. Static scan findings

Static scanning and causal compile classification remain separate.

Example:

```text
file status       = OK
diagnostic_class  = ok
scan hits         = 3
```

Another example:

```text
file status       = FAIL
diagnostic_class  = downstream
scan hits         = 2
```

Scan hits may be relevant developer clues.

They do not override stronger compilation evidence.

The classifier must not say:

```text
direct
```

solely because a scanner pattern was found.

---

# 22. Project dependency map

## 22.1 Role

The active project may maintain:

```text
project/docs/MODULE_DEPENDENCY_MAP.md
```

and structured project metadata.

## 22.2 Use

A dependency map may:

- validate that a proposed blocker relationship is structurally possible;
- help collapse chains;
- explain upstream/downstream direction;
- detect impossible diagnostic references;
- enrich reports.

## 22.3 Limitation

Documentation prose is not a machine source unless converted into a structured validated model.

The classifier must not parse Markdown to recover dependencies.

## 22.4 Source imports

A future structured GF import graph may be generated through a dedicated stage.

It must have its own owner, schema, tests, and compatibility policy.

## 22.5 Conflict

When diagnostics and a trusted dependency graph conflict:

```text
ambiguous + warning
```

unless a documented precedence rule proves one source authoritative.

---

# 23. File-selection effects

## 23.1 Complete scope

Classification is strongest when all relevant project files are included.

## 23.2 Quick mode

Quick mode may compile only one target.

A diagnostic that references another file absent from the current result set cannot be confirmed as downstream.

Recommended result:

```text
ambiguous
```

with the reference preserved in raw evidence.

## 23.3 Checkpoint mode

Checkpoint classification is limited to the checkpoint result scope.

Dependencies outside the scope require explicit dependency evidence.

## 23.4 Release and diagnostic modes

Broad source coverage provides the strongest direct/downstream classification.

## 23.5 Excluded files

An excluded file is not treated as failed.

A reference to it does not establish a blocker.

---

# 24. Scenario failures

## 24.1 Default

Scenario failures are classified separately from file compile cascades.

A failed scenario is normally:

```text
direct
```

to the scenario assertion or execution when the grammar loaded successfully.

## 24.2 Blocked scenario

A scenario may be downstream when structured evidence proves it did not execute because a required grammar load, PGF build, or prerequisite scenario failed.

Example:

```text
parse scenario not started
blocked by release-pgf build failure
```

## 24.3 Required evidence

Do not infer scenario downstream status merely because files also failed.

The scenario runner or orchestrator must explicitly model the prerequisite relationship.

## 24.4 Scenario `blocked_by`

Scenario blockers require generalized subject identities.

They must not be stored as misleading file paths in a file-only field.

This extension requires the shared result model and persisted schema to define the form.

## 24.5 Gold mismatch

A completed scenario with gold mismatch is direct to that scenario validation.

It is not automatically downstream from the grammar unless the output proves an upstream execution failure.

---

# 25. Release-artifact failures

## 25.1 PGF build failure

A PGF build failure may be downstream of one or more failed entrypoints when structured evidence identifies them.

## 25.2 Missing PGF after successful command

This is a direct artifact-contract failure.

## 25.3 Run-level tool failure

A GF executable launch failure is a run-level direct technical failure.

## 25.4 Scope caution

Do not force release results into `FileResult.blocked_by`.

Use a generalized result relationship when implemented.

---

# 26. Classification algorithm

Canonical logical algorithm:

```python
def classify_file_results(file_results):
    initialize_all_statuses(file_results)

    indexes = build_result_indexes(file_results)

    for result in deterministic_order(file_results):
        classify_single_result(
            result=result,
            indexes=indexes,
        )

    failing_index = build_failing_result_index(file_results)

    for result in deterministic_order(file_results):
        if result.diagnostic_class == "downstream":
            result.blocked_by = collapse_to_supported_roots(
                result.blocked_by,
                failing_index,
            )

    validate_classification_invariants(file_results)
    return file_results
```

Single-result logic:

```python
def classify_single_result(result, indexes):
    normalize_status(result)

    if result.status == "OK":
        return mark_ok(result)

    if result.status == "SKIPPED":
        return mark_skipped(result)

    evidence = collect_causal_evidence(result, indexes)

    if evidence.strong_self_or_local_root:
        return mark_direct(result)

    blockers = confirmed_failing_blockers(evidence, indexes)
    if blockers:
        return mark_downstream(result, blockers)

    if evidence.has_resolved_nonfailing_references:
        return mark_ambiguous(result)

    if error_kind_is_likely_local(result):
        return mark_direct(result)

    return mark_ambiguous(result)
```

Private helper names may differ.

Behavior and invariants are normative.

---

# 27. Result-index construction

## 27.1 File index

```text
normalized file identity -> FileResult
```

## 27.2 Module index

```text
normalized module identity -> FileResult
```

## 27.3 Failing index

Include:

```text
FAIL
ERROR
```

when the result model treats both as failed blockers.

The earlier implementation indexes only `FAIL`.

The final implementation must explicitly include `ERROR` where an errored subject can validly block dependents.

## 27.4 Duplicate key

Duplicate canonical file or module identity is an error.

Do not silently keep the first result.

## 27.5 Stable construction

Index construction must be deterministic and independent of report ordering.

---

# 28. Classification confidence

## 28.1 No required numeric score

GF Wordbench does not require a probabilistic confidence model.

Numeric scores would create precision without proof.

## 28.2 Explainable reason

The classifier should retain or derive a structured reason such as:

```text
self_path_reference
self_module_reference
confirmed_failed_reference
explicit_blocker
likely_local_error_kind
no_resolved_reference
reference_to_successful_subject
technical_operation_root
```

## 28.3 Schema policy

A persisted `classification_reason` field is useful but must be added through the schema-change workflow.

Until then, reason may remain internal or appear in detail logs.

## 28.4 Human message

Reports may render:

```text
Direct: first error points to this file.
Downstream: blocked by GrammarFre.gf.
Ambiguous: referenced file passed in this run.
```

Messages are explanatory, not machine authority.

---

# 29. Reporting requirements

## 29.1 Ordering

Recommended failure presentation:

```text
1. run-level execution errors
2. direct failures
3. ambiguous failures
4. downstream failures
5. skipped subjects
6. scan-only notes
```

This prioritizes likely roots.

## 29.2 Direct section

For each direct failure, show:

- subject path;
- error kind;
- first error;
- raw stdout/stderr paths;
- relevant scan notes;
- technical-root label when applicable.

## 29.3 Downstream section

For each downstream failure, show:

- subject path;
- `blocked_by`;
- concise current failure;
- raw evidence paths.

Do not duplicate the full root error for every downstream subject.

## 29.4 Ambiguous section

For each ambiguous failure, show:

- subject path;
- error kind;
- first error;
- unresolved context;
- raw evidence paths;
- suggestion to inspect dependencies or rerun a broader mode.

## 29.5 AI report

`AI_READY.md` should lead with direct failures and root blockers.

It should not ask an AI to diagnose every downstream file independently.

## 29.6 Counts

Aggregate counts must derive from classified result collections.

Canonical counts include:

```text
direct_fail
downstream_fail
ambiguous_fail
```

They must agree with serialized results.

## 29.7 No report-side mutation

A report writer must not change:

```text
diagnostic_class
is_direct
blocked_by
```

---

# 30. Persisted representation

Canonical `FileResult` fields include:

```json
{
  "file_path": "lib/src/french/LangFre.gf",
  "status": "FAIL",
  "diagnostic_class": "downstream",
  "is_direct": false,
  "blocked_by": [
    "lib/src/french/GrammarFre.gf"
  ]
}
```

## 30.1 Canonical paths

Persisted blocker paths are project-relative with `/`.

## 30.2 Stable vocabulary

Canonical writers emit only:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

## 30.3 Legacy `script_error`

A legacy `diagnostic_class = script_error` must migrate to:

```text
diagnostic_class = direct or ambiguous according to evidence
error_kind = SCRIPT
```

The migration must not discard the original technical error.

## 30.4 Legacy `framework_error`

A legacy `diagnostic_class = framework_error` must migrate to:

```text
error_kind = INTERNAL, CONFIG, IO, or TOOL
```

and a causal class supported by available evidence.

## 30.5 Invalid combination

Readers or validators should reject or normalize inconsistent combinations such as:

```text
diagnostic_class = downstream
blocked_by = []

diagnostic_class = direct
is_direct = false

status = OK
diagnostic_class = downstream
```

---

# 31. Regression comparison

Regression comparison treats diagnostic class changes as details unless status changes.

Examples:

```text
FAIL/direct -> FAIL/downstream
change_kind = unchanged
detail = diagnostic class changed
```

```text
FAIL/downstream -> FAIL/direct
change_kind = unchanged
detail = likely root shifted to current file
```

```text
FAIL/direct -> OK/ok
change_kind = improved
```

```text
OK/ok -> FAIL/downstream
change_kind = regressed
```

A blocker-set change should be reported as a detail.

---

# 32. Determinism

Classification must produce equivalent output for equivalent structured evidence.

Deterministic elements:

- file identity normalization;
- module identity normalization;
- reference extraction order;
- duplicate elimination;
- classification precedence;
- blocker order;
- root-collapse order;
- report grouping.

The algorithm must not depend on:

- filesystem iteration;
- hash randomization;
- wall-clock timing;
- report order;
- GUI order;
- locale collation.

---

# 33. Concurrency

Compilation may become parallel in a future implementation.

Classification still begins only after the relevant result collection is complete.

Parallel completion order must not affect:

- direct/downstream decision;
- blocker order;
- root collapse;
- aggregate counts.

Results are reordered into canonical identity order before classification when needed.

---

# 34. Failure of the classifier

## 34.1 Required behavior

If classification fails unexpectedly:

- preserve all raw compile results;
- preserve stdout and stderr;
- do not invent causal classes;
- mark affected results ambiguous when safe;
- record a framework error;
- continue report generation when possible.

## 34.2 Strict behavior

Strict or release mode may elevate classifier failure to:

```text
overall_status = ERROR
```

because root-cause reporting is incomplete.

## 34.3 No evidence loss

Classifier failure must not delete or rewrite compile logs.

---

# 35. Security considerations

## 35.1 Diagnostic text is untrusted input

Paths extracted from diagnostics must not be opened automatically merely because they appear in text.

## 35.2 Path containment

Before resolving a diagnostic path to a project result:

- normalize identity;
- compare against known result indexes;
- do not access arbitrary filesystem paths.

## 35.3 Resource limits

Diagnostic parsing must be bounded.

Avoid pathological regular expressions and unbounded recursion.

## 35.4 Root-collapse cycles

Visited-set handling is mandatory.

## 35.5 Report injection

Diagnostic text rendered in Markdown or HTML must be escaped or fenced according to the output format.

## 35.6 Secrets

Error text may contain local paths or sensitive fragments.

Sharing reports requires normal redaction policy.

---

# 36. Examples

## 36.1 Successful file

```text
file:
  NounFre.gf

compile:
  exit_code = 0
  error_kind = OK

result:
  status = OK
  diagnostic_class = ok
  is_direct = false
  blocked_by = []
```

## 36.2 Self-referenced type failure

```text
file:
  GrammarFre.gf

first error:
  lib/src/french/GrammarFre.gf: cannot unify ...

result:
  status = FAIL
  diagnostic_class = direct
  is_direct = true
  blocked_by = []
```

## 36.3 Failed dependency

```text
GrammarFre.gf:
  FAIL / direct

LangFre.gf first error:
  lib/src/french/GrammarFre.gf: inherited failure

LangFre.gf result:
  FAIL / downstream
  blocked_by = [GrammarFre.gf]
```

## 36.4 Reference to passing file

```text
NounFre.gf:
  OK

AllFre.gf first error:
  NounFre.gf: propagated context

AllFre.gf:
  FAIL / ambiguous
  blocked_by = []
```

## 36.5 Unresolved generic failure

```text
file:
  ExtraFre.gf

first error:
  compilation failed

error kind:
  OTHER

result:
  FAIL / ambiguous
```

## 36.6 Likely-local syntax failure

```text
file:
  StructuralFre.gf

error kind:
  SYNTAX

no other failed reference

result:
  FAIL / direct
```

## 36.7 Downstream chain

```text
MorphoFre.gf:
  direct

NounFre.gf:
  downstream -> MorphoFre.gf

GrammarFre.gf:
  downstream -> NounFre.gf
```

After collapse:

```text
GrammarFre.gf.blocked_by = [MorphoFre.gf]
```

## 36.8 Multiple direct roots

```text
MorphoFre.gf:
  direct

StructuralFre.gf:
  direct

GrammarFre.gf:
  downstream
  blocked_by = [MorphoFre.gf, StructuralFre.gf]
```

## 36.9 File timeout

```text
file:
  ExtendFre.gf

execution:
  timed_out

result:
  status = ERROR
  error_kind = TIMEOUT
  diagnostic_class = direct
```

Report label:

```text
Direct technical failure: compilation timed out.
```

## 36.10 Run-wide GF launch failure

```text
gf.exe cannot be launched
```

Preferred modeling:

```text
run-level TOOL error
file operations not started
```

Not:

```text
every source file = independent direct grammar failure
```

---

# 37. Test requirements

Recommended test structure:

```text
tests/diagnostics/
├── test_classification_status.py
├── test_direct_failures.py
├── test_downstream_failures.py
├── test_ambiguous_failures.py
├── test_blocker_resolution.py
├── test_root_collapse.py
├── test_reference_extraction.py
├── test_identity_normalization.py
├── test_error_kind_interaction.py
├── test_scope_limits.py
├── test_classifier_resilience.py
├── test_classifier_determinism.py
├── test_classification_schema.py
└── test_classification_reporting.py
```

## 37.1 Status tests

Verify:

- exit 0 and `OK` kind -> `OK/ok`;
- explicit skip -> `SKIPPED/skipped`;
- failure -> causal classification;
- timeout -> structured error;
- launch failure -> run-level technical error policy.

## 37.2 Direct tests

Verify:

- self full path;
- self basename;
- self module;
- `INTERNAL`;
- `TIMEOUT`;
- `SCRIPT`;
- `TYPE` with no blocker;
- `SYNTAX` with no blocker;
- no `blocked_by`;
- `is_direct = true`.

## 37.3 Downstream tests

Verify:

- full path to failed dependency;
- basename to failed dependency;
- module name to failed dependency;
- duplicate references;
- multiple blockers;
- failed blocker preferred over unrelated module-name noise;
- `is_direct = false`;
- non-empty `blocked_by`.

## 37.4 Ambiguous tests

Verify:

- reference to successful file;
- unknown reference;
- missing first error;
- generic `OTHER`;
- conflicting references;
- partial quick-mode scope;
- empty `blocked_by`.

## 37.5 Root-collapse tests

Verify:

- one-level blocker;
- multi-level chain;
- multiple roots;
- unresolved intermediate blocker;
- duplicate root;
- cycle;
- self-cycle;
- deterministic order.

## 37.6 Identity tests

Verify:

- Windows backslash;
- POSIX slash;
- case policy;
- project-relative path;
- duplicate module name;
- duplicate normalized file key;
- punctuation stripping.

## 37.7 Separation tests

Verify:

- scan findings do not force direct;
- report writers do not mutate classification;
- classifier does not launch GF;
- classifier does not read arbitrary referenced paths;
- error kind remains distinct from diagnostic class.

## 37.8 Legacy tests

Verify migration of:

```text
script_error
framework_error
```

without losing technical error information.

## 37.9 Determinism tests

Shuffle input result order and verify equivalent canonical output.

---

# 38. Current baseline compatibility

The current classifier already implements these important behaviors:

- initializes compile status;
- maps successful compile to `ok`;
- maps skipped compile to `skipped`;
- treats self-reference as direct;
- treats `INTERNAL`, `TIMEOUT`, and `SCRIPT` as obvious direct roots;
- treats referenced failed files as downstream;
- treats references to successful files as ambiguous;
- treats unresolved `TYPE` and `SYNTAX` as likely direct;
- extracts `.gf` references;
- indexes by file and module;
- collapses blocker chains to roots;
- prevents recursion through a visited set;
- normalizes display paths.

The final implementation must retain those useful behaviors while correcting these model boundaries:

1. canonical `ERROR` status must be supported;
2. technical error kinds remain separate from diagnostic class;
3. downstream blockers may include failed `ERROR` results where appropriate;
4. duplicate identities must fail clearly rather than silently keeping the first;
5. explicit skip state should replace reliance on text matching;
6. run-wide tool failures should not become many false file roots;
7. canonical classes exclude `script_error` and `framework_error`.

---

# 39. Reporting acceptance criteria

A final report is correct when:

```text
[ ] direct failures appear before downstream failures
[ ] each downstream failure names at least one blocker
[ ] root blockers are collapsed when known
[ ] ambiguous failures remain visible
[ ] technical roots are labeled accurately
[ ] raw evidence paths are present
[ ] scan findings remain separate
[ ] counts match result collections
[ ] reports do not reclassify
[ ] no unsupported causal statement is made
```

---

# 40. Anti-drift indicators

Probable drift exists when:

- a report decides whether a result is direct;
- `script_error` appears as a canonical diagnostic class;
- a downstream result has no blocker;
- a direct result contains blockers;
- a successful result is downstream;
- a scan hit changes compile status;
- a referenced successful file becomes a blocker;
- classification reruns GF;
- CLI and GUI show different causal classes from the same result;
- one component lowercases display paths and another preserves them;
- blocker chains are not cycle-safe;
- quick mode claims confirmed blockers outside its result scope;
- raw diagnostics are overwritten;
- error kind and diagnostic class are conflated;
- duplicate result identities are ignored;
- report prose is parsed to reconstruct blockers;
- classification changes when result order changes;
- a run-wide GF launch failure appears as many independent source roots.

Any drift indicator requires coordinated contract review.

---

# 41. Change-control workflow

A classification change must identify:

```text
Rule changed:
Current evidence threshold:
New evidence threshold:
Statuses affected:
Error kinds affected:
Path identity impact:
Blocked-by impact:
Root-collapse impact:
Schema impact:
Report impact:
Legacy impact:
Migration:
Tests:
```

Required checklist:

```text
[ ] classifier updated
[ ] shared status vocabulary reviewed
[ ] FileResult reviewed
[ ] RunResult counts reviewed
[ ] diagnostic parser reviewed
[ ] path normalization reviewed
[ ] persisted schema reviewed
[ ] interfile lock reviewed
[ ] report writers updated
[ ] GUI updated
[ ] regression comparison updated
[ ] unit tests updated
[ ] integration fixtures updated
[ ] migration documented
```

---

# 42. Implementation completion checklist

The direct/downstream classifier is complete when:

```text
[ ] canonical diagnostic classes are centralized
[ ] status and diagnostic class are separate
[ ] error kind and diagnostic class are separate
[ ] execution state and diagnostic class are separate
[ ] successful results become ok
[ ] skipped results become skipped
[ ] self references become direct
[ ] confirmed failed references become downstream
[ ] references to successful files become ambiguous
[ ] likely-local TYPE and SYNTAX behavior is tested
[ ] technical direct roots are labeled accurately
[ ] run-wide infrastructure failures are modeled once
[ ] blocker paths are canonical
[ ] downstream blockers are non-empty
[ ] direct blockers are empty
[ ] ambiguous blockers are empty
[ ] chains collapse to supported roots
[ ] cycles terminate safely
[ ] duplicates are removed deterministically
[ ] duplicate identities fail clearly
[ ] static scans do not drive causal status
[ ] classification is deterministic
[ ] raw evidence remains unchanged
[ ] reports are read-only observers
[ ] persisted output uses canonical vocabulary
[ ] legacy classes migrate
[ ] aggregate counts agree
[ ] tests pass on Windows-style and POSIX-style paths
```

---

# 43. Related documents

```text
docs/architecture/EXECUTION_FLOW.md
docs/architecture/DATA_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
docs/diagnostics/ERROR_CLASSIFICATION.md
docs/diagnostics/GF_DIAGNOSTIC_PARSING.md
docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md
docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md
docs/validation/COMPILATION_VALIDATION.md
docs/validation/REGRESSION_COMPARISON.md
docs/reports/REPORTING_OVERVIEW.md
docs/reference/STATUS_VALUES.md
docs/reference/DIAGNOSTIC_KINDS.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/MODULE_DEPENDENCY_MAP.md
SECURITY.md
```

---

# 44. Final rule

Direct/downstream classification exists to reduce failure cascades without inventing certainty.

Therefore:

> Mark a failure `direct` only when evidence supports the current subject as a local or technical root; mark it `downstream` only when another failed subject is a confirmed blocker; otherwise preserve it as `ambiguous`.
