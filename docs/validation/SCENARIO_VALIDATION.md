# GF Wordbench — Scenario Validation

**Document ID:** `GF-WB-VALIDATION-SCENARIO`  
**Status:** Normative validation specification  
**Applies to:** Native GF `.gfs` scenarios executed by GF Wordbench  
**Primary implementation owner:** `app/audit/scenario_runner.py`  
**Project asset owners:** Active language project maintainers  
**Specification version:** `1.0`  
**Target product state:** Final architecture  
**Last reviewed:** 2026-07-22  

---

## 1. Purpose

This document defines how GF Wordbench validates an active language project through native Grammatical Framework scenarios.

Scenario validation proves behavior that individual source-file compilation cannot prove reliably, including:

- loading a complete grammar;
- detecting missing linearizations;
- linearizing representative abstract trees;
- parsing representative input strings;
- checking expected ambiguity;
- running bounded generation;
- exercising morphology and grammar introspection;
- verifying project entrypoints;
- comparing stable behavioral output with reviewed expectations.

The scenario system uses GF itself as the execution engine.

GF Wordbench coordinates execution, captures evidence, validates scenario completion, normalizes unstable output, compares reviewed expectations, and reports structured results.

---

## 2. Core rule

> GF Wordbench executes native GF scenarios; it does not implement a second GF shell.

A scenario is a project-owned `.gfs` file.

The scenario runner must not:

- parse and reimplement GF command semantics;
- simulate GF parsing, linearization, generation, or introspection;
- convert `.gfs` into a private command language;
- silently repair invalid GF commands;
- infer linguistic success only from process exit code;
- rewrite scenario or gold files during normal validation.

---

## 3. Related authority

The following documents remain authoritative for their domains:

```text
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/DATA_MODEL.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/VALIDATION_SPEC.md
```

Priority when rules overlap:

1. persisted-schema lock for serialized data and canonical paths;
2. external-tool lock for GF invocation;
3. interfile locks for provider-consumer relationships;
4. scenario-format documents for scenario syntax conventions;
5. this document for scenario-validation lifecycle and success evaluation;
6. active-project validation specification for language-specific expectations.

---

## 4. Scope

This specification governs:

- scenario discovery;
- scenario registry resolution;
- required and optional scenario selection;
- `.gfs` file validation;
- scenario input handling;
- GF execution;
- marker and section validation;
- diagnostic inspection;
- output normalization;
- gold comparison;
- scenario result construction;
- mode integration;
- run totals;
- release-gate behavior;
- scenario artifacts;
- regression comparison;
- scenario tests;
- scenario security.

---

## 5. Exclusions

This specification does not define:

- GF command syntax;
- the linguistic architecture of the active project;
- which example sentences are linguistically correct;
- the exact output normalization rules;
- the exact gold file text format;
- source-module compilation;
- PGF binary format;
- report prose;
- GUI layout;
- a general testing language;
- remote or distributed scenario execution.

Language-specific expectations belong to:

```text
project/docs/VALIDATION_SPEC.md
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

---

## 6. Architectural position

Scenario validation is one stage in the validation pipeline.

```text
project configuration
        ↓
tool/version validation
        ↓
source and checkpoint validation
        ↓
entrypoint or PGF readiness
        ↓
scenario selection
        ↓
native GF execution
        ↓
raw evidence capture
        ↓
marker and diagnostic checks
        ↓
output normalization
        ↓
gold comparison
        ↓
ScenarioResult
        ↓
run aggregation and release gates
```

Scenario validation does not replace source compilation.

Source compilation and scenario execution provide different evidence.

---

## 7. Ownership

### 7.1 Framework owner

Canonical framework owner:

```text
app/audit/scenario_runner.py
```

The scenario runner owns:

- scenario request preparation;
- execution coordination;
- raw scenario output paths;
- marker validation;
- normalization invocation;
- gold-comparison invocation;
- `ScenarioResult` construction;
- scenario-level artifact records.

### 7.2 Active-project owners

The active project owns:

```text
project/project.toml
project/validation/scenarios/*.gfs
project/validation/inputs/
project/validation/gold/*.gold
project/docs/VALIDATION_SPEC.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

The framework must not silently rewrite these assets during normal validation.

### 7.3 Process owner

The shared process runner owns:

- process launch;
- direct stdin transfer;
- timeout;
- cancellation;
- process-tree termination;
- stdout capture;
- stderr capture;
- process-level result facts.

### 7.4 Normalization owner

The designated normalizer owns stable transformation rules.

The scenario runner invokes it but must not maintain a second normalization implementation.

### 7.5 Gold-comparison owner

The designated comparator owns exact normalized-output comparison and diff production.

The scenario runner coordinates it but must not duplicate its comparison rules.

---

## 8. Canonical project layout

```text
project/
├── project.toml
├── docs/
│   ├── VALIDATION_SPEC.md
│   └── INTERFILE_CONTRACT_LOCK.md
└── validation/
    ├── README.md
    ├── scenarios/
    │   ├── README.md
    │   └── <scenario-id>.gfs
    ├── inputs/
    │   ├── README.md
    │   └── <input-assets>
    └── gold/
        ├── README.md
        └── <scenario-id>.gold
```

A project may organize additional subdirectories when declared by project configuration and documented by the project contract lock.

The final resolved scenario paths must remain inside the project root.

---

## 9. Scenario identity

Every scenario has a stable `scenario_id`.

Recommended format:

```text
[a-z][a-z0-9]*(?:-[a-z0-9]+)*
```

Examples:

```text
load
missing
linearize
parse
generation
morphology
parse-basic
linearize-clitics
```

Rules:

- unique inside one active project;
- stable across runs;
- not derived from display text;
- safe for logs and artifact filenames after canonical sanitization;
- not reused for unrelated behavior;
- changed only through a documented project migration when historical comparisons exist.

The default script name is:

```text
<scenario-id>.gfs
```

A different filename may be supported only through explicit project configuration.

---

## 10. Scenario registry

The authoritative registry is resolved from:

```text
project/project.toml
project/validation/scenarios/
```

At minimum, project configuration distinguishes:

```text
required scenarios
optional scenarios
```

The final resolved registry produces ordered `ScenarioSpec` values.

The registry order is significant and deterministic.

The runner must not depend on filesystem enumeration order.

---

## 11. Conceptual `ScenarioSpec`

The following model is conceptual:

```python
@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    scenario_id: str
    script_path: Path
    required: bool
    enabled_modes: tuple[str, ...]
    working_directory: Path
    timeout_sec: float
    output_limit_bytes: int
    gold_path: Path | None
    comparison_policy: str
    normalization_version: str
    expected_sections: tuple[str, ...]
    expected_artifacts: tuple[ArtifactExpectation, ...]
    input_paths: tuple[Path, ...]
    tags: tuple[str, ...]
```

The exact configuration syntax is defined by the configuration reference.

This model defines the resolved information required by scenario validation.

---

## 12. Required scenario-spec fields

| Field | Requirement |
|---|---|
| `scenario_id` | Unique stable identifier |
| `script_path` | Existing project-owned `.gfs` file |
| `required` | Explicit boolean |
| `enabled_modes` | Deterministic supported-mode set |
| `working_directory` | Existing contained directory |
| `timeout_sec` | Finite positive timeout |
| `output_limit_bytes` | Finite positive limit |
| `gold_path` | Project-owned `.gold` or `null` |
| `comparison_policy` | Registered policy |
| `normalization_version` | Supported version |
| `expected_sections` | Ordered unique section IDs |
| `expected_artifacts` | Explicit artifact expectations |
| `input_paths` | Validated project-owned inputs |
| `tags` | Optional stable metadata |

Missing required scenario metadata is a configuration error.

---

## 13. Required and optional scenarios

### 13.1 Required scenario

A required scenario participates in the success criteria of its enabled validation modes.

A required scenario:

- must exist;
- must be valid;
- must execute unless an earlier terminal framework error prevents it;
- must satisfy all configured assertions;
- must pass gold comparison when gold is required;
- may block release.

### 13.2 Optional scenario

An optional scenario is not automatically a release gate.

It may be:

- selected explicitly;
- included in diagnostic mode;
- enabled by project policy;
- promoted to required later.

An optional scenario that is selected and fails must still be reported honestly.

Its failure affects overall status according to the selected mode and documented policy.

### 13.3 No silent promotion or demotion

The GUI, CLI, or state file must not silently change a scenario between required and optional.

That distinction belongs to project configuration.

---

## 14. Recommended scenario families

A final project may define the following families.

### 14.1 Load

Purpose:

- load the configured top-level grammar;
- prove that higher-level imports are coherent;
- verify the intended entrypoint.

### 14.2 Missing linearizations

Purpose:

- request GF evidence about missing concrete implementations;
- prevent incomplete grammar release.

### 14.3 Linearization

Purpose:

- linearize representative abstract trees;
- verify expected forms or reviewed output;
- expose runtime linearization failures.

### 14.4 Parse

Purpose:

- parse representative UTF-8 strings;
- verify parse existence, uniqueness, ambiguity bounds, or expected trees;
- test negative examples where appropriate.

### 14.5 Generation

Purpose:

- perform bounded generation;
- check representative function families;
- detect runtime issues without unbounded output.

### 14.6 Morphology

Purpose:

- exercise paradigms, forms, or morphology commands;
- validate project-specific inflectional expectations.

### 14.7 Introspection

Purpose:

- inspect grammar information required by development or release policy;
- verify declared project structure.

These families are recommendations, not mandatory hardcoded scenario IDs.

The active project defines its actual registry.

---

## 15. Validation-mode integration

Canonical modes:

```text
quick
checkpoint
diagnostic
release
```

### 15.1 Quick mode

Quick mode should run no scenario by default unless:

- the selected target has an explicitly associated smoke scenario;
- the project defines a bounded quick scenario;
- the user explicitly selects one.

Quick mode prioritizes low latency.

### 15.2 Checkpoint mode

Checkpoint mode runs:

- scenarios associated with the selected checkpoint;
- required smoke scenarios for that architectural layer;
- only bounded project-defined checks.

### 15.3 Diagnostic mode

Diagnostic mode may run:

- all required scenarios;
- selected optional scenarios;
- extended introspection;
- bounded generation;
- additional diagnostic variants.

Diagnostic mode may continue after isolated scenario failures when safe.

### 15.4 Release mode

Release mode runs every required release scenario in declared order.

Release mode must fail when:

- a required scenario is missing;
- a required scenario is invalid;
- a required scenario does not execute;
- a required assertion fails;
- required gold is absent;
- required gold comparison fails;
- a required artifact is absent;
- a scenario times out or is cancelled;
- scenario evidence cannot be interpreted safely.

---

## 16. Scenario selection

Scenario selection receives:

```text
resolved project configuration
validation mode
optional explicit scenario filter
checkpoint context where applicable
```

It returns an ordered list of `ScenarioSpec`.

Selection rules:

- required scenarios for the mode are always included;
- explicit user filters must not silently exclude release requirements;
- optional scenarios are included only by documented policy;
- duplicate IDs are rejected;
- missing referenced scripts are configuration failures;
- order follows project configuration;
- disabled scenarios remain distinguishable from absent scenarios.

The selector must not execute GF.

---

## 17. Preflight validation

Before any scenario process starts, the runner validates:

- scenario ID;
- script path;
- `.gfs` extension;
- path containment;
- UTF-8 readability;
- supported scenario file size;
- working directory;
- GF executable resolution;
- timeout;
- output limit;
- input paths;
- gold path;
- normalization version;
- expected section uniqueness;
- artifact expectation containment;
- mode eligibility;
- required/optional consistency.

Preflight failure produces:

```text
validation_status = ERROR
error_kind = CONFIG or SCRIPT
```

No GF process is launched for that scenario.

---

## 18. Scenario source integrity

The runner should record:

```text
script hash algorithm
script hash
script size
script modification metadata
```

Canonical hash:

```text
SHA-256
```

The hash proves which scenario was executed.

The runner must not execute one file and report the hash of another.

A scenario changed after preflight but before launch should cause a source-integrity error or require revalidation.

---

## 19. Input asset validation

Scenario input files may contain:

- strings;
- trees;
- expected item lists;
- morphology cases;
- bounded generation inputs;
- project-specific fixtures.

Input assets must:

- remain inside the project root;
- be declared or referenced by the scenario contract;
- be UTF-8 when textual;
- use documented formats;
- be read-only during normal validation;
- be included in project version control when required for reproducibility.

Input data must not be interpolated into an operating-system shell command.

---

## 20. Scenario trust model

A `.gfs` file is executable input for GF.

Project scenarios are trusted only to the degree the active project is trusted.

The framework must reject or prohibit by default scenario behavior capable of invoking unrestricted operating-system commands.

Prohibited without an explicit security policy:

- shell escape;
- system-command execution;
- external pipelines;
- writing outside owned output paths;
- deleting files;
- modifying source modules;
- modifying `.gold`;
- interactive terminal control.

Security validation may be conservative.

A suspicious or unsupported scenario should fail preflight rather than run silently.

---

## 21. GF invocation

Preferred execution model:

```text
resolved gf executable
        +
ordered GF arguments
        +
explicit working directory
        +
direct UTF-8 scenario stdin
```

No platform shell redirection is used.

Conceptually:

```text
gf executable starts
scenario content is provided through stdin
stdout and stderr are captured separately
```

The process request is built by:

```text
app/audit/scenario_runner.py
```

Execution is delegated to:

```text
app/utils/process_utils.py
```

---

## 22. Command ownership

The scenario runner owns the operation-specific request.

It must provide:

- operation ID;
- operation kind `scenario`;
- executable;
- ordered arguments;
- working directory;
- direct scenario input;
- timeout;
- output limit;
- raw capture paths;
- environment policy;
- expected tool artifacts where applicable.

The shared process runner must not inspect GF scenario commands.

---

## 23. Working directory

Default:

```text
resolved project root
```

A scenario-specific directory may be used when:

- declared explicitly;
- contained inside the project root;
- required by documented relative references;
- stable across clones.

The working directory must not depend on:

- terminal location;
- GUI current directory;
- launcher location;
- IDE behavior.

The actual working directory is recorded in `ScenarioResult`.

---

## 24. Scenario termination

A scenario should terminate GF explicitly when required by the selected execution method.

Recommended final command:

```text
q
```

The project scenario-format specification defines exact conventions.

A missing explicit termination may still complete if EOF is the documented mechanism, but that behavior must be consistent and tested.

Interactive prompts or an indefinitely waiting GF shell must be prevented by:

- direct input closure;
- finite timeout;
- explicit termination policy.

---

## 25. Raw output paths

Canonical run-relative paths:

```text
raw/scenarios/<scenario-id>.stdout.txt
raw/scenarios/<scenario-id>.stderr.txt
```

Canonical normalized output:

```text
raw/scenarios/<scenario-id>.out
```

Optional comparison diff:

```text
raw/scenarios/<scenario-id>.gold.diff
```

Optional structured assertion details:

```text
details/scenarios/<scenario-id>.json
```

The exact optional detail schema must be documented before machine consumption.

The runner must obtain paths through `RunPaths` or the designated artifact owner.

---

## 26. Raw evidence

For every executed scenario, preserve:

- executable and ordered arguments;
- working directory;
- scenario ID;
- scenario path;
- scenario SHA-256;
- GF version;
- start and finish timestamps;
- duration;
- execution state;
- exit code when available;
- timeout state;
- cancellation state;
- stdout path;
- stderr path;
- output-limit state;
- expected artifact observations;
- normalization result;
- comparison result.

Raw stdout and stderr are immutable after capture finalization.

---

## 27. Process execution states

Canonical process states:

```text
completed
timed_out
cancelled
launch_failed
```

These are distinct from scenario validation status.

### 27.1 Completed

GF started and exited naturally.

Further validation is still required.

### 27.2 Timed out

The scenario exceeded its deadline.

The scenario status is `ERROR`.

### 27.3 Cancelled

The controller terminated the scenario.

The scenario status is `ERROR`, unless run-level cancellation is modeled separately by the final application API.

### 27.4 Launch failed

GF did not start.

The scenario status is `ERROR`.

---

## 28. Scenario validation status

Canonical scenario statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

### 28.1 `OK`

Every applicable scenario criterion passed.

### 28.2 `FAIL`

GF executed sufficiently for validation, but a required behavioral criterion failed.

Examples:

- missing end marker;
- expected parse absent;
- unexpected parse present;
- ambiguity outside the allowed range;
- expected linearization absent;
- gold mismatch;
- required linguistic assertion failed.

### 28.3 `ERROR`

GF Wordbench could not execute or safely interpret the scenario contract.

Examples:

- invalid scenario configuration;
- launch failure;
- timeout;
- cancellation;
- output-limit cancellation;
- unreadable script;
- unsupported normalization version;
- normalization failure;
- corrupted result;
- required artifact could not be checked.

### 28.4 `SKIPPED`

The scenario was intentionally not executed.

A required release scenario must not end as `SKIPPED` in a successful release run.

---

## 29. Scenario diagnostic class

Scenario diagnostic classes remain causal classifications:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Initial scenario-runner classification should be conservative.

Recommended initial assignment:

| Condition | Initial class |
|---|---|
| passed | `ok` |
| scenario-specific assertion failed | `direct` |
| known prerequisite failed | `downstream` |
| cause unclear | `ambiguous` |
| intentionally excluded non-result | `noise` or `skipped` |
| skipped by policy | `skipped` |

Higher-level classification may refine this after all results are available.

The process layer does not assign causal class.

---

## 30. Error kinds

Recommended scenario error kinds:

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

The centralized diagnostic-kind reference is authoritative.

Adding, removing, or renaming persisted enum values requires schema review.

---

## 31. Scenario completion markers

Stable markers prove that expected scenario sections ran.

Recommended marker form:

```text
GF_WORDBENCH_BEGIN <section-id>
GF_WORDBENCH_END <section-id>
```

The exact GF command used to emit markers is defined by `SCENARIO_FORMAT.md`.

Marker text must be:

- stable;
- easily distinguishable from normal linguistic output;
- deterministic;
- unique enough to avoid accidental matches;
- emitted through GF scenario output.

---

## 32. Section identity

Section IDs follow the scenario-ID style:

```text
[a-z][a-z0-9]*(?:-[a-z0-9]+)*
```

Examples:

```text
load-main
parse-basic
linearize-pronouns
generation-bounded
```

Rules:

- unique within one scenario;
- declared or discoverable according to the scenario-format contract;
- begin marker appears before end marker;
- no nested ambiguity unless nesting is explicitly supported;
- one completed section cannot satisfy a differently named expected section.

---

## 33. Marker validation

Marker validation consumes decoded raw scenario output.

It must:

1. locate marker events;
2. preserve event order;
3. reject duplicate invalid transitions;
4. verify every expected begin marker;
5. verify every expected end marker;
6. verify begin-before-end;
7. detect incomplete sections;
8. record unexpected markers as warnings or failures by policy;
9. retain the raw output reference.

A zero exit code does not override marker failure.

---

## 34. Marker state machine

For each expected section:

```text
not_seen
  ↓ BEGIN
open
  ↓ END
completed
```

Invalid transitions:

```text
END while not_seen
BEGIN while open
BEGIN after completed
END after completed
```

The default strict policy treats invalid transitions as `FAIL`.

A repeated scenario output that legitimately repeats a section must use distinct IDs or an explicitly versioned repeatable-section policy.

---

## 35. Marker-free scenarios

A marker-free scenario may be allowed only when:

- explicitly declared;
- inherently atomic;
- validated through another reliable assertion;
- documented in the project validation specification.

Examples may include a very small versioned smoke scenario whose complete output is compared exactly with gold.

Required release scenarios should normally use markers.

---

## 36. Diagnostic inspection

After process completion, the runner or diagnostic service examines both streams.

It checks for:

- fatal GF diagnostics;
- unsupported command diagnostics;
- syntax errors in the scenario;
- import or load failures;
- runtime errors;
- missing grammar state;
- process-level decoding problems;
- contract-specific prohibited output.

Diagnostic inspection must not replace raw logs.

A scenario cannot pass solely because no recognized error text was found.

---

## 37. Exit-code policy

Exit code is evidence, not the full scenario result.

Default policy:

- non-zero exit produces `FAIL` or `ERROR` according to diagnostic interpretation;
- zero exit permits further validation;
- zero exit does not bypass markers, artifacts, normalization, or gold comparison;
- absent exit code from launch failure remains an execution error;
- timeout is represented by execution state, not a fabricated GF exit code.

Tool-version adapters may refine accepted exit behavior, but silent fallback is prohibited.

---

## 38. Assertions

Scenario assertions are stable checks applied after raw execution.

Canonical assertion categories:

```text
process
section
diagnostic
text
count
artifact
gold
```

The framework should keep the assertion system bounded.

It must not become a general programming language.

---

## 39. Process assertions

Examples:

- process completed;
- exit code equals zero;
- process did not time out;
- process was not cancelled;
- output limit was not exceeded;
- capture completed.

These assertions normally derive directly from `ProcessResult`.

---

## 40. Section assertions

Examples:

- required section completed;
- section order is valid;
- no unexpected section exists;
- section output is non-empty.

Sections should be parsed once by one owner.

Consumers must not reparse marker text independently.

---

## 41. Diagnostic assertions

Examples:

- no fatal diagnostic;
- expected diagnostic present;
- specific negative test produces an approved diagnostic class;
- unsupported command diagnostic absent.

Expected-failure scenarios must declare their expectation explicitly.

A deliberately expected error must not be treated as an accidental pass merely because some error occurred.

---

## 42. Text assertions

Examples:

- output contains an expected abstract tree;
- output contains an expected surface form;
- output does not contain an empty linearization;
- output matches one of an approved set.

Text assertions operate on:

- a declared raw stream;
- a normalized section;
- or complete normalized output.

The input source must be explicit.

---

## 43. Count assertions

Examples:

```text
parse count >= 1
parse count == 1
parse count <= configured maximum
generated results <= bound
missing linearizations == 0
```

Counts must come from a defined parser or stable output form.

Human prose must not be interpreted through undocumented ad hoc patterns.

---

## 44. Artifact assertions

Examples:

- expected `.pgf` exists before a scenario;
- scenario-produced export exists;
- produced artifact is non-empty;
- artifact remains inside the run directory.

Artifact checks must use declared expectations and owned paths.

A missing required artifact is not hidden by a successful process exit.

---

## 45. Gold assertion

Gold comparison asserts:

```text
normalized actual output == reviewed gold output
```

It occurs only after:

- raw capture;
- decoding;
- marker validation;
- required diagnostic checks;
- normalization.

A gold mismatch is a scenario `FAIL`, not a process `ERROR`.

A missing required gold is an `ERROR` or release-blocking configuration failure, according to the project contract.

---

## 46. Assertion result model

Conceptual model:

```python
@dataclass(frozen=True, slots=True)
class ScenarioAssertionResult:
    assertion_id: str
    assertion_kind: str
    status: str
    message: str
    evidence_path: Path | None
    section_id: str | None
```

Canonical assertion statuses:

```text
passed
failed
error
skipped
```

Assertion order follows scenario-spec order.

---

## 47. Assertion aggregation

Scenario aggregation uses:

```text
any assertion error      → scenario ERROR
else any assertion fail  → scenario FAIL
else all required pass   → scenario OK
```

Optional assertion semantics must be explicit.

An optional assertion failure may produce:

- warning metadata;
- scenario failure when project policy says so;
- no effect only when clearly declared informational.

Assertions must not disappear silently.

---

## 48. Output normalization

Normalization creates stable comparison output from raw evidence.

It may normalize:

- CRLF to LF;
- ANSI control sequences;
- declared absolute paths;
- run-directory paths;
- explicitly unstable timing values;
- documented GF prompt noise;
- trailing spaces where semantically irrelevant.

It must preserve:

- abstract trees;
- linearized strings;
- parse counts;
- ambiguity;
- missing-function lists;
- morphology output;
- meaningful Unicode;
- meaningful punctuation;
- evidence of incomplete sections;
- fatal diagnostics relevant to validation.

---

## 49. Normalization version

Every normalized output records:

```text
normalization_version
```

The version must match:

- scenario configuration;
- normalized output header;
- gold header when gold applies.

Unsupported or inconsistent normalization version produces `ERROR`.

A normalization change that alters comparison meaning requires:

- version update;
- unit-test update;
- deliberate gold review;
- migration note;
- changelog entry when externally visible.

---

## 50. Canonical normalized-output path

```text
raw/scenarios/<scenario-id>.out
```

The normalized file is derived evidence.

It must reference or be traceable to:

```text
raw/scenarios/<scenario-id>.stdout.txt
raw/scenarios/<scenario-id>.stderr.txt
```

Normalizers must not modify raw evidence.

---

## 51. Normalized-output minimum header

The canonical schema is defined in `PERSISTED_SCHEMA_LOCK.md`.

Expected shape:

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: <scenario-id>
# normalization_version: <version>
--- BEGIN <section-id> ---
<normalized GF output>
--- END <section-id> ---
```

The normalized file uses:

- UTF-8 without BOM;
- LF newlines;
- final newline;
- deterministic section order.

---

## 52. Gold files

Canonical path:

```text
project/validation/gold/<scenario-id>.gold
```

A gold file is:

- reviewed source material;
- project-owned;
- version-controlled when required;
- associated with one scenario identity;
- normalized under one declared version;
- read-only during normal validation.

Gold files are not raw process captures.

---

## 53. Comparison policies

Canonical policies:

```text
none
exact
```

The final core should begin with these two policies.

### 53.1 `none`

No gold comparison applies.

The scenario still requires its configured process, marker, diagnostic, and artifact checks.

### 53.2 `exact`

Canonical normalized text must match the gold text exactly after permitted newline handling.

More complex policies should not be added unless a stable need exists.

Approved alternatives such as set or unordered comparison should first be modeled through deterministic normalization where possible.

---

## 54. Exact comparison

Exact comparison verifies:

- scenario ID header;
- normalization version;
- section identities;
- section order;
- normalized text;
- final-newline convention.

A mismatch produces a structured diff.

The diff is evidence, not a replacement gold file.

---

## 55. Gold diff

Recommended path:

```text
raw/scenarios/<scenario-id>.gold.diff
```

Recommended format:

```text
unified UTF-8 text diff
```

The diff should identify:

```text
expected: project-relative gold path
actual: run-relative normalized output path
```

It must not contain unrelated absolute-path noise after canonical normalization.

---

## 56. Missing gold behavior

When `comparison_policy = exact`:

- missing gold is never an automatic pass;
- empty gold is valid only when explicitly intentional;
- unreadable gold is `ERROR`;
- unsupported gold version is `ERROR`;
- scenario-ID mismatch is `ERROR`;
- normalization-version mismatch is `ERROR`.

In release mode, all required exact-comparison gold files must be valid.

---

## 57. Gold update separation

Scenario validation is read-only for gold files.

Normal validation must not:

- create gold;
- overwrite gold;
- append to gold;
- reformat gold;
- accept actual output automatically.

Gold update is a separate explicit operation documented in:

```text
docs/scenarios/UPDATING_GOLD_FILES.md
```

The update operation must show or preserve a diff and require deliberate approval.

---

## 58. Generated and nondeterministic output

Unbounded or nondeterministic output must not be compared directly with exact gold.

Projects should use:

- fixed inputs;
- bounded generation;
- deterministic options;
- stable sorting where meaning permits;
- declared filters;
- count assertions;
- representative samples.

Random generation is unsuitable for exact gold unless a stable seed and ordering are proven and documented.

---

## 59. Bounded generation

Generation scenarios must define:

- target category;
- maximum depth or equivalent bound;
- maximum result count;
- output-size limit;
- timeout;
- deterministic ordering policy;
- assertion purpose.

The scenario must not rely only on the process timeout to bound generation.

Excessive output causes controlled cancellation and scenario `ERROR`.

---

## 60. Parse validation

Parse scenarios should declare:

- input language;
- category where needed;
- UTF-8 input;
- expected parse policy;
- ambiguity policy;
- expected or prohibited trees where applicable.

Possible policies:

```text
at_least_one
exactly_one
none
maximum_count
expected_tree
approved_tree_set
```

Linguistic expectations belong to the project validation specification.

The framework implements only stable generic assertion mechanics.

---

## 61. Linearization validation

Linearization scenarios should declare:

- abstract tree;
- target language where needed;
- variant policy;
- empty-output policy;
- expected surface form or gold policy.

The framework must distinguish:

- empty string;
- missing output;
- runtime failure;
- approved variation.

Normalization must not erase language-specific orthographic distinctions.

---

## 62. Missing-linearization validation

Missing-linearization scenarios should:

- load the intended release grammar;
- invoke the documented GF capability;
- delimit output with markers;
- assert the project release policy.

Typical release criterion:

```text
required missing-linearization count == 0
```

Project-approved exceptions must be explicit and documented.

---

## 63. Morphology validation

Morphology scenarios may validate:

- paradigms;
- inflection tables;
- agreement forms;
- irregular forms;
- orthographic alternations;
- project helper behavior visible through GF.

The framework must not encode language-specific morphology rules.

Expected forms belong to project scenarios and gold files.

---

## 64. Load validation

A load scenario proves the intended grammar can be imported or loaded in the GF shell.

It is separate from compiling one source file.

A load scenario should verify:

- documented target entrypoint;
- successful completion marker;
- no fatal import diagnostic;
- required language presence where observable;
- required retained-source behavior only when needed.

---

## 65. Scenario prerequisites

A scenario may declare prerequisites such as:

- GF version probe succeeded;
- entrypoint compilation succeeded;
- required `.gfo` exists;
- required `.pgf` exists;
- checkpoint passed;
- input files exist.

Prerequisites must be explicit.

A scenario whose prerequisite failed may become:

```text
status = SKIPPED
diagnostic_class = downstream
blocked_by = [<prerequisite-id>]
```

In release mode, a required downstream-skipped scenario still prevents release success.

---

## 66. Scenario ordering

Scenario order follows the resolved registry.

Reasons:

- reproducible evidence;
- stable report order;
- predictable grammar state assumptions;
- deterministic diff behavior.

Each scenario should normally run in a fresh GF process.

This isolates:

- loaded grammar state;
- shell options;
- failures;
- output;
- timeout;
- memory use.

Sharing one long-lived GF shell across unrelated scenarios is prohibited in the core final architecture unless a separate explicit session contract is introduced.

---

## 67. Process isolation

Default:

```text
one ScenarioSpec
    → one ProcessRequest
    → one GF process
    → one ProcessResult
    → one ScenarioResult
```

Benefits:

- simpler evidence ownership;
- reliable timeout containment;
- independent retries where ever permitted;
- deterministic raw logs;
- no hidden state leakage;
- clear failure attribution.

The overhead is acceptable relative to correctness.

---

## 68. Scenario concurrency

Default execution is sequential.

Scenario concurrency is not required for the final core.

It may be considered later only when:

- scenario processes are isolated;
- artifact paths are disjoint;
- ordering of reported results remains registry order;
- output and CPU limits are bounded;
- GF tool behavior supports it;
- cancellation is reliable;
- release reproducibility is preserved.

No unbounded scenario concurrency is permitted.

---

## 69. Conceptual `ScenarioResult`

```python
@dataclass(frozen=True, slots=True)
class ScenarioResult:
    scenario_id: str
    script_path: Path
    script_sha256: str
    required: bool
    status: str
    execution_state: str
    command: tuple[str, ...]
    working_directory: Path
    exit_code: int | None
    timed_out: bool
    cancelled: bool
    duration_ms: int
    stdout_path: Path
    stderr_path: Path
    normalized_output_path: Path | None
    gold_path: Path | None
    gold_match: bool | None
    gold_diff_path: Path | None
    diagnostic_class: str
    error_kind: str
    primary_message: str
    sections: tuple[ScenarioSectionResult, ...]
    assertions: tuple[ScenarioAssertionResult, ...]
    artifacts: tuple[ArtifactRecord, ...]
    blocked_by: tuple[str, ...]
```

The persisted schema may contain a stable subset.

Persisted field changes are governed by the schema lock.

---

## 70. Required result invariants

- `scenario_id` matches the resolved spec.
- `script_path` is project-relative in persistence.
- `required` matches project configuration.
- `status` uses the shared vocabulary.
- `command` preserves executable and argument order.
- `working_directory` records the actual directory.
- `timed_out` agrees with execution state.
- `cancelled` agrees with execution state.
- `duration_ms` is non-negative.
- stdout and stderr paths reference captured evidence.
- normalized output exists when normalization succeeded.
- `gold_match` is `null` when no comparison applies.
- a gold diff exists only for a performed mismatch or configured diagnostic output.
- section IDs are unique.
- assertion IDs are unique.
- artifact paths are owned and contained.
- `blocked_by` uses stable prerequisite identities.

---

## 71. Primary message

`primary_message` is a concise normalized explanation.

Examples:

```text
Scenario passed.
GF process timed out.
Required section `parse-basic` did not complete.
Expected at least one parse.
Normalized output differs from gold.
Required gold file is missing.
```

It must not replace detailed evidence.

It should not depend on unstable raw exception wording.

---

## 72. Result construction order

Recommended order:

1. construct process facts;
2. inspect launch/timeout/cancellation;
3. decode raw streams;
4. inspect fatal diagnostics;
5. parse markers;
6. evaluate non-gold assertions;
7. normalize output;
8. validate normalized-output contract;
9. compare gold;
10. observe scenario artifacts;
11. aggregate status;
12. assign initial causal class;
13. freeze `ScenarioResult`.

No later report writer mutates the result.

---

## 73. Evaluation precedence

When several failures occur, status precedence is:

```text
framework execution/interpretation error
        >
validation failure
        >
success
```

Recommended primary-error precedence:

1. configuration or script preflight error;
2. launch failure;
3. timeout;
4. cancellation or output limit;
5. capture or decoding error;
6. fatal tool diagnostic;
7. marker contract failure;
8. assertion error;
9. normalization error;
10. gold contract error;
11. assertion failure;
12. gold mismatch;
13. success.

All failures should remain available in detailed assertions even when one primary message is selected.

---

## 74. Required-scenario aggregation

Run-level scenario totals include:

```text
scenarios_seen
scenarios_ok
scenarios_fail
scenarios_error
scenarios_skipped
required_scenario_fail
```

`required_scenario_fail` should count required scenarios whose status is:

```text
FAIL
ERROR
SKIPPED
```

for a mode in which they were mandatory.

The exact persisted totals are governed by the schema lock.

---

## 75. Overall run impact

Scenario results affect overall status as follows.

### 75.1 Required scenario

```text
ERROR   → run ERROR
FAIL    → run FAIL
SKIPPED → run FAIL or ERROR according to cause
OK      → no negative effect
```

### 75.2 Optional selected scenario

Default:

```text
ERROR → run ERROR
FAIL  → run FAIL in diagnostic execution unless policy marks it informational
OK    → no negative effect
```

Any informational exception must be explicit in project policy.

### 75.3 Unselected optional scenario

It does not appear as an executed result.

The registry may record it separately as not selected, but it must not inflate `scenarios_seen`.

---

## 76. Release gate

The scenario release gate passes only when:

- every required release scenario exists;
- every required release scenario executed;
- every required release scenario status is `OK`;
- required markers completed;
- required assertions passed;
- required gold files were valid;
- required comparisons matched;
- required scenario artifacts exist;
- no unresolved scenario framework error exists;
- no required scenario is blocked by a failed prerequisite.

A warning may coexist with a passing gate only when explicitly non-blocking.

---

## 77. Regression comparison

Scenario regression comparison uses stable identity:

```text
subject_kind = scenario
subject_id = scenario_id
```

Possible changes:

```text
unchanged
improved
regressed
new
removed
```

Examples:

- previous `FAIL`, current `OK` → improved;
- previous `OK`, current `FAIL` → regressed;
- newly required scenario → new;
- removed scenario → removed.

A gold update alone must not erase the fact that behavior changed.

Version control review remains necessary.

---

## 78. Artifact ownership

| Artifact | Owner |
|---|---|
| `.gfs` scenario | active project maintainer |
| scenario input | active project maintainer |
| `.gold` | active project maintainer through explicit update |
| raw stdout | process runner |
| raw stderr | process runner |
| normalized `.out` | scenario runner/normalizer |
| gold diff | gold comparator |
| `ScenarioResult` | scenario runner |
| summary serialization | JSON report writer |
| human scenario report | report writer |
| manifest record | manifest writer |

No observer may rewrite another owner’s artifact.

---

## 79. Manifest integration

The run manifest should include:

- raw stdout;
- raw stderr;
- normalized output;
- gold diff when generated;
- scenario-generated artifacts copied or catalogued into the run;
- structured detail files when persisted.

Project source `.gfs` and `.gold` files are normally referenced by source metadata, not copied into the run unless export policy requires it.

Hashes should be computed after final writes.

---

## 80. Reporting

Reports consume `ScenarioResult`.

They must not:

- rerun GF;
- reparse scenario markers independently;
- recompute gold comparison with different rules;
- modify normalized output;
- modify gold;
- infer missing fields from filenames when explicit fields exist.

Reports should show:

- scenario ID;
- required/optional;
- status;
- duration;
- primary message;
- failing sections/assertions;
- gold result;
- blocker when downstream;
- evidence paths.

---

## 81. CLI behavior

The CLI may support:

```text
scenario selection
scenario listing
mode selection
diagnostic verbosity
explicit gold-update command
```

The CLI must not:

- embed scenario execution logic;
- use shell redirection;
- bypass required release scenarios;
- update gold during ordinary validation.

Exit codes derive from the final run result.

---

## 82. GUI behavior

The GUI may:

- list configured scenarios;
- show required/optional status;
- display progress;
- show assertion failures;
- open raw or normalized evidence;
- request an explicit gold-update workflow.

The GUI must not:

- edit scenario status in application state;
- directly start GF;
- treat absence of process error as pass;
- silently approve changed gold.

---

## 83. Configuration errors

Examples:

- duplicate scenario ID;
- missing script;
- required scenario not declared for release;
- unsupported normalization version;
- gold outside project root;
- invalid timeout;
- duplicate expected section;
- invalid working directory;
- input path missing;
- comparison policy unknown.

These errors should be detected before scenario execution when possible.

---

## 84. Script errors

Examples:

- unreadable UTF-8;
- prohibited command;
- missing required termination convention;
- malformed required marker declaration;
- script exceeds configured size;
- scenario changed after integrity check.

Script errors produce scenario `ERROR`.

GF-reported syntax errors after launch may be reported as `FAIL` or `ERROR` according to whether the scenario contract was valid but the project scenario itself failed.

The centralized error model defines the final distinction.

---

## 85. Timeout behavior

Every scenario has a finite timeout.

On timeout:

- process runner terminates the owned process tree;
- raw output captured so far remains available;
- `execution_state = timed_out`;
- `timed_out = true`;
- `status = ERROR`;
- `error_kind = TIMEOUT`;
- gold comparison is skipped;
- normalized output may be generated only as diagnostic evidence and must be marked incomplete;
- a required scenario blocks release.

A timeout is not a normal GF validation failure.

---

## 86. Cancellation behavior

On cancellation:

- process runner terminates the owned process tree;
- current evidence is preserved;
- `execution_state = cancelled`;
- `cancelled = true`;
- `status = ERROR`;
- gold comparison is skipped;
- the reason is recorded;
- remaining scenarios follow run-level cancellation policy.

User cancellation must not be mislabeled as timeout.

---

## 87. Output-limit behavior

When output exceeds the configured bound:

- process execution is cancelled;
- `error_kind = OUTPUT_LIMIT`;
- `status = ERROR`;
- captured evidence remains available;
- truncation or cancellation is explicit;
- exact gold comparison is skipped;
- the scenario blocks release when required.

Generation scenarios should use tighter output limits than ordinary load scenarios.

---

## 88. Decoding failure

If raw bytes cannot be decoded under the declared policy:

- original bytes remain preserved;
- decoding issue is recorded;
- marker and text assertions may become unavailable;
- scenario status is `ERROR` when required interpretation cannot proceed;
- reports may show a safe bounded representation;
- no bytes are silently discarded.

---

## 89. Normalization failure

Normalization failure produces:

```text
status = ERROR
error_kind = NORMALIZATION
gold_match = null
```

Raw outputs remain available.

The runner must not compare raw output directly as a fallback when exact normalized comparison was required.

---

## 90. Gold mismatch

Gold mismatch produces:

```text
status = FAIL
error_kind = GOLD
gold_match = false
```

when no higher-priority error exists.

A diff should be generated.

The gold file remains unchanged.

---

## 91. Expected-failure scenarios

A project may define negative scenarios.

Examples:

- phrase must not parse;
- invalid construction should be rejected;
- known unsupported operation should produce a specific diagnostic.

Negative scenarios must declare:

- expected failure domain;
- expected assertion;
- prohibited accidental outcomes.

A negative scenario passes only when the intended condition is proven.

“Any error occurred” is insufficient.

---

## 92. Known-issue scenarios

A project may retain a scenario for a known issue.

Its policy must be explicit:

```text
blocking
expected-failure
informational
temporarily optional
```

The known issue must also appear in:

```text
project/docs/KNOWN_ISSUES.md
project/docs/STATUS_LEDGER.md
```

Expected-failure scenarios should not conceal newly different errors.

---

## 93. Scenario changes

A scenario change requires review of:

- scenario contract;
- project validation spec;
- expected sections;
- inputs;
- normalization impact;
- gold file;
- coverage matrix;
- release criteria;
- project interfile lock;
- changelog or decision log when behavior changes materially.

Changing a scenario solely to make a failure disappear is prohibited unless the expectation itself was wrong and the decision is documented.

---

## 94. Gold changes

A gold change requires:

- current scenario execution;
- normalized actual output;
- visible diff;
- linguistic review;
- confirmation that normalization version is correct;
- update of relevant decision or status documentation when material;
- version-control review.

A framework refactor that changes no intended behavior should not require gold changes.

Unexpected widespread gold changes indicate possible normalization or environment drift.

---

## 95. Normalization changes

Normalization changes require review of:

- normalizer implementation;
- normalization version;
- scenario output schema;
- all affected gold files;
- unit tests;
- migration documentation;
- external-tool lock;
- persisted-schema lock;
- changelog.

A normalizer must not be changed to hide a real linguistic regression.

---

## 96. Test structure

Recommended framework tests:

```text
tests/scenarios/
├── test_scenario_registry.py
├── test_scenario_selection.py
├── test_scenario_preflight.py
├── test_scenario_request.py
├── test_scenario_markers.py
├── test_scenario_assertions.py
├── test_scenario_normalization.py
├── test_scenario_gold.py
├── test_scenario_result.py
├── test_scenario_release_gate.py
├── test_scenario_security.py
└── test_scenario_regression.py
```

Contract tests:

```text
tests/contracts/test_scenario_contracts.py
tests/contracts/test_gf_scenario_contract.py
```

Schema tests:

```text
tests/schemas/test_scenario_output_schema.py
tests/schemas/test_gold_schema.py
tests/schemas/test_summary_schema.py
```

---

## 97. Unit tests without GF

Use fake process results to test:

- successful scenario;
- non-zero exit;
- timeout;
- cancellation;
- launch failure;
- stdout-only diagnostics;
- stderr-only diagnostics;
- invalid UTF-8;
- output-limit failure;
- marker success;
- missing begin marker;
- missing end marker;
- duplicate marker;
- invalid marker order;
- no-marker policy;
- normalization success;
- normalization error;
- exact gold match;
- gold mismatch;
- missing gold;
- wrong scenario ID in gold;
- normalization-version mismatch;
- required artifact missing;
- required/optional aggregation;
- deterministic ordering;
- downstream prerequisite skip.

---

## 98. Integration tests with real GF

A small fixture grammar should test:

- load scenario;
- parse scenario;
- linearization scenario;
- missing-linearization scenario where available;
- bounded generation;
- scenario over direct stdin;
- explicit termination;
- marker emission;
- path containing spaces;
- UTF-8 language text;
- successful gold comparison;
- deliberate gold mismatch;
- timeout containment where safely testable.

Real-GF tests should be marked separately.

---

## 99. Security tests

Test that:

- shell operators in input remain scenario data or are rejected;
- OS escape commands are rejected by policy;
- scenario path escape is rejected;
- gold path escape is rejected;
- input path escape is rejected;
- scenario cannot overwrite source;
- normal execution cannot modify gold;
- output-limit cancellation works;
- secrets are not persisted;
- reports do not execute scenarios;
- a malicious scenario cannot choose an arbitrary executable through project text.

---

## 100. Determinism tests

Given equivalent:

```text
project sources
scenario scripts
input files
gold files
GF version
resolved configuration
normalization version
```

the following should be deterministic:

- selected scenario order;
- process request arguments;
- working directory;
- expected sections;
- assertion order;
- normalized output;
- gold result;
- result ordering;
- artifact paths;
- summary serialization.

Timestamps and durations are excluded from exact determinism.

---

## 101. Performance policy

Scenario validation prioritizes correctness and evidence.

Performance rules:

- sequential by default;
- one GF process per scenario;
- bounded output;
- finite timeout;
- no unbounded generation;
- no complete output duplication in memory;
- no duplicate scenario run for reports;
- no automatic rerun after failure;
- optional scenarios may be omitted from latency-sensitive modes.

---

## 102. Migration from GF Audit

The inherited GF Audit baseline does not yet include the final scenario runner.

Migration requires:

1. add `ScenarioSpec` and `ScenarioResult`;
2. add `app/audit/scenario_runner.py`;
3. add direct standard-input support to process execution;
4. add scenario run paths;
5. add scenario configuration loading;
6. add marker parsing;
7. add normalization service;
8. add gold comparator;
9. add scenario totals;
10. add scenario serialization;
11. add report sections;
12. add release gates;
13. add contract and integration tests;
14. add project scenario and gold templates.

Existing file-compilation behavior remains separate.

---

## 103. Recommended implementation boundaries

```text
app/audit/scenario_runner.py
    scenario coordination and result construction

app/audit/scenario_registry.py
    optional extraction when registry logic becomes substantial

app/audit/scenario_markers.py
    marker event parsing and section validation

app/audit/scenario_assertions.py
    bounded generic assertion evaluation

app/audit/normalization.py
    shared versioned output normalization

app/audit/gold.py
    gold loading, validation, comparison, and diff

app/utils/process_utils.py
    process execution only
```

These modules should be created only when responsibility size justifies separation.

A compact initial implementation may keep private marker and assertion helpers in `scenario_runner.py`.

Normalization and process execution should remain separate owners from the start.

---

## 104. Public API

Recommended runner API:

```python
def run_scenario(
    spec: ScenarioSpec,
    run_config: RunConfig,
    run_paths: RunPaths,
    *,
    cancellation_token: CancellationToken | None = None,
) -> ScenarioResult:
    ...
```

Recommended batch coordinator:

```python
def run_scenarios(
    specs: Sequence[ScenarioSpec],
    run_config: RunConfig,
    run_paths: RunPaths,
    *,
    cancellation_token: CancellationToken | None = None,
) -> list[ScenarioResult]:
    ...
```

Batch results preserve input registry order.

The orchestrator may call scenarios individually if it needs stage-level progress and cancellation control.

---

## 105. Exceptions versus results

Expected scenario failures should be structured results.

Examples represented as `ScenarioResult`:

- parse expectation failed;
- marker missing;
- gold mismatch;
- GF returned non-zero;
- required artifact absent.

Exceptions should be reserved for:

- programming errors;
- corrupted internal invariants;
- impossible filesystem ownership violations;
- unsupported internal configuration state;
- failures preventing safe result construction.

The orchestrator must preserve evidence when converting an exception into a run-level error.

---

## 106. No duplicate parsing

The following must each have one owner:

- marker parsing;
- diagnostic parsing;
- normalized section extraction;
- gold comparison;
- scenario status aggregation.

Reports and GUI code consume structured fields.

They must not parse raw scenario text to reconstruct missing model data.

---

## 107. Coverage mapping

Every required scenario should map to:

- one project validation objective;
- one or more project contracts;
- one coverage-matrix entry;
- one release criterion when release-required.

Recommended references:

```text
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/RELEASE_CRITERIA.md
```

A required scenario with no documented objective indicates documentation drift.

---

## 108. Scenario review checklist

```text
[ ] Scenario ID is stable and unique
[ ] Script path is project-contained
[ ] Script is UTF-8
[ ] Script terminates according to policy
[ ] Required markers are declared
[ ] Marker IDs are unique
[ ] Entrypoint is documented
[ ] Input assets are declared
[ ] Timeout is finite
[ ] Output bound is finite
[ ] Required/optional status is explicit
[ ] Enabled modes are explicit
[ ] Assertions are bounded and meaningful
[ ] Gold policy is explicit
[ ] Normalization version is explicit
[ ] Required artifacts are explicit
[ ] Security policy passes
[ ] Project validation spec references the scenario
[ ] Coverage matrix references the scenario
[ ] Project contract lock references affected relationships
```

---

## 109. Runner compliance checklist

```text
[ ] Executes GF, not a custom interpreter
[ ] Uses the shared process runner
[ ] Uses direct stdin, not shell redirection
[ ] Records actual executable and arguments
[ ] Uses explicit working directory
[ ] Captures stdout and stderr separately
[ ] Preserves raw evidence before normalization
[ ] Applies finite timeout
[ ] Applies output limit
[ ] Supports cancellation
[ ] Validates required markers
[ ] Reads both streams for diagnostics
[ ] Invokes one normalization owner
[ ] Compares only normalized output
[ ] Never updates gold in normal validation
[ ] Produces immutable ScenarioResult
[ ] Preserves deterministic registry order
[ ] Reports missing required scenarios as configuration errors
[ ] Reports required skipped scenarios as release blockers
[ ] Does not classify dependency causality in the process layer
```

---

## 110. Release compliance checklist

```text
[ ] All required release scenarios exist
[ ] All required release scenarios are valid
[ ] All required release scenarios executed
[ ] All required release scenarios are OK
[ ] No required scenario timed out
[ ] No required scenario was cancelled
[ ] No required scenario exceeded output limit
[ ] All required sections completed
[ ] All required assertions passed
[ ] All required gold files exist
[ ] All required gold headers are valid
[ ] All required gold comparisons match
[ ] All required artifacts exist
[ ] Scenario evidence is present in the manifest
[ ] No blocking known issue invalidates scenario evidence
```

---

## 111. Prohibited behavior

The following are prohibited:

- Python reimplementation of GF scenario commands;
- shell redirection for ordinary `.gfs` execution;
- scenario execution outside the shared process runner;
- implicit infinite timeout;
- unbounded generation;
- merged raw stdout and stderr;
- discarding raw output after normalization;
- passing because exit code is zero while markers are missing;
- passing because no error text was recognized;
- raw-output comparison when normalized comparison is required;
- silent gold creation;
- silent gold update;
- report-time scenario execution;
- GUI-time alternate scenario logic;
- active-language assumptions in framework code;
- nondeterministic filesystem scenario ordering;
- one long-lived hidden GF session shared across unrelated scenarios;
- expected-failure scenario accepting any unrelated error;
- normalization removing meaningful linguistic evidence;
- project state overriding required scenario status;
- missing required gold treated as pass;
- timeout reported as ordinary linguistic failure.

---

## 112. Drift indicators

Scenario-validation drift exists when:

- project configuration references a missing scenario;
- a scenario file exists but is absent from the registry without explanation;
- runner and gold comparator normalize differently;
- marker parsing exists in multiple modules;
- reports parse raw output independently;
- scenario ordering changes with filesystem order;
- CLI and GUI select different required scenarios;
- a gold file changes during normal execution;
- required scenario failure does not affect release;
- a new scenario field is used but not modeled;
- `ScenarioResult` changes without serializer updates;
- normalized output changes without version change;
- a scenario loads a different entrypoint than project documentation states;
- an input file changes without coverage or gold review;
- one scenario relies on state left by another process;
- direct and downstream classes are assigned by the process runner;
- scenario output paths are reconstructed outside `RunPaths`;
- a missing end marker is accepted;
- a zero exit code overrides a gold mismatch.

Any drift indicator requires coordinated review.

---

## 113. Change classification

### 113.1 Internal compatible change

Examples:

- private helper refactor;
- faster marker parser with identical results;
- improved logging;
- more efficient file reads.

No schema or contract change is required when observable behavior remains identical.

### 113.2 Compatible extension

Examples:

- new optional result metadata;
- new optional assertion kind with a safe default;
- new optional scenario tag;
- additional non-blocking report detail.

Requires:

- model review;
- consumer review;
- tests;
- schema minor version when persisted.

### 113.3 Breaking change

Examples:

- scenario-ID rename;
- required/optional semantic change;
- marker syntax change;
- normalized-output meaning change;
- gold format change;
- result-field rename;
- comparison-policy change;
- path-layout change;
- release-gate change.

Requires:

1. contract analysis;
2. project migration;
3. scenario and gold review;
4. model and serializer update;
5. test update;
6. documentation update;
7. changelog entry;
8. version increment where applicable.

---

## 114. Final invariants

1. Scenarios remain native `.gfs` project assets.
2. GF executes GF semantics.
3. The framework coordinates but does not reinterpret GF command language.
4. One resolved scenario produces one isolated GF process by default.
5. Scenario order is deterministic.
6. Required and optional scenarios remain distinct.
7. Missing required scenarios are configuration errors.
8. Every scenario process has a finite timeout.
9. Every scenario process has a finite output limit.
10. Stdout and stderr remain separate.
11. Raw output is preserved before normalization.
12. Process exit code is not complete scenario success.
13. Required markers prove expected sections completed.
14. Missing required end markers cause failure.
15. Diagnostic inspection considers both streams.
16. Assertions are bounded and explicitly typed.
17. Normalization is centralized and versioned.
18. Linguistically meaningful output is never normalized away.
19. Gold comparison uses normalized output.
20. Missing required gold is never an automatic pass.
21. Normal validation never modifies gold.
22. Gold mismatch is a validation failure, not a process launch error.
23. Timeout, cancellation, and output limit are execution errors.
24. Scenario results are immutable after construction.
25. Reports consume results and never rerun scenarios.
26. Release requires every mandatory scenario to pass.
27. Project-specific expectations remain in the active project.
28. Framework code remains language-neutral.
29. Scenario changes, inputs, gold, and documentation form one review unit.
30. Complexity is added only for a stable assertion, evidence, or safety requirement.

---

## 115. Final rule

Scenario validation must answer one clear question:

> Did GF execute the project-owned scenario completely, safely, and with the reviewed result required by the active project?

The evidence chain is:

```text
ScenarioSpec
    → validated .gfs and inputs
    → direct GF execution
    → separate raw streams
    → process facts
    → completed sections
    → explicit assertions
    → versioned normalization
    → reviewed gold comparison when required
    → immutable ScenarioResult
    → run and release decision
```

No stage may skip a link in this evidence chain and still claim scenario success.
