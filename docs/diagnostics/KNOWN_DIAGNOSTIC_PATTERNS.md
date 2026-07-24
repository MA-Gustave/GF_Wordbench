# GF Wordbench — Known Diagnostic Patterns

**Document ID:** `GF-WB-DIAG-KNOWN-PATTERNS`  
**Applies to:** GF compiler output, GF shell/scenario output, process failures, artifact checks, and GF Wordbench contract failures  
**Owner:** GF Wordbench diagnostics module  
**Causal classification owner:** GF Wordbench diagnostics classifier  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Catalog version:** `1.1`  
**Last reviewed:** 2026-07-24  

---

## 1. Purpose

This document defines the diagnostic patterns that GF Wordbench is allowed to recognize and normalize.

It exists to prevent three forms of drift:

1. two components recognizing the same GF output differently;
2. a new regular expression silently changing diagnostic meaning;
3. an observed message being promoted to a stable rule without evidence.

The catalog records:

- stable pattern identifiers;
- source stream policy;
- matching evidence;
- normalized error kind;
- extraction rules;
- confidence;
- precedence;
- version sensitivity;
- false-positive risks;
- required tests;
- maintenance rules.

This document does not claim that every possible GF diagnostic is known.

Unknown output must remain visible and must fall back safely.

---

## 2. Core rule

> A diagnostic pattern is canonical only when its meaning is documented, its evidence is preserved, and its behavior is tested.

A regular expression alone is not a diagnostic contract.

Every canonical pattern must have:

- a stable ID;
- a defined scope;
- one normalized meaning;
- at least one positive fixture;
- at least one relevant negative fixture;
- deterministic precedence;
- raw-evidence references;
- a compatibility rule.

---

## 3. Related authority

The following documents govern related boundaries:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
docs/diagnostics/ERROR_CLASSIFICATION.md
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
docs/diagnostics/GF_DIAGNOSTIC_PARSING.md
docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/reference/DIAGNOSTIC_KINDS.md
docs/reference/STATUS_VALUES.md
```

Priority when rules overlap:

1. accepted ADRs and `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`;
2. persisted-schema lock for serialized enum values;
3. process-execution model for launch, timeout, cancellation, and capture facts;
4. error-handling model for framework error semantics;
5. this catalog for pattern identity and normalized interpretation;
6. classifier documentation for direct/downstream causality.

Diagnostic interpretation belongs to one Wordbench run and one active project. `gf-portfolio` may consume finalized public diagnostic records but does not define, alter or execute Wordbench pattern matching.

---

## 4. Scope

This catalog covers diagnostic evidence from:

- GF source compilation;
- PGF construction;
- GF version probing;
- native `.gfs` scenarios;
- grammar loading;
- parsing;
- linearization;
- bounded generation;
- morphology and introspection;
- process launch;
- process timeout and cancellation;
- output decoding;
- required marker checks;
- required artifact checks;
- normalization;
- gold comparison;
- framework contract checks.

---

## 5. Exclusions

This catalog does not define:

- GF language semantics;
- linguistic correctness;
- static source-scan rules;
- category or lincat architecture;
- direct versus downstream classification;
- release policy;
- report formatting;
- complete GF documentation;
- speculative messages not present in captured evidence.

Static scan findings belong to:

```text
docs/validation/STATIC_SCANNING.md
```

They must not be represented as GF compiler diagnostics.

---

## 6. Diagnostic pipeline

```text
process facts
    +
raw stdout
    +
raw stderr
    +
expected artifacts
    +
scenario assertions
        ↓
evidence segmentation
        ↓
canonical pattern matching
        ↓
field extraction
        ↓
normalized DiagnosticRecord
        ↓
stage-specific result
        ↓
causal classification
        ↓
reports
```

The diagnostic parser does not launch GF.

The classifier does not reparse raw output using a separate rule set.

---

## 7. Evidence authority

Diagnostic interpretation considers:

```text
execution state
exit code
stdout
stderr
artifact observations
scenario markers
normalization result
gold result
```

Rules:

- stdout and stderr are preserved separately;
- both streams are inspected;
- stream identity remains available;
- raw evidence is never replaced by normalized text;
- exit code is evidence, not complete diagnosis;
- process facts take precedence over text guesses;
- missing required artifacts can override a zero exit code;
- missing scenario markers can override a zero exit code;
- gold mismatch is evaluated after normalization.

---

## 8. Catalog inclusion rule

The canonical pattern set is the set listed in the canonical pattern index of this document.

A canonical pattern:

- has one stable identifier;
- has one normalized meaning;
- has positive and relevant negative fixtures;
- has deterministic precedence;
- preserves raw evidence;
- defines version and stream behavior;
- may be used for automatic classification.

Text not covered by the canonical pattern set remains visible and uses the generic fallback or an authoritative process, artifact, normalization or contract diagnosis.

Examples of unsupported or insufficiently specific wording may be documented as evidence notes, but they do not receive a canonical pattern ID and do not create a specific automatic diagnosis.

---

## 9. Confidence levels

Canonical confidence:

```text
authoritative
high
medium
low
```

### Authoritative

Derived from process or framework state rather than text.

Examples:

- timeout recorded by the process runner;
- launch failure recorded by the operating-system boundary;
- missing required artifact observed by filesystem check.

### High

Text structure is distinctive and supported by fixtures.

### Medium

Text is useful but may vary by GF version or context.

### Low

Heuristic only; must not independently create a specific high-confidence diagnosis.

---

## 10. Pattern identifier format

```text
DP-<DOMAIN>-<NUMBER>
```

Domains:

```text
PROC     process execution
GFINT    GF internal failures
GFTYPE   GF type diagnostics
GFSYN    GF syntax/parse-of-source diagnostics
GFLOAD   module/import/load diagnostics
GFGEN    generation and runtime diagnostics
GFWARN   warnings
SCEN     scenario contract diagnostics
ART      artifact diagnostics
NORM     normalization diagnostics
GOLD     gold comparison diagnostics
FALLBACK generic fallback
```

Examples:

```text
DP-PROC-001
DP-GFINT-001
DP-GFTYPE-001
DP-GFSYN-001
```

Pattern IDs must never be reused for unrelated meanings.

---

## 11. Conceptual diagnostic record

```python
@dataclass(frozen=True, slots=True)
class DiagnosticRecord:
    pattern_id: str
    error_kind: str
    severity: str
    confidence: str
    source_stream: str
    operation_kind: str
    message: str
    detail: str
    file_path: Path | None
    module_name: str | None
    line: int | None
    column: int | None
    references: tuple[str, ...]
    raw_excerpt: str
```

Exact shared-model design is governed by `DATA_MODEL.md`.

---

## 12. Canonical severity

Canonical diagnostic severity:

```text
info
warning
error
fatal
```

Severity is not validation status.

Examples:

- warning may coexist with `OK`;
- error normally contributes to `FAIL`;
- process or interpretation failure normally contributes to `ERROR`;
- fatal identifies execution-stopping tool output, not necessarily a framework crash.

---

## 13. Canonical error kinds

The centralized reference is authoritative.

This catalog uses:

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
CONTRACT
ARTIFACT
NORMALIZATION
GOLD
CANCELLED
OUTPUT_LIMIT
```

A pattern must not invent an undocumented persisted error kind.

---

## 14. Match precedence

Global precedence:

```text
1. process facts
2. framework configuration and contract facts
3. GF internal-failure patterns
4. structured GF type patterns
5. structured GF syntax patterns
6. operation-specific GF patterns
7. warnings
8. generic non-zero fallback
9. unknown-output fallback
```

A lower-precedence pattern must not overwrite a higher-precedence diagnosis.

All matched secondary evidence may still be retained.

---

## 15. Multi-pattern behavior

One operation may produce several diagnostics.

The parser returns:

```text
primary diagnostic
secondary diagnostics
references
raw evidence locations
```

Primary selection is deterministic.

Example:

```text
Internal error in GeneratePMCFG
    +
Cannot find an inflection rule
```

Primary:

```text
DP-GFINT-001
```

Secondary:

```text
DP-GFGEN-001
```

The nested runtime message adds detail; it does not replace the internal-error class.

---

# 16. Process patterns

## DP-PROC-001 — Process timeout

**Confidence:** authoritative  
**Source:** process execution state  
**Text matching:** prohibited as primary detection  
**Error kind:** `TIMEOUT`  
**Severity:** fatal at operation level  

### Detection

```text
execution_state == timed_out
```

or the canonical equivalent.

### Normalized message

```text
External process timed out.
```

### Required fields

```text
timeout value
duration
termination attempted
termination succeeded
stdout path
stderr path
```

### Rules

- Do not detect timeout from the word `timeout` in tool output.
- Do not report timeout as a GF syntax or type error.
- Preserve partial stdout and stderr.
- Gold comparison is skipped for an incomplete scenario.
- A legacy timeout sentinel may be read only by compatibility code.

### Required tests

- process exceeds deadline;
- tool prints “timeout” but exits normally;
- timeout with stdout;
- timeout with stderr;
- timeout termination failure.

---

## DP-PROC-002 — Process launch failure

**Confidence:** authoritative  
**Source:** process runner  
**Error kind:** `TOOL` or centralized launch kind  
**Severity:** fatal at operation level  

### Detection

```text
execution_state == launch_failed
```

### Normalized message

```text
External process could not be started.
```

### Possible normalized subkinds

```text
not_found
permission_denied
invalid_executable
resource_unavailable
platform_error
unknown
```

### Rules

- Do not classify as a GF diagnostic.
- `exit_code` is absent when no process started.
- Preserve the executable and working directory.
- Raw exception wording may be retained as detail but is not the stable message.

---

## DP-PROC-003 — Process cancellation

**Confidence:** authoritative  
**Source:** process runner/controller  
**Error kind:** `CANCELLED`  
**Severity:** error  

### Detection

```text
execution_state == cancelled
```

### Canonical reasons

```text
user
application_shutdown
output_limit
controller_policy
```

### Rules

- User cancellation is not timeout.
- Output-limit cancellation also matches `DP-PROC-004`.
- Partial evidence remains available.
- A required release operation cannot pass.

---

## DP-PROC-004 — Output limit exceeded

**Confidence:** authoritative  
**Source:** process runner  
**Error kind:** `OUTPUT_LIMIT`  
**Severity:** error  

### Detection

```text
output_limit_exceeded == true
```

### Normalized message

```text
External process exceeded its output limit.
```

### Rules

- Never infer only from file size after an otherwise accepted run.
- Record configured limit and captured byte counts.
- Truncation or cancellation must be explicit.
- Exact gold comparison is skipped.

---

## DP-PROC-005 — Output decoding failure

**Confidence:** authoritative  
**Source:** decoder  
**Error kind:** `IO` or centralized encoding kind  
**Severity:** error when required interpretation is blocked  

### Detection

The configured decoder cannot produce the required diagnostic view while preserving the raw bytes.

### Rules

- Preserve original bytes.
- Do not silently delete invalid bytes.
- Do not fall back to locale-dependent decoding.
- A safe replacement view may be shown as secondary evidence.

---

# 17. GF internal patterns

## DP-GFINT-001 — GeneratePMCFG internal error

**Confidence:** high  
**Operation scope:** compile, PGF build, scenario  
**Source:** stdout or stderr  
**Error kind:** `INTERNAL`  
**Severity:** fatal  

### Confirmed anchor

```text
Internal error in GeneratePMCFG
```

### Legacy implementation expression

```regex
Internal error in GeneratePMCFG
```

### Extraction

Primary message:

- the complete first line containing the anchor;
- fallback: `Internal error in GeneratePMCFG`.

Detail:

```text
GeneratePMCFG
```

### Rules

- Match case-sensitively unless a version adapter proves otherwise.
- Inspect both streams.
- Retain nearby stack/runtime lines as secondary evidence.
- Do not downgrade to `OTHER`.
- Do not infer direct/downstream causality here.

### Known associated evidence

Observed nested text:

```text
Cannot find an inflection rule
```

This nested text is retained separately as non-canonical runtime evidence.

### False-positive controls

Do not match:

- documentation text copied into a scenario result intentionally;
- report prose;
- source-code comments;
- gold files outside an actual tool-output context.

### Required tests

- exact anchor on stderr;
- exact anchor on stdout;
- executable prefix before anchor;
- nested runtime detail;
- similar non-anchor wording;
- report text not treated as raw GF output.

---

# 18. GF type patterns

## DP-GFTYPE-001 — Expected/inferred type mismatch

**Confidence:** high  
**Operation scope:** compile, PGF build, scenario load  
**Source:** stdout and stderr combined for analysis, preserved separately  
**Error kind:** `TYPE`  
**Severity:** error  

### Required structure

Both lines must exist:

```text
expected: <expected-type>
inferred: <inferred-type>
```

Leading whitespace is allowed.

### Confirmed expressions

```regex
^\s*expected:\s*(.*)$
```

```regex
^\s*inferred:\s*(.*)$
```

Multiline matching is required.

### Optional context

```text
Happened in...
```

Confirmed context expression:

```regex
Happened in[^\r\n]*
```

### Extraction

Primary message:

1. first `Happened in...` line when present;
2. otherwise `Type error`.

Detail:

```text
expected: <value> | inferred: <value>
```

### Rules

- Both expected and inferred lines are required for this pattern.
- One line alone must not trigger this pattern.
- Preserve complete type text when bounded.
- Do not normalize away GF type constructors or record structure.
- A type pattern does not independently establish which file is the root cause.

### Required tests

- expected and inferred on stdout;
- expected and inferred on stderr;
- split between streams;
- leading spaces;
- empty expected value;
- only expected line;
- only inferred line;
- unrelated prose containing both words on one line.

---

## Explicit unification wording

**Confidence:** medium  
**Error kind:** `TYPE`  
**Severity:** error  

### Observed examples

```text
cannot unify
cannot unify the information
```

### Current policy

This wording may be preserved in `first_error`, but it does not create a canonical `TYPE` diagnosis by itself.

### Conditions for defining a dedicated canonical pattern

- captures from supported GF versions;
- positive and negative fixtures;
- source-location extraction test;
- interaction test with expected/inferred pattern;
- false-positive review.

---

# 19. GF syntax patterns

## DP-GFSYN-001 — GF source syntax error

**Confidence:** medium  
**Operation scope:** source compilation, PGF build, scenario script  
**Source:** stdout or stderr  
**Error kind:** `SYNTAX`  
**Severity:** error  

### Confirmed anchors

```text
Syntax error
Parse error
Unexpected token
```

### Legacy implementation expression

```regex
^.*(Syntax error|Parse error|Unexpected token).*$
```

with multiline mode.

### Extraction

Primary message:

- complete first matching line.

Detail:

- empty unless a structured source location is extracted separately.

### Rules

- The word `Parse error` in compiler output refers to parsing GF source or command syntax under this pattern.
- It must not be confused with “no parse found” for a linguistic parse scenario.
- Inspect both streams.
- Preserve source location when present.
- Do not match normalized report headings or project documentation.

### Required tests

- each anchor individually;
- path and location before anchor;
- message on stderr;
- message on stdout;
- linguistic parse result with zero parses;
- documentation sentence mentioning “Syntax error” outside tool evidence.

---

## Scenario command syntax evidence

**Error kind:** `SCRIPT` or `SYNTAX`  
**Severity:** error  

No dedicated scenario-command syntax pattern is defined because the available evidence does not distinguish it reliably from source-module syntax errors.

`DP-GFSYN-001` remains the canonical text pattern and the operation context supplies scenario scope.

---

# 20. Generic fallback patterns

## DP-FALLBACK-001 — Non-zero exit with diagnostic line

**Confidence:** medium  
**Operation scope:** any GF process  
**Source:** both streams  
**Error kind:** `OTHER`  
**Severity:** error  

### Trigger

```text
process completed
exit_code != 0
no higher-precedence canonical pattern matched
```

### Line selection

Select the first non-empty candidate line after excluding confirmed progress-only lines.

Legacy excluded progress patterns:

```regex
^- compiling\b
```

```regex
^(linking|Writing)\b
```

### Extraction

Primary message:

- first remaining non-empty line.

Detail:

- empty unless operation-specific logic adds context.

### Rules

- Preserve all raw output.
- Do not claim a specific type, syntax, or internal class.
- Progress-line filtering must remain narrow.
- New progress exclusions require fixtures.
- This pattern must not run before canonical specific patterns.

### Required tests

- non-zero with useful stderr;
- non-zero with useful stdout;
- progress line followed by error;
- only progress lines;
- empty output;
- higher-precedence type error;
- higher-precedence internal error.

---

## DP-FALLBACK-002 — Non-zero exit without matched message

**Confidence:** authoritative for the fallback fact  
**Error kind:** `OTHER`  
**Severity:** error  

### Trigger

```text
process completed
exit_code != 0
no higher pattern matched
no candidate diagnostic line remains
```

### Normalized message

```text
Non-zero exit with no recognized diagnostic message.
```

### Rules

- Record the actual exit code.
- Keep empty or progress-only raw logs.
- Do not fabricate a GF explanation.
- This condition is included in compatibility review when a new GF version is introduced.

---

## DP-FALLBACK-003 — Zero exit with no failure evidence

**Confidence:** authoritative only for process completion  
**Error kind:** `OK`  
**Severity:** info  

### Trigger

```text
execution completed
exit_code == 0
no fatal diagnostic matched
all operation-specific contracts passed
```

### Critical restriction

The parser alone cannot declare complete operation success.

The stage must also verify applicable:

- required artifacts;
- scenario markers;
- assertions;
- normalization;
- gold comparison.

---

## Fatal-looking unknown output

**Confidence:** low  
**Error kind:** `OTHER`  
**Severity:** warning or error by operation policy  

### Candidate generic anchors

Evidence excerpt extraction may use:

```text
Internal error
CallStack
error:
Error:
Exception:
Traceback
```

These strings are useful for evidence excerpt selection but are too broad to define one precise GF diagnosis automatically.

### Policy

- retain and surface the excerpt;
- do not assign a specific GF class from these anchors alone;
- non-zero exit may still trigger `DP-FALLBACK-001`;
- zero exit requires operation-specific review before failure;
- add a dedicated canonical pattern only through the catalog change policy.

---

# 21. Observed generation/runtime patterns

## Missing inflection rule runtime evidence

**Confidence:** medium  
**Operation scope:** compilation, PGF construction, generation, scenario runtime  
**Source:** stdout or stderr  
**Possible interpretation:** `INTERNAL` or `TOOL` depending on primary context  
**Severity:** fatal when nested under a terminating GF error  

### Observed anchor

```text
Cannot find an inflection rule
```

### Observed surrounding form

```text
evalTerm (Predef.error "Cannot find an inflection rule")
```

### Current interpretation

- If nested under `DP-GFINT-001`, retain it as secondary runtime detail.
- Do not replace the primary `GeneratePMCFG` internal diagnosis.
- Without a higher-precedence canonical pattern, retain it under the generic `OTHER` fallback.

### Conditions for defining a dedicated canonical pattern

- successful reproduction;
- supported-version captures;
- direct operation context;
- distinction between project runtime failure and GF internal failure;
- positive and negative tests.

---

# 22. Observed warning patterns

## Missing linearization type warning evidence

**Confidence:** medium  
**Error kind:** `OTHER` or future warning kind  
**Severity:** warning  

### Observed form

```text
Warning: no linearization type for <category>, inserting default <type>
```

### Current policy

- preserve as warning evidence;
- do not automatically fail compilation solely from this text;
- active-project release policy may prohibit it;
- missing-linearization scenarios provide stronger project-level evidence;
- do not assume the category or inserted type format is stable across GF versions.

### Conditions for defining a dedicated canonical pattern

- raw captures from supported GF versions;
- category/type extraction tests;
- coexistence test with successful exit;
- release-policy integration test.

---

## Generic GF warning evidence

**Severity:** warning  

A broad `Warning:` matcher is not canonical because:

- warning text may be version-dependent;
- not every warning has the same consequence;
- project policy may differ;
- scenario output may intentionally contain the word.

A warning family receives a dedicated ID only through the catalog change policy and complete fixtures.

---

# 23. Module and file reference patterns

## DP-GFLOAD-001 — Referenced GF source path

**Confidence:** medium  
**Error kind:** none by itself  
**Severity:** none by itself  

### Confirmed legacy expression

```regex
([A-Za-z0-9_./\\-]+\.gf)\b
```

case-insensitive.

### Purpose

Extract candidate `.gf` references from diagnostic text for later causal analysis.

### Rules

- This helper does not create a failure.
- Normalize separators after extraction.
- Resolve against known project files.
- Ignore references that cannot be mapped safely.
- Preserve the original text.
- Do not treat every referenced file as a blocker.
- Self-reference may support direct classification.
- Reference to a failing known provider may support downstream classification.

### False-positive risks

- paths in command echoes;
- documentation output;
- gold text;
- source strings;
- generated examples;
- unrelated `.gf` filenames.

The classifier must use project context and known results.

---

## Referenced GF module-name evidence


No canonical module-name-only extractor is defined.

Ordinary GF output may contain many capitalized identifiers, so a general module-name regex is prohibited.

---

# 24. Wordbench-origin diagnostic patterns

These are not GF messages.

They must be labeled as framework or contract evidence.

## DP-SCEN-001 — Required scenario missing

**Confidence:** authoritative  
**Source:** scenario registry/preflight  
**Error kind:** `CONFIG`  
**Severity:** error  

### Detection

A required configured scenario has no valid script asset.

### Normalized message

```text
Required scenario is missing.
```

No GF process is launched.

---

## DP-SCEN-002 — Required scenario section incomplete

**Confidence:** authoritative  
**Source:** marker parser  
**Error kind:** `CONTRACT`  
**Severity:** error  

### Detection

A declared section has a begin marker without a valid end marker, or another invalid marker transition.

### Normalized message

```text
Required scenario section did not complete.
```

A zero GF exit code does not override this result.

---

## Unsupported scenario-command evidence

**Confidence:** medium  
**Source:** GF output plus scenario context  
**Error kind:** `SCRIPT`  
**Severity:** error  

No dedicated canonical pattern is defined without stable supported-GF fixtures.

Such output uses syntax handling or generic non-zero fallback according to the evidence.

---

## DP-ART-001 — Required artifact missing

**Confidence:** authoritative  
**Source:** filesystem observation  
**Error kind:** `ARTIFACT`  
**Severity:** error  

### Detection

A required artifact expectation is absent after process completion.

### Normalized message

```text
Required artifact was not produced.
```

### Rules

- Zero exit does not override the failure.
- Record expected path and role.
- Do not detect from text.
- Applies to `.gfo`, `.pgf`, scenario exports, and other contracted artifacts.

---

## DP-ART-002 — Required artifact empty

**Confidence:** authoritative  
**Source:** filesystem observation  
**Error kind:** `ARTIFACT`  
**Severity:** error  

Applies when an artifact contract requires a positive minimum size.

---

## DP-NORM-001 — Normalization failed

**Confidence:** authoritative  
**Source:** normalizer  
**Error kind:** `NORMALIZATION`  
**Severity:** error  

### Rules

- Preserve raw output.
- Do not compare raw output as an undeclared fallback.
- Record normalization version and failure detail.
- Gold result remains unknown.

---

## DP-NORM-002 — Unsupported normalization version

**Confidence:** authoritative  
**Source:** normalizer/schema validation  
**Error kind:** `NORMALIZATION`  
**Severity:** error  

---

## DP-GOLD-001 — Gold mismatch

**Confidence:** authoritative  
**Source:** gold comparator  
**Error kind:** `GOLD`  
**Severity:** error  

### Detection

Canonical normalized actual output differs from validated expected gold output.

### Rules

- Create or reference a diff.
- Do not modify gold.
- This is a validation `FAIL`, not process `ERROR`, unless another higher error exists.

---

## DP-GOLD-002 — Required gold missing

**Confidence:** authoritative  
**Source:** gold preflight/comparator  
**Error kind:** `CONFIG` or `GOLD` according to centralized policy  
**Severity:** error  

Missing required gold is never an automatic pass.

---

## DP-GOLD-003 — Gold schema/version mismatch

**Confidence:** authoritative  
**Source:** gold reader  
**Error kind:** `GOLD`  
**Severity:** error  

Examples:

- wrong scenario ID;
- unsupported schema version;
- wrong normalization version;
- malformed section structure.

---

# 25. Historical and synthetic wording

The current tests and reports contain wording used to exercise downstream behavior.

Examples include:

```text
blocked by failed dependency GrammarSqi.gf
first error points to NounSqi.gf
cannot unify the information
```

These strings must not automatically be treated as stable native GF formats.

Classification:

| Wording | Catalog treatment |
|---|---|
| `blocked by failed dependency ...` | Wordbench/test-origin until real GF evidence proves otherwise |
| `first error points to ...` | Test/report wording, not active GF pattern |
| `cannot unify ...` | non-canonical type evidence |
| `.gf` path mention | extraction helper only |

Synthetic fixtures should be labeled clearly to avoid accidental promotion.

---

# 26. Progress and noise patterns

The legacy fallback parser ignores narrowly defined progress lines.

Active exclusions:

```regex
^- compiling\b
```

```regex
^(linking|Writing)\b
```

These exclusions apply only when choosing a fallback primary error after non-zero exit.

Rules:

- progress lines remain in raw output;
- exclusions are case-sensitive unless tested otherwise;
- do not discard arbitrary lines beginning with a dash;
- do not add broad “warning” exclusions;
- do not remove lines from diagnostic detail when they help context.

---

# 27. Source-location extraction

Source-location extraction is a separate helper.

It may extract:

```text
file
line
column
```

only when supported by fixtures.

Rules:

- original message remains intact;
- Windows and POSIX separators are accepted;
- project-relative canonical paths are preferred;
- external RGL paths may remain environment paths;
- a location is evidence, not causal proof;
- invalid or ambiguous coordinates remain null;
- path normalization must not change quoted linguistic text.

No universal location regex is declared active in version `1.0` without sufficient captured examples.

---

# 28. Stream policy

A pattern declares one of:

```text
stdout
stderr
either
both-structure
process-state
filesystem
framework-state
```

Examples:

- `DP-GFINT-001`: `either`;
- `DP-GFTYPE-001`: `both-structure`;
- `DP-PROC-001`: `process-state`;
- `DP-ART-001`: `filesystem`.

“Both-structure” means required parts may appear across both streams after preserving stream identity.

The parser may build a deterministic analysis view, but raw streams remain separate.

---

# 29. Combined analysis view

A deterministic combined analysis view may be built as:

```text
stdout content
separator metadata
stderr content
```

It must not be persisted as raw output.

Requirements:

- deterministic stream order;
- no silent line loss;
- no claim that original interleaving is known;
- field extraction records source stream where possible;
- complete raw paths remain available.

---

# 30. Case sensitivity

Default:

- distinctive GF anchors are case-sensitive;
- path extension extraction may be case-insensitive;
- fallback progress exclusions use tested case behavior;
- broad case-insensitive matching is prohibited without evidence.

Case-insensitive matching can increase false positives in linguistic output.

Every exception must be documented per pattern.

---

# 31. Whitespace policy

Patterns may tolerate:

- leading indentation;
- CRLF or LF;
- bounded internal spacing where GF formatting varies.

Patterns must not normalize away:

- type structure;
- trees;
- quoted strings;
- record fields;
- punctuation with semantic value.

The parser may strip outer line whitespace for `first_error`.

Raw text remains unchanged.

---

# 32. Unicode policy

Diagnostic parsing uses explicit UTF-8 policy.

Rules:

- preserve language-specific characters;
- preserve GF symbols;
- regexes must be Unicode-safe;
- do not ASCII-fold diagnostic text;
- case normalization is used only for identifiers or explicit case-insensitive patterns;
- decoding failure is handled by `DP-PROC-005`.

---

# 33. Diagnostic excerpts

A diagnostic excerpt should include:

```text
primary matching line
bounded preceding context
bounded following context
```

Context is evidence only.

Observed legacy fatal excerpt anchors include:

```text
Internal error
Cannot find an inflection rule
CallStack
error:
Error:
Exception:
Traceback
```

These anchors may select excerpts without determining the error kind.

Excerpt bounds must prevent oversized reports.

---

# 34. Pattern registry model

Canonical registry model:

```python
@dataclass(frozen=True, slots=True)
class DiagnosticPattern:
    pattern_id: str
    operations: frozenset[str]
    streams: frozenset[str]
    priority: int
    confidence: str
    error_kind: str
    severity: str
    matcher: Callable[[DiagnosticEvidence], PatternMatch | None]
```

Registry requirements:

- deterministic priority;
- unique IDs;
- no duplicate semantic owner;
- immutable definitions;
- explicit operation scope;
- test fixture references;
- no import from reports or GUI.

---

# 35. Component ownership

The diagnostics module contains four separate responsibilities:

```text
diagnostic parser
    consumes process, stream, artifact and contract evidence

canonical pattern registry
    owns pattern IDs, matching rules, precedence and fixtures

diagnostic extractors
    own bounded paths, locations, expected/inferred fields and excerpts

causal classifier
    owns direct, downstream and ambiguous classification
```

Source scanning is outside the diagnostics module.

Reports and user interfaces consume structured diagnostic records and do not own regular expressions, precedence or classification rules.

---

# 36. Public API

Canonical interface:

```python
def parse_diagnostics(
    evidence: DiagnosticEvidence,
) -> DiagnosticParseResult:
    ...
```

Conceptual evidence:

```python
@dataclass(frozen=True, slots=True)
class DiagnosticEvidence:
    operation_kind: str
    execution_state: str
    exit_code: int | None
    stdout_path: Path
    stderr_path: Path
    artifact_observations: tuple[ArtifactObservation, ...]
    metadata: Mapping[str, str]
```

Conceptual result:

```python
@dataclass(frozen=True, slots=True)
class DiagnosticParseResult:
    primary: DiagnosticRecord
    secondary: tuple[DiagnosticRecord, ...]
    references: tuple[str, ...]
    parse_warnings: tuple[str, ...]
```

---

# 37. Primary-selection algorithm

```text
inspect authoritative process state
        ↓
inspect framework contract facts
        ↓
run canonical text patterns in priority order
        ↓
collect all non-conflicting matches
        ↓
select highest-priority primary
        ↓
retain secondary evidence
        ↓
if none and exit non-zero:
    generic fallback
        ↓
if none and complete stage contract:
    OK
```

A warning must not replace a fatal primary diagnosis.

---

# 38. No-match behavior

Unknown output is expected.

When no canonical text pattern matches:

### Non-zero exit

Use:

```text
DP-FALLBACK-001
```

or:

```text
DP-FALLBACK-002
```

### Zero exit with failed artifact/contract

Use the authoritative artifact or contract pattern.

### Zero exit with no contract failure

Return process-level `OK`; the stage still evaluates its own criteria.

### Suspicious text

Record a parse warning or observed excerpt.

Do not invent a specific diagnosis.

---

# 39. Pattern-version compatibility

A pattern may vary by:

- GF version;
- operating system;
- operation kind;
- command options;
- verbosity mode;
- stdout/stderr routing.

Version-specific rules must use:

```text
explicit GF version gate
capability probe
documented compatibility adapter
```

Silent fallback to a different meaning is prohibited.

Unknown newer GF output should produce:

- raw evidence;
- generic fallback where necessary;
- compatibility warning;
- fixture candidate for review.

---

# 40. Pattern change policy

## 40.1 Compatible refinement

Examples:

- tolerate an additional documented whitespace form;
- extract a new optional field;
- improve context without changing primary kind.

Requires tests and catalog update.

## 40.2 Breaking change

Examples:

- change `error_kind`;
- change precedence;
- broaden anchor significantly;
- change primary-message selection;
- remove a recognized form;
- change persisted pattern ID;
- change direct/downstream implications.

Requires:

1. fixture review;
2. consumer review;
3. schema review;
4. changelog entry;
5. compatibility note;
6. tests;
7. catalog version update.

---

# 41. Adding a canonical pattern

To promote an non-canonical evidence form to active:

```text
[ ] Raw stdout/stderr fixture captured
[ ] GF version recorded
[ ] Operation command recorded
[ ] Working directory recorded
[ ] Exit code recorded
[ ] At least one positive fixture added
[ ] Relevant negative fixture added
[ ] Precedence defined
[ ] Error kind defined
[ ] Severity defined
[ ] Extraction rules defined
[ ] False-positive risks reviewed
[ ] Both-stream behavior tested
[ ] Report behavior tested
[ ] This catalog updated
```

One anecdotal message is insufficient evidence for a broad canonical pattern.

---

# 42. Pattern replacement and removal

A canonical pattern may be replaced or removed when:

- supported GF versions no longer emit it;
- a more structured canonical pattern replaces it;
- it causes unacceptable false positives;
- its semantic meaning is incorrect.

The change requires:

- preservation of the old ID in compatibility documentation when persisted records may contain it;
- a replacement ID when applicable;
- fixture review;
- reader and report compatibility review;
- changelog and migration notes;
- complete tests;
- catalog version update.

Canonical writers emit only the current pattern set. Compatibility readers may interpret historical pattern IDs without reintroducing them into current matching.

---

# 43. Fixture organization

Fixture layout:

```text
tests/fixtures/diagnostics/
├── compile/
│   ├── internal-generate-pmcfg/
│   │   ├── metadata.json
│   │   ├── stdout.bin
│   │   └── stderr.bin
│   ├── type-expected-inferred/
│   ├── syntax-error/
│   └── nonzero-unknown/
├── scenarios/
├── pgf/
├── process/
└── negative/
```

Fixture metadata records:

```text
fixture ID
GF version
platform
operation kind
command
exit code
execution state
expected pattern IDs
expected primary
notes
```

Raw fixture bytes should remain unchanged.

---

# 44. Unit tests

Diagnostic tests:

```text
tests/diagnostics/
├── test_pattern_registry.py
├── test_process_patterns.py
├── test_internal_patterns.py
├── test_type_patterns.py
├── test_syntax_patterns.py
├── test_warning_patterns.py
├── test_reference_extraction.py
├── test_fallback_patterns.py
├── test_pattern_precedence.py
├── test_stream_policy.py
├── test_unicode_diagnostics.py
└── test_unknown_output.py
```

---

# 45. Required compatibility tests

Compatibility tests cover:

```text
timeout → TIMEOUT
Internal error in GeneratePMCFG → INTERNAL
expected + inferred → TYPE
Syntax error → SYNTAX
Parse error → SYNTAX
Unexpected token → SYNTAX
non-zero useful line → OTHER
non-zero no useful line → OTHER fallback
zero exit no failure → OK
```

Also test:

- stdout-only;
- stderr-only;
- split expected/inferred streams;
- progress-line exclusion;
- `.gf` reference extraction;
- nested missing-inflection detail;
- warning does not erase fatal error.

---

# 46. Negative tests

Every broad anchor needs false-positive tests.

Required examples:

- scenario linguistic text contains `expected:`;
- only `expected:` exists;
- only `inferred:` exists;
- report prose contains `Internal error`;
- source file text printed by a scenario contains `Syntax error`;
- gold file content contains a diagnostic phrase;
- process prints `timeout` but did not time out;
- filename contains `Error`;
- warning contains `.gf` path but no failure;
- progress output begins with `Writing`.

Operation context and raw-source identity must prevent accidental classification.

---

# 47. Integration tests with GF

When real GF is available, maintain a small fixture grammar that can produce:

- successful compile;
- source syntax error;
- type mismatch with expected/inferred structure where supported;
- failed entrypoint or import;
- successful scenario;
- failed scenario;
- PGF build;
- missing artifact simulation at the framework layer.

An internal GF crash must not be deliberately induced in routine integration tests unless a safe stable fixture exists.

Captured historical evidence may test `DP-GFINT-001`.

---

# 48. Reports

Reports consume normalized diagnostic records.

They must not:

- run regular expressions over raw logs independently;
- change error kinds;
- select a different primary pattern;
- infer direct/downstream causality from prose;
- hide unknown output;
- discard pattern IDs when available.

Reports show:

```text
error kind
primary message
pattern ID
confidence where useful
source evidence paths
secondary details
```

Human-facing reports may omit low-level fields in concise mode.

---

# 49. Top-error aggregation

Top-error aggregation uses a stable normalized key.

Canonical key:

```text
error_kind + normalized primary message
```

Pattern ID may also be retained.

Rules:

- do not aggregate by raw full stack trace;
- do not merge different error kinds only because messages match;
- preserve counts;
- deterministic order: descending count, then message;
- unknown fallbacks remain distinguishable.

---

# 50. Causal classification boundary

Diagnostic pattern:

```text
what kind of evidence is this?
```

Causal classifier:

```text
is this file the root failure, downstream, ambiguous, noise, or skipped?
```

Rules:

- `TYPE` and `SYNTAX` are likely direct only after context review;
- `INTERNAL`, `TIMEOUT`, and framework `SCRIPT` were historically treated as obvious direct file failures, but the causal model respects operation and prerequisite context;
- `.gf` references are candidate dependency evidence;
- a referenced failing provider may support downstream classification;
- a self-reference may support direct classification;
- the pattern parser must not assign `blocked_by`.

---

# 51. Static-scan separation

Static scan patterns such as:

```text
runtime string match
untyped Str patterns
trailing spaces
suspicious comment tokens
```

are not entries in this diagnostic catalog unless GF itself emits corresponding output.

A static finding:

- may coexist with compile success;
- does not become `TYPE` or `SYNTAX`;
- has its own scan evidence;
- must not alter GF raw diagnostics.

---

# 52. Security rules

Diagnostic parsing must:

- treat output as untrusted text;
- avoid evaluating output;
- avoid terminal escape rendering;
- remove or neutralize ANSI sequences only in derived views;
- bound regex complexity;
- avoid catastrophic backtracking;
- bound excerpt size;
- validate extracted paths;
- never open arbitrary paths mentioned by output without containment checks;
- redact secrets in commands and environment evidence.

Regular expressions are precompiled and reviewed.

---

# 53. Performance rules

The parser:

- read bounded evidence where practical;
- support large file-backed logs;
- avoid repeated full-log scans for each consumer;
- run one central parse pass;
- use deterministic ordered patterns;
- avoid unbounded regex backtracking;
- preserve enough context for diagnosis;
- not load runaway generation output entirely into memory.

Output limits are enforced by the process layer.

---

# 54. Diagnostic registry review checklist

```text
[ ] Pattern ID is unique
[ ] Operation scope is explicit
[ ] Stream policy is explicit
[ ] Priority is explicit
[ ] Confidence is explicit
[ ] Error kind is valid
[ ] Severity is valid
[ ] Positive fixture exists
[ ] Negative fixture exists
[ ] Extraction rules are documented
[ ] False-positive risk is documented
[ ] Version sensitivity is documented
[ ] Raw evidence remains available
[ ] Parser and reports have one owner each
[ ] Schema impact was reviewed
```

---

# 55. Drift indicators

Diagnostic drift exists when:

- a regex appears outside the diagnostic owner for GF output;
- a report parses raw GF logs;
- stdout is inspected but stderr is ignored;
- pattern precedence differs by caller;
- a pattern ID changes without migration;
- an observed phrase becomes active without fixtures;
- a warning becomes fatal silently;
- a generic anchor is broadened without negative tests;
- process timeout is inferred from text;
- exit code zero overrides missing artifacts;
- static-scan findings are labeled as GF errors;
- `.gf` references automatically become blockers;
- normalization removes a diagnostic anchor;
- a new GF version produces generic fallback repeatedly without review;
- unknown output is discarded;
- diagnostic class is assigned inside the process runner;
- CLI and GUI display different error kinds for the same result.

Any drift indicator requires catalog and contract review.

---

# 56. Canonical pattern index

| Pattern ID | Meaning | Kind | Confidence |
|---|---|---|---|
| `DP-PROC-001` | Process timeout | `TIMEOUT` | authoritative |
| `DP-PROC-002` | Launch failure | `TOOL` | authoritative |
| `DP-PROC-003` | Cancellation | `CANCELLED` | authoritative |
| `DP-PROC-004` | Output limit | `OUTPUT_LIMIT` | authoritative |
| `DP-PROC-005` | Decode failure | `IO` | authoritative |
| `DP-GFINT-001` | GeneratePMCFG internal error | `INTERNAL` | high |
| `DP-GFTYPE-001` | Expected/inferred mismatch | `TYPE` | high |
| `DP-GFSYN-001` | Syntax/parse/unexpected token | `SYNTAX` | medium |
| `DP-FALLBACK-001` | Non-zero with candidate line | `OTHER` | medium |
| `DP-FALLBACK-002` | Non-zero without message | `OTHER` | authoritative |
| `DP-FALLBACK-003` | Completed with no failure evidence | `OK` | authoritative |
| `DP-GFLOAD-001` | `.gf` reference extraction | none | medium |
| `DP-SCEN-001` | Required scenario missing | `CONFIG` | authoritative |
| `DP-SCEN-002` | Scenario section incomplete | `CONTRACT` | authoritative |
| `DP-ART-001` | Required artifact missing | `ARTIFACT` | authoritative |
| `DP-ART-002` | Required artifact empty | `ARTIFACT` | authoritative |
| `DP-NORM-001` | Normalization failed | `NORMALIZATION` | authoritative |
| `DP-NORM-002` | Unsupported normalization version | `NORMALIZATION` | authoritative |
| `DP-GOLD-001` | Gold mismatch | `GOLD` | authoritative |
| `DP-GOLD-002` | Required gold missing | `CONFIG`/`GOLD` | authoritative |
| `DP-GOLD-003` | Gold schema/version mismatch | `GOLD` | authoritative |

---

# 57. Non-canonical evidence index

| Evidence wording or family | Treatment |
|---|---|
| explicit `cannot unify` wording | preserve as evidence; no dedicated canonical pattern |
| scenario-command syntax subtype | use `DP-GFSYN-001` plus operation context |
| `Cannot find an inflection rule` | secondary detail under the primary pattern or generic fallback |
| missing-linearization warning wording | preserve as warning evidence; project release policy decides consequence |
| generic `Warning:` | no broad matcher |
| module name without `.gf` path | no general extractor |
| unsupported scenario-command wording | syntax or generic fallback |
| fatal-looking generic anchors | excerpt selection only; no specific diagnosis |

These evidence forms do not have canonical pattern IDs.

---

# 58. Legacy parser compatibility

The predecessor parser recognizes:

```text
timeout state
Internal error in GeneratePMCFG
expected/inferred type structure
Syntax error
Parse error
Unexpected token
generic non-zero output
zero-exit OK
```

Compatibility rules:

1. preserve existing tested meanings;
2. preserve raw stdout and stderr paths;
3. stop using synthetic timeout exit codes as canonical facts;
4. return multiple diagnostic records where evidence supports them;
5. retain `first_error` compatibility fields through adapters;
6. centralize `.gf` reference extraction;
7. separate evidence excerpts from pattern classification;
8. add operation context;
9. add pattern IDs;
10. keep classifier responsibility separate.

---

# 59. Legacy result adapter

`parse_compile_summary(...)` is a compatibility wrapper for predecessor callers.

The wrapper may:

- build diagnostic evidence;
- invoke the new parser;
- select the compatible primary record;
- populate legacy `CompileSummary` fields.

It must not:

- maintain a separate regex registry;
- use different precedence;
- discard secondary evidence before raw paths are retained;
- create a second definition of error kinds.

---

# 60. Diagnostic invariants

1. Every canonical pattern has a stable ID.
2. Every canonical text pattern has fixtures.
3. Process facts outrank text inference.
4. Both stdout and stderr are considered.
5. Raw streams remain separate and immutable.
6. Exit code is not complete diagnosis.
7. Timeout is detected from process state.
8. Launch failure is not a GF error.
9. `GeneratePMCFG` internal error remains `INTERNAL`.
10. Expected/inferred structure remains `TYPE`.
11. Syntax/parse/unexpected-token source messages remain `SYNTAX`.
12. Unknown non-zero output falls back to `OTHER`.
13. Unknown output is never discarded.
14. Warnings do not silently become failures.
15. Non-canonical evidence does not create a specific diagnosis.
16. `.gf` references are evidence, not automatic blockers.
17. Diagnostic parsing and causal classification remain separate.
18. Static scan findings remain separate from GF diagnostics.
19. Reports consume structured diagnostics.
20. New GF versions trigger fixture review when output changes.
21. Pattern changes are coordinated with schemas and tests.
22. No broad regex is accepted without false-positive tests.
23. Linguistic output is not normalized to force a diagnostic match.
24. One diagnostic owner prevents parser drift.

---

# 61. Governing rule

GF Wordbench must prefer an honest generic diagnosis over a specific unsupported diagnosis.

The permitted evidence chain is:

```text
raw process facts and streams
        → documented canonical pattern
        → bounded field extraction
        → normalized diagnostic record
        → stage result
        → causal classification
        → report
```

When no documented pattern applies:

```text
preserve the evidence
use a safe fallback
mark uncertainty
add a fixture before adding a new rule
```
