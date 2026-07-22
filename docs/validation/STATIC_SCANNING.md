# GF Wordbench — Static Scanning

**Document ID:** `GF-WB-VALIDATION-STATIC-SCANNING`  
**Status:** Normative  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\validation\STATIC_SCANNING.md`  
**Applies to:** Built-in heuristic inspection of selected GF source files  
**Owner:** GF Wordbench maintainers  
**Primary implementation owner:** `app/audit/scanner.py`  
**Public contract:** `IFC-AUDIT-004`  
**Persisted fields:** `ScanCounts`, `file_results[].scan_counts`, `file_results[].scan_log_path`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

Static scanning is GF Wordbench’s fast, deterministic inspection stage for known source patterns that are useful to surface before or alongside GF compilation.

It exists to detect:

- suspicious GF notation that often indicates an accidental slash/arrow mismatch;
- string-based runtime pattern matching that should be reviewed;
- string-pattern blocks that appear to lack an explicit `Str` pattern type;
- trailing whitespace;
- future narrowly defined patterns that meet the admission criteria in this document.

Static scanning produces:

```text
structured counts
+ a per-file evidence log
```

It does not decide whether GF source is grammatically, typologically or semantically correct.

The core rule is:

> Static findings are heuristic evidence; GF compilation and GF runtime behavior remain authoritative.

---

## 2. Scope

This document governs:

- selection-independent scanning of one GF source file;
- UTF-8 source reading;
- comment removal for analysis;
- string-literal masking;
- brace-balanced block inspection;
- built-in scan-rule identities;
- stable `ScanCounts` meanings;
- source-location reporting;
- per-file scan-log creation;
- deterministic behavior;
- error handling;
- performance limits;
- integration with file results and reports;
- tests required for scanner changes;
- controlled admission of new scan rules.

This document does not govern:

- which files are selected;
- GF command construction;
- GF syntax or type checking;
- dependency resolution;
- compilation status;
- direct/downstream failure classification;
- `.gfs` scenario execution;
- gold comparison;
- report layout beyond the scanner-owned log;
- project-specific morphology or syntax correctness;
- arbitrary lint plugins;
- source rewriting or automatic repair.

---

## 3. Position in the validation pipeline

Canonical stage relationship:

```text
file selection
      ↓
source fingerprint
      ↓
static scan
      ↓
GF compilation
      ↓
diagnostic classification
      ↓
result aggregation
      ↓
reports
```

Static scanning and compilation are separate stages.

They may both inspect the same source file, but they answer different questions:

| Stage | Question |
|---|---|
| Static scan | Does the text contain a known suspicious pattern? |
| GF compilation | Does GF accept and compile the source under the resolved project configuration? |
| Classification | Is a failure direct, downstream, ambiguous, noise or skipped? |
| Scenario validation | Does the compiled grammar exhibit required runtime behavior? |

A scan finding MUST remain visible even when compilation succeeds.

A successful scan MUST NOT imply compilation success.

---

## 4. Authority boundaries

### 4.1 GF is authoritative for

- GF lexical and syntactic validity;
- type checking;
- module resolution;
- pattern legality;
- concrete-syntax compatibility;
- `.gfo` production;
- `.pgf` construction;
- runtime grammar behavior;
- GF diagnostics.

### 4.2 The scanner is authoritative for

- whether each built-in textual rule matched;
- how many matching units were counted;
- which source ranges were logged;
- where the per-file scan log was written;
- the stable meaning of each `ScanCounts` field.

### 4.3 The scanner is not authoritative for

- whether matched source is invalid GF;
- whether a match is a release blocker;
- whether an unmatched source is safe;
- whether a compile failure is direct or downstream;
- whether a linguistic implementation is correct;
- whether a gold change is acceptable.

---

## 5. Public interfile contract

The public scanner entry point is:

```python
scan_file(
    file_path: Path,
    run_config: RunConfig,
    run_paths: RunPaths,
) -> tuple[ScanCounts, Path]
```

### 5.1 Request

The caller supplies:

```text
one selected GF source file
resolved run configuration
resolved run paths
```

The scanner MUST NOT perform file selection.

### 5.2 Response

The scanner returns:

```text
ScanCounts
path to the per-file scan log
```

The returned log path MUST refer to a file created by the scanner when scanning completes successfully.

### 5.3 Side effects

Allowed:

```text
create parent scan-log directory
write one run-owned scan log
read the source file
```

Prohibited:

```text
modify the source
invoke GF
write summary reports
write compilation logs
classify dependency cascades
update project configuration
update gold files
```

### 5.4 Failure behavior

A source-read or scan-log-write failure MUST be distinguishable from a completed scan with zero findings.

The orchestrator decides how a scanner I/O failure enters the containing `FileResult`.

The scanner MUST NOT silently return zero counts after an I/O failure.

---

## 6. Core data model

Canonical scan counts:

```python
ScanCounts(
    single_slash_eq=0,
    double_slash_dash=0,
    runtime_str_match=0,
    untyped_case_str_pat=0,
    untyped_table_str_pat=0,
    trailing_spaces=0,
)
```

### 6.1 Invariants

Every field MUST:

- be an integer;
- be non-negative;
- have one stable meaning;
- count the unit defined in the rule registry;
- remain independent from compilation status;
- serialize deterministically;
- retain its name unless a versioned schema migration is provided.

### 6.2 Counts versus findings

`ScanCounts` is the stable public summary.

Internally, the scanner may represent individual findings with structured objects such as:

```text
rule ID
field name
source path
start line
end line
excerpt
message
```

Internal finding objects are recommended for implementation clarity, but they MUST NOT create a competing public schema without updating the model and persisted-schema lock.

### 6.3 Zero findings

A zero-valued `ScanCounts` means:

```text
the configured built-in rules completed
and found no matching units
```

It does not mean:

```text
the source is valid GF
the source compiles
the source is linguistically correct
the source is release-ready
```

---

## 7. Rule identity model

Every built-in rule has:

```text
stable rule ID
stable ScanCounts field
defined matching unit
defined source view
defined exclusions
defined default interpretation
required tests
```

Canonical IDs use:

```text
SCAN-<DOMAIN>-<NUMBER>
```

Current domains:

```text
NOTATION
RUNTIME
PATTERN
STYLE
```

Rule IDs are stable even when implementation details change.

A retired rule ID MUST NOT be reused for unrelated behavior.

---

## 8. Canonical rule registry

| Rule ID | `ScanCounts` field | Count unit | Default interpretation |
|---|---|---|---|
| `SCAN-NOTATION-001` | `single_slash_eq` | matching source line | suspicious single-backslash before `=>` |
| `SCAN-NOTATION-002` | `double_slash_dash` | matching source line | suspicious double-backslash before `->` |
| `SCAN-RUNTIME-001` | `runtime_str_match` | matching brace-balanced `case` block | runtime string-literal matching on a `.s` expression |
| `SCAN-PATTERN-001` | `untyped_case_str_pat` | matching brace-balanced `case` block | string concatenation pattern without explicit `: Str >` form |
| `SCAN-PATTERN-002` | `untyped_table_str_pat` | matching brace-balanced `table` block | string concatenation pattern without explicit `: Str >` form |
| `SCAN-STYLE-001` | `trailing_spaces` | source line ending in space or tab | formatting issue |

These six rules form the final v1 scanner nucleus.

No language-specific rule is part of the framework nucleus.

---

# 9. Source views

Rules do not all inspect the same text representation.

The scanner derives three aligned views from one source read:

```text
original lines
comment-stripped lines with string contents retained
comment-stripped lines with string contents masked
```

Line count and character alignment SHOULD be preserved where practical.

### 9.1 Original view

Used for:

- excerpts;
- line numbering;
- trailing-whitespace detection;
- human evidence.

### 9.2 Comment-stripped view

Used when a rule must observe string content but ignore comments.

Examples:

```text
runtime string-literal branch detection
string concatenation pattern detection
```

### 9.3 String-masked view

Used when a rule must inspect code structure without matching syntax-like text inside strings.

Examples:

```text
slash/arrow notation detection
case/table structural detection
brace balancing
```

A rule MUST explicitly choose its source view.

---

## 10. Source reading

### 10.1 Canonical encoding

GF Wordbench source scanning uses:

```text
UTF-8
```

The scanner SHOULD read strict UTF-8 first.

For documented legacy compatibility, it MAY accept:

```text
UTF-8 with BOM
```

### 10.2 Decoding errors

Decoding behavior MUST be explicit.

Preferred final policy:

1. try UTF-8;
2. accept UTF-8 BOM;
3. on invalid bytes, return a scanner I/O/encoding error;
4. preserve evidence about the decoding failure.

Silently replacing invalid bytes can change pattern meaning and SHOULD NOT be the final strict behavior.

A non-strict diagnostic mode MAY use replacement decoding only when the result clearly records that source text was lossy.

### 10.3 Newlines

The scanner MUST support:

```text
LF
CRLF
final newline present
final newline absent
```

Line numbers are one-based.

### 10.4 Empty files

An empty readable file is valid scanner input.

It produces:

```text
all counts = 0
an existing scan log
```

### 10.5 File size

The scanner SHOULD enforce a configurable or framework-owned maximum source size to prevent accidental memory exhaustion.

When the maximum is exceeded:

- scanning fails explicitly;
- compilation policy remains independent;
- the source is not partially scanned as though complete.

The limit MUST be high enough for realistic GF modules and covered by tests.

---

## 11. GF-aware lexical masking

The scanner is not a complete GF lexer.

It implements the minimum lexical state needed to prevent obvious false matches in comments and string literals.

### 11.1 Supported lexical states

```text
code
line comment
block comment
string literal
```

### 11.2 Line comments

GF line comments begin with:

```text
--
```

Outside a string or block comment, the remainder of the physical line is masked.

### 11.3 Block comments

GF block comments use:

```text
{-
...
-}
```

Block-comment state continues across physical lines.

Comment content is replaced by spaces in derived views.

The final implementation MUST document and test its behavior for nested block-comment markers before claiming nested-comment support.

It MUST NOT accidentally treat comment text as executable source.

### 11.4 String literals

String boundaries use double quotes.

The masker MUST correctly handle:

```text
ordinary string contents
backslash escape sequences supported by the scanner policy
GF doubled quote syntax `""`
comment markers inside strings
braces inside strings
arrow-like text inside strings
```

Example source text that MUST NOT trigger notation rules:

```gf
oper example = "\x => x" ;
```

Example GF text containing doubled quotes MUST keep string state coherent:

```gf
oper example = "case x of { ""a"" => y }" ;
```

### 11.5 State preservation

A line-comment ends at the physical line boundary.

A block comment may continue to the next line.

A string literal is expected to close according to the supported GF lexical rules.

Malformed or unterminated lexical constructs SHOULD produce a scanner diagnostic rather than silently changing interpretation of the remaining file.

### 11.6 Alignment

Masking SHOULD replace ignored characters with spaces instead of deleting them.

This preserves:

- physical line numbers;
- approximate column positions;
- brace alignment;
- excerpt correspondence.

---

# 12. Structural block detection

Three rules inspect `case` or `table` blocks.

The scanner uses a lightweight brace-balancing strategy after comments and string contents have been masked.

### 12.1 Start detection

Structural start patterns are recognized only in code-visible text.

Examples:

```gf
case expression of {
table {
```

The scanner MAY support a multi-line `case` header.

Example:

```gf
case
  expression
of {
```

Support for a multi-line header MUST be bounded to avoid unbounded concatenation.

### 12.2 Brace balancing

After a start is found:

1. inspect the string-masked structural view;
2. count `{` and `}`;
3. stop when the opening block returns to depth zero;
4. preserve the physical start and end lines;
5. inspect the corresponding comment-stripped block text for string-pattern rules.

Braces inside comments or string contents MUST NOT affect depth.

### 12.3 Unbalanced blocks

When no balanced end is found:

- the scanner MUST NOT claim a complete block match silently;
- it SHOULD emit a scanner diagnostic;
- it MAY inspect only the bounded available range in diagnostic mode;
- GF compilation remains responsible for authoritative syntax failure.

### 12.4 Nested blocks

Nested braces are counted.

A nested `case` or `table` may be discovered as part of the containing block.

The scanner MUST define whether a nested block is counted independently.

Final v1 policy:

> Each traversal counts the outer block selected by the rule and advances past its balanced end; nested blocks are not additionally counted during that same traversal.

This keeps counts deterministic and prevents accidental double counting.

A future independent nested-block count would change rule semantics and requires a contract review.

---

# 13. `SCAN-NOTATION-001` — suspicious single slash before `=>`

## 13.1 Purpose

Detect a line containing a single backslash followed later by `=>`, when no `->` appears first in the relevant expression segment.

Typical suspicious form:

```gf
oper bad = \x => x ;
```

## 13.2 Count unit

```text
one physical source line
```

A line is counted at most once for this rule.

## 13.3 Source view

```text
comment-stripped, string-masked
```

## 13.4 Exclusions

Do not count:

- text in line comments;
- text in block comments;
- text in string literals;
- a double backslash;
- the intended combination when `->` appears before the relevant `=>`;
- an unmatched sequence outside the rule’s bounded statement segment.

## 13.5 Interpretation

This rule indicates likely notation confusion.

It does not assert that GF rejects the line.

## 13.6 Evidence

Log:

```text
rule ID
line number
trimmed original line
```

---

# 14. `SCAN-NOTATION-002` — suspicious double slash before `->`

## 14.1 Purpose

Detect a line containing a double backslash followed later by `->`, when no `=>` appears first in the relevant expression segment.

Typical suspicious form:

```gf
oper bad = \\x -> x ;
```

## 14.2 Count unit

```text
one physical source line
```

## 14.3 Source view

```text
comment-stripped, string-masked
```

## 14.4 Exclusions

Do not count:

- comments;
- strings;
- the intended combination when `=>` appears first in the relevant segment;
- a single backslash;
- a second occurrence on the same line as an additional count.

## 14.5 Interpretation

This is a notation warning, not a compiler verdict.

---

# 15. `SCAN-RUNTIME-001` — runtime string match on `.s`

## 15.1 Purpose

Detect a `case` block whose head selects an expression ending in or containing `.s` and whose branches contain a string-literal pattern.

Representative form:

```gf
case x.s of {
  "abc" => foo ;
  _     => bar
}
```

## 15.2 Count unit

```text
one brace-balanced case block
```

## 15.3 Required conditions

All must hold:

```text
case head detected
`of {` detected
case-head expression includes `.s`
balanced block located
block contains a string-literal branch followed by `=>`
```

## 15.4 Source views

Use:

```text
string-masked view for structure and brace balancing
comment-stripped view for literal-branch detection
```

## 15.5 Interpretation

The rule surfaces runtime matching on realized string material for review.

It does not declare the construct invalid.

The project may document legitimate uses.

## 15.6 Known limitations

The lightweight detector may not fully understand:

- complex record projection syntax;
- macros or aliases around `.s`;
- string patterns expressed through named constants;
- equivalent runtime matching without direct literals;
- lexical constructs outside the supported masker.

These limitations MUST be documented rather than hidden.

---

# 16. `SCAN-PATTERN-001` — untyped `case` string pattern

## 16.1 Purpose

Detect a `case` block containing concatenation-style string patterns such as:

```gf
_ + "s"
"s" + _
```

when the block does not contain an explicit pattern type form matching:

```text
: Str >
```

Representative suspicious form:

```gf
case stem of {
  _ + "s" => mkN stem ;
  _       => mkN stem
}
```

## 16.2 Count unit

```text
one brace-balanced case block
```

## 16.3 Source views

Use:

```text
string-masked view for block structure
comment-stripped view for string-pattern and type-marker inspection
```

## 16.4 Match conditions

Count when:

```text
case block detected
string concatenation pattern detected
explicit `: Str >` form not detected in the inspected block
```

Whitespace variation around tokens is accepted.

## 16.5 Interpretation

This is a targeted warning for a known pattern-shape risk.

The scanner does not type-check the pattern.

---

# 17. `SCAN-PATTERN-002` — untyped `table` string pattern

## 17.1 Purpose

Apply the same string-pattern review to a `table` block.

Representative suspicious form:

```gf
table {
  _ + "e" => "x" ;
  _       => "y"
}
```

## 17.2 Count unit

```text
one brace-balanced table block
```

## 17.3 Match conditions

Count when:

```text
table block detected
string concatenation pattern detected
explicit `: Str >` form not detected in the inspected block
```

## 17.4 Interpretation

This rule is heuristic.

Compilation remains authoritative.

---

# 18. `SCAN-STYLE-001` — trailing whitespace

## 18.1 Purpose

Detect physical source lines ending in one or more:

```text
space
tab
```

## 18.2 Count unit

```text
one physical source line
```

A line ending in multiple trailing characters still counts once.

## 18.3 Source view

```text
original source lines
```

Comments and strings are not excluded because the rule concerns physical formatting.

## 18.4 Interpretation

Trailing whitespace is a style finding.

It MUST NOT become a GF compile failure.

A repository formatting policy may gate it separately.

---

## 19. Findings and severity policy

The scanner itself records matches, not release decisions.

Recommended interpretation categories:

| Rule family | Default policy |
|---|---|
| `NOTATION` | warning requiring review |
| `RUNTIME` | warning requiring architectural or linguistic review |
| `PATTERN` | warning requiring type/pattern review |
| `STYLE` | advisory or formatting gate |

The project validation specification MAY state that a rule must have zero findings for release.

That policy MUST be explicit and MUST remain distinct from GF compilation status.

Example:

```text
compile_status = OK
scan_counts.runtime_str_match = 1
release_policy = review required
```

The file MUST NOT be serialized as a GF compilation failure solely because of the scan count.

---

## 20. Scan-log artifact

### 20.1 Canonical location

```text
run_<run-id>/raw/scan/<safe-source-identity>.scan.txt
```

The scanner uses `RunPaths.scan_logs_dir`.

### 20.2 Naming

The log name MUST be deterministic for a project-relative source path.

It MUST be safe on supported filesystems.

Two distinct selected source paths MUST NOT silently collide to the same log path.

If sanitization can collide, the final implementation SHOULD append a short stable hash.

Example:

```text
lib_src_example_GrammarTst.gf__a1b2c3d4.scan.txt
```

### 20.3 Minimum content

A scan log SHOULD contain:

```text
source path
project-relative path
scanner version or rule-set version
completion state
summary counts
one section per rule
source ranges
bounded excerpts
encoding warnings
scanner diagnostics
```

### 20.4 Machine-consumption rule

The scan log is human evidence.

Consumers MUST use `ScanCounts` or structured findings rather than parse the log text.

### 20.5 Excerpts

Excerpts MUST:

- be bounded;
- preserve the original source line;
- include one-based line numbers;
- avoid rewriting source;
- clearly mark truncation;
- avoid leaking files outside the selected source.

### 20.6 Newline and encoding

The canonical log uses:

```text
UTF-8 without BOM
LF newlines
final newline
```

---

## 21. Aggregated scan logs

The report/log layer may create:

```text
raw/ALL_SCAN_LOGS.TXT
```

The scanner does not own this aggregate.

The aggregate writer consumes existing per-file scan logs or structured results.

It MUST NOT rescan source files.

A missing per-file log is reported as missing evidence, not silently regenerated during report writing.

---

## 22. Determinism

Equivalent source bytes, rule set and configuration MUST produce equivalent:

```text
ScanCounts
rule ordering
finding ordering
line ranges
log section ordering
```

Canonical ordering:

1. registry rule order;
2. source start line;
3. source end line;
4. stable excerpt text.

Filesystem enumeration order MUST NOT affect one-file scanning.

Timestamps SHOULD NOT appear in the per-file log unless they are clearly non-semantic metadata.

---

## 23. Performance model

### 23.1 Final target

For a source file of `n` characters, scanning SHOULD be approximately:

```text
O(n + rule passes)
```

The implementation SHOULD:

1. read the file once;
2. derive lexical views once;
3. reuse views across rules;
4. avoid repeated whole-file decoding;
5. avoid invoking external processes;
6. avoid catastrophic regular expressions;
7. avoid repeated path resolution inside rule loops.

### 23.2 Rule cost

Built-in rules are bounded textual analyses.

A new rule MUST document its complexity.

A rule requiring full semantic understanding belongs in GF execution or a dedicated validated parser, not in this scanner.

### 23.3 Memory

Keeping original and two masked line views is acceptable for normal GF source sizes.

The source-size limit protects against pathological inputs.

### 23.4 Parallelism

Files MAY be scanned in parallel at the orchestration layer when:

- each file has an independent log path;
- result ordering is restored deterministically;
- shared rule state is immutable;
- error handling remains per-file;
- no source mutation occurs.

The scanner function itself remains one-file scoped.

---

## 24. Error handling

### 24.1 Source missing

A selected source that no longer exists is an I/O error.

Return of zero counts is prohibited.

### 24.2 Source is not a regular file

Directories, broken links or unsupported special files are rejected.

Symlink policy follows repository and path-security rules.

### 24.3 Decode failure

A strict decode failure is an encoding/I/O error.

A lossy diagnostic scan must record that replacement decoding occurred.

### 24.4 Log write failure

Findings may have been computed, but the scan stage is incomplete when its required evidence cannot be written.

The caller MUST receive an error.

### 24.5 Internal rule failure

One rule throwing an unexpected exception MUST NOT be represented as “no findings.”

Preferred final behavior:

- stop the file scan;
- preserve any safe partial diagnostic;
- return or raise a structured scanner error;
- let the orchestrator mark the file-stage error;
- retain the source fingerprint and any earlier evidence.

### 24.6 Malformed braces or lexical state

Malformed source structure SHOULD produce a scanner diagnostic and continue only under a documented safe policy.

GF compilation determines authoritative syntax failure.

---

## 25. Security and trust boundary

GF source is input data.

The scanner MUST:

- open only the selected source path;
- validate containment according to project policy;
- avoid following unapproved path traversal;
- avoid shell execution;
- avoid evaluating source text;
- avoid loading Python from the project;
- avoid unbounded log output;
- avoid writing outside the run directory;
- avoid embedding secrets from environment state;
- avoid interpreting scan excerpts as formatting directives.

The scanner does not execute GF or project code.

---

## 26. Configuration policy

The final v1 scanner has one built-in framework rule set.

Project configuration MAY control:

```text
whether scanning runs
release policy for known rule IDs
strict versus diagnostic encoding behavior
source-size limit if exposed by framework policy
```

Project configuration MUST NOT inject arbitrary regular expressions into the framework scanner.

Project-specific inspections belong in:

```text
project validation scenarios
project review documents
explicit future extension mechanisms
```

This avoids turning the scanner into an unreviewed regex engine.

---

## 27. Language neutrality

Framework scan rules MUST be language-neutral.

They may target GF notation or general repository hygiene.

They MUST NOT contain active-language identifiers such as:

```text
language name
module suffix
specific lexeme
specific morphological ending
language-specific module path
```

A project may document language-specific review rules in:

```text
project/docs/VALIDATION_SPEC.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
```

Executable project-specific checks should normally use GF scenarios or dedicated project validation data.

---

## 28. Integration with compilation

For each selected file, the orchestrator may run:

```text
static scan
GF compile
```

The resulting file model contains both:

```text
scan_counts
compile_summary
```

Required invariants:

- compile success does not erase scan findings;
- compile failure does not invent scan findings;
- scanner failure is distinguishable from compile failure;
- `no_compile` mode does not make scan findings compile results;
- reports show scan and compile evidence separately;
- top GF errors are not derived from scan-log prose.

---

## 29. Integration with classification

The dependency classifier consumes compile and dependency evidence.

The scanner MUST NOT label findings as:

```text
direct
downstream
ambiguous
```

A project policy may treat a scan finding as a direct policy violation, but that is not the same as causal classification of a GF compile failure.

The shared diagnostic-class field retains its defined causal meaning.

---

## 30. Integration with file results

A canonical file result includes:

```text
file_path
module_name
status
diagnostic_class
scan_counts
fingerprint
compile_summary
scan_log_path
```

Scan invariants:

- `scan_counts` is present after a successful scan;
- `scan_log_path` is run-relative when serialized;
- counts are non-negative;
- scan findings do not independently force compile status;
- a failed scan must not masquerade as zero findings;
- reports do not reconstruct scan-log paths.

---

## 31. Integration with validation modes

### 31.1 Quick mode

Scans the selected target file when static scanning is enabled.

### 31.2 Checkpoint mode

Scans files selected for checkpoint validation.

### 31.3 Diagnostic mode

Scans every selected file and retains detailed evidence.

Diagnostic mode MAY enable additional scanner diagnostics, but it MUST NOT silently change existing rule semantics.

### 31.4 Release mode

Runs the stable scanner rule set over all release-relevant selected source files unless project policy explicitly disables scanning.

A release policy may require zero counts for selected rule IDs.

The release report must state the policy separately from GF compile status.

---

## 32. Reporting requirements

### 32.1 Machine summary

`summary.json` records canonical `scan_counts` and `scan_log_path`.

### 32.2 Markdown summary

The human summary SHOULD present:

```text
total findings by rule
files with findings
link or path to each scan log
policy significance
```

### 32.3 AI-ready report

`AI_READY.md` SHOULD include bounded scan evidence when it materially assists diagnosis.

It MUST distinguish:

```text
static heuristic
GF diagnostic
causal classification
```

### 32.4 No report-time scan

Report writers MUST NOT rerun the scanner.

---

## 33. Rule admission criteria

A new built-in scanner rule is accepted only when all conditions hold:

```text
the pattern is language-neutral
the pattern is useful across projects
the rule can be stated precisely
the count unit is unambiguous
comments and strings can be handled safely
false-positive risk is documented
false-negative risk is documented
the rule does not duplicate GF compilation
the rule does not require semantic inference
performance is bounded
tests cover positive and negative cases
a stable rule ID is assigned
persistence impact is reviewed
documentation is updated
```

Convenience alone is insufficient.

A project-specific one-off issue is not a reason to expand the framework nucleus.

---

## 34. Adding a rule

Required change set:

1. assign a stable rule ID;
2. define the public count field or approved structured representation;
3. define the count unit;
4. define the source view;
5. implement the detector in `scanner.py`;
6. add positive tests;
7. add comment/string masking tests;
8. add multiline and boundary tests;
9. add false-positive tests;
10. update `ScanCounts`;
11. update result construction;
12. update summary serialization;
13. update report rendering;
14. update `PERSISTED_SCHEMA_LOCK.md` when persisted shape changes;
15. update `INTERFILE_CONTRACT_LOCK.md` when the public contract changes;
16. update this registry;
17. add migration handling when required.

A rule MUST NOT be added only to the log while being absent from structured results if downstream policy needs it.

---

## 35. Changing a rule

### 35.1 Internal compatible change

Examples:

```text
performance improvement
equivalent regex simplification
masker correction that restores documented semantics
clearer log message
```

Requirements:

- existing semantic tests pass;
- new regression test added;
- no count-unit change;
- no persisted-field change.

### 35.2 Semantic change

Examples:

```text
counting occurrences instead of lines
counting nested blocks separately
expanding the recognized `.s` head grammar
changing typed-pattern exemption
changing comment/string interpretation
```

This is a contract change.

It requires:

- rule-version review;
- regression impact review;
- persisted comparison impact review;
- documentation update;
- tests against previous behavior;
- migration or release note when historical counts are compared.

### 35.3 Rule removal

A persisted rule field MUST NOT disappear silently.

Options:

```text
retain field with zero and mark deprecated
migrate schema in a major version
retain historical reader support
```

The rule ID remains reserved.

---

## 36. Required unit tests

Recommended location:

```text
tests/unit/audit/test_scanner.py
```

Minimum v1 cases:

```text
single slash before `=>`
double slash before `->`
runtime `.s` string case
untyped case string pattern
untyped table string pattern
trailing spaces
empty file
scan-log creation
summary counts
comment-only patterns ignored
string-only patterns ignored
```

These cases reflect the current validated scanner nucleus.

### 36.1 Lexical masking tests

Required additional final tests:

```text
line comment after code
multi-line block comment
comment delimiters inside string
braces inside string
arrows inside string
backslash escapes
GF doubled quotes
string ending near comment marker
block-comment end followed by code
CRLF source
UTF-8 BOM
Unicode source
unterminated string
unterminated block comment
```

### 36.2 Structural tests

```text
single-line case block
multi-line case head
nested braces
nested case
nested table
brace in comment
brace in string
unbalanced opening brace
closing brace without opening block
typed `: Str >` exemption
whitespace variants
```

### 36.3 Count semantics tests

```text
two matches on one notation line count once
two matching notation lines count twice
one block with multiple literal branches counts once
two separate blocks count twice
nested block policy is deterministic
trailing spaces count lines, not characters
```

### 36.4 Path and artifact tests

```text
source path with spaces
source outside project root according to policy
safe log filename
sanitization collision
run-relative serialized log path
log write failure
```

---

## 37. Contract tests

Recommended location:

```text
tests/contracts/test_scanner_contract.py
```

Contract tests MUST verify:

- public `scan_file` signature;
- `ScanCounts` stable fields;
- no GF process invocation;
- no source mutation;
- no report import;
- no classifier import;
- one per-file log;
- deterministic counts;
- deterministic finding order;
- comments and strings ignored according to policy;
- compile success cannot erase scan counts;
- report writers consume results without rescanning;
- language-specific identifiers are absent from framework scanner code.

---

## 38. Property and fuzz testing

The lexical masker is a suitable target for bounded property tests.

Recommended properties:

```text
output line count equals input line count
masked view line lengths equal original line lengths
comment-only edits do not create code findings
string-content edits do not create notation findings
scanner never writes source
scanner terminates for bounded input
all returned counts are non-negative
all finding ranges are inside the source
```

Fuzz inputs MUST be bounded in size and execution time.

Fuzzing does not replace semantic fixture tests.

---

## 39. Regression comparison

Historical scan counts may be compared between runs.

Comparison is meaningful only when:

```text
same rule semantics
same rule-set version
same source selection policy
same source path identity
```

When rule semantics change, reports SHOULD state that scan-count comparison is not directly equivalent.

A rule-set version MAY be recorded in logs and machine summaries.

It MUST remain separate from the GF version.

---

## 40. False positives and false negatives

Every heuristic scanner has both.

### 40.1 False positives

A pattern may be intentional or valid.

Required response:

```text
review the source
review GF compilation
review project policy
document a justified exception when needed
```

The scanner MUST NOT hide known false-positive risk.

### 40.2 False negatives

Textual scanning cannot detect every equivalent construct.

A zero count does not guarantee absence of the underlying architectural risk.

### 40.3 Suppression policy

Inline source suppression comments are not part of v1.

Reasons:

- they add a second directive language;
- they can conceal real issues;
- they complicate lexical masking;
- they create source-level framework coupling.

A justified exception belongs in project validation documentation or an explicit rule-policy registry.

If suppressions are added later, they require a dedicated documented contract and tests.

---

## 41. Why GF Wordbench does not build a full GF parser

A custom parser would duplicate GF responsibilities and create version drift.

The static scanner therefore remains intentionally shallow.

It may recognize enough lexical structure to avoid obvious comment/string errors and enough braces to inspect bounded blocks.

When a proposed rule requires:

```text
full module resolution
type inference
constructor semantics
abstract/concrete agreement
runtime evaluation
complete GF grammar parsing
```

the requirement belongs to GF compilation, GF shell scenarios or another explicit external-tool contract.

---

## 42. Drift indicators

Probable scanner drift exists when:

- a new count field appears in one model but not reports or schemas;
- a rule counts lines in one version and occurrences in another without notice;
- comments trigger findings;
- strings trigger notation findings;
- GF doubled quotes break string masking;
- braces inside strings change block boundaries;
- the log and `ScanCounts` disagree;
- consumers parse log prose instead of structured counts;
- scanner code imports the compiler;
- scanner code invokes GF;
- scan findings become compile failures implicitly;
- a language-specific suffix appears in framework scan logic;
- report generation rescans source;
- source is rewritten to “fix” a finding;
- different validation modes use different semantics for the same rule ID;
- a log-name sanitization collision overwrites evidence;
- decoding replacement silently changes source interpretation;
- a new arbitrary project regex bypasses rule review;
- historical scan comparisons ignore a rule semantic change.

Detected drift MUST be resolved by restoring the documented contract or changing it through the coordinated workflow.

---

## 43. Change checklist

```text
[ ] affected rule IDs identified
[ ] count units reviewed
[ ] source views reviewed
[ ] lexical masking reviewed
[ ] comment behavior tested
[ ] string behavior tested
[ ] GF doubled quotes tested
[ ] brace balancing tested
[ ] false positives documented
[ ] false negatives documented
[ ] performance bounded
[ ] ScanCounts reviewed
[ ] result model reviewed
[ ] persisted schema reviewed
[ ] scan-log format reviewed
[ ] report consumers reviewed
[ ] regression comparison reviewed
[ ] unit tests updated
[ ] contract tests updated
[ ] language neutrality verified
[ ] INTERFILE_CONTRACT_LOCK.md updated if required
[ ] PERSISTED_SCHEMA_LOCK.md updated if required
[ ] this document updated
```

---

## 44. Implementation checklist

A conforming v1 implementation satisfies:

```text
[ ] one-file public scan operation
[ ] source read once
[ ] UTF-8 policy explicit
[ ] original lines retained
[ ] comments masked
[ ] strings masked
[ ] GF doubled quotes handled
[ ] line numbers preserved
[ ] braces balanced on string-masked text
[ ] six canonical rules implemented
[ ] stable ScanCounts returned
[ ] one deterministic scan log written
[ ] source never modified
[ ] GF never invoked
[ ] compile status kept separate
[ ] classifier kept separate
[ ] reports do not rescan
[ ] errors do not become zero findings
[ ] tests cover comments, strings and empty files
[ ] framework rules remain language-neutral
```

---

## 45. Final enforcement rule

Static scanning is intentionally useful but intentionally limited.

It provides fast evidence about known textual risks without competing with GF.

Therefore:

> No static finding may be presented as authoritative GF failure, and no scanner implementation may grow into an undocumented parser, compiler, project-specific regex engine or source-rewriting system.
