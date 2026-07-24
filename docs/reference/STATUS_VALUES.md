# GF Wordbench — Status Values

**Document ID:** `GF-WB-REF-STATUS-VALUES`  
**Status:** Normative reference  
**Applies to:** GF Wordbench models, schemas, reports, CLI, GUI, validation stages, registered diagnostic tools, contract documents, migrations, and release gates  
**Primary owners:** shared domain models, diagnostics, runs, reporting, and persisted-schema layer  
**Canonical path:** `docs/reference/STATUS_VALUES.md`  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Canonical schema line:** `1.x`  
**Document version:** `1.1`  
**Last reviewed:** `2026-07-24`  

---

## 1. Purpose

This document defines the canonical status vocabularies used by GF Wordbench.

It prevents one word from carrying several incompatible meanings.

GF Wordbench distinguishes, at minimum:

```text
validation result
overall run result
external-process state
causal diagnostic classification
technical error kind
regression change
gold-comparison result
release-gate result
migration result
compatibility lifecycle
contract lifecycle
ADR lifecycle
```

These vocabularies are separate contracts.

A value from one vocabulary must not be copied into another merely because the wording seems similar.

The governing principle is:

> A status must answer one precise question, use one canonical value set, and remain separate from every other status dimension.

Every run and every subject status belongs to one active Wordbench project.
The independent `gf-portfolio` product may consume public completed artifacts,
but it does not define, mutate, or extend Wordbench runtime status vocabularies.
Portfolio aggregation state must not appear in Wordbench subject or process results.

This reference does not define coding-progress labels. Documentation and project
records must not classify capabilities as `implemented`, `partial`, `planned`,
`proposed`, `historical`, or `unknown`.

---

## 2. Canonical dimensions

| Dimension | Question answered | Canonical field |
|---|---|---|
| Validation status | Did the requested validation pass? | `status` or `validation_status` |
| Overall run status | Did the complete required run pass? | `overall_status` |
| Execution state | What happened to the external process attempt? | `execution_state` |
| Diagnostic class | Is the failure local, downstream, or unresolved? | `diagnostic_class` |
| Error kind | What technical category describes the failure? | `error_kind` |
| Regression change | How did the subject change from the baseline? | `change_kind` |
| Gold comparison | Did normalized actual output equal expected output? | `gold_match` |
| Release gate | Did one required release criterion pass? | `status` inside a gate result |
| Migration status | What did the migrator do? | `migration_status` |
| Compatibility lifecycle | How stable is a public surface? | `compatibility_status` |
| Contract lifecycle | What is the current contract state? | document `Status` |
| ADR lifecycle | What is the decision state? | ADR `Status` |

---

## 3. Case and serialization rules

Canonical values are case-sensitive.

### 3.1 Uppercase machine-result values

Use uppercase for:

```text
validation statuses
overall statuses
error kinds
```

Examples:

```text
OK
FAIL
ERROR
SKIPPED
TYPE
TIMEOUT
CONFIG
```

### 3.2 Lowercase machine-classification values

Use lowercase for:

```text
execution states
diagnostic classes
regression changes
migration statuses
```

Examples:

```text
completed
cancelled
direct
downstream
regressed
migrated
```

### 3.3 Title Case document metadata

Use Title Case for human-governance metadata:

```text
Active
Deprecated
Proposed
Accepted
Superseded
```

When a governance status is serialized into JSON, the owning schema defines its canonical case.

### 3.4 No spelling variants

Canonical writers must not emit variants such as:

```text
Success
SUCCESS
Passed
Pass
Failed
Failure
Err
Skipped by user
Canceled
Complete
Done
```

Readers may accept documented legacy aliases only through migration.

### 3.5 No numeric status codes in schemas

Persisted schemas use named strings.

CLI process exit codes are a separate interface.

---

# 4. Validation status

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

Canonical field:

```text
status
```

or, where ambiguity with another status exists:

```text
validation_status
```

---

## 5. `OK`

`OK` means:

```text
The requested validation executed sufficiently and every applicable required criterion for that subject passed.
```

Examples:

- a GF file compiled successfully;
- a scenario completed all required markers and assertions;
- a required gold comparison matched;
- a PGF build completed and the expected non-empty artifact exists;
- a release gate passed;
- a schema checker found the asset valid.

`OK` does not mean:

- no static scan findings exist;
- no warnings exist;
- the subject was not executed;
- an optional stage was omitted;
- the report writer guessed success from missing evidence.

Canonical implications for an executed subject:

```text
status = OK
execution_state = completed
error_kind = OK
diagnostic_class = ok
```

---

## 6. `FAIL`

`FAIL` means:

```text
The requested validation executed sufficiently and produced reliable evidence that one or more validation criteria did not pass.
```

Examples:

- GF completed a compile request and reported a grammar error;
- a required scenario command completed but an assertion failed;
- normalized output did not match the required gold;
- a required marker was absent after a completed GF shell process;
- the PGF process completed but the expected artifact was absent;
- a no-regression gate found a qualifying regression.

`FAIL` is a validation conclusion.

It is not the correct value when GF Wordbench could not execute or interpret the operation reliably.

Typical implications:

```text
status = FAIL
execution_state = completed
error_kind != OK
diagnostic_class = direct | downstream | ambiguous
```

A gold mismatch may use:

```text
error_kind = OTHER
```

unless a more specific canonical kind applies.

---

## 7. `ERROR`

`ERROR` means:

```text
GF Wordbench could not execute, complete, interpret, or preserve a required operation reliably enough to produce an ordinary validation conclusion.
```

Examples:

- GF executable could not launch;
- the process timed out;
- the operation was cancelled;
- configuration was invalid after run initialization;
- required input could not be decoded;
- a required report could not be written;
- manifest integrity could not be established;
- an unexpected framework exception prevented reliable completion;
- a required artifact path violated security containment;
- a required schema had an unsupported major version.

`ERROR` answers a reliability question.

It must not be downgraded to `FAIL` merely to simplify aggregation.

Typical implications:

```text
status = ERROR
error_kind != OK
```

Execution state depends on the failure:

```text
completed
timed_out
cancelled
launch_failed
null
```

The `null` form means no external process request was made.

---

## 8. `SKIPPED`

`SKIPPED` means:

```text
The operation was intentionally not executed under the resolved validation plan.
```

Examples:

- compilation was disabled by an allowed diagnostic option;
- an optional scenario was not selected;
- an optional release check was not applicable;
- an excluded noise file was represented explicitly as a result.

Canonical implications:

```text
status = SKIPPED
execution_state = null
error_kind = OK
diagnostic_class = skipped | noise
```

`SKIPPED` must not be counted as successful execution.

A required operation that was unexpectedly skipped normally makes the containing run:

```text
ERROR
```

unless the requirement explicitly allows non-applicability.

---

# 9. Validation-status decision table

| Condition | Validation status |
|---|---|
| Required criteria passed | `OK` |
| Operation completed and criteria failed | `FAIL` |
| Operation could not run or be interpreted reliably | `ERROR` |
| Operation intentionally not requested | `SKIPPED` |
| User cancelled operation | `ERROR` plus `execution_state=cancelled` |
| Operation timed out | `ERROR` plus `execution_state=timed_out` |
| GF launch failed | `ERROR` plus `execution_state=launch_failed` |
| Optional operation not selected | `SKIPPED` |
| Required operation absent because configuration is invalid | `ERROR` |
| Required artifact absent after otherwise completed execution | `FAIL` or `ERROR` according to evidence reliability |
| Static scan warning on a successful compile | `OK` with separate scan findings |

---

# 10. Validation status by subject

## 10.1 File result

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

## 10.2 Scenario result

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

## 10.3 PGF result

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

`SKIPPED` is valid only outside a mode that requires PGF construction.

## 10.4 Release gate

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

A required release gate cannot remain `SKIPPED` in a successful release.

## 10.5 Report writer

A structured report-write result may reuse:

```text
OK
ERROR
SKIPPED
```

`FAIL` is normally unnecessary because report generation is not a linguistic validation criterion.

If a writer contract is executed but produces an invalid artifact, `ERROR` is preferred because artifact reliability is not established.

## 10.6 Schema checker

Canonical command-level result:

```text
OK
FAIL
ERROR
```

Asset-level statuses may use:

```text
OK
FAIL
ERROR
SKIPPED
```

when an optional check is not applicable.

---

# 11. Overall run status

Canonical values:

```text
OK
FAIL
ERROR
```

Canonical field:

```text
overall_status
```

A finalized run does not normally use:

```text
SKIPPED
```

as its overall status.

---

## 12. Overall `OK`

Overall `OK` means:

- every required validation subject is `OK`;
- every required release gate is `OK` when release mode applies;
- required reports are valid;
- required manifest policy is satisfied;
- no required execution remains cancelled, timed out, or unresolved;
- optional failures are permitted only when project policy explicitly says they do not affect overall status.

---

## 13. Overall `FAIL`

Overall `FAIL` means:

- no required infrastructure or interpretation error outranks the result;
- one or more required validation criteria are `FAIL`.

Examples:

- required file compilation failed;
- required scenario assertion failed;
- required gold mismatch;
- required PGF artifact validation failed after reliable execution;
- explicit regression gate failed.

---

## 14. Overall `ERROR`

Overall `ERROR` means:

- at least one required operation is `ERROR`;
- or the run cannot be trusted as a complete validation result.

Examples:

- GF could not launch;
- required process timed out;
- run was cancelled;
- required result classification failed;
- required report or manifest could not be finalized;
- result counts are internally inconsistent;
- output containment was violated.

---

## 15. Overall-status precedence

Canonical precedence:

```text
ERROR
>
FAIL
>
OK
```

Aggregation:

```python
if any(required.status == "ERROR"):
    overall_status = "ERROR"
elif any(required.status == "FAIL"):
    overall_status = "FAIL"
else:
    overall_status = "OK"
```

Required `SKIPPED` subjects must be resolved before terminal aggregation.

Unexpected required skip normally becomes:

```text
ERROR
```

---

## 16. Optional subjects

An optional subject may have:

```text
OK
FAIL
ERROR
SKIPPED
```

Its effect on overall status is project policy.

The policy must be explicit.

Recommended default:

| Optional subject result | Overall effect |
|---|---|
| `OK` | none |
| `SKIPPED` | none |
| `FAIL` | warning unless configured as blocking |
| `ERROR` | warning or `ERROR` according to whether shared run reliability was affected |

An optional subject must not silently become required through report wording.

---

# 17. Execution state

Canonical field:

```text
execution_state
```

Canonical non-null values:

```text
completed
timed_out
cancelled
launch_failed
```

The field may be:

```text
null
```

when no external process request was made.

Execution state answers:

```text
What happened to the external process attempt?
```

It does not answer whether validation passed.

---

## 18. `completed`

`completed` means:

- the process launched;
- GF Wordbench observed process termination;
- an exit code or equivalent completed result is available;
- stdout and stderr capture completed according to policy.

`completed` may accompany:

```text
OK
FAIL
ERROR
```

Examples:

```text
OK + completed
FAIL + completed
ERROR + completed
```

The third combination applies when the process completed but its response violated a required contract or could not be interpreted reliably.

---

## 19. `timed_out`

`timed_out` means:

- the process launched;
- the configured finite timeout elapsed;
- GF Wordbench initiated termination;
- partial evidence was preserved where possible.

Canonical combination:

```text
status = ERROR
execution_state = timed_out
error_kind = TIMEOUT
```

A timeout is not a normal GF validation failure.

---

## 20. `cancelled`

`cancelled` means:

- the user or controlling system requested cancellation;
- the request was accepted by the orchestrator;
- no new stages should begin;
- owned processes were terminated or termination was attempted;
- partial evidence was preserved where possible.

Canonical combination:

```text
status = ERROR
execution_state = cancelled
error_kind = OTHER
```

A dedicated cancellation error kind requires a versioned enum change.

`CANCELLED` is not a canonical validation status.

---

## 21. `launch_failed`

`launch_failed` means:

- GF Wordbench attempted to start the external executable;
- the operating system or process layer could not create the process.

Canonical combination:

```text
status = ERROR
execution_state = launch_failed
error_kind = TOOL
```

Examples:

- executable missing;
- permission denied;
- invalid executable format;
- process-creation failure.

---

## 22. No process attempt

When no process request was made:

```text
execution_state = null
```

Examples:

- optional scenario not selected;
- configuration failed before launch;
- prohibited script command detected during preflight;
- compilation intentionally disabled.

Typical combinations:

```text
SKIPPED + null + OK
ERROR + null + CONFIG
ERROR + null + IO
```

The noncanonical value:

```text
not_started
```

may be accepted from development or legacy data.

Canonical migration:

```text
execution_state = null
```

with validation status and error kind preserving the reason.

---

# 23. Execution-state invariants

```text
timed_out   -> status = ERROR and error_kind = TIMEOUT
cancelled   -> status = ERROR
launch_failed -> status = ERROR and error_kind = TOOL
null + SKIPPED -> operation intentionally omitted
null + ERROR -> pre-execution failure
completed + OK -> ordinary success
completed + FAIL -> reliable validation failure
```

Invalid combinations include:

```text
status = OK, execution_state = timed_out
status = OK, execution_state = cancelled
status = FAIL, execution_state = launch_failed
status = SKIPPED, execution_state = completed
execution_state = timed_out, error_kind = OK
```

---

# 24. Diagnostic class

Canonical field:

```text
diagnostic_class
```

Canonical values:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Diagnostic class answers:

```text
What is the causal relationship of this result to the currently observed failure set?
```

It does not identify the technical error category.

---

## 25. `ok`

Use when:

```text
status = OK
```

Canonical combination:

```text
status = OK
diagnostic_class = ok
is_direct = false
blocked_by = []
```

---

## 26. `direct`

Use when evidence supports the subject as:

- a local validation root;
- a direct technical root;
- the closest supported unresolved root in the current scope.

Canonical combination:

```text
status = FAIL | ERROR
diagnostic_class = direct
is_direct = true
blocked_by = []
```

`direct` does not prove no external condition contributed.

---

## 27. `downstream`

Use when another failed subject is a supported blocker.

Canonical combination:

```text
status = FAIL | ERROR
diagnostic_class = downstream
is_direct = false
blocked_by = [one or more canonical subject identities]
```

A downstream result with an empty blocker list is invalid.

---

## 28. `ambiguous`

Use when evidence does not justify `direct` or `downstream`.

Canonical combination:

```text
status = FAIL | ERROR
diagnostic_class = ambiguous
is_direct = false
blocked_by = []
```

Ambiguity is not a framework error.

It is an honest causal classification.

---

## 29. `noise`

Use when a file or candidate is excluded as non-actionable input under selection policy.

Examples:

- backup file;
- temporary copy;
- disabled source;
- known generated noise.

If represented as a validation result:

```text
status = SKIPPED
diagnostic_class = noise
is_direct = false
```

Noise may be recorded only in selection counts rather than as a `FileResult`.

---

## 30. `skipped`

Use when the operation was intentionally not executed.

Canonical combination:

```text
status = SKIPPED
diagnostic_class = skipped
is_direct = false
blocked_by = []
```

---

# 31. Diagnostic-class migration

The following values are noncanonical:

```text
script_error
framework_error
timeout
tool_error
configuration_error
```

They combine technical nature with causal relationship.

Migration:

```text
technical meaning -> error_kind
causal meaning -> diagnostic_class
execution outcome -> execution_state
```

Example:

```text
legacy diagnostic_class = script_error
```

may become:

```text
error_kind = SCRIPT
diagnostic_class = direct
```

or:

```text
error_kind = SCRIPT
diagnostic_class = ambiguous
```

according to evidence.

Example:

```text
legacy diagnostic_class = framework_error
```

may become:

```text
error_kind = INTERNAL | CONFIG | IO | TOOL
diagnostic_class = direct | downstream | ambiguous
```

No canonical writer emits `script_error` or `framework_error`.

---

# 32. Error kind

Canonical field:

```text
error_kind
```

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

Error kind answers:

```text
What immediate technical category best describes the result?
```

---

## 33. `OK` error kind

Use only when no technical error applies.

Typical combinations:

```text
status = OK
error_kind = OK
```

or:

```text
status = SKIPPED
error_kind = OK
```

Invalid:

```text
status = FAIL
error_kind = OK
```

unless a specific validation criterion failed without a technical error and the model explicitly uses `OTHER` instead.

Preferred for such failures:

```text
error_kind = OTHER
```

---

## 34. `OTHER`

Use when:

- a real failure exists;
- no more specific canonical kind applies.

Examples:

- gold mismatch;
- semantic assertion failure;
- expected output absent;
- cancellation until a dedicated kind exists;
- generic nonzero GF failure not classified more specifically.

`OTHER` must not become a substitute for missing diagnostic work when a specific kind is available.

---

## 35. `TYPE`

Use for GF type-checking and type-unification failures.

Examples:

- type mismatch;
- invalid constructor type;
- lincat incompatibility;
- unification failure.

A `TYPE` failure may be direct or downstream.

---

## 36. `SYNTAX`

Use for source syntax or parse-of-source failures reported by GF.

Examples:

- malformed GF source;
- invalid token sequence;
- unmatched syntax construct.

A `SYNTAX` failure may be direct or downstream when the diagnostic points to another failed source.

---

## 37. `INTERNAL`

Use for:

- GF internal failure;
- invariant violation inside GF Wordbench;
- unexpected framework failure when no more specific kind applies.

Prefer a run-level error for shared framework failures.

Do not classify every affected file as an independent internal failure.

---

## 38. `TIMEOUT`

Use only when:

```text
execution_state = timed_out
```

Canonical:

```text
status = ERROR
error_kind = TIMEOUT
```

---

## 39. `SCRIPT`

Use for:

- invalid scenario command contract;
- missing required scenario marker;
- scenario-script interpretation failure;
- orchestration script failure scoped to the subject.

It does not mean Python traceback text should be parsed as a GF failure.

---

## 40. `CONFIG`

Use for:

- invalid resolved configuration;
- missing required project registration;
- invalid mode/option combination represented after run creation;
- unsupported required schema configuration;
- invalid project-owned path declaration.

Configuration errors detected before run initialization normally produce CLI exit code `2` without subject results.

---

## 41. `IO`

Use for:

- read failure;
- write failure;
- encoding/decoding failure;
- filesystem permission failure after path policy passes;
- disk or artifact stream failure.

A path-security violation may use `CONFIG`, `IO`, or `TOOL` according to the owning contract, but the mapping must be centralized and tested.

---

## 42. `TOOL`

Use for:

- external executable launch failure;
- missing required external tool;
- unsupported tool capability;
- external-tool contract failure not represented by `TYPE`, `SYNTAX`, or `TIMEOUT`;
- required tool-generated artifact failure when the tool boundary is the cause.

Do not use `TOOL` merely because GF reported an ordinary grammar failure.

---

# 43. Error-kind precedence

When several descriptions apply, choose the most specific supported kind.

Recommended precedence:

```text
TIMEOUT
CONFIG
IO
TOOL
SCRIPT
SYNTAX
TYPE
INTERNAL
OTHER
```

This is not a causal severity order.

It is a classification preference.

A parser may prefer `TYPE` or `SYNTAX` over generic `TOOL` when GF executed normally and reported a source diagnostic.

---

# 44. Diagnostic class versus error kind

Valid examples:

```text
FAIL + direct + TYPE
FAIL + downstream + TYPE
FAIL + ambiguous + OTHER
ERROR + direct + TIMEOUT
ERROR + ambiguous + TOOL
FAIL + direct + SCRIPT
```

Invalid conceptual combinations:

```text
diagnostic_class = timeout
diagnostic_class = framework_error
error_kind = downstream
error_kind = direct
```

---

# 45. Canonical subject combination matrix

| Status | Execution state | Diagnostic class | Error kind | Typical meaning |
|---|---|---|---|---|
| `OK` | `completed` | `ok` | `OK` | Validation passed |
| `FAIL` | `completed` | `direct` | `TYPE` | Local GF type failure |
| `FAIL` | `completed` | `downstream` | `TYPE` | Propagated type failure |
| `FAIL` | `completed` | `ambiguous` | `OTHER` | Reliable failure, unclear cause |
| `ERROR` | `timed_out` | `direct` or `ambiguous` | `TIMEOUT` | Process timeout |
| `ERROR` | `launch_failed` | `ambiguous` | `TOOL` | Process never launched |
| `ERROR` | `cancelled` | `ambiguous` | `OTHER` | User/system cancellation |
| `ERROR` | `null` | `direct` or `ambiguous` | `CONFIG` | Pre-execution configuration error |
| `SKIPPED` | `null` | `skipped` | `OK` | Intentionally omitted |
| `SKIPPED` | `null` | `noise` | `OK` | Excluded noise represented as a result |

The exact causal class for an `ERROR` depends on available evidence.

---

# 46. Regression change kind

Canonical field:

```text
change_kind
```

Canonical values:

```text
unchanged
improved
regressed
new
removed
```

Regression change compares compatible subject results across two runs.

It does not replace current validation status.

---

## 47. `unchanged`

Use when the primary validation status remains equivalent.

Details may still change:

- error kind;
- diagnostic class;
- blocker set;
- first error;
- source fingerprint;
- required flag;
- GF version;
- normalization version.

Example:

```text
FAIL/direct -> FAIL/downstream
change_kind = unchanged
```

---

## 48. `improved`

Use for a documented favorable status transition.

Canonical strong cases:

```text
FAIL -> OK
ERROR -> OK
```

Conditional case:

```text
ERROR -> FAIL
```

may be `improved` when execution is now reliable but validation still fails.

The message must explain the transition.

---

## 49. `regressed`

Use for a documented unfavorable transition.

Canonical strong cases:

```text
OK -> FAIL
OK -> ERROR
FAIL -> ERROR
```

Transitions involving `SKIPPED` require required/optional and scope context.

---

## 50. `new`

Use when a subject is absent from the baseline and present in the current comparable scope.

`new` does not itself mean good or bad.

The current status remains separate.

---

## 51. `removed`

Use when a subject is present in the baseline and absent from the current comparable scope.

`removed` does not prove rename, deletion intent, or improvement.

---

# 52. Regression transition summary

| Previous | Current | Typical change |
|---|---|---|
| `OK` | `OK` | `unchanged` |
| `OK` | `FAIL` | `regressed` |
| `OK` | `ERROR` | `regressed` |
| `FAIL` | `OK` | `improved` |
| `FAIL` | `FAIL` | `unchanged` |
| `FAIL` | `ERROR` | `regressed` |
| `ERROR` | `OK` | `improved` |
| `ERROR` | `FAIL` | `improved` or `unchanged` with detail |
| `ERROR` | `ERROR` | `unchanged` |
| absent | present | `new` |
| present | absent | `removed` |

Full rules belong to:

```text
docs/validation/REGRESSION_COMPARISON.md
```

---

# 53. Gold comparison

Canonical persisted field:

```text
gold_match
```

Canonical values:

```text
true
false
null
```

Meaning:

```text
true  = normalized actual output matched expected gold
false = comparison executed and mismatched
null  = no comparison applied or comparison could not be reached
```

`gold_match` is not a validation status.

---

## 54. Human gold labels

Reports may render:

```text
Match
Mismatch
Not required
Missing
Not compared
```

These are display labels derived from structured fields.

They must not become competing persisted enum values without a schema change.

Recommended derivation:

| Condition | Display |
|---|---|
| `gold_match=true` | `Match` |
| `gold_match=false` | `Mismatch` |
| no gold required | `Not required` |
| required gold path absent | `Missing` |
| comparison not reached | `Not compared` |

A missing required gold normally causes:

```text
status = ERROR
error_kind = CONFIG
```

or the exact owning contract’s documented mapping.

A gold mismatch normally causes:

```text
status = FAIL
error_kind = OTHER
```

---

# 55. Marker-section status

Canonical section fields should remain simple:

```text
begin_seen: bool
end_seen: bool
completed: bool
```

A separate section-status enum is unnecessary initially.

Derivation:

```text
completed = begin_seen and end_seen and order_valid
```

A required section with:

```text
completed = false
```

causes the scenario to be:

```text
FAIL
```

or:

```text
ERROR
```

according to whether the script executed reliably enough to establish the contract failure.

---

# 56. Release-gate status

A release gate reuses validation status:

```text
OK
FAIL
ERROR
SKIPPED
```

The gate also has:

```text
required: bool
```

Recommended combinations:

| Required | Status | Release implication |
|:---:|---|---|
| Yes | `OK` | Gate passed |
| Yes | `FAIL` | Release overall `FAIL` |
| Yes | `ERROR` | Release overall `ERROR` |
| Yes | `SKIPPED` | Invalid terminal state; resolve to `ERROR` |
| No | `OK` | Optional gate passed |
| No | `FAIL` | Warning or policy-defined failure |
| No | `ERROR` | Warning or run `ERROR` if reliability affected |
| No | `SKIPPED` | Acceptable |

A release gate must not invent:

```text
PASS
BLOCKED
PENDING
```

as validation statuses.

A pre-release planning document may use those terms in a separate lifecycle field.

---

# 57. Artifact existence and integrity

Artifact validation reuses validation status.

Examples:

```text
OK
  expected artifact exists and satisfies contract

FAIL
  process completed reliably but artifact criterion failed

ERROR
  artifact could not be inspected or integrity could not be established

SKIPPED
  optional artifact check not applicable
```

Manifest entry fields such as:

```text
required
```

are booleans, not statuses.

---

# 58. Migration status

Canonical field:

```text
migration_status
```

Canonical values:

```text
unchanged
migrated
migrated_with_warnings
failed
```

---

## 59. `unchanged` migration

Use when the input is already canonical and no rewrite is required.

---

## 60. `migrated`

Use when:

- conversion completed;
- target validates;
- no semantic losses or unresolved warnings remain.

---

## 61. `migrated_with_warnings`

Use when:

- target is usable and valid;
- non-fatal assumptions, legacy gaps, or preserved uncertainties exist;
- every warning is reported.

This must not hide required semantic loss.

---

## 62. `failed` migration

Use when:

- target could not be produced safely;
- required meaning could not be preserved;
- validation failed;
- writing or integrity failed.

The source remains unchanged.

---

## 63. Migration losses

Loss reporting is separate from `migration_status`.

Recommended fields:

```text
warnings: []
losses: []
```

A migration with a required unresolved loss must be:

```text
failed
```

It must not claim:

```text
migrated
```

---

# 64. Compatibility lifecycle

Canonical conceptual values:

```text
stable
provisional
experimental
deprecated
retired
internal
```

Canonical field when serialized:

```text
compatibility_status
```

This vocabulary describes a public surface’s compatibility guarantee.

It changes only when the public compatibility guarantee changes. It must not be
used to report coding progress or temporary development state.

It never appears as a validation status.

---

## 65. `stable`

The surface follows normal backward-compatibility policy.

---

## 66. `provisional`

The surface is expected to stabilize but may still change before a declared milestone.

---

## 67. `experimental`

The surface is opt-in and may change in a compatible framework minor release according to experimental policy.

Experimental persisted data still requires an explicit schema.

---

## 68. `deprecated`

The surface remains supported temporarily and has:

- a replacement;
- a warning;
- a removal target;
- compatibility tests.

---

## 69. `retired`

The surface is no longer accepted by normal current interfaces.

Historical migrators may still recognize it.

---

## 70. `internal`

The surface has no public compatibility promise.

Importability alone does not make it stable.

---

# 71. Contract lifecycle status

Framework and external-tool contract documents use:

```text
Active
Experimental
Deprecated
Retired
```

Project contract documents may additionally use:

```text
Blocked
```

when a required external dependency, unresolved contract contradiction, missing
evidence, or failed release prerequisite prevents the contract from being
satisfied.

`Blocked` is project-governance metadata. It does not describe coding progress.

It is not a validation status.

---

## 72. Contract `Active`

The contract governs current supported behavior.

For a stable release, every required contract must be `Active`, `Deprecated`, or `Retired` as appropriate.

---

## 73. Contract `Experimental`

The contract is opt-in and not part of ordinary stable guarantees.

A release may contain experimental optional contracts when release policy permits them.

A required release path must not depend on an experimental contract unless the release policy explicitly permits it.

---

## 74. Contract `Deprecated`

The contract remains supported during migration but should not receive new consumers.

It must identify the replacement and removal plan.

---

## 75. Contract `Retired`

The contract no longer governs current execution.

Its identifier must never be reused.

---

## 76. Project contract `Blocked`

Use when:

- the intended contract is documented;
- a named blocker prevents the required contract evidence from being established;
- current release gates cannot claim satisfaction;
- the blocker and its owning authority are recorded explicitly.

Do not use `Blocked` for unfinished coding, planned work, or general progress tracking.

A blocked required project contract prevents release readiness.

Do not use `Blocked` as a substitute for:

```text
FAIL
ERROR
SKIPPED
```

inside run results.

---

# 77. Contract applicability

The word:

```text
Conditional
```

describes applicability, not lifecycle.

Recommended separate field:

```text
applicability = required | conditional | optional
```

Therefore, a contract may be:

```text
Status: Active
Applicability: Conditional
```

Canonical contract registries should not use `Conditional` as if it were the same dimension as `Active` or `Deprecated`.

Legacy registry rows may be normalized during documentation cleanup.

---

# 78. ADR status

Canonical ADR statuses:

```text
Proposed
Accepted
Rejected
Deprecated
Superseded
```

These values govern architecture decisions.

They do not appear in runtime schemas.

---

## 79. ADR `Proposed`

Decision is under review and not yet authoritative.

---

## 80. ADR `Accepted`

Decision is approved and governs architecture, code, tests, and documentation until it is deprecated or superseded.

---

## 81. ADR `Rejected`

Proposal was reviewed and not selected.

---

## 82. ADR `Deprecated`

Decision remains historical but should not guide new work.

---

## 83. ADR `Superseded`

A later accepted ADR replaces the decision.

Reciprocal links are required.

---

# 84. Documentation status

Normative documents may use:

```text
Normative
Reference
Guide
Draft
Deprecated
Retired
```

This vocabulary is document metadata only.

Canonical document roles include:

```text
Normative reference
Normative specification
Normative policy
Guide
```

A draft document must not be cited as an active locked contract.

---

# 85. Release maturity

Framework release maturity is represented by the version:

```text
.devN
aN
bN
rcN
stable version without suffix
```

Human labels:

```text
Development
Alpha
Beta
Release Candidate
Stable
```

These are release-channel values, not validation statuses.

---

# 86. Project status ledger

`project/docs/STATUS_LEDGER__PROJECT_DOCS.md` records project-owned validation facts, known
release blockers, accepted exceptions, evidence references, and resolution
history.

It uses the canonical runtime and release vocabularies defined by this reference,
including:

```text
OK
FAIL
ERROR
SKIPPED
open
resolved
accepted_exception
```

The project ledger must not track coding progress with labels such as:

```text
implemented
partial
planned
proposed
temporary
fallback
historical
unknown
```

A project record changes only when its validation fact, blocker, exception, or
resolution changes. Ordinary code edits do not require a documentation-status
transition.

---

# 87. Warning severity

Warnings should not be represented through validation status alone.

A structured warning may use:

```text
info
warning
```

Errors that affect required reliability belong in:

```text
status = ERROR
```

Avoid adding an unnecessary multi-level warning taxonomy until a real consumer requires it.

---

# 88. CLI exit codes

CLI exit codes are not status strings.

Canonical mapping:

| Exit code | Meaning |
|---:|---|
| `0` | Command succeeded and required validation passed |
| `1` | Required validation failed |
| `2` | Usage, configuration, schema, or requested-contract error |
| `3` | Runtime, external-tool, timeout, cancellation, I/O, or integrity error |

Mapping from run status:

```text
overall_status = OK    -> 0
overall_status = FAIL  -> 1
overall_status = ERROR -> 3
```

Pre-run invocation/configuration errors:

```text
2
```

Do not serialize the CLI exit code as a replacement for `overall_status`.

---

# 89. Status ownership

| Status domain | Owner |
|---|---|
| Validation status | Shared result models |
| Overall status | Run-result builder |
| Execution state | Process runner / operation result |
| Diagnostic class | Classifier |
| Error kind | Diagnostic parser and owning operation |
| Regression change | Diff component |
| Gold match | Gold comparator |
| Release-gate status | Release-gate evaluator |
| Migration status | Schema migrator |
| Compatibility lifecycle | Compatibility policy owner |
| Contract lifecycle | Contract-lock owner |
| ADR status | ADR process owner |
| CLI exit code | CLI adapter |

A downstream consumer may display a value.

It must not redefine it.

---

# 90. Status derivation ownership

Examples:

```text
process runner
    -> execution_state

GF diagnostic parser
    -> error_kind candidate

file/scenario result builder
    -> validation status

causal classifier
    -> diagnostic_class

run result builder
    -> overall_status

diff component
    -> change_kind

report writers
    -> display only
```

Report writers must not infer a new status from prose.

GUI and CLI must consume structured fields.

---

# 91. In-memory enum recommendations

Recommended Python definitions:

```python
from enum import StrEnum


class ValidationStatus(StrEnum):
    OK = "OK"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class OverallStatus(StrEnum):
    OK = "OK"
    FAIL = "FAIL"
    ERROR = "ERROR"


class ExecutionState(StrEnum):
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    LAUNCH_FAILED = "launch_failed"


class DiagnosticClass(StrEnum):
    OK = "ok"
    DIRECT = "direct"
    DOWNSTREAM = "downstream"
    AMBIGUOUS = "ambiguous"
    NOISE = "noise"
    SKIPPED = "skipped"


class ErrorKind(StrEnum):
    OK = "OK"
    OTHER = "OTHER"
    TYPE = "TYPE"
    SYNTAX = "SYNTAX"
    INTERNAL = "INTERNAL"
    TIMEOUT = "TIMEOUT"
    SCRIPT = "SCRIPT"
    CONFIG = "CONFIG"
    IO = "IO"
    TOOL = "TOOL"


class ChangeKind(StrEnum):
    UNCHANGED = "unchanged"
    IMPROVED = "improved"
    REGRESSED = "regressed"
    NEW = "new"
    REMOVED = "removed"
```

`execution_state` remains optional when no process was launched.

The exact module path is owned by the shared-model architecture.

---

# 92. Constants versus raw strings

Core application code should use centralized enums or validated constants.

Acceptable boundary usage:

```python
ValidationStatus(raw_value)
```

Avoid scattered comparisons:

```python
if status == "failed":
if status == "Fail":
if status in ("ERROR", "CANCELLED"):
```

Canonical normalization occurs at input boundaries.

---

# 93. Schema rules

Persisted schemas must:

- define each allowed enum;
- reject unknown values in strict mode;
- document tolerant-reader behavior;
- version any meaning change;
- never silently map unknown values to `OK`;
- preserve legacy source evidence during migration;
- emit only canonical values.

Adding an enum value requires:

- schema minor version at minimum;
- reader review;
- writer review;
- report review;
- migration/compatibility tests.

Removing or redefining a value requires a schema major version.

---

# 94. Unknown status values

## 94.1 Strict mode

Reject unknown values.

Example:

```text
unknown validation status: CANCELLED
```

## 94.2 Tolerant legacy reader

A tolerant reader may:

- identify a registered legacy alias;
- migrate it;
- record a warning.

It must not guess an unregistered value.

## 94.3 Newer schema

If a newer minor schema contains an unknown optional enum:

- preserve or reject according to schema policy;
- do not reinterpret it as a known status.

---

# 95. Legacy migration table

| Legacy/noncanonical value | Canonical representation |
|---|---|
| `CANCELLED` validation status | `status=ERROR`, `execution_state=cancelled`, `error_kind=OTHER` |
| `TIMEOUT` validation status | `status=ERROR`, `execution_state=timed_out`, `error_kind=TIMEOUT` |
| `SUCCESS` | `OK` only when old contract proves equivalent meaning |
| `PASSED` | `OK` only through registered migration |
| `FAILED` | `FAIL` only through registered migration |
| `not_started` execution state | `execution_state=null` plus canonical status/reason |
| `script_error` diagnostic class | `error_kind=SCRIPT` plus evidence-based causal class |
| `framework_error` diagnostic class | technical error kind plus evidence-based causal class |
| `blocked` validation status | `FAIL`/`ERROR`/`SKIPPED` by execution evidence; blocker stored separately |
| `Conditional` contract status | lifecycle status plus `applicability=conditional` |
| `file` validation mode | `quick` mode; not a status |
| `all` validation mode | `diagnostic` mode; not a status |

Migration warnings must identify the original value.

---

# 96. `CANCELLED` harmonization

Some earlier external-tool documentation listed:

```text
CANCELLED
```

beside:

```text
OK
FAIL
ERROR
SKIPPED
```

The canonical model separates it.

Canonical:

```text
validation_status = ERROR
execution_state = cancelled
```

Reason:

- cancellation does not mean validation criteria failed;
- cancellation does not mean the operation was intentionally omitted;
- cancellation means required execution reliability was interrupted.

Every contract, schema, model, report, and test must use the canonical separation.

---

# 97. `framework_error` harmonization

Some earlier persisted-schema drafts included:

```text
diagnostic_class = framework_error
```

The canonical diagnostic vocabulary excludes it.

Canonical representation:

```text
status = ERROR
error_kind = INTERNAL | CONFIG | IO | TOOL
diagnostic_class = direct | downstream | ambiguous
execution_state = appropriate value or null
```

The exact causal class depends on evidence.

This preserves the four independent dimensions.

---

# 98. `not_started` harmonization

Some development documents use:

```text
execution_state = not_started
```

The canonical persisted execution-state vocabulary uses:

```text
null
```

when no external process request occurred.

Reason:

- `not_started` combines absence of execution with a reason;
- the reason already belongs to validation status, error kind, and message;
- optionality remains in the stage specification or `required` field.

Human reports may display:

```text
Not started
```

as a label derived from:

```text
execution_state = null
```

---

# 99. Validation invariants

Required checks:

```text
status=OK -> error_kind=OK
status=OK -> diagnostic_class=ok
status=SKIPPED -> execution_state=null
status=SKIPPED -> error_kind=OK
status=SKIPPED -> diagnostic_class=skipped|noise
execution_state=timed_out -> status=ERROR
execution_state=timed_out -> error_kind=TIMEOUT
execution_state=cancelled -> status=ERROR
execution_state=launch_failed -> status=ERROR
execution_state=launch_failed -> error_kind=TOOL
diagnostic_class=downstream -> blocked_by non-empty
diagnostic_class=direct -> is_direct=true
diagnostic_class!=direct -> is_direct=false
diagnostic_class=direct -> blocked_by empty
diagnostic_class=ambiguous -> blocked_by empty
```

---

# 100. Count invariants

File totals:

```text
files_included
=
files_ok
+ files_fail
+ files_error
+ files_skipped
```

Scenario totals:

```text
scenarios_seen
=
scenarios_ok
+ scenarios_fail
+ scenarios_error
+ scenarios_skipped
```

Diagnostic failure counts apply to:

```text
FAIL
ERROR
```

according to the result-model specification.

A subject appears once in status counts.

Noise excluded before inclusion is not part of `files_included`.

---

# 101. Report rendering

Reports display canonical strings in inline code:

```markdown
`OK`
`FAIL`
`ERROR`
`SKIPPED`
`direct`
`TIMEOUT`
```

Reports may add human explanations.

They must not replace the canonical value with localized or decorative wording.

Color and icons are optional presentation.

Plain text remains authoritative for human interpretation.

---

# 102. GUI rendering

The GUI may render friendly labels:

```text
Passed
Validation failed
Execution error
Skipped
```

It must retain the underlying canonical value.

Filters, sorting, exports, and comparisons use canonical fields.

The GUI must not persist translated labels as status values.

---

# 103. CLI rendering

The CLI prints canonical status strings.

Example:

```text
Status: FAIL
```

Exit codes remain separate.

The CLI must not infer status by parsing a report artifact when `RunResult` is available.

---

# 104. AI report rendering

`AI_READY.md` must preserve canonical statuses.

Example:

```text
status = FAIL
diagnostic_class = downstream
error_kind = TYPE
```

It may explain their meaning.

It must not simplify:

```text
ERROR
```

into:

```text
FAIL
```

or remove the distinction between direct and downstream failures.

---

# 105. Sorting and severity

Recommended validation display order:

```text
ERROR
FAIL
SKIPPED
OK
```

Recommended diagnostic display order:

```text
direct
ambiguous
downstream
skipped
noise
ok
```

Recommended regression display order:

```text
regressed
new
improved
removed
unchanged
```

These are presentation orders.

They do not redefine enum meaning.

---

# 106. Tests

Recommended test structure:

```text
tests/status/
├── test_validation_status.py
├── test_overall_status.py
├── test_execution_state.py
├── test_diagnostic_class.py
├── test_error_kind.py
├── test_status_combinations.py
├── test_status_aggregation.py
├── test_regression_change_kind.py
├── test_gold_state.py
├── test_release_gate_status.py
├── test_migration_status.py
├── test_contract_status.py
├── test_adr_status.py
├── test_status_serialization.py
├── test_status_migrations.py
└── test_status_reporting.py
```

---

# 107. Required test cases

## 107.1 Validation status

```text
OK
FAIL
ERROR
SKIPPED
unknown value
wrong case
legacy alias
```

## 107.2 Execution state

```text
completed
timed_out
cancelled
launch_failed
null
legacy not_started
```

## 107.3 Combinations

Test every canonical row in the subject combination matrix.

Reject impossible combinations.

## 107.4 Aggregation

Test:

- all required `OK`;
- one required `FAIL`;
- one required `ERROR`;
- optional `FAIL`;
- optional `ERROR`;
- required `SKIPPED`;
- release gate `ERROR`;
- manifest failure;
- cancelled run.

## 107.5 Diagnostic classes

Test:

- direct with no blockers;
- downstream with blockers;
- downstream without blockers;
- ambiguous;
- noise;
- skipped;
- `is_direct` consistency.

## 107.6 Migration

Test:

- `CANCELLED`;
- `not_started`;
- `script_error`;
- `framework_error`;
- wrong case;
- unregistered unknown value;
- canonical writer emits no legacy value.

---

# 108. Schema fixtures

Recommended fixture directories:

```text
tests/fixtures/status/canonical/
tests/fixtures/status/legacy/
tests/fixtures/status/invalid/
```

Legacy fixtures remain unchanged after migration tests.

Canonical fixtures use only current values.

---

# 109. Status checker

The schema checker should validate status combinations.

Suggested command:

```text
gf-wordbench schemas check <asset>
```

Checks:

- value belongs to correct enum;
- case is canonical;
- field belongs to correct status dimension;
- cross-field invariants hold;
- no legacy value is emitted by a current writer;
- count invariants hold;
- overall status agrees with required subject results;
- release status agrees with required gates.

---

# 110. Anti-drift indicators

Probable status drift exists when:

- two files use different strings for the same result;
- `CANCELLED` appears as a validation status;
- `not_started` appears in canonical persisted execution state;
- `framework_error` appears as a diagnostic class;
- `script_error` appears as a diagnostic class;
- a report changes `ERROR` to `FAIL`;
- GUI stores translated labels;
- CLI exit code replaces overall status;
- `SKIPPED` is counted as `OK`;
- timeout uses `FAIL`;
- launch failure uses `FAIL`;
- downstream has no blockers;
- direct has blockers;
- status `OK` has a non-`OK` error kind;
- a required release gate remains `SKIPPED`;
- `Conditional` appears as a contract lifecycle status;
- a migration maps an unknown value to `OK`;
- one writer emits lowercase `ok` for validation status;
- one writer emits uppercase `DIRECT`;
- report code derives statuses from error prose;
- result counts disagree with serialized subjects;
- a new enum value appears without schema/version review;
- a documentation or project record uses coding-progress labels;
- a Wordbench status contains `gf-portfolio` registry or aggregation state.

Any indicator requires correction or a versioned contract change.

---

# 111. Change control

A status change must identify:

```text
Status domain:
Current field:
Current values:
New values:
Meaning change:
Schema impact:
Model impact:
CLI impact:
GUI impact:
Report impact:
Migration impact:
Compatibility impact:
Tests:
```

Required checklist:

```text
[ ] shared enums updated
[ ] result models updated
[ ] aggregation updated
[ ] process mapping updated
[ ] diagnostic parser updated
[ ] classifier updated
[ ] diff updated
[ ] schemas versioned
[ ] migrations updated
[ ] contract locks updated
[ ] CLI updated
[ ] GUI updated
[ ] reports updated
[ ] fixtures updated
[ ] tests updated
[ ] changelog updated
```

Removing or redefining a persisted enum value is a schema-major change.

---

# 112. Contract conformance checklist

This checklist verifies observable contracts and serialized meaning. It does not track development progress.

```text
[ ] validation status enum is centralized
[ ] overall status enum is centralized
[ ] execution-state enum is centralized
[ ] diagnostic-class enum is centralized
[ ] error-kind enum is centralized
[ ] regression change enum is centralized
[ ] status meanings match this reference
[ ] canonical case is enforced
[ ] validation and execution state are separate
[ ] diagnostic class and error kind are separate
[ ] cancellation maps to ERROR + cancelled
[ ] timeout maps to ERROR + timed_out + TIMEOUT
[ ] launch failure maps to ERROR + launch_failed + TOOL
[ ] no-process execution state is null
[ ] legacy not_started migrates
[ ] legacy CANCELLED migrates
[ ] legacy script_error migrates
[ ] legacy framework_error migrates
[ ] downstream blockers are validated
[ ] overall aggregation uses ERROR > FAIL > OK
[ ] required SKIPPED cannot pass release
[ ] optional-status policy is explicit
[ ] gold_match remains bool/null
[ ] report labels derive from structured fields
[ ] CLI exit codes remain separate
[ ] contract and ADR statuses remain separate
[ ] schemas reject unknown strict values
[ ] current writers emit no legacy values
[ ] combination tests pass
[ ] count invariants pass
[ ] migration tests pass
```

---

# 113. Related documents

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/architecture/DATA_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/diagnostics/ERROR_CLASSIFICATION.md
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/REGRESSION_COMPARISON.md
docs/validation/RELEASE_GATES.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/SUMMARY_MARKDOWN_REFERENCE.md
docs/reference/DIAGNOSTIC_KINDS.md
docs/reference/EXIT_CODES.md
docs/development/BACKWARD_COMPATIBILITY.md
docs/release/VERSIONING_POLICY.md
docs/decisions/README.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
SECURITY.md
```

---

# 114. Core rule

Status values are compact architectural contracts.

Therefore:

> Use `OK`, `FAIL`, `ERROR`, and `SKIPPED` only for validation outcomes; use execution state for timeout, cancellation, launch, and completion; use diagnostic class for causal relationship; use error kind for technical category; and never collapse these independent dimensions into one ambiguous status string.
