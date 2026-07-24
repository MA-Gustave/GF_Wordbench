# GF Wordbench — GF Diagnostic Parsing

**Document ID:** `GF-WB-DIAG-GF-PARSING`  
**Status:** Normative diagnostic specification  
**Applies to:** GF compilation, PGF construction, native `.gfs` scenarios, introspection and supported GF operations for one active project and one run  
**Owner:** GF Wordbench maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Diagnostic authority:** `docs/diagnostics/ERROR_CLASSIFICATION.md`, `docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md`  
**External-tool authority:** `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Persisted-result authority:** `docs/PERSISTED_SCHEMA_LOCK.md`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

Grammatical Framework may emit diagnostics on standard output, standard error or both. Diagnostic wording and layout may vary by:

- GF version;
- operation;
- platform;
- path format;
- compiler phase;
- shell command;
- multiline context;
- whether the process was launched in batch or shell mode.

GF Wordbench must preserve this evidence while extracting enough structure to support:

- file and scenario results;
- deterministic primary error selection;
- stable error kinds;
- top-error aggregation;
- human-readable reports;
- AI-ready evidence;
- regression comparison;
- direct/downstream classification by a separate component;
- GF-version compatibility analysis.

This document defines the canonical diagnostic-parsing model.

The core rule is:

> Diagnostic parsing may structure GF evidence, but it must never replace, hide or overstate the evidence GF actually emitted.

A parser match is evidence about diagnostic form. It is not proof of causal ownership.

---

## 2. Scope

This specification governs parsing of diagnostics from:

- per-file GF compilation;
- PGF construction;
- GF grammar import and load;
- `.gfs` scenario execution;
- parsing;
- linearization;
- generation;
- morphology;
- missing-function inspection;
- supported grammar introspection;
- GF startup and runtime failures emitted after launch;
- stdout and stderr text captured from GF.

It governs:

- input requirements;
- text preparation;
- stream handling;
- diagnostic records;
- multiline grouping;
- pattern registry behavior;
- source-location extraction;
- severity extraction;
- error-kind mapping;
- primary diagnostic selection;
- duplicate handling;
- unknown diagnostic retention;
- truncation behavior;
- compatibility;
- security;
- tests and fixtures.

It does not govern:

- process launching;
- timeout enforcement;
- cancellation;
- filesystem errors outside GF;
- configuration validation;
- source-code static scanning;
- direct/downstream classification;
- release-gate decisions;
- report formatting;
- output normalization for gold comparison;
- GF's internal diagnostic machinery.

---

## Product and run boundary

One GF Wordbench run parses diagnostics for exactly one active GF language project and one normative language target.

Diagnostic parsing must not:

- combine evidence from several active projects into one result;
- discover projects through a Portfolio registry;
- assign portfolio-wide readiness or cross-workspace status;
- depend on `gf-portfolio` code, schemas, storage, configuration or runtime.

`gf-portfolio` may consume finalized public Wordbench artifacts. It does not participate in raw evidence capture, diagnostic parsing, causal classification or result construction.

---

## 3. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless an explicit exception is documented.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **RAW STREAM**: immutable stdout or stderr captured from a GF process.
- **PARSE VIEW**: derived text prepared for diagnostic recognition without modifying raw evidence.
- **DIAGNOSTIC RECORD**: structured representation of one recognized or retained diagnostic unit.
- **PATTERN**: versioned recognition rule for a known GF output form.
- **MATCH**: successful application of a pattern to evidence.
- **UNKNOWN DIAGNOSTIC**: suspicious or failure-associated output not safely mapped to a known pattern.
- **PRIMARY DIAGNOSTIC**: deterministic diagnostic selected for compact summaries.
- **CONTINUATION LINE**: line belonging to a preceding diagnostic.
- **SEVERITY**: diagnostic importance such as warning, error or fatal.
- **ERROR KIND**: stable GF Wordbench category such as `TYPE` or `SYNTAX`.
- **DIAGNOSTIC CLASS**: causal relation such as `direct` or `downstream`; not assigned by this parser.
- **PROVENANCE**: stream, line range, raw path and pattern information linking a record to evidence.
- **CONFIDENCE**: parser confidence in pattern interpretation, not confidence that a file is the root cause.
- **STRICT MODE**: mode that reports unsupported or ambiguous parsing conditions as contract errors where policy requires.

---

## 4. Authority boundaries

## 4.1 GF is authoritative for

- the diagnostic text it emits;
- GF syntax and type semantics;
- source references;
- module references;
- compiler and runtime failures;
- warnings;
- internal errors.

## 4.2 External-tool adapter is authoritative for

- whether the process launched;
- executable and arguments;
- working directory;
- start and end time;
- exit code;
- timeout;
- cancellation;
- stdout path;
- stderr path;
- output truncation;
- decoding metadata.

The adapter preserves raw process evidence and does not assign linguistic meaning or causal class.

## 4.3 Diagnostics module is authoritative for parsing

The diagnostics parser owns:

- splitting captured text into diagnostic units;
- recognizing documented diagnostic forms;
- extracting locations and messages;
- assigning parser severity;
- assigning a candidate `error_kind`;
- preserving unrecognized suspicious evidence;
- selecting a deterministic primary diagnostic;
- recording parsing warnings.

## 4.4 Diagnostics classifier is authoritative for causality

```text
ok
direct
downstream
ambiguous
noise
skipped
```

The parser must not assign these causal classes.

## 4.5 Validation module is authoritative for operation results

Validation stages combine:

- process facts;
- parsed diagnostics;
- artifact verification;
- scenario marker results;
- normalization and gold comparison where applicable.

They produce typed file, scenario and PGF-stage results without altering raw evidence.

## 4.6 Runs module is authoritative for run aggregation

The runs module owns:

- run-level status;
- aggregate counts;
- partial-run semantics;
- regression comparison inputs;
- run lifecycle and finalization.

## 4.7 Reporting module is authoritative for serialization

Reporting consumes completed structured results. It must not parse GF streams independently, reclassify diagnostics or introduce a competing pattern registry.

---

## 5. Required separation of concepts

GF Wordbench must keep these dimensions separate:

```text
execution_state
validation_status
error_kind
diagnostic_class
diagnostic_severity
```

Example:

```text
execution_state     = completed
validation_status   = FAIL
error_kind          = TYPE
diagnostic_class    = downstream
diagnostic_severity = error
```

Another example:

```text
execution_state     = timed_out
validation_status   = ERROR
error_kind          = TIMEOUT
diagnostic_class    = ambiguous
diagnostic_severity = none
```

The timeout example does not require a textual GF diagnostic.

---

## 6. Canonical error kinds

Canonical error kinds:

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

## 6.1 `OK`

No applicable error is established.

Warnings may still exist.

## 6.2 `TYPE`

GF reports a type-level incompatibility or related typed-interface failure.

Examples of conceptual categories:

- incompatible types;
- missing required record field;
- invalid function application;
- category mismatch;
- incompatible concrete/abstract interface;
- type-checking failure.

Exact wording belongs to the versioned pattern registry.

## 6.3 `SYNTAX`

GF reports a lexical, parsing or source-syntax failure.

Conceptual categories:

- unexpected token;
- malformed declaration;
- unterminated construct;
- illegal source syntax;
- source parser failure.

## 6.4 `INTERNAL`

GF reports an internal failure indicating a tool defect or violated internal invariant.

Conceptual categories:

- internal error;
- assertion failure;
- panic;
- impossible state;
- uncaught internal exception emitted by GF.

This kind must be used conservatively.

A normal language error MUST NOT be promoted to `INTERNAL`.

## 6.5 `TIMEOUT`

Derived from process facts:

```text
timed_out = true
```

A text pattern alone MUST NOT be the canonical source of `TIMEOUT`.

## 6.6 `SCRIPT`

A native GF shell scenario or command contract failed in a script-specific way.

Examples:

- unsupported GF shell command;
- malformed script command;
- required scenario marker contract failure;
- shell command rejected after successful process launch.

Marker structure itself is normally evaluated by the scenario runner, not by the generic text parser.

## 6.7 `CONFIG`

Configuration prevented valid execution or interpretation.

Examples:

- missing required project setting;
- invalid configured entrypoint;
- unsupported parser, normalization or validation option;
- invalid path configuration detected before execution.

This is normally assigned outside the GF text parser.

## 6.8 `IO`

An input/output or encoding operation failed.

Examples:

- raw evidence could not be read;
- output could not be decoded under policy;
- required evidence could not be written;
- filesystem operation failed.

This is normally assigned by the process or artifact layer.

## 6.9 `TOOL`

GF or another approved tool could not satisfy its external contract, without a safer specific category.

Examples:

- unsupported GF version;
- incompatible command option;
- unexpected tool response;
- required GF artifact missing;
- tool launch failure when represented at a higher result layer.

## 6.10 `OTHER`

Failure evidence exists but cannot be safely classified into a more specific canonical kind.

`OTHER` is preferred over a false precise classification.

---

## 7. Diagnostic severity

Internal parser severity vocabulary:

```text
info
warning
error
fatal
unknown
```

Severity is distinct from validation status.

| Severity | Meaning |
|---|---|
| `info` | Informational output recognized as diagnostic context |
| `warning` | Non-fatal caution emitted by GF |
| `error` | Error normally preventing the requested operation |
| `fatal` | Internal or unrecoverable tool-level diagnostic |
| `unknown` | Diagnostic-looking evidence without safe severity mapping |

Persisted result fields follow the schema lock. The parser retains severity in its structured result so reporting and compatibility behavior remain stable.

---

## 8. Parser inputs

The parser receives a structured request equivalent to:

```text
operation_kind
gf_version
platform
project_id
run_id
source_target
working_directory
project_root
stdout_path
stderr_path
stdout_text
stderr_text
stdout_truncated
stderr_truncated
exit_code
execution_state
decoding_metadata
strict
```

`operation_kind` uses the canonical GF operation vocabulary:

```text
probe_version
compile_module
build_pgf
run_scenario
inspect_grammar
```

The request distinguishes stdout and stderr. The parser must not receive only a concatenated report or human-formatted command display.

---

## 9. Input invariants

- Raw stdout and stderr were captured before parsing.
- Stream paths refer to immutable run artifacts.
- Text decoding policy is known.
- Exit code is available when the process launched.
- Timeout and launch failure are explicit process facts.
- Operation identity is explicit.
- GF version is recorded when probing succeeded.
- Missing raw text is distinguished from an empty stream.
- Truncation is explicit.
- The parser does not read project source to invent missing diagnostics.
- The parser does not rerun GF.

---

## 10. Raw evidence

Canonical examples:

```text
raw/compile/<safe-file-key>.out.txt
raw/compile/<safe-file-key>.err.txt
raw/scenarios/<scenario-id>.stdout.txt
raw/scenarios/<scenario-id>.stderr.txt
```

Raw evidence MUST remain immutable.

Parsing failures MUST NOT delete or rewrite raw evidence.

Every parsed record must be traceable to:

```text
stream
raw artifact path
start line
end line
```

Byte offsets MAY be recorded when capture infrastructure supports them reliably.

---

## 11. Parse view

The parser may construct an in-memory parse view.

Permitted preparation:

- CRLF to LF;
- explicit decoding result use;
- removal of recognized ANSI terminal-control sequences;
- splitting into lines;
- retaining original line numbers;
- replacing a leading BOM for recognition;
- retaining a mapping back to raw text.

The parse view MUST NOT:

- apply gold-comparison normalization;
- remove source paths;
- remove line and column locations;
- remove unknown lines;
- sort diagnostics;
- rewrite messages;
- translate output;
- collapse all whitespace;
- merge stdout and stderr destructively.

---

## 12. Stream handling

## 12.1 Separate parsing

Stdout and stderr are parsed separately.

Each diagnostic record includes:

```text
stream = stdout | stderr
```

## 12.2 No stderr assumption

GF Wordbench MUST NOT assume:

```text
stderr = errors
stdout = success
```

GF versions and operations may place diagnostics on either stream.

## 12.3 Combined interpretation

After separate parsing, records may be combined into one deterministic collection.

The combination does not claim exact cross-stream chronology unless the process runner captured a reliable sequence.

## 12.4 Deterministic fallback order

When no cross-stream event sequence exists, canonical display ordering is:

1. severity rank;
2. selected primary ranking;
3. stream tie-breaker;
4. line number;
5. pattern ID;
6. message.

Canonical stream tie-breaker:

```text
stderr
stdout
```

This tie-breaker is deterministic, not chronological.

---

## 13. Diagnostic record model

A canonical internal record contains:

```text
record_id
operation
stream
start_line
end_line
severity
error_kind
message
detail
source_path
source_module
line
column
end_line_number
end_column
symbol
pattern_id
pattern_version
confidence
raw_excerpt
normalized_signature
continuation_lines
is_fatal
is_warning
is_unknown
```

Not every field is required for every record.

---

## 14. Required diagnostic fields

Minimum fields:

```text
stream
start_line
end_line
severity
error_kind
message
pattern_id
confidence
raw_excerpt
```

Unknown retained records use:

```text
pattern_id = DIAG-UNKNOWN
error_kind = OTHER
confidence = unknown
```

when failure-associated output requires preservation.

---

## 15. Record identity

`record_id` is deterministic within one parse result.

Canonical construction inputs:

```text
stream
start_line
end_line
pattern_id
normalized_signature
```

A record ID is not a persistent global identity.

It must not include nondeterministic Python object hashes.

---

## 16. Pattern identifiers

Pattern IDs use:

```text
GF-DIAG-<DOMAIN>-<NUMBER>
```

Canonical domains:

```text
SYNTAX
TYPE
INTERNAL
SCRIPT
TOOL
WARNING
LOCATION
CONTEXT
```

Examples:

```text
GF-DIAG-SYNTAX-001
GF-DIAG-TYPE-003
GF-DIAG-INTERNAL-001
GF-DIAG-WARNING-002
```

Pattern IDs:

- are stable;
- are not reused;
- remain listed after retirement;
- identify diagnostic form, not project root cause;
- are documented in `KNOWN_DIAGNOSTIC_PATTERNS.md`.

---

## 17. Pattern registry entry

Every registered pattern must define:

```text
pattern_id
lifecycle_state
supported_operations
supported_gf_versions
supported_platforms
stream_scope
start_rule
continuation_rule
termination_rule
severity
error_kind
extracted_fields
precedence
confidence
false_positive_guards
fixtures
notes
```

Pattern lifecycle state:

```text
active
experimental
deprecated
retired
```

Experimental patterns MUST NOT silently determine release success.

---

## 18. Pattern confidence

Canonical parser confidence:

```text
exact
strong
fallback
unknown
```

## 18.1 `exact`

The output matches a narrowly defined, fixture-backed GF form.

## 18.2 `strong`

The output matches a documented family with sufficient contextual guards.

## 18.3 `fallback`

The output appears to be a failure diagnostic but lacks a specific safe mapping.

`fallback` normally maps to `OTHER`.

## 18.4 `unknown`

The parser retains suspicious output without claiming interpretation.

Confidence is not root-cause confidence.

---

## 19. Pattern precedence

Patterns execute in explicit precedence order.

Canonical precedence order:

1. internal/fatal signatures;
2. strongly located syntax/type signatures;
3. operation-specific command failures;
4. warnings;
5. generic failure signatures;
6. unknown failure-associated retention.

A broad fallback pattern MUST NOT run before a specific pattern.

Pattern order is contract-relevant and tested.

---

## 20. Line classification

Each parse-view line is classified as one of:

```text
diagnostic_start
diagnostic_continuation
context
known_noise
unknown
```

Known noise may include narrowly recognized:

- progress lines;
- successful compile lines;
- prompts;
- version banners;
- command echoes.

Known noise remains in raw evidence.

The parser MUST NOT use broad deletion rules to classify noise.

---

## 21. Multiline diagnostics

GF diagnostics may span multiple lines.

The parser uses a state machine:

```text
idle
    → open diagnostic
    → append continuation/context
    → close diagnostic
```

A diagnostic closes when:

- a new higher-precedence diagnostic start appears;
- an explicit termination rule matches;
- a non-continuation boundary appears;
- the stream ends;
- a configured maximum diagnostic length is reached.

Continuation rules must be pattern-specific where possible.

---

## 22. Continuation-line policy

A continuation line may contain:

- source excerpt;
- caret or range marker;
- expected/actual type;
- imported module context;
- symbol context;
- nested explanation;
- stack or internal-error context.

The parser MUST preserve continuation text in order.

It MUST NOT:

- flatten all lines without separators;
- discard source excerpts;
- detach carets from locations;
- attach unrelated later output;
- grow one record without a finite line limit.

---

## 23. Diagnostic length bounds

Every multiline pattern must have a finite maximum.

Required controls:

```text
maximum continuation lines
maximum characters per record
maximum total records
maximum total parsed characters
```

When a bound is reached:

- the record is retained;
- truncation is marked;
- raw evidence remains available;
- parsing continues when safe;
- strict mode may produce a parser contract error.

---

## 24. Source-location extraction

A location may contain:

```text
source_path
line
column
end_line
end_column
```

The parser must accept supported platform path forms without assuming that every colon separates a field.

Examples requiring careful handling:

```text
C:\project\Module.gf:42:7
/project/Module.gf:42:7
Module.gf:42
```

Exact supported forms belong to pattern fixtures.

---

## 25. Windows path handling

Windows drive letters make naive colon splitting unsafe.

Prohibited:

```python
parts = text.split(":")
```

without a documented location parser.

The location parser must:

- recognize drive prefixes;
- support spaces;
- support Unicode;
- preserve original path text;
- normalize only in a derived path field;
- avoid path traversal resolution unless explicitly needed;
- retain an unparsed location when ambiguity remains.

---

## 26. Path representation

A record may retain:

```text
source_path_raw
source_path_normalized
```

Rules:

- raw message text remains unchanged;
- normalized path uses project-relative form when safely resolvable;
- paths outside known roots remain explicit;
- path resolution failure does not erase the location;
- filenames relevant to diagnosis are preserved;
- serialization follows the persisted schema policy.

---

## 27. Line and column fields

Line and column numbers:

- are positive integers when present;
- use GF's reported indexing convention;
- are not converted silently between zero-based and one-based forms;
- remain absent when not provided;
- do not default to zero;
- are preserved even if a scenario normalization profile ignores them for gold comparison.

The diagnostic parser and gold normalizer have separate responsibilities.

---

## 28. Module and symbol extraction

Patterns MAY extract:

```text
source_module
symbol
expected_type
actual_type
```

Extraction must be narrow and fixture-backed.

The parser MUST NOT infer a module solely from the currently compiled filename when the diagnostic names another module.

The current target may be recorded separately as process context.

---

## 29. Message field

`message` is the compact human-readable diagnostic identity.

Rules:

- preserve GF wording;
- remove only structural prefixes already represented in fields;
- preserve punctuation when meaningful;
- preserve Unicode;
- remain bounded;
- use the first complete diagnostic statement where possible;
- do not paraphrase;
- do not prepend causal classification;
- do not include report prose.

Example conceptual transformation:

```text
raw:
<location and structured prefix> type mismatch ...

message:
type mismatch ...
```

The exact transformation belongs to the pattern.

---

## 30. Detail field

`detail` contains additional diagnostic context not suitable for the compact message.

Examples:

- expected and actual type lines;
- source excerpt;
- caret;
- nested explanation;
- internal stack context.

`detail` may be empty.

It must remain traceable to the raw excerpt.

---

## 31. Raw excerpt

Every recognized failure record SHOULD retain a bounded `raw_excerpt`.

Rules:

- excerpt preserves line order;
- excerpt identifies the source stream;
- truncation is explicit;
- excerpt does not replace raw artifact paths;
- secret-redaction policy applies only in publication copies, not by silently changing raw evidence.

---

## 32. Warning parsing

Warnings are retained separately from errors.

A warning does not automatically produce:

```text
validation_status = FAIL
```

Project or release policy may elevate selected warnings.

The parser must not independently decide warning policy.

Warnings use:

```text
severity = warning
```

and a suitable error kind, often:

```text
OTHER
TOOL
```

unless a more specific documented mapping exists.

---

## 33. Fatal diagnostics

Fatal diagnostics include narrowly recognized:

- internal GF errors;
- assertion failures;
- panic-like conditions;
- unrecoverable tool-state failures.

A fatal diagnostic SHOULD outrank ordinary errors as the primary diagnostic.

It normally maps to:

```text
severity = fatal
error_kind = INTERNAL
```

or `TOOL` when the failure is external-contract-specific.

---

## 34. Exit-code relationship

Exit code is process evidence.

The parser receives it but does not rewrite it.

Rules:

- non-zero exit strengthens the need to retain unknown failure evidence;
- zero exit does not suppress fatal text;
- zero exit does not prove scenario success;
- non-zero exit does not determine `TYPE` versus `SYNTAX`;
- a parser with no recognized error under non-zero exit should return an unknown failure-associated record;
- exit code alone does not assign `direct` or `downstream`.

---

## 35. Timeout relationship

When:

```text
timed_out = true
```

the result layer assigns:

```text
error_kind = TIMEOUT
```

The diagnostic parser may still parse partial output.

Parsed partial diagnostics:

- remain available;
- may explain what GF was doing;
- do not replace timeout as the execution failure;
- must be marked as coming from truncated or partial execution where applicable.

---

## 36. Launch-failure relationship

When GF did not launch:

- no GF textual diagnostic is expected;
- operating-system launch evidence belongs to the process layer;
- the parser is skipped or returns an empty parse result;
- final error kind is normally `TOOL`, `IO` or `CONFIG` according to the actual failure;
- a launch failure MUST NOT be presented as GF `SYNTAX`.

---

## 37. Decoding failures

A decoding problem belongs primarily to process/evidence handling.

The parser must receive:

```text
decoding_lossy
decoding_error
```

or equivalent metadata when applicable.

Rules:

- replacement characters are preserved in the parse view;
- lossy decoding is reported;
- exact message matching becomes less trustworthy;
- strict release interpretation may produce `ERROR`;
- raw bytes or a recoverable representation SHOULD remain available.

---

## 38. Truncated streams

When stdout or stderr is truncated:

- the parser records stream truncation;
- no absence claim may rely solely on the truncated stream;
- an open multiline diagnostic is marked incomplete;
- a primary message may still be selected when complete enough;
- strict mode may reject a successful interpretation;
- reports reference the truncation state.

A truncated stream MUST NOT be reported as complete raw evidence.

---

## 39. Duplicate diagnostics

The same diagnostic may appear:

- repeatedly in one stream;
- in both stdout and stderr;
- once as summary and once as detail;
- for multiple dependent modules.

Default: preserve occurrences.

The parser MAY produce a deduplicated view for aggregation.

Deduplication must not erase provenance.

---

## 40. Diagnostic signature

A `normalized_signature` supports grouping.

Canonical inputs:

```text
error_kind
stable message
normalized source path when relevant
stable symbol when relevant
pattern_id
```

The signature may normalize:

- known absolute root prefixes;
- path separators;
- unstable temporary paths;
- documented nondiagnostic numbers.

It MUST NOT remove:

- linguistic strings relevant to the error;
- constructor names;
- module names;
- meaningful types;
- line content needed to distinguish errors.

---

## 41. Duplicate key

Recommended duplicate key:

```text
pattern_id
error_kind
normalized_signature
source_path_normalized
line
column
```

Cross-stream duplicates may be collapsed into one aggregate record with:

```text
occurrences
streams
provenance
```

The full raw evidence remains unchanged.

---

## 42. Top-error aggregation

Top-error aggregation uses stable compact fields:

```text
error_kind
first_error or primary message
count
```

Canonical persisted form:

```json
{
  "error_kind": "TYPE",
  "message": "type mismatch",
  "count": 3
}
```

Rules:

- empty messages are excluded;
- aggregation does not change individual records;
- ordering is descending count, then case-insensitive message;
- broad path or number deletion is prohibited;
- `OK` is excluded;
- parser failures are not silently aggregated as language failures.

---

## 43. Primary diagnostic

Compact result models may expose:

```text
error_kind
first_error
error_detail
```

These fields derive from the primary diagnostic.

## 43.1 Selection objectives

The selected record should be:

- actionable;
- deterministic;
- close to the original failure;
- specific rather than generic;
- supported by raw evidence.

## 43.2 Canonical ranking

1. fatal internal diagnostic;
2. located syntax or type error;
3. unlocated syntax or type error;
4. operation-specific script/tool error;
5. unknown error associated with non-zero exit;
6. warning only when no error exists and policy requests warning surfacing.

Tie-breakers:

1. confidence;
2. specific pattern precedence;
3. stream tie-breaker;
4. earliest line;
5. pattern ID;
6. message.

## 43.3 Prohibited selection

Do not select:

- a progress line;
- a later cascade message over an earlier clear error without rule support;
- a warning when a fatal error exists;
- a report-generated summary;
- an inferred cause not present in the evidence.

---

## 44. `first_error`

`first_error` is a compatibility field name.

It means:

```text
compact message from the selected primary failure diagnostic
```

It does not necessarily mean the first byte emitted across both streams.

Cross-stream chronology may be unavailable.

Documentation and code should not claim otherwise.

---

## 45. `error_detail`

`error_detail` contains bounded supporting context from the primary record.

It may include:

- location;
- expected/actual information;
- source excerpt;
- continuation message.

It MUST NOT contain entire unbounded logs.

Raw paths provide the complete evidence.

---

## 46. Parser result model

A canonical parse result contains:

```text
parser_version
gf_version
operation
records
warnings
primary_record_id
primary_error_kind
primary_message
primary_detail
fatal_detected
unknown_failure_output
stdout_truncated
stderr_truncated
decoding_lossy
parse_complete
```

`parse_complete = false` when:

- stream truncation prevents full interpretation;
- multiline structure is incomplete;
- unsupported output invalidates strict parsing;
- internal parser limits were reached;
- decoding loss prevents safe recognition.

---

## 47. Parser status

The diagnostic parser itself may return:

```text
OK
ERROR
SKIPPED
```

### `OK`

Parsing completed under policy, including cases with recognized GF errors.

A GF error is data successfully parsed.

### `ERROR`

The parser could not reliably satisfy its own contract.

Examples:

- raw evidence unavailable;
- corrupt input contract;
- internal parser exception;
- unsupported strict output;
- safety bound exceeded;
- inconsistent line mapping.

### `SKIPPED`

No GF text parsing applies, such as a launch failure with no streams.

The parser does not return `FAIL`; failure belongs to validation interpretation.

---

## 48. Parser failure containment

A parser failure MUST NOT erase the GF process result.

When parsing fails:

- raw stdout remains;
- raw stderr remains;
- exit code remains;
- timeout and launch state remain;
- result status becomes `ERROR` according to the result layer;
- error kind may become `TOOL` or `OTHER`;
- reports identify diagnostic parse failure;
- no fabricated `first_error` is emitted.

---

## 49. Unknown diagnostics

Unknown failure-associated evidence is first-class.

The parser SHOULD retain it when:

- exit code is non-zero;
- a known fatal prefix appears without a complete pattern;
- strict pattern recognition fails;
- new GF wording appears;
- a suspicious error-like line is not safely classifiable.

Unknown records use conservative fields:

```text
severity = unknown
error_kind = OTHER
pattern_id = DIAG-UNKNOWN
confidence = unknown
```

Unknown evidence is not noise.

---

## 50. Known noise

A line may be classified as known noise only through a documented, fixture-backed rule.

Examples may include:

- deterministic progress output;
- prompt-only lines;
- known startup banners;
- successful compilation announcements.

Noise classification must not hide:

- errors;
- warnings;
- module names relevant to failure;
- source locations;
- missing functions;
- scenario marker failures.

Unknown lines default to preserved context, not noise.

---

## 51. Static scanning separation

Static source scanning and GF diagnostic parsing are independent.

Static scan findings:

- are not GF errors;
- do not become `TYPE` or `SYNTAX` solely from heuristic rules;
- remain in `scan_counts` and scan logs;
- may support human diagnosis;
- do not override native GF evidence.

GF diagnostic parsing consumes only GF process evidence and explicit process context.

---

## 52. Causal classification separation

The parser may identify a referenced source path or module.

It MUST NOT conclude:

```text
direct
downstream
ambiguous
```

solely from that reference.

The classifier may use:

- compiled target;
- referenced location;
- dependency graph;
- earlier failed modules;
- import chain;
- checkpoint state;
- process order;
- parsed records.

A non-zero exit and a referenced dependency do not automatically establish direct ownership.

---

## 53. Operation-specific context

Patterns may be scoped to:

```text
probe_version
compile_module
build_pgf
run_scenario
inspect_grammar
```

A pattern valid for `compile_module` must not automatically parse `run_scenario` output.

Operation scoping reduces false positives.

---

## 54. GF-version scoping

Every precise pattern defines supported GF versions.

Forms:

```text
all tested versions
minimum to maximum range
explicit version family
capability-based condition
```

An unknown newer GF version:

- may use safe generic patterns;
- records compatibility warning;
- must not be silently treated as fully supported;
- may fail strict parsing when release policy requires tested compatibility.

---

## 55. Platform scoping

Patterns may vary for:

```text
windows
posix
all
```

Platform differences commonly affect:

- path syntax;
- newline;
- executable messages;
- process wrapper errors;
- encoding.

Language diagnostic meaning should not be made platform-specific without evidence.

---

## 56. Pattern false-positive guards

Every lossy or classifying pattern must define guards.

Examples:

- expected operation;
- line prefix;
- full-line anchor;
- nearby source-location form;
- non-success exit context;
- GF version range;
- required continuation line;
- prohibited surrounding text.

Broad substring matches are prohibited for high-impact categories.

---

## 57. Regex policy

Regular expressions may be used.

Every regex must:

- be bounded or structurally safe;
- avoid catastrophic backtracking;
- be anchored where possible;
- preserve named fields;
- have positive fixtures;
- have negative fixtures;
- have Unicode fixtures;
- have Windows path fixtures where relevant;
- have long-input performance tests;
- identify its pattern ID.

Prohibited examples:

```text
.*error.*
.*type.*
split every colon
remove every number
```

without contextual guards.

---

## 58. Parser security

GF output is untrusted text.

The parser MUST:

- treat it as data;
- avoid `eval`;
- avoid dynamic imports from output;
- avoid shell execution;
- bound memory;
- bound record count;
- bound line length handling;
- avoid unsafe regex behavior;
- escape content in HTML-capable reports;
- avoid terminal-control execution;
- preserve security-relevant diagnostics.

A diagnostic message must not become an executable command.

---

## 59. HTML and Markdown safety

Reports may render parsed diagnostics.

The parser should preserve plain text.

Report writers must escape text for their output format.

The parser MUST NOT embed trusted HTML flags based on GF output.

Backticks, angle brackets and Markdown control characters remain data.

---

## 60. Determinism

For identical parser request inputs, output records must be deterministic.

The parser must not depend on:

- locale;
- current working directory;
- terminal width;
- unordered set iteration;
- random UUIDs;
- current time;
- machine hostname;
- active GUI state.

Pattern registry order is explicit.

Record ordering is explicit.

---

## 61. Parser version

The parser has its own version:

```text
MAJOR.MINOR
```

Example:

```text
1.0
```

Parser version is separate from:

- GF Wordbench package version;
- GF version;
- persisted schema version;
- normalization version.

---

## 62. Parser-version changes

### Major change

Required when changing:

- record meaning;
- pattern precedence in a result-changing way;
- primary diagnostic selection semantics;
- error-kind mapping;
- duplicate semantics;
- unknown retention policy;
- location interpretation.

### Minor change

Appropriate for:

- adding a new pattern without changing existing matches;
- adding optional metadata;
- supporting a new compatible GF wording;
- adding a warning.

Persisted consumers require schema review when parser-version data is serialized.

---

## 63. Pattern lifecycle

### Active

Used in normal parsing.

### Experimental

Collected for comparison or warning, but does not silently determine high-impact result interpretation.

### Deprecated

Still recognized for older GF versions.

### Retired

Not used for new parsing, retained in registry history.

Pattern IDs are never reassigned.

---

## 64. Compatibility adapters

A GF-version adapter may select pattern families.

It MUST NOT:

- rewrite GF diagnostics into older wording before parsing;
- hide semantic changes;
- claim support without fixtures;
- silently fall back to an incompatible pattern.

Adapters select documented interpretation rules.

Raw evidence remains unchanged.

---

## 65. Fixture model

Framework fixtures are stored under:

```text
tests/fixtures/gf_diagnostics/
├── compile/
├── pgf/
├── scenarios/
├── warnings/
├── internal/
└── unknown/
```

Each fixture includes metadata:

```text
gf_version
platform
operation
stream
exit_code
expected_records
expected_primary
```

Fixtures must not depend on the active language unless explicitly marked as project integration fixtures.

---

## 66. Positive fixtures

Every active pattern needs at least one positive fixture.

High-impact patterns have fixtures for:

- stdout;
- stderr;
- Windows path;
- POSIX path;
- location present;
- location absent;
- multiline form;
- Unicode module or path where supported.

---

## 67. Negative fixtures

Every broad pattern needs negative fixtures proving it does not match:

- linguistic text containing “type”;
- source comments echoed by a tool;
- paths containing colons;
- warning text resembling an error;
- successful progress lines;
- scenario output containing diagnostic-like words;
- user test sentences containing “error”;
- arbitrary Unicode.

---

## 68. Unknown-version fixtures

When supporting a new GF version:

1. capture real raw output;
2. store fixtures;
3. compare existing pattern behavior;
4. classify wording changes;
5. add or update patterns;
6. review primary selection;
7. update compatibility documentation.

Do not write a pattern from memory when actual GF evidence is available.

---

## 69. Unit tests

Canonical test file:

```text
tests/diagnostics/test_gf_diagnostic_parsing.py
```

Required test groups follow.

### 69.1 Stream tests

- stdout-only error;
- stderr-only error;
- errors on both streams;
- warning on stdout and error on stderr;
- duplicate diagnostic across streams;
- empty streams;
- missing stream artifact;
- no reliable cross-stream chronology.

### 69.2 Exit tests

- zero exit with fatal diagnostic;
- non-zero exit with known diagnostic;
- non-zero exit with unknown output;
- non-zero exit with empty output;
- timeout with partial diagnostic;
- launch failure with no GF output.

### 69.3 Location tests

- project-relative path;
- absolute POSIX path;
- Windows drive path;
- path containing spaces;
- Unicode path;
- line only;
- line and column;
- range;
- malformed location;
- colon in message.

### 69.4 Multiline tests

- expected/actual type continuation;
- source excerpt and caret;
- diagnostic followed by progress line;
- two adjacent diagnostics;
- stream end while record open;
- continuation limit;
- long internal diagnostic.

### 69.5 Classification tests

- `TYPE`;
- `SYNTAX`;
- `INTERNAL`;
- `SCRIPT`;
- `TOOL`;
- `OTHER`;
- warning;
- unknown.

`TIMEOUT`, `CONFIG` and `IO` tests should also prove correct assignment outside text-pattern recognition.

### 69.6 Primary selection tests

- fatal outranks ordinary error;
- located specific error outranks generic failure;
- error outranks warning;
- deterministic stream tie-break;
- earliest line tie-break;
- unknown fallback;
- no diagnostic.

### 69.7 Duplicate tests

- identical repeated line;
- same message at different locations;
- same diagnostic on both streams;
- summary/detail variant;
- occurrence provenance retained.

### 69.8 Safety tests

- extremely long line;
- many lines;
- hostile regex input;
- ANSI sequences;
- Markdown injection;
- HTML-like text;
- invalid Unicode replacement characters;
- bounded parsing time.

---

## 70. Real-GF integration tests

A small fixture grammar produces:

- successful compile;
- syntax failure;
- type failure;
- missing import or module failure;
- scenario command failure;
- warning when a stable supported warning can be induced safely.

Integration tests run against the declared supported GF versions.

They must retain raw stdout and stderr on failure.

---

## 71. Differential parser tests

When parser rules change, differential tests compare:

```text
old parser result
new parser result
```

for the complete fixture corpus.

The review identifies:

- newly matched records;
- no-longer-matched records;
- changed error kinds;
- changed primary diagnostics;
- changed signatures;
- changed warnings.

Unexpected differences block the change.

---

## 72. Fuzz testing

The parser test suite includes bounded fuzz/property tests for:

- arbitrary Unicode lines;
- arbitrary path punctuation;
- repeated prefixes;
- malformed multiline input;
- large whitespace sequences;
- embedded NUL policy;
- terminal-control sequences.

Properties:

- no crash;
- bounded execution;
- deterministic output;
- raw text not modified;
- unknown text not silently lost.

---

## 73. Parser observability

Diagnostic parsing exposes bounded debug metadata in diagnostic mode:

```text
parser_version
patterns_considered
patterns_matched
records_emitted
unknown_lines
limits_reached
parse_duration_ms
```

This metadata must not overwhelm normal reports.

Pattern debug output is a derived diagnostic artifact, not raw GF output.

---

## 74. Optional parser trace

Strict diagnostic workflows MAY create:

```text
details/<safe-key>.diagnostic-parse.txt
```

The trace may show:

- line numbers;
- stream;
- chosen classification;
- pattern ID;
- continuation grouping;
- rejected pattern reasons.

The trace MUST NOT replace stdout or stderr.

It must avoid exposing secrets beyond existing evidence policy.

---

## 75. Integration with compilation

Compilation-stage flow:

```text
validation builds typed GF request
    → external-tool adapter executes GF
    → adapter preserves stdout/stderr and process facts
    → diagnostics parser structures GF evidence
    → validation verifies expected compile artifacts
    → diagnostics classifier assigns causal ownership
    → validation builds FileResult
```

Ownership:

- validation owns compile intent and expected artifacts;
- the external-tool adapter owns process execution and raw capture;
- diagnostics owns parsing and causal classification;
- reporting consumes the completed result.

Compilation handling must not:

- assign dependency cascades before cross-file evidence exists;
- generate reports;
- discard parser warnings;
- rewrite raw output;
- reconstruct the GF command after execution.

---

## 76. Integration with scenarios

Scenario-stage flow:

```text
validation loads registered .gfs scenario
    → validation builds typed run_scenario request
    → external-tool adapter executes GF
    → adapter preserves stdout/stderr and process facts
    → diagnostics parser structures GF evidence
    → validation verifies markers
    → validation normalizes semantic sections
    → validation compares reviewed gold
    → diagnostics classifier assigns causal ownership
    → validation builds ScenarioResult
```

Diagnostic parsing and scenario output normalization are separate derived views.

A line may be relevant to both views, but neither component modifies raw evidence. The parser does not decide marker completion or gold success.

---

## 77. Integration with PGF build

PGF-stage success requires:

- process launched;
- no timeout or cancellation;
- exit policy passed;
- no fatal diagnostic;
- expected `.pgf` exists;
- artifact is non-empty;
- artifact belongs to the current request;
- manifest registration succeeds.

The diagnostics parser identifies and ranks textual GF evidence.

The validation PGF stage verifies the artifact. A missing or invalid PGF remains a contract or artifact failure even when no textual diagnostic was emitted.

---

## 78. Integration with result models

Conceptual compile summary fields:

```text
exit_code
timed_out
duration_ms
error_kind
first_error
error_detail
stdout_path
stderr_path
```

The parser supplies candidates for:

```text
error_kind
first_error
error_detail
```

The result builder may override with higher-authority process facts:

```text
TIMEOUT
IO
CONFIG
TOOL
```

The override reason should remain visible.

---

## 79. Integration with reports

Reports consume:

- final error kind;
- primary message;
- optional detail;
- raw paths;
- diagnostic class;
- parser warnings where relevant.

Reports MUST NOT:

- parse stdout independently;
- use a separate regex set;
- infer root cause from message text alone;
- hide unknown diagnostics;
- rewrite error kinds.

---

## 80. Integration with regression comparison

Regression comparison may compare:

- validation status;
- error kind;
- primary signature;
- source identity;
- scenario identity.

It should not compare raw full messages when they contain unstable paths or locations unless policy requires exact identity.

Parser-version changes may alter regression signatures and require migration notes.

---

## 81. Automated checks

The diagnostic-contract checker verifies:

1. pattern IDs are unique;
2. every active pattern has fixtures;
3. every broad pattern has negative fixtures;
4. precedence is explicit;
5. error kinds are canonical;
6. no parser assigns diagnostic class;
7. stdout and stderr are both considered;
8. raw artifacts are never modified;
9. regex safety tests pass;
10. primary selection is deterministic;
11. supported GF versions have fixture coverage;
12. retired IDs are not reused;
13. unknown output is retained;
14. parser version is declared;
15. report modules do not contain competing GF regex patterns;
16. no active-language identity appears in framework patterns;
17. no Portfolio state participates in parsing.

Exact command names and options are owned by `docs/usage/CLI_REFERENCE.md`.

---

## 82. Drift indicators

Diagnostic-parsing drift exists when:

- only stderr is parsed;
- only stdout is parsed;
- a report owns a second diagnostic regex;
- a pattern changes without fixture updates;
- a new GF version is treated as supported without evidence;
- unknown failure output disappears;
- line and column locations are removed;
- Windows paths are split incorrectly;
- a warning becomes an error without policy;
- `TYPE` and `SYNTAX` mapping differs between components;
- parser output assigns `direct` or `downstream`;
- timeout is inferred only from text;
- launch failure is reported as GF syntax;
- zero exit suppresses fatal text;
- a broad `.*error.*` pattern becomes authoritative;
- primary selection changes nondeterministically;
- duplicate handling loses stream provenance;
- parser failure deletes raw evidence;
- `first_error` is described as true cross-stream chronology;
- active-language names appear in framework patterns;
- top-error aggregation reparses human reports;
- diagnostic parsing reads a Portfolio registry or `gf-portfolio` state.

Any drift indicator requires restoration or a coordinated contract change.

---

## 83. Change workflow

A parser change is complete only when all applicable checks pass.

```text
[ ] Pattern or parser contract identified
[ ] Actual GF evidence captured
[ ] GF version recorded
[ ] Platform recorded
[ ] Operation recorded
[ ] Pattern ID assigned
[ ] Precedence reviewed
[ ] Error-kind mapping reviewed
[ ] Severity mapping reviewed
[ ] False-positive guards documented
[ ] Positive fixtures added
[ ] Negative fixtures added
[ ] Windows path impact reviewed
[ ] Unicode impact reviewed
[ ] Multiline impact reviewed
[ ] Primary-selection impact reviewed
[ ] Duplicate impact reviewed
[ ] Unknown-output behavior reviewed
[ ] Performance and regex safety tested
[ ] Parser version reviewed
[ ] Persisted schema impact reviewed
[ ] Classifier impact reviewed
[ ] Report impact reviewed
[ ] Compatibility documentation updated
[ ] Contract locks updated
```

Change record template:

```text
Pattern ID:
GF version:
Platform:
Operation:
Stream:
Observed raw output:
Expected records:
Error kind:
Severity:
Precedence:
False-positive guards:
Primary-selection impact:
Compatibility:
Parser version:
Tests:
```

---

## 84. Pattern contribution procedure

To add a pattern:

1. obtain raw GF output from a reproducible operation;
2. preserve stdout and stderr separately;
3. record GF version and platform;
4. identify the smallest stable diagnostic structure;
5. create an exact or strongly guarded rule;
6. add positive fixtures;
7. add plausible negative fixtures;
8. test against the entire corpus;
9. inspect primary-selection changes;
10. document the pattern;
11. update compatibility notes.

A pattern must not be added from an isolated paraphrased error message.

---

## 85. Forbidden behavior

The diagnostic system MUST NOT:

```text
discard stderr
discard stdout
overwrite raw evidence
parse only summary.md
parse only AI_READY.md
treat every non-zero exit as TYPE
treat every line containing "error" as fatal
infer TIMEOUT only from text
assign direct/downstream in the parser
translate GF diagnostics
remove source locations
case-fold linguistic identifiers
hide unknown output
silently ignore parser exceptions
rerun GF from a report
reuse retired pattern IDs
hardcode active-language module names
use unbounded regexes
claim cross-stream chronology without capture evidence
```

---

## 86. Related documents

### Alignment and diagnostic model

- `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`
- `docs/architecture/PRODUCT_BOUNDARIES.md`
- `docs/diagnostics/DIAGNOSTIC_OVERVIEW.md`
- `docs/diagnostics/ERROR_CLASSIFICATION.md`
- `docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md`
- `docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md`
- `docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md`

### GF and process integration

- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/gf/GF_COMMAND_CONSTRUCTION.md`
- `docs/gf/GF_COMPILATION.md`
- `docs/gf/GF_PGF_BUILD.md`
- `docs/gf/GF_SCRIPT_EXECUTION.md`
- `docs/gf/GF_VERSION_COMPATIBILITY.md`
- `docs/architecture/PROCESS_EXECUTION_MODEL.md`

### Results and artifacts

- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/ARTIFACT_MODEL.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/reports/RAW_LOGS_REFERENCE.md`
- `docs/reports/AI_READY_REFERENCE.md`
- `docs/reference/DIAGNOSTIC_KINDS.md`
- `docs/reference/STATUS_VALUES.md`

---

## 87. Governing rule

GF diagnostics are evidence produced by GF, not text owned by GF Wordbench.

GF Wordbench may recognize, structure, rank and reference that evidence, but it must preserve uncertainty and retain the original streams.

Therefore:

> No diagnostic pattern, error-kind mapping, primary-selection rule or unknown-output policy changes through an isolated regex edit.

Every diagnostic-parsing change must be grounded in raw GF evidence, version-scoped, fixture-backed, false-positive-tested, deterministic, compatible with the result model and reviewable as one coordinated contract change.
