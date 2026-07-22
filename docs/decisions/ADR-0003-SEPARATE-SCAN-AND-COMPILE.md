# ADR-0003 — Separate Static Scan and GF Compilation

**Status:** Accepted  
**Decision ID:** `ADR-0003`  
**Decision date:** `2026-07-22`  
**Applies to:** GF Wordbench framework and every active GF language project  
**Owners:** GF Wordbench maintainers  
**Supersedes:** None  
**Superseded by:** None  
**Related decisions:**
- `ADR-0001-SINGLE-ACTIVE-LANGUAGE.md`
- `ADR-0002-GF-AS-EXECUTION-ENGINE.md`
- `ADR-0005-FILE-AND-SCENARIO-RESULTS.md`

**Related normative documents:**
- `docs/architecture/ARCHITECTURE_OVERVIEW.md`
- `docs/architecture/ERROR_HANDLING_MODEL.md`
- `docs/validation/VALIDATION_PIPELINE.md`
- `docs/validation/STATIC_SCANNING.md`
- `docs/validation/COMPILATION_VALIDATION.md`
- `docs/diagnostics/ERROR_CLASSIFICATION.md`
- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`

---

## 1. Decision

GF Wordbench SHALL model static source scanning and GF compilation as two separate validation stages with separate request types, result types, statuses, evidence, ownership, configuration, diagnostics, and report sections.

The stages may operate on the same `.gf` source file, but they answer different questions:

```text
static scan:
Does the source text contain a documented suspicious pattern?

GF compilation:
Does the selected GF toolchain accept the source under the resolved project environment?
```

Static scanning is heuristic and framework-owned.

Compilation is authoritative for GF syntax, typing, module resolution, and compiler diagnostics.

A scan finding MUST NOT be represented as a GF compilation error.

A successful scan MUST NOT be represented as proof that a file compiles.

A successful compilation MUST NOT erase or automatically dismiss an independent scan finding.

---

## 2. Context

GF language development benefits from two different forms of feedback.

The first form is inexpensive source inspection.

A scanner can detect patterns such as:

- unresolved conflict markers;
- prohibited temporary markers;
- suspicious copied filenames;
- known project-specific anti-patterns;
- malformed or unexpected source text;
- patterns that frequently correlate with incomplete GF implementations;
- rules defined by the active project's static policy.

The second form is actual execution of GF.

Only GF can authoritatively determine whether a module:

- parses as GF;
- type-checks;
- resolves its imports;
- satisfies module interfaces;
- produces the expected tool artifacts;
- fails with a GF diagnostic;
- times out or cannot be executed under the configured toolchain.

The original GF Audit implementation already treated these as distinct result kinds:

```text
scan result
compile result
```

That separation is intentional and must remain part of GF Wordbench.

Without a locked decision, implementations tend to drift toward one of several unsafe designs:

- treating scanner rules as a substitute compiler;
- merging scan and compile messages into one undifferentiated error string;
- marking a file failed because of a warning-only scan finding;
- skipping GF compilation after a heuristic match;
- suppressing scan findings when compilation succeeds;
- allowing reports to infer compilation status from scan data;
- classifying scanner findings as direct or downstream GF failures;
- giving CLI and GUI different interpretations of the same file.

This ADR prevents those forms of drift.

---

## 3. Forces

The decision balances the following forces.

### 3.1 Fast feedback

Static scanning is usually faster than launching GF and can provide immediate, focused guidance.

### 3.2 Authoritative correctness

GF remains the authority for GF language semantics and compiler acceptance.

### 3.3 False-positive containment

Heuristic source rules may identify suspicious text that is nevertheless valid and intentional.

### 3.4 False-negative containment

A clean scan does not prove that GF accepts the source.

### 3.5 Diagnostic clarity

Users must know whether a message came from:

- source-policy inspection;
- GF itself;
- process execution;
- artifact verification;
- downstream classification.

### 3.6 Independent evolution

Scanner rules and GF compiler integration change for different reasons and at different rates.

### 3.7 Testability

The scanner must be testable without a GF installation.

The compiler must be testable through process fixtures and real-GF integration tests.

### 3.8 Release policy

A project may promote selected static findings to release blockers without pretending that they are compiler failures.

### 3.9 Evidence preservation

Scan evidence and compiler stdout/stderr require different artifact contracts.

---

## 4. Definitions

### 4.1 Static scan

A deterministic inspection of source bytes or decoded source text performed by GF Wordbench without invoking GF.

### 4.2 Scan rule

A named, version-controlled rule that detects one documented source condition.

### 4.3 Scan finding

One occurrence reported by a scan rule.

### 4.4 Scan result

The structured collection of findings and scan-stage execution information for one file.

### 4.5 Compilation

Invocation of the configured GF executable against one selected GF source target.

### 4.6 Compile diagnostic

A normalized interpretation derived from GF stdout, GF stderr, process state, exit status, and required artifact checks.

### 4.7 Compile result

The structured outcome of one compilation request.

### 4.8 Authoritative GF diagnostic

Evidence emitted by GF or derived directly from its process/artifact contract.

### 4.9 Policy blocker

A finding that project or framework policy declares sufficient to fail a validation gate.

A policy blocker is not necessarily a GF compiler error.

---

## 5. Stage ownership

### 5.1 Scanner owner

Recommended module:

```text
app/audit/scanner.py
```

The scanner owns:

- source-text inspection;
- scan-rule execution;
- scan finding construction;
- scan-stage status;
- scan raw/detail artifacts;
- scanner-specific diagnostic codes.

The scanner does not own:

- GF process invocation;
- GF path construction;
- GF version compatibility;
- compile result interpretation;
- dependency-cascade classification;
- user-facing aggregate reports.

### 5.2 Compiler owner

Canonical module:

```text
app/audit/compiler.py
```

The compiler owns:

- compilation request construction;
- GF process invocation through the process layer;
- timeout handling;
- stdout/stderr capture;
- exit-code capture;
- required compile-artifact checks;
- compiler diagnostic extraction;
- compile result construction.

The compiler does not own:

- source-policy scanning;
- dependency-cascade classification;
- aggregate reporting;
- gold comparison;
- release decision aggregation.

### 5.3 Orchestrator owner

Recommended module:

```text
app/audit/audit_core.py
```

The orchestrator owns:

- deciding which stages apply;
- ordering stage execution;
- preserving both results;
- applying mode and project policy;
- assembling the file-level result;
- passing finalized results to classification and reporting.

The orchestrator MUST NOT reinterpret scan findings as GF diagnostics.

---

## 6. Result separation

One selected source file may have both:

```text
ScanResult
CompileResult
```

The two objects remain independently addressable.

Recommended file-level composition:

```python
@dataclass(frozen=True, slots=True)
class FileResult:
    file_path: str
    fingerprint: str | None
    scan: ScanResult | None
    compile: CompileResult | None
    diagnostic_class: str
    overall_status: str
```

The exact persisted structure is governed by `PERSISTED_SCHEMA_LOCK.md`.

### 6.1 Absence

A missing stage result is represented explicitly.

Examples:

```text
scan = null
reason = scan_not_selected
```

```text
compile = null
reason = no_compile_mode
```

Absence MUST NOT be converted to an empty successful result.

### 6.2 Separate status

Each stage has its own canonical validation status:

```text
OK
FAIL
ERROR
SKIPPED
```

### 6.3 File-level status

The file-level overall status is derived by the orchestrator from applicable policy.

It does not replace stage statuses.

---

## 7. Scan semantics

### 7.1 Scan `OK`

The scanner executed successfully and found no finding that violates the selected scan criterion.

A scan may be `OK` with informational observations if policy defines them as non-failing metadata.

### 7.2 Scan `FAIL`

The scanner executed successfully and found at least one finding classified as blocking for the selected validation policy.

### 7.3 Scan `ERROR`

The scanner could not inspect the file reliably.

Examples:

- file disappeared;
- file could not be read;
- decoding policy failed;
- rule registry was invalid;
- scanner internal contract failed.

### 7.4 Scan `SKIPPED`

Static scanning was intentionally not selected or was inapplicable.

### 7.5 Finding severity

Recommended severities:

```text
info
warning
error
```

Severity and release-blocking status remain separate.

A project may treat a warning code as blocking in release mode.

### 7.6 Finding identity

Each finding SHOULD contain:

```text
rule_id
severity
message
file_path
line
column
excerpt
blocking
documentation_reference
```

### 7.7 No GF error kind fabrication

A scan finding MUST NOT claim:

```text
TYPE
SYNTAX
INTERNAL
```

as though GF emitted that diagnosis.

Scanner-specific findings use stable scanner codes.

---

## 8. Compilation semantics

### 8.1 Compile `OK`

All applicable conditions hold:

- GF process launched;
- process completed;
- no timeout;
- exit code indicates success;
- no fatal GF diagnostic was recognized;
- required compile artifacts exist when enabled.

### 8.2 Compile `FAIL`

GF executed correctly, but the source did not satisfy compilation criteria.

Examples:

- GF syntax error;
- GF type error;
- unresolved import;
- interface mismatch;
- fatal GF diagnostic;
- required compiler artifact absent after an otherwise interpretable execution when policy classifies it as validation failure.

### 8.3 Compile `ERROR`

GF Wordbench could not execute or interpret the compilation contract.

Examples:

- executable missing;
- launch failure;
- timeout;
- invalid GF path;
- output directory failure;
- process result unavailable;
- artifact contract could not be evaluated.

### 8.4 Compile `SKIPPED`

Compilation was intentionally not executed.

Examples:

- explicit scan-only operation;
- `no_compile` compatibility option;
- prerequisite source-read error;
- mode excludes compilation.

A skipped compile is never equivalent to compile success.

### 8.5 Raw authority

Compilation interpretation considers:

```text
stdout
stderr
exit code
timeout state
launch state
required artifacts
```

No one signal alone is sufficient.

---

## 9. Stage ordering

Default per-file order:

```text
fingerprint
→ static scan
→ GF compilation
→ direct/downstream classification
→ file-level aggregation
```

### 9.1 Why scan normally runs first

Running scan first:

- provides fast findings;
- records source-read problems early;
- permits the same decoded-source evidence to support fingerprinting;
- does not require GF;
- does not establish compile status.

### 9.2 No default short-circuit

A scan `FAIL` MUST NOT skip compilation by default.

Reasons:

- the scanner may be wrong;
- compilation remains authoritative;
- users need both kinds of evidence;
- release diagnosis benefits from independent results;
- scanner changes must not silently reduce GF execution coverage.

### 9.3 Permitted prerequisite short-circuit

Compilation may be skipped when the scan/source-access stage proves that a valid source request cannot be constructed safely.

Examples:

- source path is outside the permitted project root;
- file cannot be read under required encoding policy;
- file no longer exists;
- source is not a regular file;
- security policy blocks the path.

In this case:

```text
scan status = ERROR
compile status = SKIPPED
compile skip reason = invalid_source_prerequisite
overall status = ERROR
```

### 9.4 Explicit fast-fail policy

A future explicit project policy may stop after selected security-critical static blockers.

Such a policy must:

- be opt-in;
- name the exact rule IDs;
- record the short-circuit;
- mark compile `SKIPPED`;
- remain prohibited for ordinary warning/error heuristics;
- update this ADR if it changes the default architecture.

---

## 10. Independence matrix

| Scan | Compile | Meaning |
|---|---|---|
| `OK` | `OK` | No blocking scan finding; GF accepted source |
| `FAIL` | `OK` | GF accepted source, but static project policy was violated |
| `OK` | `FAIL` | Scanner found no blocker; GF rejected source |
| `FAIL` | `FAIL` | Static policy and GF compilation both failed |
| `ERROR` | `SKIPPED` | Source could not be inspected safely enough to compile |
| `OK` | `ERROR` | Scan completed; toolchain/process failed |
| `SKIPPED` | `OK` | Compilation-only validation |
| `OK` | `SKIPPED` | Scan-only validation |
| `SKIPPED` | `SKIPPED` | No meaningful file validation; valid only under explicit operation |

This matrix is deliberate.

No row may be collapsed into another by report presentation.

---

## 11. Overall file status

The orchestrator computes overall status from applicable stages and policy.

Recommended precedence:

```text
ERROR > FAIL > OK > SKIPPED
```

### 11.1 Derivation

```text
if any required stage == ERROR:
    overall = ERROR
else if any required stage == FAIL:
    overall = FAIL
else if all applicable required stages == OK:
    overall = OK
else:
    overall = SKIPPED
```

### 11.2 Optional stages

An optional scan finding does not fail the file unless current policy declares it blocking.

### 11.3 Compile authority does not erase policy

A compile `OK` does not override a blocking scan `FAIL`.

The file may remain overall `FAIL` because a separate release/project policy was violated.

### 11.4 Scan success does not override GF

A scan `OK` never overrides compile `FAIL` or `ERROR`.

---

## 12. Diagnostic classification

The higher-level causal classification is:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

### 12.1 Compilation failures

`direct`, `downstream`, and `ambiguous` apply primarily to compilation failures and their dependency relationships.

### 12.2 Scan findings

A scan finding is not classified as downstream merely because another module imports the file.

Static findings describe local source text.

### 12.3 Scan-only file classification

Recommended mapping:

- no blocking finding and no compile failure: `ok`;
- blocking scan finding with compile OK: `direct` only if project policy explicitly defines local policy violations as direct file findings;
- informational scan output excluded from actionable results: `noise`;
- stage not selected: `skipped`.

The classifier must preserve source type so users can distinguish:

```text
direct compile failure
direct static-policy finding
```

### 12.4 Error kind

`error_kind` remains distinct from diagnostic class.

Compile examples:

```text
TYPE
SYNTAX
TOOL
TIMEOUT
```

Scan examples SHOULD use scanner diagnostic codes and an appropriate broad kind such as:

```text
CONFIG
IO
OTHER
```

when a shared broad kind is required.

---

## 13. Static policy levels

GF Wordbench SHOULD define three scan-policy levels.

### 13.1 Advisory

Findings are visible but do not change validation status.

### 13.2 Enforced

Selected findings produce scan `FAIL`.

### 13.3 Strict

All configured warnings or selected severity threshold findings become blocking.

### 13.4 Mode mapping

Recommended defaults:

| Mode | Scan policy |
|---|---|
| `quick` | enforced project blockers |
| `checkpoint` | enforced |
| `diagnostic` | advisory plus full evidence |
| `release` | strict project release policy |

The exact rule-to-policy mapping belongs to `STATIC_SCANNING.md` and project validation policy.

---

## 14. Scanner rule requirements

Every active rule MUST define:

```text
rule ID
name
purpose
scope
matching logic
severity
default blocking behavior
false-positive considerations
examples
exceptions
tests
```

### 14.1 Stable rule IDs

Recommended form:

```text
SCAN-<DOMAIN>-<NUMBER>
```

Examples:

```text
SCAN-SOURCE-001
SCAN-TEMP-002
SCAN-PROJECT-003
```

### 14.2 Rule changes

Changing matching semantics requires:

- tests;
- release classification;
- documentation;
- project gold/report review when outputs change.

### 14.3 Language neutrality

Framework scan rules should be language-neutral.

Language-specific rules belong to project configuration or a documented project scanner extension.

### 14.4 No speculative parser

The scanner MUST NOT evolve into a partial undocumented GF parser.

Rules should remain bounded, explicit text/pattern checks unless a formal parser integration is separately designed.

---

## 15. Compiler requirements

Compilation remains governed by the external-tool contract.

At minimum, the compiler records:

```text
executable
ordered arguments
working directory
GF path
timeout
stdout path
stderr path
exit code
execution state
duration
diagnostics
artifact list
```

### 15.1 No scanner dependency

The compiler accepts a valid compile request.

It MUST NOT inspect scanner prose to decide command construction.

### 15.2 Shared source identity

The orchestrator may provide the same normalized source path and fingerprint to both stages.

### 15.3 No compile emulation

The scanner cannot satisfy a request for compilation.

### 15.4 No compiler policy scanning

The compiler should not duplicate scanner rules by searching source text before launch.

Preflight path/security validation remains allowed.

---

## 16. Evidence layout

Canonical run ownership keeps evidence separate.

```text
raw/scan/
raw/compile/
```

### 16.1 Scan evidence

Recommended examples:

```text
raw/scan/<safe-file-key>.txt
```

or structured result evidence under the canonical scan layout.

### 16.2 Compile evidence

Canonical examples:

```text
raw/compile/<safe-file-key>.out.txt
raw/compile/<safe-file-key>.err.txt
```

### 16.3 Details

A combined detail report may display both result types.

It must label sections clearly:

```text
Static Scan
GF Compilation
Classification
```

### 16.4 No evidence overwriting

The scanner cannot write into `raw/compile/`.

The compiler cannot write into `raw/scan/`.

### 16.5 Aggregate logs

Aggregate reports may combine references, but individual artifacts remain authoritative.

---

## 17. Reporting

Reports must preserve stage identity.

### 17.1 Machine summary

`summary.json` should expose separate fields/objects for:

```text
scan
compile
```

### 17.2 Human summary

Human reports should distinguish:

```text
Static finding
GF compile failure
Tool execution error
```

### 17.3 AI-ready report

`AI_READY.md` must not present a heuristic finding as a quotation from GF.

It should identify evidence source explicitly.

### 17.4 Top errors

Top-error grouping must preserve category/source.

Recommended conceptual key:

```text
source + diagnostic code + normalized message
```

This avoids grouping a scanner message and a GF error merely because wording resembles.

### 17.5 Counts

Separate counts SHOULD be available for:

```text
files with scan blockers
files with scan warnings
files compile OK
files compile FAIL
files compile ERROR
files compile SKIPPED
```

An aggregate overall count may also be reported.

---

## 18. CLI behavior

The CLI should support intentional stage selection.

Recommended concepts:

```text
scan enabled
compile enabled
scan-only
compile-only
```

Exact flags belong to `CLI_REFERENCE.md`.

### 18.1 Default

Normal validation modes run both applicable stages.

### 18.2 Scan-only

A scan-only operation:

- does not require GF;
- records compilation as not selected/skipped;
- cannot prove release readiness;
- must not label files compiled.

### 18.3 Compile-only

A compile-only operation:

- skips scanner findings;
- remains valid for focused GF diagnosis;
- may not satisfy release policy requiring static checks.

### 18.4 Legacy `no_compile`

During migration, `no_compile` may request scan-only behavior.

Canonical product semantics should eventually expose a positive explicit stage-selection model.

---

## 19. GUI behavior

The GUI must show separate indicators for:

```text
Scan
Compile
Overall
```

### 19.1 Display rules

- scan warning is not displayed as GF error;
- compile failure remains visible when scan passes;
- scan blocker remains visible when compile passes;
- skipped stage is visible;
- tool error is visually distinct from validation failure.

### 19.2 Shared semantics

The GUI consumes the same results and policy as the CLI.

It does not recompute file status independently.

---

## 20. Release behavior

Release mode requires both stages when project/framework release policy requires static scanning.

### 20.1 Compilation gate

Compilation failure blocks release independently.

### 20.2 Static gate

A blocking static-policy finding blocks release independently.

### 20.3 No compensation

The following is prohibited:

```text
compile OK compensates for blocking scan finding
```

and:

```text
scan OK compensates for compile failure
```

### 20.4 Required skip

A required scan or compile stage with `SKIPPED` blocks release.

### 20.5 Evidence

Release evidence must preserve both result sets and their raw/detail artifacts.

---

## 21. Performance

### 21.1 Scanner performance

The scanner should:

- read each file once when practical;
- precompile regular expressions;
- avoid quadratic rule behavior;
- avoid unbounded parsing;
- remain deterministic.

### 21.2 Compiler performance

Compilation cost is controlled through:

- mode-specific file selection;
- checkpoint ordering;
- timeouts;
- run-owned artifact directories;
- optional caching only under a future explicit contract.

### 21.3 Parallelism

Scanning may be parallelized independently of compilation.

Compilation parallelism requires GF/toolchain and artifact-isolation validation.

### 21.4 Ordering

Result serialization remains deterministic regardless of execution parallelism.

---

## 22. Security

### 22.1 Scanner

The scanner treats source text as untrusted input.

It MUST NOT:

- execute matched text;
- evaluate source as Python;
- invoke a shell;
- follow unsafe paths;
- load arbitrary plugins without contract.

### 22.2 Compiler

The compiler uses ordered process arguments with no implicit shell.

### 22.3 Source containment

Both stages validate source path containment through shared path contracts.

### 22.4 Sensitive excerpts

Scanner excerpts and GF output may contain local paths or source text.

Reports apply bounded evidence and secret rules without modifying raw evidence.

---

## 23. Consequences

### 23.1 Positive consequences

- GF remains the authoritative compiler.
- Heuristic rules remain useful without being overstated.
- Scan and compile false positives/negatives are visible.
- Users can run scan-only checks without GF.
- Compiler integration can evolve independently.
- Static policy can become a release gate without falsifying GF results.
- Reports provide clearer root-cause evidence.
- Unit tests remain fast for scanner behavior.
- Real-GF tests focus on compiler contracts.
- Existing GF Audit behavior is preserved.
- AI-assisted debugging receives clearly sourced evidence.

### 23.2 Negative consequences

- File results are more complex.
- Reports need two result sections.
- Status aggregation needs explicit policy.
- More tests are required.
- Users may need to understand why compile `OK` and overall `FAIL` can coexist.
- Duplicate-looking messages may appear from different sources.
- Configuration must distinguish scan and compile selection.

### 23.3 Accepted complexity

This complexity is intentional because collapsing the stages would reduce correctness and diagnostic trust.

---

## 24. Alternatives considered

### 24.1 Alternative A — Use only GF compilation

**Rejected.**

Advantages:

- simpler result model;
- no heuristic false positives;
- one apparent authority.

Disadvantages:

- loses fast project-policy feedback;
- cannot detect non-GF textual/process issues;
- requires GF for every basic inspection;
- removes a proven feature of the existing audit tool;
- makes release-specific source policy harder to express.

### 24.2 Alternative B — Use static scan as a pre-compiler

**Rejected.**

This would require the scanner to decide whether GF should run.

It risks:

- false positives suppressing authoritative evidence;
- accidental partial reimplementation of GF;
- divergence across GF versions;
- unclear ownership.

### 24.3 Alternative C — Merge all findings into one status/message list

**Rejected.**

This loses:

- source provenance;
- process state;
- GF authority distinction;
- separate retry/skip semantics;
- reliable automation.

### 24.4 Alternative D — Run scan only when compilation fails

**Rejected.**

A successful compile can still violate project static policy.

The approach would also make scan coverage dependent on GF outcome.

### 24.5 Alternative E — Run compilation only when scan passes

**Rejected.**

Heuristic findings cannot safely gate authoritative compilation by default.

### 24.6 Alternative F — Treat scanner findings as compiler warnings

**Rejected.**

The warnings did not originate from GF and must not be attributed to it.

---

## 25. Implementation constraints

The implementation SHALL satisfy all of the following.

1. `scanner.py` does not launch GF.
2. `compiler.py` does not run static scanner rules.
3. Both stages return structured results.
4. Both stages have independent statuses.
5. Both stages preserve independent evidence.
6. Scan blockers do not skip compilation by default.
7. Scan success does not imply compile success.
8. Compile success does not erase scan findings.
9. Direct/downstream classification does not originate in either stage.
10. Reports consume results; they do not rerun either stage.
11. CLI and GUI use the same aggregation policy.
12. Release mode requires all configured mandatory stages.
13. Persisted schema preserves stage provenance.
14. Unknown scanner codes and GF diagnostic kinds are not silently reinterpreted.
15. Stage selection is explicit in the resolved run configuration.

---

## 26. Recommended interfaces

### 26.1 Scan request

```python
@dataclass(frozen=True, slots=True)
class ScanRequest:
    file_path: Path
    project_relative_path: str
    fingerprint: str | None
    policy: ScanPolicy
    rules: tuple[ScanRule, ...]
```

### 26.2 Scan finding

```python
@dataclass(frozen=True, slots=True)
class ScanFinding:
    rule_id: str
    severity: str
    message: str
    line: int | None
    column: int | None
    excerpt: str | None
    blocking: bool
```

### 26.3 Scan result

```python
@dataclass(frozen=True, slots=True)
class ScanResult:
    status: str
    findings: tuple[ScanFinding, ...]
    source_encoding: str
    duration_ms: int
    artifact_paths: tuple[Path, ...]
    primary_message: str
```

### 26.4 Compile request

```python
@dataclass(frozen=True, slots=True)
class CompileRequest:
    source_path: Path
    project_relative_path: str
    gf_executable: Path
    gf_path: GFPathResolution
    working_directory: Path
    timeout_ms: int
    artifact_paths: CompileArtifactPaths
```

### 26.5 Compile result

```python
@dataclass(frozen=True, slots=True)
class CompileResult:
    status: str
    execution_state: str
    exit_code: int | None
    timed_out: bool
    error_kind: str
    diagnostics: tuple[CompileDiagnostic, ...]
    stdout_path: Path | None
    stderr_path: Path | None
    generated_artifacts: tuple[Path, ...]
    duration_ms: int
    primary_message: str
```

These names are recommendations until locked by the interfile contract.

---

## 27. Persistence and migration

### 27.1 Canonical representation

Canonical summaries preserve scan and compile semantics separately.

### 27.2 Legacy GF Audit

Legacy summaries that already contain separate scan and compile data should map each field to the corresponding canonical stage.

### 27.3 Lossy legacy inputs

When a legacy summary contains only one merged status/message:

- do not guess which stage produced it;
- preserve the legacy message;
- record migration uncertainty;
- use `unknown`/`null` fields according to schema;
- never fabricate a compile success.

### 27.4 Writer policy

Current writers emit canonical stage separation only.

### 27.5 Schema change

Changing stage result shapes requires persisted-schema versioning, migrations, and reader tests.

---

## 28. Testing requirements

Recommended files:

```text
tests/audit/test_scanner.py
tests/audit/test_compiler.py
tests/audit/test_file_result_aggregation.py
tests/contracts/test_scan_compile_separation.py
tests/integration/test_scan_and_real_gf.py
tests/migrations/test_legacy_scan_compile_results.py
```

### 28.1 Scanner tests

- no findings;
- advisory finding;
- blocking finding;
- multiple findings;
- invalid encoding;
- file missing;
- deterministic ordering;
- line/column evidence;
- false-positive exception;
- no GF process launch.

### 28.2 Compiler tests

- successful compile;
- GF syntax failure;
- GF type failure;
- stdout-only diagnostic;
- stderr-only diagnostic;
- timeout;
- launch failure;
- missing required artifact;
- compile skipped;
- no scanner invocation.

### 28.3 Aggregation matrix tests

Test every important combination:

```text
scan OK + compile OK
scan FAIL + compile OK
scan OK + compile FAIL
scan FAIL + compile FAIL
scan ERROR + compile SKIPPED
scan OK + compile ERROR
scan SKIPPED + compile OK
scan OK + compile SKIPPED
```

Verify:

- separate statuses;
- overall status;
- report labels;
- exit behavior;
- release-gate behavior.

### 28.4 Contract tests

Verify:

- separate artifact directories;
- scanner cannot write compiler artifacts;
- compiler cannot write scanner artifacts;
- result provenance survives serialization;
- report writers do not launch stages;
- CLI/GUI parity;
- scan blocker does not skip compile by default.

### 28.5 Real-GF integration

Use a fixture containing:

- clean scan + successful compile;
- clean scan + GF failure;
- blocking scan marker + valid GF source;
- blocking scan marker + GF failure.

This proves the independence matrix against the real toolchain.

---

## 29. Operational examples

### 29.1 Suspicious marker, valid GF

```text
scan:
  status = FAIL
  finding = SCAN-TEMP-001
  message = release-blocking temporary marker

compile:
  status = OK

overall:
  status = FAIL
```

Meaning:

GF accepts the module, but the project release policy does not.

### 29.2 Clean text, GF type failure

```text
scan:
  status = OK

compile:
  status = FAIL
  error_kind = TYPE

overall:
  status = FAIL
```

Meaning:

The scanner is not a type checker.

### 29.3 Source unreadable

```text
scan:
  status = ERROR
  message = source could not be decoded

compile:
  status = SKIPPED
  reason = invalid_source_prerequisite

overall:
  status = ERROR
```

### 29.4 GF executable missing

```text
scan:
  status = OK

compile:
  status = ERROR
  execution_state = launch_failed
  error_kind = TOOL

overall:
  status = ERROR
```

### 29.5 Scan-only operation

```text
scan:
  status = OK

compile:
  status = SKIPPED
  reason = stage_not_selected

overall:
  status = OK for scan-only command
release eligibility:
  false
```

The command outcome is successful for its declared scope but does not prove compilation.

---

## 30. Decision compliance checklist

```text
[ ] Scanner and compiler have separate modules
[ ] Scanner and compiler have separate requests
[ ] Scanner and compiler have separate results
[ ] Stage statuses are preserved
[ ] Scan rule IDs are stable
[ ] GF diagnostics retain GF provenance
[ ] Scan blocker does not skip GF by default
[ ] Compile success does not clear scan findings
[ ] Scan success does not clear compile failures
[ ] Source-access prerequisite failures are explicit
[ ] Direct/downstream classification occurs after compilation
[ ] Raw scan and compile evidence are separate
[ ] summary.json preserves both stages
[ ] Human reports label both sources
[ ] AI_READY.md does not attribute scanner text to GF
[ ] CLI and GUI aggregate identically
[ ] Release gates require configured stages
[ ] Legacy merged results are migrated without guessing
[ ] Unit, contract, matrix, and real-GF tests pass
```

---

## 31. Review triggers

This ADR must be reviewed when:

- a formal GF parser is proposed for static analysis;
- scan rules begin affecting GF command construction;
- compilation caching depends on scan results;
- scan and compile results are merged in a persisted schema;
- release policy introduces default scan short-circuit;
- project plugins can execute custom scan code;
- classification semantics expand beyond compilation failures;
- GF provides a native lint/static-analysis interface;
- stage ordering changes;
- a public API exposes only one merged file status.

---

## 32. Reversal criteria

This decision may be replaced only when a new architecture proves all of the following:

1. GF authority remains explicit;
2. heuristic provenance remains explicit;
3. false positives cannot suppress required GF evidence;
4. persisted results remain unambiguous;
5. release policies remain independently expressible;
6. migration preserves historical meaning;
7. CLI, GUI, and automation remain consistent;
8. performance and maintenance benefits justify the compatibility cost.

A replacement requires:

- a new ADR;
- this ADR marked superseded;
- contract updates;
- schema migration;
- full result/report migration;
- release-major analysis.

---

## 33. Final statement

Static scan and GF compilation are complementary, not competing, validation mechanisms.

The scanner identifies documented suspicious source conditions.

GF determines whether the source is accepted by the configured GF toolchain.

> GF Wordbench shall preserve both truths separately and combine them only through explicit orchestration and policy.

No heuristic finding may masquerade as a GF compiler result, and no compiler result may erase independent project-policy evidence.
