# GF Wordbench — GF Output Normalization

**Document ID:** `GF-WB-GF-OUTPUT-NORMALIZATION`  
**Status:** Normative integration specification  
**Applies to:** Native GF process output, `.gfs` scenario transcripts, normalized comparison output, diagnostics and golden tests  
**Owner:** GF Wordbench maintainers  
**Primary implementation owner:** scenario output normalizer  
**Related external contract:** `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Related persisted schema:** `docs/PERSISTED_SCHEMA_LOCK.md`  
**Related artifact model:** `docs/architecture/ARTIFACT_MODEL.md`  
**Related scenario specification:** `docs/scenarios/OUTPUT_NORMALIZATION.md`

---

## 1. Purpose

GF output contains both stable semantic evidence and unstable execution details.

GF Wordbench normalizes only the unstable details required to make reviewed comparisons reproducible across:

- supported operating systems;
- temporary and run directories;
- equivalent path separators;
- permitted GF versions;
- repeated executions;
- different process durations;
- known shell prompts or banners;
- explicitly configured scenario variants.

This document defines:

- the boundary between raw and normalized evidence;
- the canonical normalized-output format;
- normalization profiles and versions;
- the order in which rules execute;
- permitted and prohibited transformations;
- stable replacement tokens;
- whitespace, path, prompt and version handling;
- marker extraction and validation;
- diagnostics and linguistic-output preservation;
- comparison with project gold files;
- failure behavior;
- compatibility and migration policy;
- implementation and test requirements.

The core rule is:

> Normalization may remove execution instability, but it must not remove or reinterpret linguistic, diagnostic or contractual meaning.

---

## 2. Scope

This specification governs normalization of:

- GF shell stdout;
- GF shell stderr when used as comparison material;
- merged comparison views derived from separately captured streams;
- `.gfs` scenario output;
- load and import output;
- `pg -missing` or equivalent missing-function output;
- parse output;
- linearization output;
- morphology output;
- bounded generation output;
- abstract-tree output;
- GF version banners when a scenario declares them unstable;
- prompts;
- echoed commands when explicitly recognized;
- paths;
- timestamps and durations;
- stable scenario markers;
- newline and encoding representation;
- derived `.out` files used in gold comparison.

This specification does not govern:

- raw stdout or stderr storage;
- GF command construction;
- source-code formatting;
- `.gfo` or `.pgf` binary contents;
- diagnostic causal classification;
- the semantic acceptance criteria of a language project;
- report prose;
- automatic correction of GF output;
- automatic rewriting of project gold files.

---

## 3. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **RAW OUTPUT**: stdout or stderr captured from GF before transformation.
- **NORMALIZED OUTPUT**: deterministic derived text used for stable comparison.
- **NORMALIZER**: component applying the rules in this document.
- **PROFILE**: named, versioned set of normalization rules.
- **MARKER**: stable line delimiting a scenario output section.
- **SECTION**: output between a matched begin and end marker.
- **TOKEN**: stable placeholder replacing a documented unstable value.
- **SEMANTIC OUTPUT**: linguistic or grammatical content whose identity matters.
- **DIAGNOSTIC OUTPUT**: errors, warnings, locations or tool messages relevant to diagnosis.
- **NOISE**: explicitly documented unstable output with no intended validation meaning.
- **GOLD**: reviewed expected normalized output.
- **IDEMPOTENT**: applying normalization twice produces the same bytes as applying it once.
- **LOSSY RULE**: rule that removes or replaces source text.
- **STRICT MODE**: validation mode rejecting unknown or ambiguous unstable output instead of silently preserving or removing it.

---

## 4. Architectural boundary

The evidence chain is:

```text
GF process
    → raw stdout and raw stderr
    → stream interpretation
    → marker validation
    → normalization profile
    → canonical normalized output
    → gold comparison
    → structured scenario result
    → reports
```

Each layer has separate ownership.

| Layer | Owner | May modify prior layer? |
|---|---|---|
| Raw capture | process/scenario runner | No |
| Stream interpretation | scenario runner | No |
| Marker validation | scenario runner | No |
| Normalization | normalizer | Produces a new artifact only |
| Gold comparison | comparator | No |
| Structured result | result builder | No |
| Reports | report writers | No |

The normalizer MUST NOT overwrite raw stdout or stderr.

---

## 5. Raw-evidence invariant

Stdout and stderr MUST be captured separately before normalization.

Canonical raw paths include:

```text
raw/scenarios/<scenario-id>.stdout.txt
raw/scenarios/<scenario-id>.stderr.txt
```

or the final paths supplied by `RunPaths`.

Raw evidence:

- preserves original decoded text according to the process encoding policy;
- preserves stream identity;
- preserves line ordering within each stream;
- records truncation explicitly when limits apply;
- becomes immutable after capture closes;
- remains available even when normalization fails.

A normalized file MUST reference its source raw paths through the structured scenario result.

---

## 6. Normalization objectives

A valid normalization profile produces output that is:

- deterministic;
- reviewable;
- portable;
- bounded;
- idempotent;
- traceable to raw evidence;
- stable for declared compatible GF versions;
- safe for exact gold comparison;
- conservative about meaning.

Normalization is not intended to make every GF version produce identical output.

When upstream behavior changes semantically or diagnostically, GF Wordbench must expose the change rather than hide it.

---

## 7. Non-objectives

Normalization MUST NOT be used to:

- make a failing scenario pass;
- erase a GF error;
- erase missing functions;
- hide a timeout;
- convert malformed output into valid output;
- sort linguistic variants merely to avoid a diff;
- change orthography;
- change Unicode normalization without project approval;
- repair malformed trees;
- reformat arbitrary GF syntax;
- translate diagnostics;
- infer missing markers;
- synthesize expected sections;
- remove unexpected extra output;
- hide differences caused by unsupported GF versions.

---

## 8. Canonical normalized-output artifact

## 8.1 Path

Canonical path:

```text
run_<run-id>/raw/scenarios/<scenario-id>.out
```

The path stored in `ScenarioResult.normalized_output_path` is relative to the run directory in persisted summaries.

---

## 8.2 File identity

Canonical header:

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: <scenario-id>
# profile_id: <profile-id>
# normalization_version: <major.minor>
```

Example:

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: parse
# profile_id: scenario-default
# normalization_version: 1.0
```

The header MUST be generated by GF Wordbench.

It MUST NOT be copied from untrusted GF output.

---

## 8.3 Section format

Canonical section delimiters:

```text
--- BEGIN <section-id> ---
<normalized GF output>
--- END <section-id> ---
```

Example:

```text
--- BEGIN parse-basic ---
PredVP (UsePN John_PN) (UseV sleep_V)
--- END parse-basic ---
```

Rules:

- section IDs are unique within a scenario;
- section order follows scenario execution;
- every begin delimiter has one matching end delimiter;
- delimiters are generated after validating raw scenario markers;
- section content may be empty only when the scenario contract permits it;
- one final LF newline is required.

---

## 8.4 Empty scenario output

An output file with no sections is invalid for a scenario requiring markers.

A scenario explicitly permitting no semantic output may use:

```text
--- BEGIN <section-id> ---
--- END <section-id> ---
```

The scenario specification must state why empty content is valid.

---

## 9. Scenario marker contract

## 9.1 Raw marker syntax

Recommended raw marker syntax emitted by `.gfs` scenarios:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
GF_WORDBENCH_END <scenario-id>:<section-id>
```

A compact form without repeated scenario ID may be supported only when the scenario-format specification declares it:

```text
GF_WORDBENCH_BEGIN <section-id>
GF_WORDBENCH_END <section-id>
```

One canonical marker syntax SHOULD be selected for new scenarios.

---

## 9.2 Marker recognition

Marker recognition MUST:

- require an exact documented prefix;
- match the complete line after permitted line-ending normalization;
- validate scenario identity when included;
- validate section-ID syntax;
- reject duplicate open sections;
- reject an end marker without an open section;
- reject nested sections unless a future version explicitly supports them;
- reject a missing end marker;
- preserve output outside sections as separate preamble or unexpected-output evidence.

The normalizer MUST NOT recognize approximate marker spellings.

---

## 9.3 Marker identity

Recommended section-ID syntax:

```text
[a-z][a-z0-9-]*
```

Examples:

```text
load-grammar
missing-functions
parse-basic
linearize-basic
morphology-nouns
generation-bounded
```

Project-specific prefixes MAY be used when documented.

Changing a section ID is a gold-contract change.

---

## 9.4 Output outside markers

Output outside markers may include:

- GF startup banner;
- prompt;
- echoed import;
- exit text;
- diagnostics;
- unexpected semantic output.

A profile must classify each recognized outside-marker line as:

```text
preserve
replace
drop
error
```

Default behavior for unknown outside-marker output:

- non-strict mode: preserve in an explicit `unscoped-output` section and warn;
- strict mode: fail normalization.

Unknown output MUST NOT be silently discarded.

---

## 10. Normalization profile model

## 10.1 Profile identity

Each scenario resolves one profile:

```text
profile_id
normalization_version
```

Canonical default:

```text
profile_id = "scenario-default"
normalization_version = "1.0"
```

A project may define additional profiles only when a real output class requires different rules.

Examples:

```text
scenario-default
diagnostic-locations
version-probe
bounded-generation
```

A profile MUST NOT be created solely to conceal one failing gold comparison.

---

## 10.2 Profile contents

A profile defines:

```text
profile_id
version
supported_content_types
ordered_rules
stable_tokens
marker_policy
unknown_line_policy
unicode_policy
whitespace_policy
variant_order_policy
maximum_output_size
```

Profiles SHOULD be represented as immutable typed configuration.

Executable arbitrary replacement code in project configuration is prohibited.

---

## 10.3 Profile ownership

Framework profiles are owned by the framework normalizer.

Language-specific acceptance belongs to project scenarios and gold files, not to arbitrary framework normalization.

Project configuration MAY select an approved profile.

It MUST NOT inject unreviewed regular-expression deletion rules into the normalizer.

---

## 10.4 Rule identity

Every lossy rule SHOULD have a stable identifier:

```text
NORM-<DOMAIN>-<NUMBER>
```

Examples:

```text
NORM-TEXT-001
NORM-PATH-001
NORM-TIME-001
NORM-PROMPT-001
NORM-VERSION-001
```

Rule IDs make gold-impact reviews traceable.

---

## 11. Normalization pipeline

Rules execute in this canonical order:

```text
1. Validate input availability
2. Decode or accept previously decoded raw text
3. Normalize line endings
4. Remove a leading UTF-8 BOM when accepted for compatibility
5. Remove ANSI control sequences
6. Validate and extract raw scenario markers
7. Classify scoped and unscoped output
8. Apply exact prompt and banner rules
9. Replace approved unstable paths
10. Replace approved timestamps and durations
11. Apply operation-specific stable substitutions
12. Apply whitespace policy
13. Validate Unicode policy
14. Validate required content
15. Render canonical header and section delimiters
16. Enforce output-size policy
17. Verify idempotence in tests or strict diagnostics
18. Write the derived `.out` artifact atomically
```

Changing rule order may change output and therefore requires compatibility review.

---

## 12. Text encoding

## 12.1 Canonical encoding

Normalized output MUST use:

```text
UTF-8 without BOM
```

## 12.2 Raw decoding

Raw process decoding is governed by the process execution model.

The normalizer receives either:

- valid decoded Unicode plus decoding metadata; or
- raw bytes through an explicit decoding interface.

Decoding errors MUST NOT silently discard bytes.

A replacement-character strategy, when used, must:

- be explicit;
- record that decoding was lossy;
- normally prevent exact release gold success unless the scenario permits it.

---

## 12.3 BOM handling

A single leading UTF-8 BOM MAY be removed.

A BOM elsewhere in content MUST be preserved or treated as unexpected Unicode according to profile policy.

---

## 13. Line endings

Canonical normalized newline:

```text
LF
```

Rules:

- CRLF becomes LF;
- isolated CR becomes LF only when the input policy explicitly supports it;
- one final LF is required;
- line-ending normalization occurs before marker recognition;
- raw files remain unchanged.

Line-ending differences alone must not create gold mismatches.

---

## 14. ANSI and terminal control sequences

ANSI color and terminal-control sequences MAY be removed from normalized output when:

- they are recognized structurally;
- they have no semantic meaning;
- their removal does not join previously separated text incorrectly.

The rule MUST NOT remove arbitrary bracketed text that resembles an escape sequence after decoding.

Terminal cursor movement that changes visible line content requires a documented rendering strategy.

Strict mode SHOULD fail when control behavior cannot be interpreted safely.

---

## 15. Whitespace policy

## 15.1 Allowed normalization

The default profile MAY:

- remove trailing spaces and tabs;
- convert platform newlines to LF;
- ensure one final newline;
- remove whitespace-only lines explicitly classified as prompt separation;
- collapse repeated blank lines only when the profile declares them non-semantic.

## 15.2 Preserved whitespace

The normalizer MUST preserve:

- leading spaces when they convey tree structure or output layout;
- internal spaces in linearized strings;
- tabs when part of declared semantic output;
- blank lines within a section when the scenario treats them as meaningful;
- empty strings distinguishable from missing output.

## 15.3 Prohibited generic cleanup

The normalizer MUST NOT globally:

- trim every line on both sides;
- collapse all whitespace to one space;
- reindent trees;
- wrap long lines;
- reorder columns;
- parse and reserialize linguistic strings merely for aesthetics.

---

## 16. Stable replacement tokens

Canonical tokens:

```text
<PROJECT_ROOT>
<RGL_ROOT>
<RUN_DIR>
<GF_EXECUTABLE>
<TEMP_DIR>
<DURATION_MS>
<TIMESTAMP>
```

Additional tokens require documentation and version review.

---

## 16.1 Token properties

Tokens MUST:

- use uppercase ASCII names;
- be enclosed in angle brackets;
- have one stable meaning;
- replace only a resolved known value;
- not collide with expected linguistic text without an escaping policy;
- be documented in the profile;
- remain stable for the profile version.

---

## 16.2 Replacement precedence

When paths overlap, replace the most specific path first.

Recommended order:

```text
RUN_DIR
PROJECT_ROOT
RGL_ROOT
TEMP_DIR
GF_EXECUTABLE
```

Example:

```text
C:\work\GF_Wordbench\runs\run_20260721_163210\raw\scenarios\parse.out
```

becomes:

```text
<RUN_DIR>/raw/scenarios/parse.out
```

It must not become:

```text
<PROJECT_ROOT>/runs/run_20260721_163210/raw/scenarios/parse.out
```

when `<RUN_DIR>` is the more specific approved identity.

---

## 17. Path normalization

## 17.1 Permitted path transformations

A profile MAY:

- replace an exact resolved absolute root with its stable token;
- convert separators inside a recognized path to `/`;
- remove a documented ephemeral filename suffix;
- normalize Windows drive-letter case when comparing the same resolved path;
- replace a verified temporary directory with `<TEMP_DIR>`.

## 17.2 Path-recognition requirements

A path replacement rule MUST use:

- a resolved path supplied by run configuration or `RunPaths`;
- explicit boundary checks;
- platform-aware matching;
- longest-match precedence;
- tests for paths containing spaces;
- tests for Unicode path segments.

A rule MUST NOT search for arbitrary text resembling a path and remove it broadly.

---

## 17.3 Relative project paths

Project-relative source paths SHOULD be preserved because they are diagnostically useful and portable.

Example:

```text
lib/src/french/GrammarFre.gf:42:7
```

should remain, unless a profile specifically replaces only the absolute project prefix.

---

## 17.4 Diagnostic locations

Line and column locations MUST be preserved by default.

Example:

```text
GrammarFre.gf:42:7
```

A scenario MAY ignore locations only when:

- location instability is documented;
- the validation purpose does not depend on exact location;
- the profile uses a specific rule;
- raw diagnostics remain available;
- the gold-impact decision is reviewed.

A generic deletion of all numbers after colons is prohibited.

---

## 18. Timestamps

A timestamp MAY be replaced by:

```text
<TIMESTAMP>
```

only when:

- the timestamp format is recognized exactly;
- the timestamp is execution metadata rather than linguistic output;
- the scenario declares it unstable;
- the surrounding text remains meaningful.

Project test data containing dates MUST NOT be normalized as timestamps merely because it matches a date pattern.

Rules should prefer known output positions or prefixes over broad date regular expressions.

---

## 19. Durations and performance values

Measured durations MAY be replaced by:

```text
<DURATION_MS>
```

or removed with their entire known non-semantic line when the profile permits.

Examples:

```text
duration_ms=143
```

becomes:

```text
duration_ms=<DURATION_MS>
```

CPU, memory and timing values MUST be preserved when the scenario validates performance behavior.

Performance normalization is operation-specific, not global.

---

## 20. GF prompts

Known GF shell prompts MAY be removed when:

- the exact prompt form is recognized;
- prompt identity is not part of the scenario;
- removal does not delete content sharing the same line;
- GF-version compatibility is documented.

Prompt handling MUST distinguish:

```text
prompt-only line
prompt followed by echoed command
prompt embedded in semantic output
```

Unknown prompt forms:

- are preserved with a warning in non-strict mode;
- cause normalization failure in strict mode when they disrupt markers or content.

---

## 21. Echoed commands

GF or a wrapper may echo commands.

Echo removal is allowed only when:

- the executed command list is already preserved separately;
- the exact echoed line is known;
- removing it does not remove GF response text;
- the scenario profile declares echo non-semantic.

A line matching user linguistic input MUST NOT be removed merely because it resembles a command.

---

## 22. GF startup and version banners

## 22.1 Default policy

GF version information is evidence and SHOULD remain visible in run metadata.

A scenario output profile MAY remove or replace a startup banner when the scenario is explicitly version-independent.

## 22.2 Version-dependent scenarios

A version-probe or compatibility scenario MUST preserve the relevant version text.

## 22.3 Safe replacement

When a banner is intentionally abstracted, use a stable representation such as:

```text
GF_VERSION=<recorded>
```

or omit it from the normalized scenario section while retaining it in raw evidence and run metadata.

The profile must document which policy applies.

## 22.4 Unsupported changes

If a newer GF version changes meaningful output structure, the normalizer MUST NOT treat the new structure as banner noise.

---

## 23. Diagnostics

Normalization MUST preserve diagnostic meaning.

It MUST preserve by default:

- severity;
- diagnostic message;
- source filename;
- line and column;
- referenced module or symbol;
- expected and actual types;
- syntax fragments;
- missing-function names;
- internal-error identity;
- timeout or launch evidence when included in derived views.

Allowed diagnostic normalization is limited to known unstable context such as:

- absolute root prefixes;
- path separators;
- temporary paths;
- terminal color;
- explicitly unstable timing.

Diagnostic wording MUST NOT be paraphrased.

---

## 24. Parse output

Parse normalization MUST preserve:

- parse count when emitted;
- abstract trees;
- ambiguity;
- order unless the scenario defines an unordered set;
- empty parse result;
- failure diagnostics;
- language and category distinctions relevant to the scenario.

It MUST NOT:

- alphabetically sort trees by default;
- deduplicate identical lines unless GF's duplicate semantics are irrelevant and documented;
- remove constructor names;
- rewrite trees;
- treat no output as zero parses without explicit evidence.

---

## 25. Linearization output

Linearization normalization MUST preserve:

- surface strings;
- Unicode characters;
- punctuation;
- spacing with linguistic meaning;
- variants;
- variant order unless explicitly declared unordered;
- empty-string output;
- language labels when required;
- runtime errors.

It MUST NOT:

- case-fold;
- strip accents;
- normalize punctuation;
- collapse internal whitespace globally;
- sort variants merely to stabilize output;
- convert Unicode letters to ASCII;
- apply language-specific orthographic correction.

---

## 26. Morphology output

Morphology normalization MUST preserve:

- lemma;
- paradigm labels;
- feature labels;
- form strings;
- table structure when semantically relevant;
- missing forms;
- variants;
- Unicode distinctions;
- failure diagnostics.

A morphology profile MAY normalize known column padding only if it retains an unambiguous field structure.

It MUST NOT infer, repair or complete missing forms.

---

## 27. Missing-function output

Missing-function normalization MUST preserve:

- every missing function;
- module context when emitted;
- duplicate identity when duplicates are meaningful;
- fatal diagnostics;
- explicit no-missing result when emitted.

Ordering may be normalized only if:

- upstream ordering is documented as unstable;
- the result is semantically a set;
- the scenario declares set comparison;
- duplicate handling is specified;
- the normalization-version change is reviewed.

Default behavior preserves GF order.

---

## 28. Generation output

Generation can be nondeterministic or excessively large.

A generation scenario MUST define:

- a deterministic seed where supported, or a non-exact assertion strategy;
- a finite result bound;
- expected ordering policy;
- duplicate policy;
- whether exact gold comparison is valid.

Normalization MUST NOT convert random generation into apparently deterministic exact gold output.

When exact ordering is not guaranteed, use structured assertions rather than arbitrary sorting unless the project specification explicitly defines the output as an unordered set.

---

## 29. Tree and structured output

For abstract trees, term output and structured GF values:

- preserve constructor names;
- preserve argument order;
- preserve nesting;
- preserve quotes and escapes;
- preserve line breaks when they convey structure;
- avoid parser/reserializer changes unless a dedicated canonical GF-term parser is formally specified.

Textual tree reformatting is prohibited in the default profile.

---

## 30. Unicode policy

## 30.1 Default

Unicode code points are preserved exactly after decoding.

## 30.2 Unicode normalization forms

NFC, NFD, NFKC or NFKD conversion MUST NOT occur by default.

A language project may require a Unicode normalization form only when:

- the language specification documents it;
- source and expected output policy agree;
- raw output remains unchanged;
- the profile version records the rule;
- project gold files are reviewed.

Compatibility normalization that changes characters is prohibited without explicit project approval.

## 30.3 Invisible characters

The normalizer MAY detect and report:

- zero-width characters;
- non-breaking spaces;
- directional marks;
- control characters.

It MUST NOT silently remove them when they may be linguistically meaningful.

---

## 31. Ordering policy

Default: preserve source order.

A profile may sort only when all conditions hold:

1. the output represents a documented unordered collection;
2. the sort key is explicit;
3. duplicate behavior is defined;
4. sorting does not hide a meaningful upstream ordering change;
5. the scenario contract selects the rule;
6. gold impact is reviewed.

Stable sorting SHOULD use Unicode code-point order unless a different deterministic key is specified.

Locale-dependent sorting is prohibited.

---

## 32. Duplicate policy

Default: preserve duplicates.

Deduplication is allowed only for a documented set-valued output.

When deduplicating:

- exact identity rules must be defined;
- order after deduplication must be deterministic;
- duplicate counts must be preserved separately when they are evidence;
- the profile must state that multiplicity is non-semantic.

---

## 33. Size limits and truncation

## 33.1 Raw output

Raw-output limits are governed by the process model.

Any truncation MUST be explicit.

## 33.2 Normalized output

A profile may define:

```text
maximum_output_size
maximum_lines
maximum_items
```

If normalized content exceeds the limit:

- exact gold comparison MUST fail or be skipped with `ERROR`;
- the normalized file may contain an explicit truncation marker;
- the scenario result records truncation;
- raw evidence remains referenced;
- success MUST NOT be inferred from the retained prefix.

Canonical marker:

```text
<GF_WORDBENCH_OUTPUT_TRUNCATED>
```

This marker is framework-generated and cannot be interpreted as normal GF content.

---

## 34. Unknown output policy

Unknown output is text not classified by:

- markers;
- a preserved semantic section;
- an approved noise rule;
- an approved replacement rule;
- a known diagnostic rule.

Default policies:

| Mode | Policy |
|---|---|
| Development non-strict | Preserve and warn |
| Diagnostic | Preserve with maximum context |
| Release | Fail required exact comparison unless explicitly accepted |
| Strict checker | Fail normalization |

Unknown output MUST never be silently deleted.

---

## 35. Failure semantics

Normalization produces one of:

```text
OK
FAIL
ERROR
SKIPPED
```

### `OK`

- raw evidence exists;
- required markers are valid;
- all rules execute;
- output is produced;
- no prohibited ambiguity remains.

### `FAIL`

Use only when normalization completed correctly but a validation criterion based on normalized output fails, such as gold mismatch.

The normalizer itself normally reports `OK`; the comparator reports `FAIL`.

### `ERROR`

Examples:

- missing raw input;
- malformed markers;
- decoding contract failure;
- unsafe ambiguous path replacement;
- unsupported profile version;
- unexpected output under strict policy;
- output limit exceeded for exact comparison;
- write failure;
- non-idempotent rule behavior detected.

### `SKIPPED`

Normalization is intentionally not required because the scenario did not run or does not produce comparison material.

A skipped normalization is distinct from empty normalized output.

---

## 36. Normalization result model

A structured normalization result SHOULD contain:

```text
scenario_id
profile_id
normalization_version
status
raw_stdout_path
raw_stderr_path
normalized_output_path
sections
warnings
applied_rule_ids
unknown_output_present
truncated
error_kind
primary_message
```

`applied_rule_ids` SHOULD include lossy or compatibility-relevant rules, not every trivial internal operation.

The persisted shape is governed by the shared models and schema lock.

---

## 37. Canonical comparison with gold

Comparison inputs:

```text
actual = normalized scenario .out
expected = project .gold
```

Before exact comparison, the comparator may apply only file-container normalization already required by the persisted schema:

- UTF-8 BOM compatibility handling;
- CRLF to LF;
- final-newline policy.

The comparator MUST NOT apply a second hidden semantic normalizer.

Actual and gold headers must agree on:

```text
scenario_id
normalization_version
```

The profile ID SHOULD also agree when present.

---

## 38. Gold mismatch

On mismatch, GF Wordbench SHOULD create:

```text
raw/scenarios/<scenario-id>.gold.diff
```

The diff is a derived artifact.

It SHOULD contain:

- scenario ID;
- expected gold path;
- actual normalized path;
- profile ID;
- normalization version;
- deterministic unified diff;
- explicit newline-at-end information when relevant.

The diff MUST NOT replace either input.

---

## 39. Gold update boundary

Normal validation is read-only for:

```text
project/validation/gold/*.gold
```

A gold update requires a separate explicit operation.

Conceptual command:

```text
gf-wordbench gold update <scenario-id>
```

The update workflow must:

1. execute the scenario;
2. preserve raw evidence;
3. normalize with the selected profile;
4. compare old and new output;
5. show or store a diff;
6. require explicit approval or a dedicated reviewed CI mode;
7. write atomically;
8. update project review evidence;
9. update normalization version or documentation when rules changed.

A gold file MUST NOT be updated merely to make a test pass.

---

## 40. Profile versioning

Profile versions use:

```text
MAJOR.MINOR
```

### Major increment

Required when a change may alter existing normalized semantic content or invalidate existing gold interpretation.

Examples:

- changing marker extraction;
- changing path-base semantics;
- sorting an output previously preserving order;
- changing Unicode normalization;
- removing a newly classified line;
- changing duplicate handling;
- changing stable-token meaning;
- changing section rendering.

### Minor increment

Appropriate for compatible changes such as:

- adding support for a new exact prompt variant without affecting existing output;
- adding a new optional warning;
- supporting a new profile field with a safe default;
- recognizing an additional path spelling that maps to the same token.

A new profile version must not be inferred from the application version.

---

## 41. Compatibility across GF versions

Normalization compatibility depends on GF output behavior.

GF Wordbench must maintain:

```text
tested GF versions
known incompatible GF versions
profile versions tested with each GF version
```

When a new GF version changes output:

1. preserve raw evidence;
2. determine whether the change is noise, formatting, diagnostic or semantic;
3. avoid changing rules until classified;
4. add fixtures from the new version;
5. update the profile only when safe;
6. review affected gold files;
7. document compatibility.

Unknown newer GF versions may proceed with warnings outside strict release policy.

Normalization MUST NOT silently claim compatibility.

---

## 42. Idempotence

For any valid normalized output `N`:

```text
normalize(N) = N
```

or, when the implementation accepts only raw-format input:

```text
render(parse(N)) = N
```

Idempotence tests are required for:

- canonical headers;
- section delimiters;
- tokens;
- line endings;
- trailing whitespace;
- prompt removal;
- path replacement;
- timestamps;
- durations.

A non-idempotent profile is invalid.

---

## 43. Determinism

Normalization must not depend on:

- current working directory;
- machine hostname;
- user locale;
- local timezone;
- hash-randomization order;
- unordered dictionary traversal;
- terminal width;
- console color capability;
- GUI state;
- system path separator after canonical rendering.

All injected values must come from explicit run configuration, process results or profile configuration.

---

## 44. Security

Normalization input is untrusted text.

The normalizer MUST:

- treat output as data, never executable code;
- avoid shell evaluation;
- avoid template execution from output text;
- validate paths before replacement;
- bound memory and output size;
- avoid catastrophic regular expressions;
- avoid leaking secret environment values through overly broad diagnostics;
- preserve redaction provenance when a publication pipeline creates redacted derived copies.

The normalizer MUST NOT use project-supplied arbitrary Python or shell code.

---

## 45. Regular-expression policy

Regular expressions MAY be used for recognized unstable formats.

Every lossy regex rule MUST:

- be anchored where possible;
- define expected context;
- avoid matching arbitrary linguistic text;
- have positive fixtures;
- have negative fixtures;
- have Unicode fixtures;
- have performance tests for hostile input;
- have a stable rule ID;
- be reviewed for gold impact.

Broad patterns such as these are prohibited:

```text
remove every number
remove every path-looking substring
remove every bracketed expression
remove every line containing "time"
```

---

## 46. Implementation boundaries

Recommended components:

```text
app/audit/scenario_runner.py
app/audit/normalization.py
app/audit/gold_compare.py
app/models.py
```

or equivalent final names.

### Scenario runner

Owns:

- raw capture;
- marker-aware execution result;
- source paths;
- scenario identity.

Does not own:

- arbitrary gold updates;
- user-facing reports.

### Normalizer

Owns:

- approved profile application;
- canonical `.out` rendering;
- normalization warnings and errors.

Does not own:

- raw evidence;
- linguistic acceptance criteria;
- gold approval.

### Gold comparator

Owns:

- actual/expected comparison;
- deterministic diff;
- gold-match result.

Does not modify gold.

### Reports

Consume structured normalization and comparison results.

Do not normalize raw output independently.

---

## 47. Central rule registry

Normalization rules MUST have one implementation owner.

Prohibited:

```text
scenario_runner normalizes prompts
report writer normalizes paths
gold comparator trims whitespace
AI report removes timestamps
```

Expected:

```text
normalizer applies all comparison normalization
comparator performs only documented file-container normalization
reports consume normalized paths and results
```

A second hidden normalizer creates drift.

---

## 48. Required unit tests

Recommended file:

```text
tests/gf/test_output_normalization.py
```

Required cases:

### Encoding and newlines

- UTF-8 text;
- leading BOM;
- CRLF;
- LF;
- isolated CR policy;
- invalid byte handling;
- final newline.

### Markers

- valid one-section scenario;
- multiple ordered sections;
- duplicate section ID;
- missing end;
- end without begin;
- nested marker;
- wrong scenario ID;
- marker-like linguistic text;
- unscoped output.

### Whitespace

- trailing spaces;
- meaningful leading spaces;
- meaningful internal spaces;
- empty line;
- empty string;
- repeated blank-line policy.

### Paths

- Windows drive path;
- path containing spaces;
- POSIX path;
- Unicode path;
- overlapping roots;
- separator conversion;
- false positive path-like linguistic text;
- path traversal text.

### Prompts and banners

- known prompt;
- prompt with command echo;
- unknown prompt;
- version-independent banner;
- version-probe scenario;
- changed banner.

### Time values

- known timestamp line;
- linguistic date;
- known duration;
- semantic performance scenario;
- number-heavy linguistic output.

### Unicode

- accented letters;
- combining marks;
- non-breaking space;
- directional mark;
- emoji or symbols when present;
- NFC/NFD preservation.

### Linguistic output

- parse tree;
- multiple parses;
- linearization punctuation;
- empty linearization;
- morphology table;
- missing-function list;
- generation duplicates;
- variant order.

### Safety

- huge line;
- hostile regex input;
- ANSI sequences;
- unknown control sequence;
- output truncation;
- unknown output strict mode.

### Idempotence

- every canonical fixture normalizes identically on a second pass.

---

## 49. Golden fixtures for the normalizer

The framework SHOULD maintain normalization fixtures separate from language-project gold files.

Recommended layout:

```text
tests/fixtures/normalization/
├── raw/
├── expected/
└── profiles/
```

Fixture names should identify:

```text
GF version
platform class
operation
profile version
case
```

Example:

```text
gf-3x_windows_parse_prompt.raw.txt
gf-3x_windows_parse_prompt.expected.out
```

Fixtures MUST NOT depend on the active language unless explicitly labeled as language-specific integration fixtures.

---

## 50. Real-GF integration tests

A small fixture grammar SHOULD verify:

- startup and prompt handling;
- load markers;
- parse output;
- linearization output;
- missing-function output;
- bounded generation;
- supported GF versions;
- Windows and POSIX path behavior where available.

Real-GF tests must preserve raw outputs as test diagnostics.

They SHOULD be marked separately from fast unit tests.

---

## 51. Contract checks

Recommended command:

```text
gf-wordbench normalization check
```

Strict mode:

```text
gf-wordbench normalization check --strict
```

The checker should verify:

1. every configured profile exists;
2. every profile has a version;
3. rule IDs are unique;
4. required markers use the canonical syntax;
5. gold files declare compatible normalization versions;
6. unknown project deletion rules are absent;
7. normalized fixtures match expected output;
8. profiles are idempotent;
9. output ordering is deterministic;
10. raw artifacts are not modified;
11. comparator has no hidden semantic normalization;
12. regex rules pass safety tests;
13. supported GF-version fixtures exist;
14. stable tokens use canonical meanings.

---

## 52. Drift indicators

Normalization drift exists when:

- raw files change during normalization;
- a report applies additional cleanup;
- GUI and CLI select different profiles for equivalent runs;
- one scenario uses undocumented markers;
- a marker is approximately matched;
- an unknown line disappears;
- a path is removed without a stable token;
- semantic punctuation changes;
- Unicode is silently normalized;
- variants are reordered without policy;
- duplicates disappear without policy;
- line locations vanish globally;
- a new GF version produces different output but gold still passes because of a broad deletion rule;
- profile behavior changes without version change;
- gold changes without normalization review;
- the comparator trims or sorts beyond this specification;
- normalized output cannot identify raw source evidence;
- applying normalization twice changes output.

Any drift indicator requires restoration or a coordinated versioned contract change.

---

## 53. Change workflow

A normalization change is complete only when all applicable items are satisfied.

```text
[ ] Rule purpose documented
[ ] Rule ID assigned
[ ] Profile identified
[ ] Current version identified
[ ] Lossy/non-lossy classification recorded
[ ] Semantic-risk review completed
[ ] Diagnostic-risk review completed
[ ] Unicode impact reviewed
[ ] Ordering and duplicate impact reviewed
[ ] Raw evidence remains unchanged
[ ] Positive fixtures added
[ ] Negative fixtures added
[ ] Idempotence test added
[ ] Real-GF compatibility reviewed
[ ] Affected gold files identified
[ ] Gold diffs reviewed deliberately
[ ] Profile version updated
[ ] Persisted schema impact reviewed
[ ] External-tool lock updated when applicable
[ ] Migration note added
[ ] Documentation updated
```

Change record template:

```text
Rule ID:
Profile:
Current version:
Target version:
Observed unstable output:
Proposed transformation:
Why it is non-semantic:
False-positive risk:
GF versions:
Platforms:
Affected scenarios:
Affected gold files:
Compatibility:
Migration:
Tests:
```

---

## 54. Allowed default transformations

The canonical default profile may perform only the following unless extended deliberately:

```text
NORM-TEXT-001  CRLF → LF
NORM-TEXT-002  remove one leading UTF-8 BOM
NORM-TEXT-003  remove trailing spaces and tabs
NORM-TEXT-004  ensure one final LF
NORM-TERM-001  remove recognized ANSI control sequences
NORM-MARK-001  validate and convert scenario markers
NORM-PATH-001  replace exact run root with <RUN_DIR>
NORM-PATH-002  replace exact project root with <PROJECT_ROOT>
NORM-PATH-003  replace exact RGL root with <RGL_ROOT>
NORM-PATH-004  replace exact GF executable path with <GF_EXECUTABLE>
NORM-PATH-005  canonicalize separators inside recognized paths
NORM-PROMPT-001 remove exact documented prompt-only lines
NORM-TIME-001  replace exact documented execution timestamp
NORM-TIME-002  replace exact documented duration value
```

Prompt, timestamp and duration rules are applied only when selected by the profile and recognized in explicit context.

---

## 55. Forbidden transformations

The default and custom profiles MUST NOT:

```text
remove all numbers
remove all diagnostics
remove all paths
remove all blank lines
trim both sides of every line
collapse all whitespace
case-fold output
strip accents
transliterate Unicode
sort all lines
sort all trees
deduplicate all lines
remove constructor names
remove line/column locations globally
rewrite GF trees
repair malformed syntax
translate messages
synthesize missing markers
ignore unmatched markers
drop unknown output
replace linguistic dates as timestamps
update gold files
```

---

## 56. Related documents

### External execution and artifacts

- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/architecture/PROCESS_EXECUTION_MODEL.md`
- `docs/architecture/ARTIFACT_MODEL.md`
- `docs/gf/GF_SCRIPT_EXECUTION.md`

### Scenarios and gold

- `docs/scenarios/SCENARIO_FORMAT.md`
- `docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md`
- `docs/scenarios/OUTPUT_NORMALIZATION.md`
- `docs/scenarios/GOLDEN_TESTS.md`
- `docs/scenarios/UPDATING_GOLD_FILES.md`

### Schemas and diagnostics

- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/reports/SUMMARY_JSON_REFERENCE.md`
- `docs/diagnostics/GF_DIAGNOSTIC_PARSING.md`
- `docs/reference/DIAGNOSTIC_KINDS.md`

### Project authority

- `project/project.toml`
- `project/docs/VALIDATION_SPEC.md`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`

---

## 57. Final enforcement rule

Normalized output is derived evidence, not cleaned-up truth.

GF Wordbench must always preserve the distinction between what GF emitted and what the framework transformed for stable comparison.

Therefore:

> No normalization rule may be added, broadened, reordered or reinterpreted without proving that raw evidence remains intact and that linguistic and diagnostic meaning are preserved.

Any change capable of altering existing gold comparisons is a versioned contract change requiring fixtures, compatibility review, deliberate gold review and migration documentation.
