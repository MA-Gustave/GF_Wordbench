# GF Wordbench Project Template — Validation Specification

**Document ID:** `GF-WB-PROJECT-VALIDATION-SPEC`  
**Status:** Normative project template  
**Applies to:** One active GF language project created from `templates/project/`  
**Template owner:** GF Wordbench maintainers  
**Project owner after initialization:** `<PROJECT_OWNER>`  
**Project ID:** `<PROJECT_ID>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**GF module suffix:** `<GF_SUFFIX>`  
**Project root:** `<PROJECT_ROOT>`  
**Source root:** `<SOURCE_ROOT>`  
**Configuration authority:** `project/project.toml`  
**Project contract authority:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Coverage authority:** `project/docs/TEST_COVERAGE_MATRIX.md`  
**Release authority:** `project/docs/RELEASE_CRITERIA.md`  
**Status authority:** `project/docs/STATUS_LEDGER.md` and `project/docs/KNOWN_ISSUES.md`  
**Template version:** `1.0.0`  
**Last reviewed:** `<YYYY-MM-DD>`

---

## 1. Purpose

This document defines the validation policy for one active GF language project.

It specifies:

- which project facts must be validated;
- which source files are selected;
- which modules are checkpoints;
- which modules are entrypoints;
- which native GF operations must run;
- which `.gfs` scenarios are required or optional;
- which scenario sections and assertions must pass;
- which normalized outputs are compared with reviewed gold files;
- which `.gfo` and `.pgf` artifacts are required;
- how process, diagnostic and artifact failures map to project results;
- how known issues and incomplete states affect release eligibility;
- which evidence must be persisted;
- which conditions constitute project release readiness.

The core rule is:

> Every project release criterion must map to current executable evidence or to an explicitly documented manual review when automation is not technically possible.

This template contains intentional placeholders.

It becomes an active project specification only after every required placeholder has been replaced, every non-applicable example has been removed or marked not applicable, and every declared rule agrees with `project/project.toml`, project source files, scenarios, gold files and the project interfile contract lock.

---

## 2. Template-use rule

This file under:

```text
templates/project/docs/VALIDATION_SPEC.md
```

remains generic.

When initializing a project, copy it to:

```text
project/docs/VALIDATION_SPEC.md
```

Then:

1. replace all required placeholders;
2. remove example scenario rows that do not apply;
3. add project-specific validation requirements;
4. align all module names with the active GF suffix;
5. align entrypoints and checkpoints with `project/project.toml`;
6. create every required scenario file;
7. create or approve every required gold file;
8. map every requirement into `TEST_COVERAGE_MATRIX.md`;
9. record temporary or blocked coverage in `STATUS_LEDGER.md`;
10. run initial validation and record the baseline evidence.

The active project copy MUST NOT retain unresolved required placeholders while claiming release readiness.

---

## 3. Placeholder vocabulary

The following placeholders are intentional in the reusable template:

```text
<PROJECT_OWNER>
<PROJECT_ID>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<PROJECT_ROOT>
<SOURCE_ROOT>
<SOURCE_GLOB>
<GF_VERSION_POLICY>
<RGL_PATH_POLICY>
<CHECKPOINT_MODULE>
<GRAMMAR_ENTRYPOINT>
<LANGUAGE_ENTRYPOINT>
<API_ENTRYPOINT>
<RELEASE_ENTRYPOINT>
<EXPECTED_GFO>
<EXPECTED_PGF>
<SCENARIO_ID>
<SCENARIO_FILE>
<INPUT_FILE>
<GOLD_FILE>
<NORMALIZATION_PROFILE>
<REQUIREMENT_ID>
<ISSUE_ID>
<YYYY-MM-DD>
```

Rules:

- placeholders are valid in `templates/project/`;
- placeholders are invalid in active normative project facts after initialization;
- examples must remain clearly labeled as examples;
- placeholder text must never be interpreted as a module, path, scenario or artifact;
- strict project checks should reject unresolved placeholders in the active copy.

---

## 4. Authority hierarchy

When project validation sources disagree, use this order:

1. `project/project.toml`;
2. `project/docs/INTERFILE_CONTRACT_LOCK.md`;
3. current GF source modules;
4. `project/docs/LANGUAGE_ARCHITECTURE.md`;
5. `project/docs/MODULE_DEPENDENCY_MAP.md`;
6. this active validation specification;
7. `project/docs/TEST_COVERAGE_MATRIX.md`;
8. `project/docs/STATUS_LEDGER.md`;
9. `project/docs/KNOWN_ISSUES.md`;
10. historical run artifacts.

This hierarchy does not allow configuration to override a broken source contract silently.

It identifies where the current intended facts are owned.

When the sources disagree, the project is in drift and must be repaired through a coordinated change.

---

## 5. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **VALIDATION REQUIREMENT**: one behavior or invariant that must be proven.
- **VALIDATION OBJECT**: configuration, source file, checkpoint, entrypoint, scenario, artifact or release gate being evaluated.
- **EVIDENCE**: persisted output proving or explaining a result.
- **CHECKPOINT**: module whose successful validation proves a dependency layer is coherent.
- **ENTRYPOINT**: top-level module used for grammar loading, API exposure, PGF construction or release.
- **SCENARIO**: registered native GF `.gfs` script.
- **GOLD**: reviewed normalized expected output.
- **REQUIRED**: non-success blocks the containing gate.
- **OPTIONAL**: visible validation that does not block every gate.
- **CONDITIONAL**: required only when a documented project condition is true.
- **MANUAL REVIEW**: explicit human verification used only when automation is not technically practical.
- **CURRENT ARTIFACT**: artifact proven to belong to the current invocation.
- **STALE ARTIFACT**: pre-existing artifact not proven to belong to the current invocation.
- **RELEASE BLOCKER**: condition preventing release readiness.

---

## 6. Scope

This specification governs project validation for:

- project configuration;
- source discovery;
- file selection;
- source hygiene scanning;
- direct source compilation;
- checkpoint compilation;
- entrypoint compilation and load;
- abstract/concrete completeness;
- missing-function inspection;
- morphology;
- parsing;
- linearization;
- bounded generation;
- project-specific structural behavior;
- extension families;
- scenario inputs;
- normalized scenario output;
- gold comparison;
- `.gfo` production;
- `.pgf` construction;
- artifact freshness;
- diagnostic classification;
- known issues;
- status-ledger states;
- release gates;
- evidence persistence.

---

## 7. Non-goals

This specification does not:

- reimplement GF parsing or type checking;
- define framework Python architecture;
- define the complete run-summary schema;
- define the external GF command contract;
- replace detailed morphology or syntax specifications;
- make GUI state authoritative;
- infer project identity from source filenames;
- infer entrypoints from naming conventions;
- update gold files during normal validation;
- accept incomplete behavior merely because it compiles;
- define language-specific facts in the reusable template.

---

## 8. Validation principles

Project validation follows these principles:

### 8.1 GF is authoritative

Native GF execution is authoritative for:

```text
source parsing
type checking
module loading
parsing
linearization
morphology
generation
missing-function inspection
.gfo production
.pgf production
```

### 8.2 Static scanning is supplementary

Static findings may identify risks but cannot replace native GF validation.

### 8.3 Raw evidence precedes interpretation

Process stdout and stderr are captured separately before parsing, normalization or reporting.

### 8.4 One requirement, one owner

Every validation requirement has one authoritative specification owner.

### 8.5 Deterministic ordering

File, checkpoint, entrypoint and scenario execution order is deterministic.

### 8.6 Normal validation is read-only

A normal run does not modify:

```text
project/project.toml
project/docs/
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
GF source files
```

### 8.7 Current evidence only

Stale `.gfo`, `.pgf`, normalized output or previous reports cannot satisfy current validation.

### 8.8 Incomplete states remain visible

Fallback, scaffolding, blocked, disabled and warning states remain recorded and participate in release policy.

### 8.9 Reports do not rerun validation

Reports consume structured completed results and evidence paths.

### 8.10 No silent release exception

Every release exception is explicit, reviewed, documented and linked to a decision or issue.

---

## 9. Canonical validation statuses

Project results use:

```text
OK
FAIL
ERROR
SKIPPED
```

### `OK`

The validation object executed and every applicable criterion passed.

### `FAIL`

The intended validation executed and produced interpretable evidence that a project criterion failed.

Examples:

- GF syntax or type failure;
- missing linearization;
- parse expectation not met;
- unexpected linearization;
- gold mismatch;
- required current artifact absent after otherwise reliable execution.

### `ERROR`

The framework could not complete or interpret validation reliably.

Examples:

- invalid project configuration;
- process timeout;
- cancellation;
- launch failure;
- I/O failure;
- unsupported schema;
- missing scenario markers;
- truncated required output;
- incompatible normalization profile;
- untrusted artifact;
- internal result inconsistency.

### `SKIPPED`

The object was not executed under an explicit selection or prerequisite rule.

A required release object that is skipped without an approved exception prevents release.

---

## 10. Canonical process execution states

External process execution uses:

```text
completed
timed_out
cancelled
launch_failed
```

These values are separate from validation status.

Required mapping:

| Execution state | Default validation status | Default error kind |
|---|---:|---|
| `completed` with passing criteria | `OK` | `OK` |
| `completed` with project/GF failure | `FAIL` | parsed kind |
| `completed` with uninterpretable contract failure | `ERROR` | `TOOL` or `OTHER` |
| `timed_out` | `ERROR` | `TIMEOUT` |
| `cancelled` | `ERROR` | `OTHER` |
| `launch_failed` | `ERROR` | `TOOL`, `CONFIG` or `IO` |

Cancellation is not a fifth validation status.

---

## 11. Canonical error kinds

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

Project documentation must not create competing error-kind values.

A project-specific linguistic expectation normally maps to `FAIL` with the closest safe kind or `OTHER`.

---

## 12. Canonical diagnostic classes

```text
ok
direct
downstream
ambiguous
noise
skipped
```

The classifier assigns diagnostic class.

A scenario script, diagnostic parser or project document must not assign causal ownership from one text fragment alone.

---

## 13. Validation modes

Canonical modes:

```text
quick
checkpoint
release
diagnostic
```

The active project must define which project requirements apply in each mode.

### 13.1 `quick`

Purpose:

- fast feedback on a selected target or narrow work area;
- source/configuration sanity;
- supplementary scan;
- direct native compilation where selected.

Quick mode does not prove release readiness.

### 13.2 `checkpoint`

Purpose:

- validate configured dependency layers;
- run checkpoint-associated scenarios;
- detect direct and downstream failures before final assembly.

### 13.3 `release`

Purpose:

- execute every required project gate;
- validate final entrypoints;
- run every required scenario;
- compare required golds;
- produce and verify required release artifacts;
- enforce issue and status-ledger policy.

### 13.4 `diagnostic`

Purpose:

- collect broad evidence;
- continue independent checks where safe;
- expose unknown diagnostics and incomplete coverage;
- investigate failures without weakening their statuses.

Diagnostic mode may gather more evidence but does not redefine success.

---

## 14. Project mode matrix

Replace this matrix during project initialization.

| Validation domain | `quick` | `checkpoint` | `release` | `diagnostic` |
|---|---:|---:|---:|---:|
| Project configuration | required | required | required | required |
| Source inventory | targeted | required | required | required |
| Static scan | targeted | configured | required if policy says so | broad |
| Direct file compilation | selected | configured | required set | broad |
| Checkpoint compilation | optional | required | required | required/broad |
| Final entrypoint compile | optional | configured | required | required |
| Entry load scenario | optional | configured | required | required |
| Missing-function scenario | optional | configured | required per policy | required |
| Parse scenarios | optional | configured | required set | broad |
| Linearization scenarios | optional | configured | required set | broad |
| Morphology scenarios | optional | configured | required set | broad |
| Generation scenarios | no/optional | optional | required only if deterministic/project-required | broad |
| Gold comparison | selected | configured | every required gold | every available comparable gold |
| PGF build | no | optional | required if configured | optional/diagnostic |
| Known-issue review | no | warnings | required | required |
| Manifest verification | required for completed run | required | required | required |

The active project must replace vague values such as `configured` with explicit policy where release significance exists.

---

## 15. Validation pipeline

Canonical project validation flow:

```text
resolve project identity
    → validate project schema
    → resolve toolchain and GF version
    → select source files
    → scan selected sources
    → compile selected files
    → validate checkpoints in dependency order
    → validate entrypoints
    → run registered scenarios
    → validate markers
    → normalize scenario output
    → compare required golds
    → verify generated artifacts
    → classify diagnostics
    → apply issue/status/release policy
    → build structured results
    → write reports
    → finalize manifest
```

A stage may be skipped only under explicit mode or dependency policy.

A skipped stage does not imply success.

---

## 16. Requirement identifiers

Project validation requirements use:

```text
VAL-<DOMAIN>-<NUMBER>
```

Recommended domains:

```text
CONFIG
SOURCE
SCAN
COMPILE
CHECKPOINT
ENTRY
SCENARIO
PARSE
LIN
MORPH
GEN
MISSING
GOLD
ARTIFACT
PGF
ISSUE
RELEASE
DOC
```

Examples:

```text
VAL-CONFIG-001
VAL-CHECKPOINT-003
VAL-LIN-002
VAL-RELEASE-001
```

Identifiers:

- are stable;
- are not reused;
- appear in the coverage matrix;
- link to scenarios or evidence;
- remain listed after retirement with a retired status where history matters.

---

## 17. Requirement entry template

Use this template for every project requirement.

```markdown
## VAL-<DOMAIN>-<NUMBER> — <Requirement title>

**Status:** required | optional | conditional | experimental | retired  
**Applies in modes:** quick | checkpoint | release | diagnostic  
**Owner:** <document/module/maintainer>  
**Project contract:** <PIFC-ID>  
**Decision:** <PDEC-ID or not applicable>

### Requirement

<State the exact behavior or invariant.>

### Validation object

<source file, checkpoint, entrypoint, scenario, artifact or document>

### Preconditions

- <precondition>;

### Execution

- <GF command, scenario or validation operation>;

### Success criteria

- <criterion>;

### Failure mapping

- <FAIL/ERROR/SKIPPED behavior>;

### Evidence

- <raw path>;
- <structured result>;
- <gold or artifact>;
- <report link>;

### Release impact

<blocking, non-blocking or conditional>

### Last reviewed

<YYYY-MM-DD or release>
```

---

## 18. Project configuration validation

### VAL-CONFIG-001 — Project schema identity

**Template status:** required

The active configuration must declare the canonical project schema identity and supported version.

Expected conceptual values:

```text
schema_id = gf-wordbench.project
schema_version = 1.0
```

Success criteria:

- schema ID recognized;
- schema version supported;
- file parses;
- required sections exist;
- unknown enum values are rejected safely;
- no secret values exist.

Failure:

```text
status = ERROR
error_kind = CONFIG
```

---

## 19. Project identity validation

### VAL-CONFIG-002 — Single active project identity

**Template status:** required

Validate:

```text
project ID
display name
language code
module suffix
project root
source root
```

Success criteria:

- values are non-empty and schema-valid;
- module suffix agrees with active source modules and scenarios;
- no previous-language active identifiers remain;
- identity does not depend on GUI state or old runs.

---

## 20. Project path validation

### VAL-CONFIG-003 — Portable project paths

**Template status:** required

Validate that project-owned paths:

- resolve from the documented base;
- remain inside approved roots;
- contain no accidental developer-specific tool paths;
- support spaces and Unicode;
- do not resolve through unsafe traversal;
- follow symlink policy.

Tool-local paths such as GF executable and RGL installation follow local configuration policy.

---

## 21. Project registry validation

### VAL-CONFIG-004 — Entrypoint, checkpoint and scenario registries

**Template status:** required

Validate:

- entrypoint IDs/modules are unique;
- checkpoint modules are unique;
- checkpoint order is deterministic;
- required scenario IDs are unique;
- optional scenario IDs are unique;
- required and optional sets do not overlap;
- every registered scenario file exists;
- no required registry value is a placeholder.

---

## 22. Toolchain validation

### VAL-CONFIG-005 — GF executable and compatibility

**Template status:** required

Validate:

- executable resolves;
- version probe completes;
- version is supported, conditionally supported or explicitly experimental;
- required commands/capabilities are available;
- working directory and GF path are explicit.

An untested GF version may be accepted only under documented mode/policy.

Strict release mode should reject unknown compatibility unless an explicit release decision permits it.

---

## 23. RGL and search-path validation

### VAL-CONFIG-006 — GF path components

**Template status:** required

Validate the ordered GF path components required by the active project.

The order must be deterministic.

Compilation and scenario execution must use compatible path construction.

A scenario must not invent a conflicting GF path.

---

## 24. Source inventory

### VAL-SOURCE-001 — Source root exists

**Template status:** required

Success criteria:

- source root resolves;
- it is a directory;
- it remains inside the approved project/repository scope;
- it is not a generated run directory.

### VAL-SOURCE-002 — Source selection is non-empty

**Template status:** required after bootstrap

Success criteria:

- source glob selects at least one intended `.gf` file;
- generated `.gfo` and `.pgf` files are excluded;
- temporary backup files are excluded under policy;
- selection order is deterministic.

A bootstrap project may temporarily allow an empty source selection only when explicitly recorded in `STATUS_LEDGER.md` and blocked from release.

---

## 25. Module declaration validation

### VAL-SOURCE-003 — File/module identity agreement

For every selected `.gf` file:

- file contains the expected GF module declaration;
- configured module references resolve;
- duplicate module names are prohibited;
- module suffix follows project policy;
- stale-language identifiers are rejected or migrated explicitly.

---

## 26. Dependency-map validation

### VAL-SOURCE-004 — Source imports agree with dependency map

Validate:

- every major direct import is documented;
- lower-level modules do not import final entrypoints;
- prohibited cycles are absent;
- provider ownership remains unique;
- moved/renamed modules are reflected in consumers;
- conditional interface/instance or extension families are documented.

Failure is normally project `FAIL`.

An unreadable source or impossible analysis is `ERROR`.

---

## 27. Static scanning

Static scanning is supplementary.

The active project must define which scan rules are:

```text
required
warning-only
experimental
disabled
```

Recommended scan domains:

- malformed or suspicious module declarations;
- duplicate public helpers;
- placeholder markers;
- unsafe temporary code;
- disallowed fallback patterns;
- stale suffixes;
- suspicious string flattening;
- unsupported local paths;
- copied backup files;
- unresolved `TODO` or `TBD` in release-significant source.

A scan result must preserve:

```text
rule ID
file path
line
column where available
message
severity/policy
```

A scan finding does not automatically become a GF `TYPE` or `SYNTAX` diagnostic.

---

## 28. Scan requirement template

| Requirement ID | Rule ID | Scope | Mode | Blocking | Rationale |
|---|---|---|---|---:|---|
| `<REQUIREMENT_ID>` | `<SCAN_RULE_ID>` | `<files>` | `<modes>` | yes/no | `<reason>` |

Remove this example row in the active project.

---

## 29. Direct file compilation

### VAL-COMPILE-001 — Selected source compilation

Compile each selected source file according to mode and file-selection policy.

Required process evidence:

```text
executable
arguments
working directory
GF version
stdout path
stderr path
exit code
execution state
duration
produced artifacts
```

Success requires:

- process launched;
- process completed;
- no timeout/cancellation;
- no fatal GF diagnostic;
- required `.gfo` artifact exists when expected;
- artifact belongs to the current operation.

---

## 30. Compilation failure semantics

A normal GF source failure:

```text
execution_state = completed
status = FAIL
error_kind = TYPE | SYNTAX | INTERNAL | OTHER
```

An execution failure:

```text
status = ERROR
```

Examples:

- timeout;
- cancellation;
- launch failure;
- capture failure;
- invalid GF path;
- artifact trust failure.

Do not report a timeout as a type error merely because partial output contains a type diagnostic.

---

## 31. Checkpoint registry

Replace this table with active checkpoint facts.

| Order | Checkpoint module | Layer proven | Required modes | Required scenario(s) | Release blocking |
|---:|---|---|---|---|---:|
| 1 | `<CHECKPOINT_MODULE>` | `<morphology/resources>` | checkpoint, release | `<SCENARIO_ID or none>` | yes |
| 2 | `<CHECKPOINT_MODULE>` | `<categories/lincats>` | checkpoint, release | `<SCENARIO_ID or none>` | yes |
| 3 | `<CHECKPOINT_MODULE>` | `<syntax/structural>` | checkpoint, release | `<SCENARIO_ID or none>` | yes |
| 4 | `<CHECKPOINT_MODULE>` | `<extensions>` | `<modes>` | `<SCENARIO_ID or none>` | `<yes/no>` |
| 5 | `<RELEASE_ENTRYPOINT>` | `<final assembly>` | release | `<SCENARIO_ID>` | yes |

The active project must remove unused rows and supply exact module names.

---

## 32. Checkpoint rules

- Every required checkpoint exists.
- Checkpoint order follows dependency order.
- Every checkpoint compiles before dependent checkpoints.
- A failed lower checkpoint may block dependent execution.
- A dependent skip remains visible.
- A downstream failure is not presented as an independent root failure when evidence identifies the provider.
- Skipping a release checkpoint requires an explicit release exception.
- Successful final entrypoint compilation does not erase a required checkpoint failure.

---

## 33. Entrypoint registry

Replace this table during initialization.

| Entrypoint role | Module | File | Consumers | Required modes | Expected artifact |
|---|---|---|---|---|---|
| Grammar | `<GRAMMAR_ENTRYPOINT>` | `<SOURCE_ROOT>/<GRAMMAR_ENTRYPOINT>.gf` | scenarios/compiler | checkpoint, release | `<EXPECTED_GFO>` |
| Language | `<LANGUAGE_ENTRYPOINT>` | `<SOURCE_ROOT>/<LANGUAGE_ENTRYPOINT>.gf` | scenarios/API | release | `<EXPECTED_GFO>` |
| API | `<API_ENTRYPOINT or not-applicable>` | `<path or not-applicable>` | application scenarios | `<modes>` | `<artifact>` |
| Release | `<RELEASE_ENTRYPOINT>` | `<SOURCE_ROOT>/<RELEASE_ENTRYPOINT>.gf` | PGF builder | release | `<EXPECTED_PGF>` |

A single module may serve several roles when documented explicitly.

---

## 34. Entrypoint validation

For each active entrypoint:

- configured module/file exists;
- module name matches configuration;
- direct imports are documented;
- required lower checkpoints pass;
- it compiles from a clean current artifact directory;
- it loads in GF through the required scenario;
- missing functions satisfy project policy;
- required scenarios target the documented entrypoint;
- expected `.gfo` is current;
- release entrypoint produces the expected `.pgf` when required.

---

## 35. Clean-build requirement

Release validation must not rely on pre-existing compiled objects.

The release workflow should use a clean run-owned artifact location or otherwise prove current ownership.

Success requires:

```text
current source state
current command
current GF version
current artifact
current manifest metadata
```

Stale artifact existence cannot satisfy a failed build.

---

## 36. Abstract/concrete completeness

The project must define the completeness policy for concrete implementations.

Possible release policies:

```text
zero missing functions
zero missing functions in release entrypoints
explicit allowlist for experimental modules
separate stable and experimental entrypoints
```

Replace this template text with one selected policy.

A missing-function result must remain visible.

---

## 37. Missing-function requirement template

```markdown
## VAL-MISSING-<NUMBER> — <Policy title>

**Entrypoint:** `<ENTRYPOINT>`  
**Scenario:** `<SCENARIO_ID>`  
**Required in release:** yes/no  
**Accepted missing set:** none | `<explicit allowlist>`  
**Gold/assertion:** `<GOLD_FILE or structural assertion>`  
**Blocking rule:** `<rule>`
```

---

## 38. Scenario registry

Every scenario is registered explicitly.

Directory presence alone does not activate a scenario.

Replace this table.

| Scenario ID | Script | Loaded entrypoint | Required | Modes | Inputs | Gold/assertion | Purpose |
|---|---|---|---:|---|---|---|---|
| `load` | `validation/scenarios/load.gfs` | `<ENTRYPOINT>` | `<yes/no>` | `<modes>` | none | marker/assertion | Load target grammar |
| `missing` | `validation/scenarios/missing.gfs` | `<ENTRYPOINT>` | `<yes/no>` | `<modes>` | none | `<GOLD_FILE/assertion>` | Inspect missing functions |
| `linearize` | `validation/scenarios/linearize.gfs` | `<ENTRYPOINT>` | `<yes/no>` | `<modes>` | `<INPUT_FILE/inline>` | `<GOLD_FILE>` | Validate representative trees |
| `parse` | `validation/scenarios/parse.gfs` | `<ENTRYPOINT>` | `<yes/no>` | `<modes>` | `<INPUT_FILE/inline>` | `<GOLD_FILE/assertion>` | Validate representative phrases |
| `morphology` | `validation/scenarios/morphology.gfs` | `<ENTRYPOINT>` | `<yes/no>` | `<modes>` | `<INPUT_FILE/inline>` | `<GOLD_FILE>` | Validate paradigms |
| `generation` | `validation/scenarios/generation.gfs` | `<ENTRYPOINT>` | no/conditional | diagnostic | `<INPUT_FILE/inline>` | bounded assertion | Investigate generation |

Example scenario IDs must be removed or completed in the active project.

---

## 39. Scenario identity rules

- IDs use lowercase kebab-case.
- Filename stem should equal scenario ID.
- IDs are unique.
- Required and optional status is configuration-owned.
- Scenario order follows configuration.
- Scenario files are UTF-8.
- Scenarios run as native GF shell scripts.
- Each scenario identifies its loaded entrypoint.
- Each scenario terminates under the selected GF execution contract.
- Interactive prompts are prohibited unless explicitly handled.
- Shell escape is disabled unless an explicit security-reviewed contract permits it.
- Scenario execution has finite timeout and output limits.

---

## 40. Scenario section markers

Canonical marker form:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
GF_WORDBENCH_END <scenario-id>:<section-id>
```

Rules:

- section IDs are unique within the scenario;
- every begin marker has one matching end marker;
- order is deterministic;
- marker text is not localized;
- marker identity is preserved by normalization;
- missing required markers produce `ERROR`;
- duplicate or overlapping marker structure produces `ERROR`;
- incomplete sections cannot pass gold comparison.

---

## 41. Scenario success baseline

A scenario can be `OK` only when:

- process launched;
- finite timeout did not expire;
- cancellation did not occur;
- process capture completed;
- required GF command contract passed;
- required begin/end markers are complete;
- fatal diagnostic policy passed;
- output is not truncated where exact evidence is required;
- normalization succeeded where applicable;
- gold comparison or structural assertion passed;
- required current artifacts exist.

A zero process exit code alone is insufficient.

---

## 42. Scenario input assets

Canonical location:

```text
project/validation/inputs/
```

Every external input file must define:

```text
path
format
encoding
line/record semantics
owner
consumer scenarios
ordering
stability
source/provenance
```

Rules:

- inputs are version-controlled when required for release;
- temporary generated inputs do not replace reviewed inputs;
- removal or reordering may invalidate golds;
- untrusted text is treated as scenario data, not shell command text;
- line endings and Unicode policy are explicit.

---

## 43. Input registry template

| Input ID | Path | Format | Encoding | Consumer scenarios | Ordering semantic | Stability |
|---|---|---|---|---|---:|---|
| `<INPUT_ID>` | `validation/inputs/<INPUT_FILE>` | `<format>` | UTF-8 | `<SCENARIO_ID>` | yes/no | stable/experimental |

Remove the example row in the active project.

---

## 44. Load scenarios

A load scenario proves that a documented target module can be loaded by GF.

Required assertions may include:

- entrypoint name appears in scenario metadata;
- load command completed;
- no fatal diagnostic;
- required markers complete;
- no unexpected fallback path;
- correct GF path used.

Loading a lower-level substitute is not equivalent to loading the configured release entrypoint.

---

## 45. Parse scenarios

For each parse requirement, define:

```text
input phrase
language
category
expected parse count
expected tree(s)
allowed ambiguity
forbidden tree(s)
negative-case policy
ordering semantics
```

Possible assertions:

- at least one parse;
- exactly one parse;
- expected tree present;
- only approved trees present;
- no parse for a negative input;
- parse count within a bound.

Absence of a fatal error does not prove parse success.

Raw tree output is preserved before normalization.

---

## 46. Parse requirement template

| Requirement ID | Input | Category | Expected count | Expected tree policy | Scenario section | Gold/assertion |
|---|---|---|---:|---|---|---|
| `<REQUIREMENT_ID>` | `<text/input ID>` | `<GF_CATEGORY>` | `<count/range>` | `<policy>` | `<section-id>` | `<GOLD_FILE/assertion>` |

---

## 47. Linearization scenarios

For each linearization requirement, define:

```text
abstract tree
target language
expected string or accepted variants
variant ordering
empty-string policy
punctuation/spacing policy
normalization profile
```

Success may require:

- exact expected output;
- one of an approved set;
- all approved variants in stable order;
- no empty output;
- no runtime diagnostic;
- gold match.

Normalization must not erase meaningful orthography.

---

## 48. Linearization requirement template

| Requirement ID | Abstract tree | Expected output policy | Variant order | Scenario section | Gold |
|---|---|---|---|---|---|
| `<REQUIREMENT_ID>` | `<GF_TREE>` | `<exact/approved-set>` | `<semantic/not-semantic>` | `<section-id>` | `<GOLD_FILE>` |

---

## 49. Morphology scenarios

Morphology validation may cover:

```text
noun paradigms
adjective paradigms
verb paradigms
pronouns
determiners
irregular forms
stem transformations
agreement dimensions
case/number/person/gender/definiteness
```

For every paradigm test, define:

- constructor or lookup operation;
- representative lexical item;
- requested form table;
- required fields;
- expected forms;
- empty/missing-form policy;
- variant policy;
- release significance.

A table that prints does not automatically prove every required cell exists.

---

## 50. Morphology requirement template

| Requirement ID | Domain | Item/constructor | Requested forms | Expected policy | Scenario section | Gold |
|---|---|---|---|---|---|---|
| `<REQUIREMENT_ID>` | `<noun/verb/etc.>` | `<item>` | `<forms>` | `<exact/property>` | `<section-id>` | `<GOLD_FILE/assertion>` |

---

## 51. Generation scenarios

Generation must remain bounded.

Define:

```text
category
depth/size bound
result limit
seed policy
ordering policy
duplicate policy
timeout
output byte limit
success assertion
```

Exact gold is allowed only when generation is deterministic under the declared GF version/profile.

Otherwise use bounded structural assertions.

Unbounded generation is prohibited.

---

## 52. Structural and extension scenarios

Project-specific structural and extension requirements should cover:

- canonical structural vocabulary;
- preposition/complement behavior;
- pronoun agreement;
- determiner agreement;
- conjunction behavior;
- extension constructor families;
- compatibility wrappers;
- fallback visibility;
- scaffolding exclusions.

Every extension family required for release must have:

- provider contract;
- consumer list;
- checkpoint or entrypoint compile evidence;
- scenario evidence;
- status-ledger alignment.

---

## 53. Negative scenarios

Negative scenarios intentionally validate rejection.

They must distinguish:

- expected GF rejection;
- unsupported input;
- project semantic rejection;
- process error;
- timeout;
- missing marker;
- tool incompatibility.

A timeout cannot satisfy a negative scenario.

Expected rejection normally produces project `OK` only when the scenario assertion explicitly requires and recognizes that rejection.

---

## 54. Assertion strategies

Allowed assertion strategies include:

```text
exact gold comparison
expected tree membership
parse-count range
absence/presence of missing functions
required artifact existence and integrity
bounded set membership
structured diagnostic expectation
explicit manual review
```

Every scenario must declare one primary assertion strategy.

“Command ran” is insufficient unless process execution itself is the requirement.

---

## 55. Normalization

Scenario comparison uses one central versioned normalization profile.

Each gold-backed scenario declares:

```text
profile_id
normalization_version
```

Normalization may remove approved execution instability such as:

```text
absolute paths
run paths
temporary paths
timestamps
durations
known prompts
terminal control sequences
compatible non-semantic banners
```

Normalization must preserve:

```text
linguistic strings
Unicode distinctions
punctuation
tree structure
constructor names
missing-function names
diagnostic meaning
section identity
semantic ordering
duplicates by default
```

---

## 56. Unknown and truncated output

### Unknown output

Unknown output is preserved and surfaced.

Policy:

- non-strict diagnostic mode may preserve with warning;
- strict/release comparison should fail when unknown output makes exact evidence unreliable.

### Truncated output

Truncated output cannot satisfy a required exact comparison.

The raw retained prefix remains evidence.

The result is normally `ERROR`.

---

## 57. Gold files

Canonical project location:

```text
project/validation/gold/<scenario-id>.gold
```

A gold file is:

- reviewed;
- project-owned;
- version-controlled;
- normalized expected semantic output;
- linked to one scenario/profile variant;
- independent from current run output.

A gold file is not:

- raw GF stdout;
- generated report output;
- a stale run artifact;
- automatically approved current behavior.

---

## 58. Gold requiredness

Every scenario declares:

```text
required
optional
not applicable
```

for gold comparison.

### Required

Missing or incompatible gold is non-success and blocks every gate where the scenario is required.

### Optional

Comparison occurs when present, but another explicit assertion defines success.

### Not applicable

A documented non-gold assertion is used.

The active specification must not leave requiredness ambiguous.

---

## 59. Gold comparison

Default comparison is exact after canonical container handling and central normalization.

Preserve:

- section order;
- line order;
- Unicode;
- punctuation;
- duplicate lines;
- empty sections;
- meaningful whitespace;
- final newline policy.

The comparator must not apply hidden semantic cleanup.

---

## 60. Gold result mapping

| Condition | Scenario status | `gold_match` |
|---|---:|---:|
| Exact match | `OK` | `true` |
| Valid mismatch | `FAIL` | `false` |
| Missing required gold | `FAIL` or configuration `ERROR` according to active policy | `null` |
| Unsupported gold schema | `ERROR` | `null` |
| Profile/version incompatibility | `ERROR` | `null` |
| Truncated actual output | `ERROR` | `null` |
| Scenario process timeout | `ERROR` | `null` |
| Gold not applicable and alternative assertion passes | `OK` | `null` |
| Scenario skipped | `SKIPPED` | `null` |

The active project should select one consistent missing-required-gold mapping and document it.

---

## 61. Gold updates

Normal validation never writes gold files.

An explicit gold update requires:

1. registered scenario;
2. successful complete process execution;
3. complete markers;
4. preserved raw stdout/stderr;
5. successful normalization;
6. known profile/version;
7. non-truncated actual output;
8. deterministic old/new diff;
9. linguistic or architectural review;
10. atomic replacement;
11. related specification and decision updates.

A gold must not be updated merely to make a failing scenario pass.

---

## 62. Gold registry template

| Scenario ID | Gold path | Required | Profile ID | Version | Approval owner | Release impact |
|---|---|---:|---|---|---|---|
| `<SCENARIO_ID>` | `validation/gold/<GOLD_FILE>` | yes/no | `<NORMALIZATION_PROFILE>` | `<MAJOR.MINOR>` | `<OWNER>` | `<blocking/non-blocking>` |

---

## 63. Artifact validation

Every generated artifact has:

```text
owner
producer
path base
role
requiredness
freshness rule
integrity rule
consumer
retention policy
```

Project validation must distinguish:

- source files;
- project assets;
- raw run evidence;
- normalized evidence;
- generated `.gfo`;
- generated `.pgf`;
- report artifacts;
- manifest records.

---

## 64. `.gfo` validation

A required `.gfo` counts only when:

- produced by the current compile operation;
- compile process completed;
- no fatal diagnostic invalidates it;
- path is expected;
- file exists;
- non-empty when required;
- not stale;
- recorded in the run artifact inventory.

A `.gfo` produced during timeout/cancellation is untrusted.

---

## 65. PGF validation

When release requires PGF, the active project must define:

```text
release entrypoint
expected PGF filename
required concrete language(s)
required public functions
artifact path policy
source fingerprint
consumer compatibility
```

PGF success requires:

- every required checkpoint passed;
- release entrypoint compiled;
- build process completed;
- expected file exists;
- file is current;
- artifact is non-empty;
- required concrete language is present;
- required functions satisfy policy;
- release scenarios pass;
- manifest records size/hash/role.

---

## 66. PGF registry template

| Requirement ID | Release entrypoint | Expected PGF | Required language | Required modes | Verification |
|---|---|---|---|---|---|
| `<REQUIREMENT_ID>` | `<RELEASE_ENTRYPOINT>` | `<EXPECTED_PGF>` | `<CONCRETE_LANGUAGE>` | release | `<inspection/assertion>` |

---

## 67. Artifact freshness

Freshness must not rely on file existence alone.

Use one or more:

```text
run-owned output directory
pre-launch cleanup of owned destination
creation/modification evidence
source fingerprint
command identity
manifest record
hash
producer metadata
```

Do not delete or overwrite source/project assets while proving freshness.

---

## 68. Diagnostic parsing

Diagnostic parsing structures GF text.

It must preserve:

- source stream;
- raw span or excerpt;
- file location where available;
- line/column where available;
- recognized pattern ID;
- severity;
- candidate error kind;
- incomplete multiline state;
- unknown evidence.

It does not assign direct/downstream causal ownership.

---

## 69. Failure classification

Classification uses:

- dependency map;
- checkpoint order;
- diagnostic locations;
- failed-provider evidence;
- blocked-by relationships;
- scenario/entrypoint relationships.

Rules:

- use `direct` only when evidence identifies the current owner;
- use `downstream` only when a failed prerequisite is known;
- use `ambiguous` when evidence is insufficient;
- use `noise` only for recognized non-failure output;
- never hide unknown diagnostics as noise.

---

## 70. File result requirements

A file result should preserve:

```text
file path
module identity where available
status
diagnostic class
error kind
primary message
error detail
scan counts
process result
raw stdout/stderr paths
produced artifacts
blocked-by relationships
duration
```

The exact persisted shape belongs to the run-summary schema.

---

## 71. Scenario result requirements

A scenario result should preserve:

```text
scenario ID
script path
requiredness
loaded entrypoint
status
error kind
diagnostic class
execution state
raw stdout/stderr paths
normalized output path
marker/section status
profile ID/version
gold path
gold match
diff path
warnings
duration
```

---

## 72. Evidence artifacts

At minimum, each applicable validation stage should preserve:

```text
executed command identity
GF version
working directory
stdout
stderr
structured result
normalized output where applicable
gold diff where applicable
generated artifacts
manifest entry
```

Reports may summarize but must link to canonical evidence.

---

## 73. Run summary and reports

Canonical machine source:

```text
summary.json
```

Human projections may include:

```text
summary.md
AI_READY.md
top_errors.txt
details/
```

Reports:

- consume structured results;
- do not rerun GF;
- do not change statuses;
- do not rewrite gold;
- do not normalize independently;
- do not infer missing evidence from prose.

---

## 74. Manifest validation

The run manifest verifies finalized artifact inventory.

Required checks:

- paths are run-relative;
- paths are unique;
- roles are recognized;
- required artifacts exist;
- sizes match;
- SHA-256 hashes match;
- no artifact remains open;
- manifest does not hash itself;
- untrusted partial artifacts are not mislabeled as successful release artifacts.

---

## 75. Timeout policy

Every external process uses a finite timeout.

The active project may choose operation-specific values through supported configuration.

It must not:

- use infinite timeout;
- extend deadline because output continues;
- treat timeout as a linguistic failure;
- trust partial artifacts;
- update gold from timeout output.

Timeout result:

```text
execution_state = timed_out
status = ERROR
error_kind = TIMEOUT
```

---

## 76. Cancellation policy

Cancellation:

- stops scheduling new dependent operations;
- terminates active owned processes;
- preserves partial evidence;
- does not produce release success;
- maps to `ERROR`;
- leaves unexecuted work visible as skipped under audit policy.

A cancelled run cannot become a baseline release run.

---

## 77. Process launch and capture failures

Launch, path, permission, encoding and capture failures are infrastructure/configuration errors.

They must not be represented as GF source errors.

Required evidence includes the requested command and safe launch error details.

---

## 78. Output and resource bounds

Every scenario and external process should define:

```text
timeout
stdout limit
stderr limit
combined output limit where supported
generation/result limit
maximum input size where relevant
```

A safety limit being reached remains explicit.

Strict exact validation cannot pass on truncated evidence.

---

## 79. Security validation

Project validation must check:

- scenario files are reviewed executable input;
- shell escape is disabled by default;
- scenario input cannot become shell fragments;
- paths remain inside approved roots;
- symlink policy is respected;
- no secrets are persisted;
- output rendering escapes untrusted text;
- cleanup cannot delete source or project golds;
- untrusted run artifacts are never executed.

Security violations are release blockers.

---

## 80. Determinism

Given equivalent:

```text
source state
project configuration
GF version
platform compatibility class
scenario inputs
normalization profile
```

normalized results should be deterministic.

The active project must define ordering for:

- source files;
- checkpoints;
- entrypoints;
- scenarios;
- scenario sections;
- variants;
- unordered semantic sets;
- gold contents.

Filesystem enumeration order is never authoritative.

---

## 81. Unicode and orthography

The active project must define:

- source encoding;
- input encoding;
- Unicode normalization policy;
- canonical output policy;
- accepted variants;
- punctuation and spacing semantics.

Execution-output normalization must not invent language orthography.

Linguistically meaningful Unicode differences remain visible.

---

## 82. Known issues

Every known issue records:

```text
issue ID
status
affected requirements
affected files/modules
evidence
workaround
release blocking
owner
exit condition
```

Accepted issues are explicit.

An undocumented warning cannot be silently accepted for release.

---

## 83. Status-ledger integration

Every temporary, fallback, blocked, warning, disabled, scaffolded or experimental implementation state must be represented in `STATUS_LEDGER.md`.

The validation specification must state:

- which requirement detects it;
- whether scenarios cover it;
- whether it blocks release;
- what evidence proves removal or promotion.

A compiling fallback is not automatically stable.

---

## 84. Manual review

Manual review is permitted only when automation is not technically practical.

Each manual criterion must state:

```text
requirement ID
reviewer role
review procedure
required evidence
acceptance criteria
record location
review date/release
```

“Maintainer looked at it” is insufficient.

Manual review cannot substitute for native GF compilation where compilation is technically available.

---

## 85. Coverage matrix relationship

Every required validation requirement must appear in:

```text
project/docs/TEST_COVERAGE_MATRIX.md
```

Minimum mapping:

```text
requirement ID
provider/source
checkpoint
entrypoint
scenario
input
gold/assertion
evidence artifact
release criterion
current status
```

A required release criterion without a coverage row is incomplete.

A scenario without a mapped requirement should be reviewed for purpose or redundancy.

---

## 86. Documentation consistency

Validation should check that:

- documented modules exist;
- module roles match current architecture;
- entrypoints match configuration;
- checkpoints match dependency order;
- scenario IDs match registry/files;
- gold IDs match scenarios;
- known issues reference valid requirements;
- status-ledger entries reference real modules;
- release criteria reference executable evidence;
- no stale language identifier remains;
- no required placeholder remains in active normative documents.

---

## 87. Release gate model

Release readiness is the conjunction of configured required gates.

Conceptually:

```text
project configuration valid
AND required source inventory valid
AND required checkpoints pass
AND required entrypoints pass
AND required scenarios pass
AND required golds match
AND missing-function policy passes
AND required PGF verifies
AND required artifacts verify
AND no release-blocking known issue remains
AND no release-blocking status-ledger item remains
AND required documentation/coverage is complete
```

No single successful artifact overrides another failed required gate.

---

## 88. Release criteria registry template

| Gate ID | Requirement | Evidence | Blocking | Exception allowed | Owner |
|---|---|---|---:|---:|---|
| `REL-001` | Project configuration valid | config result | yes | no | project maintainers |
| `REL-002` | All required checkpoints pass | checkpoint results | yes | `<policy>` | architecture maintainers |
| `REL-003` | All required scenarios pass | scenario results | yes | no | validation maintainers |
| `REL-004` | Required golds match | comparison results | yes | no | project reviewers |
| `REL-005` | Missing-function policy passes | missing scenario | yes | `<policy>` | architecture maintainers |
| `REL-006` | Required PGF verifies | artifact + manifest | `<yes/no>` | no | release maintainers |
| `REL-007` | No blocking issues | issue/ledger review | yes | explicit only | project owner |

Replace or extend this table in the active project.

---

## 89. Release exception policy

A release exception must state:

```text
exception ID
affected gate
reason
risk
scope
owner
approval
expiry or review condition
user impact
evidence
```

Rules:

- no implicit exception;
- no exception through GUI-only state;
- no permanent exception without updating project policy;
- no exception that converts timeout, capture failure or untrusted artifact into success;
- no exception that updates gold automatically.

---

## 90. Baseline run

A project may designate a compatible baseline run for previous-run regression comparison.

The baseline is not a replacement for gold.

Baseline selection must define:

```text
run ID
project identity
project version
schema compatibility
GF compatibility
source fingerprint relationship
selection rationale
```

A failed or partial release run must not become the accepted baseline without explicit policy.

---

## 91. Gold comparison versus run regression

Gold comparison asks:

```text
Does current normalized behavior equal accepted behavior?
```

Previous-run comparison asks:

```text
How did current behavior change relative to a compatible prior run?
```

These are distinct.

A result may be unchanged from the baseline but still fail gold.

A result may change from the baseline and become correct according to gold.

---

## 92. Compatibility and versions

The active project must record as applicable:

```text
GF Wordbench application version
project schema version
project version
GF version
diagnostic parser version
normalization profile versions
gold schema version
run-summary schema version
manifest schema version
```

Application version does not replace schema/profile/project versions.

---

## 93. GF version changes

Before accepting a new GF version:

1. probe version/capabilities;
2. compile representative files;
3. run checkpoints;
4. run required scenarios;
5. review diagnostic parser behavior;
6. review normalization output;
7. compare golds;
8. build/verify PGF;
9. test supported platforms;
10. update compatibility policy.

A banner-only change should normally be handled through conservative normalization.

A semantic output change requires project review.

---

## 94. Project contract changes

A contract change is complete only when updated together:

```text
provider
direct consumers
downstream entrypoints
project configuration
scenarios
inputs
golds
dependency map
status ledger
decision log
validation specification
coverage matrix
release evidence
project interfile contract lock
```

An isolated file edit is insufficient.

---

## 95. Validation change classification

### Internal compatible change

Examples:

- private refactor;
- performance improvement preserving output;
- documentation clarification;
- additional non-semantic evidence.

Expected action:

- targeted tests;
- no gold update unless output legitimately changes.

### Compatible project addition

Examples:

- optional scenario;
- new lexical coverage preserving public behavior;
- optional artifact;
- new non-blocking scan rule.

Expected action:

- update configuration/docs/coverage;
- run affected checkpoints/scenarios.

### Breaking project change

Examples:

- module suffix rename;
- entrypoint change;
- lincat field change;
- constructor semantic change;
- scenario ID change;
- gold/profile major change;
- PGF identity change;
- weakened release gate.

Expected action:

- decision entry;
- migration;
- full consumer review;
- release validation.

---

## 96. Required project-specific validation sections

Before the active specification is complete, add explicit requirements for:

```text
language variety/dialect policy
orthography and Unicode
nominal morphology
adjectival morphology
verbal morphology
pronouns and determiners
word order
negation
questions
relative clauses
coordination
structural vocabulary
lexical coverage
irregular forms
public extension families
missing functions
release API
```

Mark non-applicable domains explicitly with rationale.

Do not leave the absence ambiguous.

---

## 97. Project validation inventory

Replace this high-level registry.

| Domain | Requirement IDs | Provider document | Automated evidence | Release required |
|---|---|---|---|---:|
| Identity/configuration | `VAL-CONFIG-*` | `project.toml` | config checks | yes |
| Source architecture | `VAL-SOURCE-*` | architecture/dependency map | inventory/compile | yes |
| Morphology | `<VAL-MORPH-*>` | `MORPHOLOGY_SPEC.md` | scenarios/golds | `<yes/no>` |
| Syntax | `<VAL-LIN/PARSE-*>` | syntax rules | scenarios/golds | `<yes/no>` |
| Lincats | `<VAL-COMPILE-*>` | category contract | checkpoints | yes |
| Structural vocabulary | `<REQUIREMENT_IDS>` | syntax/architecture | scenario/gold | `<yes/no>` |
| Extensions | `<REQUIREMENT_IDS>` | architecture/status ledger | compile/scenario | `<yes/no>` |
| Entrypoints | `VAL-ENTRY-*` | architecture/config | load/compile | yes |
| Missing functions | `VAL-MISSING-*` | validation/release policy | scenario/assertion | yes |
| PGF | `VAL-PGF-*` | release criteria | build/manifest | `<yes/no>` |
| Documentation | `VAL-DOC-*` | project docs | docs check | yes |

---

## 98. Initial validation sequence

For a newly initialized project:

### Phase 1 — Structure

- project directories exist;
- required documents exist;
- configuration parses;
- placeholders are identified.

### Phase 2 — Identity

- project ID, language code, suffix and source root are populated;
- stale-language names are removed.

### Phase 3 — Source inventory

- source files discovered;
- modules mapped;
- entrypoint candidates reviewed;
- checkpoints selected.

### Phase 4 — Direct native validation

- GF version captured;
- representative source compiles;
- raw evidence and structured result produced.

### Phase 5 — Checkpoints

- ordered layers compile;
- direct/downstream behavior reviewed.

### Phase 6 — Scenarios

- scripts created;
- entrypoints load;
- markers complete;
- assertions evaluated.

### Phase 7 — Golds

- normalized outputs reviewed;
- required golds approved explicitly.

### Phase 8 — Release artifact

- final entrypoint selected;
- PGF built if required;
- artifact freshness/integrity verified.

### Phase 9 — Release gate

- full `release` mode passes;
- manifest verifies;
- no blocking issue remains.

---

## 99. Bootstrap-incomplete policy

A project may temporarily be structurally valid while incomplete.

Examples:

```text
no final entrypoint
no required scenario yet
no gold yet
incomplete morphology
scaffolding module
unknown GF compatibility
```

Every bootstrap gap must:

- appear in `STATUS_LEDGER.md`;
- state an owner;
- state validation impact;
- state release impact;
- state an exit condition;
- remain visible in reports where applicable.

Bootstrap-incomplete projects must not claim release readiness.

---

## 100. Validation evidence review

For every release-significant failure, reviewers should be able to locate:

```text
structured status
error kind
diagnostic class
raw stdout
raw stderr
executed command
GF version
source/checkpoint/scenario identity
normalized output if applicable
gold and diff if applicable
produced artifact metadata
known issue or ledger link
```

If evidence cannot establish what ran and why it passed or failed, the validation result is incomplete.

---

## 101. Required automated checks

A complete project checker should validate:

1. schema and project identity;
2. source path and glob;
3. module suffix consistency;
4. entrypoint existence;
5. checkpoint existence/order;
6. scenario registration and file mapping;
7. scenario-to-entrypoint mapping;
8. scenario markers;
9. input file ownership/encoding;
10. gold mapping/schema/profile;
11. required gold existence;
12. expected `.gfo`/`.pgf` names;
13. status-ledger references;
14. known-issue release impact;
15. validation-spec requirement IDs;
16. coverage-matrix completeness;
17. unresolved active placeholders;
18. stale language identifiers;
19. required document existence;
20. release-gate traceability.

---

## 102. Conceptual commands

The following commands are conceptual until confirmed by `docs/usage/CLI_REFERENCE.md`:

```text
gf-wordbench project check
gf-wordbench project contracts check
gf-wordbench scenarios check
gf-wordbench normalization check
gf-wordbench gold check
gf-wordbench audit --mode quick
gf-wordbench audit --mode checkpoint
gf-wordbench audit --mode diagnostic
gf-wordbench audit --mode release
```

This template must not claim a conceptual command is implemented.

When the final CLI differs, the active project documentation must use the implemented command surface.

---

## 103. Test requirements for the specification itself

Framework/project checks should test:

- requirement ID uniqueness;
- scenario ID uniqueness;
- unresolved placeholder detection;
- entrypoint/checkpoint reference resolution;
- gold path consistency;
- coverage-matrix references;
- release-gate references;
- issue/ledger references;
- deterministic table/order parsing where automated;
- template/active separation.

The active project should test representative project rules through native GF integration.

---

## 104. Validation-spec drift indicators

Drift exists when:

- `project.toml` names a scenario absent from this spec;
- this spec names an entrypoint absent from configuration;
- a required scenario has no assertion;
- a required gold is missing;
- a gold exists with no registered scenario;
- a scenario loads an undocumented module;
- checkpoint order differs from the dependency map;
- a release criterion has no requirement ID;
- a requirement has no coverage row;
- a known issue does not state release impact;
- a temporary fallback has no ledger entry;
- PGF name differs from configuration;
- a timeout is described as `FAIL`;
- cancellation is described as a validation status;
- static scan is described as native GF proof;
- reports are used as validation input;
- normal validation updates project assets;
- language-specific facts remain in the generic template;
- required placeholders remain in the active copy.

Every drift condition requires restoration or a coordinated project decision.

---

## 105. Active-project completion checklist

Use after copying this template.

```text
[ ] Replace project metadata placeholders
[ ] Define GF version policy
[ ] Define source root and glob
[ ] Define module suffix policy
[ ] Register every entrypoint
[ ] Register every checkpoint in dependency order
[ ] Define file-selection policy
[ ] Define scan policy
[ ] Define direct compile requirements
[ ] Define missing-function policy
[ ] Register required scenarios
[ ] Register optional scenarios
[ ] Define every scenario entrypoint
[ ] Define every scenario section
[ ] Define every scenario assertion
[ ] Register every input file
[ ] Register every required gold
[ ] Define normalization profiles
[ ] Define gold-update review policy
[ ] Define expected .gfo artifacts
[ ] Define expected PGF artifact
[ ] Define artifact freshness checks
[ ] Define timeout/output bounds
[ ] Define known-issue policy
[ ] Define status-ledger release impact
[ ] Define manual review criteria
[ ] Map every requirement into TEST_COVERAGE_MATRIX.md
[ ] Align INTERFILE_CONTRACT_LOCK.md
[ ] Align RELEASE_CRITERIA.md
[ ] Remove non-applicable example rows
[ ] Remove unresolved active placeholders
[ ] Execute initial quick validation
[ ] Execute initial checkpoint validation
[ ] Execute diagnostic validation
[ ] Approve initial golds
[ ] Execute release validation
[ ] Verify manifest
[ ] Record baseline run
```

---

## 106. Template preservation checklist

For the reusable template copy:

```text
[ ] No active-language name
[ ] No active-language code
[ ] No real module suffix used as a default
[ ] No real source root used as a default
[ ] No active project scenario marked required
[ ] No active project gold name
[ ] No machine-specific GF path
[ ] No project-specific linguistic rule
[ ] Placeholders remain clearly intentional
[ ] Paths remain relative and generic
[ ] Example rows remain labeled examples
```

---

## 107. Related project-template documents

- `templates/project/README.md`
- `templates/project/project.toml`
- `templates/project/docs/00_PROJECT_START_HERE.md`
- `templates/project/docs/INTERFILE_CONTRACT_LOCK.md`
- `templates/project/docs/LANGUAGE_OVERVIEW.md`
- `templates/project/docs/LANGUAGE_ARCHITECTURE.md`
- `templates/project/docs/MODULE_DEPENDENCY_MAP.md`
- `templates/project/docs/CATEGORY_AND_LINCAT_CONTRACT.md`
- `templates/project/docs/MORPHOLOGY_SPEC.md`
- `templates/project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md`
- `templates/project/docs/TEST_COVERAGE_MATRIX.md`
- `templates/project/docs/STATUS_LEDGER.md`
- `templates/project/docs/DECISION_LOG.md`
- `templates/project/docs/KNOWN_ISSUES.md`
- `templates/project/docs/RELEASE_CRITERIA.md`
- `templates/project/docs/RESEARCH_EVIDENCE.md`
- `templates/project/validation/README.md`
- `templates/project/validation/scenarios/README.md`
- `templates/project/validation/gold/README.md`
- `templates/project/validation/inputs/README.md`

---

## 108. Related framework documents

- `docs/projects/PROJECT_MODEL.md`
- `docs/projects/CREATING_A_PROJECT.md`
- `docs/projects/PROJECT_COMPLETION_CHECKLIST.md`
- `docs/configuration/PROJECT_TOML_REFERENCE.md`
- `docs/validation/VALIDATION_OVERVIEW.md`
- `docs/validation/VALIDATION_PIPELINE.md`
- `docs/validation/VALIDATION_MODES.md`
- `docs/validation/FILE_SELECTION.md`
- `docs/validation/STATIC_SCANNING.md`
- `docs/validation/COMPILATION_VALIDATION.md`
- `docs/validation/SCENARIO_VALIDATION.md`
- `docs/validation/REGRESSION_COMPARISON.md`
- `docs/validation/RELEASE_GATES.md`
- `docs/scenarios/SCENARIO_FORMAT.md`
- `docs/scenarios/WRITING_GFS_SCENARIOS.md`
- `docs/scenarios/GOLDEN_TESTS.md`
- `docs/scenarios/UPDATING_GOLD_FILES.md`
- `docs/gf/GF_OUTPUT_NORMALIZATION.md`
- `docs/diagnostics/ERROR_CLASSIFICATION.md`
- `docs/diagnostics/TIMEOUTS_AND_PROCESS_FAILURES.md`
- `docs/architecture/ARTIFACT_MODEL.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`

---

## 109. Final enforcement rule

This template defines how one active language project turns source contracts and linguistic requirements into reproducible GF evidence.

It must remain generic.

The active project copy must become specific.

Therefore:

> A project validation requirement is not complete until its owner, validation object, execution, success criteria, failure behavior, evidence, release impact and coverage mapping are all explicit.

No project may claim release readiness while required placeholders, unregistered scenarios, missing golds, unverified entrypoints, stale artifacts or undocumented release exceptions remain.
