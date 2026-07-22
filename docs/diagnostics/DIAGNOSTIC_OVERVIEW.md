# GF Wordbench — Diagnostic Overview

**Document ID:** `GF-WB-DIAGNOSTIC-OVERVIEW`  
**Status:** Normative diagnostic architecture  
**Applies to:** GF Wordbench framework, validation pipeline, reports, and one active GF language project  
**Owner:** GF Wordbench maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\diagnostics\DIAGNOSTIC_OVERVIEW.md`  
**Document version:** `1.0.0`

---

## 1. Purpose

This document defines the diagnostic model used by GF Wordbench.

It explains:

- what a diagnostic is;
- which evidence is authoritative;
- how GF diagnostics, framework errors, static findings, scenario failures, gold mismatches, and artifact failures remain distinct;
- how validation status differs from execution state;
- how error kind differs from causal classification;
- how direct, downstream, ambiguous, noise, and skipped results are assigned;
- how diagnostic evidence flows from raw output to reports;
- how confidence and uncertainty are represented;
- how failures are grouped without losing their original evidence;
- how the current audit implementation migrates to the final GF Wordbench model;
- which invariants tests and reports must preserve.

This is the overview document.

Detailed behavior is owned by:

```text
docs/diagnostics/ERROR_CLASSIFICATION.md
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
docs/diagnostics/GF_DIAGNOSTIC_PARSING.md
docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md
docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md
```

Pipeline ordering is owned by:

```text
docs/validation/VALIDATION_PIPELINE.md
```

External process behavior is locked by:

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
```

Persisted diagnostic fields are locked by:

```text
docs/PERSISTED_SCHEMA_LOCK.md
```

Python component boundaries are locked by:

```text
docs/INTERFILE_CONTRACT_LOCK.md
```

---

## 2. Diagnostic objective

The diagnostic system must answer:

1. **What operation was attempted?**
2. **What evidence was produced?**
3. **Did execution complete normally?**
4. **Did the requested validation criterion pass?**
5. **What kind of problem occurred?**
6. **Where is the most likely causal source?**
7. **What other items are blocked by that source?**
8. **How certain is the interpretation?**
9. **Which raw artifacts support the conclusion?**
10. **What should be investigated first?**

The purpose is not to produce a convincing narrative.

The purpose is to produce a traceable, conservative, evidence-backed diagnosis.

---

## 3. Core diagnostic rule

> No diagnostic conclusion may replace or destroy the evidence from which it was derived.

Every diagnostic conclusion must remain traceable to one or more of:

- stdout;
- stderr;
- process metadata;
- source file;
- scan log;
- GF diagnostic location;
- scenario marker;
- normalized scenario output;
- gold diff;
- expected artifact check;
- project dependency map;
- previous-run structured result;
- configuration validation result.

When evidence is insufficient, GF Wordbench must say so.

It must not invent a direct root cause merely to avoid an ambiguous result.

---

## 4. Authority boundaries

### 4.1 GF is authoritative for

GF is authoritative for:

- GF source syntax;
- type checking;
- module loading;
- dependency resolution;
- grammar execution;
- parsing;
- linearization;
- generation;
- morphology;
- GF introspection;
- native GF diagnostic messages.

GF Wordbench may interpret GF output, but must not claim that its parser replaces GF’s own semantics.

### 4.2 GF Wordbench is authoritative for

GF Wordbench is authoritative for:

- process launch state;
- timeout and cancellation state;
- captured stdout and stderr;
- expected artifact checks;
- static scan findings;
- diagnostic normalization;
- scenario marker verification;
- gold comparison;
- direct/downstream classification;
- regression classification;
- result aggregation;
- report presentation.

### 4.3 Active project authority

The active project is authoritative for:

- expected module relationships;
- entrypoints;
- checkpoints;
- required scenarios;
- gold expectations;
- accepted language-specific warnings;
- known limitations;
- release-blocking diagnostic policy.

Project-specific interpretation rules must be documented under:

```text
project/docs/
```

They must not be hidden inside generic framework code.

---

## 5. The four diagnostic axes

GF Wordbench separates four independent axes.

```text
validation_status
execution_state
error_kind
diagnostic_class
```

These fields answer different questions.

They must not be merged into one status string.

---

## 6. Validation status

Validation status answers:

> Did the requested validation criterion pass?

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

### 6.1 `OK`

Use when:

- the operation executed as required;
- evidence is sufficient;
- every applicable criterion passed.

### 6.2 `FAIL`

Use when:

- execution was reliable;
- the project or tested behavior did not satisfy a validation criterion.

Examples:

- GF rejects a source module;
- required parse expectation is not met;
- linearized output differs from reviewed gold;
- required PGF is built but fails a declared content check;
- missing linearizations violate project policy.

### 6.3 `ERROR`

Use when GF Wordbench cannot reliably execute or interpret the requested validation.

Examples:

- executable cannot launch;
- process times out;
- output cannot be captured;
- required evidence disappears;
- diagnostic parser cannot determine a trustworthy result;
- output path violates containment;
- configuration is invalid;
- required artifact verification cannot run.

### 6.4 `SKIPPED`

Use when the operation was intentionally not executed.

Examples:

- optional scenario not selected;
- compile disabled in an allowed diagnostic run;
- dependent scenario blocked after its required entrypoint failed;
- PGF stage not required in quick mode.

A required skipped operation prevents an overall successful run.

---

## 7. Execution state

Execution state answers:

> What happened to the operation or process?

Canonical values:

```text
completed
timed_out
cancelled
launch_failed
```

An internal orchestration model may temporarily use:

```text
not_started
```

but it must not be exposed as a canonical persisted value unless the schema lock is updated.

### 7.1 `completed`

The operation reached normal process or stage completion.

This does not imply validation success.

A completed GF compile may still be `FAIL`.

### 7.2 `timed_out`

The operation exceeded its finite timeout.

Typical mapping:

```text
execution_state = timed_out
validation_status = ERROR
error_kind = TIMEOUT
```

### 7.3 `cancelled`

The user or controlling system stopped execution.

Cancellation must remain distinguishable from timeout.

A cancelled required operation cannot produce overall `OK`.

### 7.4 `launch_failed`

GF Wordbench could not start the process.

Typical mapping:

```text
execution_state = launch_failed
validation_status = ERROR
error_kind = TOOL or IO
```

---

## 8. Error kind

Error kind answers:

> What broad technical or GF-facing type of problem occurred?

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

### 8.1 `OK`

No error kind applies.

It does not mean there are no non-blocking static findings.

### 8.2 `TYPE`

GF reports a type or unification problem.

Examples:

- incompatible lincat type;
- constructor argument mismatch;
- unification failure;
- record-field type mismatch;
- incompatible concrete implementation.

### 8.3 `SYNTAX`

GF reports invalid source or command syntax.

Examples:

- malformed GF source expression;
- invalid module declaration;
- parser error in a `.gf` file;
- malformed supported GF shell command input.

### 8.4 `INTERNAL`

An internal invariant or unexpected framework/GF condition fails.

This category must be used carefully.

It must not hide:

- configuration errors;
- launch failures;
- timeouts;
- ordinary GF type failures.

### 8.5 `TIMEOUT`

A finite time limit was exceeded.

Timeout is not a GF syntax or type failure.

### 8.6 `SCRIPT`

A GF scenario or framework-controlled script contract fails.

Examples:

- required marker missing;
- malformed scenario metadata;
- scenario cannot be interpreted;
- prohibited shell escape detected.

A language assertion failure inside a valid scenario may instead be `OTHER`, `TYPE`, or a more precise kind depending on evidence.

### 8.7 `CONFIG`

Configuration is missing, invalid, contradictory, or unsupported.

Examples:

- unknown checkpoint;
- missing project identity;
- invalid timeout;
- duplicate scenario ID;
- unsupported schema version.

### 8.8 `IO`

A filesystem, encoding, or stream operation fails.

Examples:

- source unreadable;
- output unwritable;
- raw log cannot be persisted;
- invalid UTF-8 prevents exact comparison;
- artifact disappears during verification.

### 8.9 `TOOL`

An external tool or its contract fails outside ordinary language validation.

Examples:

- GF executable missing;
- unsupported GF version;
- required command capability absent;
- process launch failure;
- expected tool artifact missing despite apparent process success.

### 8.10 `OTHER`

The evidence proves a failure, but no more specific canonical kind applies.

`OTHER` must not become a substitute for incomplete diagnostic work.

---

## 9. Diagnostic class

Diagnostic class answers:

> What is this result’s causal position relative to the project?

Canonical values:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

### 9.1 `ok`

The item satisfies its required criterion.

A file may be `ok` while still having non-blocking static findings.

### 9.2 `direct`

Evidence indicates that the item is a likely local or root source of failure.

Examples:

- diagnostic location points to the file itself;
- file-local syntax error;
- source-local type mismatch;
- the item is the first known failed provider;
- a scenario’s own required assertion fails without a failed prerequisite.

`direct` means likely causal source.

It does not mean absolute certainty.

### 9.3 `downstream`

The item fails or cannot run because a known provider failed.

A downstream result should identify at least one blocker when known:

```text
blocked_by[]
```

Examples:

- top-level grammar fails after a required resource module fails;
- scenario cannot load an entrypoint because the entrypoint did not compile;
- PGF build is blocked by a failed concrete grammar.

### 9.4 `ambiguous`

Evidence is insufficient to classify the result as direct or downstream.

Use when:

- first error points outside the current item but dependency evidence is incomplete;
- several candidate providers failed;
- diagnostic wording is version-dependent and not safely interpreted;
- a combined operation obscures which input caused the failure.

Ambiguous is a correct result when certainty is unavailable.

### 9.5 `noise`

The item or finding is non-actionable under documented selection policy.

Examples:

- excluded backup source;
- generated duplicate excluded from validation;
- recognized non-project file;
- known harmless diagnostic line excluded from actionable grouping.

Noise must never hide a required project failure.

### 9.6 `skipped`

The item was intentionally not executed.

When the item is blocked by a known provider, prefer:

```text
validation_status = SKIPPED
diagnostic_class = downstream
blocked_by = [...]
```

Use `skipped` when omission is policy-driven rather than causally blocked.

---

## 10. Operational diagnostic kinds

GF Wordbench may use more detailed operational diagnostic labels in logs, internal models, or diagnostic records.

Recommended values include:

```text
gf_compile_failure
gf_scenario_failure
launch_failure
timeout
contract_failure
artifact_failure
normalization_failure
gold_mismatch
configuration_failure
unsupported_version
diagnostic_parse_failure
encoding_failure
path_containment_failure
source_mutation
```

These values do not replace the four canonical axes.

Example:

```text
validation_status = ERROR
execution_state = completed
error_kind = TOOL
diagnostic_class = direct
operational_kind = artifact_failure
```

A new persisted operational kind requires schema review.

---

## 11. Diagnostic evidence hierarchy

Not all evidence has equal authority.

Recommended hierarchy:

1. raw external process evidence;
2. verified process metadata;
3. verified generated artifacts;
4. native GF diagnostic location and text;
5. scenario markers and structured assertions;
6. normalized output;
7. gold diff;
8. project dependency map;
9. static scan findings;
10. previous-run comparison;
11. human interpretation.

Lower-ranked evidence may support a conclusion but must not silently override contradictory higher-ranked evidence.

### 11.1 Raw process evidence

Includes:

- stdout;
- stderr;
- exit code;
- timeout state;
- launch error;
- command;
- working directory;
- produced files.

### 11.2 Native diagnostic evidence

Includes:

- GF error message;
- source path;
- line and column;
- module name;
- type/unification details;
- command context.

### 11.3 Derived evidence

Includes:

- normalized messages;
- extracted first error;
- grouped diagnostics;
- causal classification;
- regression labels;
- AI-ready excerpts.

Derived evidence must reference raw evidence.

---

## 12. Diagnostic lifecycle

The canonical diagnostic lifecycle is:

```text
capture
→ preserve
→ decode
→ parse
→ normalize
→ classify technical kind
→ classify causal relationship
→ aggregate
→ compare
→ report
```

### 12.1 Capture

Capture process metadata and streams.

### 12.2 Preserve

Write raw evidence before interpretation.

### 12.3 Decode

Apply the explicit UTF-8 policy without silently discarding bytes.

### 12.4 Parse

Extract recognized diagnostic structures.

### 12.5 Normalize

Remove only approved unstable environment noise.

### 12.6 Classify technical kind

Assign `error_kind` and operational diagnostic kind.

### 12.7 Classify causal relationship

Assign `diagnostic_class` and `blocked_by`.

### 12.8 Aggregate

Group repeated errors without losing individual records.

### 12.9 Compare

Build previous-run regression entries.

### 12.10 Report

Render structured facts for humans and AI systems.

---

## 13. Raw evidence contract

For every external operation, preserve when applicable:

```text
operation ID
operation kind
subject ID
command
working directory
environment overrides
started_at
finished_at
duration_ms
execution state
exit code
timeout state
cancellation state
launch error
stdout path
stderr path
produced artifacts
```

### 13.1 Separate streams

Stdout and stderr remain separate.

Diagnostic parsing considers both.

### 13.2 Immutability

Raw evidence becomes immutable after capture.

Derived diagnostic summaries must not overwrite it.

### 13.3 Missing raw evidence

If required raw evidence is missing:

```text
validation_status = ERROR
error_kind = IO or INTERNAL
operational_kind = artifact_failure
```

The system must not pretend that a parsed summary is the original evidence.

---

## 14. Static diagnostic findings

Static scanning detects suspicious source patterns.

Static findings are not GF errors.

A static finding should contain:

```text
rule_id
file_path
line or range
message
severity
evidence excerpt
blocking policy
```

### 14.1 Current foundational rules

The current scanner foundation includes checks for:

- suspicious slash/equality patterns;
- suspicious doubled-slash/dash patterns;
- runtime string matching;
- untyped case blocks with string patterns;
- untyped table blocks with string patterns;
- trailing whitespace.

### 14.2 Static result policy

A file may have:

```text
validation_status = OK
diagnostic_class = ok
scan findings > 0
```

when findings are non-blocking.

Static findings must be presented separately from compile failures.

### 14.3 Blocking static rules

A project may declare selected rules release-blocking.

Such policy must be explicit in project validation documentation.

The framework must not silently promote warnings to failures.

---

## 15. GF compilation diagnostics

Compilation diagnostics originate from:

```text
raw/compile/<safe-file-key>.out.txt
raw/compile/<safe-file-key>.err.txt
```

The compile diagnostic interpreter should extract:

```text
exit_code
timed_out
error_kind
first_error
error_detail
source locations
fatal messages
stdout_path
stderr_path
expected artifact state
```

### 15.1 Compile success

A compile is not `OK` unless:

- process launched;
- no timeout;
- exit indicates success;
- no recognized fatal diagnostic;
- required artifacts exist.

### 15.2 Compile failure

A normal GF source rejection is usually:

```text
validation_status = FAIL
execution_state = completed
error_kind = TYPE, SYNTAX, OTHER, or INTERNAL
```

`INTERNAL` should represent a real internal diagnostic, not every unknown message.

### 15.3 Compile infrastructure error

Examples:

```text
launch_failed
timed_out
raw output unwritable
artifact verification unavailable
```

These are normally `ERROR`, not ordinary language `FAIL`.

---

## 16. Scenario diagnostics

Scenario diagnostics combine:

- GF process evidence;
- required marker checks;
- forbidden marker checks;
- scenario assertions;
- normalized output;
- gold comparison;
- expected artifacts.

### 16.1 Process completion is insufficient

A scenario may complete with exit code zero while:

- a command was ignored;
- a required section never ran;
- a marker is missing;
- output is incomplete;
- expected artifact is absent;
- gold comparison fails.

### 16.2 Scenario contract error

Examples:

- malformed scenario metadata;
- missing required end marker;
- duplicate section ID;
- unsupported shell command under policy;
- invalid normalization header.

Typical mapping:

```text
validation_status = ERROR
error_kind = SCRIPT
operational_kind = contract_failure
```

### 16.3 Scenario validation failure

Examples:

- parse assertion fails;
- expected linearization absent;
- required missing-function list is non-empty;
- reviewed gold differs.

Typical mapping:

```text
validation_status = FAIL
execution_state = completed
diagnostic_class = direct or downstream
```

---

## 17. Gold mismatch diagnostics

A gold mismatch is a validation failure when:

- the scenario executed reliably;
- normalization succeeded;
- expected and actual outputs are comparable;
- the values differ.

Typical mapping:

```text
validation_status = FAIL
execution_state = completed
error_kind = OTHER
operational_kind = gold_mismatch
```

The diagnostic record must reference:

```text
scenario ID
gold path
actual normalized path
diff path
normalization version
```

A missing required gold file is a project completeness failure.

An unreadable gold file is an `ERROR`.

---

## 18. Artifact diagnostics

Artifact validation checks:

- existence;
- containment;
- file type;
- non-empty requirement;
- hash;
- expected name;
- manifest registration;
- producer identity.

### 18.1 Missing required artifact

A required artifact missing after apparent tool success is:

```text
validation_status = ERROR or FAIL
error_kind = TOOL
operational_kind = artifact_failure
```

Use `ERROR` when the external contract is violated or the result cannot be trusted.

Use `FAIL` only when project policy intentionally treats artifact absence as a successfully evaluated project criterion.

### 18.2 Invalid PGF

Examples:

- expected PGF missing;
- zero-byte PGF;
- PGF outside run root;
- filename does not match declared release target;
- PGF not registered in manifest.

Release must not pass.

---

## 19. Configuration diagnostics

Configuration diagnostics occur before or during validation setup.

Examples:

- malformed `project.toml`;
- unsupported schema;
- duplicate scenario ID;
- unknown validation mode;
- missing entrypoint;
- invalid regex;
- invalid timeout;
- conflicting flags;
- unresolved template placeholder in active project.

Typical mapping:

```text
validation_status = ERROR
error_kind = CONFIG
diagnostic_class = direct
```

Configuration errors must identify the authoritative source and field when known.

---

## 20. Process and tool diagnostics

Process-layer failures include:

```text
launch_failure
timeout
cancelled
encoding_failure
stream_capture_failure
termination_failure
```

The process layer must not assign:

```text
direct
downstream
ambiguous
```

Those are higher-level causal classifications.

A launch failure must not be reported as GF syntax failure.

A timeout must not be reported as ordinary compile failure.

---

## 21. Direct failure criteria

A result may be classified `direct` when one or more strong signals exist.

Strong signals:

- diagnostic path matches the current source;
- diagnostic line belongs to the current source;
- current item contains a verified syntax error;
- current item is the first failed provider in the dependency graph;
- scenario’s own assertion fails after all prerequisites pass;
- configuration source itself contains the invalid value;
- expected artifact producer completed but violated its own contract.

Weak signals alone are not sufficient:

- current file was being processed when another path appears;
- failure occurs early;
- filename resembles a provider;
- previous run failed similarly;
- static scan finding exists near unrelated GF output.

Detailed rules belong in:

```text
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
```

---

## 22. Downstream failure criteria

A result may be classified `downstream` when:

- a known imported provider failed;
- the GF diagnostic points to a failed provider;
- project dependency map confirms the relationship;
- the item was blocked before execution by a required failed prerequisite;
- scenario cannot load a known failed entrypoint;
- PGF build is blocked by a failed concrete module.

A downstream result should record:

```text
blocked_by = [stable subject IDs]
```

When several blockers exist, preserve deterministic order.

A downstream result must not inflate the count of independent root causes.

---

## 23. Ambiguous failure criteria

Use `ambiguous` when:

- no reliable source location exists;
- diagnostic text is not recognized;
- multiple plausible providers failed;
- the operation combines several inputs;
- project dependency information is incomplete;
- the first error and exit state conflict;
- output is truncated before the causal message;
- supported GF versions emit materially different structures.

Recommended report wording:

```text
The available evidence does not reliably distinguish a local failure from a dependency failure.
```

Do not replace ambiguity with speculation.

---

## 24. Noise classification

Noise is evidence that is intentionally non-actionable under explicit policy.

Examples:

- excluded backup file;
- duplicate generated file;
- harmless progress line;
- platform banner;
- repeated copy of an already-recorded diagnostic;
- non-semantic timing output.

Noise classification must be reversible through raw evidence.

Normalization or grouping may hide noise from summary views, but raw logs remain complete unless explicit truncation policy applies.

---

## 25. Confidence and certainty

GF Wordbench should communicate certainty without inventing an additional required persisted enum.

Recommended human wording:

```text
confirmed
strongly indicated
likely
uncertain
unknown
```

These phrases are explanatory.

They are not canonical schema values unless the schema lock is updated.

### 25.1 Confirmed

Direct source evidence proves the conclusion.

### 25.2 Strongly indicated

Several independent signals agree.

### 25.3 Likely

Evidence supports one explanation but does not exclude alternatives.

### 25.4 Uncertain

Evidence supports multiple explanations.

### 25.5 Unknown

Required evidence is absent or uninterpretable.

Reports must distinguish diagnostic confidence from validation status.

---

## 26. First error

`first_error` is a compact navigation field.

It is not the full diagnosis.

### 26.1 Selection

The parser should select the earliest actionable diagnostic according to documented ordering, not merely the first non-empty output line.

### 26.2 Requirements

`first_error` should:

- be concise;
- preserve meaningful GF wording;
- remove only approved environment noise;
- not contain an entire log;
- reference raw evidence;
- not paraphrase away source location.

### 26.3 Missing first error

A non-zero exit without a recognized first error remains a failure.

Use a conservative message:

```text
GF exited with a non-zero status; no recognized primary diagnostic was extracted.
```

Do not mark the operation successful.

---

## 27. Diagnostic detail

`error_detail` may contain:

- unification detail;
- expected/actual type;
- referenced module;
- relevant location;
- marker failure;
- artifact expectation;
- normalization failure;
- concise process error.

It should not duplicate complete stdout or stderr.

Large evidence remains in raw files.

---

## 28. Diagnostic locations

A diagnostic location should preserve when available:

```text
path
line
column
end_line
end_column
module_name
```

### 28.1 Path normalization

Persisted source locations should use project-relative paths.

Raw GF text may retain native paths.

### 28.2 External paths

RGL or tool paths may remain environment paths where diagnostically relevant.

Reports may render them with stable tokens in normalized views while preserving raw text.

### 28.3 Location trust

A parsed location must be marked unavailable rather than guessed when the diagnostic pattern is uncertain.

---

## 29. Grouping and top errors

Top-error grouping supports triage.

It must not replace item-level results.

### 29.1 Canonical grouping key

Recommended logical grouping:

```text
error_kind + normalized primary message
```

### 29.2 Deterministic ordering

Sort by:

1. descending count;
2. case-insensitive message;
3. stable kind.

### 29.3 Exclusions

Do not group:

- empty messages;
- successful results;
- duplicate copies of the same diagnostic from one subject unless policy counts occurrences;
- downstream summary messages as independent root causes when a direct provider is already identified.

### 29.4 Root-cause view

Reports should provide both:

```text
all failing subjects
```

and:

```text
likely direct/root failures
```

---

## 30. Diagnostic aggregation

Run-level diagnosis should summarize:

- direct failures;
- downstream failures;
- ambiguous failures;
- framework errors;
- timeouts;
- launch failures;
- scenario failures;
- gold mismatches;
- artifact failures;
- non-blocking scan findings;
- regressions;
- unresolved warnings.

Aggregation must be derived from structured result collections.

Reports must not reclassify raw items independently.

---

## 31. Regression diagnostics

Previous-run comparison classifies changes as:

```text
unchanged
improved
regressed
new
removed
```

### 31.1 Regression identity

Compare using stable subject identity.

Examples:

```text
file:<project-relative-path>
scenario:<scenario-id>
artifact:<run-relative-role>
```

### 31.2 Diagnostic regression

A result may regress through:

- `OK → FAIL`;
- `OK → ERROR`;
- `FAIL → ERROR`;
- direct failure newly appearing;
- new required gold mismatch;
- new timeout;
- missing required artifact;
- broader blocker cascade.

### 31.3 Improvement

Improvement may include:

- failure to success;
- ambiguous to correctly resolved downstream;
- framework error replaced by a reliable project failure;
- reduced blocker cascade;
- resolved gold mismatch.

A change in wording alone is not necessarily a diagnostic improvement.

---

## 32. Diagnostic reporting

GF Wordbench writes diagnostic information to:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
details/
raw/
```

### 32.1 `summary.json`

Primary machine-readable source.

It must contain structured fields and evidence paths.

### 32.2 `summary.md`

Human overview.

It should present:

- overall outcome;
- direct failures first;
- downstream blockers;
- ambiguous failures;
- scenario failures;
- release-blocking issues;
- artifact paths.

### 32.3 `AI_READY.md`

AI handoff.

It must:

- use existing `RunResult`;
- not rerun GF;
- include bounded excerpts;
- distinguish direct/downstream/ambiguous;
- identify raw artifacts;
- avoid unsupported diagnosis.

### 32.4 `top_errors.txt`

Compact grouped list.

It does not replace `summary.json`.

### 32.5 `details/`

Focused per-result diagnostic views.

Detail files may copy bounded evidence but must reference raw sources.

---

## 33. Diagnostic priority for humans

Recommended investigation order:

1. framework/configuration errors;
2. launch failures and timeouts;
3. direct source failures;
4. direct scenario failures;
5. artifact contract failures;
6. gold mismatches;
7. ambiguous failures;
8. downstream failures;
9. non-blocking static findings;
10. optional warnings.

This order prevents developers from fixing cascades before root causes.

---

## 34. Diagnostic priority for automation

Automation should evaluate:

1. overall status;
2. required stage errors;
3. required direct failures;
4. required scenario failures;
5. required artifact failures;
6. release gates;
7. regressions;
8. warnings.

Automation must use structured fields.

It must not parse prose headings or color labels.

---

## 35. Diagnostic priority for AI systems

AI-ready diagnostics should provide:

```text
run identity
GF version
mode
overall status
direct failures
downstream relationships
ambiguous failures
scenario failures
gold diffs
scan findings on otherwise successful files
raw evidence paths
bounded excerpts
```

AI prompts should explicitly require:

- evidence-based reasoning;
- no source edits without reviewing providers and consumers;
- preservation of GF module contracts;
- distinction between root and downstream failures.

---

## 36. Security and privacy

Diagnostics must not expose:

- passwords;
- access tokens;
- private keys;
- complete environment dumps;
- secret arguments;
- unrelated user files.

### 36.1 Path exposure

Local absolute paths may be necessary for diagnosis.

Portable reports may normalize them to stable tokens.

Raw evidence may retain them under local access control.

### 36.2 Untrusted output

GF output and project content must be treated as untrusted text when rendered.

GUI and HTML-like report surfaces must escape content safely.

### 36.3 Scenario output

Scenario output must not be executed or interpreted as operating-system commands by report components.

---

## 37. Diagnostic determinism

Given the same:

- source bytes;
- GF version;
- configuration;
- raw evidence;
- diagnostic parser version;
- dependency map;
- normalization version;

GF Wordbench should produce equivalent structured diagnostic results.

### 37.1 Deterministic parser rules

- stable pattern precedence;
- stable first-error selection;
- stable source-location parsing;
- stable blocker ordering;
- stable top-error grouping;
- stable report ordering.

### 37.2 Version-specific rules

GF-version-specific diagnostic patterns must be explicit.

A version adapter may select rule sets.

Silent reinterpretation is prohibited.

---

## 38. Diagnostic parser failure policy

A diagnostic parser may fail while raw evidence remains valid.

When parsing fails:

1. preserve raw evidence;
2. record parser failure;
3. retain process exit and execution state;
4. assign the most conservative valid status;
5. avoid unsupported error kind;
6. classify causality as ambiguous when needed;
7. continue independent finalization.

A parser failure must not erase a known language failure.

---

## 39. Current implementation foundation

The existing audit implementation already provides:

- compile summaries;
- `error_kind`;
- `first_error`;
- direct/downstream/ambiguous classification;
- `blocked_by`;
- top-error grouping;
- AI-ready diagnostic sections;
- raw compile and scan evidence.

Existing tests demonstrate intended distinctions between:

- direct file failure;
- downstream failure with a blocker;
- ambiguous failure;
- successful compile with scan findings;
- clean successful compile.

These are retained in GF Wordbench.

---

## 40. Required migration corrections

The final system must correct several legacy simplifications.

### 40.1 Timeout status

Legacy behavior may derive:

```text
timed_out = true
→ validation_status = FAIL
```

Final behavior should normally be:

```text
timed_out = true
execution_state = timed_out
validation_status = ERROR
error_kind = TIMEOUT
```

### 40.2 Technical failure classification

Legacy classifier behavior may treat:

```text
INTERNAL
TIMEOUT
SCRIPT
```

as automatically direct file failures.

Final behavior must separate:

- technical nature;
- execution state;
- causal position.

A timeout does not prove the source file is a direct root cause.

### 40.3 Deprecated diagnostic classes

The final canonical set excludes:

```text
script_error
framework_error
```

Use instead:

```text
validation_status
execution_state
error_kind
operational diagnostic kind
```

### 40.4 Canonical modes

Legacy mode names:

```text
file
all
```

remain migration aliases only.

Canonical reports use:

```text
quick
checkpoint
release
diagnostic
```

### 40.5 Error versus failure counts

Final reports must count separately:

```text
files_fail
files_error
scenarios_fail
scenarios_error
```

Infrastructure errors must not be hidden inside project failure counts.

---

## 41. Recommended diagnostic record

A complete internal diagnostic record may contain:

```json
{
  "diagnostic_id": "diag:file:GrammarFre:001",
  "subject_kind": "file",
  "subject_id": "lib/src/french/GrammarFre.gf",
  "validation_status": "FAIL",
  "execution_state": "completed",
  "error_kind": "TYPE",
  "diagnostic_class": "direct",
  "operational_kind": "gf_compile_failure",
  "message": "type mismatch",
  "detail": "expected ...",
  "locations": [
    {
      "path": "lib/src/french/GrammarFre.gf",
      "line": 42,
      "column": 7
    }
  ],
  "blocked_by": [],
  "evidence_paths": [
    "raw/compile/GrammarFre.out.txt",
    "raw/compile/GrammarFre.err.txt"
  ]
}
```

This is an architectural example.

It does not create a new persisted schema by itself.

Persisting this structure requires updating `PERSISTED_SCHEMA_LOCK.md`.

---

## 42. Diagnostic invariants

The following are mandatory.

1. Raw evidence exists before diagnostic parsing.
2. Stdout and stderr remain separately accessible.
3. Exit code alone does not determine success.
4. Static findings remain distinct from GF failures.
5. Validation status remains distinct from execution state.
6. Error kind remains distinct from diagnostic class.
7. Process layer does not assign causal class.
8. Classifier does not rerun GF.
9. Reports do not reclassify independently.
10. Downstream results identify blockers when known.
11. Ambiguous results remain ambiguous when evidence is insufficient.
12. A timeout is not a syntax error.
13. A launch failure is not a source failure.
14. Missing required artifacts are not accepted as success.
15. Gold mismatch does not rewrite gold.
16. Diagnostic normalization preserves linguistic evidence.
17. Top-error grouping does not destroy item identity.
18. Current structured results remain valid when previous-run comparison fails.
19. Active-language rules remain outside generic framework parsers.
20. Diagnostic conclusions reference evidence paths.

---

## 43. Required tests

Recommended test structure:

```text
tests/diagnostics/
├── test_status_mapping.py
├── test_execution_states.py
├── test_error_kinds.py
├── test_gf_diagnostic_parsing.py
├── test_first_error_selection.py
├── test_diagnostic_locations.py
├── test_direct_classification.py
├── test_downstream_classification.py
├── test_ambiguous_classification.py
├── test_noise_classification.py
├── test_scenario_diagnostics.py
├── test_gold_mismatch_diagnostics.py
├── test_artifact_diagnostics.py
├── test_timeout_diagnostics.py
├── test_launch_failure_diagnostics.py
├── test_top_error_grouping.py
└── test_diagnostic_reporting.py
```

### 43.1 Status mapping tests

- completed success;
- completed GF failure;
- timeout;
- cancellation;
- launch failure;
- skipped optional operation;
- blocked required operation.

### 43.2 Parser tests

- stdout-only diagnostic;
- stderr-only diagnostic;
- same diagnostic in both streams;
- source path with spaces;
- Windows path;
- POSIX path;
- Unicode source;
- multiline unification message;
- unknown diagnostic;
- truncated output;
- invalid UTF-8.

### 43.3 Classification tests

- self-referenced direct failure;
- known provider downstream failure;
- multiple blockers;
- ambiguous external location;
- scenario blocked by entrypoint;
- PGF blocked by concrete module;
- timeout not automatically direct;
- configuration failure direct to configuration source.

### 43.4 Reporting tests

- direct failures rendered first;
- downstream blocker shown;
- ambiguous uncertainty shown;
- scan hits on compile-OK file shown separately;
- raw evidence links preserved;
- no report reruns GF;
- top errors deterministic;
- secrets absent.

---

## 44. Diagnostic drift indicators

Probable drift exists when:

- a new status appears in only one module;
- timeout maps to `FAIL` in one stage and `ERROR` in another;
- process layer assigns `direct`;
- report writers infer blockers independently;
- `script_error` or `framework_error` reappears as diagnostic class;
- a downstream result lacks blocker evidence despite a known dependency;
- a parser removes line numbers from raw evidence;
- static scan warnings appear as GF type errors;
- gold mismatch becomes `TOOL`;
- launch failure becomes `SYNTAX`;
- top-error grouping counts downstream copies as root causes;
- AI-ready report states certainty not present in structured results;
- raw stderr is discarded after extracting a message;
- previous-run prose is parsed for regression logic;
- unknown GF diagnostic is silently mapped to a specific type;
- result fields disagree with aggregate counts.

Any drift indicator requires contract and test review.

---

## 45. Diagnostic change workflow

A diagnostic change is complete only when:

```text
[ ] Evidence source identified
[ ] Parser owner identified
[ ] Status mapping reviewed
[ ] Execution-state mapping reviewed
[ ] Error-kind mapping reviewed
[ ] Causal-classification impact reviewed
[ ] Raw evidence preservation reviewed
[ ] Persisted schema reviewed
[ ] Report impact reviewed
[ ] Previous-run compatibility reviewed
[ ] Unit tests updated
[ ] Integration fixtures updated
[ ] Known GF versions reviewed
[ ] Documentation updated
[ ] Contract lock updated when required
```

Examples of diagnostic contract changes:

- adding an error kind;
- changing timeout mapping;
- changing first-error selection;
- adding a GF message pattern;
- changing blocker inference;
- changing top-error grouping;
- changing normalized diagnostic text;
- persisting a new diagnostic field.

No such change may be made in only one consumer.

---

## 46. Related documentation

Read with:

```text
docs/00_START_HERE.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/STATIC_SCANNING.md
docs/validation/COMPILATION_VALIDATION.md
docs/validation/SCENARIO_VALIDATION.md
docs/diagnostics/ERROR_CLASSIFICATION.md
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
docs/diagnostics/GF_DIAGNOSTIC_PARSING.md
docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md
docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md
docs/reports/AI_READY_REFERENCE.md
docs/reference/STATUS_VALUES.md
docs/reference/DIAGNOSTIC_KINDS.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/KNOWN_ISSUES.md
project/docs/STATUS_LEDGER.md
```

---

## 47. Final rule

A useful diagnosis is not merely an error message.

> A GF Wordbench diagnosis must state what was validated, what executed, what evidence exists, what kind of problem occurred, where the likely causal source lies, what is blocked by it, and how certain that interpretation is.

When the evidence supports only uncertainty, the correct diagnosis is uncertainty.

When the problem belongs to infrastructure, it must not be blamed on the language source.

When the problem is downstream, it must not be presented as an independent root failure.

Every conclusion must remain traceable to preserved evidence.
