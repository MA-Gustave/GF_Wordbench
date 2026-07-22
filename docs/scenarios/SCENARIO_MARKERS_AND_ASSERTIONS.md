# GF Wordbench — Scenario Markers and Assertions

**Document ID:** `GF-WB-SCENARIO-MARKERS-ASSERTIONS`  
**Status:** Normative  
**Applies to:** Native `.gfs` validation scenarios executed by GF Wordbench  
**Owner:** GF Wordbench maintainers  
**Project counterpart:** `project/docs/VALIDATION_SPEC.md`  
**Protocol version:** `1.0.0`  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\scenarios\SCENARIO_MARKERS_AND_ASSERTIONS.md`  
**Last structural review:** 2026-07-22

---

## 1. Purpose

This document defines how a GF Wordbench scenario proves that its intended operations ran and that their results satisfy declared validation criteria.

It specifies:

- the canonical raw-output marker syntax;
- marker identity and parsing rules;
- section-completion rules;
- the boundary between raw and normalized output;
- the assertion model;
- built-in assertion types;
- assertion evaluation order;
- failure and error semantics;
- result aggregation;
- evidence requirements;
- extension rules;
- testing requirements;
- anti-drift checks.

A scenario is not successful merely because the GF process returned exit code `0`.

The central rule is:

> Scenario success requires explicit completion evidence and successful evaluation of every required assertion.

---

## 2. Scope

This document governs:

- markers emitted during `.gfs` execution;
- marker parsing from captured scenario output;
- expected section registration;
- section extraction;
- marker protocol errors;
- scenario assertions;
- automatic framework assertions;
- project-declared assertions;
- assertion evidence;
- assertion status;
- scenario status aggregation;
- normalized section wrappers;
- gold-comparison assertions;
- artifact assertions;
- assertion-type extension.

---

## 3. Non-scope

This document does not define:

- GF shell command semantics;
- the exact GF command used to emit text;
- full `.gfs` authoring conventions;
- project-specific linguistic test cases;
- output-normalization algorithms;
- gold-file update procedures;
- process-launch behavior;
- GF diagnostic parsing;
- the complete persisted `ScenarioResult` schema;
- CLI or GUI presentation.

Those responsibilities belong to:

```text
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/diagnostics/GF_DIAGNOSTIC_PARSING.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
```

---

## 4. Authority boundaries

### 4.1 GF is authoritative for

GF remains authoritative for:

- loading modules;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- GF-native diagnostics;
- GF shell execution.

### 4.2 GF Wordbench is authoritative for

GF Wordbench is authoritative for:

- scenario registration;
- process execution policy;
- raw-output capture;
- marker recognition;
- section extraction;
- completion verification;
- assertion definitions;
- assertion evaluation;
- output normalization;
- gold comparison;
- scenario status;
- assertion reporting.

### 4.3 Active project is authoritative for

The active project defines:

- which scenarios exist;
- which entrypoint each scenario loads;
- which sections are expected;
- which assertions are required;
- which assertions are advisory;
- which gold file applies;
- which scenario modes apply;
- which outputs are linguistically accepted.

### 4.4 Forbidden duplication

GF Wordbench must not implement a second GF interpreter to evaluate scenarios.

Project files must not supply arbitrary Python callbacks for assertions.

Reports must not independently parse markers or reevaluate assertions.

---

## 5. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **SCENARIO**: one registered `.gfs` validation script.
- **SECTION**: a named, ordered region of scenario output.
- **BEGIN MARKER**: line declaring the start of one section.
- **END MARKER**: line declaring the end of one section.
- **MARKER STREAM**: output stream parsed for canonical markers.
- **EXPECTED SECTION**: section declared by the scenario definition.
- **ASSERTION**: typed, machine-verifiable validation criterion.
- **SYSTEM ASSERTION**: mandatory framework assertion applied automatically.
- **PROJECT ASSERTION**: assertion declared by the active project.
- **REQUIRED ASSERTION**: assertion whose failure blocks scenario success.
- **ADVISORY ASSERTION**: assertion whose failure remains visible but does not automatically fail the scenario.
- **RAW OUTPUT**: unmodified captured output from GF.
- **NORMALIZED OUTPUT**: deterministic representation derived from raw output.
- **PROTOCOL ERROR**: structurally invalid marker or assertion contract.
- **VALIDATION FAILURE**: validly evaluated criterion whose expected condition was not met.

---

# 6. Canonical marker protocol

## 6.1 Protocol name

The canonical raw-output marker protocol is:

```text
GF Wordbench Scenario Marker Protocol 1.0
```

The protocol uses two reserved line prefixes:

```text
GF_WORDBENCH_BEGIN
GF_WORDBENCH_END
```

## 6.2 Canonical marker forms

Begin marker:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
```

End marker:

```text
GF_WORDBENCH_END <scenario-id>:<section-id>
```

Example:

```text
GF_WORDBENCH_BEGIN parse:basic-np
GF_WORDBENCH_END parse:basic-np
```

Angle brackets in the grammar are placeholders and are not emitted.

## 6.3 Exact lexical grammar

Canonical marker lines match the following conceptual grammar:

```text
begin-marker = "GF_WORDBENCH_BEGIN" SP scenario-id ":" section-id
end-marker   = "GF_WORDBENCH_END"   SP scenario-id ":" section-id
SP           = one ASCII space
```

Canonical identifiers use:

```text
[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*
```

Examples of valid identifiers:

```text
parse
parse-basic
parse.basic
parse_basic
np-001
missing-linearizations
```

Examples of invalid identifiers:

```text
Parse
parse basic
parse:basic
-parse
parse-
parse/basic
parse\basic
parse é
```

Rules:

- identifiers use lowercase ASCII;
- identifiers contain no whitespace;
- identifiers contain no colon;
- identifiers contain no path separator;
- identifiers do not begin or end with punctuation;
- scenario and section IDs are stable contracts;
- localized names belong in descriptions, not identifiers.

## 6.4 Full-line recognition

A marker is recognized only when the complete output line matches the canonical form.

The parser removes the line terminator and an optional carriage return caused by CRLF normalization.

It does not trim other leading or trailing whitespace before recognition.

These are not markers:

```text
> GF_WORDBENCH_BEGIN parse:basic-np
 GF_WORDBENCH_BEGIN parse:basic-np
GF_WORDBENCH_BEGIN parse:basic-np 
message: GF_WORDBENCH_BEGIN parse:basic-np
```

This prevents GF prompts, echoed commands, diagnostics, or linguistic content containing the reserved words from becoming false control markers.

## 6.5 Canonical marker stream

The canonical marker stream is captured scenario `stdout`.

`stderr` remains raw diagnostic evidence and is not a marker stream.

A GF version or external execution adapter that cannot emit markers to `stdout` requires an explicit external-tool contract change. It must not silently switch marker parsing to a merged stream.

Reasons:

- stdout and stderr must remain separately preserved;
- cross-stream ordering is not reliably reconstructible on every platform;
- diagnostics must not accidentally become control markers;
- marker evaluation must remain deterministic.

## 6.6 Reserved prefix

Any full output line beginning with:

```text
GF_WORDBENCH_
```

is reserved for GF Wordbench control protocol.

An unrecognized reserved line is a protocol error.

Examples:

```text
GF_WORDBENCH_START parse:basic
GF_WORDBENCH_BEGINNING parse:basic
GF_WORDBENCH_ASSERT something
```

Project scenarios must not use the reserved prefix for ordinary linguistic output.

---

# 7. Marker policy

## 7.1 Default policy

The default marker policy is:

```text
required
```

A marker-required scenario declares one or more expected sections.

## 7.2 Marker-free policy

A scenario may explicitly use:

```text
none
```

only when all of the following are true:

- it is process-only or artifact-only;
- it does not use section-scoped assertions;
- it does not use section-based gold comparison;
- another explicit completion criterion exists;
- project validation policy documents why markers are unnecessary.

A marker-free release-significant scenario requires review.

## 7.3 No implicit optional policy

GF Wordbench does not define an implicit “markers optional” mode.

Either:

- markers are required and verified; or
- the scenario explicitly declares a marker-free assertion strategy.

This avoids runs that pass merely because marker detection was not enforced.

---

# 8. Expected section registry

## 8.1 Declaration

Every marker-required scenario must declare its expected sections.

Conceptual example:

```text
scenario_id: parse
sections:
  - basic-np
  - basic-clause
  - ambiguity-check
```

The exact configuration serialization is owned by the scenario-format and project-configuration documents.

## 8.2 Registry rules

Expected section IDs must:

- be unique within the scenario;
- use the canonical identifier grammar;
- have deterministic declaration order;
- represent stable validation responsibilities;
- remain synchronized with the `.gfs` script;
- remain synchronized with normalized output and gold files.

## 8.3 Discovered markers are not registration

The runner must not infer the expected-section registry solely from markers observed at runtime.

Otherwise:

- a misspelled section could become accepted;
- an omitted required section could disappear;
- a script could reduce validation coverage silently.

Observed markers are compared with declared expectations.

## 8.4 Section order

By default, observed sections must follow declared order.

A scenario definition may explicitly declare a different deterministic order policy only when the scenario format supports it.

Release scenarios should use strict declared order.

---

# 9. Section lifecycle

A section has the following conceptual states:

```text
not_started
open
completed
failed
```

## 9.1 Not started

No begin marker has been observed.

## 9.2 Open

The correct begin marker has been observed, but the matching end marker has not.

## 9.3 Completed

The correct begin and matching end markers have been observed in valid order.

## 9.4 Failed

The section violates protocol or fails a required section assertion.

Section state is separate from the scenario’s process state.

---

# 10. Marker invariants

The following invariants are mandatory.

## 10.1 Unique section identity

A section ID may be completed at most once in one scenario execution.

Repeated cases must use distinct stable IDs, for example:

```text
case-001
case-002
case-003
```

## 10.2 Matching pair

Every begin marker must have one matching end marker.

The scenario ID and section ID must match exactly.

## 10.3 No end without begin

An end marker without an open matching section is a protocol error.

## 10.4 No nested sections

Sections must not be nested.

This sequence is invalid:

```text
GF_WORDBENCH_BEGIN parse:first
GF_WORDBENCH_BEGIN parse:second
GF_WORDBENCH_END parse:second
GF_WORDBENCH_END parse:first
```

The protocol intentionally remains flat so parsing and gold projection stay simple and deterministic.

## 10.5 No overlapping sections

A second begin marker while another section is open is a protocol error.

## 10.6 Correct scenario identity

A marker inside scenario `parse` must identify scenario `parse`.

This is invalid during that run:

```text
GF_WORDBENCH_BEGIN linearize:basic
```

## 10.7 Expected section only

A marker for an undeclared section is a protocol error unless a future version explicitly defines dynamic sections.

Protocol 1.0 does not support dynamic sections.

## 10.8 Exact declared order

Sections must appear in expected order under strict order policy.

## 10.9 Complete termination

At process completion:

- no section may remain open;
- every required expected section must be completed;
- all required marker assertions must be evaluable.

## 10.10 Marker identity survives normalization

Normalization may remove the raw marker lines from section bodies, but it must preserve their identity as canonical normalized section wrappers.

---

# 11. Output inside and outside sections

## 11.1 Section body

The section body contains output lines strictly between its begin and end markers.

Raw marker lines are not part of the semantic body.

## 11.2 Preamble

Output before the first begin marker is preamble.

Examples:

- GF banner;
- shell prompt;
- module loading messages;
- startup diagnostics.

Preamble is preserved in raw output.

It is excluded from section gold comparison by default.

## 11.3 Inter-section output

Output between a completed section and the next begin marker is out-of-section output.

It is preserved raw.

It is excluded from section gold comparison by default.

## 11.4 Epilogue

Output after the last end marker is epilogue.

It is preserved raw.

It is excluded from section gold comparison by default.

## 11.5 Global diagnostics

Exclusion from section gold does not mean ignored.

GF Wordbench must still inspect all raw streams for:

- launch and process failure;
- fatal diagnostics;
- unsupported commands;
- incomplete execution;
- security violations;
- output truncation.

## 11.6 Transcript-scoped assertions

A declared transcript-scoped assertion may evaluate normalized or raw out-of-section content when the assertion type explicitly supports it.

Section assertions should remain preferred for linguistic expectations.

---

# 12. Marker parsing algorithm

The canonical parser follows this logical process.

```text
1. Read captured stdout as decoded text.
2. Normalize line endings for parsing only.
3. Iterate lines in original order.
4. Detect exact reserved control lines.
5. Validate marker grammar.
6. Validate scenario identity.
7. Validate expected section identity.
8. Validate declared order.
9. Open or close the current section.
10. Accumulate non-marker lines into the current section body.
11. Preserve all raw lines independently.
12. At end of stream, validate completeness.
13. Produce structured section and protocol results.
```

The parser must not:

- modify raw stdout;
- combine stdout and stderr;
- guess missing markers;
- auto-close an open section;
- infer expected sections from output;
- ignore malformed reserved lines;
- reorder sections;
- treat unknown sections as optional;
- repair mismatched IDs.

---

# 13. Marker protocol conditions

Canonical protocol conditions include:

```text
ok
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
decode_error
output_truncated
```

## 13.1 Validation failure conditions

The following normally produce scenario status `FAIL` when the protocol itself was interpretable:

- required expected section never began;
- required expected section did not complete;
- required section-completion assertion failed.

Recommended technical error kind:

```text
SCRIPT
```

## 13.2 Protocol error conditions

The following normally produce scenario status `ERROR`:

- malformed reserved marker line;
- end marker without begin;
- mismatched end marker;
- nested begin marker;
- duplicate completed section;
- wrong scenario ID;
- unexpected section under strict protocol;
- parser decode failure preventing reliable interpretation;
- truncated output preventing reliable completion evaluation.

Recommended technical error kind:

```text
SCRIPT
```

or a more specific approved contract kind when the shared model defines one.

## 13.3 No pass on ambiguity

If GF Wordbench cannot determine whether required sections completed, the scenario must not be `OK`.

---

# 14. Marker result model

Each expected section should produce a structured result containing at least:

```text
section_id
status
completed
begin_line
end_line
body_line_count
protocol_condition
primary_message
```

Recommended optional fields:

```text
raw_body_path
normalized_body_path
body_hash
assertion_ids
```

Rules:

- line numbers refer to the decoded marker stream;
- absent begin or end locations use `null`;
- `completed = true` requires a valid matching pair;
- body hash uses the canonical normalized body when present;
- assertion IDs remain deterministically ordered.

The exact persisted representation is owned by `docs/PERSISTED_SCHEMA_LOCK.md`.

No new serialized field may be emitted until that schema lock defines it or explicitly permits it.

---

# 15. Raw-to-normalized section mapping

## 15.1 Raw marker input

Example raw stdout:

```text
GF banner or prompt
GF_WORDBENCH_BEGIN parse:basic-np
PredVP (DetCN (DetQuant DefArt NumSg) (UseN house_N)) (UseV sleep_V)
GF_WORDBENCH_END parse:basic-np
GF_WORDBENCH_BEGIN parse:ambiguity-check
2
GF_WORDBENCH_END parse:ambiguity-check
```

## 15.2 Canonical normalized output

The normalized scenario artifact uses the persisted text schema:

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: parse
# normalization_version: 1.0
--- BEGIN basic-np ---
PredVP (DetCN (DetQuant DefArt NumSg) (UseN house_N)) (UseV sleep_V)
--- END basic-np ---
--- BEGIN ambiguity-check ---
2
--- END ambiguity-check ---
```

## 15.3 Mapping rules

- raw `GF_WORDBENCH_BEGIN` and `GF_WORDBENCH_END` lines remain in raw stdout;
- normalized output does not copy raw control lines as semantic body;
- normalized wrappers preserve section identity;
- normalized section order matches declared scenario order;
- normalized wrappers are not reinterpreted as raw markers;
- scenario ID appears in the normalized header;
- normalization version is explicit;
- incomplete sections cannot produce a valid canonical normalized output.

## 15.4 Gold mapping

A gold file uses equivalent normalized section wrappers:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: parse
# normalization_version: 1.0
--- BEGIN basic-np ---
<expected normalized body>
--- END basic-np ---
```

Raw marker syntax and normalized wrapper syntax are separate contracts.

They must not be conflated.

---

# 16. Assertion model

## 16.1 Definition

An assertion is a typed rule evaluated against structured process evidence, marker results, normalized output, gold comparison, registered metrics, or produced artifacts.

## 16.2 Common assertion fields

Every assertion definition must identify:

```text
assertion_id
assertion_type
required
source
scope
target
expected condition
failure message
```

Optional type-specific fields may include:

```text
expected_value
allowed_values
minimum
maximum
literal
count
artifact_role
metric_id
comparison_strategy
```

The exact configuration serialization is owned by:

```text
docs/scenarios/SCENARIO_FORMAT.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/PERSISTED_SCHEMA_LOCK.md
```

## 16.3 Assertion identifier

Assertion IDs use the canonical identifier grammar.

Recommended examples:

```text
process-completed
exit-zero
basic-np-completed
basic-np-nonempty
no-missing-linearizations
gold-match
pgf-exists
parse-count-bounded
```

Assertion IDs must be unique within one scenario definition.

## 16.4 Assertion requiredness

Each assertion is either:

```text
required
advisory
```

A required assertion affects scenario status.

An advisory assertion:

- is still evaluated;
- remains visible;
- may generate warnings;
- does not automatically fail the scenario;
- may be escalated only by explicit mode or release policy.

## 16.5 Assertion sources

Canonical source families:

```text
process
stdout
stderr
transcript
section
normalized_output
gold
artifact
metric
```

An assertion type must define which sources it accepts.

## 16.6 Assertion scopes

Canonical scopes:

```text
scenario
section
artifact
metric
```

A section-scoped assertion must name one declared section.

An artifact-scoped assertion must name a registered artifact role or path identity.

A metric-scoped assertion must name a registered metric producer.

---

# 17. Assertion result model

Each evaluated assertion should produce:

```text
assertion_id
assertion_type
status
required
source
scope
target
expected
actual
primary_message
evidence_reference
```

Canonical assertion statuses use the shared validation vocabulary:

```text
OK
FAIL
ERROR
SKIPPED
```

## 17.1 Assertion `OK`

The assertion was evaluated and its criterion passed.

## 17.2 Assertion `FAIL`

The assertion was evaluated correctly, but the expected condition was not met.

## 17.3 Assertion `ERROR`

The assertion could not be evaluated reliably because of:

- invalid assertion configuration;
- unknown assertion type;
- incompatible source;
- missing required evidence caused by protocol error;
- malformed expected value;
- metric extraction failure;
- internal evaluation failure.

## 17.4 Assertion `SKIPPED`

The assertion was intentionally not evaluated under explicit policy.

A required assertion must not be silently skipped.

## 17.5 Persistence rule

Assertion results belong to the structured `ScenarioResult`.

Their exact serialized field layout must be defined in `docs/PERSISTED_SCHEMA_LOCK.md` before canonical JSON emission.

Reports may not invent an incompatible private assertion schema.

---

# 18. Automatic system assertions

GF Wordbench applies system assertions independently of project-declared assertions.

Recommended stable system assertions are listed below.

## 18.1 Process started

```text
assertion_id: sys-process-started
```

Passes when the external process launched.

Launch failure produces assertion `ERROR`.

## 18.2 Process completed

```text
assertion_id: sys-process-completed
```

Passes when execution reached a terminal state that permits interpretation.

Timeout, uncontrolled cancellation, or launch failure does not pass.

## 18.3 Exit code allowed

```text
assertion_id: sys-exit-code-allowed
```

Default allowed exit code:

```text
0
```

A scenario-specific non-zero allowance requires an explicit scenario contract and must not conceal fatal diagnostics.

## 18.4 Protocol valid

```text
assertion_id: sys-marker-protocol-valid
```

Passes when:

- all reserved lines are valid;
- no forbidden nesting exists;
- IDs match;
- order is valid;
- no duplicate or unexpected section exists.

## 18.5 Expected sections complete

```text
assertion_id: sys-sections-complete
```

Passes when every required expected section has a valid begin/end pair.

## 18.6 No fatal diagnostic

```text
assertion_id: sys-no-fatal-diagnostic
```

Passes when diagnostic interpretation finds no fatal GF, process, or script error that invalidates the scenario.

A zero exit code does not override this assertion.

## 18.7 Required gold matched

```text
assertion_id: sys-gold-match
```

Applied when the scenario requires gold comparison.

A missing required gold file does not pass.

## 18.8 Required artifacts exist

```text
assertion_id: sys-required-artifacts
```

Applied when the scenario declares required artifacts.

Process success without the artifact does not pass.

## 18.9 System assertion immutability

The active project must not disable mandatory safety and integrity assertions.

Project configuration may strengthen them.

It must not weaken:

- launch evidence;
- timeout evidence;
- protocol validity;
- required section completion;
- required artifact existence;
- required gold comparison.

---

# 19. Built-in project assertion types

## 19.1 `marker_present`

**Purpose**

Verify that one exact expected marker was observed.

**Source**

```text
section
```

**Parameters**

```text
section_id
marker_kind: begin | end
```

**Pass**

The exact declared marker was observed once in valid protocol context.

**Failure**

The marker is absent.

This type does not override broader protocol validation.

---

## 19.2 `section_completed`

**Purpose**

Verify that a declared section completed.

**Source**

```text
section
```

**Parameters**

```text
section_id
```

**Pass**

The section has one valid begin/end pair.

**Failure**

The expected section did not complete.

---

## 19.3 `section_empty`

**Purpose**

Verify that a normalized section body contains no semantic output.

**Source**

```text
section
```

**Parameters**

```text
section_id
```

**Pass**

The normalized body is empty according to the scenario normalization profile.

**Typical use**

- missing-linearization output expected to be empty;
- absence of diagnostic items;
- no unresolved entries.

Whitespace semantics are owned by the normalization profile.

---

## 19.4 `section_nonempty`

**Purpose**

Verify that a normalized section body contains semantic output.

**Source**

```text
section
```

**Parameters**

```text
section_id
```

**Pass**

At least one semantic line or code point remains after normalization.

This assertion does not establish linguistic correctness by itself.

---

## 19.5 `contains`

**Purpose**

Verify that a stable literal occurs.

**Accepted sources**

```text
section
normalized_output
transcript
stdout
stderr
```

**Parameters**

```text
literal
occurrence policy
```

**Default semantics**

- literal Unicode comparison;
- case-sensitive;
- exact code-point sequence after the selected source normalization;
- at least one occurrence.

Case-insensitive behavior requires explicit declaration.

The assertion definition must identify whether matching occurs before or after normalization.

---

## 19.6 `not_contains`

**Purpose**

Verify that a forbidden stable literal does not occur.

**Accepted sources**

```text
section
normalized_output
transcript
stdout
stderr
```

**Parameters**

```text
literal
```

**Typical use**

- forbidden placeholder;
- unimplemented marker;
- known runtime failure token;
- prohibited empty linearization representation.

This assertion must not replace the global fatal-diagnostic parser.

---

## 19.7 `equals`

**Purpose**

Verify exact equality with a declared expected value.

**Accepted sources**

```text
section
normalized_output
metric
```

**Parameters**

```text
expected_value
```

For multiline scenario output, gold comparison should normally be preferred.

---

## 19.8 `line_count`

**Purpose**

Verify normalized line count.

**Source**

```text
section
```

**Parameters**

One or more of:

```text
exact
minimum
maximum
```

Blank-line treatment is defined by the normalization profile.

At least one bound is required.

---

## 19.9 `occurrence_count`

**Purpose**

Count a stable literal in one source.

**Accepted sources**

```text
section
normalized_output
transcript
```

**Parameters**

```text
literal
exact | minimum | maximum
```

This assertion is literal-based.

It must not use undocumented regular-expression semantics.

---

## 19.10 `exit_code_in`

**Purpose**

Verify the actual process exit code against an explicit allowed set.

**Source**

```text
process
```

**Parameters**

```text
allowed_values
```

An empty allowed set is invalid configuration.

This assertion is necessary evidence but never sufficient evidence for scenario success.

---

## 19.11 `no_fatal_diagnostic`

**Purpose**

Require the structured diagnostic layer to report no fatal condition.

**Sources**

```text
stdout
stderr
process
```

**Pass**

No fatal diagnostic is present under the supported GF-version parser.

The assertion must not rely on one raw substring alone when structured diagnostic parsing exists.

---

## 19.12 `gold_match`

**Purpose**

Require normalized scenario output to match its reviewed gold expectation.

**Source**

```text
gold
```

**Parameters**

```text
comparison_strategy
gold_path
```

**Pass**

The declared comparison strategy reports a match.

**Failure**

- mismatch;
- missing required gold;
- incompatible normalization version;
- invalid gold format.

Invalid gold format may be `ERROR` rather than `FAIL`.

---

## 19.13 `artifact_exists`

**Purpose**

Require a registered artifact to exist after scenario execution.

**Source**

```text
artifact
```

**Parameters**

```text
artifact_role or registered artifact identity
```

Path lookup uses the artifact model.

Project text must not supply an unchecked arbitrary path.

---

## 19.14 `artifact_nonempty`

**Purpose**

Require an artifact to exist and contain at least one byte.

**Source**

```text
artifact
```

This assertion does not prove semantic artifact validity.

A PGF or other structured artifact may require stronger type-specific validation.

---

## 19.15 `metric_compare`

**Purpose**

Compare a registered structured metric.

**Source**

```text
metric
```

**Parameters**

```text
metric_id
operator
expected_value
```

Canonical numeric operators:

```text
eq
ne
lt
le
gt
ge
between
```

Examples:

- parse count is at least one;
- ambiguity count is no more than a declared bound;
- missing-function count equals zero;
- generated tree count lies within a bounded range.

A metric must be produced by a registered framework extractor or scenario-type adapter.

Project configuration must not define arbitrary Python extraction code.

---

# 20. Assertions not included in protocol 1.0

Protocol 1.0 does not define a general-purpose assertion language.

The following are intentionally excluded:

- arbitrary Python expressions;
- JavaScript expressions;
- shell commands;
- dynamically imported predicates;
- unrestricted regular expressions as the default comparison mechanism;
- XPath, JSONPath, or query languages without a real structured-output requirement;
- assertions embedded in human Markdown;
- implicit magic comments;
- assertions inferred from scenario filenames;
- fuzzy linguistic similarity;
- AI-generated pass/fail judgment;
- automatic gold acceptance.

A future assertion type must follow the extension process in this document.

---

# 21. Assertion evaluation sources

## 21.1 Raw sources

Raw sources include:

```text
stdout
stderr
transcript
```

Raw assertions are appropriate for:

- process banners;
- known diagnostic presence;
- exact control evidence;
- debugging.

They are less portable across GF versions and platforms.

## 21.2 Normalized sources

Normalized sources include:

```text
section
normalized_output
```

They are preferred for stable semantic validation and gold comparison.

## 21.3 Structured sources

Structured sources include:

```text
process
artifact
metric
gold
```

They are preferred when the condition is already represented as typed data.

An assertion should not parse text to recover a value already available structurally.

---

# 22. Assertion evaluation order

Assertions are evaluated in deterministic phases.

```text
1. Configuration assertions
2. Process launch and completion assertions
3. Marker protocol assertions
4. Section completion assertions
5. Diagnostic assertions
6. Normalization
7. Section-content assertions
8. Metric assertions
9. Gold assertions
10. Artifact assertions
11. Scenario aggregation
```

## 22.1 Dependency-aware skipping

An assertion may be `SKIPPED` only when a prerequisite made evaluation impossible and policy explicitly permits a skip result.

Examples:

- section-content assertion skipped because marker protocol was invalid;
- gold assertion skipped because canonical normalized output could not be produced;
- artifact semantic assertion skipped because artifact did not exist.

A required skipped assertion normally contributes to scenario `ERROR`.

## 22.2 No contradictory override

A later assertion cannot override an earlier fatal failure.

Examples:

- gold match cannot override a process timeout;
- artifact existence cannot override malformed marker protocol;
- expected token presence cannot override a fatal GF diagnostic;
- exit code `0` cannot override a missing required section.

---

# 23. Requiredness and severity

## 23.1 Required assertion

A required assertion with status:

- `FAIL` makes scenario status at least `FAIL`;
- `ERROR` makes scenario status `ERROR`;
- `SKIPPED` makes scenario status `ERROR` unless an explicit stage policy maps it differently;
- `OK` contributes no failure.

## 23.2 Advisory assertion

An advisory assertion with status:

- `FAIL` produces a visible warning;
- `ERROR` remains visible and may escalate under strict or release policy;
- `SKIPPED` remains visible;
- `OK` contributes no warning.

## 23.3 Release policy

Release policy may escalate a named advisory assertion to required.

It must do so explicitly and deterministically.

Disposable UI state may not change assertion requiredness for release mode.

---

# 24. Scenario status aggregation

Canonical scenario statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

## 24.1 Scenario `OK`

A scenario is `OK` only when:

- it was selected and executed;
- process execution is interpretable;
- mandatory system assertions pass;
- marker policy is satisfied;
- every required project assertion passes;
- required gold comparison passes;
- required artifacts exist;
- no fatal diagnostic invalidates the result.

Advisory warnings may coexist with `OK` when policy permits.

## 24.2 Scenario `FAIL`

A scenario is `FAIL` when execution was interpretable but one or more required validation criteria were not met.

Examples:

- required section missing;
- expected section output not empty;
- forbidden token present;
- metric outside expected range;
- gold mismatch;
- required artifact absent after otherwise completed execution;
- GF reports a project-level validation failure.

## 24.3 Scenario `ERROR`

A scenario is `ERROR` when the contract could not be executed or interpreted reliably.

Examples:

- process launch failure;
- timeout under scenario error policy;
- malformed marker protocol;
- unknown assertion type;
- invalid assertion configuration;
- output decode failure;
- output truncation prevents reliable evaluation;
- normalized output cannot be constructed;
- gold file format is invalid;
- internal assertion evaluator failure.

## 24.4 Scenario `SKIPPED`

A scenario is `SKIPPED` only when it was intentionally not executed under explicit mode or project policy.

A required scenario that is skipped without an approved policy must cause run failure or error.

## 24.5 Aggregation precedence

Recommended precedence:

```text
ERROR > FAIL > OK
```

`SKIPPED` is not an aggregation success state for required work.

---

# 25. Failure messages

Every failed or errored assertion must provide a concise primary message.

Recommended structure:

```text
<assertion-id>: expected <condition>; observed <actual>
```

Examples:

```text
basic-np-completed: expected completed section; observed missing end marker
no-missing-linearizations: expected empty section; observed 3 lines
parse-count-bounded: expected value <= 2; observed 4
gold-match: expected exact normalized match; observed mismatch in section basic-clause
pgf-exists: expected artifact role release-pgf; artifact not found
```

Messages must not:

- claim unsupported linguistic diagnosis;
- discard raw evidence;
- expose secrets;
- include unbounded output;
- replace structured expected and actual fields.

---

# 26. Assertion evidence

## 26.1 Evidence reference

An assertion result should reference one or more of:

```text
stdout path
stderr path
raw transcript path
normalized output path
section ID
gold path
gold diff path
artifact path
metric record
process result
```

## 26.2 Evidence excerpt

A human-facing excerpt may be stored or rendered when useful.

Excerpts must be:

- bounded;
- line-attributed where possible;
- derived from preserved evidence;
- escaped safely for Markdown or UI;
- clearly marked as raw or normalized.

## 26.3 No evidence destruction

Assertion evaluation must not modify its evidence source.

## 26.4 Traceability

For every release-significant assertion, a reviewer should be able to trace:

```text
assertion definition
→ evaluated source
→ actual value
→ assertion result
→ scenario status
→ run status
```

---

# 27. Marker and assertion configuration validation

Before launching GF, GF Wordbench should validate:

- scenario ID grammar;
- unique scenario ID;
- marker policy;
- expected section ID grammar;
- unique expected sections;
- deterministic section order;
- assertion ID grammar;
- unique assertion IDs;
- known assertion types;
- required common fields;
- valid source/type combination;
- valid scope;
- valid target section;
- valid artifact role;
- valid metric ID;
- valid numeric bounds;
- required gold path;
- normalization version;
- mode applicability.

Invalid configuration should fail before scenario execution when possible.

---

# 28. Scenario examples

## 28.1 Complete marker-backed scenario

Declared contract:

```text
scenario_id: linearize
marker_policy: required
expected_sections:
  - noun-phrase
  - clause
required_assertions:
  - noun-phrase-completed
  - noun-phrase-nonempty
  - clause-completed
  - clause-nonempty
  - gold-match
```

Observed raw marker stream:

```text
GF_WORDBENCH_BEGIN linearize:noun-phrase
the house
GF_WORDBENCH_END linearize:noun-phrase
GF_WORDBENCH_BEGIN linearize:clause
the house sleeps
GF_WORDBENCH_END linearize:clause
```

Result:

```text
marker protocol: OK
required sections: OK
content assertions: OK
gold assertion: OK
scenario status: OK
```

## 28.2 Missing end marker

Observed:

```text
GF_WORDBENCH_BEGIN parse:basic
PredVP ...
```

Result:

```text
section basic: incomplete
protocol condition: open_section_at_eof
required completion assertion: FAIL
scenario status: FAIL or ERROR according to protocol interpretation policy
```

For the canonical policy in this document:

- an otherwise valid expected section missing only its end marker is `FAIL`;
- malformed or contradictory protocol structure is `ERROR`.

## 28.3 Nested marker

Observed:

```text
GF_WORDBENCH_BEGIN parse:first
GF_WORDBENCH_BEGIN parse:second
```

Result:

```text
protocol condition: nested_begin
system protocol assertion: ERROR
dependent section assertions: SKIPPED
scenario status: ERROR
```

## 28.4 Zero exit with missing section

Observed:

```text
exit_code: 0
expected section: missing-functions
observed section: absent
```

Result:

```text
sys-exit-code-allowed: OK
sys-sections-complete: FAIL
scenario status: FAIL
```

Exit code does not override missing completion evidence.

## 28.5 Gold mismatch

Observed:

```text
process: completed
markers: complete
normalization: valid
gold comparison: mismatch
```

Result:

```text
sys-gold-match: FAIL
scenario status: FAIL
```

## 28.6 Marker-free artifact scenario

Declared:

```text
marker_policy: none
required assertion:
  artifact_exists(release-pgf)
```

Allowed only when the project contract explicitly defines artifact existence as sufficient completion evidence for that scenario.

---

# 29. Repeated and generated cases

## 29.1 Stable case IDs

Repeated examples should use stable case-specific section IDs:

```text
case-001
case-002
case-003
```

## 29.2 No dynamic ID from output

Section IDs must not be generated from:

- linearized text;
- timestamps;
- random numbers;
- source paths;
- parse trees;
- platform values.

## 29.3 Generated scenarios

Generated or bounded-generation scenarios must:

- use deterministic case identities;
- record generation limits;
- avoid exact gold on unstable random output;
- assert bounded counts or stable projections;
- preserve generated trees and outputs when release-significant.

## 29.4 Large inventories

A scenario with many cases may group them in one section and use metrics or gold comparison.

It should not create thousands of marker sections unless individual case identity is required for diagnosis.

---

# 30. Output truncation

## 30.1 Truncation policy

If process output is truncated because of configured evidence limits:

- truncation must be explicit;
- original byte or line counts should be recorded when known;
- marker parsing must report whether required control lines may have been lost;
- affected assertions must not pass without sufficient evidence.

## 30.2 Truncated marker stream

When truncation may have removed markers or section content:

```text
protocol condition: output_truncated
scenario status: ERROR
```

unless every required assertion can still be proven from independent structured evidence.

## 30.3 Bounded excerpts versus raw capture

Report excerpt limits are not raw-capture truncation.

Reports may show bounded excerpts while complete raw evidence remains stored.

---

# 31. Encoding and Unicode

Scenario marker lines use ASCII.

Scenario bodies may use full Unicode.

Rules:

- `.gfs` files use the framework’s documented UTF-8 policy;
- stdout and stderr decoding follows the external-tool contract;
- Unicode decoding errors remain explicit;
- normalizers must preserve language-relevant distinctions;
- assertion literals are interpreted as Unicode;
- case-insensitive comparison must define its Unicode policy;
- reports must preserve or safely escape Unicode;
- marker recognition is unaffected by localized linguistic output.

A decoding strategy must not silently delete bytes that could contain marker or assertion evidence.

---

# 32. Security requirements

`.gfs` files are executable inputs.

Marker and assertion processing must therefore enforce:

- no arbitrary Python callbacks;
- no shell commands as assertions;
- no unchecked project path access;
- no path traversal in artifact assertions;
- no secret interpolation into expected values;
- no environment dump assertions;
- no automatic external command execution;
- bounded output and metric extraction;
- safe rendering of assertion evidence;
- explicit authorization for any GF shell escape capability.

Literal assertions against untrusted content must not become command input.

---

# 33. Performance requirements

Marker parsing and built-in assertions should be linear or predictably bounded relative to captured output.

Requirements:

- one ordered pass should parse markers;
- section bodies should not be copied repeatedly without need;
- occurrence counting should be bounded by output size;
- metric extractors should declare complexity;
- pathological pattern matching is prohibited;
- report excerpts should be produced from stored references when practical;
- assertion evaluation must respect overall scenario timeout and resource policy.

A costly assertion type requires documented justification and tests.

---

# 34. Assertion-type extension

A new assertion type is permitted only when existing types cannot express a stable required criterion.

Every new assertion type must define:

```text
assertion_type
owner
purpose
accepted sources
accepted scopes
required parameters
comparison semantics
normalization assumptions
OK condition
FAIL condition
ERROR condition
SKIPPED condition
evidence fields
serialization
report rendering
security considerations
complexity
unit tests
contract tests
integration tests
```

Extension rules:

- stable type ID;
- duplicate type rejection;
- deterministic evaluation;
- no project Python;
- no import-side-effect registration;
- unknown type never passes;
- persisted-schema review;
- documentation update;
- compatibility classification;
- relevant lock update.

A generic plugin API must not be introduced for one assertion type.

---

# 35. Versioning and compatibility

## 35.1 Protocol version

Marker protocol version changes when raw marker syntax or parsing semantics change.

## 35.2 Compatible change

Examples:

- new optional assertion type;
- new optional result metadata;
- clearer failure message;
- additional protocol diagnostic that preserves existing meaning.

## 35.3 Breaking change

Examples:

- marker prefix change;
- identifier grammar change;
- nesting support;
- marker stream change;
- section-order semantic change;
- required assertion behavior change;
- assertion status semantic change;
- normalized wrapper change;
- persisted assertion-field change without migration.

Breaking changes require:

1. protocol version update;
2. scenario review;
3. gold review where affected;
4. parser update;
5. schema update;
6. compatibility or migration policy;
7. contract tests;
8. release-note entry.

## 35.4 Legacy marker support

A legacy marker syntax may be read only through an explicit compatibility adapter.

Canonical writers and templates emit only the current syntax.

Legacy and current markers must not be mixed in one scenario execution.

---

# 36. Testing requirements

Recommended test files:

```text
tests/scenarios/test_marker_parser.py
tests/scenarios/test_section_extraction.py
tests/scenarios/test_assertion_definitions.py
tests/scenarios/test_assertion_evaluation.py
tests/scenarios/test_scenario_aggregation.py
tests/contracts/test_scenario_marker_contract.py
tests/contracts/test_scenario_assertion_contract.py
tests/integration/test_gf_scenario_markers.py
```

## 36.1 Marker parser unit tests

Required cases:

```text
valid single section
valid multiple sections
CRLF input
Unicode section body
prompt-prefixed non-marker
leading-space non-marker
trailing-space non-marker
malformed reserved line
wrong scenario ID
unknown section ID
out-of-order section
end without begin
mismatched end
nested begin
duplicate section
missing begin
missing end
open section at EOF
output truncation
decode error
```

## 36.2 Assertion unit tests

Required cases:

```text
known assertion type
unknown assertion type
duplicate assertion ID
invalid source/type pair
required OK
required FAIL
required ERROR
required SKIPPED
advisory FAIL
literal contains
literal not_contains
empty section
nonempty section
line count bounds
occurrence count bounds
exit code allowed
fatal diagnostic
gold match
gold mismatch
missing gold
artifact exists
artifact missing
metric comparison
missing metric
```

## 36.3 Aggregation tests

Required cases:

```text
all required assertions OK
advisory warning only
one required FAIL
one required ERROR
required assertion skipped
zero exit plus missing marker
gold match plus timeout
artifact exists plus protocol error
multiple failures with deterministic primary message
```

## 36.4 Integration tests with real GF

A small fixture grammar should verify:

- marker emission reaches stdout;
- prompt echo does not create false markers;
- loading scenario completes markers;
- parse scenario extracts sections;
- linearization Unicode is preserved;
- non-zero process failure is captured;
- zero exit with incomplete script does not pass;
- normalized output uses canonical wrappers;
- gold comparison uses normalized sections;
- raw stdout retains original markers.

Tests requiring GF must be marked separately from pure unit tests.

---

# 37. Contract checks

A future command should validate scenario contracts before execution:

```text
gf-wordbench scenarios check
```

Recommended checks:

- registered scenario file exists;
- scenario ID matches filename policy;
- expected sections are unique;
- assertion IDs are unique;
- assertion types are known;
- assertion sources and scopes are valid;
- referenced section exists;
- required gold exists;
- normalization version is known;
- artifact roles are registered;
- metrics are registered;
- marker prefixes in scripts use current protocol where statically detectable;
- old language identifiers are absent;
- normal scenarios contain no prohibited shell escape.

Strict mode:

```text
gf-wordbench scenarios check --strict
```

Strict mode may additionally reject:

- undeclared scenario files;
- unused gold files;
- advisory assertions in release scenarios without rationale;
- out-of-date protocol versions;
- deprecated assertion types;
- unbounded generation patterns;
- ambiguous marker emission constructs.

---

# 38. Anti-drift indicators

Scenario marker or assertion drift is probable when:

- a scenario emits an undocumented marker prefix;
- scenario and section IDs use different spelling across configuration and output;
- a begin marker has no matching end marker;
- marker lines are parsed from merged stdout/stderr;
- a marker is recognized after arbitrary whitespace trimming;
- expected sections are inferred only from observed output;
- a new section appears without project validation review;
- a required section disappears but the scenario still passes;
- markers are removed during normalization without preserved section identity;
- raw marker syntax appears directly in gold body;
- normalized wrapper syntax is parsed as raw protocol;
- exit code `0` is treated as complete success;
- an assertion reads Markdown instead of structured evidence;
- an unknown assertion type passes;
- project configuration points to a Python callback;
- two assertion types use the same ID with different meaning;
- assertion order depends on mapping iteration;
- assertion failure has no evidence reference;
- a required assertion is silently skipped;
- a report reevaluates assertions;
- gold comparison occurs before normalization;
- normal validation rewrites gold;
- output truncation is hidden;
- assertion results are serialized without schema ownership;
- a new metric is extracted through undocumented text scraping;
- linguistic output is normalized away to make an assertion pass.

Each drift indicator requires restoration of the current contract or a coordinated versioned change.

---

# 39. Review checklist

Use this checklist for every scenario-marker or assertion change.

```text
[ ] Scenario ID is stable
[ ] Marker policy is explicit
[ ] Expected sections are declared
[ ] Section IDs are valid and unique
[ ] Raw marker syntax is canonical
[ ] Marker stream remains stdout
[ ] No nesting is introduced
[ ] Section order is deterministic
[ ] Required assertions are declared
[ ] Advisory assertions are justified
[ ] Assertion IDs are unique
[ ] Assertion types are known
[ ] Source and scope are valid
[ ] Expected values are explicit
[ ] Process success is necessary but not sufficient
[ ] Fatal diagnostics remain visible
[ ] Raw output is preserved
[ ] Normalization preserves section identity
[ ] Gold comparison follows normalization
[ ] Required artifacts are verified
[ ] Assertion evidence is traceable
[ ] Status aggregation is correct
[ ] Output truncation is handled
[ ] Security impact is reviewed
[ ] Persisted-schema impact is reviewed
[ ] Unit tests are updated
[ ] Contract tests are updated
[ ] Real-GF integration tests are updated where needed
[ ] Gold files are reviewed deliberately
[ ] Project validation specification is updated
[ ] Relevant lock files are updated
```

---

# 40. Documentation ownership

This document owns:

- raw marker syntax;
- marker parsing semantics;
- section lifecycle;
- assertion-type semantics;
- assertion status;
- scenario aggregation rules related to assertions.

Other documents own:

| Topic | Owner |
|---|---|
| Complete scenario file structure | `SCENARIO_FORMAT.md` |
| Practical `.gfs` authoring | `WRITING_GFS_SCENARIOS.md` |
| Output normalization algorithm | `OUTPUT_NORMALIZATION.md` |
| Gold comparison policy | `GOLDEN_TESTS.md` |
| Gold update workflow | `UPDATING_GOLD_FILES.md` |
| Scenario pipeline integration | `docs/validation/SCENARIO_VALIDATION.md` |
| GF process contract | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persistent output schema | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Active project scenario registry | `project/docs/VALIDATION_SPEC.md` |
| Project interfile contracts | `project/docs/INTERFILE_CONTRACT_LOCK.md` |

A downstream document should link to these rules rather than redefine marker or assertion semantics.

---

# 41. Canonical protocol summary

Raw begin marker:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
```

Raw end marker:

```text
GF_WORDBENCH_END <scenario-id>:<section-id>
```

Canonical properties:

```text
marker stream: stdout
matching: exact full line
identifier case: lowercase ASCII
nesting: prohibited
duplicate sections: prohibited
dynamic sections: prohibited
declared order: required
missing required section: FAIL
malformed protocol: ERROR
raw output: immutable
normalization: after raw capture
gold comparison: after normalization
unknown assertion type: ERROR
normal gold update: prohibited
```

---

# 42. Final enforcement rule

Markers prove execution structure.

Assertions prove declared validation criteria.

Neither replaces GF semantics, raw evidence, project contracts, or reviewed gold expectations.

Therefore:

> A scenario may be reported as successful only when its process evidence is interpretable, its marker protocol is valid, every required section completes, every required assertion passes, and every required gold or artifact contract is satisfied.
