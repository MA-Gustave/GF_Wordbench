# GF Wordbench — Diagnostic Kinds Reference

**Document ID:** `GF-WB-REFERENCE-DIAGNOSTIC-KINDS`  
**Status:** Normative  
**Applies to:** GF Wordbench file results, scenario results, process results, diagnostic parsing, causal classification, reports, summaries, regression comparison, and release gates  
**Owner:** GF Wordbench maintainers  
**Vocabulary version:** `1.0.0`  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\reference\DIAGNOSTIC_KINDS.md`  
**Last structural review:** 2026-07-22

---

## 1. Purpose

This document defines the canonical diagnostic vocabulary used by GF Wordbench.

It establishes the meaning of:

- validation status;
- execution state;
- technical error kind;
- causal diagnostic class;
- detailed diagnostic codes;
- primary diagnostic selection;
- diagnostic evidence;
- direct, downstream, ambiguous, noise, and skipped classifications;
- file and scenario diagnostic mapping;
- compatibility and migration behavior.

The vocabulary is intentionally split into independent axes.

A single label cannot correctly answer all of the following questions:

1. Did the requested validation criterion pass?
2. Did the external process launch and complete?
3. What technical family best describes the problem?
4. Is the observed failure a root-like failure or a dependency consequence?
5. Which exact contract or assertion failed?
6. Which preserved evidence supports the conclusion?

The central rule is:

> Validation status, execution state, error kind, causal class, and detailed diagnostic code are separate fields and must never be collapsed into one overloaded value.

---

## 2. Scope

This reference governs diagnostic values produced or consumed by:

```text
app/models.py
app/audit/diagnostics.py
app/audit/classifier.py
app/audit/compiler.py
app/audit/scenario_runner.py
app/audit/result_model.py
app/audit/diff.py
app/reports/
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest-linked diagnostic evidence
```

It applies to:

- GF version probing;
- source scanning;
- GF module compilation;
- PGF construction;
- `.gfs` scenario execution;
- marker and assertion evaluation;
- output normalization;
- gold comparison;
- artifact verification;
- project configuration validation;
- filesystem operations;
- external-tool launch;
- timeout and cancellation;
- framework contract failures;
- regression comparison.

---

## 3. Non-scope

This document does not:

- define every GF diagnostic message;
- reproduce GF compiler internals;
- define the regular expressions used by diagnostic parsers;
- define the complete persisted JSON schema;
- define report layout;
- define exit-code numbers;
- define scenario assertion syntax;
- assign linguistic correctness automatically;
- replace raw stdout or stderr;
- allow static scanning to become GF compilation truth.

Detailed parsing patterns belong to:

```text
docs/diagnostics/GF_DIAGNOSTIC_PARSING.md
docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md
```

Detailed causal rules belong to:

```text
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
```

Persisted field shape belongs to:

```text
docs/PERSISTED_SCHEMA_LOCK.md
```

---

## 4. Related normative documents

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
docs/diagnostics/ERROR_CLASSIFICATION.md
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
docs/diagnostics/GF_DIAGNOSTIC_PARSING.md
docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md
docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md
docs/reference/STATUS_VALUES.md
docs/reference/EXIT_CODES.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/AI_READY_REFERENCE.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/validation/VALIDATION_OVERVIEW.md
```

When this reference overlaps a serialized field definition, `PERSISTED_SCHEMA_LOCK.md` owns the field shape and version.

This reference owns the semantic interpretation of the diagnostic vocabulary.

---

## 5. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **DIAGNOSTIC**: structured interpretation of preserved validation evidence.
- **RAW DIAGNOSTIC EVIDENCE**: unmodified stdout, stderr, process metadata, source location, scan log, scenario transcript, or artifact check.
- **NORMALIZED DIAGNOSTIC**: stable structured representation derived from raw evidence.
- **PRIMARY DIAGNOSTIC**: one deterministic diagnostic selected to summarize a result.
- **SECONDARY DIAGNOSTIC**: additional diagnostic retained without replacing the primary.
- **VALIDATION STATUS**: whether the requested criterion passed, failed, errored, or was skipped.
- **EXECUTION STATE**: whether the external operation completed, timed out, was cancelled, or failed to launch.
- **ERROR KIND**: broad technical family of the result.
- **DIAGNOSTIC CLASS**: causal relationship between a result and project-level failure.
- **DIAGNOSTIC CODE**: optional detailed machine identifier for a specific contract or failure condition.
- **DIRECT FAILURE**: failure attributed to the evaluated provider or target.
- **DOWNSTREAM FAILURE**: failure caused by a failed dependency or provider.
- **AMBIGUOUS FAILURE**: failure whose causal origin cannot be determined confidently.
- **NOISE**: evidence excluded from causal ranking without being silently discarded.
- **SKIPPED RESULT**: intentionally unexecuted work.
- **FRAMEWORK ERROR**: failure of configuration, orchestration, I/O, process control, parsing, or internal framework behavior rather than an established language-project defect.
- **TOOL FAILURE**: external tool launched and failed or violated an integration contract.
- **VALIDATION FAILURE**: validation executed and established that a required project criterion was not met.

---

# 6. Diagnostic model

Every result should be interpretable through the following conceptual record:

```text
status
execution_state
error_kind
diagnostic_class
diagnostic_code
primary_message
error_detail
source_location
blocked_by
raw_evidence_paths
```

Not every current persisted result contains every field directly.

Fields not present in the active schema must not be invented in canonical output.

They may be represented through existing structured fields until a schema revision adds them.

---

## 6.1 The five diagnostic axes

| Axis | Question answered | Canonical example |
|---|---|---|
| Validation status | Did the requested criterion pass? | `FAIL` |
| Execution state | Did the external operation complete? | `completed` |
| Error kind | What broad technical family applies? | `TYPE` |
| Diagnostic class | Is this root-like or dependency-derived? | `direct` |
| Diagnostic code | What exact condition occurred? | `gf_type_mismatch` |

Example:

```text
status = FAIL
execution_state = completed
error_kind = TYPE
diagnostic_class = direct
diagnostic_code = gf_type_mismatch
```

Another valid example:

```text
status = ERROR
execution_state = launch_failed
error_kind = TOOL
diagnostic_class = skipped
diagnostic_code = launch_failure
```

These values are not interchangeable.

---

# 7. Canonical validation status

Canonical validation statuses are:

```text
OK
FAIL
ERROR
SKIPPED
```

Status values are uppercase ASCII.

---

## 7.1 `OK`

Meaning:

- the requested operation or criterion executed when execution was required;
- the result was interpretable;
- every required success condition passed.

Examples:

- selected GF module compiled;
- required `.gfo` exists;
- scenario markers completed;
- required assertions passed;
- gold output matched;
- required PGF exists and is valid under its contract.

`OK` does not mean:

- no warnings exist;
- no static scan finding exists;
- every project feature is complete;
- release mode passed when only quick mode ran.

---

## 7.2 `FAIL`

Meaning:

- validation executed sufficiently to interpret the result;
- one or more required project criteria were not met.

Examples:

- GF syntax error;
- GF type mismatch;
- required marker missing in an otherwise interpretable scenario;
- required assertion evaluated false;
- normalized output differs from gold;
- required artifact absent after otherwise completed validation;
- project release criterion failed.

`FAIL` normally represents a project-validation outcome, not an inability of GF Wordbench to operate.

---

## 7.3 `ERROR`

Meaning:

- GF Wordbench could not execute, complete, or interpret the required contract reliably.

Examples:

- invalid required configuration;
- executable could not launch;
- process timed out under error policy;
- required evidence could not be decoded;
- scenario assertion type is unknown;
- normalized output could not be produced;
- required result file could not be written;
- internal result invariant failed;
- manifest could not be finalized.

`ERROR` is not a more severe spelling of `FAIL`.

It describes a different failure boundary.

---

## 7.4 `SKIPPED`

Meaning:

- the operation was intentionally not executed under explicit policy.

Examples:

- optional scenario excluded from quick mode;
- compilation disabled by an explicit diagnostic option;
- project criterion not applicable to the selected mode;
- dependent action omitted after a preflight error.

A required operation that is skipped without approved policy must make the run `FAIL` or `ERROR`.

`SKIPPED` must not be used to hide:

- unsupported behavior;
- missing configuration;
- launch failure;
- timeout;
- unimplemented required functionality.

---

# 8. Canonical execution state

Canonical persisted execution states are:

```text
completed
timed_out
cancelled
launch_failed
```

Execution states are lowercase ASCII.

A component may use an internal pre-execution state such as `not_started`, but it must not emit a new canonical persisted value without a schema change.

---

## 8.1 `completed`

Meaning:

- the process or internal operation reached a normal terminal point;
- exit status and captured evidence are available when applicable.

`completed` does not imply `OK`.

Valid examples:

```text
completed + OK
completed + FAIL
completed + ERROR
```

---

## 8.2 `timed_out`

Meaning:

- the configured deadline expired;
- GF Wordbench attempted the documented termination behavior;
- partial output may exist.

Required implications:

```text
error_kind = TIMEOUT
status = ERROR by default
```

A stage may map timeout to `FAIL` only when its contract explicitly defines timeout as an evaluated validation criterion rather than an infrastructure inability.

A timeout must never be reported as:

```text
SYNTAX
TYPE
normal GF compile failure
```

---

## 8.3 `cancelled`

Meaning:

- the user or controlling system requested termination;
- execution did not complete normally.

Recommended implications:

```text
status = ERROR
error_kind = OTHER or TOOL according to the cancellation owner
diagnostic_class = skipped or ambiguous
```

Cancellation is not a canonical error kind.

It is an execution state.

The exact cancellation detail should use a diagnostic code such as:

```text
user_cancelled
controller_cancelled
ci_cancelled
```

when the schema supports detailed codes.

---

## 8.4 `launch_failed`

Meaning:

- GF Wordbench could not start the intended external process.

Typical error kinds:

```text
CONFIG
IO
TOOL
```

Examples:

- executable path invalid before launch: `CONFIG`;
- executable exists but cannot be opened because of permission or filesystem error: `IO`;
- executable resolution or process creation fails for a tool-specific reason: `TOOL`.

A launch failure must not be classified as a GF language error.

---

# 9. Canonical error kinds

Canonical error kinds are:

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

Error kinds are uppercase ASCII.

They are intentionally broad.

Detailed failure identity belongs to an optional diagnostic code and preserved evidence.

---

## 9.1 Error-kind summary

| Error kind | Broad meaning | Default status | Typical execution state |
|---|---|---|---|
| `OK` | No technical error | `OK` or explicit `SKIPPED` | `completed` or no process |
| `OTHER` | Recognized failure outside defined families | `FAIL` or `ERROR` | any |
| `TYPE` | GF type or unification failure | `FAIL` | `completed` |
| `SYNTAX` | GF source or command-language syntax failure | `FAIL` | `completed` |
| `INTERNAL` | Internal invariant or implementation failure | `FAIL` or `ERROR` | `completed` |
| `TIMEOUT` | Deadline exceeded | `ERROR` by default | `timed_out` |
| `SCRIPT` | Scenario, marker, assertion, or script contract failure | `FAIL` or `ERROR` | `completed` |
| `CONFIG` | Invalid or missing configuration | `ERROR` | no process or `launch_failed` |
| `IO` | Filesystem, path, encoding, read, or write failure | `ERROR` | any |
| `TOOL` | External-tool availability, version, capability, or contract failure | `ERROR` | any |

---

# 10. `OK`

## 10.1 Meaning

`OK` means no technical error applies to the represented operation.

## 10.2 Valid combinations

```text
status = OK
error_kind = OK
diagnostic_class = ok
```

An intentionally skipped operation may use:

```text
status = SKIPPED
error_kind = OK
diagnostic_class = skipped
```

when no failure caused the skip.

## 10.3 Invalid combinations

The following are invalid:

```text
status = FAIL
error_kind = OK
```

unless the failing criterion is represented entirely outside the current error-kind field and the schema has not yet been expanded.

Canonical final writers should assign the closest valid non-`OK` error kind.

---

# 11. `OTHER`

## 11.1 Meaning

`OTHER` is the fallback technical family when:

- a real failure exists;
- available evidence is sufficient to establish failure;
- no more specific canonical error kind is justified.

## 11.2 Appropriate uses

Examples:

- unrecognized GF diagnostic after completed execution;
- project validation mismatch that is not type, syntax, script, configuration, I/O, timeout, internal, or tool-specific;
- legacy diagnostic whose precise family cannot be recovered;
- cancellation detail when no dedicated canonical kind applies and status remains explicit.

## 11.3 Inappropriate uses

Do not use `OTHER` merely because parsing work has not been implemented.

Known conditions should use their specific kind.

Do not use `OTHER` to conceal:

- timeout;
- invalid configuration;
- missing executable;
- I/O failure;
- malformed scenario protocol.

## 11.4 Evidence requirement

`OTHER` must preserve a meaningful primary message and raw evidence reference.

---

# 12. `TYPE`

## 12.1 Meaning

`TYPE` represents a GF semantic typing or unification failure.

Typical conditions:

```text
type mismatch
cannot unify
incorrect argument type
missing record field required by type
record or table shape mismatch
constructor result incompatible with declared lincat
invalid parameter-domain use
```

## 12.2 Authority

GF is authoritative for type checking.

GF Wordbench recognizes and normalizes GF diagnostics.

It does not implement a competing type checker.

## 12.3 Default mapping

```text
status = FAIL
execution_state = completed
error_kind = TYPE
diagnostic_class = direct | downstream | ambiguous
```

## 12.4 Causal caution

A `TYPE` diagnostic is not automatically direct.

Examples:

- diagnostic points to the evaluated source: likely `direct`;
- diagnostic points to a failed imported provider: may be `downstream`;
- source attribution is unclear: `ambiguous`.

## 12.5 Required evidence

Preserve when available:

```text
GF message
source file
line
column
expected type
actual type
relevant module identity
stdout path
stderr path
```

---

# 13. `SYNTAX`

## 13.1 Meaning

`SYNTAX` represents invalid syntax in:

- GF source;
- a GF shell command;
- a script command interpreted by GF.

Typical conditions:

```text
parse error
unexpected token
unterminated declaration
malformed module header
invalid GF command syntax
```

## 13.2 Distinction from `SCRIPT`

Use:

```text
SYNTAX
```

when GF reports syntactic invalidity in GF language or GF command input.

Use:

```text
SCRIPT
```

when GF Wordbench’s scenario protocol, markers, assertions, or script-level completion contract fails.

A `.gfs` file can therefore produce either kind:

```text
malformed GF command → SYNTAX
missing required completion marker → SCRIPT
```

## 13.3 Default mapping

```text
status = FAIL
execution_state = completed
error_kind = SYNTAX
diagnostic_class = direct | downstream | ambiguous
```

## 13.4 Causal caution

Imported-file syntax failure may cause downstream failures in consumers.

The classifier, not the parser, determines causal class.

---

# 14. `INTERNAL`

## 14.1 Meaning

`INTERNAL` represents an internal invariant or implementation failure reported by:

- GF;
- a GF runtime component;
- GF Wordbench;
- a tightly owned adapter.

Examples:

```text
GF internal error
GeneratePMCFG internal failure
assertion inside GF or the framework
impossible internal model state
unexpected invariant violation
```

## 14.2 Origin field

`INTERNAL` alone does not identify the failing component.

The diagnostic should retain or derive an origin such as:

```text
gf
gf-wordbench
scenario-runner
report-writer
manifest-writer
```

A future persisted `origin` field requires a schema update.

Until then, origin belongs in structured detail or the primary message.

## 14.3 Status mapping

If GF launched and reported an internal error while validating project material:

```text
status = FAIL or ERROR according to stage contract
execution_state = completed
error_kind = INTERNAL
```

If GF Wordbench itself violated an invariant and the validation result is unreliable:

```text
status = ERROR
error_kind = INTERNAL
```

## 14.4 Causal class

An internal error is not automatically a direct project failure.

Canonical final behavior:

- use `direct` only when evidence links the failure to the evaluated provider;
- use `downstream` only when a confirmed blocker exists;
- use `ambiguous` when the project-level cause is unknown;
- use `skipped` when semantic validation never started.

The predecessor classifier treated `INTERNAL` as obviously direct.

That behavior is transitional and must be refined for framework-origin internal errors.

---

# 15. `TIMEOUT`

## 15.1 Meaning

`TIMEOUT` means a finite configured deadline expired.

## 15.2 Required execution state

Canonical combination:

```text
execution_state = timed_out
error_kind = TIMEOUT
```

## 15.3 Default status

```text
status = ERROR
```

because the required contract did not complete.

A documented stage may use `FAIL` only when timeout is itself an evaluated criterion.

## 15.4 Causal class

Timeout does not establish a project root cause.

Recommended mapping:

- `direct` only when the operation is inherently local to the target and no external blocker exists;
- `downstream` when waiting on a confirmed failed dependency is established;
- `ambiguous` when cause is unknown;
- `skipped` only for dependent work not launched after another timeout.

The predecessor classifier treated `TIMEOUT` as automatically direct.

Canonical final classification must use operation context and evidence.

## 15.5 Detailed codes

Examples:

```text
version_probe_timeout
compile_timeout
pgf_build_timeout
scenario_timeout
generation_timeout
diagnostic_timeout
termination_timeout
```

## 15.6 Evidence

Preserve:

```text
configured timeout
elapsed duration
termination attempt
termination result
partial stdout
partial stderr
owned child-process information when available
```

---

# 16. `SCRIPT`

## 16.1 Meaning

`SCRIPT` represents a failure in a native `.gfs` scenario or GF Wordbench’s scenario-control contract.

Typical conditions:

```text
required marker missing
end marker missing
malformed reserved marker
wrong scenario ID in marker
unexpected section
nested section
duplicate section
unknown assertion type
invalid assertion configuration
required assertion failed
scenario completion protocol failed
```

## 16.2 `FAIL` versus `ERROR`

Use `FAIL` when the scenario contract was interpretable and a required criterion evaluated false.

Examples:

```text
expected section never completed
required assertion returned false
expected marker absent
```

Use `ERROR` when the scenario contract could not be interpreted reliably.

Examples:

```text
malformed reserved marker
nested marker protocol
unknown assertion type
invalid assertion configuration
output truncation prevents evaluation
```

## 16.3 Distinction from `SYNTAX`

GF-reported syntax invalidity:

```text
SYNTAX
```

GF Wordbench scenario-protocol invalidity:

```text
SCRIPT
```

## 16.4 Causal class

A scenario script failure is not automatically a source-module direct failure.

Possible mappings:

- `direct`: scenario asset itself is invalid;
- `downstream`: scenario fails because a confirmed entrypoint dependency failed;
- `ambiguous`: evidence does not isolate script versus grammar behavior;
- `skipped`: scenario not executed under policy.

## 16.5 Detailed codes

Examples:

```text
missing_expected_begin
missing_expected_end
end_without_begin
mismatched_end
nested_begin
duplicate_section
unexpected_section
wrong_scenario
out_of_order
malformed_reserved_line
open_section_at_eof
unknown_assertion_type
assertion_failed
```

---

# 17. `CONFIG`

## 17.1 Meaning

`CONFIG` represents missing, malformed, unsupported, contradictory, or unsafe configuration.

Typical conditions:

```text
missing project.toml
unsupported project schema
required field absent
invalid mode
unknown required scenario
missing configured checkpoint
invalid timeout
path escapes project root
multiple active projects detected
required GF path part absent
```

## 17.2 Default mapping

```text
status = ERROR
error_kind = CONFIG
diagnostic_class = skipped or ambiguous
```

If validation never started because configuration was invalid:

```text
diagnostic_class = skipped
```

If partial work ran and project-level causality is unclear:

```text
diagnostic_class = ambiguous
```

## 17.3 Execution state

Configuration failure may occur before an external process exists.

When a process-result field requires an execution state, use the stage’s documented representation.

Do not claim:

```text
completed
```

for a process that was never attempted unless `completed` refers explicitly to internal preflight completion.

## 17.4 Detailed codes

Examples:

```text
missing_project_config
unsupported_schema
missing_required_field
invalid_field_type
unknown_mode
invalid_path
path_traversal
missing_entrypoint
missing_checkpoint
missing_scenario
missing_gold_registration
invalid_timeout
```

---

# 18. `IO`

## 18.1 Meaning

`IO` represents filesystem, path access, encoding, read, write, or stream-capture failure.

Typical conditions:

```text
source file unreadable
scenario file unreadable
gold file unreadable
output directory cannot be created
stdout file cannot be written
stderr file cannot be written
summary write failure
manifest write failure
permission denied
disk full
invalid encoding
path disappeared during run
```

## 18.2 Default mapping

```text
status = ERROR
error_kind = IO
```

Execution state depends on timing:

```text
before process → launch_failed or no process
during process → completed, timed_out, or cancelled may still apply
after process → completed process with report/artifact ERROR
```

## 18.3 Causal class

I/O failures are not automatically project-root failures.

Use:

- `skipped` when validation did not begin;
- `ambiguous` when partial validation cannot be trusted;
- `direct` only when the project-owned file itself is the confirmed invalid or unreadable target and the classification contract defines that relation.

## 18.4 Detailed codes

Examples:

```text
file_not_found
permission_denied
read_failure
write_failure
atomic_replace_failure
decode_error
encode_error
disk_full
path_escape
symlink_violation
evidence_missing
```

---

# 19. `TOOL`

## 19.1 Meaning

`TOOL` represents failure of an external executable or its integration contract when no more specific canonical kind applies.

Typical conditions:

```text
GF executable unavailable
GF process creation failure
unsupported GF version
required command option unsupported
external tool contract violated
expected tool response absent
tool-produced artifact structurally invalid
optional external tool unavailable when required
```

## 19.2 Distinction from other kinds

Use:

- `CONFIG` when configured values are invalid before tool invocation;
- `IO` for filesystem or permission failure;
- `TIMEOUT` for deadline expiry;
- `SYNTAX` or `TYPE` for GF project diagnostics;
- `INTERNAL` for explicit internal-error evidence;
- `TOOL` for external capability, launch, compatibility, or contract failure.

## 19.3 Default mapping

```text
status = ERROR
error_kind = TOOL
diagnostic_class = skipped or ambiguous
```

## 19.4 Detailed codes

Examples:

```text
launch_failure
tool_failure
unsupported_version
unknown_version
capability_missing
contract_failure
artifact_failure
version_probe_failure
unexpected_exit
invalid_tool_output
```

## 19.5 Artifact failure

A required artifact missing after an apparently successful tool process is typically:

```text
status = FAIL or ERROR according to stage contract
error_kind = TOOL
diagnostic_code = artifact_failure
execution_state = completed
```

It must not be represented as `OK`.

---

# 20. Detailed diagnostic codes

## 20.1 Purpose

Error kinds are deliberately broad.

Detailed diagnostic codes identify the exact contract condition.

Examples:

```text
gf_type_mismatch
gf_parse_error
launch_failure
unsupported_version
artifact_failure
gold_mismatch
normalization_failure
missing_expected_end
assertion_failed
path_traversal
```

## 20.2 Current schema rule

A canonical writer must not emit a new persisted `diagnostic_code` field until `PERSISTED_SCHEMA_LOCK.md` defines it.

Until then, a detailed code may appear in:

- an internal structured diagnostic object;
- `error_detail`;
- `primary_message`;
- a detail artifact;
- report text derived from a stable internal value.

## 20.3 Identifier syntax

Recommended syntax:

```text
[a-z][a-z0-9]*(?:_[a-z0-9]+)*
```

Examples:

```text
launch_failure
gf_type_mismatch
missing_required_artifact
gold_mismatch
```

## 20.4 Stability

Once persisted or publicly documented, a diagnostic code is a versioned contract.

It must not be reused with a different meaning.

## 20.5 Unknown code

Readers must preserve an unknown detailed code as unknown.

They must not reinterpret it as another known code.

---

# 21. Recommended diagnostic-code families

These families are reference categories, not a currently mandatory persisted enum.

## 21.1 Process

```text
launch_failure
unexpected_exit
timeout
termination_failure
user_cancelled
controller_cancelled
stream_capture_failure
```

## 21.2 Toolchain

```text
unknown_version
unsupported_version
capability_missing
version_probe_failure
tool_contract_failure
```

## 21.3 GF compilation

```text
gf_parse_error
gf_type_mismatch
gf_unification_failure
gf_internal_error
module_not_found
dependency_load_failure
```

## 21.4 Scenario

```text
script_syntax_error
missing_expected_begin
missing_expected_end
end_without_begin
mismatched_end
nested_begin
duplicate_section
unexpected_section
wrong_scenario
out_of_order
malformed_reserved_line
open_section_at_eof
unknown_assertion_type
invalid_assertion
assertion_failed
```

## 21.5 Normalization and gold

```text
normalization_failure
unsupported_normalization_version
gold_missing
gold_invalid
gold_version_mismatch
gold_mismatch
gold_write_prohibited
```

## 21.6 Artifact

```text
artifact_missing
artifact_empty
artifact_invalid
artifact_hash_mismatch
artifact_path_escape
manifest_missing_entry
```

## 21.7 Configuration and schema

```text
config_missing
config_invalid
schema_missing
schema_unsupported
required_field_missing
invalid_field_type
unknown_required_key
multiple_active_projects
```

## 21.8 Filesystem and encoding

```text
file_not_found
permission_denied
read_failure
write_failure
decode_error
encode_error
atomic_replace_failure
disk_full
```

---

# 22. Canonical diagnostic classes

Canonical causal diagnostic classes are:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

They are lowercase ASCII.

These classes describe project-level causal relationship.

They do not describe process mechanics.

---

## 22.1 Diagnostic-class summary

| Class | Meaning | Typical status |
|---|---|---|
| `ok` | No failure requiring causal classification | `OK` |
| `direct` | Failure attributed to evaluated provider/target | `FAIL` or, rarely, `ERROR` |
| `downstream` | Failure caused by confirmed failed dependency | `FAIL` |
| `ambiguous` | Failure exists but causal origin is uncertain | `FAIL` or `ERROR` |
| `noise` | Evidence excluded from root-cause ranking | usually not a required failing result |
| `skipped` | Work intentionally not executed or semantically not reached | `SKIPPED` or preflight `ERROR` |

---

# 23. `ok`

## 23.1 Meaning

The result passed and has no causal failure.

Canonical combination:

```text
status = OK
diagnostic_class = ok
is_direct = false
blocked_by = []
```

Static scan findings may coexist with `ok` when they do not define compile or scenario failure.

## 23.2 Invalid use

Do not use `ok` when:

- required validation failed;
- required validation errored;
- required validation was skipped;
- a fatal diagnostic exists;
- a required artifact is missing.

---

# 24. `direct`

## 24.1 Meaning

The strongest supported evidence attributes the failure to the evaluated target or provider.

Evidence may include:

- diagnostic source path equals evaluated file;
- diagnostic module identity equals evaluated module;
- scenario script itself violates its declared protocol;
- artifact owned by the evaluated stage is invalid for a target-local reason;
- explicit project dependency model identifies the target as the failing provider.

## 24.2 Required invariants

```text
diagnostic_class = direct
is_direct = true
```

`blocked_by` should be empty unless the schema uses it for additional context that does not contradict directness.

## 24.3 Not automatic

The following do not prove directness by themselves:

- non-zero exit code;
- processing order;
- first failed file in a list;
- `TYPE` kind alone;
- `SYNTAX` kind alone;
- `INTERNAL` kind alone;
- timeout alone;
- script failure alone;
- filename mentioned in a prompt or echoed command.

## 24.4 Root-like, not metaphysical certainty

`direct` means strongest supported local attribution under available evidence.

It does not guarantee there is no deeper design defect elsewhere.

---

# 25. `downstream`

## 25.1 Meaning

The evaluated result failed because one or more dependencies already failed.

Examples:

- entrypoint cannot load a failed imported module;
- concrete module fails because its resource provider did not compile;
- scenario cannot load an entrypoint blocked by a failed checkpoint;
- PGF build fails because a required entrypoint failed earlier.

## 25.2 Required evidence

A downstream result should identify confirmed blockers.

Canonical invariant:

```text
diagnostic_class = downstream
is_direct = false
blocked_by = [<one or more blocker identities>]
```

When the blocker is known, `blocked_by` must not be empty.

## 25.3 Blocker normalization

Blockers should be normalized to stable project-relative file or module identities.

Duplicate blockers are removed deterministically.

Where a chain exists:

```text
A fails directly
B is blocked by A
C is blocked by B
```

the classifier may collapse C’s blocker list to root-like A when the contract defines that behavior.

It must preserve enough evidence to reconstruct the relationship.

## 25.4 Status

A downstream result remains `FAIL`.

It is not converted to `SKIPPED` merely because another file caused the failure, unless the operation was intentionally not executed.

---

# 26. `ambiguous`

## 26.1 Meaning

A failure exists, but available evidence cannot assign a confident causal origin.

Examples:

- diagnostic references several modules;
- source location is absent;
- parser recognized failure but not provider;
- execution failed after partial dependency loading;
- framework error prevents reliable project attribution;
- candidate blockers exist but none is confirmed.

## 26.2 Invariants

```text
diagnostic_class = ambiguous
is_direct = false
```

`blocked_by` may contain candidate blockers only when the model and report label them explicitly as candidates.

It must not imply confirmed downstream causality.

## 26.3 Prefer ambiguity over false certainty

When evidence does not justify `direct` or `downstream`, use `ambiguous`.

Reports must preserve uncertainty.

## 26.4 Primary message

The primary message should state what is known, not invent a root cause.

---

# 27. `noise`

## 27.1 Meaning

`noise` marks diagnostic evidence that should not influence root-cause ranking.

Examples:

- repeated prompt echo;
- duplicate diagnostic line;
- known non-semantic tool banner;
- a recognized harmless line excluded by a version-specific rule;
- a redundant cascade message already represented structurally.

## 27.2 Evidence preservation

Noise is not deleted from raw evidence.

It may be excluded from:

- primary-diagnostic selection;
- top-error counts;
- root-cause ranking;
- concise report excerpts.

## 27.3 Result-level caution

A required failing result must not be converted to `OK` or hidden because its recognized lines were classified as noise.

If all parsed diagnostics appear noisy but the operation failed:

```text
error_kind = OTHER or appropriate process kind
diagnostic_class = ambiguous
```

until failure can be explained.

## 27.4 Status

`noise` is primarily a diagnostic-record classification.

When used on a result, status must remain consistent with the underlying operation.

---

# 28. `skipped`

## 28.1 Meaning

The operation or semantic validation did not run under explicit policy or because a prerequisite prevented it.

Canonical intentional skip:

```text
status = SKIPPED
diagnostic_class = skipped
is_direct = false
```

A preflight error may produce:

```text
status = ERROR
diagnostic_class = skipped
```

for downstream items never attempted.

## 28.2 Blocker representation

If a required item was skipped because another result blocked execution, reports should identify the blocker.

The item remains distinct from a process that launched and failed downstream.

## 28.3 Invalid use

Do not use `skipped` to conceal:

- timeout after launch;
- cancellation after work began;
- unimplemented required capability;
- missing required configuration;
- unknown result.

---

# 29. Compatibility value `framework_error`

A draft persisted schema admitted:

```text
framework_error
```

as a diagnostic-class value.

This value mixes two independent dimensions:

- framework-origin technical failure;
- project-level causal relationship.

Canonical vocabulary version `1.0.0` does not use `framework_error` as a newly emitted causal class.

Canonical writers emit one of:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

and represent framework failure through:

```text
status = ERROR
error_kind = CONFIG | IO | TOOL | INTERNAL | TIMEOUT | SCRIPT | OTHER
execution_state = <appropriate state>
```

## 29.1 Reader compatibility

Until `PERSISTED_SCHEMA_LOCK.md` is harmonized, readers may accept `framework_error` from draft or legacy data.

A migrator must not map it blindly.

Recommended evidence-based conversion:

| Legacy condition | Canonical class |
|---|---|
| Validation never started | `skipped` |
| Partial result, project cause unknown | `ambiguous` |
| Confirmed target-local project failure plus framework reporting defect | `direct` with separate framework warning |
| Confirmed dependency consequence plus framework reporting defect | `downstream` with blocker |
| Only duplicate/non-causal reporting noise | `noise` |

Migration must:

- preserve the original legacy value;
- record a warning;
- preserve raw evidence;
- state the chosen canonical mapping;
- report uncertainty or loss.

## 29.2 Release requirement

Before final stable release, the persisted schema, models, reports, tests, and this reference must agree on the canonical diagnostic-class enum.

---

# 30. `is_direct`

## 30.1 Purpose

`is_direct` is a compatibility convenience field.

It does not define an independent causal axis.

Canonical invariant:

```text
is_direct == (diagnostic_class == "direct")
```

## 30.2 Invalid combinations

Invalid:

```text
diagnostic_class = direct
is_direct = false
```

Invalid:

```text
diagnostic_class = downstream
is_direct = true
```

## 30.3 Future removal

Removing `is_direct` from a persisted schema requires a schema major increment unless a migration and compatibility policy define otherwise.

---

# 31. `blocked_by`

## 31.1 Meaning

`blocked_by` identifies confirmed causal blockers for downstream results.

## 31.2 Canonical identity

Use stable identities:

```text
project-relative source path
module identity
scenario ID
stage ID
artifact role
```

The field’s exact allowed type is owned by the persisted schema.

## 31.3 Determinism

Blockers must be:

- normalized;
- unique;
- deterministically ordered;
- project-contained when they are paths.

## 31.4 Ambiguous candidates

Do not treat candidate blockers as confirmed blockers without explicit labeling.

A future `candidate_blockers` field requires a schema revision.

---

# 32. Primary diagnostic

## 32.1 Purpose

A result may have many diagnostic lines.

The primary diagnostic provides one deterministic summary.

## 32.2 Selection priority

Recommended selection order:

```text
1. launch, timeout, cancellation, or required contract failure
2. explicit fatal GF diagnostic with source location
3. direct target-local GF diagnostic
4. required scenario protocol or assertion failure
5. required artifact failure
6. gold mismatch
7. dependency diagnostic
8. unclassified non-zero process failure
9. fallback OTHER diagnostic
```

Stage-specific rules may refine this order.

## 32.3 Stability

For equivalent evidence, primary selection should be deterministic.

## 32.4 No evidence loss

Selecting a primary diagnostic must not discard secondary diagnostics or raw logs.

## 32.5 First line is not always primary

The first output line may be:

- a banner;
- prompt;
- warning;
- dependency echo;
- duplicate.

Primary selection uses parsed meaning and contract priority, not raw line order alone.

---

# 33. Primary message

## 33.1 Purpose

`primary_message` or its current model equivalent presents the concise human-readable diagnostic.

## 33.2 Requirements

A primary message should:

- be bounded;
- identify the relevant condition;
- retain source location when available;
- avoid unsupported causal claims;
- avoid secrets;
- avoid complete unbounded logs;
- preserve Unicode.

## 33.3 Examples

```text
GrammarX.gf:42:7: cannot unify expected and actual record types
Scenario parse-basic: required section `basic-clause` did not complete
GF executable could not be launched
Required artifact `release_pgf` is missing
Normalized output differs from gold in section `noun-phrase`
```

## 33.4 No report prose as source

The structured message is rendered into reports.

Reports must not be reparsed to recover it.

---

# 34. Error detail

`error_detail` may provide bounded supplementary context.

Examples:

```text
expected type
actual type
failed assertion ID
configured timeout
unsupported version range
missing artifact role
candidate blocker
```

It must not:

- duplicate complete raw logs;
- contain secrets;
- become an unversioned nested schema;
- replace raw evidence paths.

When stable structure is required, add typed fields through schema evolution.

---

# 35. Source location

## 35.1 Fields

A normalized diagnostic may identify:

```text
file_path
line
column
end_line
end_column
module_name
```

The current persisted schema may store only part of this information.

## 35.2 Path rules

Project source locations use project-relative canonical paths.

Environment and tool paths follow their own path policy.

## 35.3 Unknown location

Unknown location uses `null` or absence according to schema.

Do not use:

```text
line = 0
column = 0
```

to imply an actual source location.

## 35.4 Prompt and command echoes

A filename in an echoed command is not automatically a diagnostic source location.

---

# 36. Parser responsibilities

The diagnostic parser may:

- inspect stdout and stderr;
- recognize supported GF patterns;
- capture source locations;
- normalize message wording;
- assign broad error kind;
- assign detailed diagnostic code;
- identify likely referenced files;
- retain unrecognized evidence.

The parser must not:

- assign direct/downstream/ambiguous causal class;
- mutate raw evidence;
- hide non-zero exit;
- infer success from stdout alone;
- turn an unknown message into `OK`;
- report a source location from command echo alone;
- remove contradictory evidence.

---

# 37. Parser rule ordering

Recommended ordering:

```text
1. process and launch conditions
2. timeout and cancellation
3. explicit GF internal errors
4. explicit GF syntax patterns
5. explicit GF type/unification patterns
6. scenario protocol failures
7. configuration and schema errors
8. I/O errors
9. external-tool contract failures
10. generic GF failure
11. OTHER fallback
```

Specific patterns must precede broad fallback patterns.

Version-specific patterns should identify their supported GF range.

---

# 38. Causal classifier responsibilities

The causal classifier may:

- inspect structured diagnostics;
- resolve referenced files or modules;
- use project dependency data;
- identify confirmed blockers;
- collapse dependency chains according to policy;
- assign one canonical diagnostic class;
- derive `is_direct`;
- normalize `blocked_by`.

The classifier must not:

- launch GF;
- parse reports;
- mutate raw stdout or stderr;
- change technical error kind without explicit normalization ownership;
- claim directness from processing order alone;
- convert framework errors into project failures without evidence.

---

# 39. Error kind versus causal class

The same error kind may have several causal classes.

Examples:

| Error kind | Direct example | Downstream example | Ambiguous example |
|---|---|---|---|
| `TYPE` | Target lincat mismatches its declaration | Entrypoint reports failed imported provider | Message lacks reliable source |
| `SYNTAX` | Target source contains malformed declaration | Consumer cannot load dependency with syntax error | Output names several files |
| `INTERNAL` | GF internal error consistently triggered by target | PGF stage blocked by failed entrypoint | Framework/GF origin unclear |
| `SCRIPT` | Scenario marker protocol malformed in its own script | Scenario cannot load failed entrypoint | Script versus grammar cause unclear |
| `OTHER` | Target-specific recognized failure | Confirmed provider failure cascades | Unrecognized non-zero failure |

Causal class must never be inferred solely from error kind.

---

# 40. Status versus error kind

Recommended default matrix:

| Error kind | `OK` | `FAIL` | `ERROR` | `SKIPPED` |
|---|---:|---:|---:|---:|
| `OK` | Yes | No | Rare transitional case | Yes |
| `OTHER` | No | Yes | Yes | No |
| `TYPE` | No | Yes | Rare parser/infrastructure case | No |
| `SYNTAX` | No | Yes | Rare parser/infrastructure case | No |
| `INTERNAL` | No | Yes | Yes | No |
| `TIMEOUT` | No | Contract-specific | Default | No |
| `SCRIPT` | No | Yes | Yes | No |
| `CONFIG` | No | Rare project-policy case | Default | No |
| `IO` | No | Rare content-validation case | Default | No |
| `TOOL` | No | Rare tool-produced validation failure | Default | No |

“Rare” combinations require an explicit stage contract and evidence.

---

# 41. Execution state versus status

| Execution state | Typical status | Notes |
|---|---|---|
| `completed` | `OK`, `FAIL`, or `ERROR` | Completion does not imply success |
| `timed_out` | `ERROR` | `FAIL` only by explicit contract |
| `cancelled` | `ERROR` | Partial evidence may remain |
| `launch_failed` | `ERROR` | No GF semantic conclusion |

An intentionally skipped operation may have no external execution state in a future model.

Until then, the persisted schema’s documented representation must be used consistently.

---

# 42. File-result mapping

## 42.1 Successful file

```text
status = OK
error_kind = OK
diagnostic_class = ok
is_direct = false
blocked_by = []
```

## 42.2 Direct GF type failure

```text
status = FAIL
execution_state = completed
error_kind = TYPE
diagnostic_class = direct
is_direct = true
blocked_by = []
```

## 42.3 Downstream import failure

```text
status = FAIL
execution_state = completed
error_kind = OTHER or the parsed GF kind
diagnostic_class = downstream
is_direct = false
blocked_by = ["project/relative/provider.gf"]
```

## 42.4 Ambiguous compile failure

```text
status = FAIL
execution_state = completed
error_kind = OTHER
diagnostic_class = ambiguous
is_direct = false
blocked_by = []
```

## 42.5 Compile timeout

```text
status = ERROR
execution_state = timed_out
error_kind = TIMEOUT
diagnostic_class = ambiguous
is_direct = false
```

## 42.6 Compile launch failure

```text
status = ERROR
execution_state = launch_failed
error_kind = TOOL
diagnostic_class = skipped
is_direct = false
```

---

# 43. Scenario-result mapping

## 43.1 Successful scenario

```text
status = OK
execution_state = completed
error_kind = OK
diagnostic_class = ok
```

## 43.2 Required assertion failure

```text
status = FAIL
execution_state = completed
error_kind = SCRIPT
diagnostic_class = direct or ambiguous
diagnostic_code = assertion_failed
```

Use `direct` when the failing criterion belongs clearly to the scenario’s own contract.

Use `ambiguous` when grammar behavior versus scenario construction cannot be isolated.

## 43.3 Gold mismatch

Until a dedicated persisted kind exists:

```text
status = FAIL
execution_state = completed
error_kind = OTHER or SCRIPT according to scenario contract
diagnostic_code = gold_mismatch
diagnostic_class = direct or ambiguous
```

A future schema may add a dedicated broad kind only through versioned change.

## 43.4 Malformed marker protocol

```text
status = ERROR
execution_state = completed
error_kind = SCRIPT
diagnostic_code = malformed_reserved_line
diagnostic_class = direct
```

when the scenario asset is confirmed invalid.

## 43.5 Scenario blocked by failed entrypoint

If the scenario process ran and failed because of the entrypoint:

```text
status = FAIL
diagnostic_class = downstream
blocked_by = [<entrypoint or provider>]
```

If the scenario was not launched:

```text
status = SKIPPED or ERROR according to requiredness
diagnostic_class = skipped
```

## 43.6 Scenario timeout

```text
status = ERROR
execution_state = timed_out
error_kind = TIMEOUT
diagnostic_class = ambiguous
```

---

# 44. PGF and artifact mapping

## 44.1 PGF build GF type/syntax failure

Use parsed GF kind and causal class.

## 44.2 PGF process succeeds but artifact missing

```text
status = FAIL or ERROR according to PGF contract
execution_state = completed
error_kind = TOOL
diagnostic_code = artifact_missing
diagnostic_class = direct or ambiguous
```

## 44.3 Manifest hash mismatch

```text
status = ERROR
error_kind = IO or TOOL according to origin
diagnostic_code = artifact_hash_mismatch
diagnostic_class = ambiguous
```

## 44.4 Artifact path escapes run root

```text
status = ERROR
error_kind = CONFIG or IO
diagnostic_code = artifact_path_escape
diagnostic_class = skipped or ambiguous
```

---

# 45. Static scan findings

Static scan findings are not GF diagnostic error kinds.

A scan rule should use:

```text
rule_id
severity
file_path
line
column
message
evidence
```

A file may have:

```text
status = OK
error_kind = OK
diagnostic_class = ok
scan finding count > 0
```

A scan finding may affect release policy when explicitly configured.

It must not be mislabeled as:

```text
TYPE
SYNTAX
direct GF failure
```

unless GF execution independently supports that conclusion.

---

# 46. Warnings

The canonical final error-kind enum does not contain `WARNING`.

Warnings are separate non-fatal diagnostic records.

A warning may coexist with:

```text
status = OK
```

or with a failing result.

A warning should define:

```text
warning code
message
source
evidence
blocking policy
```

A warning becomes release-blocking only through explicit project or framework policy.

Do not convert all warnings to `FAIL`.

Do not discard warnings from raw evidence.

---

# 47. Severity

Severity is separate from status and error kind.

A future diagnostic-record model may use:

```text
info
warning
error
fatal
```

This field must not be persisted canonically until schema-defined.

Examples:

- a fatal tool diagnostic can produce `status = ERROR`;
- an error-level GF diagnostic can produce `status = FAIL`;
- a warning can coexist with `status = OK`.

Severity does not determine causal class.

---

# 48. Diagnostic origin

A future structured diagnostic may identify origin:

```text
framework
gf
scenario
normalizer
gold_comparator
artifact_verifier
filesystem
configuration
external_tool
```

Origin is useful because `INTERNAL`, `OTHER`, and `TOOL` can otherwise be ambiguous.

Until a schema field exists, origin should be preserved through:

- component ownership;
- evidence path;
- primary message;
- detail artifact.

Origin must not be inferred from report prose.

---

# 49. Raw evidence

For every external execution, preserve when applicable:

```text
executable
ordered arguments
working directory
environment overrides
start time
end time
duration
exit code
execution state
launch error
stdout path
stderr path
produced artifacts
```

Diagnostic normalization must not replace raw evidence.

A parser defect must remain recoverable from raw output.

---

# 50. Stream handling

## 50.1 Separate capture

stdout and stderr must be captured separately.

## 50.2 Joint interpretation

Diagnostic parsing must consider both streams.

## 50.3 No stdout-only success

Success must not be inferred from stdout alone.

## 50.4 Cross-stream order

When exact stdout/stderr interleaving is unavailable, the parser must not invent a total order.

## 50.5 Source attribution

Every selected excerpt identifies its source stream.

---

# 51. Diagnostic deduplication

## 51.1 Purpose

GF or wrappers may repeat equivalent messages.

## 51.2 Deduplication key

A deduplication strategy may use:

```text
error_kind
diagnostic_code
normalized message
source path
line
column
origin
```

## 51.3 Raw preservation

Deduplication affects structured presentation, not raw logs.

## 51.4 No semantic merging

Do not merge diagnostics that differ in:

- source;
- expected/actual type;
- assertion ID;
- artifact role;
- blocker;
- execution state.

---

# 52. Top-error aggregation

Top errors aggregate repeated normalized diagnostics.

Recommended key:

```text
error_kind
normalized primary message
```

Optional future key dimensions:

```text
diagnostic_code
origin
```

Top-error counts must not:

- count downstream cascades as independent root causes by default;
- combine warnings and failures silently;
- combine different source meanings under vague text;
- omit the error kind.

Ordering:

```text
descending count
then error kind
then normalized message
```

---

# 53. Regression comparison

Regression comparison uses stable result identity and status.

Diagnostic comparison may include:

```text
error_kind
diagnostic_class
diagnostic_code when available
primary message fingerprint
blocker identity
```

Canonical change kinds remain:

```text
unchanged
improved
regressed
new
removed
```

A diagnostic-class change may be meaningful even when status remains `FAIL`.

Example:

```text
previous: FAIL / ambiguous
current: FAIL / direct
```

This is not necessarily improvement or regression by status.

Reports may describe it as improved diagnostic precision.

---

# 54. Overall run status

Per-result diagnostic values contribute to overall run status through stage and mode policy.

Recommended precedence:

```text
ERROR > FAIL > OK
```

A result-level `SKIPPED` affects overall status according to requiredness.

The run must not aggregate causal classes as status.

Examples:

- many downstream failures can still produce overall `FAIL`;
- one required configuration `ERROR` can produce overall `ERROR`;
- `noise` does not independently force failure;
- one required skipped scenario prevents release `OK`.

---

# 55. Exit codes

Process exit code is evidence.

It is not the same as:

```text
validation status
execution state
error kind
diagnostic class
GF Wordbench CLI exit code
```

A zero external-tool exit must not override:

- fatal diagnostic;
- missing required marker;
- missing required artifact;
- incomplete scenario;
- gold mismatch.

A non-zero external-tool exit normally indicates failure but does not identify its kind or causal class.

Exact GF Wordbench CLI exit numbers belong to:

```text
docs/reference/EXIT_CODES.md
```

---

# 56. Unknown diagnostics

## 56.1 Required behavior

When a diagnostic is not recognized:

```text
error_kind = OTHER
```

unless process/configuration evidence supports another canonical kind.

## 56.2 Preserve evidence

Retain:

- raw text;
- source stream;
- exit code;
- execution state;
- tool version;
- command;
- context.

## 56.3 No false success

Unknown text plus failed process cannot become `OK`.

## 56.4 Pattern update

A new diagnostic parser rule requires:

- fixture;
- GF version applicability;
- specific priority;
- expected kind;
- evidence capture;
- regression test;
- documentation update when public.

---

# 57. Conflicting diagnostics

If evidence conflicts:

- preserve all relevant evidence;
- select the primary according to deterministic priority;
- use `ambiguous` when causal relation is uncertain;
- prefer specific process truth over speculative project diagnosis;
- do not suppress a fatal diagnostic because another stream appears successful.

Example:

```text
exit code = 0
stderr contains fatal GF diagnostic
required artifact missing
```

Result cannot be `OK`.

---

# 58. Diagnostic confidence

A report may display confidence:

```text
confirmed
supported
uncertain
```

Confidence is derived presentation.

It is not a canonical diagnostic class.

Recommended meaning:

| Confidence | Meaning |
|---|---|
| `confirmed` | Explicit evidence establishes the statement |
| `supported` | Multiple evidence items support it but alternatives remain |
| `uncertain` | Evidence is incomplete or conflicting |

A future persisted confidence field requires schema review.

---

# 59. Diagnostic rendering

## 59.1 JSON

`summary.json` uses exact canonical enum values.

## 59.2 Markdown

Markdown reports render enum values in inline code.

## 59.3 AI-ready packet

The AI-ready report must distinguish:

```text
Status
Execution state
Error kind
Causal class
Detailed condition
Evidence
```

## 59.4 Console

Console output may abbreviate for humans.

It must not introduce new canonical values.

## 59.5 GUI

GUI labels may be localized.

The underlying model stores canonical values.

---

# 60. Migration from the predecessor implementation

The predecessor implementation used:

```text
Status:
  OK
  FAIL
  SKIPPED

DiagnosticClass:
  ok
  direct
  downstream
  ambiguous
  noise
  skipped

ErrorKind:
  OK
  OTHER
  TYPE
  SYNTAX
  INTERNAL
  TIMEOUT
  SCRIPT
```

The final vocabulary adds:

```text
status:
  ERROR

error_kind:
  CONFIG
  IO
  TOOL

execution_state:
  completed
  timed_out
  cancelled
  launch_failed
```

## 60.1 Legacy status migration

Legacy failures caused by framework inability must migrate to `ERROR` when evidence supports it.

Do not preserve `FAIL` merely because the old model lacked `ERROR`.

## 60.2 Legacy timeout migration

Legacy:

```text
timed_out = true
error_kind = TIMEOUT
status = FAIL
diagnostic_class = direct
```

Canonical migration should review context.

Typical canonical result:

```text
status = ERROR
execution_state = timed_out
error_kind = TIMEOUT
diagnostic_class = ambiguous
```

## 60.3 Legacy script migration

Legacy `SCRIPT` may represent:

- actual scenario validation failure;
- framework script-building error;
- file processing exception.

Migration must inspect evidence and choose:

```text
SCRIPT
CONFIG
IO
INTERNAL
TOOL
OTHER
```

appropriately.

## 60.4 Legacy directness

The predecessor classifier considered:

```text
INTERNAL
TIMEOUT
SCRIPT
```

obviously direct.

Canonical final logic must distinguish technical origin from project causality.

## 60.5 Legacy unknown values

Unknown legacy values are preserved as migration warnings and mapped only when evidence supports a canonical value.

---

# 61. Schema-version rules

Adding an error kind or diagnostic class can break strict readers.

Therefore:

- adding a canonical enum value requires at least a schema minor increment;
- removing or redefining a value requires a schema major increment;
- writers emit only supported canonical values;
- strict readers reject unknown enum values;
- historical readers may preserve unknown values without reinterpretation;
- migrations report lossy mappings;
- retired values are not reused.

This reference’s vocabulary version is not a substitute for the persisted schema version.

---

# 62. Extension procedure

A new broad error kind is justified only when:

- existing kinds cannot represent the condition accurately;
- the condition is stable across several real cases;
- reports and release policy need broad grouping;
- detailed diagnostic code alone is insufficient.

Required change record:

```text
proposed error kind
purpose
existing kinds considered
producer
consumers
default status
execution-state compatibility
causal-class compatibility
persisted-schema impact
report impact
migration
tests
```

A new detailed diagnostic code has a lower threshold but still requires stable semantics and tests once public.

---

# 63. Test requirements

Recommended tests:

```text
tests/diagnostics/test_error_kinds.py
tests/diagnostics/test_execution_states.py
tests/diagnostics/test_diagnostic_classes.py
tests/diagnostics/test_primary_diagnostic.py
tests/diagnostics/test_gf_diagnostic_parsing.py
tests/diagnostics/test_diagnostic_migration.py
tests/contracts/test_diagnostic_vocabulary.py
tests/schemas/test_diagnostic_enums.py
```

## 63.1 Enum tests

Verify exact canonical values:

```text
OK
FAIL
ERROR
SKIPPED

completed
timed_out
cancelled
launch_failed

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

ok
direct
downstream
ambiguous
noise
skipped
```

## 63.2 Combination tests

Required cases:

```text
OK + completed + OK + ok
FAIL + completed + TYPE + direct
FAIL + completed + TYPE + downstream
FAIL + completed + OTHER + ambiguous
ERROR + timed_out + TIMEOUT + ambiguous
ERROR + launch_failed + TOOL + skipped
ERROR + completed + IO + ambiguous
SKIPPED + OK + skipped
```

## 63.3 Invalid-combination tests

Reject or flag:

```text
FAIL + error_kind OK
OK + diagnostic_class direct
downstream + empty blocker when blocker is known
direct + is_direct false
skipped + is_direct true
timed_out + error_kind SYNTAX
launch_failed + status OK
unknown canonical enum value
```

## 63.4 Parser tests

Cover:

```text
GF syntax diagnostic
GF type diagnostic
GF internal diagnostic
stdout-only diagnostic
stderr-only diagnostic
conflicting streams
unknown diagnostic
path with spaces
Windows path
Unicode message
missing source location
duplicate lines
```

## 63.5 Classifier tests

Cover:

```text
self-referenced direct failure
confirmed dependency downstream failure
collapsed root blocker
ambiguous reference
successful result
intentional skip
framework preflight error
timeout without causal proof
script failure with failed entrypoint
noise does not suppress failure
```

## 63.6 Migration tests

Cover:

```text
legacy missing ERROR status
legacy direct timeout
legacy direct internal error
legacy SCRIPT used for I/O
legacy framework_error
unknown legacy error kind
loss reporting
idempotent migration
```

---

# 64. Contract invariants

```text
INV-DIAG-001 Status, execution state, error kind, and causal class are distinct.
INV-DIAG-002 Raw evidence is preserved before parsing.
INV-DIAG-003 Both stdout and stderr are considered.
INV-DIAG-004 A zero exit code is not complete success evidence.
INV-DIAG-005 Unknown diagnostics never become OK.
INV-DIAG-006 Parser assigns technical kind, not causal class.
INV-DIAG-007 Classifier assigns causal class, not process outcome.
INV-DIAG-008 Directness requires evidence.
INV-DIAG-009 Downstream classification records blockers when known.
INV-DIAG-010 Ambiguity is preferred over false certainty.
INV-DIAG-011 Noise is preserved raw.
INV-DIAG-012 Required skipped work affects run status.
INV-DIAG-013 Timeout is distinct from GF syntax/type failure.
INV-DIAG-014 Framework error is represented through status/kind/state, not a canonical causal class.
INV-DIAG-015 Enum changes are versioned.
INV-DIAG-016 Reports consume structured diagnostics and never reclassify independently.
```

---

# 65. Anti-drift indicators

Probable diagnostic drift exists when:

- one module introduces a new status literal;
- one report introduces a new error kind;
- `framework_error` is emitted as a new canonical causal class;
- a timeout is reported as `SYNTAX`;
- a launch failure is reported as `TYPE`;
- an I/O failure is reported as project `FAIL` without justification;
- directness is inferred from file-processing order;
- every `INTERNAL` error is classified direct;
- every `SCRIPT` error is classified direct;
- every timeout is classified direct;
- downstream failure has no blocker despite known dependency evidence;
- ambiguous failure is forced into direct for report simplicity;
- noise is removed from raw evidence;
- static scan findings become GF error kinds;
- warnings become `FAIL` automatically;
- reports parse other reports to recover diagnostics;
- stdout is used while stderr is discarded;
- zero exit overrides missing artifact;
- unknown parser output becomes `OK`;
- a detailed code is emitted without schema ownership;
- `is_direct` conflicts with diagnostic class;
- migration silently maps unknown values;
- top-error aggregation counts downstream cascades as independent root errors;
- GUI localization writes localized enum values into JSON;
- the schema enum and Python model disagree;
- a new GF version changes message patterns without fixtures;
- a parser normalizes away source location;
- cancellation is treated as a canonical error kind;
- execution state is inferred from validation status alone.

Every indicator requires contract review.

---

# 66. Review checklist

```text
[ ] Validation status is correct
[ ] Execution state is correct
[ ] Error kind is the most specific justified kind
[ ] Diagnostic class is evidence-based
[ ] Detailed code is stable or kept internal
[ ] Primary message is bounded
[ ] Source location is preserved when available
[ ] stdout path is preserved
[ ] stderr path is preserved
[ ] Exit code is preserved
[ ] Timeout information is preserved
[ ] Launch error is preserved
[ ] Required artifact checks are preserved
[ ] Directness is not inferred from order alone
[ ] Downstream blockers are normalized
[ ] Ambiguity is explicit
[ ] Noise remains in raw evidence
[ ] Skipped work is explicit
[ ] Static scan findings remain separate
[ ] Warnings remain separate
[ ] Reports do not reclassify
[ ] JSON uses canonical enum spellings
[ ] Legacy values are migrated with warnings
[ ] Schema version impact is reviewed
[ ] Unit tests pass
[ ] Contract tests pass
[ ] Real-GF fixtures are updated when needed
```

---

# 67. Quick reference

## 67.1 Status

```text
OK       criterion passed
FAIL     criterion executed and failed
ERROR    contract could not be executed or interpreted reliably
SKIPPED  intentionally not executed
```

## 67.2 Execution state

```text
completed     operation reached a normal terminal point
timed_out     deadline expired
cancelled     controller requested termination
launch_failed process could not start
```

## 67.3 Error kind

```text
OK        no technical error
OTHER     real failure not fitting a specific family
TYPE      GF type or unification failure
SYNTAX    GF source or command syntax failure
INTERNAL  internal invariant or implementation failure
TIMEOUT   configured deadline exceeded
SCRIPT    scenario, marker, assertion, or script contract failure
CONFIG    invalid or missing configuration
IO        filesystem, encoding, read, or write failure
TOOL      external-tool availability, compatibility, or contract failure
```

## 67.4 Diagnostic class

```text
ok          no causal failure
direct      target/provider is the supported root-like failure
downstream  confirmed failed dependency caused the result
ambiguous   failure exists but causal origin is uncertain
noise       evidence excluded from root-cause ranking
skipped     semantic validation was intentionally not executed or not reached
```

---

# 68. Example records

## 68.1 Direct type error

```json
{
  "status": "FAIL",
  "execution_state": "completed",
  "error_kind": "TYPE",
  "diagnostic_class": "direct",
  "primary_message": "GrammarX.gf:42:7: cannot unify expected and actual types",
  "blocked_by": []
}
```

## 68.2 Downstream failure

```json
{
  "status": "FAIL",
  "execution_state": "completed",
  "error_kind": "OTHER",
  "diagnostic_class": "downstream",
  "primary_message": "Entrypoint could not load failed provider GrammarX",
  "blocked_by": [
    "project/src/GrammarX.gf"
  ]
}
```

## 68.3 Timeout

```json
{
  "status": "ERROR",
  "execution_state": "timed_out",
  "error_kind": "TIMEOUT",
  "diagnostic_class": "ambiguous",
  "primary_message": "Compilation exceeded the configured 60-second timeout",
  "blocked_by": []
}
```

## 68.4 Configuration error

```json
{
  "status": "ERROR",
  "execution_state": "launch_failed",
  "error_kind": "CONFIG",
  "diagnostic_class": "skipped",
  "primary_message": "Configured GF executable does not exist",
  "blocked_by": []
}
```

## 68.5 Scenario assertion failure

```json
{
  "status": "FAIL",
  "execution_state": "completed",
  "error_kind": "SCRIPT",
  "diagnostic_class": "direct",
  "primary_message": "Required assertion `basic-clause-nonempty` failed",
  "blocked_by": []
}
```

These examples are semantic illustrations.

The active persisted schema determines which fields may be emitted.

---

# 69. Documentation ownership

This document owns:

- canonical diagnostic vocabulary;
- error-kind semantics;
- diagnostic-class semantics;
- cross-axis interpretation;
- compatibility guidance for `framework_error`.

Other documents own:

| Topic | Owner |
|---|---|
| Status-only reference | `docs/reference/STATUS_VALUES.md` |
| Exact parser patterns | `docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md` |
| GF parser implementation rules | `docs/diagnostics/GF_DIAGNOSTIC_PARSING.md` |
| Direct/downstream algorithm | `docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md` |
| Process failure behavior | `docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md` |
| Persistent enum fields | `docs/PERSISTED_SCHEMA_LOCK.md` |
| CLI exit numbers | `docs/reference/EXIT_CODES.md` |
| Report presentation | `docs/reports/` |
| Scenario marker/assertion errors | `docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md` |

Downstream documents should link here instead of redefining error-kind meanings.

---

# 70. Final enforcement rule

A diagnostic is trustworthy only when it states separately:

- whether validation passed;
- whether execution completed;
- what technical family applies;
- what causal relationship is supported;
- which evidence proves the statement.

Therefore:

> No GF Wordbench component may use an error kind as a validation status, an execution state as a causal class, a process exit code as a complete diagnosis, or a framework failure as an unproven project root cause.
