# GF Wordbench — Scenario Output Normalization

**Document ID:** `GF-WB-SCENARIO-OUTPUT-NORMALIZATION`  
**Status:** Normative  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\scenarios\OUTPUT_NORMALIZATION.md`  
**Applies to:** GF scenario stdout normalization, canonical `.out` generation and gold comparison  
**Owner:** GF Wordbench maintainers  
**Primary implementation owner:** `app/audit/scenario_runner.py`  
**External contract:** Output normalization contract in `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Project contracts:** `PIFC-SCENARIO-004`, `PIFC-GOLD-001`, `PIFC-GOLD-002`  
**Persisted schemas:** `gf-wordbench.scenario-output/1.0`, `gf-wordbench.scenario-gold/1.0`  
**Normalization version:** `1.0`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

Scenario output normalization converts raw GF scenario output into stable, reviewable comparison material.

It exists to remove execution noise that is unrelated to the grammar behavior under test while preserving every semantically meaningful result.

Normalization supports:

- deterministic gold comparison;
- cross-platform runs;
- stable paths in evidence;
- stable scenario-section boundaries;
- reviewable diffs;
- explicit compatibility changes;
- reproducible release validation.

Normalization is not a repair stage.

It does not reinterpret GF output, correct a grammar, hide a failure or rewrite expected results.

The core rule is:

> Normalize only proven execution noise; preserve all linguistic, grammatical, diagnostic and structural evidence.

---

## 2. Scope

This document governs:

- the relationship between raw and normalized scenario output;
- canonical marker recognition;
- section extraction;
- canonical `.out` serialization;
- newline normalization;
- ANSI-sequence removal;
- trailing horizontal-whitespace removal;
- exact path-token replacement;
- explicitly unstable wrapper metadata;
- unscoped-output handling;
- deterministic comparison with `.gold`;
- normalization-version policy;
- normalization failures;
- gold-update integration;
- required tests;
- anti-drift rules.

This document does not govern:

- `.gfs` command syntax;
- which scenarios are required;
- GF process launching;
- timeouts and cancellation;
- GF command semantics;
- source compilation;
- PGF construction;
- project-specific expected linguistic output;
- approval of gold changes;
- report prose;
- arbitrary user-defined text filters.

---

## 3. Related normative documents

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/gf/GF_OUTPUT_NORMALIZATION.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/validation/SCENARIO_VALIDATION.md
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/VALIDATION_SPEC.md
```

This file owns scenario comparison normalization.

`docs/gf/GF_OUTPUT_NORMALIZATION.md` may describe broader GF diagnostic normalization, but it MUST link here for scenario `.out` and `.gold` semantics rather than defining a competing pipeline.

---

## 4. Terminology

- **RAW STDOUT**: exact stdout bytes captured from the GF process.
- **RAW STDERR**: exact stderr bytes captured from the GF process.
- **RAW EVIDENCE**: raw streams, command, working directory, exit code, timing and process state.
- **MARKER**: stable scenario-emitted boundary identifying one output section.
- **SECTION**: ordered semantic output between one matching begin/end marker pair.
- **UNSCOPED OUTPUT**: non-marker output outside declared sections.
- **NORMALIZER**: the single framework-owned implementation that creates canonical scenario output.
- **CANONICAL OUTPUT**: normalized `.out` text written under the run directory.
- **GOLD**: reviewed canonical expected text stored under `project/validation/gold/`.
- **NORMALIZATION VERSION**: explicit version of rules affecting canonical output.
- **NOISE**: output proven to be operationally unstable and semantically irrelevant.
- **SEMANTIC OUTPUT**: content whose value, spelling, structure, count, punctuation or Unicode form is part of validation evidence.
- **GOLD MATCH**: exact comparison success between compatible canonical output and gold text.

---

## 5. Authority boundaries

### 5.1 GF is authoritative for

- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- abstract trees;
- ambiguity;
- missing-function results;
- GF diagnostics;
- GF prompt and banner behavior.

### 5.2 GF Wordbench is authoritative for

- raw-stream capture;
- marker validation;
- section extraction;
- allowed normalization;
- normalized artifact creation;
- normalization-version identity;
- exact gold comparison;
- diff creation;
- failure classification at the scenario-contract boundary.

### 5.3 The active project is authoritative for

- scenario purpose;
- required sections;
- expected section order;
- expected linguistic content;
- whether a scenario uses gold comparison;
- the reviewed gold file;
- explicit acceptance decisions.

### 5.4 Forbidden authority transfer

The normalizer MUST NOT decide that changed linguistic output is acceptable.

A gold file MUST NOT be updated automatically because normalization or implementation output changed.

---

## 6. Artifact ownership

### 6.1 Raw streams

Owned by:

```text
app/audit/scenario_runner.py
```

Canonical paths:

```text
run_<run-id>/raw/scenarios/<scenario-id>.stdout.txt
run_<run-id>/raw/scenarios/<scenario-id>.stderr.txt
```

Raw streams are immutable after capture.

### 6.2 Normalized output

Owned by:

```text
app/audit/scenario_runner.py
```

Canonical path:

```text
run_<run-id>/raw/scenarios/<scenario-id>.out
```

### 6.3 Gold file

Owned by:

```text
project maintainer
explicit gold-update workflow
```

Canonical path:

```text
project/validation/gold/<scenario-id>.gold
```

### 6.4 Comparison result

Owned by scenario comparison logic operating on:

```text
one canonical `.out`
one compatible `.gold`
```

No report writer may regenerate normalized output or rewrite gold.

---

## 7. Raw evidence is immutable

Normalization MUST occur after raw stdout and stderr are captured.

The normalizer MUST NOT modify:

```text
raw stdout file
raw stderr file
command record
exit code
timeout state
working directory
GF version evidence
```

Every normalized artifact MUST retain a structured reference to its raw source evidence through `ScenarioResult`.

If normalization fails, raw evidence remains valid and available.

A normalization failure MUST NOT delete or overwrite raw streams.

---

## 8. Canonical input stream

### 8.1 v1 source stream

Normalization version `1.0` extracts scenario sections from:

```text
decoded raw stdout
```

Raw stderr is not merged into semantic scenario output.

Reasons:

- stdout is the canonical scenario-result channel;
- stderr may contain diagnostics or platform/tool noise;
- merging streams destroys original ordering guarantees;
- gold comparison should not accidentally depend on diagnostic routing.

### 8.2 Stderr handling

Stderr remains required evidence.

The scenario runner considers stderr when determining:

```text
tool failure
fatal diagnostic
contract failure
scenario status
```

A scenario with matching normalized stdout may still fail because stderr or process state indicates failure.

### 8.3 Diagnostic scenarios

A scenario intended to validate GF diagnostics MUST use a separately documented diagnostic assertion strategy.

It MUST NOT silently switch the canonical semantic normalizer to merged stdout/stderr.

Support for stderr-backed canonical gold would require a new documented normalization profile and contract review.

---

## 9. Decoding policy

### 9.1 Raw bytes

Process capture SHOULD preserve raw bytes or an exact byte-safe file before text decoding.

### 9.2 Canonical encoding

Normalized output uses:

```text
UTF-8 without BOM
```

### 9.3 Decode strategy

The final v1 strategy is:

1. decode stdout as UTF-8;
2. accept and remove one leading UTF-8 BOM;
3. on invalid UTF-8, return `normalization_failure`;
4. preserve raw bytes;
5. do not silently discard or replace undecodable bytes in release validation.

A diagnostic-only mode MAY expose lossy decoded text separately, but it MUST NOT use that text for a passing gold comparison.

### 9.4 Unicode preservation

The normalizer MUST preserve Unicode code points exactly.

It MUST NOT apply:

```text
NFC normalization
NFD normalization
NFKC normalization
NFKD normalization
case folding
accent removal
transliteration
smart-quote replacement
dash replacement
whitespace-category folding
```

Unicode distinctions may be linguistically meaningful.

---

## 10. Raw scenario markers

### 10.1 Canonical marker syntax

A scenario emits exact marker payloads:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
GF_WORDBENCH_END <scenario-id>:<section-id>
```

Example:

```text
GF_WORDBENCH_BEGIN parse:parse-basic
GF_WORDBENCH_END parse:parse-basic
```

### 10.2 Marker identifiers

`scenario-id` and `section-id` MUST:

- be non-empty;
- contain only documented identifier characters;
- be stable;
- be case-sensitive;
- contain no whitespace;
- contain no path separator;
- contain no control character.

Recommended identifier pattern:

```text
[a-z0-9][a-z0-9._-]*
```

### 10.3 Marker identity

The marker scenario ID MUST match the configured scenario ID.

The section ID MUST match one declared section for that scenario.

### 10.4 Marker line recognition

A marker is recognized only when its payload occupies the complete logical output line after:

- newline removal;
- optional exact known GF prompt-prefix removal;
- optional surrounding horizontal whitespace around the marker payload.

Arbitrary text before or after the payload invalidates marker recognition.

### 10.5 Marker preservation

Raw marker identity is preserved by converting each validated pair into canonical section markers.

The normalizer does not retain the literal raw marker line inside section content.

### 10.6 Legacy short markers

Legacy forms without the scenario ID MAY be read only through an explicit compatibility adapter:

```text
GF_WORDBENCH_BEGIN <section-id>
GF_WORDBENCH_END <section-id>
```

Canonical v1 writers MUST emit the full form.

Legacy acceptance MUST be recorded and MUST NOT redefine canonical syntax.

---

## 11. Marker-state rules

### 11.1 Required state machine

The parser operates with these states:

```text
outside section
inside section
completed
invalid
```

### 11.2 Begin marker

A begin marker is valid only when:

- no section is currently open;
- the scenario ID matches;
- the section ID is declared;
- the section ID has not already completed.

### 11.3 End marker

An end marker is valid only when:

- a section is open;
- scenario ID matches the open marker;
- section ID matches the open marker.

### 11.4 Nested sections

Nested sections are prohibited in v1.

A begin marker encountered inside an open section is a contract error.

### 11.5 Duplicate sections

A section ID may appear exactly once unless a future version explicitly defines repeatable sections.

Duplicate section IDs are a contract error.

### 11.6 Missing end marker

A missing end marker invalidates normalized output.

The output MUST NOT pass gold comparison.

### 11.7 End without begin

An unmatched end marker is a contract error.

### 11.8 Order

Section order follows the scenario’s declared order.

If the emitted order differs:

- normalization records the mismatch;
- required scenario validation fails;
- the normalizer MUST NOT reorder sections to conceal the defect.

### 11.9 Completion

Every required section MUST complete.

Optional-section semantics must be declared in scenario configuration.

Absence of an optional section is not equivalent to an empty section.

---

## 12. Canonical output schema

### 12.1 Identity

```text
schema_id: gf-wordbench.scenario-output
schema_version: 1.0
```

This is a canonical text schema.

### 12.2 Path

```text
run_<run-id>/raw/scenarios/<scenario-id>.out
```

### 12.3 Exact structure

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: <scenario-id>
# normalization_version: 1.0
--- BEGIN <section-id> ---
<normalized section content>
--- END <section-id> ---
```

For multiple sections:

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: parse
# normalization_version: 1.0
--- BEGIN parse-basic ---
<content>
--- END parse-basic ---
--- BEGIN parse-ambiguous ---
<content>
--- END parse-ambiguous ---
```

### 12.4 Header rules

The header is exactly three lines in v1:

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: <scenario-id>
# normalization_version: 1.0
```

No timestamp, machine path, duration or GF version appears in the canonical header.

Those values belong in structured scenario evidence.

### 12.5 Section marker rules

Canonical section markers are:

```text
--- BEGIN <section-id> ---
--- END <section-id> ---
```

They are generated by GF Wordbench, not copied verbatim from GF output.

### 12.6 Final newline

A canonical `.out` MUST end with exactly one LF newline after the final end marker.

### 12.7 Empty section

An explicitly completed empty section is represented as:

```text
--- BEGIN empty-section ---
--- END empty-section ---
```

There is no synthetic blank content line between markers.

---

## 13. Canonical gold schema

### 13.1 Identity

```text
schema_id: gf-wordbench.scenario-gold
schema_version: 1.0
```

### 13.2 Path

```text
project/validation/gold/<scenario-id>.gold
```

### 13.3 Exact structure

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: <scenario-id>
# normalization_version: 1.0
--- BEGIN <section-id> ---
<expected normalized content>
--- END <section-id> ---
```

### 13.4 Relationship to `.out`

The gold body and canonical output body use the same:

```text
scenario ID
normalization version
section IDs
section order
section marker format
content normalization rules
```

Only the first identity line differs:

```text
# GF_WORDBENCH_OUTPUT 1.0
# GF_WORDBENCH_GOLD 1.0
```

### 13.5 Gold is already canonical

The comparator MUST NOT run raw-output normalization over the gold file.

It may only:

- decode according to canonical text rules;
- accept CRLF as a compatibility input;
- normalize CRLF to LF for comparison;
- validate the gold schema;
- verify final semantic text.

Running the current normalizer over old gold could hide a stale normalization version and is prohibited.

---

## 14. Normalization pipeline

The v1 pipeline is ordered and deterministic.

```text
raw stdout bytes
      ↓
UTF-8 decode
      ↓
newline canonicalization
      ↓
ANSI control-sequence removal
      ↓
known prompt handling for marker recognition
      ↓
raw marker validation
      ↓
section extraction
      ↓
section-level normalization
      ↓
canonical marker serialization
      ↓
UTF-8/LF `.out` write
      ↓
gold schema validation
      ↓
exact comparison
```

The transformation order is locked.

Changing order may change output and requires review.

---

## 15. Step 1 — newline canonicalization

### 15.1 Allowed conversion

Convert:

```text
CRLF → LF
CR   → LF
```

### 15.2 Scope

Newline conversion applies to decoded stdout before marker parsing.

### 15.3 Preservation

The number and placement of logical line boundaries remain equivalent.

The normalizer MUST NOT:

- join lines;
- wrap lines;
- split long lines;
- collapse consecutive blank lines.

---

## 16. Step 2 — ANSI control-sequence removal

### 16.1 Purpose

Terminal color and cursor controls are platform or environment noise.

### 16.2 Allowed removal

The normalizer MAY remove recognized ANSI terminal control sequences, including documented:

```text
CSI color/style sequences
CSI cursor sequences
OSC title sequences when safely terminated
single-character terminal controls in the supported set
```

### 16.3 Safety

The implementation MUST use a bounded, tested parser or bounded regular expressions.

It MUST NOT remove arbitrary bracketed text.

### 16.4 Raw preservation

The raw stdout retains every original byte.

### 16.5 Post-removal text

Removing an ANSI sequence MUST NOT insert or delete surrounding visible characters.

---

## 17. Step 3 — known prompt handling

### 17.1 Purpose

GF may emit interactive prompt text or echo behavior that varies by invocation mode or version.

### 17.2 Canonical v1 rule

Prompt handling is limited to an explicit compatibility table maintained for supported GF versions.

A known prompt prefix MAY be removed:

- to recognize a marker line;
- from unscoped wrapper noise;
- when the prompt is proven not to be scenario content.

### 17.3 Content safety

Inside a declared semantic section, prompt-like text is preserved by default.

The normalizer MUST NOT strip every occurrence of characters such as:

```text
>
?
gf>
```

### 17.4 Unknown prompt

Unknown prompt text is unscoped or section content according to marker position.

It is not silently discarded.

---

## 18. Step 4 — section extraction

### 18.1 Marker lines

Validated raw marker lines become boundaries and are excluded from section content.

### 18.2 Content range

Section content consists of every logical line after its begin marker and before its matching end marker.

### 18.3 Exact ordering

Content line order is preserved.

### 18.4 Output outside sections

Output outside sections is handled by the unscoped-output policy.

It is never inserted into a semantic section automatically.

### 18.5 Required evidence

The scenario result records at least:

```text
section ID
completed state
start location where available
end location where available
normalization state
```

---

## 19. Unscoped-output policy

### 19.1 Definition

Unscoped output is non-marker stdout outside any declared section.

Examples:

```text
GF banner
prompt
echoed scenario command
unexpected result
debug print
diagnostic text
```

### 19.2 Known wrapper noise

The normalizer MAY discard exact, documented wrapper noise such as:

- a supported GF version banner when the scenario is version-independent;
- a known initial prompt;
- an exact command echo generated by the invocation mechanism;
- framework-owned timing metadata outside semantic sections.

### 19.3 Unknown non-empty unscoped output

Unknown non-whitespace unscoped output MUST be recorded.

For a required gold-backed scenario:

> Unknown unscoped output prevents a clean gold pass.

The scenario is `FAIL` or `ERROR` according to whether output was valid but unexpected or could not be interpreted safely.

### 19.4 Whitespace-only unscoped output

Whitespace-only lines outside sections MAY be ignored.

### 19.5 No hidden section

The normalizer MUST NOT invent an `unscoped` canonical section in schema v1.

Adding such a section would change persisted semantics.

---

## 20. Step 5 — trailing horizontal whitespace

### 20.1 Allowed removal

Remove spaces and tabs at the end of each semantic content line.

### 20.2 Preserved whitespace

Preserve:

- leading whitespace;
- internal spaces;
- internal tabs;
- empty lines;
- line count;
- indentation;
- spacing in linearized strings;
- Unicode whitespace other than explicitly defined ASCII trailing space/tab.

### 20.3 No global trim

The normalizer MUST NOT call a whole-document trim that removes meaningful leading blank lines or indentation.

Only final file-newline handling and per-line trailing ASCII horizontal whitespace are canonicalized.

---

## 21. Step 6 — stable path replacement

### 21.1 Allowed tokens

Normalization version `1.0` supports exactly:

```text
<PROJECT_ROOT>
<RGL_ROOT>
<RUN_DIR>
<GF_EXECUTABLE>
<DURATION_MS>
```

### 21.2 Exact replacement sources

The normalizer receives resolved values from structured run configuration and paths.

It MUST NOT discover roots by guessing from output.

### 21.3 Path tokens

Exact occurrences of these resolved values may be replaced:

| Resolved value | Token |
|---|---|
| project root | `<PROJECT_ROOT>` |
| RGL root | `<RGL_ROOT>` |
| current run directory | `<RUN_DIR>` |
| GF executable path | `<GF_EXECUTABLE>` |

### 21.4 Path forms

For each resolved path, the normalizer may recognize only explicitly generated equivalent forms:

```text
native separator form
forward-slash form
resolved absolute form
documented GF-rendered form
Windows drive-letter case variant
```

It MUST NOT perform unrestricted case-insensitive substring replacement.

### 21.5 Longest-first replacement

Overlapping paths are replaced longest-first.

This prevents a parent root from partially replacing a more specific path.

### 21.6 Boundaries

Path replacement SHOULD verify reasonable textual boundaries to avoid replacing the same character sequence inside unrelated linguistic text.

### 21.7 Source filenames and locations

Replacing a root preserves the remaining relative source identity.

Example:

```text
C:\work\project\lib\GrammarTst.gf:12:4
```

becomes:

```text
<PROJECT_ROOT>/lib/GrammarTst.gf:12:4
```

The normalizer MUST NOT remove:

```text
GrammarTst.gf
line 12
column 4
```

### 21.8 Arbitrary paths

Arbitrary absolute paths not matching an approved resolved root remain unchanged and trigger review if they affect gold stability.

The normalizer MUST NOT replace every Windows or POSIX absolute path generically.

### 21.9 Temporary paths

A temporary path inside the run directory maps through `<RUN_DIR>`.

External system temporary paths are not normalized in v1 unless a future version introduces a documented stable token.

---

## 22. Step 7 — measured duration replacement

### 22.1 Token

```text
<DURATION_MS>
```

### 22.2 Allowed use

A measured duration may be replaced only in a framework-defined metadata pattern known to be unstable.

Example framework-owned text:

```text
duration_ms=143
```

may become:

```text
duration_ms=<DURATION_MS>
```

### 22.3 Forbidden use

The normalizer MUST NOT replace arbitrary numbers followed by `ms` inside linguistic or diagnostic output.

Duration metadata SHOULD normally remain outside semantic sections and in structured `ScenarioResult`.

---

## 23. Timestamp handling

### 23.1 Wrapper timestamps

Framework-owned timestamps outside semantic sections may be omitted as known wrapper noise.

### 23.2 Section timestamps

Timestamp-like text inside a semantic section is preserved in v1.

A scenario that emits unstable timestamps inside required semantic sections is not gold-stable and SHOULD be redesigned.

### 23.3 No arbitrary date regex

The normalizer MUST NOT delete arbitrary date/time patterns from section content.

Such text may be linguistically meaningful.

---

## 24. Version-banner handling

### 24.1 Default

GF version evidence belongs in structured scenario metadata and raw output.

### 24.2 Version-independent scenarios

A known GF banner outside semantic sections MAY be omitted.

### 24.3 Version-sensitive scenarios

A scenario validating GF version behavior must place relevant output inside an explicit semantic section.

The normalizer then preserves it.

### 24.4 Unknown banners

Unknown banner text is unscoped output and follows the unscoped-output policy.

---

## 25. Platform path separators

### 25.1 Root replacements

Approved absolute roots are converted to tokens, and the remaining path uses `/` in canonical output when it is clearly part of the replaced path.

### 25.2 No global slash conversion

The normalizer MUST NOT globally replace:

```text
\ → /
```

Backslashes may be:

- GF syntax;
- escaped string content;
- linguistic output;
- diagnostic punctuation.

### 25.3 Relative path normalization

A known structured relative path emitted by GF Wordbench MAY use `/`.

Arbitrary GF output is preserved.

---

## 26. Content that MUST be preserved

Normalization MUST preserve:

```text
GF error messages
source filenames relevant to diagnosis
line and column locations
abstract trees
concrete trees
linearized strings
parse alternatives
ambiguity counts
missing-function lists
generation results
morphology results
grammar introspection results
category names
function names
module names
language-specific Unicode
diacritics
combining marks
capitalization
punctuation
quotation marks
token boundaries
leading indentation
internal whitespace
blank-line structure
section order
evidence that a required section did not complete
```

When uncertain whether text is noise or semantic, preserve it.

---

## 27. Forbidden normalization

The following are prohibited:

```text
sorting parse alternatives
sorting generated sentences
sorting trees
deduplicating repeated lines
collapsing repeated spaces
collapsing blank lines
case folding
lowercasing
uppercasing
accent removal
Unicode normalization
transliteration
punctuation normalization
quote normalization
decimal-number replacement
generic integer replacement
generic path removal
generic timestamp removal
generic version-number removal
source-filename removal
line/column removal
diagnostic paraphrasing
error-message suppression
removal of missing markers
inserting expected output
repairing malformed output
using gold content to transform actual output
```

Gold must never influence normalization of actual output.

---

## 28. Canonical serialization rules

Canonical `.out` and `.gold` text uses:

```text
UTF-8 without BOM
LF newlines
no trailing spaces or tabs
one final newline
case-sensitive identifiers
deterministic section order
```

### 28.1 No extra separator line

There is no mandatory blank line between sections.

Example:

```text
--- END first ---
--- BEGIN second ---
```

### 28.2 Section content ending

If a section contains content, the final content line is followed by LF before the end marker.

### 28.3 Empty final content line

An intentional blank line at the end of semantic content is meaningful and preserved as an empty content line before the end marker.

This differs from trailing horizontal whitespace, which is removed.

---

## 29. Comparison algorithm

### 29.1 Preconditions

Before comparison:

- actual `.out` schema is valid;
- gold schema is valid;
- scenario IDs match;
- normalization versions match;
- required sections completed;
- section identifiers and order match project expectations;
- no blocking unexpected unscoped output exists;
- process/scenario state permits comparison.

### 29.2 Gold compatibility read

The gold reader may convert:

```text
CRLF → LF
CR → LF
```

It MUST NOT apply current raw-output normalization rules to gold content.

### 29.3 Identity-line comparison

The first header line differs by artifact type.

For semantic comparison, the comparator validates each identity line and compares a canonical projection where:

```text
OUTPUT identity
GOLD identity
```

are treated as corresponding artifact roles.

All other canonical text is compared exactly.

### 29.4 Exact content comparison

After role-aware header validation and newline compatibility:

```text
scenario ID must match exactly
normalization version must match exactly
section markers must match exactly
section content must match exactly
```

### 29.5 No fuzzy comparison

The comparator MUST NOT use:

```text
edit-distance thresholds
case-insensitive comparison
trimmed-line comparison beyond canonical rules
unordered comparison
locale-aware collation
semantic similarity
AI judgment
```

### 29.6 Result

```text
gold_match = true
gold_match = false
gold_match = null
```

Use `null` only when no gold comparison applies.

An error reading or interpreting gold is not `false`; it is a scenario contract error.

---

## 30. Diff generation

### 30.1 Purpose

A mismatch produces reviewable evidence.

### 30.2 Format

A unified textual diff SHOULD be used.

Recommended labels:

```text
expected: project/validation/gold/<scenario-id>.gold
actual: run_<run-id>/raw/scenarios/<scenario-id>.out
```

### 30.3 Diff source

The diff compares canonical semantic projections, not raw stdout/stderr.

Raw evidence remains separately linked.

### 30.4 Limits

Large diffs MAY be bounded in human reports.

The complete diff SHOULD be stored as an artifact when generated.

Truncation MUST be explicit.

### 30.5 No automatic acceptance

A diff is evidence, not approval.

---

## 31. Failure semantics

### 31.1 `FAIL`

Use scenario validation `FAIL` when execution completed and interpretable output violates expected behavior.

Examples:

```text
required marker absent
required section absent
section order incorrect
unexpected unscoped semantic output
gold mismatch
```

### 31.2 `ERROR`

Use `ERROR` when GF Wordbench cannot safely interpret or produce the normalization contract.

Examples:

```text
invalid UTF-8
duplicate marker
nested marker
unmatched end marker
mismatched scenario ID in marker
normalizer internal failure
normalized artifact write failure
invalid gold schema
normalization-version incompatibility
```

### 31.3 `SKIPPED`

Use `SKIPPED` when the scenario or gold comparison was intentionally not executed under policy.

### 31.4 Process failure precedence

A process timeout, launch failure or fatal GF failure remains visible even if partial stdout can be normalized.

A partial normalized artifact MAY be retained for evidence, but it MUST NOT turn the scenario into `OK`.

### 31.5 Error kind

Recommended scenario error kinds include:

```text
SCRIPT
CONFIG
IO
TOOL
TIMEOUT
INTERNAL
```

`normalization_failure` and `gold_mismatch` are diagnostic reasons, not new causal diagnostic classes.

---

## 32. Normalization versioning

### 32.1 Version format

```text
MAJOR.MINOR
```

Current version:

```text
1.0
```

### 32.2 Independent identity

Normalization version is independent from:

```text
GF version
GF Wordbench package version
scenario schema version
project version
gold review date
```

### 32.3 Output-affecting change

Any rule change that can change canonical output requires a normalization-version change.

Examples:

```text
new path replacement
changed prompt handling
changed marker recognition
changed whitespace behavior
changed ANSI handling
changed section ordering
changed unscoped-output policy
changed token format
```

### 32.4 Major change

Increment major version when changing:

```text
canonical header
canonical section syntax
semantic preservation rules
comparison semantics
stream source
Unicode policy
path-token meanings
```

### 32.5 Minor change

Increment minor version for a compatible, bounded output rule addition whose impact is reviewed.

Even a minor change requires reviewing all affected gold files.

### 32.6 No-output change

Internal refactoring with byte-for-byte equivalent canonical output does not require a normalization-version change.

It requires regression tests.

### 32.7 Exact compatibility

A `.gold` with a different normalization version MUST NOT pass.

The system may provide an explicit migration workflow.

It MUST NOT silently reinterpret the gold.

---

## 33. Normalization profile policy

The project contract may name a normalization profile.

Version `1.0` defines one canonical profile:

```text
canonical-v1
```

It maps to:

```text
normalization_version = 1.0
source stream = stdout
marker syntax = full scenario-and-section markers
comparison = exact
```

No plugin registry or arbitrary project-provided normalizer is supported in v1.

A future profile requires:

- a distinct documented purpose;
- stable identifier;
- explicit version;
- security review;
- persistence review;
- tests;
- project-lock update.

---

## 34. Gold-update integration

### 34.1 Explicit command

Canonical operation:

```text
gf-wordbench gold update <scenario-id>
```

### 34.2 Workflow

The operation MUST:

1. execute the configured scenario;
2. preserve raw stdout and stderr;
3. normalize with the configured version;
4. validate all required markers;
5. validate absence of blocking unscoped output;
6. create the candidate canonical output;
7. compare with existing gold when present;
8. show or save the diff;
9. require explicit approval or approved CI policy;
10. transform the artifact identity from `OUTPUT` to `GOLD`;
11. write the gold atomically;
12. preserve normalization version;
13. record the change in version control.

### 34.3 Prohibitions

A normal audit MUST NOT:

- create a missing gold;
- update a mismatching gold;
- migrate gold;
- change its newline format;
- change its normalization version.

### 34.4 Empty gold

An empty semantic expectation is valid only when the project explicitly documents it.

The gold still contains header and section markers.

---

## 35. Atomic writes

Normalized `.out` and updated `.gold` files SHOULD use atomic replacement.

Canonical sequence:

1. write sibling temporary file;
2. flush and close;
3. validate canonical schema;
4. replace destination atomically;
5. clean temporary file on failure where safe.

A failed write MUST NOT destroy the last valid gold.

---

## 36. Determinism

Equivalent inputs produce equivalent canonical output when all of these match:

```text
raw stdout bytes
normalization version
scenario ID
declared sections
resolved replacement paths
GF compatibility prompt table
normalizer implementation semantics
```

Determinism requires:

- fixed transformation order;
- fixed token vocabulary;
- fixed marker grammar;
- fixed section ordering;
- no locale-dependent case conversion;
- no current-time values;
- no random identifiers;
- no filesystem enumeration inside normalization;
- no environment lookup outside resolved inputs.

---

## 37. Idempotence

### 37.1 Line-level transformations

Allowed line-level transformations SHOULD be idempotent.

Applying them twice must not further alter text.

### 37.2 Canonical artifact validation

Canonical `.out` text is validated, not treated as raw stdout.

The raw normalizer need not accept canonical markers as raw scenario markers.

### 37.3 Gold

Gold is validated as canonical gold and compared.

It is never recursively normalized.

---

## 38. Path-replacement safety

### 38.1 Replacement ordering

Resolved paths are sorted by decreasing text length before replacement.

### 38.2 Duplicate roots

Equivalent resolved roots map consistently.

Conflicting token ownership is a configuration error.

Example conflict:

```text
PROJECT_ROOT == RGL_ROOT
```

The implementation must define one explicit precedence or reject the ambiguous configuration.

Recommended precedence:

```text
GF_EXECUTABLE
RUN_DIR
PROJECT_ROOT
RGL_ROOT
```

after longest-first ordering.

### 38.3 Replacement metadata

The scenario result SHOULD record which token replacements occurred.

It MUST NOT record secrets.

### 38.4 Token collision in linguistic text

Existing literal text such as:

```text
<PROJECT_ROOT>
```

inside semantic output is preserved.

The normalizer does not escape or reinterpret pre-existing tokens.

Tests must distinguish original token text from replaced path text through raw evidence.

---

## 39. Output-size limits

Scenario output may be large.

GF Wordbench SHOULD define:

```text
maximum raw capture size
maximum normalized output size
maximum diff size
```

### 39.1 Raw truncation

Raw evidence truncation, when necessary, MUST be explicit.

A truncated required scenario MUST NOT pass exact gold comparison unless the project contract explicitly proves truncation occurs outside all semantic sections, which is not supported in canonical v1.

### 39.2 Normalized truncation

Normalized semantic output MUST NOT be silently truncated.

Exceeding the limit is a scenario error.

### 39.3 Bounded generation

Generation scenarios SHOULD be bounded at the GF command level rather than normalized after runaway output.

---

## 40. Security

The normalizer processes untrusted text.

It MUST:

- avoid shell execution;
- avoid evaluating output;
- avoid interpreting ANSI as terminal commands;
- use bounded parsers;
- reject control-character abuse where required;
- bound output and diff size;
- validate scenario and section identifiers;
- contain writes inside run-owned paths;
- avoid environment dumps;
- avoid exposing secrets in normalized reports;
- preserve raw evidence under retention policy.

Raw output displayed in terminals or HTML MUST be escaped by the presentation layer.

---

## 41. Cross-platform requirements

The v1 normalizer MUST behave consistently on:

```text
Windows
Linux
macOS where supported
```

Required cases:

- CRLF and LF;
- Windows drive paths;
- POSIX paths;
- paths with spaces;
- Unicode paths;
- ANSI and non-ANSI output;
- differing path separators;
- stdout files with or without final newline.

Canonical output remains UTF-8 with LF on every platform.

---

## 42. Implementation ownership

The scenario runner owns the operation:

```text
raw stdout → canonical `.out`
```

A private helper or dedicated module MAY implement normalization if architecture documents and contracts identify it as the single owner.

Allowed future extraction:

```text
app/audit/output_normalization.py
```

Only when:

- `COMPONENT_MAP.md` is updated;
- `INTERFILE_CONTRACT_LOCK.md` is updated;
- scenario runner remains the orchestrating owner;
- gold comparison uses the same canonical service;
- duplicate implementations are removed.

---

## 43. No duplicate normalizer

The following are prohibited:

```text
one normalizer in scenario_runner
another normalizer in gold comparison
another normalizer in reports
a project-specific copy
a GUI-only normalizer
test fixtures with independent production rules
```

Tests may implement small independent assertions, but not a second production normalizer.

One normalization service defines canonical output.

---

## 44. Structured result requirements

`ScenarioResult` records at least:

```text
scenario_id
stdout_path
stderr_path
normalized_output_path
gold_path
gold_match
sections
status
error_kind
primary_message
```

Normalization-related structured evidence SHOULD include:

```text
normalization_version
normalization_profile
normalization_status
marker errors
unscoped-output state
replacement tokens used
normalized size
normalized SHA-256
gold diff path
```

Adding persisted fields requires schema review.

---

## 45. Reporting

### 45.1 `summary.json`

Machine output references:

```text
raw stdout
raw stderr
normalized `.out`
gold file
gold result
sections
normalization state
```

### 45.2 `summary.md`

Human summary SHOULD show:

```text
scenario status
normalization version
completed sections
gold result
paths to raw and normalized evidence
primary normalization failure
```

### 45.3 `AI_READY.md`

AI evidence SHOULD distinguish:

```text
raw tool output
normalized comparison output
gold expectation
diff
normalization rules
```

### 45.4 No report-time normalization

Report writers consume the normalized artifact.

They MUST NOT rerun or reinterpret the normalization pipeline.

---

## 46. Unit tests

Recommended file:

```text
tests/unit/audit/test_output_normalization.py
```

Required v1 tests:

### 46.1 Encoding and newline

```text
UTF-8
UTF-8 BOM
invalid UTF-8
LF
CRLF
CR
missing final newline
Unicode preservation
combining-character preservation
no NFC conversion
```

### 46.2 Markers

```text
one valid section
multiple valid sections
scenario ID mismatch
unknown section
duplicate section
nested section
end without begin
missing end
missing begin
wrong end ID
wrong section order
optional section absent
empty section
marker-like text inside content
known prompt before marker
unknown prefix before marker
```

### 46.3 Whitespace

```text
trailing spaces
trailing tabs
leading indentation
internal multiple spaces
internal tabs
consecutive blank lines
intentional final blank content line
```

### 46.4 ANSI

```text
color sequence
reset sequence
cursor sequence
OSC sequence
malformed escape sequence
visible bracketed text preserved
```

### 46.5 Paths

```text
project root native form
project root slash form
RGL root
run directory
GF executable
overlapping roots
path with spaces
Unicode path
Windows drive-letter case
unrelated absolute path preserved
source filename and line preserved
literal token text preserved
```

### 46.6 Wrapper noise

```text
known banner outside sections
unknown banner outside sections
whitespace outside sections
known prompt outside sections
unexpected output after final marker
timestamp inside semantic section preserved
duration token only in framework metadata
```

### 46.7 Canonical serialization

```text
exact three-line header
canonical section markers
deterministic order
UTF-8 without BOM
LF output
exactly one final newline
no trailing horizontal whitespace
```

### 46.8 Comparison

```text
exact match
content mismatch
section mismatch
scenario mismatch
normalization-version mismatch
invalid gold header
CRLF gold compatibility
missing gold
empty gold policy
role-aware OUTPUT versus GOLD identity
no fuzzy match
```

---

## 47. Contract tests

Recommended file:

```text
tests/contracts/test_normalization_contract.py
```

Contract tests MUST verify:

- raw stdout remains unchanged;
- raw stderr remains unchanged;
- one owner produces normalized output;
- gold comparison does not duplicate normalization;
- reports do not normalize;
- canonical token vocabulary matches `PERSISTED_SCHEMA_LOCK.md`;
- canonical header matches the persisted schema;
- marker identity matches project contracts;
- missing markers cannot pass;
- linguistically meaningful output is preserved;
- Unicode distinctions are preserved;
- normal validation never writes gold;
- normalization version is explicit;
- version mismatch cannot pass;
- output path comes from `RunPaths`;
- normalized output references raw evidence;
- output-affecting change requires gold review.

---

## 48. Property tests

Recommended bounded properties:

```text
normalization is deterministic
line-level transformations are idempotent
Unicode code points survive unless part of an exact allowed replacement
section content order is preserved
raw files remain byte-identical
all canonical section starts have matching ends
all canonical IDs come from declared IDs
no canonical output contains CR
no canonical line ends in space or tab
canonical output ends in LF
path replacement never escapes token vocabulary
```

Property tests MUST be bounded for time and memory.

---

## 49. Integration tests with GF

A minimal real-GF fixture SHOULD verify:

```text
marker emission
known GF prompt handling
stdout/stderr separation
parse output preservation
linearization preservation
Unicode preservation
ambiguity-count preservation
missing-function preservation
cross-platform path replacement
gold match
gold mismatch
nonzero exit with partial output
supported GF version banners
```

Tests requiring GF are marked separately and skippable when no compatible GF installation exists.

---

## 50. Gold migration

A normalization-version migration is explicit.

Canonical operation may be:

```text
gf-wordbench gold migrate --from 1.0 --to 1.1
```

A migration MUST:

1. list affected gold files;
2. preserve originals;
3. run or load traceable source evidence;
4. generate candidate canonical output;
5. show diffs;
6. require review;
7. write atomically;
8. update normalization-version headers;
9. record migration notes;
10. remain separate from normal validation.

Blind header-only version replacement is prohibited when output semantics changed.

---

## 51. Compatibility with GF versions

Known GF prompt and banner behavior may vary by version.

GF Wordbench maintains compatibility data in:

```text
docs/gf/GF_VERSION_COMPATIBILITY.md
```

A compatibility adapter may affect:

```text
known prompt recognition
known wrapper banner recognition
path rendering variants
ANSI behavior
```

It MUST NOT change semantic preservation rules by GF version.

An unknown newer GF version may produce unrecognized unscoped output.

Strict release validation should fail rather than silently broaden normalization.

---

## 52. Drift indicators

Probable normalization drift exists when:

- raw output changes after normalization;
- stdout and stderr are merged silently;
- marker syntax differs between scenario docs and runner;
- canonical `.out` header differs from schema lock;
- token vocabulary differs from schema lock;
- runner and comparator normalize independently;
- a report regenerates `.out`;
- Unicode normalization appears;
- parse alternatives are reordered;
- duplicate lines disappear;
- blank lines collapse;
- source locations vanish;
- arbitrary timestamps are removed;
- arbitrary paths are removed;
- unknown unscoped output is ignored;
- a new GF banner is silently allowlisted;
- gold passes under a different normalization version;
- normal validation rewrites gold;
- a gold update occurs without diff review;
- output-affecting rules change without version update;
- a new project-provided regex alters canonical output;
- a failure marker is normalized away;
- truncated output passes;
- a path token replaces unrelated linguistic text.

Any drift indicator requires contract review.

---

## 53. Change checklist

```text
[ ] normalization version reviewed
[ ] canonical output schema reviewed
[ ] canonical gold schema reviewed
[ ] raw evidence preservation reviewed
[ ] stdout/stderr boundary reviewed
[ ] marker grammar reviewed
[ ] section ordering reviewed
[ ] unscoped-output policy reviewed
[ ] Unicode preservation reviewed
[ ] newline rules reviewed
[ ] whitespace rules reviewed
[ ] ANSI rules reviewed
[ ] prompt compatibility reviewed
[ ] path-token vocabulary reviewed
[ ] source-location preservation reviewed
[ ] semantic output preservation reviewed
[ ] comparison algorithm reviewed
[ ] diff behavior reviewed
[ ] gold-update workflow reviewed
[ ] persisted schema updated if required
[ ] interfile contracts updated if required
[ ] project contracts reviewed
[ ] unit tests updated
[ ] contract tests updated
[ ] integration tests updated
[ ] affected gold files reviewed
[ ] migration note added
[ ] this document updated
```

---

## 54. Implementation checklist

A conforming v1 implementation satisfies:

```text
[ ] captures stdout and stderr separately
[ ] preserves raw streams
[ ] uses stdout as canonical section source
[ ] decodes strict UTF-8
[ ] converts CRLF/CR to LF
[ ] removes only recognized ANSI controls
[ ] recognizes full scenario-and-section markers
[ ] rejects nested and duplicate markers
[ ] verifies required section completion
[ ] records unexpected unscoped output
[ ] removes only trailing ASCII space/tab
[ ] preserves leading and internal whitespace
[ ] preserves Unicode code points exactly
[ ] replaces only approved exact roots
[ ] uses the five locked tokens
[ ] preserves filenames and line/column data
[ ] writes canonical three-line header
[ ] writes canonical section markers
[ ] writes one final LF
[ ] validates gold schema separately
[ ] requires exact normalization-version match
[ ] compares exactly without fuzzy logic
[ ] writes reviewable mismatch evidence
[ ] never updates gold during normal validation
[ ] has one production normalizer
[ ] reports consume existing artifacts
```

---

## 55. Final enforcement rule

Normalization is allowed to remove instability, not meaning.

Therefore:

> A normalization rule is valid only when the removed or replaced text is explicitly identified as operational noise, the raw evidence remains immutable, the transformation is deterministic and versioned, and no linguistic result, GF diagnostic, structural marker or failure evidence is weakened.
