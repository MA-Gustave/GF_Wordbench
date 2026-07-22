# Albanian (`Sqi`) — Known Issues

**Document ID:** `GF-WB-PROJECT-KNOWN-ISSUES`  
**Status:** Active project issue registry  
**Project language:** Albanian  
**GF module suffix:** `Sqi`  
**Canonical source root:** `lib/src/albanian`  
**Primary owner:** Albanian project maintainers  
**Configuration owner:** `project/project.toml`  
**Status owner:** `project/docs/STATUS_LEDGER.md`  
**Release-policy owner:** `project/docs/RELEASE_CRITERIA.md`  
**Issue-registry version:** `1.0`  
**Last reviewed:** 2026-07-22  

---

## 1. Purpose

This document records known defects, limitations, risks, evidence gaps, and release blockers for the active Albanian (`Sqi`) GF project.

It exists to prevent:

- temporary implementations being presented as stable;
- historical failures being confused with current failures;
- downstream compile failures being treated as independent root causes;
- release decisions being made without reproducible evidence;
- undocumented workarounds becoming permanent architecture;
- known linguistic limitations disappearing from review;
- documentation drift between source, scenarios, gold files, entrypoints, and release criteria.

This registry is project-specific.

Framework defects belong in the framework issue tracker or framework documentation.

---

## 2. Core rule

> An issue is “known” only when its evidence level, affected scope, current status, release impact, and next verification action are explicit.

A message appearing in a historical test fixture is not sufficient to declare a current project defect.

A successful compile is not sufficient to close a linguistic issue.

A downstream failure is not a second root issue when it is blocked by a documented provider failure.

---

## 3. Evidence warning

The available baseline contains historical and synthetic Albanian examples involving modules such as:

```text
GrammarSqi.gf
StructuralSqi.gf
LangSqi.gf
ExtendSqi.gf
AllSqi.gf
NounSqi.gf
```

Example messages include:

```text
cannot unify
Internal error in GeneratePMCFG
Cannot find an inflection rule
Warning: no linearization type for DAP
blocked by failed dependency GrammarSqi.gf
```

These examples are useful for:

- parser tests;
- classifier tests;
- report tests;
- regression-fixture design.

They do **not** prove that the same failures exist in the current source revision.

Every such item is classified below as historical, synthetic, or requiring reproduction until a current GF Wordbench run confirms it.

---

## 4. Related project documents

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
project/docs/RELEASE_CRITERIA.md
project/docs/RESEARCH_EVIDENCE.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Framework references:

```text
docs/diagnostics/KNOWN_DIAGNOSTIC_PATTERNS.md
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
docs/validation/SCENARIO_VALIDATION.md
docs/reports/REPORTING_OVERVIEW.md
docs/release/RELEASE_PROCESS.md
```

---

## 5. Scope

This registry may contain issues concerning:

- project identity;
- GF module availability;
- import relationships;
- public categories and functions;
- lincat fields;
- parameter domains;
- noun morphology;
- verb morphology;
- adjective morphology;
- pronouns and clitics;
- syntax;
- word order;
- structural vocabulary;
- paradigms;
- lexicon;
- extension modules;
- entrypoints;
- scenarios;
- normalized output;
- gold files;
- PGF artifacts;
- project documentation;
- release evidence;
- tested GF compatibility.

---

## 6. Exclusions

This registry does not directly own:

- Python framework defects;
- GF upstream defects not reproduced by this project;
- operating-system defects;
- feature requests without identified project impact;
- speculative linguistic improvements without a concrete requirement;
- private implementation tasks that affect no contract;
- resolved historical issues retained only in the decision log or changelog.

An upstream GF issue may be referenced here when it blocks the Albanian project.

---

# 7. Issue status vocabulary

Canonical statuses:

```text
Open
Investigating
Blocked
Mitigated
Deferred
Resolved
Closed as not reproducible
Closed as duplicate
Retired
```

---

## 8. Open

The issue is accepted and requires action.

It has enough evidence to remain in the active registry.

---

## 9. Investigating

The symptom is credible but root cause or exact scope is not yet established.

A reproduction plan is mandatory.

---

## 10. Blocked

Progress depends on:

- another project issue;
- an upstream GF fix;
- missing linguistic evidence;
- unresolved architecture decision;
- unavailable project asset.

The blocker must be identified.

---

## 11. Mitigated

A workaround limits impact, but the underlying issue remains.

A mitigation must not be described as a final fix.

---

## 12. Deferred

The issue is accepted but intentionally postponed.

Required fields:

```text
reason
review trigger
release impact
```

---

## 13. Resolved

The implementation and required evidence demonstrate that the issue is fixed.

Resolution is not complete until affected consumers and release gates are reviewed.

---

## 14. Closed as not reproducible

A current controlled attempt did not reproduce the issue.

The reproduction environment and evidence must be recorded.

Historical evidence remains referenced.

---

## 15. Closed as duplicate

The issue is represented by another canonical issue ID.

The replacement ID is mandatory.

---

## 16. Retired

The affected feature or module is no longer part of the active project contract.

Consumers must no longer depend on it.

---

# 17. Evidence levels

Canonical evidence levels:

```text
E0 — assertion only
E1 — historical or synthetic fixture
E2 — current static evidence
E3 — current reproducible GF failure
E4 — current reproducible scenario or gold failure
E5 — release-run or artifact verification failure
```

---

## 18. Evidence level `E0`

No durable evidence exists.

An `E0` item should normally be a verification task, not a confirmed defect.

---

## 19. Evidence level `E1`

Evidence exists only in:

- historical logs;
- synthetic test fixtures;
- example reports;
- migration fixtures.

It is not a current release blocker without reproduction.

---

## 20. Evidence level `E2`

Current source, configuration, or documentation demonstrates a concrete issue without running GF.

Examples:

- missing configured file;
- unresolved required placeholder;
- duplicate scenario ID;
- absolute machine path in project configuration;
- missing required project document;
- documented lincat field absent from provider source.

---

## 21. Evidence level `E3`

A current controlled GF operation reproduces the failure.

Required evidence:

```text
source revision
GF version
GF Wordbench version
command
working directory
stdout
stderr
exit code
affected artifact
```

---

## 22. Evidence level `E4`

A current required scenario or gold comparison reproduces the issue.

Required evidence:

```text
scenario ID
entrypoint
normalization version
raw output
normalized output
gold result
```

---

## 23. Evidence level `E5`

A current release-mode run or artifact verification proves release impact.

Examples:

- required PGF missing;
- required release scenario fails;
- manifest verification fails;
- required entrypoint fails;
- release gate fails.

`E5` is the strongest project-release evidence.

---

# 24. Severity

Canonical severities:

```text
Critical
High
Medium
Low
Informational
```

---

## 25. Critical

Examples:

- unsafe artifact overwrite;
- source or gold data loss;
- release artifact invalid despite reported success;
- severe security boundary violation;
- project identity corruption.

A critical unresolved issue blocks all release.

---

## 26. High

Examples:

- release entrypoint fails;
- required PGF cannot be built;
- required scenario fails;
- core category contract is broken;
- current internal GF failure blocks core grammar;
- required morphology is structurally unavailable.

A high unresolved issue normally blocks project release.

---

## 27. Medium

Examples:

- optional construction is incorrect;
- important coverage gap;
- non-core module failure;
- ambiguous failure classification requiring investigation;
- documented fallback used outside release-critical paths.

Release impact depends on `RELEASE_CRITERIA.md`.

---

## 28. Low

Examples:

- minor lexical gap;
- nonblocking formatting or wording issue;
- optional documentation refinement;
- limited diagnostic inconvenience.

---

## 29. Informational

Used for:

- historical observations;
- compatibility notes;
- monitoring items;
- resolved risks retained temporarily for review.

---

# 30. Priority

Canonical priorities:

```text
P0 — immediate
P1 — before next release
P2 — planned
P3 — backlog
```

Severity and priority are separate.

A medium issue may be `P1` because it affects an imminent release.

---

# 31. Release impact

Canonical release-impact values:

```text
Blocks all release
Blocks project release
Blocks affected feature
Nonblocking with explicit acceptance
No current release impact
Unknown pending reproduction
```

The release impact must agree with:

```text
project/docs/RELEASE_CRITERIA.md
```

---

# 32. Issue identifiers

Canonical format:

```text
KI-SQI-<NUMBER>
```

Examples:

```text
KI-SQI-001
KI-SQI-002
```

Rules:

- IDs are never reused;
- resolved IDs remain historically identifiable;
- duplicate items reference the canonical ID;
- IDs are independent of module names;
- renaming a module does not rename an issue ID.

---

# 33. Required issue fields

Every detailed issue entry must specify:

| Field | Requirement |
|---|---|
| Issue ID | Stable `KI-SQI-*` identifier |
| Title | Concise problem statement |
| Status | Canonical issue status |
| Evidence level | `E0`–`E5` |
| Severity | Canonical severity |
| Priority | `P0`–`P3` |
| Release impact | Explicit release meaning |
| Affected area | Modules, scenarios, docs, artifacts, or contracts |
| Observation | What is known |
| Non-claims | What the evidence does not prove |
| Reproduction | Current reproduction steps or required plan |
| Expected behavior | Contractual expectation |
| Current behavior | Reproduced behavior or unknown |
| Root cause | Known, suspected, or unknown |
| Dependencies | Blockers and downstream items |
| Workaround | Existing mitigation or none |
| Resolution criteria | Evidence required to close |
| Validation | Tests, scenarios, compile targets, artifacts |
| Owner | Responsible project role or person |
| Last reviewed | Date or release |

---

# 34. Registry summary

The following entries are initialized from available project-contract requirements and historical fixtures.

None of the historical diagnostic examples is marked as a current confirmed source defect without a current reproduction.

| Issue ID | Title | Status | Evidence | Severity | Release impact |
|---|---|---|---|---|---|
| `KI-SQI-001` | Current release baseline must be established | Open | `E0` | High | Unknown pending reproduction |
| `KI-SQI-002` | Historical `GrammarSqi` unification failure requires reproduction | Investigating | `E1` | High | Unknown pending reproduction |
| `KI-SQI-003` | Historical `GeneratePMCFG` / inflection-rule failure requires reproduction | Investigating | `E1` | High | Unknown pending reproduction |
| `KI-SQI-004` | Historical missing `DAP` linearization type requires verification | Investigating | `E1` | Medium | Unknown pending reproduction |
| `KI-SQI-005` | Downstream failures must not be counted as independent root issues | Open | `E1` | Medium | No current release impact |
| `KI-SQI-006` | Project documentation and contract placeholders require zero-placeholder verification | Open | `E2` when confirmed | High | Blocks project release if present |
| `KI-SQI-007` | Entrypoint, scenario, gold, and PGF registry consistency requires release check | Open | `E0` | High | Blocks project release if inconsistent |
| `KI-SQI-008` | Legacy GF Audit assumptions must not remain canonical project policy | Open | `E1` | Medium | Blocks affected feature |
| `KI-SQI-009` | Exact active module inventory and status must remain synchronized | Open | `E0` | Medium | Blocks project release if unresolved |
| `KI-SQI-010` | Linguistic coverage gaps must be moved from implicit knowledge into matrices | Open | `E0` | Medium | Nonblocking only with explicit acceptance |

---

# 35. KI-SQI-001 — Current release baseline must be established

**Status:** Open  
**Evidence level:** `E0`  
**Severity:** High  
**Priority:** `P1`  
**Release impact:** Unknown pending reproduction  

## Affected area

```text
project/project.toml
lib/src/albanian/
project/validation/
project/docs/RELEASE_CRITERIA.md
release PGF
```

## Observation

No current release-mode `summary.json` or verified project manifest is part of the evidence used to initialize this registry.

Therefore the following are not yet established by this document:

- current module pass/fail state;
- current required scenario state;
- current gold state;
- current final PGF state;
- current tested GF version;
- current release readiness.

## Non-claims

This issue does not claim that the project currently fails.

It claims only that a current canonical release baseline is required before release status can be asserted here.

## Required reproduction

Run the configured active project in:

```text
release
```

using:

- a supported GF Wordbench revision;
- a supported GF executable;
- the configured RGL root;
- a clean run directory;
- the current source revision.

## Expected behavior

The run produces:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
master.log
required raw evidence
required normalized outputs
final PGF
```

Every required gate has a final result.

## Root cause

Not applicable.

This is a release-evidence gap.

## Dependencies

Blocks confirmation or closure of:

```text
KI-SQI-002
KI-SQI-003
KI-SQI-004
KI-SQI-007
```

## Workaround

Development can continue using `quick`, `checkpoint`, and `diagnostic` runs.

No release-readiness claim may be based solely on those partial runs.

## Resolution criteria

```text
[ ] current release run ID recorded
[ ] source revision recorded
[ ] GF Wordbench version recorded
[ ] GF version recorded
[ ] required entrypoints evaluated
[ ] required scenarios evaluated
[ ] required gold evaluated
[ ] PGF verified
[ ] manifest verified
[ ] release result linked from this registry
```

## Owner

Project release maintainer.

---

# 36. KI-SQI-002 — Historical `GrammarSqi` unification failure requires reproduction

**Status:** Investigating  
**Evidence level:** `E1`  
**Severity:** High  
**Priority:** `P1`  
**Release impact:** Unknown pending reproduction  

## Affected area

Historical examples reference:

```text
lib/src/albanian/GrammarSqi.gf
lib/src/albanian/LangSqi.gf
lib/src/albanian/ExtendSqi.gf
```

## Observation

Historical or synthetic fixtures contain messages such as:

```text
GrammarSqi.gf: cannot unify
cannot unify the information
```

They also model `LangSqi` or `ExtendSqi` as downstream of `GrammarSqi`.

## Non-claims

The fixture does not prove:

- that current `GrammarSqi.gf` fails;
- that the message is native GF wording in every sample;
- that one specific lincat or function causes the mismatch;
- that downstream modules contain independent defects.

## Required reproduction

```text
1. compile GrammarSqi.gf directly
2. preserve stdout and stderr separately
3. record GF version
4. parse expected/inferred types when emitted
5. compile registered direct consumers
6. classify downstream evidence
7. run the relevant checkpoint
```

## Expected behavior

`GrammarSqi.gf` compiles under the project’s configured GF path and satisfies every registered consumer contract.

## Current behavior

Unknown for the current source revision.

## Suspected root-cause families

Only after current evidence may investigation consider:

- lincat field mismatch;
- changed parameter domain;
- constructor argument mismatch;
- imported provider contract drift;
- abstract/concrete signature mismatch;
- stale compiled artifact;
- GF-version compatibility.

No family is selected as the current root cause.

## Dependencies

Potential downstream subjects:

```text
LangSqi.gf
ExtendSqi.gf
AllSqi.gf
release entrypoint
PGF build
```

Actual dependency edges must be confirmed from `MODULE_DEPENDENCY_MAP.md`.

## Workaround

None approved.

A downstream module must not patch the provider mismatch locally.

## Resolution criteria

```text
[ ] current direct compile reproduced or disproved
[ ] primary provider identified if reproduced
[ ] expected/inferred type preserved
[ ] direct consumers reviewed
[ ] checkpoint passes
[ ] scenarios updated where required
[ ] gold reviewed where output changed
[ ] contract lock updated
[ ] decision log updated if breaking
```

## Owner

Grammar/category architecture maintainer.

---

# 37. KI-SQI-003 — Historical `GeneratePMCFG` / inflection-rule failure requires reproduction

**Status:** Investigating  
**Evidence level:** `E1`  
**Severity:** High  
**Priority:** `P1`  
**Release impact:** Unknown pending reproduction  

## Affected area

Historical fixture references include:

```text
StructuralSqi.gf
GrammarSqi.gf
CatSqi.gf
```

## Observation

Captured test evidence contains:

```text
Internal error in GeneratePMCFG
Cannot find an inflection rule
```

The nested form appears as:

```text
evalTerm (Predef.error "Cannot find an inflection rule")
```

## Non-claims

This evidence does not prove that:

- the current project triggers the error;
- `StructuralSqi.gf` is the current root cause;
- GF itself is defective rather than surfacing a project-level incomplete table;
- the failure occurs on every supported GF version.

## Required reproduction

```text
1. compile the smallest historical provider candidate
2. compile StructuralSqi.gf when present
3. compile GrammarSqi.gf
4. build the configured PGF
5. record exact GF version
6. retain stdout/stderr and generated artifacts
7. compare behavior across supported GF versions when necessary
```

## Expected behavior

No required compile or PGF build reaches an internal `GeneratePMCFG` failure.

Every required inflection lookup is defined for the relevant parameter domain.

## Current behavior

Unknown for the current source revision.

## Investigation order

```text
1. locate every explicit Predef.error related to inflection
2. locate incomplete morphology tables
3. identify structural entries using affected paradigms
4. identify missing parameter branches
5. identify default or fallback paradigms
6. reproduce with the smallest entrypoint
7. check GF-version compatibility
```

## Workaround

No hidden fallback is approved.

A temporary fallback must be entered in `STATUS_LEDGER.md` and must not conceal release failure.

## Resolution criteria

```text
[ ] current reproduction established or closed as not reproducible
[ ] smallest failing provider identified
[ ] missing inflection domain identified when applicable
[ ] provider fixed without raw-string flattening
[ ] structural consumers compile
[ ] grammar entrypoint compiles
[ ] PGF builds
[ ] morphology/structural scenarios pass
[ ] affected gold reviewed
```

## Owner

Morphology and structural-vocabulary maintainers.

---

# 38. KI-SQI-004 — Historical missing `DAP` linearization type requires verification

**Status:** Investigating  
**Evidence level:** `E1`  
**Severity:** Medium  
**Priority:** `P1`  
**Release impact:** Unknown pending reproduction  

## Observation

A historical report fixture includes:

```text
Warning: no linearization type for DAP, inserting default {s : Str}
```

## Affected area

Potentially:

```text
abstract category DAP
concrete category provider
CatSqi.gf or registered equivalent
downstream syntax consumers
missing-linearization scenario
```

## Non-claims

The fixture does not prove that:

- `DAP` remains in the active abstract API;
- the current concrete syntax lacks a lincat;
- the warning is current;
- `{s : Str}` is currently inserted;
- release behavior is affected.

## Expected behavior

Every required abstract category exposed by the release entrypoint has one documented concrete `lincat`.

No required category receives an unintended default lincat.

## Required verification

```text
1. confirm whether DAP is active in the selected abstract grammar
2. inspect the current category provider
3. compile the concrete category checkpoint
4. run missing-linearization inspection
5. compile release entrypoint
6. verify current warning output
```

## Release impact

If reproduced for a required category:

```text
Blocks project release
```

If the category is not part of the active release API:

```text
No current release impact
```

with explicit documentation.

## Resolution criteria

```text
[ ] category applicability determined
[ ] current lincat documented
[ ] no unintended default inserted
[ ] direct consumers compile
[ ] missing-linearization check passes
[ ] category contract updated
```

## Owner

Category/lincat contract maintainer.

---

# 39. KI-SQI-005 — Downstream failures must not be counted as independent root issues

**Status:** Open  
**Evidence level:** `E1`  
**Severity:** Medium  
**Priority:** `P1`  
**Release impact:** No current release impact  

## Observation

Historical classification fixtures model:

```text
GrammarSqi.gf → direct failure
LangSqi.gf    → downstream
ExtendSqi.gf  → downstream
```

when their diagnostics reference the failed provider.

## Risk

Without dependency-aware review:

- one root failure may generate many apparent issues;
- maintainers may patch consumers incorrectly;
- release reports may overstate defect count;
- issue IDs may be duplicated for the same cause.

## Required behavior

A downstream issue entry must include:

```text
blocked_by
root issue ID
affected consumer
independent evidence, if any
```

A consumer receives its own root issue only when current evidence demonstrates an independent failure.

## Workaround

During triage:

1. start with `direct`;
2. inspect `blocked_by`;
3. defer downstream repair;
4. rerun consumers after provider repair;
5. promote only remaining independent failures.

## Resolution criteria

This governance issue remains open until the active project workflow and reports consistently preserve root/downstream distinctions.

## Validation

```text
classifier tests
dependency-map review
current diagnostic run
post-provider-fix rerun
```

## Owner

Project validation maintainer.

---

# 40. KI-SQI-006 — Project documentation and contract placeholders require zero-placeholder verification

**Status:** Open  
**Evidence level:** `E2` when a placeholder is confirmed in active files  
**Severity:** High  
**Priority:** `P1`  
**Release impact:** Blocks project release if present  

## Affected area

```text
project/docs/
project/project.toml
project/validation/
project/docs/INTERFILE_CONTRACT_LOCK.md
```

## Observation

Project documentation templates use placeholders such as:

```text
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<SOURCE_DIR>
<ENTRYPOINT>
<EXPECTED_PGF>
<status>
<YYYY-MM-DD>
```

The active project must contain no unresolved required placeholder.

## Non-claims

Template files under:

```text
templates/project/
```

are expected to contain placeholders.

This issue concerns active project files only.

## Required check

Search active project-owned files for unresolved placeholder syntax.

Recommended patterns:

```regex
<[A-Z][A-Z0-9_ -]*>
```

and known status alternatives left as template choices.

Review false positives manually.

## Expected behavior

Every active-project document and configuration field contains:

- Albanian/Sqi identity;
- actual source paths;
- actual entrypoints;
- actual scenario IDs;
- actual statuses;
- actual PGF name;
- actual review dates where required.

## Resolution criteria

```text
[ ] active project placeholder scan is clean
[ ] template placeholders remain confined to templates
[ ] project lock identity is filled
[ ] architecture ownership map is filled
[ ] contract registry statuses are final
[ ] entrypoint and PGF fields are concrete
[ ] documentation consistency check passes
```

## Owner

Project documentation maintainer.

---

# 41. KI-SQI-007 — Entrypoint, scenario, gold, and PGF registry consistency requires release check

**Status:** Open  
**Evidence level:** `E0`  
**Severity:** High  
**Priority:** `P1`  
**Release impact:** Blocks project release if inconsistent  

## Affected area

```text
project/project.toml
lib/src/albanian/
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/RELEASE_CRITERIA.md
```

## Risk

Drift may occur when:

- an entrypoint is renamed;
- a scenario loads an old module;
- a gold filename no longer matches the scenario;
- the PGF target changes;
- a required scenario becomes optional accidentally;
- a module exists but is not registered;
- a registered file is missing.

## Expected behavior

One consistent registry defines:

```text
ordered checkpoints
required entrypoints
optional entrypoints
required scenarios
optional scenarios
scenario scripts
input files
gold files
release entrypoint
expected PGF
```

## Required checks

```text
[ ] every configured module exists
[ ] module name matches filename
[ ] every required scenario exists
[ ] every scenario ID is unique
[ ] every scenario loads a registered entrypoint
[ ] every required gold exists
[ ] every gold identifies the correct scenario
[ ] normalization versions agree
[ ] release entrypoint exists
[ ] expected PGF name is consistent
[ ] release manifest expects the same PGF
```

## Resolution criteria

A current release check passes with no registry inconsistency.

## Owner

Project configuration and validation maintainer.

---

# 42. KI-SQI-008 — Legacy GF Audit assumptions must not remain canonical project policy

**Status:** Open  
**Evidence level:** `E1`  
**Severity:** Medium  
**Priority:** `P2`  
**Release impact:** Blocks affected feature  

## Historical assumptions

Legacy fixtures and code may contain:

```text
mode = all
mode = file
_gf_audit
gf-audit
flat RunConfig fields
legacy timeout sentinels
unversioned summaries
historical active-language paths in framework tests
```

## Canonical GF Wordbench replacements

```text
all  → diagnostic
file → quick
_gf_audit → _gf_wordbench or configured output root
gf-audit → gf-wordbench
versioned persisted schemas
structured process execution state
project-owned language paths
```

## Risk

Legacy assumptions may cause:

- wrong mode semantics;
- wrong artifact location;
- stale documentation;
- incompatible previous-run comparison;
- framework/project boundary leakage;
- incorrect timeout interpretation.

## Expected behavior

The active project uses canonical GF Wordbench names and schemas.

Legacy forms remain only in:

- migration fixtures;
- compatibility readers;
- clearly historical tests;
- historical documentation.

## Resolution criteria

```text
[ ] project.toml uses canonical modes
[ ] project docs use canonical product name
[ ] validation docs use canonical artifact paths
[ ] active scenarios contain no legacy launcher assumptions
[ ] active state/config contains no legacy language fields
[ ] legacy forms are isolated and labeled
[ ] release run emits canonical schemas
```

## Owner

Migration and project configuration maintainers.

---

# 43. KI-SQI-009 — Exact active module inventory and status must remain synchronized

**Status:** Open  
**Evidence level:** `E0`  
**Severity:** Medium  
**Priority:** `P1`  
**Release impact:** Blocks project release if unresolved  

## Observation

Architecture documents mention representative or expected modules.

The source tree is authoritative for actual current files.

## Risk

Documentation may:

- list a module that does not exist;
- omit a public provider;
- give two modules the same responsibility;
- mark an incomplete module stable;
- retain a retired module as an entrypoint;
- omit a source file from validation selection.

## Required inventory

For every active `.gf` file, record:

```text
module name
path
layer
provider role
direct consumers
status
checkpoint
release relevance
required scenarios
```

The detailed graph belongs in:

```text
project/docs/MODULE_DEPENDENCY_MAP.md
```

## Resolution criteria

```text
[ ] source inventory generated or reviewed
[ ] project configuration includes intended source root/glob
[ ] architecture map covers every public provider
[ ] dependency map covers every public import edge
[ ] status ledger covers every nonstable module
[ ] retired files are excluded
[ ] release entrypoints are explicit
[ ] checkpoint validation passes
```

## Owner

Language architecture maintainer.

---

# 44. KI-SQI-010 — Linguistic coverage gaps must be moved from implicit knowledge into matrices

**Status:** Open  
**Evidence level:** `E0`  
**Severity:** Medium  
**Priority:** `P2`  
**Release impact:** Nonblocking only with explicit acceptance  

## Observation

A grammar may compile while important linguistic behavior remains:

- untested;
- partially implemented;
- represented by fallback;
- absent from required scenarios;
- known only to one maintainer.

## Coverage domains

At minimum review:

```text
noun number/case/definiteness
adjective agreement and placement
verb tense/person/number
object valency
pronoun forms
clitics and clitic order
negation
questions
relative clauses
coordination
prepositions and case selection
determiners
numerals
subordination
word order
punctuation
lexical irregularities
parse ambiguity
generation bounds
```

## Required behavior

Every release-relevant domain must be classified as:

```text
covered
partially covered
not covered
not applicable
blocked
```

in:

```text
project/docs/TEST_COVERAGE_MATRIX.md
```

## Resolution criteria

```text
[ ] coverage matrix contains every release-relevant domain
[ ] every covered domain links to evidence
[ ] every partial gap has an issue or ledger entry
[ ] release criteria identify accepted gaps
[ ] gold files represent approved behavior
[ ] no fallback is hidden
```

## Owner

Linguistic validation maintainer.

---

# 45. New issue template

```markdown
## KI-SQI-<NUMBER> — <Concise title>

**Status:** Open | Investigating | Blocked | Mitigated | Deferred | Resolved  
**Evidence level:** E0 | E1 | E2 | E3 | E4 | E5  
**Severity:** Critical | High | Medium | Low | Informational  
**Priority:** P0 | P1 | P2 | P3  
**Release impact:** <canonical value>

### Affected area

- `<module, scenario, gold, document, artifact, or contract>`

### Observation

Describe only what the evidence supports.

### Non-claims

State what is not yet proven.

### Reproduction

```text
exact steps
```

### Expected behavior

Describe the documented contract.

### Current behavior

Describe the reproduced result or state `Unknown`.

### Root cause

`Known`, `suspected`, or `unknown`, with evidence.

### Dependencies

- `blocked_by: KI-SQI-...`
- downstream consumers

### Workaround

Describe the mitigation or write `None approved`.

### Resolution criteria

```text
[ ] implementation criterion
[ ] direct validation
[ ] consumer validation
[ ] scenario/gold validation
[ ] documentation update
```

### Validation evidence

- run:
- GF Wordbench:
- GF:
- source revision:
- raw logs:
- scenario:
- gold:
- artifact:

### Owner

`<project role or maintainer>`

### Last reviewed

`YYYY-MM-DD`
```

---

# 46. Reproduction standard

A reproducible GF issue should record:

```text
issue ID
source revision
project version
GF Wordbench version
GF executable path or stable installation identity
GF version output
RGL revision or identity
platform
project root
entrypoint
command
working directory
timeout
stdout path
stderr path
exit code
execution state
expected artifacts
actual artifacts
```

Secrets and unrelated environment data must not be recorded.

---

# 47. Linguistic issue evidence

A linguistic issue should include at least one:

- abstract tree;
- expected Albanian form;
- actual Albanian form;
- parse input;
- expected parse count or tree;
- observed parse result;
- morphology table excerpt;
- research citation in `RESEARCH_EVIDENCE.md`;
- scenario;
- gold diff.

A prose assertion alone remains `E0`.

---

# 48. Architecture issue evidence

An architecture issue should identify:

```text
provider
public surface
consumers
contract ID
expected type/shape
actual type/shape
downstream entrypoints
```

A change affecting a lincat must update the category contract.

---

# 49. Scenario issue evidence

A scenario issue should identify:

```text
scenario ID
required/optional status
script path
entrypoint
input path
expected markers
assertions
normalization version
gold path
raw output
normalized output
```

---

# 50. PGF issue evidence

A PGF issue should identify:

```text
release entrypoint
expected PGF filename
GF command
GF version
process result
artifact existence
artifact size
SHA-256
manifest entry
required languages/functions
```

---

# 51. Root versus downstream issue policy

Create one canonical root issue for a provider failure.

Downstream consumers may be listed inside it.

Create a separate downstream issue only when it has independent project-management value, such as:

- a distinct workaround;
- a separate release criterion;
- independent failure after root repair;
- separate ownership.

Every downstream issue must reference its root blocker.

---

# 52. Duplicate policy

Before creating an issue:

1. search this registry;
2. search `STATUS_LEDGER.md`;
3. search `DECISION_LOG.md`;
4. search current run summaries;
5. inspect `blocked_by`;
6. inspect known upstream GF issues.

A duplicate is closed with the canonical replacement ID.

---

# 53. Relationship with `STATUS_LEDGER.md`

Use `KNOWN_ISSUES.md` for problems requiring investigation, correction, mitigation, or release decisions.

Use `STATUS_LEDGER.md` for implementation-state declarations such as:

```text
temporary
fallback
blocked
disabled
experimental
retired
```

A fallback may require both:

- a status-ledger entry;
- a known issue explaining why it exists and when it must be replaced.

The two documents must cross-reference each other.

---

# 54. Relationship with `DECISION_LOG.md`

Use `DECISION_LOG.md` when maintainers intentionally choose:

- a representation;
- a limitation;
- a compatibility break;
- a temporary architecture;
- a rejected alternative;
- an accepted nonblocking issue.

An issue records the problem and evidence.

A decision records the chosen response.

---

# 55. Relationship with `RELEASE_CRITERIA.md`

Every unresolved `Critical` or `High` issue must have explicit release treatment.

Possible treatment:

```text
blocking
nonblocking with approval
not applicable to release scope
upstream exception
```

Silence does not mean nonblocking.

---

# 56. Relationship with reports

A current run report may discover or reproduce an issue.

Reports do not automatically edit this registry.

The maintainer must:

1. review evidence;
2. determine root/downstream scope;
3. assign or update issue ID;
4. link the run;
5. update release impact.

---

# 57. Relationship with gold updates

A gold mismatch is not automatically a gold defect.

Possible causes:

```text
implementation regression
intended linguistic change
normalization change
GF-version change
scenario change
wrong gold
nondeterminism
```

A gold file may be updated only after the cause is decided.

The issue and decision records must explain material updates.

---

# 58. Issue discovery workflow

```text
new observation
    ↓
preserve raw evidence
    ↓
search existing issue IDs
    ↓
classify evidence level
    ↓
identify root or downstream
    ↓
assess severity and release impact
    ↓
create/update issue
    ↓
define reproduction and closure evidence
```

---

# 59. Issue triage order

Recommended order:

```text
Critical safety/data issues
    ↓
current release-run ERROR
    ↓
direct High failures
    ↓
required scenario failures
    ↓
ambiguous failures
    ↓
downstream failures
    ↓
coverage and documentation gaps
    ↓
historical verification candidates
```

---

# 60. Issue closure workflow

An issue may be marked `Resolved` only after:

```text
[ ] root cause addressed
[ ] direct provider validation passes
[ ] direct consumers pass
[ ] downstream entrypoints pass
[ ] required scenarios pass
[ ] affected gold reviewed
[ ] release impact reevaluated
[ ] status ledger updated
[ ] dependency map updated when needed
[ ] contract lock updated when needed
[ ] decision log updated when needed
[ ] current evidence linked
```

---

# 61. Not-reproducible workflow

To close as not reproducible:

```text
[ ] current source revision recorded
[ ] current GF Wordbench version recorded
[ ] current GF version recorded
[ ] original reproduction approximated faithfully
[ ] direct target tested
[ ] relevant entrypoint tested
[ ] raw evidence retained
[ ] no silent environmental fallback used
[ ] closure limitation stated
```

A later reproduction may reopen the same issue ID.

---

# 62. Reopen policy

Reopen when:

- the same root cause returns;
- closure evidence was invalid;
- a supported GF version reproduces it;
- downstream consumers were not actually validated;
- release mode exposes the same contract failure.

Create a new issue only for a distinct root cause.

---

# 63. Release triage checklist

```text
[ ] current release run exists
[ ] every non-OK required result has an issue or explicit transient explanation
[ ] direct and downstream failures are separated
[ ] every Critical/High issue has release treatment
[ ] every blocking fallback has an issue
[ ] required scenario failures have issue IDs
[ ] gold mismatches have reviewed causes
[ ] PGF failures have issue IDs
[ ] manifest failures have issue IDs
[ ] known upstream GF blockers are identified
[ ] accepted limitations appear in release notes
```

---

# 64. Documentation quality checklist

```text
[ ] issue title states one problem
[ ] observation is evidence-based
[ ] non-claims prevent overstatement
[ ] status is canonical
[ ] evidence level is correct
[ ] severity is justified
[ ] priority is justified
[ ] release impact is explicit
[ ] root/downstream relationship is explicit
[ ] reproduction is actionable
[ ] resolution criteria are testable
[ ] owner is assigned
[ ] last-reviewed date is current
[ ] linked paths are project-relative
```

---

# 65. Anti-drift checks

The project checker should eventually detect:

- an issue marked resolved while its required scenario fails;
- a blocking ledger entry with no known issue;
- an unresolved High issue absent from release criteria;
- an issue referencing a missing module;
- an issue referencing a retired scenario as active;
- duplicate issue IDs;
- invalid status or severity;
- missing owner;
- missing resolution criteria;
- stale unresolved placeholders;
- a downstream issue missing `blocked_by`;
- a gold update without issue or decision reference when material;
- a release report containing an unregistered direct failure.

---

# 66. Historical-fixture policy

Historical and synthetic evidence is retained because it proves framework behavior.

It must be labeled as one of:

```text
historical
synthetic
migration
example
current
```

Only `current` evidence can independently establish an active project defect.

A test fixture may remain valuable after its project issue is closed.

---

# 67. Upstream GF issues

When the root cause is believed to be upstream GF:

- retain a local project issue;
- record GF version;
- record minimal reproduction;
- link the upstream issue identifier when available;
- document affected project features;
- document supported workaround;
- test the workaround;
- define the GF version or capability that resolves the blocker.

Do not classify every `Internal error` as upstream automatically.

---

# 68. Accepted limitations

An accepted limitation must specify:

```text
affected construction
user-visible consequence
scope
reason
evidence
release acceptance
planned review
```

Accepted does not mean invisible.

It belongs in release notes when relevant.

---

# 69. Security and integrity issues

Immediately use `Critical` when evidence suggests:

- source or gold modification during normal validation;
- path escape;
- arbitrary command execution;
- secret disclosure;
- manifest claiming incorrect artifacts;
- release PGF hash mismatch;
- project identity replaced silently.

Preserve evidence without publishing secrets.

---

# 70. Prohibited issue-registry behavior

The following are prohibited:

- declaring a current defect from synthetic fixtures alone;
- marking an issue resolved because one file compiles;
- treating downstream failures as independent roots automatically;
- using free-form status values;
- omitting release impact;
- hiding fallbacks outside the status ledger;
- updating gold to close an unexplained mismatch;
- deleting resolved issue history;
- reusing issue IDs;
- assigning a root cause without evidence;
- listing a project issue only in private notes;
- marking a required scenario failure nonblocking silently;
- closing an upstream issue without testing the supported GF version;
- recording secrets in reproduction data;
- using this file as a substitute for raw run evidence.

---

# 71. Final invariants

1. Every active issue has a stable `KI-SQI-*` ID.
2. Historical fixtures do not prove current defects.
3. Evidence level is explicit.
4. Severity and priority remain separate.
5. Release impact is explicit.
6. Root and downstream failures remain distinct.
7. Every blocking fallback appears in both the ledger and issue registry.
8. Every required scenario failure has reviewable issue evidence.
9. Gold mismatches are investigated before gold updates.
10. Current source, GF Wordbench, GF, and RGL identities are recorded for reproductions.
11. Resolved issues validate direct and downstream consumers.
12. Breaking fixes update contracts and decisions.
13. Active project placeholders block release.
14. Entrypoints, scenarios, golds, and PGF targets must agree.
15. Module inventory and status must remain synchronized.
16. Accepted linguistic limitations are visible.
17. Upstream GF attribution requires a minimal reproduction.
18. Current release readiness requires current release evidence.
19. Issue history is retained.
20. The registry never replaces raw logs, summaries, manifests, scenarios, or gold files.

---

# 72. Final rule

The known-issues registry follows one evidence chain:

```text
observation
    → preserved evidence
    → current reproduction
    → root/downstream classification
    → severity and release impact
    → owned corrective action
    → direct and consumer validation
    → scenario/gold/PGF verification
    → documented resolution
```

Until that chain reaches current reproduction, a historical diagnostic remains a verification candidate—not a confirmed defect in the current Albanian grammar.
