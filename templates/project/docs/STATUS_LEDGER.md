# GF Wordbench Project Template — Status Ledger

**Document ID:** `GF-WB-PROJECT-STATUS-LEDGER`  
**Status:** Normative project template  
**Applies to:** One active GF language project created from `templates/project/`  
**Template owner:** GF Wordbench maintainers  
**Project owner after initialization:** `<PROJECT_OWNER>`  
**Project ID:** `<PROJECT_ID>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**GF module suffix:** `<GF_SUFFIX>`  
**Project root:** `<PROJECT_ROOT>`  
**Configuration authority:** `project/project.toml`  
**Contract authority:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Validation authority:** `project/docs/VALIDATION_SPEC.md`  
**Known-issue authority:** `project/docs/KNOWN_ISSUES.md`  
**Release authority:** `project/docs/RELEASE_CRITERIA.md`  
**Decision authority:** `project/docs/DECISION_LOG.md`  
**Template version:** `1.0.0`  
**Last reviewed:** `<YYYY-MM-DD>`

---

## 1. Purpose

This document is the canonical project ledger for implementation states that are not fully stable and complete.

It records:

- scaffolding;
- temporary implementations;
- fallbacks;
- warnings;
- blocked work;
- disabled behavior;
- experimental behavior;
- deprecated behavior;
- release blockers;
- accepted limitations;
- migration-only states;
- incomplete validation coverage;
- incomplete documentation;
- incomplete entrypoints;
- incomplete scenarios;
- incomplete gold coverage;
- incomplete artifacts;
- known ownership and exit conditions.

The ledger exists to prevent a compiling placeholder, workaround or partially implemented module from being presented as stable project behavior.

The core rule is:

> Every non-stable project state must be visible, owned, validated and tied to an explicit exit condition or acceptance decision.

---

## 2. Template-use rule

This file under:

```text
templates/project/docs/STATUS_LEDGER.md
```

remains generic.

When initializing an active project, copy it to:

```text
project/docs/STATUS_LEDGER.md
```

Then:

1. replace all required metadata placeholders;
2. remove example rows that do not apply;
3. inventory every non-stable source, scenario, gold, artifact and documentation state;
4. assign stable ledger IDs;
5. assign one owner;
6. define validation impact;
7. define release impact;
8. define evidence;
9. define an exit condition;
10. synchronize with known issues, decisions, contracts and release criteria.

The active copy MUST NOT retain unresolved required placeholders while claiming release readiness.

---

## 3. Intentional placeholders

The template intentionally uses placeholders such as:

```text
<PROJECT_OWNER>
<PROJECT_ID>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<PROJECT_ROOT>
<MODULE>
<FILE>
<ENTRYPOINT>
<SCENARIO_ID>
<GOLD_FILE>
<ARTIFACT>
<REQUIREMENT_ID>
<CONTRACT_ID>
<DECISION_ID>
<ISSUE_ID>
<OWNER>
<MILESTONE>
<YYYY-MM-DD>
```

Rules:

- placeholders are valid in `templates/project/`;
- placeholders are invalid in completed active ledger entries;
- a placeholder must never be interpreted as an active module or requirement;
- strict project checks should reject unresolved placeholders in the active copy;
- examples must remain clearly labeled as examples.

---

## 4. Scope

The ledger covers non-stable states affecting:

```text
project identity
project configuration
GF source modules
module ownership
lincat structures
morphology
syntax
constructors
structural vocabulary
extension families
entrypoints
checkpoints
scenarios
scenario inputs
normalization
gold files
.gfo artifacts
.pgf artifacts
documentation
validation coverage
release gates
tool compatibility
migrations
```

---

## 5. Out of scope

This ledger does not replace:

- `KNOWN_ISSUES.md` for defect analysis and current limitations;
- `DECISION_LOG.md` for durable architectural or linguistic choices;
- `VALIDATION_SPEC.md` for required validation behavior;
- `TEST_COVERAGE_MATRIX.md` for requirement-to-evidence mapping;
- `RELEASE_CRITERIA.md` for final release gates;
- `INTERFILE_CONTRACT_LOCK.md` for provider/consumer contracts;
- issue-tracker tickets for implementation planning;
- source comments for local implementation detail.

A ledger entry may link to all of these.

---

## 6. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless an explicit reason is documented.
- **MAY**: optional.
- **LEDGER ENTRY**: one tracked non-stable project state.
- **OWNER**: maintainer or team accountable for the entry.
- **AFFECTED OBJECT**: module, file, scenario, artifact, document or contract affected by the state.
- **EXIT CONDITION**: objective condition required before the entry can be closed or promoted.
- **RELEASE BLOCKER**: state that prevents release readiness.
- **WORKAROUND**: temporary operational method reducing impact without resolving the cause.
- **FALLBACK**: alternate implementation used when the preferred implementation is unavailable or incomplete.
- **SCAFFOLDING**: incomplete structure intended to support future implementation.
- **PROMOTION**: transition from a non-stable state to stable.
- **RETIREMENT**: removal of the governed behavior.
- **ACCEPTANCE**: deliberate decision that a limitation is permitted under a defined release policy.
- **EVIDENCE**: current compile, scenario, gold, artifact, review or contract proof.

---

## 7. Canonical ledger statuses

Canonical statuses:

```text
stable
experimental
temporary
fallback
warning
blocked
disabled
deprecated
retired
```

Only non-stable states normally need active ledger entries.

A `stable` entry may be retained briefly for closure history or audit, but stable implementation should primarily be described by architecture and specifications.

---

## 8. `stable`

Meaning:

- implementation and contracts are complete for the declared scope;
- required consumers validate;
- required scenarios pass;
- required golds match;
- release policy accepts the state;
- no unresolved workaround remains.

A state MUST NOT be promoted to `stable` solely because one source file compiles.

---

## 9. `experimental`

Meaning:

- behavior exists for evaluation;
- compatibility is not promised;
- public use is limited or explicitly experimental;
- validation coverage may be partial but is documented;
- release inclusion is conditional.

Required fields:

```text
experiment purpose
scope
consumers
validation plan
promotion or retirement criteria
release exposure
```

---

## 10. `temporary`

Meaning:

- implementation is intentionally short-lived;
- a replacement is planned;
- temporary behavior must not become permanent silently.

Required fields:

```text
reason
replacement plan
owner
target milestone
exit condition
```

A temporary state without a target or exit condition is invalid.

---

## 11. `fallback`

Meaning:

- alternate behavior is used when the preferred behavior is unavailable;
- the fallback is visible and documented;
- semantic differences are known;
- selection rules are deterministic.

Required fields:

```text
preferred provider
fallback provider
selection condition
semantic difference
validation evidence
release policy
removal condition
```

A fallback MUST NOT be presented as equivalent when it is not.

---

## 12. `warning`

Meaning:

- implementation is usable;
- a known risk, limitation or suspicious condition remains;
- the warning is visible in validation or release review;
- it may or may not block release.

A warning entry must state:

```text
risk
affected scope
detection method
release impact
escalation trigger
```

---

## 13. `blocked`

Meaning:

- required work cannot proceed because a prerequisite is unresolved;
- the blocking owner and dependency are known;
- dependent validation is skipped or downstream;
- release impact is explicit.

Required fields:

```text
blocking dependency
blocked work
owner of blocker
owner of blocked work
evidence
unblock condition
```

---

## 14. `disabled`

Meaning:

- behavior exists or is planned but is intentionally excluded from active execution or release;
- selection logic is explicit;
- consumers do not rely on it accidentally.

Required fields:

```text
disabled scope
reason
activation condition
configuration control
release impact
```

Disabled behavior MUST NOT be selected implicitly by filesystem presence.

---

## 15. `deprecated`

Meaning:

- behavior remains supported temporarily;
- replacement exists or is planned;
- consumers must migrate;
- removal policy is documented.

Required fields:

```text
replacement
first deprecated version
warning behavior
consumer list
migration steps
planned removal
```

---

## 16. `retired`

Meaning:

- behavior has been removed from the active project;
- active consumers and configuration no longer reference it;
- historical evidence is preserved where needed;
- identifiers are not reused.

Retired entries may remain in the ledger history.

---

## 17. Ledger identifiers

Ledger IDs use:

```text
STAT-<DOMAIN>-<NUMBER>
```

Recommended domains:

```text
CONFIG
SOURCE
MODULE
LINCAT
MORPH
SYNTAX
LEXICON
STRUCT
EXT
ENTRY
CHECKPOINT
SCENARIO
INPUT
NORM
GOLD
ARTIFACT
PGF
DOC
TEST
TOOL
RELEASE
MIGRATION
```

Examples:

```text
STAT-MORPH-001
STAT-ENTRY-002
STAT-GOLD-003
```

Rules:

- IDs are unique;
- IDs are never reused;
- domain reflects the primary owner;
- cross-domain impacts are listed separately;
- closed or retired IDs remain discoverable;
- renaming a title does not change the ID.

---

## 18. Required entry fields

Every active ledger entry must contain:

```text
ID
title
status
summary
affected objects
owner
introduced date or provenance
reason
current behavior
expected stable behavior
consumers
validation impact
release impact
risk
workaround
evidence
dependencies
exit condition
target milestone
related requirements
related contracts
related decisions
related known issues
last reviewed
```

Use `not applicable` explicitly when a field genuinely does not apply.

Do not omit required fields silently.

---

## 19. Compact ledger table

Maintain a compact index near the top of the active project copy.

Template:

| ID | Status | Object | Summary | Owner | Release blocker | Target |
|---|---|---|---|---|---:|---|
| `STAT-<DOMAIN>-001` | `<status>` | `<FILE/MODULE>` | `<summary>` | `<OWNER>` | yes/no/conditional | `<MILESTONE>` |

Remove the example row in the active project.

The detailed entry remains authoritative.

---

## 20. Detailed entry template

```markdown
## STAT-<DOMAIN>-<NUMBER> — <Title>

**Status:** experimental | temporary | fallback | warning | blocked | disabled | deprecated | retired  
**Owner:** <OWNER>  
**Introduced:** <YYYY-MM-DD or provenance>  
**Last reviewed:** <YYYY-MM-DD>  
**Target milestone:** <MILESTONE>  
**Release blocker:** yes | no | conditional  
**Affected project version:** <version or not assigned>

### Summary

<One concise statement of the state.>

### Affected objects

- `<FILE or MODULE>`;
- `<SCENARIO_ID>`;
- `<GOLD_FILE>`;
- `<ARTIFACT>`;
- `<DOCUMENT>`.

### Reason

<Why the state exists.>

### Current behavior

<What the project currently does.>

### Expected stable behavior

<What the final accepted implementation must do.>

### Consumers and dependencies

- Provider: `<MODULE or FILE>`;
- Direct consumers: `<consumers>`;
- Blocking dependency: `<dependency or none>`;
- Downstream entrypoints: `<entrypoints>`.

### Validation impact

- Requirement(s): `<REQUIREMENT_ID>`;
- Checkpoint(s): `<checkpoint>`;
- Scenario(s): `<SCENARIO_ID>`;
- Gold(s): `<GOLD_FILE>`;
- Current expected status: `<OK/FAIL/ERROR/SKIPPED or condition>`.

### Release impact

<State exactly how the entry affects release.>

### Risk

<Correctness, compatibility, linguistic, security or maintenance risk.>

### Workaround

<Temporary workaround or not applicable.>

### Evidence

- Source: `<path>`;
- Raw evidence: `<path or run>`;
- Structured result: `<result>`;
- Contract review: `<CONTRACT_ID>`;
- Manual review: `<record or not applicable>`.

### Exit condition

<Objective conditions required to close, promote or retire the entry.>

### Closure evidence required

- <compile/scenario/gold/artifact/review>;

### Related records

- Contract: `<CONTRACT_ID>`;
- Requirement: `<REQUIREMENT_ID>`;
- Decision: `<DECISION_ID>`;
- Known issue: `<ISSUE_ID>`;
- Coverage row: `<reference>`;
```

---

## 21. Entry creation rule

Create a ledger entry when any of the following is true:

- a module contains scaffolding;
- a public constructor is incomplete;
- a lincat is temporarily simplified;
- a fallback provider is active;
- a required function is missing;
- a scenario is disabled;
- required gold is missing;
- normalization is provisional;
- expected PGF is not yet defined;
- a checkpoint is blocked;
- a source path is temporary;
- a tool version is experimental;
- documentation describes planned rather than current behavior;
- validation coverage is incomplete;
- a release exception exists;
- a deprecated module remains in use;
- a workaround changes normal project behavior.

Do not wait until release preparation to create the entry.

---

## 22. Entry not required

A ledger entry is normally unnecessary for:

- private refactoring with unchanged behavior;
- completed stable implementation;
- ordinary local variable names;
- formatting changes;
- a transient developer note not committed;
- a resolved defect with no remaining limitation;
- an issue fully represented by a current known issue and no implementation state.

When uncertain, prefer a ledger entry if release or consumer behavior could be misunderstood.

---

## 23. Relationship to known issues

`KNOWN_ISSUES.md` records defects and limitations.

The ledger records implementation state.

A single problem may require both.

Example:

```text
Known issue:
  parse ambiguity exceeds accepted policy

Ledger state:
  parser-disambiguation helper is experimental
```

Rules:

- every linked ID must exist;
- release-blocking values must agree;
- closing the issue does not automatically promote the ledger state;
- promoting the state does not automatically close every related issue.

---

## 24. Relationship to decision log

Use `DECISION_LOG.md` when a non-stable state reflects a durable choice.

Examples:

- deliberate fallback accepted for one release;
- separate experimental entrypoint;
- supported dialect variant policy;
- temporary public API compatibility wrapper;
- retirement of a scaffolding module.

The ledger describes current state.

The decision log explains why the policy exists.

---

## 25. Relationship to contract lock

Any non-stable state affecting another file must be represented in the project interfile contract lock.

Examples:

```text
temporary lincat field
fallback morphology provider
conditional extension coordinator
deprecated entrypoint
disabled scenario
provisional PGF name
```

The ledger and lock must agree on:

- provider;
- consumers;
- status;
- invariants;
- validation evidence;
- forbidden behavior.

---

## 26. Relationship to validation specification

Every active entry must identify how validation exposes the state.

Possible methods:

```text
direct compile
checkpoint compile
entrypoint compile
native scenario
missing-function inspection
gold mismatch
artifact absence
configuration check
documentation check
manual review
```

A state that is invisible to validation is at high risk of becoming permanent silently.

---

## 27. Relationship to coverage matrix

Every release-significant entry should map to one or more coverage rows.

The coverage matrix should show:

```text
requirement
affected provider
checkpoint
scenario
gold/assertion
current status
ledger ID
release impact
```

A release-blocking ledger entry without coverage is incomplete.

---

## 28. Relationship to release criteria

`RELEASE_CRITERIA.md` defines whether a status blocks release.

Default policy:

| Status | Default release impact |
|---|---|
| `experimental` | conditional or blocking if included in release surface |
| `temporary` | blocking unless explicitly accepted |
| `fallback` | blocking unless explicitly accepted and validated |
| `warning` | project-defined |
| `blocked` | blocking when required scope is affected |
| `disabled` | blocking when required scope is disabled |
| `deprecated` | non-blocking during valid support window unless policy says otherwise |
| `retired` | non-blocking if all references removed |
| `stable` | non-blocking |

The active project must define any deviations.

---

## 29. Release-blocker field

Canonical values:

```text
yes
no
conditional
```

### `yes`

Release cannot proceed while the entry is active.

### `no`

The entry is accepted as non-blocking for the current release scope.

### `conditional`

Blocking depends on a named condition.

A conditional entry must define:

- condition;
- how it is evaluated;
- evidence;
- behavior when true;
- behavior when false.

---

## 30. Promotion to stable

An entry may be promoted to stable only when:

```text
[ ] Expected behavior is implemented
[ ] Provider contract is current
[ ] Direct consumers are reviewed
[ ] Downstream entrypoints validate
[ ] Required checkpoints pass
[ ] Required scenarios pass
[ ] Required golds match
[ ] Required artifacts verify
[ ] Known issues are updated
[ ] Coverage matrix is updated
[ ] Decision log is updated when applicable
[ ] Release impact is reassessed
[ ] Closure evidence is recorded
```

Compilation alone is insufficient.

---

## 31. Retirement

Retire an entry when the affected behavior is removed.

Required retirement checks:

```text
[ ] Source/module removed or no longer active
[ ] Configuration references removed
[ ] Imports/consumers removed
[ ] Scenario references removed or migrated
[ ] Golds removed or migrated deliberately
[ ] Contracts retired
[ ] Documentation updated
[ ] Artifacts no longer expected
[ ] Identifier not reused
[ ] Historical rationale preserved
```

---

## 32. Blocking dependencies

A blocked entry must name the actual blocker.

Avoid:

```text
Blocked by other work.
```

Preferred:

```text
Blocked by STAT-LINCAT-002 because <ENTRYPOINT> requires the missing agreement field.
```

Blocked work must not be classified as an independent direct failure when current evidence identifies the failed prerequisite.

---

## 33. Workarounds

A workaround must state:

- exact activation method;
- scope;
- semantic difference;
- safety constraints;
- consumer impact;
- whether release uses it;
- removal condition.

Workarounds MUST NOT:

- update gold automatically;
- suppress raw evidence;
- convert `ERROR` to `OK`;
- hide missing functions;
- accept stale artifacts;
- bypass required checkpoints silently;
- make GUI state project authority.

---

## 34. Fallback selection

Fallback selection must be deterministic.

Selection may depend on:

```text
project configuration
entrypoint role
explicit capability
documented version condition
explicit experimental mode
```

It must not depend on:

- which provider happens to compile first;
- filesystem order;
- best matching gold;
- previous run output;
- GUI-only state;
- hidden environment variables.

---

## 35. Scaffolding

Scaffolding must:

- be named clearly;
- have limited consumers;
- not be selected as release entrypoint without an explicit decision;
- expose incomplete behavior through validation;
- have a promotion or retirement plan;
- remain listed in architecture/dependency documentation.

A scaffolding module that becomes stable should normally be renamed or its stable role explicitly approved.

---

## 36. Temporary lincats

A temporary lincat entry must document:

```text
current shape
expected shape
missing fields
affected constructors
affected consumers
compile behavior
scenario behavior
migration plan
```

Flattening a structured value to `Str` solely to compile is a release-significant ledger state and contract change.

---

## 37. Missing functions

A missing-function state must identify:

```text
entrypoint
missing function names or bounded inventory
reason
consumer impact
scenario/assertion
release policy
completion plan
```

Do not hide missing functions as scan noise or warnings unless the release policy explicitly permits the exact set.

---

## 38. Experimental entrypoints

An experimental entrypoint must define:

- purpose;
- modules included;
- public surface;
- allowed consumers;
- scenario coverage;
- missing-function policy;
- PGF exclusion or inclusion;
- compatibility promise;
- promotion criteria.

It must not be confused with the configured stable release entrypoint.

---

## 39. Disabled scenarios

A disabled scenario entry must identify:

```text
scenario ID
script path
reason
requiredness before disablement
coverage lost
replacement assertion
release impact
reenable condition
```

A required scenario cannot be disabled and still count as passing.

---

## 40. Missing golds

A missing required gold entry must identify:

- scenario ID;
- expected gold path;
- normalization profile/version;
- actual output availability;
- review owner;
- release impact;
- creation exit condition.

Normal validation MUST NOT auto-create the gold.

---

## 41. Provisional normalization

A provisional normalization entry must identify:

```text
profile ID
current version
unstable output source
lossy rules
unknown output policy
affected golds
migration/review plan
```

A provisional profile should not support final release exact comparison unless explicitly accepted.

---

## 42. Tool compatibility

An experimental or blocked GF-version state must identify:

```text
GF version
platform
compile evidence
scenario evidence
diagnostic parser impact
normalization impact
PGF impact
supported/experimental status
```

One successful version probe is insufficient.

---

## 43. Documentation gaps

A documentation ledger entry is required when:

- a public module lacks an owner;
- a shared lincat lacks specification;
- a scenario has no documented purpose;
- a release criterion has no evidence mapping;
- a fallback exists only in comments;
- active behavior differs from project docs.

Documentation gaps may block release when they affect maintainability, reproducibility or contract interpretation.

---

## 44. Validation gaps

A validation-gap entry must identify:

```text
unproven requirement
affected behavior
current evidence
missing evidence
risk
planned scenario/test
release impact
```

“Not tested” is not equivalent to “works.”

---

## 45. Artifact gaps

An artifact-gap entry may cover:

- missing current `.gfo`;
- undefined expected `.pgf`;
- stale artifact risk;
- missing manifest role;
- unverified source fingerprint;
- incomplete artifact integrity check.

A release-required artifact gap blocks release by default.

---

## 46. Security states

Security-related ledger entries may include:

- unreviewed shell escape;
- path traversal risk;
- unbounded generation;
- secret leakage;
- unsafe cleanup;
- untrusted symlink behavior;
- executable scenario provenance gap.

Security entries are release blockers unless a formal security review documents otherwise.

---

## 47. Entry evidence hierarchy

Preferred evidence order:

1. current project configuration;
2. current source;
3. current contract lock;
4. current validation result;
5. current raw evidence;
6. current scenario/gold result;
7. current artifact/manifest;
8. current manual review;
9. historical evidence.

Historical evidence alone must not define current state.

---

## 48. Dates and provenance

Use ISO dates:

```text
YYYY-MM-DD
```

When the original introduction date is unknown, use:

```text
Introduced: before ledger initialization; exact date unknown
```

Do not invent a historical date.

`Last reviewed` records current review, not implementation origin.

---

## 49. Owners

Owners should be roles or named maintainers under project policy.

Examples:

```text
project architecture maintainers
morphology maintainers
syntax maintainers
validation maintainers
release maintainers
toolchain maintainers
```

An entry without an owner is incomplete.

---

## 50. Target milestones

Target milestone examples:

```text
before project v1.0.0
before next release candidate
after <ENTRYPOINT> migration
after GF <VERSION> support
before enabling <SCENARIO_ID>
```

Avoid vague targets:

```text
later
eventually
when possible
```

---

## 51. Risk categories

Recommended risk categories:

```text
linguistic correctness
type/contract compatibility
source architecture
release integrity
diagnostic reliability
artifact freshness
security
portability
performance
maintainability
documentation
```

An entry may have multiple risks.

---

## 52. Closure types

An entry closes through one of:

```text
promoted to stable
retired
superseded by another entry
converted to accepted permanent limitation
migrated to another provider
no longer applicable after scope change
```

The closure type and evidence must be recorded.

---

## 53. Accepted permanent limitations

A permanent limitation must not remain labeled `temporary`.

To accept a limitation permanently:

1. create or update a decision entry;
2. update language/project scope;
3. update validation specification;
4. update known issues;
5. update release criteria;
6. update golds only if accepted semantic output changes;
7. set an appropriate status such as `warning`, `disabled` or `retired`;
8. record project-version impact.

---

## 54. Ledger change workflow

When a state changes:

```text
[ ] Update detailed ledger entry
[ ] Update compact index
[ ] Update source comments when applicable
[ ] Update project configuration when applicable
[ ] Update contract lock
[ ] Update architecture/dependency map
[ ] Update validation specification
[ ] Update coverage matrix
[ ] Update known issues
[ ] Update decision log
[ ] Update release criteria
[ ] Update scenarios/inputs/golds
[ ] Run required validation
[ ] Record closure or new evidence
```

No isolated status change is complete when consumers or release gates are affected.

---

## 55. Review cadence

Review the ledger:

- before every release;
- before every release candidate;
- after a major checkpoint change;
- after entrypoint changes;
- after GF-version changes;
- after gold-profile major changes;
- after major bug fixes;
- after project migration;
- after scaffolding promotion or retirement;
- at scheduled project maintenance reviews.

---

## 56. Required release review

Before release:

```text
[ ] Every active entry reviewed
[ ] Every release-blocker value confirmed
[ ] Conditional entries evaluated
[ ] No owner missing
[ ] No exit condition missing
[ ] No unresolved active placeholders
[ ] No hidden fallback in source
[ ] No undocumented disabled scenario
[ ] No missing required gold
[ ] No undefined release artifact
[ ] No stale known-issue link
[ ] No retired object referenced actively
[ ] Closure evidence verified
```

---

## 57. Compact active ledger template

Replace this table in the active project.

| ID | Status | Affected object | Validation impact | Release blocker | Owner | Exit condition |
|---|---|---|---|---:|---|---|
| `STAT-MODULE-001` | temporary | `<MODULE>` | `<REQUIREMENT_ID>` | yes | `<OWNER>` | `<condition>` |
| `STAT-SCENARIO-001` | disabled | `<SCENARIO_ID>` | `<coverage lost>` | conditional | `<OWNER>` | `<condition>` |
| `STAT-GOLD-001` | blocked | `<GOLD_FILE>` | `<comparison unavailable>` | yes | `<OWNER>` | `<condition>` |

These rows are examples only.

---

## 58. Example detailed entry — scaffolding

The following is a template example and must be replaced or removed.

```markdown
## STAT-EXT-001 — Extension coordinator remains scaffolding

**Status:** temporary  
**Owner:** <OWNER>  
**Introduced:** before ledger initialization; exact date unknown  
**Last reviewed:** <YYYY-MM-DD>  
**Target milestone:** before <MILESTONE>  
**Release blocker:** conditional

### Summary

`<MODULE>` provides incomplete extension wiring and is not stable.

### Affected objects

- `<SOURCE_ROOT>/<MODULE>.gf`;
- `<ENTRYPOINT>`;
- `<SCENARIO_ID>`.

### Reason

Required extension providers are incomplete.

### Current behavior

The module compiles only with placeholder or partial implementations.

### Expected stable behavior

Every required extension constructor is supplied by documented providers and validated through the release entrypoint.

### Consumers and dependencies

- Provider: `<MODULE>`;
- Consumers: `<consumers>`;
- Blocking dependency: `<dependency>`;
- Downstream entrypoint: `<ENTRYPOINT>`.

### Validation impact

- Requirement: `<REQUIREMENT_ID>`;
- Checkpoint: `<CHECKPOINT_MODULE>`;
- Scenario: `<SCENARIO_ID>`;
- Current expected status: `FAIL` or `SKIPPED` according to dependency evidence.

### Release impact

Blocks release when `<ENTRYPOINT>` includes this module.

### Risk

Incomplete public behavior may be mistaken for stable support.

### Workaround

Exclude the experimental entrypoint from the release surface.

### Evidence

- Contract: `<CONTRACT_ID>`;
- Scenario: `<SCENARIO_ID>`;
- Raw evidence: `<run path>`.

### Exit condition

All required extension providers compile, required scenarios pass, golds match and the entrypoint is approved.

### Related records

- Decision: `<DECISION_ID>`;
- Known issue: `<ISSUE_ID>`;
```

---

## 59. Example detailed entry — fallback lincat

Template example:

```markdown
## STAT-LINCAT-001 — Temporary simplified lincat

**Status:** fallback  
**Owner:** <OWNER>  
**Release blocker:** yes

### Summary

`<CATEGORY>` currently uses a simplified record that omits required fields.

### Current behavior

`lincat <CATEGORY> = {s : Str}`

### Expected stable behavior

Use the documented project lincat with all required agreement and structural fields.

### Risk

Consumers may lose agreement, case, definiteness or complement behavior.

### Exit condition

Provider and all consumers compile with the final shape; representative parse/linearization scenarios pass; golds are reviewed.
```

This example must not be copied as an accepted implementation.

---

## 60. Example detailed entry — missing gold

Template example:

```markdown
## STAT-GOLD-001 — Required scenario has no approved gold

**Status:** blocked  
**Owner:** <OWNER>  
**Release blocker:** yes

### Summary

Scenario `<SCENARIO_ID>` executes but no reviewed gold exists.

### Current behavior

Actual normalized output is produced, but exact accepted behavior is not established.

### Expected stable behavior

A reviewed gold with matching scenario ID, profile ID and normalization version exists.

### Exit condition

Raw output and normalized output are reviewed; gold is created explicitly and atomically; comparison passes.
```

---

## 61. Example detailed entry — experimental GF version

Template example:

```markdown
## STAT-TOOL-001 — GF version support is experimental

**Status:** experimental  
**Owner:** <OWNER>  
**Release blocker:** conditional

### Summary

GF `<VERSION>` has passed version probing but not the full project compatibility matrix.

### Required completion

- representative compile;
- checkpoints;
- required scenarios;
- diagnostic parser review;
- normalization review;
- PGF build;
- platform evidence.

### Release impact

Release may use only a fully supported GF version unless an explicit project decision permits this version.
```

---

## 62. Automated ledger checks

Recommended conceptual command:

```text
gf-wordbench project status check
```

Strict mode:

```text
gf-wordbench project status check --strict
```

The checker should verify:

1. ledger IDs are unique;
2. statuses are canonical;
3. every active entry has an owner;
4. every active entry has an exit condition;
5. release blocker is explicit;
6. affected paths/modules exist or are explicitly planned;
7. referenced requirements exist;
8. referenced contracts exist;
9. referenced decisions exist;
10. referenced known issues exist;
11. referenced scenarios/golds exist where expected;
12. retired objects are not active;
13. stable promotion has closure evidence;
14. active project contains no unresolved required placeholders;
15. generic template contains no active-language facts.

Actual command availability belongs to the CLI reference.

---

## 63. Suggested tests

Recommended tests:

```text
tests/project/
├── test_status_ledger_schema.py
├── test_status_ledger_ids.py
├── test_status_ledger_links.py
├── test_status_ledger_release_impact.py
├── test_status_ledger_placeholders.py
├── test_status_ledger_source_consistency.py
├── test_status_ledger_contract_consistency.py
└── test_status_ledger_template_separation.py
```

---

## 64. ID tests

Required cases:

- valid domain/number;
- duplicate ID;
- malformed ID;
- reused retired ID;
- deterministic index order;
- detailed entry missing from compact index;
- compact row missing detailed entry.

---

## 65. Status tests

Required cases:

- canonical status;
- unknown status;
- stable promotion without evidence;
- conditional blocker without condition;
- temporary entry without milestone;
- fallback without selection rule;
- deprecated entry without replacement;
- blocked entry without blocker;
- disabled scenario still configured required.

---

## 66. Link tests

Required cases:

- valid requirement link;
- missing requirement;
- valid contract link;
- missing contract;
- valid decision link;
- missing decision;
- valid issue link;
- missing issue;
- valid scenario/gold link;
- retired target still referenced.

---

## 67. Release-policy tests

Required cases:

```text
required blocked entry → release fails
required temporary entry → release fails by default
accepted warning → project policy
conditional entry true → apply blocking rule
conditional entry false → non-blocking
retired entry with no references → non-blocking
disabled required scenario → release fails
missing required gold entry → release fails
```

---

## 68. Placeholder tests

Template tests should require intentional placeholders.

Active-project strict checks should reject:

```text
<PROJECT_ID>
<LANGUAGE_NAME>
<MODULE>
<ENTRYPOINT>
<SCENARIO_ID>
<GOLD_FILE>
<OWNER>
<YYYY-MM-DD>
```

when they appear in active ledger metadata or active entries.

---

## 69. Source consistency checks

The checker should detect:

- scaffolding-like filenames absent from the ledger;
- fallback comments absent from the ledger;
- disabled source files absent from the ledger;
- deprecated modules absent from the ledger;
- active ledger object missing from source/configuration;
- module renamed without ledger update;
- temporary helper consumed by undocumented modules.

Heuristics produce findings, not automatic linguistic conclusions.

---

## 70. Scenario consistency checks

Detect:

- disabled scenario still listed as required;
- blocked scenario not referenced in validation coverage;
- temporary scenario with permanent gold but no rationale;
- missing required scenario with no ledger entry;
- scenario marked stable while marker/timeout policy fails;
- scenario entrypoint changed without ledger/decision review.

---

## 71. Gold consistency checks

Detect:

- required gold missing without ledger entry;
- blocked gold still reported as matching;
- provisional profile treated as stable;
- gold update while entry remains unresolved without review;
- retired scenario gold still active;
- gold path renamed without migration;
- release gold with unresolved placeholder.

---

## 72. Artifact consistency checks

Detect:

- expected PGF undefined;
- current PGF missing;
- stale artifact accepted;
- temporary artifact name in release configuration;
- artifact role absent from manifest policy;
- disabled producer still expected to create an artifact;
- retired entrypoint still named as PGF producer.

---

## 73. Documentation consistency checks

Detect:

- architecture calls a ledger object stable while ledger says temporary;
- validation spec requires a disabled scenario without exception;
- release criteria ignore a blocking entry;
- known issue and ledger disagree on release impact;
- decision log accepts a state ledger still calls open;
- contract lock says active while ledger says retired;
- coverage matrix omits a blocking entry.

---

## 74. Ledger drift indicators

Drift exists when:

- non-stable code has no entry;
- an entry has no owner;
- an entry has no exit condition;
- a temporary state has no target;
- a fallback has no deterministic selection rule;
- a blocked entry has no blocker;
- a disabled scenario remains required;
- a missing gold is treated as success;
- a scaffold is described as stable;
- source comments and ledger disagree;
- known issue and ledger disagree on release blocking;
- release criteria omit an active blocker;
- a retired ID is reused;
- active project contains template placeholders;
- template contains active-language facts;
- closure occurs without validation evidence;
- one file is updated without consumers/contracts/docs;
- historical evidence is treated as current status;
- GUI state suppresses a ledger blocker.

Every drift indicator requires correction before release.

---

## 75. Active ledger initialization workflow

When creating a project:

1. inventory source files;
2. search for scaffolding, placeholders and fallback comments;
3. inspect project configuration gaps;
4. inspect entrypoints/checkpoints;
5. inspect scenario registry;
6. inspect missing scenarios;
7. inspect missing golds;
8. inspect expected artifacts;
9. inspect documentation placeholders;
10. create ledger entries;
11. assign owners;
12. assign release impact;
13. define exit conditions;
14. link requirements/contracts/issues/decisions;
15. execute baseline validation;
16. update evidence;
17. review release eligibility.

---

## 76. Migration workflow

When migrating an existing project:

```text
[ ] Import old temporary-state records
[ ] Distinguish current from historical states
[ ] Preserve old identifiers when externally referenced
[ ] Create new ledger IDs where necessary
[ ] Link historical runs as provenance only
[ ] Validate current source/configuration
[ ] Remove resolved historical defects from active list
[ ] Keep regression tests where useful
[ ] Update release blocker policy
[ ] Review every old fallback
```

Historical logs do not define current status automatically.

---

## 77. Closure record template

When an entry closes, append:

```markdown
### Closure

**Closed:** <YYYY-MM-DD>  
**Closure type:** promoted | retired | superseded | accepted limitation | migrated  
**Project version:** <version>  
**Evidence:**

- <checkpoint>;
- <scenario>;
- <gold>;
- <artifact>;
- <review>.

**Follow-up records:**

- <decision/issue/contract/version>.
```

Do not delete the rationale and historical state.

---

## 78. Project completion criteria for the ledger

The ledger itself is complete for release when:

```text
[ ] Every non-stable state is registered
[ ] Every active entry has an owner
[ ] Every active entry has an exit condition
[ ] Every entry has validation impact
[ ] Every entry has release impact
[ ] Blocking entries appear in release criteria
[ ] Related known issues agree
[ ] Related decisions agree
[ ] Related contracts agree
[ ] Coverage rows exist
[ ] Closure evidence exists for promoted entries
[ ] No required placeholder remains
[ ] No stale identifier remains
```

A release may still contain accepted warnings or deprecated states when project policy permits them explicitly.

---

## 79. Template preservation checklist

For this reusable template:

```text
[ ] No active-language name
[ ] No active-language code
[ ] No real GF suffix
[ ] No real source root
[ ] No real module marked incomplete
[ ] No active scenario ID claimed
[ ] No active gold name claimed
[ ] No real issue/decision ID claimed as project fact
[ ] Examples remain labeled examples
[ ] Placeholders remain intentional
[ ] Paths remain generic
```

---

## 80. Related project-template documents

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
- `templates/project/docs/VALIDATION_SPEC.md`
- `templates/project/docs/TEST_COVERAGE_MATRIX.md`
- `templates/project/docs/DECISION_LOG.md`
- `templates/project/docs/KNOWN_ISSUES.md`
- `templates/project/docs/RELEASE_CRITERIA.md`
- `templates/project/docs/RESEARCH_EVIDENCE.md`

---

## 81. Related framework documents

- `docs/projects/PROJECT_MODEL.md`
- `docs/projects/CREATING_A_PROJECT.md`
- `docs/projects/PROJECT_COMPLETION_CHECKLIST.md`
- `docs/validation/VALIDATION_OVERVIEW.md`
- `docs/validation/RELEASE_GATES.md`
- `docs/scenarios/GOLDEN_TESTS.md`
- `docs/scenarios/UPDATING_GOLD_FILES.md`
- `docs/architecture/ARTIFACT_MODEL.md`
- `docs/release/VERSIONING_POLICY.md`
- `docs/reference/TERMINOLOGY_REFERENCE.md`
- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`

---

## 82. Final enforcement rule

The status ledger is the project’s explicit record of everything that is not yet fully stable.

Therefore:

> No fallback, scaffold, disabled behavior, missing validation, provisional artifact or temporary contract may remain implicit.

Every active non-stable state must have one stable ID, one owner, current evidence, explicit validation and release impact, and an objective exit condition.
