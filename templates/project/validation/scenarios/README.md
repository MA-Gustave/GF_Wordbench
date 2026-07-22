# <LANGUAGE_NAME> Validation Scenarios

**Document ID:** `GF-WB-PROJECT-SCENARIOS-README`  
**Status:** Normative project template  
**Applies to:** Native GF `.gfs` validation scenarios for one initialized GF Wordbench language project  
**Template owner:** GF Wordbench  
**Project owner:** `<PROJECT_OWNER>`  
**Project ID:** `<PROJECT_ID>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**Project root:** `<PROJECT_ROOT>`  
**Scenario root:** `project/validation/scenarios/`  
**Last reviewed:** `<YYYY-MM-DD>`  
**Scenario contract version:** `1.0.0`

**Normative counterparts:**
- `project/project.toml`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`
- `project/docs/VALIDATION_SPEC.md`
- `project/docs/TEST_COVERAGE_MATRIX.md`
- `project/docs/MODULE_DEPENDENCY_MAP.md`
- `project/docs/STATUS_LEDGER.md`
- `project/docs/DECISION_LOG.md`
- `project/docs/RELEASE_CRITERIA.md`
- `project/validation/inputs/README.md`
- `project/validation/gold/README.md`
- `docs/scenarios/SCENARIO_FORMAT.md`
- `docs/scenarios/WRITING_GFS_SCENARIOS.md`
- `docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md`
- `docs/scenarios/OUTPUT_NORMALIZATION.md`
- `docs/scenarios/GOLDEN_TESTS.md`
- `docs/validation/SCENARIO_VALIDATION.md`
- `docs/gf/GF_SCRIPT_EXECUTION.md`

---

## 1. Purpose

This directory contains native GF shell scenarios used to validate the active language project.

A scenario is a source-controlled `.gfs` script executed by GF through GF Wordbench.

Scenarios provide repeatable evidence for behavior such as:

- loading the configured grammar;
- checking missing linearizations;
- linearizing representative trees;
- parsing representative phrases;
- inspecting morphology;
- exercising agreement and constructor rules;
- testing questions, relatives, coordination, and complements;
- running bounded generation;
- performing stable grammar introspection;
- validating release entrypoints.

A scenario is not:

- a Python test script;
- a replacement GF interpreter;
- a report template;
- a gold file;
- a shell script;
- an unbounded interactive session;
- a place for undocumented manual experimentation.

> A project scenario must declare one validation purpose, load one documented project entrypoint, emit stable section markers, finish deterministically, and preserve enough evidence to decide whether its criterion passed.

---

## 2. Template completion rule

This file is a template.

Before an initialized project is release-ready:

- replace every required `<PLACEHOLDER>`;
- register all required and optional scenarios;
- create every required `.gfs` file;
- identify the entrypoint loaded by each scenario;
- document any external input file;
- define required output sections;
- define assertions or gold mapping;
- define mode membership;
- verify commands against the supported GF version;
- ensure all generation/introspection operations are bounded;
- remove any example scenario not applicable to the project;
- add language-specific scenario families required by project scope.

A release must fail when a required scenario remains represented only by this README.

---

## 3. Directory contract

Canonical directory:

```text
project/validation/scenarios/
```

Permitted contents:

```text
README.md
<scenario-id>.gfs
<scenario-id>.<variant-id>.gfs
```

Normally prohibited contents:

```text
.gold files
normalized .out files
raw stdout/stderr
generated .gfo files
generated .pgf files
Python scripts
PowerShell or shell scripts
temporary editor files
backup copies
run reports
unregistered input corpora
```

External scenario inputs belong under:

```text
project/validation/inputs/
```

Reviewed expected output belongs under:

```text
project/validation/gold/
```

Run evidence belongs under:

```text
run_<run-id>/raw/scenarios/
```

---

## 4. Ownership

Scenario files are owned by active project maintainers.

GF Wordbench may:

- locate registered scenarios;
- validate paths and encoding;
- read the script;
- pass it to GF through standard input;
- capture stdout and stderr separately;
- enforce a timeout;
- verify required markers and assertions;
- normalize selected output;
- compare normalized output with a gold;
- write run-owned evidence;
- report structured `ScenarioResult` values.

Normal validation must not rewrite scenario files.

Project-writing commands such as initialization or explicit migration may create or transform scenarios only through documented, reviewable operations.

---

## 5. Native GF execution

Scenarios remain native GF shell scripts.

Conceptual user-shell form:

```text
gf < project/validation/scenarios/<scenario-id>.gfs
```

GF Wordbench implementation must not depend on shell redirection.

It should:

1. open the `.gfs` file;
2. supply its contents through GF process standard input;
3. launch GF with an ordered argument list;
4. use `shell=False`;
5. capture stdout and stderr separately;
6. enforce a finite timeout;
7. preserve raw output before normalization.

The runner executes GF.

It must not reimplement the semantics of GF shell commands in Python.

---

## 6. Scenario identity

Standard scenario identifier:

```text
<scenario-id>
```

Standard filename:

```text
<scenario-id>.gfs
```

Recommended pattern:

```text
^[a-z][a-z0-9-]*$
```

Examples:

```text
load
missing
linearize
parse
generation
morphology-nouns
agreement-basic
questions-polar
relatives-object
```

### 6.1 Variant identity

Variant filename:

```text
<scenario-id>.<variant-id>.gfs
```

Examples:

```text
parse.strict.gfs
generation-small.gfs
morphology-irregular.gfs
```

Variants must be registered explicitly.

### 6.2 Prohibited names

Avoid:

```text
test.gfs
new.gfs
final.gfs
working.gfs
everything.gfs
copy.gfs
scenario2.gfs
```

Names must identify validated behavior.

---

## 7. Scenario registry

The active registry is defined by:

```text
project/project.toml
project/docs/VALIDATION_SPEC.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Schema `1.0` distinguishes:

```toml
[validation]
required_scenarios = [...]
optional_scenarios = [...]
```

### 7.1 Registry invariants

- scenario IDs are unique;
- required and optional lists do not overlap;
- every required scenario file exists;
- optional scenarios are marked explicitly;
- filenames should match scenario IDs;
- scenario order is deterministic;
- unregistered scenarios are not release evidence;
- every scenario loads a documented entrypoint;
- every gold-backed scenario identifies one authoritative gold;
- scenario removals update configuration and project validation documentation.

---

## 8. Recommended initial registry

Replace or extend this table for the active language.

| Scenario ID | Script | Required | Modes | Gold | Purpose |
|---|---|---:|---|---|---|
| `load` | `load.gfs` | Yes | `checkpoint`, `release` | Optional | Load the configured main grammar/entrypoint |
| `missing` | `missing.gfs` | Yes | `release` | `missing.gold` | Detect missing linearizations |
| `linearize` | `linearize.gfs` | Yes | `checkpoint`, `release` | `linearize.gold` | Validate representative abstract trees |
| `parse` | `parse.gfs` | `<Yes/No>` | `release` | `parse.gold` | Validate representative phrases |
| `generation` | `generation.gfs` | No | `diagnostic`, optionally `release` | Optional | Bounded generation checks |
| `morphology` | `morphology.gfs` | `<Yes/No>` | `checkpoint`, `diagnostic`, `release` | `<gold-or-none>` | Validate paradigms/forms |

Delete non-applicable entries and add project-specific scenarios.

---

## 9. Required and optional scenarios

### Required scenario

A required scenario:

- must exist;
- must be registered;
- must have a documented purpose;
- must load the documented entrypoint;
- must use compatible GF commands;
- must complete required markers;
- must satisfy assertions;
- must compare with required gold when configured;
- must not be skipped in release mode.

### Optional scenario

An optional scenario:

- remains registered;
- has a documented purpose;
- may run only in selected modes;
- may become required through a future project contract change;
- must not be counted as release evidence when not selected.

### Missing required scenario

A missing required scenario is a configuration error.

It is not a skipped test and not an automatic pass.

---

## 10. Scenario-to-entrypoint map

Complete this table.

| Scenario ID | Scenario file | Loaded entrypoint | Required | Purpose |
|---|---|---|---:|---|
| `<id>` | `<id>.gfs` | `<ENTRYPOINT_MODULE>` | `<yes/no>` | `<purpose>` |

### 10.1 Entrypoint rules

- the scenario must load the documented configured entrypoint;
- loading a lower-level substitute is not equivalent;
- module suffix migrations require scenario updates;
- a required scenario that cannot load its entrypoint fails;
- an entrypoint rename requires review of every scenario;
- release scenarios must not load test-only or temporary substitute modules unless explicitly approved.

---

## 11. Scenario-to-input map

When a scenario uses project input files, complete:

| Scenario ID | Input file | Format | Encoding | Record/line meaning | Ownership | Stability |
|---|---|---|---|---|---|---|
| `<id>` | `project/validation/inputs/<file>` | `<format>` | `UTF-8` | `<meaning>` | `<owner>` | `<stable/versioned>` |

### 11.1 Input invariants

- paths remain beneath the project input root;
- encoding is documented;
- line or record meaning is documented;
- scenario and input versions remain compatible;
- changing input order may invalidate golds;
- generated temporary inputs do not replace reviewed canonical release inputs;
- input files do not contain secrets or unrelated personal data.

---

## 12. Scenario-to-gold map

Complete for every gold-backed scenario.

| Scenario ID | Scenario file | Gold file | Normalization profile | Normalization version | Required |
|---|---|---|---|---|---:|
| `<id>` | `<id>.gfs` | `project/validation/gold/<id>.gold` | `<profile>` | `<version>` | `<yes/no>` |

### 12.1 Gold invariants

- required gold-backed scenarios identify one gold;
- scenario and gold IDs agree;
- missing required gold is not an automatic pass;
- normal validation never rewrites gold;
- gold comparison occurs after normalization;
- meaningful linguistic output remains;
- updates require an explicit reviewed operation.

---

## 13. File encoding

Canonical scenario encoding:

```text
UTF-8 without BOM
```

Canonical newline:

```text
LF
```

Readers may accept CRLF where supported.

Canonical writers and template renderers use LF.

A final newline is required.

---

## 14. Scenario structure

Recommended structure:

```text
# scenario metadata/comments

<load/import command>

<setup commands>

<begin marker>
<GF operation(s)>
<end marker>

<additional sections>

<explicit quit command>
```

### 14.1 Comments

Comments should explain:

- scenario purpose;
- loaded entrypoint;
- section meaning;
- boundedness;
- unusual GF-version requirement;
- input file dependency;
- accepted ambiguity.

Comments must not replace markers or executable validation.

### 14.2 Setup

Setup commands should be minimal and deterministic.

Do not rely on state left by another scenario.

Each scenario starts with a fresh GF process unless the scenario contract explicitly defines another isolated behavior.

---

## 15. Marker format

Recommended marker identity:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
GF_WORDBENCH_END <scenario-id>:<section-id>
```

The exact GF command used to emit text is version-dependent and defined by `SCENARIO_FORMAT.md`.

Example logical output:

```text
GF_WORDBENCH_BEGIN linearize:basic-declaratives
<GF output>
GF_WORDBENCH_END linearize:basic-declaratives
```

### 15.1 Marker invariants

- section IDs are unique within the scenario;
- every begin marker has one matching end marker;
- sections do not overlap;
- section order is deterministic;
- marker text is not localized;
- normalization preserves marker identity;
- required missing markers cause failure/error;
- a zero GF exit code does not override incomplete markers.

### 15.2 Section ID

Recommended pattern:

```text
^[a-z][a-z0-9-]*$
```

---

## 16. Assertions

A scenario may use:

- marker-completion assertions;
- expected text/regex assertions;
- count assertions;
- artifact assertions;
- gold comparison;
- semantic checks derived from stable GF output.

The final assertion syntax is defined by:

```text
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
```

### 16.1 Assertion requirements

Every assertion must define:

```text
assertion ID
section
criterion
expected value/pattern
failure message
release significance
```

### 16.2 Appropriate assertions

Examples:

```text
entrypoint loaded
parse count > 0
missing function count == 0
required constructor appears
generation count <= configured bound
required section completed
```

### 16.3 Gold vs assertion

Use a gold when the complete stable output matters.

Use an assertion when one scalar or presence condition matters.

A scenario may combine both.

---

## 17. Explicit termination

A scenario must terminate GF explicitly when required by the supported GF shell behavior.

Recommended conceptual final command:

```text
q
```

The exact supported quit command belongs to the GF script-execution contract.

### 17.1 No interactive wait

A scenario must not wait for user input.

### 17.2 No implicit EOF reliance in release

Where explicit termination is supported, release scenarios should use it.

### 17.3 Post-quit content

No required scenario operation may appear after the termination command.

---

## 18. Supported operation families

Exact syntax is GF-version checked.

Typical scenario operation families include:

| Purpose | Typical GF shell operation |
|---|---|
| import/load | `i` |
| parse | `p` |
| linearize | `l` |
| generate | `gr` |
| morphological analysis | `ma` |
| print grammar | `pg` |
| missing linearizations | `pm` or compatible operation |
| compute concrete | `cc` |
| show operations | `so` |
| show dependencies | `sd` |
| quit | `q` |

This README does not replace the official GF shell reference.

Only operations verified for the supported GF compatibility line may be used in required scenarios.

---

## 19. Unsupported command behavior

A scenario must not be considered successful merely because GF returned zero while ignoring or mishandling an unsupported command.

The runner should evaluate:

- raw stdout;
- raw stderr;
- exit code;
- timeout;
- required markers;
- explicit assertions;
- known unsupported-command diagnostics;
- expected artifacts.

Unsupported operations should produce an explicit scenario failure or error.

---

## 20. Working directory

Canonical scenario working directory:

```text
resolved project root
```

A different working directory requires an explicit scenario contract.

Scenarios must not depend on the GUI or terminal process current directory.

Relative paths inside a scenario are interpreted under the documented working-directory contract.

---

## 21. GF path

Scenario execution uses the same centralized effective GF path as:

- module compilation;
- grammar loading;
- PGF construction;
- introspection.

A scenario must not build or mutate a different GF path.

The effective path is resolved from:

- explicit run override;
- project path parts;
- RGL root/aliases;
- documented environment fallback;
- compatibility policy.

The resolved path is recorded in run evidence.

---

## 22. Raw evidence

Canonical paths:

```text
run_<run-id>/raw/scenarios/<scenario-id>.stdout.txt
run_<run-id>/raw/scenarios/<scenario-id>.stderr.txt
```

Raw output is captured before:

- marker extraction;
- assertion evaluation;
- normalization;
- gold comparison;
- report summarization.

Raw evidence must remain accessible after failure.

---

## 23. Normalized output

Canonical path:

```text
run_<run-id>/raw/scenarios/<scenario-id>.out
```

Canonical schema identity:

```text
GF_WORDBENCH_OUTPUT 1.0
```

Conceptual form:

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: <scenario-id>
# normalization_version: <version>
--- BEGIN <section-id> ---
<normalized output>
--- END <section-id> ---
```

Normalization is versioned and profile-based.

---

## 24. Normalization rule

Normalization may remove only documented unstable noise.

Possible examples:

- CRLF-to-LF;
- known GF prompt text;
- absolute run path;
- temporary path;
- timestamps;
- measured durations;
- platform path separators;
- version banners when semantically irrelevant.

Normalization must not remove:

- trees;
- linearizations;
- parse alternatives;
- ambiguity counts;
- morphology forms;
- missing-function lists;
- meaningful punctuation;
- language-significant Unicode;
- required markers;
- meaningful ordering or duplicates;
- relevant fatal diagnostics.

---

## 25. `ScenarioResult`

Each execution produces a structured scenario result.

Required semantic fields include:

```text
scenario_id
script_path
required
status
command
working_directory
exit_code
timed_out
duration_ms
stdout_path
stderr_path
normalized_output_path
gold_path
gold_match
diagnostic_class
error_kind
primary_message
sections
artifacts
```

Recommended future result model:

```python
@dataclass(frozen=True, slots=True)
class ScenarioResult:
    scenario_id: str
    script_path: str
    required: bool
    status: str
    command: tuple[str, ...]
    working_directory: str
    exit_code: int | None
    timed_out: bool
    duration_ms: int
    stdout_path: str | None
    stderr_path: str | None
    normalized_output_path: str | None
    gold_path: str | None
    gold_match: bool | None
    diagnostic_class: str
    error_kind: str
    primary_message: str
    sections: tuple["ScenarioSectionResult", ...]
    artifacts: tuple[str, ...]
```

The persisted schema remains authoritative.

---

## 26. Scenario statuses

Canonical statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

### `OK`

- execution completed;
- no timeout;
- required commands were supported;
- required markers completed;
- assertions passed;
- required gold matched;
- required artifacts existed.

### `FAIL`

The scenario executed correctly but did not satisfy its validation criterion.

Examples:

- assertion failed;
- marker-required operation produced wrong output;
- gold mismatch;
- missing-function inventory was non-empty when zero was required.

### `ERROR`

GF Wordbench could not execute or interpret the scenario reliably.

Examples:

- script missing/unreadable;
- GF launch failure;
- timeout;
- invalid configuration;
- invalid marker structure;
- normalization failure;
- invalid gold schema.

### `SKIPPED`

The scenario was intentionally not selected or not applicable.

A required release scenario must not be skipped.

---

## 27. Execution states

Process execution state remains separate from validation status.

Examples:

```text
completed
timed_out
cancelled
launch_failed
terminated
```

A timed-out scenario normally contributes `ERROR`, not an ordinary linguistic `FAIL`.

---

## 28. Timeouts

Every scenario has a finite timeout.

Timeout selection should consider:

- operation family;
- input size;
- expected GF version;
- project size;
- release vs diagnostic use.

A required release scenario must not disable its timeout.

Timeout evidence includes:

```text
configured timeout
duration
partial stdout
partial stderr
termination result
execution state
```

---

## 29. Output bounds

Scenario output must be bounded.

Bound:

- generation count;
- tree depth;
- number of input phrases;
- morphology items;
- introspection scope;
- parse alternatives displayed;
- recursive operations;
- report excerpts.

Unbounded generation is prohibited in required scenarios.

A diagnostic scenario may use broader bounds, but still finite.

---

## 30. Determinism

Given the same:

- project source;
- GF executable/version;
- RGL identity;
- GF path;
- scenario script;
- input files;
- normalization profile;

the scenario should produce deterministic canonical output.

Avoid dependence on:

- current time;
- random generation without fixed seed;
- filesystem enumeration order;
- terminal dimensions;
- GUI state;
- previous run;
- absolute machine paths;
- network resources;
- interactive input.

---

## 31. Random generation

Random or nondeterministic generation must not be compared to an exact gold unless:

- a stable seed is supported and fixed;
- result ordering is stable;
- count is bounded;
- behavior is tested across supported GF versions.

Otherwise, use assertions:

```text
generation completed
at least one result exists
all results linearize
required constructor appears
result count within bound
```

---

## 32. Scenario isolation

Each scenario should be independently executable.

It must not rely on:

- another scenario having run;
- another scenario's output;
- a previous GF process;
- stale `.gfo` files;
- a prior generated PGF;
- a writable project source tree;
- an existing run directory.

Required setup belongs inside the scenario or shared documented entrypoint.

---

## 33. Security

A `.gfs` scenario is executable/semi-executable project input.

### 33.1 Shell escapes

GF shell features capable of invoking operating-system commands, piping, or shell utilities are prohibited under normal project policy.

### 33.2 Untrusted scenarios

Review scenarios from untrusted projects before execution.

### 33.3 Paths

Scenario and input paths must be validated for containment.

### 33.4 Secrets

Do not place in scenarios:

- credentials;
- tokens;
- private keys;
- private environment values;
- secret URLs;
- complete environment dumps.

### 33.5 Resource exhaustion

Bound output and execution to avoid disk exhaustion or runaway generation.

---

# Part I — Core scenario templates

## 34. `load.gfs`

Purpose:

- load the configured main entrypoint;
- prove the grammar can be imported by the GF shell;
- preserve load diagnostics;
- establish a base scenario for checkpoint/release modes.

Required documentation:

```text
loaded entrypoint
expected success marker
optional grammar identity check
timeout
```

Conceptual structure:

```text
# Load <ENTRYPOINT>

<IMPORT_ENTRYPOINT>

<EMIT_BEGIN load:grammar-loaded>
<BOUNDED_STABLE_LOAD_CHECK>
<EMIT_END load:grammar-loaded>

<QUIT>
```

### 34.1 Success

- entrypoint loads;
- marker completes;
- no fatal load diagnostic.

### 34.2 Failure

- module cannot be found;
- imported dependency fails;
- command unsupported;
- marker missing;
- timeout.

---

## 35. `missing.gfs`

Purpose:

- inspect missing concrete linearizations;
- prove project completeness or accepted scope;
- provide release-gate evidence.

Conceptual structure:

```text
# Missing linearizations for <ENTRYPOINT>

<IMPORT_ENTRYPOINT>

<EMIT_BEGIN missing:missing-functions>
<MISSING_LINEARIZATION_OPERATION>
<EMIT_END missing:missing-functions>

<QUIT>
```

### 35.1 Gold

Recommended:

```text
project/validation/gold/missing.gold
```

### 35.2 Zero-missing expectation

An empty normalized section may mean:

```text
no missing functions
```

This meaning must be documented explicitly.

### 35.3 Accepted omissions

Any accepted missing function must appear in:

- project scope/release criteria;
- status ledger or decision log;
- validation specification.

---

## 36. `linearize.gfs`

Purpose:

- linearize representative abstract trees;
- validate word order, agreement, morphology, punctuation, and constructor behavior.

Conceptual structure:

```text
# Representative linearizations

<IMPORT_ENTRYPOINT>

<EMIT_BEGIN linearize:basic-declaratives>
<LINEARIZE_TREE_1>
<LINEARIZE_TREE_2>
<EMIT_END linearize:basic-declaratives>

<EMIT_BEGIN linearize:agreement>
<LINEARIZE_AGREEMENT_CASES>
<EMIT_END linearize:agreement>

<QUIT>
```

### 36.1 Case selection

Include:

- core categories;
- high-impact constructors;
- agreement branches;
- structural entries;
- project-specific difficult behavior;
- fixed regressions.

### 36.2 Gold

Recommended:

```text
project/validation/gold/linearize.gold
```

---

## 37. `parse.gfs`

Purpose:

- parse representative surface phrases;
- validate expected abstract trees;
- expose ambiguity;
- verify preposition, agreement, word-order, and construction behavior.

Conceptual structure:

```text
# Representative parsing

<IMPORT_ENTRYPOINT>

<EMIT_BEGIN parse:basic-phrases>
<PARSE_PHRASE_1>
<PARSE_PHRASE_2>
<EMIT_END parse:basic-phrases>

<QUIT>
```

### 37.1 Input source

Small stable phrases may be embedded in the script.

Larger corpora belong under:

```text
project/validation/inputs/
```

### 37.2 Gold

Recommended:

```text
project/validation/gold/parse.gold
```

### 37.3 Ambiguity

Accepted ambiguity must be documented.

Do not normalize away parse alternatives merely to make the gold stable.

---

## 38. `generation.gfs`

Purpose:

- exercise bounded grammar generation;
- detect missing or broken constructor paths;
- provide diagnostic coverage.

Conceptual structure:

```text
# Bounded generation

<IMPORT_ENTRYPOINT>

<EMIT_BEGIN generation:small-sample>
<BOUNDED_GENERATION_COMMAND>
<EMIT_END generation:small-sample>

<QUIT>
```

### 38.1 Bounds

Document:

```text
maximum results
maximum depth
target category
seed if applicable
timeout
```

### 38.2 Exact gold

Use exact gold only when deterministic.

Otherwise use assertions.

---

## 39. `morphology.gfs`

Purpose:

- inspect selected lexical forms or paradigms;
- verify form completeness;
- validate irregular and high-risk items.

Conceptual structure:

```text
# Morphology checks

<IMPORT_ENTRYPOINT_OR_MORPHOLOGY_MODULE>

<EMIT_BEGIN morphology:representative-forms>
<MORPHOLOGY_OPERATION>
<EMIT_END morphology:representative-forms>

<QUIT>
```

### 39.1 Scope

Include representative:

- regular paradigms;
- irregular paradigms;
- agreement dimensions;
- orthographic alternations;
- repaired regressions.

### 39.2 Entry module

Loading a lower-level morphology module is acceptable only when the scenario is documented as a focused checkpoint scenario.

Release language behavior should also be exercised through the final entrypoint.

---

# Part II — Project-specific scenario families

## 40. Agreement scenarios

Recommended IDs:

```text
agreement-np
agreement-subject-verb
agreement-adjective
agreement-coordination
```

Each case should identify:

```text
controller
target
dimensions
expected form/order
constructor/rule ID
```

---

## 41. Negation scenarios

Recommended IDs:

```text
negation-basic
negation-nonfinite
negation-questions
```

Cover:

- positive/negative contrast;
- placement;
- tense/aspect interaction;
- constituent negation;
- project-specific negative concord.

---

## 42. Question scenarios

Recommended IDs:

```text
questions-polar
questions-content
questions-embedded
```

Cover:

- direct/embedded distinction;
- subject behavior;
- interrogative form/case;
- word order;
- negation;
- ambiguity.

---

## 43. Relative scenarios

Recommended IDs:

```text
relatives-subject
relatives-object
relatives-oblique
```

Cover:

- relative marker;
- gap/resumptive behavior;
- agreement;
- preposition/case;
- attachment;
- punctuation.

---

## 44. Coordination scenarios

Recommended IDs:

```text
coordination-np
coordination-vp
coordination-sentence
```

Cover:

- two and multiple conjuncts;
- separators;
- conjunction placement;
- agreement resolution;
- category-state preservation.

---

## 45. Complement scenarios

Recommended IDs:

```text
complements-v2
complements-v3
complements-sentential
complements-question
complements-nonfinite
```

Cover:

- valency;
- case/preposition;
- complement order;
- saturation;
- optionality;
- extraction/passive behavior when in scope.

---

## 46. Structural scenarios

Recommended IDs:

```text
structural-pronouns
structural-determiners
structural-prepositions
structural-conjunctions
```

These scenarios should verify that closed-class entries expose complete documented category behavior.

---

## 47. Regression scenarios

A fixed defect may receive a focused scenario.

Recommended name:

```text
regression-<stable-issue-id>
```

The scenario must reference:

- issue/status/decision ID;
- original failing behavior;
- expected corrected behavior;
- broader constructor/feature coverage.

A regression scenario should not duplicate a general scenario indefinitely without rationale.

---

## 48. Smoke scenarios

A smoke scenario is small and fast.

Use for:

- quick mode;
- installation verification;
- entrypoint load;
- one parse/linearization;
- critical release-surface sanity.

A smoke scenario does not replace complete checkpoint/release scenarios.

---

# Part III — Scenario authoring

## 49. One purpose per scenario

A scenario should answer one coherent validation question.

Prefer:

```text
linearize-agreement.gfs
parse-questions.gfs
morphology-irregular.gfs
```

over:

```text
everything.gfs
```

A broad release scenario is acceptable only when section boundaries and review remain clear.

---

## 50. Stable case identity

Every case or coherent group should have a stable identifier.

Recommended conceptual form:

```text
<scenario-id>:<section-id>
```

Case identity should remain stable when expected output changes.

Renaming case IDs may invalidate golds and historical comparisons.

---

## 51. Tree examples

Abstract trees embedded in a scenario should:

- use public constructors;
- remain readable;
- avoid unnecessary implementation detail;
- reference rule/coverage IDs where useful;
- represent the intended project surface.

Do not use a private helper solely because it makes a test easier unless the scenario's purpose is to test that helper.

---

## 52. Phrase examples

Surface phrases should:

- use project orthography;
- be UTF-8;
- avoid hidden whitespace;
- have documented meaning when ambiguous;
- be stable and reviewable;
- avoid sensitive or copyrighted corpora beyond permitted short test data.

---

## 53. Ordering

Command and section order is significant.

Recommended order:

1. load entrypoint;
2. emit setup/identity section if needed;
3. core success cases;
4. edge cases;
5. known accepted limitations;
6. summary assertions;
7. quit.

Do not rely on filesystem order for external inputs unless explicitly sorted by the runner/command.

---

## 54. Error-focused scenarios

A scenario may intentionally provoke a GF or grammar-level failure only when:

- purpose is explicit;
- expected diagnostic is stable enough;
- failure semantics are documented;
- scenario result distinguishes expected failure from runner error;
- release policy defines whether it is required.

Avoid golding complete compiler diagnostics when wording is unstable across GF versions.

Prefer stable diagnostic codes/assertions.

---

## 55. Diagnostic-only scenarios

Diagnostic scenarios may:

- use broader output;
- inspect dependencies;
- inspect operations;
- explore generation;
- include non-release evidence.

They still must:

- terminate;
- remain bounded;
- use safe commands;
- preserve markers;
- avoid project writes.

---

## 56. Comments and metadata

Recommended header comments:

```text
scenario_id
purpose
loaded entrypoint
required/optional
modes
normalization profile
gold path
input files
timeout class
owner
last reviewed
```

These comments are helpful but are not the machine registry unless a future scenario schema explicitly defines them.

---

## 57. Formatting

Use:

- one command per logical line;
- blank lines between sections;
- consistent marker spelling;
- stable indentation;
- no trailing whitespace;
- LF newlines;
- final newline.

Do not format scenarios to depend on terminal wrapping.

---

## 58. Reusable fragments

Schema `1.0` does not define textual include fragments for `.gfs`.

Avoid copy-pasting large command blocks across scenarios.

When duplication becomes significant:

- move behavior into a loaded GF module;
- create a shared validation entrypoint;
- split scenarios;
- propose an explicitly versioned scenario include mechanism.

Do not invent an undocumented preprocessor.

---

# Part IV — Running scenarios

## 59. Run one scenario

Recommended command:

```text
gf-wordbench scenario run <scenario-id>
```

The command should:

- load project configuration;
- resolve GF/RGL paths;
- create one run directory;
- execute GF;
- preserve raw streams;
- validate markers/assertions;
- normalize output;
- compare gold;
- write `ScenarioResult`;
- write reports and manifest when applicable.

---

## 60. Run selected validation mode

```text
gf-wordbench validate --mode quick
gf-wordbench validate --mode checkpoint --checkpoint <id>
gf-wordbench validate --mode diagnostic
gf-wordbench validate --mode release
```

Scenario membership is determined by project validation policy.

---

## 61. Direct GF debugging

A maintainer may run:

```text
gf < scenario.gfs
```

for local debugging.

Such a manual run is not canonical GF Wordbench release evidence because it may lack:

- resolved configuration record;
- timeout;
- raw-stream paths;
- normalization;
- structured assertions;
- manifest;
- toolchain identity.

Use GF Wordbench for recorded validation.

---

## 62. Run output locations

Examples:

```text
run_<run-id>/raw/scenarios/<scenario-id>.stdout.txt
run_<run-id>/raw/scenarios/<scenario-id>.stderr.txt
run_<run-id>/raw/scenarios/<scenario-id>.out
run_<run-id>/raw/scenarios/<scenario-id>.gold.diff
```

Exact recorded paths in `ScenarioResult` are authoritative.

Consumers must not reconstruct them when structured paths exist.

---

# Part V — Validation modes

## 63. Quick mode

Quick mode may run:

- `load`;
- one small smoke scenario;
- a target-related focused scenario.

Requirements:

- bounded;
- fast;
- deterministic;
- no full release claim.

A selected quick scenario failure fails the quick run's scope.

---

## 64. Checkpoint mode

Checkpoint scenarios should align with:

- one configured checkpoint;
- its direct syntax/morphology family;
- associated golds;
- expected downstream impact.

A checkpoint scenario must not silently load a different module from the configured checkpoint/entrypoint policy.

---

## 65. Diagnostic mode

Diagnostic mode may run:

- all optional scenarios;
- broad generation;
- introspection;
- extended morphology;
- focused regressions;
- additional parse/linearization cases.

Diagnostic output remains bounded.

---

## 66. Release mode

Release mode runs every required scenario.

Release requirements:

- scripts exist;
- scripts are registered;
- entrypoints load;
- commands are compatible;
- timeouts are finite;
- required markers complete;
- assertions pass;
- required golds match;
- required artifacts exist;
- no required scenario is skipped;
- scenarios and golds remain unchanged;
- evidence is included in reports/manifest.

---

# Part VI — Scenario changes

## 67. Internal compatible change

Examples:

- comment correction;
- whitespace cleanup;
- clearer local variable/tree formatting;
- added non-output comment.

Required:

- scenario check;
- rerun when executable content might be affected.

---

## 68. Compatible scenario extension

Examples:

- add a new optional section;
- add a new optional scenario;
- add a new assertion;
- add representative cases without changing existing case meaning.

Required:

- registry/specification review;
- normalization/gold review;
- coverage update;
- project minor-change analysis when public project behavior expands.

---

## 69. Breaking scenario change

Examples:

- rename scenario ID;
- change loaded entrypoint;
- remove required section;
- change marker ID;
- change normalization profile;
- reorder semantically ordered output;
- change input meaning/order;
- remove release coverage;
- redefine pass criterion.

Required:

1. decision or migration record;
2. project configuration update;
3. interfile contract update;
4. validation specification update;
5. coverage matrix update;
6. gold rename/review;
7. historical comparison policy review;
8. release-impact review.

---

## 70. Scenario rename checklist

```text
[ ] Scenario filename renamed
[ ] Scenario ID updated
[ ] project.toml updated
[ ] VALIDATION_SPEC.md updated
[ ] Interfile contract updated
[ ] Entry-point map updated
[ ] Input references updated
[ ] Gold filename/metadata updated
[ ] Coverage matrix updated
[ ] CLI/CI references updated
[ ] Migration/decision recorded
[ ] New scenario passes
```

---

## 71. Entrypoint change checklist

```text
[ ] New entrypoint exists
[ ] New entrypoint is configured
[ ] Scenario load command updated
[ ] Dependency map updated
[ ] Interfile lock updated
[ ] Direct entrypoint compile passes
[ ] Missing-function check reviewed
[ ] Scenario output reviewed
[ ] Gold diff reviewed
[ ] PGF/release impact reviewed
```

---

## 72. Input change checklist

```text
[ ] Input encoding unchanged or documented
[ ] Record/line meaning remains compatible
[ ] Scenario reference updated
[ ] Input ordering reviewed
[ ] Raw output reviewed
[ ] Normalized output reviewed
[ ] Gold updated explicitly if intended
[ ] Coverage matrix updated
```

---

## 73. GF/RGL migration checklist

```text
[ ] New GF version compatibility verified
[ ] RGL identity recorded
[ ] Scenario commands still supported
[ ] Entry points load
[ ] Marker output still emitted
[ ] Unsupported-command diagnostics checked
[ ] Raw stdout/stderr reviewed
[ ] Normalization reviewed
[ ] Gold diffs reviewed
[ ] Required scenarios pass
[ ] Decision/release notes updated
```

---

# Part VII — Diagnostics

## 74. Recommended diagnostic codes

```text
SCENARIO_NOT_REGISTERED
SCENARIO_FILE_MISSING
SCENARIO_PATH_OUTSIDE_ROOT
SCENARIO_FILE_UNREADABLE
SCENARIO_ENCODING_INVALID
SCENARIO_ENTRYPOINT_UNDOCUMENTED
SCENARIO_ENTRYPOINT_LOAD_FAILED
SCENARIO_COMMAND_UNSUPPORTED
SCENARIO_LAUNCH_FAILED
SCENARIO_TIMEOUT
SCENARIO_CANCELLED
SCENARIO_MARKER_DUPLICATE
SCENARIO_BEGIN_MARKER_MISSING
SCENARIO_END_MARKER_MISSING
SCENARIO_SECTION_INCOMPLETE
SCENARIO_ASSERTION_FAILED
SCENARIO_OUTPUT_NORMALIZATION_FAILED
SCENARIO_GOLD_MISSING
SCENARIO_GOLD_MISMATCH
SCENARIO_INPUT_MISSING
SCENARIO_INPUT_INVALID
SCENARIO_OUTPUT_LIMIT_EXCEEDED
SCENARIO_SHELL_ESCAPE_FORBIDDEN
SCENARIO_QUIT_MISSING
SCENARIO_ARTIFACT_MISSING
```

---

## 75. Common failure patterns

### GF returns zero but marker is missing

Result:

```text
FAIL or ERROR according to marker contract
```

Never `OK`.

### Script loads a lower-level module

Result:

```text
project/scenario contract failure
```

unless explicitly documented.

### Gold mismatch

Result:

```text
FAIL
```

Do not update gold automatically.

### GF executable missing

Result:

```text
ERROR
error_kind = TOOL
```

### Timeout

Result:

```text
ERROR
execution_state = timed_out
```

### Optional scenario not selected

Result:

```text
SKIPPED
```

### Required scenario absent

Result:

```text
ERROR
error_kind = CONFIG
```

---

## 76. Drift indicators

Scenario drift is likely when:

- a required scenario has no script;
- an unregistered script is treated as release evidence;
- a scenario loads a renamed module;
- a scenario uses an undocumented local path;
- commands work only on one developer's GF version;
- a begin marker lacks an end marker;
- scenario IDs and filenames differ without variant policy;
- output passes only because an unsupported command was ignored;
- generation is unbounded;
- external input changed without gold review;
- normal validation rewrites gold;
- a scenario omits explicit termination where required;
- source behavior changed but scenario coverage did not;
- release entrypoint changed without scenario review;
- project configuration and scenario registry disagree.

Resolve drift by restoring the existing contract or changing it deliberately.

---

# Part VIII — Testing and anti-drift

## 77. Scenario contract tests

Recommended tests:

```text
tests/scenarios/test_scenario_registry.py
tests/scenarios/test_scenario_loader.py
tests/scenarios/test_scenario_runner.py
tests/scenarios/test_scenario_markers.py
tests/scenarios/test_scenario_assertions.py
tests/scenarios/test_scenario_normalization.py
tests/scenarios/test_scenario_security.py
tests/contracts/test_project_scenario_contract.py
tests/integration/test_real_gf_scenarios.py
```

---

## 78. Required unit cases

- registered scenario;
- unregistered scenario;
- missing required script;
- optional scenario missing;
- invalid encoding;
- unsafe path;
- duplicate scenario ID;
- required/optional overlap;
- deterministic ordering;
- unique markers;
- missing begin;
- missing end;
- nested/overlapping markers;
- unsupported command evidence;
- explicit quit;
- timeout;
- cancellation;
- raw stream preservation;
- normalization failure;
- gold mismatch;
- no gold comparison;
- input missing;
- output-size limit.

---

## 79. Real-GF integration cases

Use a language-neutral or active-project fixture to prove:

- entrypoint load;
- one linearization;
- one parse where supported;
- missing-function operation;
- marker emission;
- explicit termination;
- timeout behavior;
- stdout/stderr capture;
- normalized output;
- gold comparison.

Real-GF tests must use an explicit GF/RGL environment.

They must not depend on a developer's global `GF_LIB_PATH`.

---

## 80. Automated project checks

Recommended command:

```text
gf-wordbench scenario check
```

It should verify:

1. registry uniqueness;
2. required/optional separation;
3. script existence;
4. filename/ID agreement;
5. UTF-8;
6. final newline;
7. path containment;
8. marker balance;
9. documented entrypoint;
10. input existence;
11. gold mapping;
12. normalization profile;
13. prohibited shell escape patterns;
14. explicit termination where required;
15. mode membership;
16. no stale language suffix;
17. no unregistered required scenario.

Strict mode may inspect GF command compatibility through safe probes.

---

# Part IX — Authoring templates

## 81. Scenario registry entry template

```markdown
### <SCENARIO_ID> — <title>

**Script:** `project/validation/scenarios/<SCENARIO_ID>.gfs`  
**Status:** Active | Deprecated | Retired  
**Required:** yes | no  
**Modes:** quick | checkpoint | diagnostic | release  
**Owner:** <OWNER>  
**Loaded entrypoint:** `<ENTRYPOINT>`  
**Purpose:** <PURPOSE>  
**Inputs:** <FILES OR NONE>  
**Normalization profile:** <PROFILE>  
**Gold:** `project/validation/gold/<SCENARIO_ID>.gold` | none  
**Timeout class:** <CLASS>  
**Output bound:** <BOUND>  
**Required sections:**
- `<SECTION_ID>`

**Assertions:**
- `<ASSERTION_ID>` — <CRITERION>

**Coverage:**
- project rules/contracts: <IDS>
- modules: <MODULES>
- release criteria: <IDS>

**Last reviewed:** `<YYYY-MM-DD>`
```

---

## 82. Generic `.gfs` template

The exact marker-emission command must be replaced with syntax supported by the selected GF version.

```text
-- Scenario: <SCENARIO_ID>
-- Purpose: <PURPOSE>
-- Entrypoint: <ENTRYPOINT>
-- Required: <YES/NO>
-- Normalization: <PROFILE>/<VERSION>
-- Gold: <PATH OR NONE>

<IMPORT_OR_LOAD_ENTRYPOINT>

<EMIT_TEXT "GF_WORDBENCH_BEGIN <SCENARIO_ID>:<SECTION_ID>">

<BOUNDED_GF_COMMANDS>

<EMIT_TEXT "GF_WORDBENCH_END <SCENARIO_ID>:<SECTION_ID>">

<QUIT_COMMAND>
```

Do not leave angle-bracket placeholders in active scenario files.

---

## 83. Linearization scenario template

```text
-- Scenario: <SCENARIO_ID>
-- Purpose: Validate representative linearizations.

<IMPORT_ENTRYPOINT>

<BEGIN_MARKER basic>
<LINEARIZE REPRESENTATIVE_TREE_1>
<LINEARIZE REPRESENTATIVE_TREE_2>
<END_MARKER basic>

<BEGIN_MARKER edge-cases>
<LINEARIZE EDGE_CASE_TREE_1>
<END_MARKER edge-cases>

<QUIT>
```

---

## 84. Parse scenario template

```text
-- Scenario: <SCENARIO_ID>
-- Purpose: Validate representative parsing.

<IMPORT_ENTRYPOINT>

<BEGIN_MARKER basic>
<PARSE REPRESENTATIVE_PHRASE_1>
<PARSE REPRESENTATIVE_PHRASE_2>
<END_MARKER basic>

<QUIT>
```

---

## 85. Missing-function template

```text
-- Scenario: missing
-- Purpose: Detect missing linearizations.

<IMPORT_ENTRYPOINT>

<BEGIN_MARKER missing-functions>
<PRINT_MISSING_LINEARIZATIONS>
<END_MARKER missing-functions>

<QUIT>
```

---

## 86. Bounded generation template

```text
-- Scenario: <SCENARIO_ID>
-- Purpose: Bounded generation diagnostic.

<IMPORT_ENTRYPOINT>

<BEGIN_MARKER generated-sample>
<GENERATE WITH EXPLICIT CATEGORY, DEPTH, AND COUNT BOUNDS>
<END_MARKER generated-sample>

<QUIT>
```

---

# Part X — Review checklists

## 87. New scenario checklist

```text
[ ] Scenario ID is unique
[ ] Filename matches ID
[ ] Purpose is documented
[ ] Required/optional status is set
[ ] Modes are set
[ ] Entrypoint is documented
[ ] Entrypoint exists
[ ] Commands are GF-version compatible
[ ] Input files are documented
[ ] Output is bounded
[ ] Marker IDs are unique
[ ] Every begin has an end
[ ] Assertions are explicit
[ ] Normalization profile is selected
[ ] Gold mapping is explicit
[ ] Explicit quit is present where required
[ ] Security review passes
[ ] Scenario is in project.toml
[ ] VALIDATION_SPEC.md is updated
[ ] TEST_COVERAGE_MATRIX.md is updated
[ ] Interfile contract is updated
[ ] Scenario runs through GF Wordbench
```

---

## 88. Scenario modification checklist

```text
[ ] Purpose remains unchanged or specification updated
[ ] Entrypoint remains correct
[ ] Commands remain supported
[ ] Input compatibility reviewed
[ ] Marker IDs reviewed
[ ] Assertion semantics reviewed
[ ] Raw stdout reviewed
[ ] Raw stderr reviewed
[ ] Normalized output reviewed
[ ] Gold diff reviewed
[ ] Coverage updated
[ ] Release impact reviewed
[ ] Decision/status records updated when needed
```

---

## 89. Release checklist

```text
[ ] All required scenarios are registered
[ ] All required scripts exist
[ ] No unresolved template placeholders remain
[ ] Every scenario loads a documented entrypoint
[ ] All commands are supported by certified GF
[ ] Every scenario has a finite timeout
[ ] Every output-producing operation is bounded
[ ] Required markers complete
[ ] Assertions pass
[ ] Required golds exist
[ ] Required golds match
[ ] No scenario or gold changed during validation
[ ] Raw evidence is preserved
[ ] Scenario results are in summary.json
[ ] Scenario artifacts are in manifest.json
[ ] No required scenario is skipped
```

---

## 90. Directory checklist

```text
[ ] README.md is current
[ ] Only .gfs files and README.md are present
[ ] No backup/copy/temp files exist
[ ] Filenames follow ID rules
[ ] Files are UTF-8 without BOM
[ ] Files use LF
[ ] Files end with newline
[ ] No shell escapes exist
[ ] No secrets exist
[ ] No unregistered required script exists
[ ] No stale old-language module name exists
```

---

# Part XI — Project completion record

## 91. Active scenario inventory

Replace this table during initialization.

| Scenario ID | Required | Modes | Entrypoint | Inputs | Gold | Status | Last verified run |
|---|---:|---|---|---|---|---|---|
| `<id>` | `<yes/no>` | `<modes>` | `<module>` | `<inputs>` | `<gold>` | `<Active/Deprecated/Retired>` | `<run-id>` |

---

## 92. Coverage summary

| Feature/contract | Scenario IDs | Assertion/gold | Coverage status |
|---|---|---|---|
| Grammar load | `load` | marker/assertion | `<complete/gap>` |
| Missing functions | `missing` | gold/count assertion | `<complete/gap>` |
| Linearization | `linearize` | gold | `<complete/gap>` |
| Parsing | `parse` | gold/assertions | `<complete/gap/out-of-scope>` |
| Generation | `generation` | bounded assertions | `<complete/gap/out-of-scope>` |
| Morphology | `<ids>` | `<method>` | `<status>` |
| Agreement | `<ids>` | `<method>` | `<status>` |
| Questions | `<ids>` | `<method>` | `<status>` |
| Relatives | `<ids>` | `<method>` | `<status>` |
| Coordination | `<ids>` | `<method>` | `<status>` |

This table must agree with `TEST_COVERAGE_MATRIX.md`.

---

## 93. Known scenario limitations

| Limitation ID | Scenario(s) | Description | Release impact | Owner | Exit condition |
|---|---|---|---|---|---|
| `<STATUS_ID>` | `<ids>` | `<description>` | `<blocking/non-blocking>` | `<owner>` | `<condition>` |

Blocking limitations belong in `STATUS_LEDGER.md` or `KNOWN_ISSUES.md`.

---

## 94. Change history

| Contract version | Date | Change | Decision/migration | Reviewer |
|---|---|---|---|---|
| `1.0.0` | `<YYYY-MM-DD>` | Initial scenario registry and rules | `<DECISION_OR_NONE>` | `<REVIEWER>` |

---

## 95. Final enforcement rule

A scenario is executable project evidence, not an informal transcript.

It must be registered, deterministic, bounded, safe, entrypoint-correct, marker-complete, and independently reviewable.

> Required scenario success depends on GF execution, expected marker completion, assertion results, normalized output, and required gold comparison—not on process exit code alone.

Normal validation may read and execute scenario files. It must never rewrite them or their gold expectations.
