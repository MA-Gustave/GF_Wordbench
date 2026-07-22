# ADR-0002 — GF as the Execution Engine

**ADR ID:** `ADR-0002`  
**Title:** GF as the Execution Engine  
**Status:** Accepted  
**Decision scope:** GF Wordbench framework, active language projects, validation pipeline, CLI, GUI, reports, and external-tool integration  
**Decision owner:** GF Wordbench maintainers  
**Decision date:** `2026-07-22`  
**Last reviewed:** `2026-07-22`  
**ADR version:** `1.0.0`  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\decisions\ADR-0002-GF-AS-EXECUTION-ENGINE.md`

---

## 1. Decision summary

GF Wordbench uses the Grammatical Framework toolchain as the authoritative execution engine for GF semantics.

GF Wordbench does not reimplement:

- GF source parsing;
- GF type checking;
- GF module resolution;
- GF compilation;
- PGF construction;
- grammar loading;
- parsing;
- linearization;
- generation;
- morphology;
- GF shell semantics;
- GF-native introspection.

GF Wordbench owns:

- configuration;
- executable and path resolution;
- process orchestration;
- finite timeouts;
- stdout and stderr capture;
- artifact verification;
- static heuristic scanning;
- diagnostic normalization;
- direct/downstream classification;
- scenario selection;
- marker verification;
- gold comparison;
- regression comparison;
- run manifests;
- machine and human reports;
- CLI and GUI presentation.

The architecture therefore follows:

```text
GF Wordbench decides what to validate
→ GF executes GF semantics
→ GF Wordbench preserves and interprets the evidence
```

---

## 2. Context

GF Wordbench is a development and validation framework for one active GF language project at a time.

A complete language-development workflow requires capabilities such as:

- compiling `.gf` modules;
- resolving imports and dependencies;
- checking types;
- producing `.gfo` artifacts;
- building `.pgf` grammars;
- loading grammars;
- parsing input strings;
- linearizing abstract trees;
- generating trees;
- analyzing morphology;
- inspecting grammar contents;
- detecting missing linearizations;
- executing repeatable validation scripts.

GF already provides these capabilities.

The framework also requires capabilities that GF alone does not provide as a complete development system:

- portable project configuration;
- repeatable validation modes;
- deterministic subject selection;
- file-level evidence capture;
- timeout and cancellation control;
- static source heuristics;
- direct/downstream failure classification;
- scenario marker contracts;
- gold regression comparison;
- previous-run comparison;
- artifact manifests;
- structured summary data;
- GUI and CLI workflows;
- release gates.

The architecture must combine these two responsibility sets without duplicating GF internals or weakening evidence quality.

---

## 3. Problem

Several implementation strategies are possible.

### Option A — Reimplement GF semantics in Python

Python could parse GF source, resolve modules, infer types, interpret grammar behavior, or implement a partial GF runtime.

This would allow deeper Python-level inspection, but it would create a second semantic implementation.

### Option B — Use GF only as a final release compiler

Python could perform most validation independently and invoke GF only for the final PGF build.

This would make development validation faster in some cases, but Python results could diverge from actual GF behavior.

### Option C — Use GF as the authoritative execution engine

Python constructs controlled requests, invokes GF, preserves evidence, and interprets results without replacing GF semantics.

This keeps GF authoritative while allowing GF Wordbench to provide orchestration, diagnostics, regression control, and reporting.

A formal decision is required because this boundary affects:

- module ownership;
- process contracts;
- data models;
- scenario formats;
- result semantics;
- report trustworthiness;
- testing;
- performance;
- security;
- release readiness.

---

## 4. Decision

GF Wordbench adopts **Option C**.

GF is the authoritative execution engine for every operation whose correctness depends on GF semantics.

GF Wordbench may perform static heuristic analysis, but heuristic findings must remain explicitly separate from GF results.

The framework must invoke GF through a controlled external-tool adapter and process-execution layer.

Every GF operation must be represented by a structured request containing, as applicable:

```text
operation ID
operation kind
executable
ordered arguments
working directory
environment overrides
standard input
timeout
expected artifacts
```

Every operation must produce structured evidence containing, as applicable:

```text
start time
end time
duration
execution state
exit code
timeout state
cancellation state
launch error
stdout path
stderr path
generated artifact paths
```

GF Wordbench converts this evidence into validation results only after preserving the raw outputs.

---

## 5. Decision status

This decision is:

```text
Accepted
```

It is a foundational architectural rule.

It is not experimental.

Core framework components, validation stages, GUI actions, CLI actions, reports, and project workflows must comply with it.

---

## 6. Scope

This ADR governs:

- GF executable resolution;
- GF version probing;
- `.gf` compilation;
- `.gfo` generation;
- `.pgf` construction;
- `.gfs` scenario execution;
- grammar import;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- missing-function checks;
- process timeouts;
- process cancellation;
- stdout and stderr;
- external-tool artifact verification;
- GF diagnostic interpretation;
- CLI and GUI access to GF operations.

This ADR also governs future features whose correctness depends on GF semantics.

---

## 7. Out of scope

This ADR does not require GF to own:

- project metadata;
- application state;
- run-directory creation;
- file selection;
- static scanner rules;
- diagnostic grouping;
- causal classification;
- output normalization;
- gold comparison;
- regression comparison;
- report generation;
- artifact manifests;
- UI layout;
- release policy.

These remain GF Wordbench responsibilities.

---

## 8. Authority model

### 8.1 GF authority

GF is authoritative for:

```text
source syntax
type correctness
module compatibility
import resolution
compilation
grammar loading
parse results
linearization results
generation results
morphology results
GF introspection
GF-native diagnostics
PGF production
```

### 8.2 GF Wordbench authority

GF Wordbench is authoritative for:

```text
selected executable
resolved GF version
selected project
selected mode
selected files
selected scenarios
ordered command arguments
working directory
GF search path
timeouts
cancellation
captured evidence
expected artifact checks
normalization
gold comparison
causal classification
regression state
release gates
reports
manifest
overall validation status
```

### 8.3 Project authority

The active language project is authoritative for:

```text
source roots
entrypoints
checkpoints
project GF path additions
required scenarios
optional scenarios
scenario inputs
gold expectations
release artifact requirements
language-specific validation criteria
```

---

## 9. Core invariant

The central invariant is:

> GF Wordbench must not claim a GF-semantic result that GF did not execute or produce.

Examples:

- Python may identify a suspicious source pattern, but it must not call the file syntactically invalid unless GF reports or confirms a syntax failure.
- Python may infer dependency relationships, but it must not claim that a module compiled unless GF compilation succeeded.
- Python may compare expected and actual linearizations, but GF must produce the actual linearization.
- Python may verify a `.pgf` exists, but GF must produce the `.pgf`.
- Python may classify a failure as downstream, but the underlying compile or load evidence must come from GF execution.

---

## 10. Static scanning boundary

GF Wordbench may statically scan `.gf` source for known risks.

Examples:

- suspicious slash patterns;
- runtime string matching;
- untyped string-pattern blocks;
- trailing whitespace;
- project-specific anti-patterns.

Static scanning is permitted because it provides early, targeted feedback.

However:

```text
static finding ≠ GF compiler error
clean static scan ≠ successful GF compilation
```

Static findings must use their own result fields, rule IDs, severities, and evidence.

They must not be merged into GF error kinds without an explicit project policy.

---

## 11. External process boundary

GF runs as an external executable.

Preferred invocation model:

```python
subprocess.run(
    [executable, *arguments],
    shell=False,
)
```

Equivalent controlled process APIs are permitted.

Requirements:

- executable and arguments remain separate;
- argument ordering is preserved;
- working directory is explicit;
- standard input is explicit;
- stdout and stderr are captured separately;
- every process has a finite timeout;
- cancellation is distinguishable from timeout;
- process launch errors are distinguishable from GF failures;
- expected artifacts are verified;
- the actual command is recorded;
- project-controlled text is not concatenated into an operating-system shell command.

---

## 12. GF operation classes

GF Wordbench recognizes distinct GF operation classes.

### 12.1 Version probe

Purpose:

```text
identify GF
evaluate compatibility
record evidence
```

Conceptual command:

```text
<gf> --version
```

### 12.2 Module compilation

Purpose:

```text
validate one selected .gf module
produce compile evidence
produce .gfo when applicable
```

Conceptual command:

```text
<gf> -batch -s <path-options> <artifact-options> <source-file>
```

### 12.3 PGF release build

Purpose:

```text
build the declared portable runtime grammar
```

Conceptual command:

```text
<gf> -make -optimize-pgf <path-options> <entrypoints...>
```

### 12.4 Scenario execution

Purpose:

```text
execute native GF shell commands
validate runtime grammar behavior
```

Conceptual model:

```text
<gf> receives scenario.gfs through standard input
```

### 12.5 Introspection

Purpose:

```text
inspect grammar categories
inspect functions
inspect retained operations
inspect dependencies
detect missing linearizations
```

Each class has independent:

- timeout;
- expected output;
- required artifacts;
- success criteria;
- diagnostics;
- tests.

---

## 13. Compilation decision

GF Wordbench uses GF compilation as the authoritative determination of source-module validity.

A compile result is successful only when applicable criteria pass:

```text
process launched
process completed
no timeout
no cancellation
exit code indicates success
no recognized fatal GF diagnostic
required artifact checks pass
```

A zero exit code alone is not always sufficient.

A report or classifier must not override missing required evidence.

The compiler stage must not:

- classify dependency cascades;
- generate human reports;
- update gold;
- mutate source;
- infer project release readiness.

---

## 14. PGF decision

PGF construction is a separate GF operation.

Successful individual `.gfo` compilation does not prove that the release PGF can be built.

Release readiness requires, when declared:

```text
required entrypoints
successful GF build
expected .pgf path
non-empty .pgf
manifest registration
release checks
```

GF Wordbench must not synthesize or modify a PGF while presenting it as GF output.

---

## 15. Scenario decision

GF Wordbench uses native `.gfs` scripts for runtime grammar validation.

This avoids inventing a parallel scenario language for GF semantics.

A scenario may exercise:

- grammar loading;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- missing-function detection.

GF Wordbench adds a stable scenario contract around native scripts:

```text
scenario ID
required flag
working directory
GF path
timeout
required markers
forbidden markers
normalization version
gold path
expected artifacts
```

A scenario process completing with exit code zero does not automatically pass.

Required markers and assertions must also pass.

---

## 16. Diagnostic decision

GF Wordbench interprets GF diagnostics but does not redefine their semantic authority.

The diagnostic pipeline may extract:

```text
error kind
first error
detail
source location
fatal messages
artifact failure
parser warnings
```

Raw stdout and stderr remain authoritative evidence.

The framework must preserve both streams before parsing.

Unknown GF output must not be mapped to a precise error category without evidence.

Conservative fallback is required.

---

## 17. Causal classification decision

GF does not own GF Wordbench’s project-level causal categories.

GF Wordbench may classify results as:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

This classification is based on:

- GF diagnostics;
- source locations;
- failed providers;
- dependency maps;
- project configuration;
- blocked prerequisites.

The classifier must not rerun GF.

It must not modify raw evidence.

When causality is unclear:

```text
diagnostic_class = ambiguous
```

is the correct result.

---

## 18. Status separation

This ADR requires four distinct result axes.

### Validation status

```text
OK
FAIL
ERROR
SKIPPED
```

### Execution state

```text
completed
timed_out
cancelled
launch_failed
```

### Error kind

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

### Diagnostic class

```text
ok
direct
downstream
ambiguous
noise
skipped
```

The process layer owns execution facts.

The GF interpreter owns broad technical interpretation.

The classifier owns causal position.

The validation pipeline owns required-criterion status.

These values must not be collapsed into one enum.

---

## 19. Evidence-before-interpretation rule

The required order is:

```text
execute GF
→ capture stdout and stderr
→ persist raw evidence
→ record process metadata
→ verify artifacts
→ parse diagnostics
→ normalize derived output
→ classify
→ compare
→ report
```

A parser failure must not destroy the original output.

A report failure must not destroy process evidence.

A normalization failure must not overwrite raw scenario output.

---

## 20. Raw evidence rule

For each launched GF operation, preserve as applicable:

```text
command
working directory
environment overrides
start time
end time
duration
exit code
execution state
stdout
stderr
artifact list
```

Raw stream artifacts are immutable after capture.

Framework-generated explanations must not be inserted into captured GF stdout or stderr as if GF emitted them.

Timeout and cancellation messages belong in structured metadata and lifecycle logs.

---

## 21. Output normalization rule

GF output may contain unstable environment details.

GF Wordbench may normalize approved non-semantic values such as:

- line endings;
- ANSI escapes;
- run-specific absolute paths;
- project root;
- RGL root;
- run directory;
- explicitly unstable timing lines.

Normalization must not remove:

- GF errors;
- source locations needed for diagnosis;
- abstract trees;
- linearized strings;
- ambiguity counts;
- morphology results;
- missing-function lists;
- meaningful punctuation;
- meaningful Unicode;
- evidence that a required scenario section did not execute.

Normalization rules are versioned.

A change that affects gold comparison requires deliberate gold review.

---

## 22. Gold comparison rule

GF produces actual runtime output.

GF Wordbench compares normalized actual output with reviewed project expectations.

Normal validation:

- reads gold;
- never rewrites gold;
- writes an actual-output artifact;
- writes a diff on mismatch;
- records the normalization version;
- records the scenario ID.

Gold is not used to simulate GF execution.

A gold match cannot compensate for missing current GF evidence.

---

## 23. GUI and CLI rule

The GUI and CLI are clients of shared orchestration.

They must not invoke GF independently.

Allowed flow:

```text
CLI or GUI
→ shared bootstrap
→ canonical RunConfig
→ audit orchestration
→ GF adapter/process runner
```

Prohibited flow:

```text
GUI widget
→ subprocess
```

or:

```text
CLI parser
→ compiler command construction
```

Equivalent GUI and CLI requests must resolve to equivalent GF operations.

---

## 24. Report rule

Reports are views of completed structured results.

Reports must not:

- invoke GF;
- rerun a scenario;
- reconstruct missing compile evidence;
- parse source to determine compilation success;
- update gold;
- produce a missing PGF;
- reinterpret an unknown result as successful.

The canonical machine source is:

```text
summary.json
```

Raw GF evidence remains under:

```text
raw/
```

---

## 25. Security decision

Because GF and `.gfs` scripts are executable inputs, the integration is a trust boundary.

GF Wordbench must:

- validate project and scenario paths;
- avoid implicit operating-system shells;
- prohibit unapproved GF shell escapes;
- use finite output bounds;
- use finite process timeouts;
- terminate owned processes on timeout/cancellation;
- avoid environment-secret leakage;
- treat untrusted scenarios as executable code;
- keep generated outputs inside owned directories.

Using GF as the engine does not transfer security ownership to GF.

GF Wordbench owns safe invocation.

---

## 26. Determinism decision

Given the same:

```text
source bytes
project configuration
GF version
RGL revision
scenario inputs
normalization version
platform policy
```

GF Wordbench should produce equivalent structured results.

Known unstable values may include:

- timestamps;
- durations;
- absolute paths;
- random generation;
- diagnostic ordering;
- platform line endings.

Only documented non-semantic instability may be normalized.

GF Wordbench must record the GF version because GF behavior may vary between versions.

---

## 27. Version compatibility decision

GF Wordbench maintains:

```text
minimum_supported_gf_version
tested_gf_versions
known_incompatible_gf_versions
version-specific capabilities
```

An unknown newer GF may proceed with warning outside strict mode when capability checks pass.

An older unsupported GF should fail before language validation.

Silent fallback to different command semantics is prohibited.

Version-specific behavior must use:

- version-gated request construction;
- capability probes;
- documented compatibility adapters.

---

## 28. Testing decision

The framework must test the boundary at two levels.

### 28.1 Tests without real GF

Use fake executables or process-result fixtures to test:

- argument ordering;
- working directories;
- paths containing spaces;
- timeout behavior;
- cancellation;
- stdout-only diagnostics;
- stderr-only diagnostics;
- invalid UTF-8;
- artifact checks;
- version parsing;
- marker verification;
- normalization;
- status mapping.

### 28.2 Tests with real GF

Use a small synthetic fixture grammar to test:

- version probing;
- successful compilation;
- failed compilation;
- PGF construction;
- scenario loading;
- parsing;
- linearization;
- bounded generation;
- morphology;
- introspection;
- raw evidence preservation.

Real-GF tests must not depend on the active language project.

---

## 29. Implementation boundaries

Recommended ownership:

| Responsibility | Owner |
|---|---|
| GF executable/version adapter | GF toolchain component |
| GF path construction | one GF path resolver |
| generic process execution | `app/utils/process_utils.py` |
| file compilation | `app/audit/compiler.py` |
| PGF build | dedicated PGF builder |
| scenario execution | dedicated scenario runner |
| diagnostic parsing | diagnostic parser |
| causal classification | `app/audit/classifier.py` |
| output normalization | normalizer |
| gold comparison | gold comparator |
| orchestration | `app/audit/audit_core.py` |
| result assembly | `app/audit/result_model.py` |
| reports | `app/reports/` |
| GUI/CLI | presentation adapters |

Exact filenames may evolve through coordinated architectural change.

The ownership boundaries must remain.

---

## 30. Consequences

### 30.1 Positive consequences

#### Semantic fidelity

GF Wordbench validates the same semantics that GF users ultimately depend on.

#### Reduced duplication

The framework does not maintain a second GF compiler or runtime.

#### Better compatibility

GF behavior changes are isolated through the external-tool adapter and recorded version evidence.

#### Trustworthy release artifacts

`.gfo` and `.pgf` files come from GF.

#### Native scenarios

Project validation uses familiar GF shell capabilities.

#### Stronger evidence

Every result can point to actual GF process output.

#### Cleaner architecture

Python orchestration remains separate from GF language semantics.

#### Easier testing

Most process and interpretation behavior can be tested with fake executables; semantic compatibility can be tested with a small real-GF fixture.

---

### 30.2 Negative consequences

#### External-process overhead

Starting GF processes is slower than calling an in-process Python implementation.

#### Version variability

GF output and behavior may vary across versions and platforms.

#### Diagnostic parsing complexity

GF Wordbench must interpret output conservatively.

#### Installation dependency

Users need a compatible GF toolchain and usually an RGL installation.

#### Process-management complexity

Timeout, cancellation, encoding, child-process termination, and stream capture require robust implementation.

#### Limited source understanding

Static Python scanners cannot fully understand GF semantics without duplicating GF internals.

These costs are accepted because semantic duplication would create a larger correctness risk.

---

## 31. Rejected alternative: Python reimplementation of GF parsing

### Description

Implement a Python parser for GF source.

### Reasons rejected

- grammar and language evolution would require continuous duplication;
- parser acceptance might differ from GF;
- source parsing alone would not provide type checking;
- users could receive contradictory results;
- maintenance cost would be high;
- a partial parser could create false confidence.

A limited lexical scanner remains permitted for heuristics.

---

## 32. Rejected alternative: Python type checker

### Description

Implement GF type checking in Python.

### Reasons rejected

- type semantics are GF’s responsibility;
- implementation complexity is substantial;
- version compatibility would be difficult;
- false positives and false negatives would undermine trust;
- final compilation would still require GF.

---

## 33. Rejected alternative: PGF-only validation

### Description

Build PGF once and perform all validation only through the resulting PGF.

### Reasons rejected

- file-level compilation evidence would be lost;
- provider failures would be harder to isolate;
- checkpoint development would be less precise;
- incomplete modules could be hidden until final build;
- source diagnostics would be weaker.

PGF validation remains a required release layer, not the only layer.

---

## 34. Rejected alternative: report-driven execution

### Description

Let report writers invoke GF when evidence is missing.

### Reasons rejected

- reports would become nondeterministic;
- different reports could execute different operations;
- evidence could diverge;
- result ownership would be unclear;
- failures during reporting could alter validation semantics;
- repeated runs would be expensive;
- GUI and CLI consistency would degrade.

Reports remain pure consumers.

---

## 35. Rejected alternative: custom scenario language

### Description

Create a Python-specific DSL that translates to GF operations.

### Reasons rejected

- duplicates GF shell concepts;
- requires another parser and versioned language;
- reduces direct reproducibility in GF;
- increases debugging layers;
- risks translation errors.

GF Wordbench-specific metadata and markers may wrap native `.gfs`, but native GF commands remain the executed semantics.

---

## 36. Rejected alternative: GF shell through operating-system command strings

### Description

Build one shell command string and use redirection or platform shell behavior.

### Reasons rejected

- quoting differs across platforms;
- project text could affect command interpretation;
- paths with spaces become fragile;
- process-tree control is harder;
- command evidence is less structured;
- security risk increases.

Structured arguments and direct stdin are required.

---

## 37. Rejected alternative: infer success from exit code only

### Description

Treat zero exit code as success.

### Reasons rejected

A zero exit code may coexist with:

- missing required scenario markers;
- ignored script commands;
- missing artifacts;
- incomplete output;
- failed gold comparison;
- recognized fatal diagnostics.

Success requires the complete operation contract.

---

## 38. Rejected alternative: parse stdout only

### Description

Ignore stderr.

### Reasons rejected

GF versions and platforms may emit diagnostics on either stream.

Both streams are required evidence.

They remain separately captured.

---

## 39. Rejected alternative: automatic gold update

### Description

Rewrite expected output whenever GF produces a different result.

### Reasons rejected

- regressions would be accepted automatically;
- GF-version changes could be hidden;
- project behavior changes would not receive review;
- release evidence would lose meaning.

Gold updates remain explicit and reviewed.

---

## 40. Migration from the earlier audit engine

The existing audit foundation already uses GF for:

- version probing;
- file compilation;
- compile diagnostics.

The final GF Wordbench architecture extends this principle consistently to:

- native scenarios;
- runtime grammar operations;
- PGF release construction;
- GF introspection;
- release evidence.

Migration requirements:

```text
[ ] centralize GF executable resolution
[ ] centralize GF path construction
[ ] preserve stdout and stderr separately
[ ] separate process state from validation status
[ ] separate compilation from PGF build
[ ] add native scenario runner
[ ] add marker verification
[ ] add normalization versioning
[ ] add explicit gold comparison
[ ] add artifact verification
[ ] add real-GF integration fixture
[ ] prevent GUI/CLI stage bypass
[ ] prevent report-driven execution
```

Legacy compatibility behavior may remain temporarily, but the resolved command must always be recorded.

---

## 41. Compliance rules

The architecture complies with this ADR only when all applicable conditions hold.

```text
[ ] GF executes every GF-semantic operation
[ ] static scans are labeled heuristic
[ ] GF commands use one controlled adapter
[ ] processes use finite timeouts
[ ] stdout and stderr are preserved separately
[ ] raw evidence precedes interpretation
[ ] compile and PGF stages are separate
[ ] scenarios are native .gfs scripts
[ ] scenario completion uses required markers
[ ] normal runs do not update gold
[ ] reports do not execute GF
[ ] GUI and CLI use shared orchestration
[ ] process layer does not classify causal position
[ ] classifier does not execute GF
[ ] GF version is recorded
[ ] required artifacts are verified
[ ] unknown evidence is handled conservatively
```

---

## 42. Drift indicators

This ADR is being violated when:

- Python code claims GF syntax or type correctness without GF evidence;
- a report launches GF;
- a GUI widget launches GF directly;
- CLI command parsing builds GF arguments independently;
- compilation and scenarios use different GF path builders;
- a process runs without a timeout;
- stderr is discarded;
- exit code zero overrides missing markers;
- missing PGF is accepted;
- a normal run rewrites gold;
- a timeout becomes a syntax error;
- static findings appear as GF compiler errors;
- a classifier reruns GF;
- a custom scenario language replaces native `.gfs`;
- a project-specific GF command is embedded in the generic process layer;
- an unsupported GF version silently receives different semantics;
- raw output is overwritten by normalized output;
- generated GF artifacts are modified while presented as raw GF products.

Any drift indicator requires contract and architectural review.

---

## 43. Change procedure

A change affecting this decision must review:

```text
GF toolchain adapter
process runner
configuration
RunConfig
result models
diagnostic parser
classifier
scenario runner
normalizer
gold comparator
artifact paths
reports
CLI
GUI
tests
external-tool contract
persisted schema
release notes
```

No GF-semantic capability may be moved into Python through an isolated implementation edit.

---

## 44. Review triggers

Review this ADR when:

- GF introduces a supported in-process API;
- the framework adopts a PGF runtime library;
- GF command semantics change materially;
- scenario execution no longer uses native `.gfs`;
- a new external grammar engine is proposed;
- performance pressure motivates semantic caching;
- the framework proposes source rewriting;
- a supported platform cannot execute GF reliably;
- external-tool security assumptions change;
- GF becomes unavailable for a required deployment environment.

A review does not automatically reverse the decision.

Any replacement must preserve equivalent semantic authority and evidence quality.

---

## 45. Supersession requirements

This ADR may be superseded only by a new ADR that defines:

- the replacement execution authority;
- semantic equivalence guarantees;
- compatibility with GF source and PGF;
- migration of scenarios;
- migration of diagnostics;
- migration of gold files;
- artifact provenance;
- security model;
- performance evidence;
- test strategy;
- rollback strategy.

The new ADR must explicitly supersede:

```text
ADR-0002
```

Until then, this decision remains active.

---

## 46. Related decisions

This ADR works with:

```text
ADR-0001 — Single Active Language
ADR-0003 — Separate Scan and Compile
ADR-0004 — Native GFS Scenarios
ADR-0005 — File and Scenario Results
ADR-0006 — AI-Ready Report
ADR-0007 — Golden Output Testing
```

Relationships:

```text
ADR-0001 limits project scope
ADR-0002 establishes GF semantic authority
ADR-0003 separates heuristics from GF compilation
ADR-0004 defines native runtime validation
ADR-0005 structures evidence
ADR-0006 constrains AI reporting
ADR-0007 defines reviewed regression expectations
```

---

## 47. Related documentation

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/gf/GF_COMPILATION.md
docs/gf/GF_PGF_BUILD.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/gf/GF_VERSION_COMPATIBILITY.md
docs/validation/VALIDATION_PIPELINE.md
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/development/TESTING_GF_WORDBENCH.md
```

---

## 48. Final decision statement

GF remains the semantic authority for GF grammars.

GF Wordbench remains the orchestration and evidence authority around GF.

> GF Wordbench must never replace GF execution with an unverified approximation when the result depends on GF semantics.

The framework is trustworthy only when it can show:

```text
what GF operation was requested
which GF executable performed it
what evidence GF produced
which artifacts resulted
how GF Wordbench interpreted the evidence
why the final validation status was assigned
```
