# GF Wordbench — Known Diagnostic Patterns

**Document ID:** `GF-WB-DIAG-KNOWN-PATTERNS`  
**Status:** Normative diagnostic catalog  
**Applies to:** GF compiler output, GF shell/scenario output, process failures, artifact checks, and GF Wordbench contract failures  
**Primary implementation owner:** `app/audit/diagnostics.py`  
**Legacy implementation source:** `app/utils/gf_utils.py`  
**Causal classification owner:** `app/audit/classifier.py`  
**Catalog version:** `1.0`  
**Target product state:** Final architecture  
**Last reviewed:** 2026-07-22  

---

## 1. Purpose

This document defines the diagnostic patterns that GF Wordbench is allowed to recognize and normalize.

It exists to prevent three forms of drift:

1. two components recognizing the same GF output differently;
2. a new regular expression silently changing diagnostic meaning;
3. an observed message being promoted to a stable rule without evidence.

The catalog records:

- stable pattern identifiers;
- pattern status;
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

> A diagnostic pattern is active only when its meaning is documented, its evidence is preserved, and its behavior is tested.

A regular expression alone is not a diagnostic contract.

Every active pattern must have:

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

1. persisted-schema lock for serialized enum values;
2. process-execution model for launch, timeout, cancellation, and capture facts;
3. error-handling model for framework error semantics;
4. this catalog for pattern identity and normalized interpretation;
5. classifier documentation for direct/downstream causality.

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
active pattern matching
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

## 8. Pattern status

Canonical catalog statuses:

```text
active
observed
experimental
deprecated
retired
reserved
```

### 8.1 Active

Implemented, tested, and permitted for normal classification.

### 8.2 Observed

Present in a captured fixture or historical evidence but not stable enough for automatic classification.

### 8.3 Experimental

Implemented behind explicit diagnostic or compatibility policy.

### 8.4 Deprecated

Still recognized for compatibility but scheduled for removal or replacement.

### 8.5 Retired

No longer matched. The ID remains reserved.

### 8.6 Reserved

Identity allocated for a semantic class whose exact GF text patterns are not yet approved.

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
    status: str
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

Recommended diagnostic severity:

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

The final centralized reference is authoritative.

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

The parser should return:

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

# 16. Active process patterns

## DP-PROC-001 — Process timeout

**Status:** active  
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

**Status:** active  
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

**Status:** active  
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

**Status:** active  
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

**Status:** active  
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

# 17. Active GF internal patterns

## DP-GFINT-001 — GeneratePMCFG internal error

**Status:** active  
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

This nested text is cataloged separately as `DP-GFGEN-001`.

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

# 18. Active GF type patterns

## DP-GFTYPE-001 — Expected/inferred type mismatch

**Status:** active  
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

## DP-GFTYPE-002 — Explicit unification wording

**Status:** observed  
**Confidence:** medium  
**Error kind:** `TYPE`  
**Severity:** error  

### Observed examples

```text
cannot unify
cannot unify the information
```

### Current policy

This wording may be preserved in `first_error`, but it must not be promoted to active automatic `TYPE` classification until representative raw GF fixtures are added.

### Promotion requirements

- captures from supported GF versions;
- positive and negative fixtures;
- source-location extraction test;
- interaction test with expected/inferred pattern;
- false-positive review.

---

# 19. Active GF syntax patterns

## DP-GFSYN-001 — GF source syntax error

**Status:** active  
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

## DP-GFSYN-002 — Scenario command syntax failure

**Status:** reserved  
**Confidence:** not assigned  
**Error kind:** `SCRIPT` or `SYNTAX`  
**Severity:** error  

This ID is reserved for a scenario-specific command parser diagnostic when supported fixtures prove that it can be distinguished reliably from source-module syntax errors.

Until then, `DP-GFSYN-001` remains the text pattern and the operation context supplies scenario scope.

---

# 20. Active generic fallback

## DP-FALLBACK-001 — Non-zero exit with diagnostic line

**Status:** active  
**Confidence:** medium  
**Operation scope:** any GF process  
**Source:** both streams  
**Error kind:** `OTHER`  
**Severity:** error  

### Trigger

```text
process completed
exit_code != 0
no higher-precedence active pattern matched
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
- This pattern must not run before active specific patterns.

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

**Status:** active  
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
- This condition should be included in compatibility investigation when new GF versions are introduced.

---

## DP-FALLBACK-003 — Zero exit with no failure evidence

**Status:** active  
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

## DP-FALLBACK-004 — Unknown fatal-looking output

**Status:** experimental  
**Confidence:** low  
**Error kind:** `OTHER`  
**Severity:** warning or error by operation policy  

### Candidate generic anchors

Observed evidence extractors have used:

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
- add a dedicated pattern when a stable meaning is proven.

---

# 21. Observed generation/runtime patterns

## DP-GFGEN-001 — Missing inflection rule runtime detail

**Status:** observed  
**Confidence:** medium  
**Operation scope:** compilation, PGF construction, generation, scenario runtime  
**Source:** stdout or stderr  
**Provisional error kind:** `INTERNAL` or `TOOL` depending on primary context  
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

- If nested under `DP-GFINT-001`, retain as secondary runtime detail.
- Do not replace the primary `GeneratePMCFG` internal diagnosis.
- If observed without a higher-precedence pattern, retain as `OTHER` until fixtures establish stable semantics.

### Promotion requirements

- successful reproduction;
- supported-version captures;
- direct operation context;
- distinction between project runtime failure and GF internal failure;
- positive and negative tests.

---

# 22. Observed warning patterns

## DP-GFWARN-001 — Missing linearization type warning

**Status:** observed  
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

### Promotion requirements

- raw captures from supported GF versions;
- category/type extraction tests;
- coexistence test with successful exit;
- release-policy integration test.

---

## DP-GFWARN-002 — Generic GF warning

**Status:** reserved  
**Confidence:** not assigned  
**Severity:** warning  

A broad `Warning:` matcher is not active because:

- warning text may be version-dependent;
- not every warning has the same consequence;
- project policy may differ;
- scenario output may intentionally contain the word.

New warning families should receive dedicated IDs.

---

# 23. Module and file reference patterns

## DP-GFLOAD-001 — Referenced GF source path

**Status:** active as extraction helper  
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

## DP-GFLOAD-002 — Referenced GF module name

**Status:** reserved  
**Confidence:** not assigned  

Reserved for stable extraction of module identifiers not accompanied by `.gf` paths.

No general module-name regex is active in this catalog because ordinary GF output may contain many capitalized identifiers.

---

# 24. Wordbench-origin diagnostic patterns

These are not GF messages.

They must be labeled as framework or contract evidence.

## DP-SCEN-001 — Required scenario missing

**Status:** active  
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

**Status:** active  
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

## DP-SCEN-003 — Unsupported scenario command evidence

**Status:** experimental  
**Confidence:** medium  
**Source:** GF output plus scenario context  
**Error kind:** `SCRIPT`  
**Severity:** error  

This pattern becomes active only when supported GF fixtures define stable unsupported-command output.

Until then, such output falls through syntax or generic non-zero handling.

---

## DP-ART-001 — Required artifact missing

**Status:** active  
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

**Status:** active  
**Confidence:** authoritative  
**Source:** filesystem observation  
**Error kind:** `ARTIFACT`  
**Severity:** error  

Applies when an artifact contract requires a positive minimum size.

---

## DP-NORM-001 — Normalization failed

**Status:** active  
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

**Status:** active  
**Confidence:** authoritative  
**Source:** normalizer/schema validation  
**Error kind:** `NORMALIZATION`  
**Severity:** error  

---

## DP-GOLD-001 — Gold mismatch

**Status:** active  
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

**Status:** active  
**Confidence:** authoritative  
**Source:** gold preflight/comparator  
**Error kind:** `CONFIG` or `GOLD` according to centralized policy  
**Severity:** error  

Missing required gold is never an automatic pass.

---

## DP-GOLD-003 — Gold schema/version mismatch

**Status:** active  
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
| `cannot unify ...` | Observed candidate `DP-GFTYPE-002` |
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

These anchors may select excerpts without determining final error kind.

Excerpt bounds must prevent oversized reports.

---

# 34. Pattern registry model

Recommended implementation:

```python
@dataclass(frozen=True, slots=True)
class DiagnosticPattern:
    pattern_id: str
    status: str
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

# 35. Recommended implementation files

Final architecture:

```text
app/audit/diagnostics.py
    diagnostic orchestration and public API

app/audit/diagnostic_patterns.py
    registry and active pattern definitions

app/audit/diagnostic_extractors.py
    paths, locations, expected/inferred fields, excerpts

app/audit/classifier.py
    direct/downstream/ambiguous classification
```

A smaller implementation may initially keep private pattern definitions inside `diagnostics.py`.

Do not preserve `app/utils/gf_utils.py` as the permanent owner of both source scanning and diagnostic parsing.

The final separation should be:

```text
scanner/source helpers
diagnostic output parsing
causal classification
```

---

# 36. Public API

Recommended interface:

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
run active text patterns in priority order
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

When no active text pattern matches:

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

# 41. Promotion workflow

To promote an observed pattern to active:

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

One anecdotal message is insufficient when the pattern is broad.

---

# 42. Deprecation workflow

A pattern may be deprecated when:

- GF no longer emits it in supported versions;
- a more structured pattern replaces it;
- it causes unacceptable false positives;
- its semantic meaning was wrong.

Deprecation requires:

- retained ID;
- replacement ID when applicable;
- compatibility window;
- tests for legacy reading when persisted;
- changelog entry;
- removal date or release target.

---

# 43. Fixture organization

Recommended layout:

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

Metadata should record:

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

Recommended tests:

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

# 45. Required current-baseline tests

The migration must preserve tests for:

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

Reports should show:

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

Top-error aggregation should use a stable normalized key.

Recommended key:

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
- `INTERNAL`, `TIMEOUT`, and framework `SCRIPT` were historically treated as obvious direct file failures, but the final model must still respect operation and prerequisite context;
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

Regular expressions should be precompiled and reviewed.

---

# 53. Performance rules

The parser should:

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
[ ] Status is explicit
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

# 56. Active-pattern index

| Pattern ID | Meaning | Status | Kind | Confidence |
|---|---|---|---|---|
| `DP-PROC-001` | Process timeout | active | `TIMEOUT` | authoritative |
| `DP-PROC-002` | Launch failure | active | `TOOL` | authoritative |
| `DP-PROC-003` | Cancellation | active | `CANCELLED` | authoritative |
| `DP-PROC-004` | Output limit | active | `OUTPUT_LIMIT` | authoritative |
| `DP-PROC-005` | Decode failure | active | `IO` | authoritative |
| `DP-GFINT-001` | GeneratePMCFG internal error | active | `INTERNAL` | high |
| `DP-GFTYPE-001` | Expected/inferred mismatch | active | `TYPE` | high |
| `DP-GFSYN-001` | Syntax/parse/unexpected token | active | `SYNTAX` | medium |
| `DP-FALLBACK-001` | Non-zero with candidate line | active | `OTHER` | medium |
| `DP-FALLBACK-002` | Non-zero without message | active | `OTHER` | authoritative |
| `DP-FALLBACK-003` | Completed with no failure evidence | active | `OK` | authoritative |
| `DP-GFLOAD-001` | `.gf` reference extraction | active helper | none | medium |
| `DP-SCEN-001` | Required scenario missing | active | `CONFIG` | authoritative |
| `DP-SCEN-002` | Scenario section incomplete | active | `CONTRACT` | authoritative |
| `DP-ART-001` | Required artifact missing | active | `ARTIFACT` | authoritative |
| `DP-ART-002` | Required artifact empty | active | `ARTIFACT` | authoritative |
| `DP-NORM-001` | Normalization failed | active | `NORMALIZATION` | authoritative |
| `DP-NORM-002` | Unsupported normalization version | active | `NORMALIZATION` | authoritative |
| `DP-GOLD-001` | Gold mismatch | active | `GOLD` | authoritative |
| `DP-GOLD-002` | Required gold missing | active | `CONFIG`/`GOLD` | authoritative |
| `DP-GOLD-003` | Gold schema/version mismatch | active | `GOLD` | authoritative |

---

# 57. Observed and reserved index

| Pattern ID | Meaning | Status | Promotion blocker |
|---|---|---|---|
| `DP-GFTYPE-002` | Explicit unification wording | observed | representative GF fixtures |
| `DP-GFSYN-002` | Scenario command syntax subtype | reserved | stable distinguishing output |
| `DP-GFGEN-001` | Missing inflection rule detail | observed | standalone semantic evidence |
| `DP-GFWARN-001` | Missing lincat warning | observed | supported-version captures |
| `DP-GFWARN-002` | Generic warning | reserved | too broad |
| `DP-GFLOAD-002` | Module-name extraction | reserved | false-positive-safe grammar |
| `DP-SCEN-003` | Unsupported scenario command | experimental | stable GF fixtures |
| `DP-FALLBACK-004` | Fatal-looking unknown output | experimental | intentionally generic |

---

# 58. Baseline migration

The inherited parser currently lives in:

```text
app/utils/gf_utils.py
```

It recognizes:

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

Migration target:

```text
app/audit/diagnostics.py
app/audit/diagnostic_patterns.py
app/audit/diagnostic_extractors.py
```

Migration rules:

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

# 59. Compatibility adapter

During migration, `parse_compile_summary(...)` may remain as a wrapper.

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

# 60. Final invariants

1. Every active pattern has a stable ID.
2. Every active text pattern has fixtures.
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
15. Observed patterns are not active without proof.
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

# 61. Final rule

GF Wordbench must prefer an honest generic diagnosis over a specific unsupported diagnosis.

The permitted evidence chain is:

```text
raw process facts and streams
        → documented active pattern
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
