# GF Wordbench — Albanian Project Validation Assets

**Document ID:** `GF-WB-PROJECT-VALIDATION-README`  
**Status:** Normative operational guide  
**Applies to:** Active Albanian GF project (`sqi`, module suffix `Sqi`)  
**Directory:** `project/validation/`  
**Owner:** Active project maintainers  
**Validation asset contract version:** `1.0.0`  
**Last structural review:** 2026-07-22

---

## 1. Purpose

This directory contains the version-controlled validation assets for the active Albanian GF project.

It defines the project-owned inputs to GF Wordbench validation:

```text
project/validation/
├── README.md
├── scenarios/
│   ├── README.md
│   └── *.gfs
├── inputs/
│   ├── README.md
│   └── <reviewed input assets>
└── gold/
    ├── README.md
    └── *.gold
```

These assets describe what the project expects GF to execute, what stable data it consumes, and which normalized outputs have been reviewed and accepted.

This directory does not contain generated run evidence.

Generated evidence belongs in the run directory managed by GF Wordbench.

The central rule is:

> Project validation assets are reviewed source assets; run logs, normalized outputs, diffs, reports, and generated GF artifacts are immutable run evidence and must remain outside `project/validation/`.

---

## 2. Active project context

| Field | Current project value |
|---|---|
| Language | Albanian |
| Project/language code | `sqi` |
| GF suffix | `Sqi` |
| Current source directory | `lib/src/albanian` |
| Main configured entrypoints | `GrammarSqi.gf`, `SyntaxSqi.gf` |
| Configured checkpoints | `MorphoSqi.gf`, `NounSqi.gf`, `VerbSqi.gf`, `ExtendSqi.gf`, `StructuralSqi.gf` |
| Required scenario families | `load`, `missing`, `linearize`, `parse` |
| Optional scenario families | `generation`, `morphology` |
| Release PGF requirement | Required |
| Configuration authority | `project/project.toml` |

The exact active configuration is always read from:

```text
project/project.toml
```

This README describes the directory contract.

It must not become a second scenario registry.

---

## 3. Authority boundaries

### 3.1 GF is authoritative for

- module loading;
- GF syntax;
- GF typing and unification;
- imports;
- linearization;
- parsing;
- generation;
- morphology commands;
- missing-linearization inspection;
- PGF construction;
- GF process output.

### 3.2 GF Wordbench is authoritative for

- loading the project scenario registry;
- selecting scenarios by validation mode;
- launching GF with finite timeouts;
- preserving stdout and stderr separately;
- interpreting GF Wordbench markers;
- evaluating configured assertions;
- normalizing output;
- comparing normalized output with gold;
- preserving evidence;
- assigning statuses;
- generating summaries and manifests.

### 3.3 The active project is authoritative for

- required and optional scenario IDs;
- scenario purpose;
- target entrypoints;
- reviewed `.gfs` files;
- reviewed input files;
- reviewed gold expectations;
- release requiredness;
- project-specific linguistic acceptance criteria;
- project-specific manual review requirements.

### 3.4 No duplicated authority

This directory must not:

- reimplement GF parsing;
- define a second project configuration;
- infer required scenarios from filenames alone;
- infer entrypoints from script text alone;
- redefine normalization independently;
- define a second marker protocol;
- define report schemas;
- contain machine-local GF or RGL paths.

---

## 4. Related normative documents

Framework-level references:

```text
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
docs/validation/SCENARIO_VALIDATION.md
docs/validation/REGRESSION_COMPARISON.md
docs/validation/RELEASE_GATES.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
docs/PERSISTED_SCHEMA_LOCK.md
```

Project-level references:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA.md
```

When this README overlaps a specialized document, the specialized document owns the detailed rule.

---

## 5. Directory ownership

| Path | Owner | Purpose | Normal validation may modify it |
|---|---|---|---:|
| `project/validation/README.md` | project maintainers | directory contract | No |
| `project/validation/scenarios/` | project maintainers | native GF scripts | No |
| `project/validation/inputs/` | project maintainers | reviewed scenario data | No |
| `project/validation/gold/` | project maintainers | reviewed normalized expectations | No |
| run `raw/scenarios/` | scenario runner | raw process evidence | Yes, in new run only |
| run normalized outputs | normalizer | comparison evidence | Yes, in new run only |
| run gold diffs | gold comparator | mismatch evidence | Yes, in new run only |
| run reports | report writers | derived presentation | Yes, in new run only |
| run manifest | manifest writer | artifact inventory | Yes, in new run only |

A normal validation run is read-only with respect to the project-owned rows.

---

## 6. Canonical validation modes

GF Wordbench uses four canonical modes:

```text
quick
checkpoint
release
diagnostic
```

Legacy aliases may be accepted only during migration:

```text
file → quick
all  → diagnostic
```

New project assets and reports use only canonical names.

---

## 7. Mode intent

### 7.1 `quick`

Purpose:

- fast feedback for one touched module or a narrow target;
- direct compile evidence;
- nearest affected checks;
- bounded scenario subset.

Typical project validation assets:

- load smoke section;
- family-specific linearization or morphology section;
- exact helper/constructor regression associated with the changed area.

`quick` must not be described as release proof.

---

### 7.2 `checkpoint`

Purpose:

- validate one coherent Albanian development layer;
- compile the checkpoint and direct consumers;
- run scenarios assigned to that layer;
- detect downstream entrypoint effects.

Current configured checkpoint families include:

```text
MorphoSqi
NounSqi
VerbSqi
ExtendSqi
StructuralSqi
```

The exact mapping from checkpoint to scenarios belongs to `project/docs/VALIDATION_SPEC.md`.

---

### 7.3 `release`

Purpose:

- validate the complete declared release scope;
- execute all required scenarios;
- compare every required gold;
- build and verify the required PGF;
- evaluate all release gates.

A required scenario skipped in release mode prevents overall `OK`.

---

### 7.4 `diagnostic`

Purpose:

- collect broad evidence;
- exercise optional scenarios;
- inspect warning clusters;
- investigate ambiguous or downstream failures;
- compare with previous compatible runs.

Diagnostic mode is not permitted to mutate gold.

---

## 8. Project scenario registry

The authoritative scenario registry is:

```text
project/project.toml
```

The current canonical configuration declares these families:

```toml
[validation]
required_scenarios = [
  "load",
  "missing",
  "linearize",
  "parse",
]

optional_scenarios = [
  "generation",
  "morphology",
]

release_requires_pgf = true
```

This README records their intended roles.

The exact script path, target entrypoint, marker policy, assertions, timeout, modes, normalization version, and gold path must be defined through the supported project configuration contract.

---

## 9. Required scenario families

### 9.1 `load`

Purpose:

- prove that the intended final entrypoint loads in GF;
- detect missing imports, incompatible modules, and unresolved generated objects;
- verify the scenario does not load a lower-level substitute.

Minimum expectations:

```text
GF process starts
configured entrypoint is loaded
process completes within timeout
no fatal diagnostic
required completion section closes
```

Recommended target:

```text
the final grammar or syntax entrypoint declared by project.toml
```

A successful load of only `MorphoSqi`, `NounSqi`, or another checkpoint is not equivalent to final-entrypoint load success.

---

### 9.2 `missing`

Purpose:

- inspect missing linearizations or equivalent completeness evidence;
- detect defaulted, absent, or unresolved concrete functions;
- provide release evidence for the intended entrypoint.

Minimum expectations:

```text
target entrypoint loads
missing-function command executes
output section completes
fatal diagnostics are absent
accepted missing inventory matches project release policy
```

A zero process exit does not override a missing required section.

The accepted missing inventory, when non-empty, must be documented in:

```text
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA.md
```

---

### 9.3 `linearize`

Purpose:

- exercise representative Albanian abstract trees;
- verify surface realization;
- cover high-risk category boundaries;
- provide reviewed gold evidence where output is deterministic.

Minimum coverage should include:

```text
noun and determiner agreement
AP and CN agreement
NP case realization
pronoun realization
preposition plus NP
verb and complement behavior
sentence realization
question realization
relative realization
coordination
structural closed-class items
```

The exact accepted trees and outputs belong to the scenario and gold assets.

---

### 9.4 `parse`

Purpose:

- verify that accepted Albanian strings parse through the intended grammar;
- preserve ambiguity evidence;
- detect regressions in lexical, morphological, and syntactic coverage.

Minimum expectations:

```text
entrypoint loads
registered inputs execute
required parse sections complete
accepted inputs produce required parse behavior
ambiguity is preserved rather than normalized away
gold comparison passes when required
```

A parse scenario must not declare one arbitrary parse as correct merely because multiple parses exist.

Project policy must state whether each input requires:

- at least one parse;
- a specific tree;
- a bounded accepted set;
- no parse;
- manual ambiguity review.

---

## 10. Optional scenario families

### 10.1 `generation`

Purpose:

- exercise bounded generation;
- detect missing linearizations across a selected abstract subset;
- provide diagnostic coverage beyond fixed examples.

Requirements:

- generation must be bounded;
- ordering must be deterministic or normalized safely;
- unbounded combinatorial generation is prohibited;
- generated output must not automatically become gold;
- truncation must be explicit.

Generation becomes release-required only through project configuration and release criteria.

---

### 10.2 `morphology`

Purpose:

- inspect Albanian inflection tables and paradigm behavior;
- validate representative nominal, adjectival, verbal, pronominal, and closed-class forms.

Recommended dimensions:

```text
Species
Case
Gender
Number
Person
Tense
clitic behavior
irregular paradigms
defective paradigms
```

Morphology output is linguistically meaningful and must not be normalized away.

---

## 11. Albanian high-risk validation families

The project’s validation assets must cover the structural risks documented in the category, syntax, status, and test specifications.

### 11.1 Rich-category preservation

Cover:

```text
CN
NP
Pron
AP
lexical verb categories
ListNP
ListCN
ListAP
Digits
Decimal
```

Required assertions:

- full target category remains constructible;
- expected table dimensions are exercised;
- no one-cell reconstruction is presented as the full category;
- agreement, gender, case, clitics, or complement slots are not silently lost.

---

### 11.2 AP/CN/predicate conversion

Cover relevant functions such as:

```text
ICompAP
PredAPVP
AdjAsCN
AdjAsNP
CompoundAP
CompBareCN
CompIQuant
AdvIsNPAP
```

Validation must detect:

- `A` versus `AP` helper mismatch;
- early AP flattening;
- early CN flattening;
- invalid rich-to-rich reconstruction;
- unexplained lock warnings.

---

### 11.3 Existential constructions

Cover the active existential family where implemented, including functions such as:

```text
ExistS
ExistNPQS
ExistIPQS
ExistsNP
ExistCN
ExistMassCN
ExistPluralCN
```

Validation must check:

- coherent family construction;
- intended clause or question path;
- agreement behavior;
- absence of unsupported string-only shortcuts.

Only functions actually present in the active source and scope belong in executable scenarios.

---

### 11.4 Reflexive noun-phrase family

Cover the active RNP family where implemented, including:

```text
ReflPron
ReflPoss
PredetRNP
AdvRNP
AdvRVP
AdvRAP
ReflA2RNP
PossPronRNP
ConjRNP
Base_rr_RNP
Base_nr_RNP
Base_rn_RNP
Cons_rr_RNP
Cons_nr_RNP
Cons_rn_RNP
```

Validation must check:

- coherent `NP`/`ListNP` strategy;
- rich list preservation;
- no member left on a different representation;
- no ad hoc shallow list replacement.

---

### 11.5 Prepositional government

Cover:

```text
PrepNP
PrepCN
AdvRNP
AdvRVP
AdvRAP
relevant structural prepositions
```

Current project contract expects the established Albanian post-preposition case behavior where applicable.

Validation must detect:

- invented local case policies;
- disagreement between local and structural export paths;
- expanded `lock_Prep` warning clusters;
- bypass of approved preposition producers.

---

### 11.6 Focus/AP helper discipline

Cover:

```text
FocusAP
AP-surface helpers used by Utt-returning functions
exact A versus AP compatibility
```

A shallow `Utt` target may use surface realization only through an exact `AP`-compatible helper or extractor.

Family resemblance is not sufficient.

---

### 11.7 Structural closed-class constructors

Cover:

```text
both7and_DConj
either7or_DConj
StructuralSqiClause
StructuralSqi
other touched structural shallow categories
```

Validation must prove constructor availability in the actual module context.

The visible lincat `{s : Str}` is not proof that arbitrary local construction is accepted.

---

### 11.8 Downstream importer cleanliness

Every targeted repair must distinguish:

- first failing provider;
- direct consumer failures;
- downstream façade failures;
- ambiguous attribution.

A scenario report must not present `GrammarSqi`, `SyntaxSqi`, `StructuralSqi`, or `ExtendSqi` as the root merely because those aggregators fail after a lower module.

---

### 11.9 Comment-versus-code discipline

When a touched source contains explanatory comments, validation review must confirm that the comments still agree with:

- current code;
- current lincat provider;
- current GF compile behavior;
- current constructor availability.

A stale comment must be corrected or registered.

---

## 12. Scenario files

Scenario scripts live under:

```text
project/validation/scenarios/
```

Canonical extension:

```text
.gfs
```

Recommended path:

```text
project/validation/scenarios/<scenario-id>.gfs
```

Examples:

```text
load.gfs
missing.gfs
linearize.gfs
parse.gfs
generation.gfs
morphology.gfs
```

These names are illustrative only when the matching IDs are registered.

An unregistered `.gfs` file is not release evidence.

---

## 13. Native GF script rule

A scenario is a native GF script.

GF Wordbench must not reinterpret GF command syntax.

Python may:

- select the script;
- launch GF;
- capture streams;
- detect GF Wordbench markers;
- evaluate external assertions;
- normalize output;
- compare gold.

Python must not:

- reproduce the GF shell;
- translate custom project commands into GF commands;
- implement an alternate parser;
- fabricate successful GF output.

---

## 14. Scenario identity

Each scenario has a stable lowercase ASCII identifier.

Recommended grammar:

```text
[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*
```

Valid examples:

```text
load
parse
linearize-basic
morphology.nouns
structural_dconj
```

Invalid examples:

```text
Parse
parse basic
parse:basic
-parse
parse/
parse é
```

Scenario IDs must not be reused for a different purpose after retirement.

Renaming a scenario requires coordinated changes to:

- project configuration;
- script filename;
- marker lines;
- assertion configuration;
- input mapping;
- gold filename and header;
- validation specification;
- coverage matrix;
- historical comparison policy.

---

## 15. Marker protocol

The canonical marker protocol is:

```text
GF Wordbench Scenario Marker Protocol 1.0
```

Begin marker:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
```

End marker:

```text
GF_WORDBENCH_END <scenario-id>:<section-id>
```

Example:

```text
GF_WORDBENCH_BEGIN parse:basic-np
<GF command output>
GF_WORDBENCH_END parse:basic-np
```

Markers are recognized only as exact complete stdout lines.

The reserved prefix is:

```text
GF_WORDBENCH_
```

Project output must not use that prefix for ordinary linguistic text.

---

## 16. Marker invariants

```text
MARK-001 Scenario ID matches the registered scenario.
MARK-002 Section ID is registered and stable.
MARK-003 Every begin marker has one matching end marker.
MARK-004 No end marker appears without a begin marker.
MARK-005 Sections do not nest.
MARK-006 Sections do not overlap.
MARK-007 Duplicate sections are prohibited unless protocol explicitly permits them.
MARK-008 Required sections appear in declared order.
MARK-009 All open sections close before process termination.
MARK-010 Marker identity survives normalization.
MARK-011 stderr is not treated as marker control stream.
MARK-012 An unknown reserved marker is a protocol error.
```

A zero GF exit with a missing required end marker is not scenario success.

---

## 17. Section design

A section should represent one stable validation contract.

Good section boundaries:

```text
one module-load proof
one missing-function inventory
one parse input family
one linearization family
one morphology paradigm
one structural constructor family
one artifact inspection
```

Avoid:

- one marker pair around an entire unbounded transcript;
- sections whose meaning changes with test ordering;
- dynamic section IDs generated from GF output;
- localized section IDs;
- duplicate sections for unrelated purposes;
- sections that include unstable environment banners without need.

---

## 18. Assertions

Scenario success is not equivalent to process success.

Every required scenario must have an explicit assertion strategy.

Built-in assertion families may include:

```text
marker_present
section_completed
section_empty
section_nonempty
contains
not_contains
equals
line_count
occurrence_count
exit_code_in
no_fatal_diagnostic
gold_match
artifact_exists
artifact_nonempty
metric_compare
```

The exact supported assertion vocabulary is owned by:

```text
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
```

Unknown assertion types must produce `ERROR`, not pass.

---

## 19. Automatic system assertions

GF Wordbench should evaluate system conditions independently of project assertions:

```text
process started
process completed
allowed exit code
marker protocol valid
required sections complete
no fatal diagnostic
required gold matched
required artifacts exist
```

Project configuration must not disable or redefine these system assertions silently.

---

## 20. Assertion requiredness

An assertion is:

```text
required
```

or:

```text
advisory
```

Required assertion failure affects scenario status.

Advisory assertion failure remains visible but affects release only when project policy says so.

A release-critical condition must not be labeled advisory merely to permit release.

---

## 21. Scenario statuses

Canonical statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

### `OK`

All required execution, protocol, assertion, gold, and artifact conditions passed.

### `FAIL`

The scenario executed sufficiently to evaluate a required project condition, and that condition failed.

Examples:

- required assertion false;
- missing required section;
- gold mismatch;
- required expected linguistic output absent.

### `ERROR`

The scenario could not be executed or interpreted reliably.

Examples:

- launch failure;
- timeout;
- malformed marker protocol;
- unknown assertion type;
- unreadable input;
- normalization failure.

### `SKIPPED`

The scenario was intentionally not executed under explicit mode policy.

A required release scenario skipped unexpectedly prevents release `OK`.

---

## 22. Input files

Reviewed external input files live under:

```text
project/validation/inputs/
```

Inputs may include:

- Albanian strings for parsing;
- abstract trees for linearization;
- lexical inventories;
- morphology lemmas;
- bounded generation seeds;
- expected negative cases;
- reviewed ambiguity cases.

An input file must have documented:

```text
owner
scenario ID
format
encoding
record or line semantics
ordering semantics
stability
version compatibility
empty-line policy
comment syntax when any
```

---

## 23. Input naming

Recommended form:

```text
<scenario-id>.<purpose>.<extension>
```

Examples:

```text
parse.basic.txt
parse.negative.txt
linearize.trees.txt
morphology.nouns.txt
morphology.verbs.txt
generation.seeds.txt
```

A file may be shared only when:

- ownership is explicit;
- every consumer is documented;
- ordering semantics are compatible;
- one scenario cannot modify it for another.

---

## 24. Input encoding

Canonical text encoding:

```text
UTF-8
```

Requirements:

- no hidden locale dependency;
- Albanian diacritics are preserved;
- line endings are normalized only according to the input contract;
- a byte-order mark is prohibited unless explicitly supported;
- decode errors produce `ERROR`;
- normal validation never rewrites the input.

---

## 25. Input ordering

Input order is either:

```text
significant
```

or:

```text
insignificant
```

The owner must state which.

If significant:

- reordering is a contract change;
- output and gold may change;
- diffs require review.

If insignificant:

- the runner or scenario may sort only through an explicit deterministic rule;
- the original file remains unchanged.

---

## 26. Negative inputs

Negative inputs are valid when the scenario purpose explicitly expects:

- no parse;
- rejected constructor;
- fatal diagnostic;
- missing artifact;
- assertion failure in a framework fixture.

A project release scenario must not pass merely because a positive input failed in the same way as a negative test.

Negative cases require explicit identity and expectation.

---

## 27. Gold files

Reviewed gold files live under:

```text
project/validation/gold/
```

Recommended path:

```text
project/validation/gold/<scenario-id>.gold
```

A gold file is accepted normalized output.

It is not:

- raw stdout;
- raw stderr;
- a complete run log;
- an automatic snapshot;
- proof of linguistic correctness without review;
- a substitute for assertions.

---

## 28. Gold schema

Canonical gold schema:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: <scenario-id>
# normalization_version: <version>
--- BEGIN <section-id> ---
<expected normalized GF output>
--- END <section-id> ---
```

Example:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: parse
# normalization_version: 1.0
--- BEGIN basic-np ---
<reviewed normalized parse output>
--- END basic-np ---
```

The scenario ID, filename, registry, and header must agree.

---

## 29. Gold invariants

```text
GOLD-001 Gold is version controlled.
GOLD-002 Gold is scenario-specific.
GOLD-003 Gold uses the registered scenario ID.
GOLD-004 Gold records the normalization version.
GOLD-005 Gold section IDs match registered scenario sections.
GOLD-006 Normal validation is read-only.
GOLD-007 Missing required gold is a failure.
GOLD-008 Empty gold requires explicit documentation.
GOLD-009 Linguistically meaningful output is preserved.
GOLD-010 Unstable noise may be normalized only by approved rules.
GOLD-011 Gold updates are explicit and reviewed.
GOLD-012 Gold is never updated merely to remove a failure.
```

---

## 30. Output normalization

Normalization occurs after raw capture and marker parsing according to the normalization contract.

Allowed stabilization may include:

```text
line-ending normalization
approved ANSI removal
approved path-token replacement
approved timing-token replacement
known non-semantic GF banner handling
```

Current recognized conceptual path tokens include:

```text
<PROJECT_ROOT>
<RGL_ROOT>
<RUN_DIR>
<GF_EXECUTABLE>
<DURATION_MS>
```

Normalization must not remove or rewrite:

- Albanian linguistic strings;
- abstract trees;
- case/gender/number evidence;
- ambiguity evidence;
- missing-function lists;
- morphology tables;
- fatal diagnostics;
- marker identity;
- meaningful ordering.

---

## 31. Raw versus normalized evidence

For each executed scenario, GF Wordbench should preserve:

```text
raw stdout
raw stderr
execution metadata
parsed marker sections
normalized output
assertion results
gold comparison result
gold diff when mismatched
produced artifact checks
```

Raw evidence is immutable.

Normalized output is derived evidence.

Gold is a reviewed source asset.

These three layers must never be confused.

---

## 32. Gold comparison

Gold comparison occurs only after:

1. process evidence is captured;
2. marker protocol is validated;
3. required sections complete;
4. output is normalized with the declared version;
5. gold schema and identity are validated.

Comparison must not pass when:

- the process timed out;
- a required section is incomplete;
- normalization failed;
- gold is missing;
- gold version is incompatible;
- output was truncated in a way that affects comparison.

---

## 33. Gold update workflow

Gold update is a separate explicit maintenance operation.

The exact command is owned by:

```text
docs/usage/CLI_REFERENCE.md
```

A valid update requires:

1. intentional source/specification change;
2. current scenario execution;
3. preserved old raw evidence;
4. preserved new raw evidence;
5. old/new normalized diff;
6. linguistic or architectural review;
7. confirmation that scenario purpose is unchanged or intentionally updated;
8. normalization review;
9. `VALIDATION_SPEC.md` review;
10. decision-log update when significant;
11. contract-lock update when the accepted contract changed;
12. atomic write;
13. follow-up validation.

A gold updater must never run implicitly during ordinary validation.

---

## 34. Generated run evidence

Generated evidence must not be written under:

```text
project/validation/
```

It belongs in a run directory conceptually containing:

```text
run_<id>/
├── raw/
│   ├── compile/
│   └── scenarios/
├── normalized/
├── diffs/
├── artifacts/
├── summary.json
├── summary.md
├── AI_READY.md
└── manifest.json
```

The exact layout is owned by the run-directory and persisted-schema contracts.

Do not copy a generated `.out`, `.stdout.txt`, `.stderr.txt`, or `.diff` file into `gold/` without explicit normalization and review.

---

## 35. Scenario execution lifecycle

For each selected scenario:

```text
1. Resolve registered scenario
2. Validate script path and containment
3. Validate input and gold mappings
4. Resolve intended entrypoint
5. Prepare unique raw evidence paths
6. Launch GF with finite timeout
7. Capture stdout and stderr separately
8. Parse exact marker lines from stdout
9. Build section results
10. Evaluate automatic assertions
11. Evaluate project assertions
12. Normalize complete eligible output
13. Validate and compare gold when configured
14. Verify produced artifacts when configured
15. Build structured ScenarioResult
16. Preserve all evidence
```

Reports consume the resulting `ScenarioResult`.

They must not rerun the scenario.

---

## 36. Stop and continue policy

### 36.1 Stop the affected scenario when

- script is missing;
- path containment fails;
- required input is missing;
- GF cannot launch;
- process times out;
- process is cancelled;
- output cannot be decoded;
- marker protocol becomes structurally invalid;
- required evidence cannot be written.

### 36.2 Continue evidence collection when safe

- one assertion fails;
- one section fails but the transcript remains parseable;
- gold differs;
- a non-fatal warning appears;
- an optional artifact is missing;
- one input case fails but later independent cases remain executable.

### 36.3 Release behavior

Release mode may continue after a failure to collect evidence.

Continuation never converts the final failure to success.

---

## 37. Timeouts and bounds

Every scenario must have finite resource limits.

Potential bounds:

```text
process timeout
generation count
input count
parse result count
output byte count
section line count
report excerpt count
```

A bound must not silently discard evidence needed for success.

When truncation occurs:

- raw truncation status is explicit;
- required assertions dependent on truncated content do not pass;
- gold comparison does not pass unless the contract proves truncation irrelevant.

---

## 38. Determinism

Given the same:

```text
source revision
project configuration
GF version
RGL identity
scenario script
input files
normalization version
```

the scenario result should be deterministic.

Potential nondeterminism must be:

- removed;
- bounded and sorted;
- projected to a deterministic subset;
- or documented as unsuitable for exact gold comparison.

Randomness, current time, machine paths, or unordered filesystem enumeration must not leak into accepted gold.

---

## 39. Security and trust

A `.gfs` file is executable input to GF.

Rules:

- scripts must be reviewed;
- project paths remain inside the project boundary;
- input and gold paths remain contained;
- shell escape is prohibited unless explicitly authorized;
- no secret is embedded in scripts or inputs;
- normal validation performs no source mutation;
- untrusted scenarios require sandbox policy;
- complete environments are not logged;
- external uploads are not implicit.

Generating `AI_READY.md` does not authorize sending project evidence to an external AI service.

---

## 40. Scenario naming and organization

For a small suite, one script per registered scenario is preferred.

For larger coverage, use stable subfamilies while preserving one authoritative registry.

Possible organization:

```text
scenarios/
├── load.gfs
├── missing.gfs
├── linearize.gfs
├── parse.gfs
├── generation.gfs
├── morphology.gfs
└── regression/
    ├── structural-dconj.gfs
    ├── focus-ap.gfs
    └── prep-government.gfs
```

Nested layout requires explicit registered paths.

Directory scanning alone must not decide requiredness.

---

## 41. Scenario comments

A scenario should explain:

- purpose;
- target entrypoint;
- expected sections;
- input dependencies;
- gold relationship;
- known limits;
- reason for unusual commands.

Comments must not:

- assert a type contradicted by source;
- describe a stale entrypoint;
- claim a warning is harmless without evidence;
- substitute for a marker or assertion;
- encode machine-local paths.

---

## 42. Inputs and scenario portability

Scenario assets must avoid:

- developer-specific absolute paths;
- current-user profile paths;
- output-directory paths;
- hidden dependency on prior `.gfo` or `.pgf`;
- undocumented locale behavior;
- reliance on interactive prompts;
- reliance on a previous GF shell session.

A scenario begins from a controlled fresh process unless the external-tool contract explicitly defines another model.

---

## 43. Albanian touched-module minimum

When one Albanian GF file changes, minimum validation should include:

```text
compile the touched module
review hard errors
review warnings
run its category/family checks
compile nearest importer or façade
review affected status-ledger entries
```

Examples of nearest importer relationships include:

```text
ExtendSqiFocusPrep.gf → ExtendSqi.gf
StructuralSqiClause.gf → StructuralSqi.gf
structural producer → StructuralSqi.gf
user-facing structural change → SyntaxSqi.gf
```

The exact dependency map is authoritative.

---

## 44. Albanian subsystem minimum

When a complete family changes:

```text
compile every changed family member
run family regressions
compile family coordinator
compile affected façade
run warning-cluster checks
run exact-helper-type checks
run constructor-availability checks
run affected scenarios
review gold
```

---

## 45. Albanian repair-cycle minimum

Before declaring a repair cycle complete:

```text
compile all selected Albanian release modules
pass fragile regression set
introduce no unexplained warning cluster
keep façade modules thin
do not promote blocked symbols silently
reconcile changed comments and docs
run required scenarios
verify required gold
build required PGF in release mode
```

---

## 46. Warning review

Warnings are evidence.

High-risk warning families include:

```text
lock_AP
lock_CN
lock_Prep
missing lincat/default insertion
shape-loss warnings
constructor-context warnings
```

No new warning is accepted silently.

Each warning must be:

- eliminated;
- understood and accepted;
- documented in the status ledger;
- linked to an exit condition when temporary.

A scenario process with warnings may still be `OK` only when project policy explicitly permits them.

---

## 47. Status-ledger integration

A scenario or validation asset that exercises a temporary or blocked item must reference the corresponding status-ledger identity in project documentation or scenario metadata.

Statuses such as:

```text
warning
temporary
fallback
incomplete
blocked
```

must not be silently treated as stable because a test currently passes.

Tests prove the declared current behavior.

They do not promote maturity status.

---

## 48. Known project regression anchors

The validation suite must retain regression coverage for currently documented fragile areas, including:

```text
DConj constructor availability
both7and_DConj
either7or_DConj
must_VV implementation path
A versus AP helper compatibility
preposition government
rich category preservation
rich list preservation
direct versus downstream failure attribution
stale comment hazards
```

Exact symbol status and current applicability belong to:

```text
project/docs/STATUS_LEDGER.md
```

Resolved anchors may remain as regression tests.

---

## 49. Release-gate expectations

A release-ready validation run normally requires:

```text
valid project configuration
supported GF toolchain
selected source inventory complete
blocking scan findings resolved
required checkpoints compile
final entrypoints compile
missing-linearization policy passes
all required scenarios execute
all required markers and assertions pass
all required gold comparisons pass
required PGF exists and is valid
no unresolved release-blocking issue
summary and manifest are valid
```

This README does not weaken `project/docs/RELEASE_CRITERIA.md`.

---

## 50. Failure classification

Scenario failures use the shared diagnostic model:

```text
status
execution_state
error_kind
diagnostic_class
primary_message
evidence
```

Relevant technical error kinds include:

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

Relevant causal classes include:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

The scenario runner must not classify every script or timeout failure as a direct Albanian grammar defect.

---

## 51. Direct and downstream examples

### Direct scenario asset failure

```text
scenario marker is malformed
→ status ERROR
→ error_kind SCRIPT
→ diagnostic_class direct
```

### Downstream grammar failure

```text
parse scenario cannot load SyntaxSqi because NounSqi failed
→ scenario status FAIL or SKIPPED according to execution
→ diagnostic_class downstream or skipped
→ blocker identifies failed provider
```

### Ambiguous runtime failure

```text
GF exits unexpectedly with no reliable source attribution
→ status FAIL or ERROR
→ diagnostic_class ambiguous
```

### Tool failure

```text
GF executable cannot launch
→ status ERROR
→ error_kind TOOL or CONFIG
→ no Albanian linguistic conclusion
```

---

## 52. Regression comparison

A scenario is compared across runs by stable scenario identity.

Comparison may consider:

```text
status
error kind
diagnostic class
completed sections
assertion results
gold match
artifact results
duration
output fingerprint
```

A previous run from another project ID is not a valid baseline.

Changing a scenario ID breaks automatic historical identity unless a migration mapping is defined.

---

## 53. Scenario result evidence

A scenario result should preserve or reference:

```text
scenario_id
script_path
requiredness
status
command
working_directory
exit_code
execution state
duration
stdout_path
stderr_path
normalized_output_path
gold_path
gold_match
diagnostic class
error kind
primary message
section results
assertion results
artifact results
```

The exact serialized fields are owned by the persisted schema.

---

## 54. README responsibilities of subdirectories

### `scenarios/README.md`

Owns:

- script authoring conventions;
- GF shell discipline;
- marker placement examples;
- scenario review checklist;
- local naming examples.

It must not redefine the global marker protocol.

### `inputs/README.md`

Owns:

- input formats;
- encoding;
- line semantics;
- ordering;
- comments;
- file-specific ownership.

### `gold/README.md`

Owns:

- gold format;
- review workflow;
- diff review;
- update checklist;
- empty-gold policy.

This parent README owns the overall relationship among the three directories.

---

## 55. Adding a new scenario

Checklist:

```text
[ ] Purpose is documented
[ ] Stable scenario ID selected
[ ] Required or optional status decided
[ ] Applicable modes decided
[ ] Target entrypoint identified
[ ] Script path selected
[ ] Native `.gfs` script created
[ ] Timeout chosen
[ ] Marker policy chosen
[ ] Expected section IDs declared
[ ] Assertions declared
[ ] Inputs created and documented when needed
[ ] Normalization version selected
[ ] Gold relationship decided
[ ] Gold created only through explicit review
[ ] Artifact expectations declared when needed
[ ] project.toml updated
[ ] VALIDATION_SPEC.md updated
[ ] TEST_COVERAGE_MATRIX.md updated
[ ] INTERFILE_CONTRACT_LOCK.md updated
[ ] Scenario executes from a clean environment
[ ] Evidence paths are correct
[ ] Required consumers and release gates reviewed
```

---

## 56. Modifying a scenario

A scenario modification requires review of:

```text
purpose
entrypoint
GF commands
section IDs
marker order
assertions
inputs
normalization
gold
timeout
requiredness
applicable modes
artifact expectations
historical comparison
```

Changing only the `.gfs` file is insufficient when another asset depends on its output.

---

## 57. Removing a scenario

Before removal:

```text
[ ] Scenario is no longer required by project.toml
[ ] Release criteria are updated
[ ] Coverage matrix shows replacement or accepted loss
[ ] Inputs have no remaining consumers
[ ] Gold has no remaining consumer
[ ] Historical identity is recorded
[ ] Contract lock is updated
[ ] Decision log is updated when coverage changes materially
[ ] No report or automation expects the old ID
```

A removed scenario ID must not be reused for unrelated coverage.

---

## 58. Adding or modifying input data

Checklist:

```text
[ ] Owning scenario identified
[ ] Format documented
[ ] UTF-8 verified
[ ] Ordering semantics documented
[ ] Empty-line policy documented
[ ] Comment policy documented
[ ] Positive/negative expectation explicit
[ ] No machine-local path present
[ ] No secret present
[ ] Scenario reads the intended file
[ ] Output impact reviewed
[ ] Gold impact reviewed
[ ] Version compatibility reviewed
```

---

## 59. Adding or modifying gold

Checklist:

```text
[ ] Scenario ID matches filename
[ ] Gold schema header is valid
[ ] Normalization version matches
[ ] Section IDs match scenario registry
[ ] Old raw output reviewed
[ ] New raw output reviewed
[ ] Normalized diff reviewed
[ ] Linguistic reason documented
[ ] Architectural reason documented when relevant
[ ] No unstable path/timing noise remains
[ ] No meaningful output was normalized away
[ ] Validation specification reviewed
[ ] Decision log updated when significant
[ ] Contract lock updated when behavior changed
[ ] Gold written atomically
[ ] Full affected validation rerun
```

---

## 60. Review checklist for this directory

```text
[ ] `README.md` reflects current validation architecture
[ ] `scenarios/README.md` exists
[ ] `inputs/README.md` exists
[ ] `gold/README.md` exists
[ ] Every required scenario is registered
[ ] Every registered script exists
[ ] Every script has stable identity
[ ] Every required scenario has assertions
[ ] Every marker-required scenario has expected sections
[ ] Every input is documented
[ ] Every required gold exists
[ ] Every gold header is valid
[ ] Normalization versions agree
[ ] No generated run file is stored here
[ ] No machine-local path is stored here
[ ] No normal run modified project assets
[ ] High-risk Albanian families have coverage
[ ] Status-ledger anchors have regression coverage
[ ] Release-required scenarios pass
[ ] Required PGF gate is represented
```

---

## 61. Anti-drift indicators

Probable validation-asset drift exists when:

- a required scenario ID has no `.gfs`;
- an unregistered script is treated as release evidence;
- script filename and scenario ID disagree;
- script marker ID differs from registry ID;
- section IDs change without gold review;
- a scenario loads a lower-level substitute;
- an input file is reordered without review;
- a gold file is created automatically;
- a normal run rewrites gold;
- raw stdout is copied directly into gold;
- a gold header has the wrong normalization version;
- generated logs appear under `project/validation/`;
- an absolute local path appears in a script;
- a marker is emitted to stderr and silently accepted;
- an unknown reserved marker is ignored;
- zero exit is treated as success despite incomplete sections;
- optional scenario failure is hidden;
- required scenario is skipped in release mode;
- generation is unbounded;
- parse ambiguity is normalized away;
- Albanian diacritics are damaged by encoding;
- `A`/`AP`, `NP`/`Pron`, or list-category distinctions disappear in tests;
- DConj or Prep constructor risk loses regression coverage;
- status-ledger items are silently promoted;
- reports rerun scenarios;
- scenario output changes but gold and validation spec remain untouched.

Every indicator requires correction before release.

---

## 62. Implementation transition

The current predecessor implementation primarily audits and compiles files.

The complete GF Wordbench design adds:

```text
native scenario runner
marker parser
assertion evaluator
normalizer
gold comparator
scenario result model
PGF release verification
artifact manifest integration
```

Until those components are implemented:

- this directory remains the normative target structure;
- project assets may be prepared incrementally;
- unavailable scenario capabilities must be reported as planned or skipped;
- legacy `all` mode must not be described as full release validation;
- no report may claim scenario/gold/PGF gates executed when they did not.

---

## 63. Minimum completion criteria

The project validation directory is structurally complete when:

```text
[ ] Parent README is current
[ ] Scenario README is current
[ ] Input README is current
[ ] Gold README is current
[ ] Required scenario files exist
[ ] Optional scenario files are explicitly registered
[ ] Required inputs exist
[ ] Required gold files exist
[ ] Scenario IDs are unique
[ ] Marker protocol is valid
[ ] Assertion strategy is explicit
[ ] Normalization versions are supported
[ ] Project configuration paths resolve
[ ] Validation specification maps every scenario
[ ] Coverage matrix maps every release criterion
```

It is release-complete only when the clean release run passes every required gate.

---

## 64. Quick operational summary

### Edit source

```text
compile touched module
compile nearest importer
run affected family scenario
review warnings
review ledger anchors
```

### Edit scenario

```text
validate registry
run scenario
validate markers
validate assertions
review normalized output
review gold impact
```

### Edit input

```text
validate encoding and semantics
run consuming scenario
review output and gold
```

### Edit gold

```text
use explicit update workflow
review raw old/new evidence
review normalized diff
rerun affected release validation
```

### Prepare release

```text
run canonical release mode
execute all required scenarios
match all required golds
build and verify PGF
verify summary and manifest
retain evidence
```

---

## 65. Final enforcement rule

This directory is the project’s reviewed validation specification in executable form.

It must remain stable, attributable, deterministic, and separate from generated evidence.

Therefore:

> No Albanian project release may treat a scenario as passed unless its registered native GF script executed under the declared policy, its required sections and assertions completed, its reviewed inputs were used, its required normalized output matched the corresponding gold, and all evidence was preserved outside the project validation source directory.
