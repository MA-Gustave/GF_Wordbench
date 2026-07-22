# GF Wordbench Project — Status Ledger

**Document ID:** `GF-WB-PROJECT-STATUS-LEDGER`  
**Status:** Active project register  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\project\docs\STATUS_LEDGER.md`  
**Applies to:** The single active GF language project in this GF Wordbench working copy  
**Project identity authority:** `project/project.toml`  
**Project contract authority:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Ledger contract:** `PIFC-DOC-004`  
**Document owner:** Active project maintainers  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This file is the authoritative register of incomplete, provisional, exceptional and retired implementation states in the active language project.

It records work that must not be mistaken for stable project capability, including:

```text
experimental implementations
temporary implementations
fallback behavior
known warnings
blocked work
disabled behavior
retired behavior retained for history
explicit release exceptions
resolved entries and their closing evidence
```

The ledger exists to prevent a source file from appearing complete merely because:

```text
it compiles
a fallback returns a value
a placeholder satisfies a type
a scenario does not cover the missing behavior
a warning is ignored
a downstream entrypoint happens to build
an old gold file still matches
```

The central rule is:

> Every temporary, fallback, blocked, disabled or warning-bearing project behavior must be visible here, linked to its provider and consumers, and paired with evidence, a next action or an explicit exit condition.

---

## 2. What this ledger is not

This ledger is not:

```text
a task-management system
a complete bug database
a duplicate contract lock
a duplicate decision log
a duplicate test matrix
a source-code inventory
a release checklist
a changelog
a list of every stable feature
```

Use:

```text
project/docs/KNOWN_ISSUES.md
```

for confirmed defects and limitations.

Use:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

for normative provider/consumer promises.

Use:

```text
project/docs/DECISION_LOG.md
```

for project decisions and rationale.

Use:

```text
project/docs/TEST_COVERAGE_MATRIX.md
```

for requirement-to-evidence mapping.

Use:

```text
project/docs/RELEASE_CRITERIA.md
```

for release gates.

This ledger links to those authorities rather than replacing them.

---

## 3. Scope

The ledger covers project-owned status involving:

```text
GF source modules
public categories
lincats
morphology providers
syntax providers
constructors
lexical resources
helpers
interfaces and instances
entrypoints
checkpoints
scenarios
gold expectations
PGF targets
project documentation
research-dependent decisions
external project blockers
```

The ledger does not govern:

```text
Python framework implementation
GF Wordbench application defects
generated run artifacts
temporary local editor files
private local helper refactors with no consumer
ordinary completed work with no exceptional status
```

Framework defects belong in the framework issue or development workflow.

---

## 4. Related authoritative files

```text
project/project.toml
project/docs/00_PROJECT_START_HERE.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_OVERVIEW.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/DECISION_LOG.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA.md
project/docs/RESEARCH_EVIDENCE.md
project/validation/
```

A ledger entry must point to the files that own its detailed contract, design, defect, evidence or release treatment.

---

## 5. Core invariants

The ledger must always satisfy:

```text
every temporary implementation is registered
every fallback implementation is registered
every blocked contract is registered
every disabled required capability is registered
every accepted warning affecting project claims is registered
every entry identifies its provider
every entry identifies its known consumers
every entry identifies affected contracts
every entry has an owner or explicit unassigned state
every non-stable entry has a next action or exit condition
every release-blocking entry remains visible
every release exception is explicit and reviewed
every resolved entry retains closing evidence
source comments and ledger entries do not contradict one another
```

An empty or incomplete ledger is not proof that the project is stable.

---

# Part I — Status vocabularies

## 6. Implementation state versus contract status

The project uses two different vocabularies.

They must not be conflated.

### 6.1 Implementation state

This ledger uses:

```text
stable
experimental
temporary
fallback
warning
blocked
disabled
retired
```

These values describe the state of an implementation, capability, artifact or project obligation.

### 6.2 Contract status

The project contract lock uses:

```text
active
experimental
deprecated
blocked
retired
```

These values describe the lifecycle of a normative provider/consumer contract.

### 6.3 Example distinction

A contract may be:

```text
contract status: active
```

while its implementation is:

```text
implementation state: fallback
```

This means:

- consumers currently rely on the contract;
- the implementation satisfies it only through an explicitly limited fallback;
- the fallback must remain visible here;
- release treatment must be defined.

A fallback must not be labeled `stable` merely because its contract is active.

---

## 7. `stable`

Meaning:

```text
implemented according to the current project contract
validated by the required evidence
not dependent on an undocumented fallback
not blocked by a known unresolved requirement
eligible for normal project claims within documented scope
```

### 7.1 Ledger use

Stable capabilities do not need permanent open entries.

Use a stable ledger entry only when:

- closing a previous exceptional state;
- preserving a release-significant transition record;
- recording a reviewed stabilization milestone;
- documenting that a formerly provisional provider is now canonical.

### 7.2 Stable does not mean complete language coverage

`stable` means stable within the documented scope.

It does not mean:

```text
all vocabulary implemented
all constructions supported
all dialects supported
no known issues exist
no future compatible extension is possible
```

---

## 8. `experimental`

Meaning:

```text
implemented for evaluation
not yet committed as the final project design
may change incompatibly
requires explicit evaluation evidence
must not be presented as stable coverage
```

Required entry content:

```text
experiment question
provider
consumers
scope
evaluation method
decision date or exit condition
affected contracts
release effect
```

An experimental public surface requires an experimental contract entry or an explicit note that no stable consumer may depend on it.

---

## 9. `temporary`

Meaning:

```text
short-lived implementation used while the intended implementation is pending
known not to be the final design
must have a replacement plan or removal condition
```

Examples:

```text
temporary wrapper
temporary import bridge
temporary constructor
temporary duplicated table during migration
temporary module alias
temporary scenario workaround
```

Required entry content:

```text
why temporary behavior exists
intended replacement
deadline, milestone or exit condition
consumers that currently depend on it
validation proving it does not hide unrelated failures
```

A temporary implementation without a next action or exit condition violates the project contract.

---

## 10. `fallback`

Meaning:

```text
behavior used when the preferred linguistic or architectural implementation is unavailable
may provide reduced precision, reduced structure or reduced coverage
must be distinguishable from the intended behavior
```

Examples:

```text
default inflection
string-based substitute
generic agreement value
default constructor branch
placeholder linearization
inherited behavior outside validated scope
reduced-feature morphology
```

Required entry content:

```text
trigger condition
fallback output or behavior
preferred provider
affected consumers
known loss of information
scenario evidence
release treatment
removal condition
```

### 10.1 No hidden fallback

A fallback must not be hidden only in a source comment.

It must be registered here and referenced by the relevant project contract.

### 10.2 Structured values

A fallback that flattens a structured category or lincat requires explicit architecture and contract review.

---

## 11. `warning`

Meaning:

```text
implemented behavior remains usable but has a known risk, uncertainty, validation gap or non-blocking limitation requiring visibility
```

Examples:

```text
unverified edge case
optional scenario failure
tool-version sensitivity
known ambiguity increase
performance concern
research uncertainty
incomplete manual review
```

Required entry content:

```text
warning condition
affected scope
evidence
why it does not currently block
monitoring or next review
promotion condition to blocked, fallback or stable
```

A recurring warning must not be accepted silently across releases.

---

## 12. `blocked`

Meaning:

```text
work or validation cannot proceed because a named dependency, decision, defect, source, tool or contract is unresolved
```

Required entry content:

```text
blocking condition
blocked provider or capability
upstream dependency
owner of unblock action
consumers affected
release effect
evidence showing the block
next review condition
```

### 12.1 Blocking is not failure classification

`blocked` is a project implementation state.

It is not the runtime diagnostic class `downstream`.

A blocked feature may cause downstream validation failures, but the concepts remain distinct.

---

## 13. `disabled`

Meaning:

```text
implementation or capability exists or was planned but is intentionally prevented from normal use
```

Examples:

```text
scenario disabled
entrypoint excluded
constructor branch disabled
module not included in release
feature guarded by project configuration
```

Required entry content:

```text
reason disabled
mechanism enforcing disablement
affected contracts
consumers
risk if re-enabled
re-enable condition
release treatment
```

A required release capability that is disabled blocks release unless the validation specification explicitly excludes it.

---

## 14. `retired`

Meaning:

```text
implementation, workaround or project capability is no longer active and must not be used by current consumers
```

Retired entries remain in resolved history when they are important for:

```text
migration
old module-name recognition
decision traceability
gold-history explanation
release compatibility
```

Required closing content:

```text
retirement date or release
replacement
consumer migration evidence
validation evidence
remaining historical references
```

A retired provider must not remain an undocumented active dependency.

---

# Part II — Release impact and priority

## 15. Release impact

Every open entry has one release-impact value.

Canonical values:

```text
none
review
blocks-release
accepted-exception
not-applicable
```

### 15.1 `none`

The state does not affect the declared release scope.

The reason must still be clear.

### 15.2 `review`

The item requires release review but does not automatically block.

Examples:

```text
optional warning
non-release experimental module
documentation uncertainty
optional scenario failure
```

### 15.3 `blocks-release`

The item prevents release until resolved or deliberately removed from release scope through an approved contract and release-criteria change.

### 15.4 `accepted-exception`

A release owner has explicitly accepted the item for a named release.

This requires:

```text
decision reference
accepted scope
risk statement
release or expiry
reviewer
validation evidence
```

An accepted exception is not equivalent to stable.

### 15.5 `not-applicable`

Use only for historical or retired entries where current release impact no longer applies.

---

## 16. Priority

Canonical priority values:

```text
P0
P1
P2
P3
```

### 16.1 `P0`

Immediate integrity or release-critical risk.

Examples:

```text
required entrypoint invalid
wrong project identity
stale PGF accepted as current
gold modified by normal validation
public lincat contract broken
```

### 16.2 `P1`

High-priority project capability or major blocker.

### 16.3 `P2`

Normal planned correction or completion work.

### 16.4 `P3`

Low-risk cleanup, optional refinement or deferred improvement.

Priority does not replace release impact.

A `P3` item may still block release if release criteria require it.

---

## 17. Confidence

An entry may record one confidence value:

```text
confirmed
probable
hypothesis
unknown
```

Use confidence for the diagnosis or status claim.

Do not use it to weaken a confirmed release block.

Examples:

```text
status = blocked
confidence = confirmed
```

or:

```text
status = warning
confidence = hypothesis
```

---

# Part III — Entry identity and fields

## 18. Stable entry IDs

Every ledger entry has a stable identifier.

Format:

```text
STAT-<DOMAIN>-<NUMBER>
```

Examples:

```text
STAT-MORPH-001
STAT-LINC-002
STAT-SYNTAX-004
STAT-SCENARIO-003
STAT-PGF-001
```

IDs must not be reused after resolution or retirement.

---

## 19. Recommended domains

```text
ARCH
CONFIG
MODULE
LINC
MORPH
SYNTAX
LEXICON
HELPER
STRUCTURAL
EXTEND
ENTRY
SCENARIO
GOLD
PGF
VALIDATION
DOC
RESEARCH
TOOL
MIGRATION
RELEASE
```

Use the narrowest clear domain.

Do not create a new domain for one entry unless it represents a durable project category.

---

## 20. Required fields

Every open entry must define:

| Field | Requirement |
|---|---|
| Entry ID | Stable `STAT-<DOMAIN>-<NUMBER>` |
| Title | Short description of the state |
| Implementation state | One canonical ledger state |
| Priority | `P0`, `P1`, `P2` or `P3` |
| Release impact | Canonical release-impact value |
| Confidence | `confirmed`, `probable`, `hypothesis` or `unknown` |
| Provider | File, module, artifact or project obligation |
| Consumers | Known direct consumers |
| Affected contracts | Project contract IDs |
| Scope | Exact supported and unsupported behavior |
| Reason | Why this state exists |
| Evidence | Compile, scenario, gold, run, research or review evidence |
| Risk | Consequence of leaving the state unresolved |
| Next action | Smallest concrete next step |
| Exit condition | Objective condition for state transition or closure |
| Owner | Responsible maintainer or `unassigned` |
| Introduced | Date, commit or release |
| Last reviewed | Date or release |
| Related issues | Known-issue IDs when applicable |
| Related decisions | Decision IDs when applicable |

---

## 21. Conditional fields

Use when applicable:

```text
blocked by
fallback trigger
preferred replacement
disabled mechanism
release exception
expiry
target milestone
affected scenarios
affected gold files
affected entrypoints
affected artifacts
research dependency
tool compatibility
migration path
```

---

## 22. Provider field

The provider identifies what currently owns the behavior.

Examples:

```text
path/to/Morphology.gf
path/to/Syntax.gf
project/project.toml
project/validation/scenarios/parse-core.gfs
project/validation/gold/parse-core.gold
configured PGF entrypoint
manual review obligation
```

A provider must be specific enough to inspect.

Avoid:

```text
morphology code
syntax stuff
project
GF
unknown module
```

When the provider is not yet known, use:

```text
unresolved provider
```

and make provider identification the next action.

---

## 23. Consumers field

List all known direct consumers.

Examples:

```text
path/to/Noun.gf
path/to/Grammar.gf
path/to/Language.gf
project/validation/scenarios/agreement.gfs
release PGF entrypoint
```

If consumer discovery is incomplete, state:

```text
consumer inventory incomplete
```

and list the search evidence used so far.

A ledger entry is not complete merely because one visible consumer is listed.

---

## 24. Affected contracts

Reference stable project contract IDs.

Examples:

```text
PIFC-LINC-001
PIFC-MORPH-002
PIFC-SCENARIO-004
PIFC-ENTRY-003
PIFC-RELEASE-002
```

When no project contract exists for a cross-file behavior, create or update the contract before treating the behavior as established.

---

## 25. Scope

Scope states exactly where the entry applies.

Include:

```text
supported categories
supported forms
supported constructors
supported registers or variants
affected modules
affected scenarios
excluded cases
```

Avoid statements such as:

```text
some verbs fail
syntax incomplete
needs work
```

Prefer:

```text
applies to productive regular verb class X in present indicative;
irregular verbs and non-finite forms remain outside this provider
```

---

## 26. Evidence

Every entry requires evidence.

Accepted evidence types include:

```text
direct module compilation
consumer compilation
checkpoint compilation
entrypoint compilation
`.gfs` scenario
normalized scenario output
gold comparison
PGF build
run summary
raw GF diagnostic
source fingerprint
manual review with named reviewer and method
research source
```

### 26.1 Evidence path

Prefer a stable repository path or run-relative artifact path.

Example:

```text
runs/run_<id>/summary.json
runs/run_<id>/raw/compile/<file>.stderr.txt
project/validation/scenarios/<scenario>.gfs
project/validation/gold/<scenario>.gold
```

### 26.2 Evidence freshness

Evidence must identify the source version or run.

Old evidence may remain historical but cannot prove current status after relevant source changes.

### 26.3 Missing evidence

Use:

```text
evidence missing
```

and make evidence creation a next action.

Do not leave the field blank.

---

## 27. Next action

The next action must be concrete and small enough to execute.

Good:

```text
replace the generic `Str` fallback in `NounX.gf` with the documented `NForm` table and run checkpoint `MorphologyX`
```

Weak:

```text
fix morphology
improve syntax
investigate
finish later
```

### 27.1 Blocked entries

For a blocked entry, the next action may be:

```text
obtain a research decision
upgrade GF
complete an upstream provider
approve a lincat migration
```

It must identify who or what can unblock the work.

---

## 28. Exit condition

The exit condition defines objective closure or transition.

Examples:

```text
provider and all consumers compile
required scenario passes
gold reviewed
PGF built from current sources
fallback branch removed
decision accepted
contract status changed
research uncertainty resolved
feature removed from release scope
```

Avoid:

```text
when it looks good
when complete
later
```

---

## 29. Owner

Use:

```text
maintainer name
team or role
unassigned
external dependency owner
```

`unassigned` is explicit and visible.

It is preferable to an empty owner field.

---

## 30. Dates and releases

Use ISO dates:

```text
YYYY-MM-DD
```

or immutable release identifiers.

Examples:

```text
2026-07-22
project-<id>-v1.0.0
commit <sha>
```

Relative dates such as `last week` are prohibited.

---

# Part IV — Canonical ledger layout

## 31. Project status snapshot

The identity itself remains in:

```text
project/project.toml
```

The ledger snapshot records only status administration.

| Field | Value |
|---|---|
| Project identity source | `project/project.toml` |
| Contract source | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Validation source | `project/docs/VALIDATION_SPEC.md` |
| Release source | `project/docs/RELEASE_CRITERIA.md` |
| Ledger population state | Project-specific review required |
| Last complete ledger review | Not yet recorded |
| Release exception count | Not yet assessed |
| Release-blocking entry count | Not yet assessed |

### 31.1 Baseline note

This generated baseline defines the ledger contract and entry format.

It does not claim that the active source tree has no temporary, fallback, warning, blocked or disabled behavior.

Project maintainers must inspect the current source, contracts and validation evidence and populate the open-entry register before making completeness or release claims.

---

## 32. Open-entry summary

Populate this table from the detailed open entries.

| Entry ID | State | Priority | Release impact | Provider | Owner | Next action |
|---|---|---|---|---|---|---|
| — | — | — | — | No project-specific entry recorded in this baseline | unassigned | Perform the initial project status review |

The administrative row above is not a project status entry and must be replaced by actual entries after review.

---

## 33. Release-blocking summary

Populate this table with every open entry whose release impact is:

```text
blocks-release
```

or:

```text
accepted-exception
```

| Entry ID | Impact | Blocking or accepted condition | Decision | Expiry or target |
|---|---|---|---|---|
| — | — | Not yet assessed | — | — |

A release review must not proceed while this table is unassessed.

---

## 34. Open entries

Add detailed entries below this heading.

Order:

1. `P0`;
2. `P1`;
3. `P2`;
4. `P3`;
5. within priority, `blocks-release`;
6. then `review`;
7. then other release impacts;
8. then entry ID.

No project-specific open entry is inserted automatically by this baseline.

The absence of an entry is not evidence of stability.

---

## 35. Resolved and retired entries

Resolved entries remain below this heading.

They record:

```text
former state
resolution or retirement
closing evidence
consumer migration
contract update
release impact
closed date
```

Do not delete a resolved entry when it explains current architecture, gold history, migration or release evidence.

A trivial entry with no continuing value may be archived according to project documentation policy.

---

# Part V — Entry template

## 36. Canonical open-entry template

```markdown
## STAT-<DOMAIN>-<NUMBER> — <short title>

**Implementation state:** `experimental | temporary | fallback | warning | blocked | disabled`  
**Priority:** `P0 | P1 | P2 | P3`  
**Release impact:** `none | review | blocks-release | accepted-exception`  
**Confidence:** `confirmed | probable | hypothesis | unknown`  
**Owner:** `<maintainer, role, external owner, or unassigned>`  
**Introduced:** `<YYYY-MM-DD, release, or commit>`  
**Last reviewed:** `<YYYY-MM-DD or release>`

### Provider

```text
<path, module, artifact, or unresolved provider>
```

### Consumers

```text
<direct consumer paths>
```

### Affected contracts

```text
<PIFC-...>
```

### Scope

Describe the exact affected and unaffected behavior.

### Reason

Describe why the project is in this state.

### Current behavior

Describe what the provider currently does.

### Intended behavior

Describe the target behavior or state that would remove the entry.

### Evidence

```text
<compile, scenario, gold, run, diagnostic, research, or manual review>
```

### Risk

Describe the consequence of leaving the state unresolved.

### Next action

Describe the smallest concrete next step.

### Exit condition

Describe the objective condition for transition or closure.

### Related issues

```text
<known issue IDs or none>
```

### Related decisions

```text
<decision IDs or none>
```

### Release exception

Use only when `release impact = accepted-exception`.

Record:

- named release;
- reviewer;
- accepted scope;
- risk;
- expiry;
- decision reference.
```

---

## 37. Canonical resolved-entry addition

When closing or retiring an entry, retain the original fields and add:

```markdown
### Resolution

**Final state:** `stable | retired`  
**Resolved:** `<YYYY-MM-DD or release>`  
**Resolved by:** `<maintainer or decision>`  
**Replacement:** `<provider or none>`  
**Closing evidence:**

```text
<current evidence paths>
```

**Consumer review:**

```text
<consumer validation or migration evidence>
```

**Contract updates:**

```text
<contract IDs and versions>
```

**Remaining limitations:**

```text
<none or explicit limitations>
```
```

---

# Part VI — State-specific requirements

## 38. Experimental entry checklist

```text
[ ] experiment question is explicit
[ ] no stable consumer depends on an undocumented surface
[ ] evaluation method is defined
[ ] success and failure criteria are defined
[ ] target decision date or milestone exists
[ ] release impact is defined
[ ] affected contracts are marked experimental when needed
```

---

## 39. Temporary entry checklist

```text
[ ] temporary provider is named
[ ] intended replacement is named
[ ] all current consumers are listed
[ ] no duplicate provider remains undocumented
[ ] removal condition is objective
[ ] target milestone exists
[ ] validation proves temporary behavior does not hide unrelated failure
```

---

## 40. Fallback entry checklist

```text
[ ] fallback trigger is defined
[ ] preferred behavior is defined
[ ] information loss is described
[ ] affected categories or forms are listed
[ ] source behavior is distinguishable
[ ] scenario coverage exists
[ ] release treatment is defined
[ ] removal condition exists
```

---

## 41. Warning entry checklist

```text
[ ] warning condition is reproducible or clearly hypothetical
[ ] affected scope is bounded
[ ] evidence is linked
[ ] reason it does not currently block is explicit
[ ] monitoring or next review exists
[ ] escalation condition exists
```

---

## 42. Blocked entry checklist

```text
[ ] blocker is specific
[ ] blocked provider or capability is named
[ ] unblock owner is named
[ ] affected consumers are listed
[ ] release impact is explicit
[ ] next review trigger exists
[ ] downstream symptoms are not misreported as separate root blockers
```

---

## 43. Disabled entry checklist

```text
[ ] disablement mechanism is named
[ ] disabled surface is named
[ ] consumers are prevented from accidental use
[ ] release policy is explicit
[ ] re-enable condition exists
[ ] stale scenario and gold references are reviewed
```

---

## 44. Retired entry checklist

```text
[ ] replacement or removal reason recorded
[ ] consumers migrated
[ ] entrypoints updated
[ ] scenarios updated
[ ] gold mappings updated
[ ] project.toml updated
[ ] dependency map updated
[ ] contracts retired or redirected
[ ] closing evidence recorded
```

---

# Part VII — Lifecycle

## 45. Entry creation triggers

Create a ledger entry when any of these occurs:

- a placeholder implementation is introduced;
- a generic fallback is introduced;
- an inherited behavior is used outside validated scope;
- a provider is knowingly incomplete;
- a required consumer is blocked;
- a feature is disabled;
- a warning is accepted temporarily;
- a scenario is intentionally skipped;
- a required gold is missing;
- a release artifact is unavailable;
- a research decision is pending;
- an external tool blocks required behavior;
- a temporary duplicate provider exists during migration;
- a release exception is proposed;
- source comments identify unfinished public behavior.

Do not wait until release review.

---

## 46. Entry update triggers

Update an entry when:

```text
provider changes
consumer set changes
status changes
priority changes
release impact changes
evidence changes
next action changes
owner changes
blocker changes
scenario or gold changes
contract changes
decision changes
release exception is accepted or expires
```

---

## 47. Entry closure

An entry closes only when its exit condition is met.

Required closure sequence:

1. implement or remove the affected behavior;
2. validate provider;
3. validate direct consumers;
4. validate downstream checkpoints;
5. run affected scenarios;
6. review gold;
7. update affected contracts;
8. update specifications;
9. update coverage matrix;
10. update known issues;
11. add closing evidence;
12. set final state;
13. move to resolved history.

Closing an entry because work is no longer planned requires:

```text
retired state
decision reference
consumer removal
release-scope review
```

---

## 48. Allowed state transitions

Typical transitions:

```text
experimental → stable
experimental → temporary
experimental → fallback
experimental → blocked
experimental → retired

temporary → stable
temporary → blocked
temporary → retired

fallback → stable
fallback → blocked
fallback → retired

warning → stable
warning → blocked
warning → fallback
warning → retired

blocked → experimental
blocked → temporary
blocked → stable
blocked → retired

disabled → experimental
disabled → stable
disabled → retired
```

A direct transition must be supported by evidence.

---

## 49. Prohibited silent transitions

The following require explicit ledger updates:

```text
fallback → stable
temporary → stable
blocked → stable
disabled → stable
warning → ignored
experimental → active contract
accepted-exception → permanent acceptance
```

Source edits alone do not perform a status transition.

---

## 50. Reopening an entry

A resolved entry may be reopened when:

```text
regression occurs
closing evidence becomes invalid
a new consumer exposes the limitation
a tool upgrade changes behavior
a gold update reveals the issue
a release criterion expands scope
```

Keep the same entry ID.

Add:

```text
reopened date
reason
new evidence
new state
```

---

# Part VIII — Evidence and validation

## 51. Minimum evidence by state

| State | Minimum evidence |
|---|---|
| `experimental` | Reproducible experiment or focused test |
| `temporary` | Provider compile plus affected consumer review |
| `fallback` | Trigger scenario and documented output |
| `warning` | Reproduction, diagnostic or review evidence |
| `blocked` | Evidence of blocker and affected validation |
| `disabled` | Configuration/source proof that use is prevented |
| `retired` | Consumer migration and absence from current entrypoints |
| `stable` closure | Required project validation evidence |

---

## 52. Evidence quality

Evidence should be:

```text
current
specific
traceable
bounded
reproducible where possible
associated with source identity
associated with GF and RGL identity when relevant
```

### 52.1 Weak evidence

Weak evidence includes:

```text
memory
chat transcript only
unpreserved console text
old run with unknown source revision
manual claim without method
matching output from an unrelated scenario
```

Weak evidence may support a hypothesis but not stable closure.

---

## 53. Direct and downstream evidence

When an entry arises from a failure:

- identify the direct provider when possible;
- avoid creating separate blocker entries for every downstream failure;
- list downstream consumers under the root entry;
- preserve ambiguity when the root is not known.

The ledger is not a duplicate runtime diagnostic classifier, but it must respect existing causal evidence.

---

## 54. Scenario evidence

A scenario used by a ledger entry must identify:

```text
scenario ID
purpose
entrypoint
required inputs
markers
gold or assertion strategy
latest relevant result
```

A disabled or missing scenario may itself require an entry.

---

## 55. Gold evidence

A gold mismatch may indicate:

```text
implementation regression
intended linguistic change
stale gold
normalization change
GF version difference
RGL difference
scenario change
```

The ledger entry must not assume the cause without evidence.

Normal validation never updates gold automatically.

---

## 56. Manual evidence

Manual inspection is acceptable only when automation is impractical.

Record:

```text
reviewer
date
method
files inspected
criteria
result
limitations
```

“Reviewed manually” without these details is insufficient.

---

# Part IX — Relationship to other project records

## 57. Relationship to `KNOWN_ISSUES.md`

Use a known-issue entry when there is a confirmed defect or limitation.

Use a status-ledger entry when there is an exceptional implementation state.

Examples:

```text
fallback morphology provider
    → status ledger

incorrect form produced for a documented input
    → known issue

fallback causes the incorrect form
    → linked entries in both files
```

Do not duplicate the full description.

Cross-reference stable IDs.

---

## 58. Relationship to `DECISION_LOG.md`

Use a decision entry when maintainers choose:

```text
architecture
representation
fallback acceptance
release exception
scope reduction
migration
retirement
```

The ledger records the resulting state and operational follow-up.

A release exception without a decision reference is invalid.

---

## 59. Relationship to the contract lock

The contract lock defines:

```text
what providers guarantee
what consumers may assume
```

The ledger records:

```text
where implementation does not yet meet the intended stable state
where a fallback or exception remains
where the contract is blocked or experimental
```

Every relevant ledger entry must be referenced from the affected contract or contract section.

---

## 60. Relationship to specifications

Use:

```text
CATEGORY_AND_LINCAT_CONTRACT.md
MORPHOLOGY_SPEC.md
SYNTAX_AND_CONSTRUCTOR_RULES.md
```

for intended behavior.

The ledger records deviations, provisional implementations and blockers.

Do not define the target linguistic model only in the ledger.

---

## 61. Relationship to the coverage matrix

The coverage matrix records whether requirements have evidence.

The ledger records why a requirement is:

```text
provisional
blocked
fallback-backed
disabled
warning-bearing
```

A release-critical coverage gap normally requires a ledger entry.

---

## 62. Relationship to release criteria

`RELEASE_CRITERIA.md` defines release gates.

This ledger supplies:

```text
open blockers
accepted exceptions
unresolved warnings
fallback inventory
disabled capability inventory
closing evidence
```

Release criteria must not be weakened only by changing this ledger.

A scope or gate change requires the release-criteria and decision workflows.

---

## 63. Relationship to source comments

Source comments may reference a ledger entry.

Recommended form:

```gf
-- STATUS: STAT-MORPH-001
```

or another project-approved short form.

A comment must not contain a conflicting state.

Example conflict:

```text
source comment: temporary
ledger state: stable
```

The conflict must be resolved.

### 63.1 No comment-only status

A public temporary or fallback behavior must not be tracked only by `TODO`, `FIXME` or a source comment.

---

# Part X — Release exceptions

## 64. Exception requirements

A release exception is allowed only when:

```text
release impact is accepted-exception
a decision entry exists
scope is bounded
risk is documented
reviewer is named
release is named
expiry or next-review condition exists
validation evidence exists
release criteria permit the exception
```

### 64.1 Exception does not change state

An accepted fallback remains:

```text
implementation state = fallback
```

It does not become `stable`.

### 64.2 Exception expiry

An exception expires at:

```text
named release
date
milestone
source change
tool upgrade
scope expansion
```

After expiry, release review must reassess it.

### 64.3 Permanent acceptance

A permanent design choice should be moved into:

```text
specification
contract lock
decision log
validation
```

and the ledger entry closed as stable or retired.

The ledger must not accumulate permanent “temporary” exceptions.

---

## 65. Release review procedure

Before release:

1. review every open `P0` and `P1` entry;
2. review every `blocks-release` entry;
3. review every `accepted-exception`;
4. verify expiry;
5. review fallback coverage;
6. review disabled required capabilities;
7. review warnings added since the previous release;
8. verify resolved entries have current evidence;
9. update the release-blocking summary;
10. record the review date and release.

A release is not ready while the ledger remains administratively unassessed.

---

# Part XI — Initial population workflow

## 66. Initial project status review

Because this baseline cannot infer the actual language implementation, maintainers must populate it through repository inspection.

Review in this order:

1. `project/project.toml`;
2. project contract lock;
3. language architecture;
4. dependency map;
5. category and lincat contract;
6. morphology specification;
7. syntax and constructor rules;
8. validation specification;
9. coverage matrix;
10. known issues;
11. decision log;
12. source comments containing `TODO`, `FIXME`, `temporary`, `fallback`, `disabled`, `blocked`, `warning`;
13. current entrypoints and checkpoints;
14. current scenarios and gold files;
15. latest diagnostic run.

---

## 67. Initial search terms

Search project-owned sources for terms equivalent to:

```text
TODO
FIXME
TEMP
temporary
fallback
default
placeholder
stub
dummy
disabled
blocked
warning
not implemented
unsupported
inherit
override
Predef.error
variants {}
```

A match is a review candidate, not automatically a ledger entry.

Interpret it in context.

---

## 68. Initial inventory questions

For each major project responsibility, ask:

```text
Is there one authoritative provider?
Does the provider match the specification?
Do all consumers compile?
Is the public shape documented?
Is a generic fallback used?
Is any branch disabled?
Is any required scenario absent?
Is gold coverage missing?
Is a release artifact unavailable?
Is a warning accepted without a decision?
Is a blocker external or internal?
```

---

## 69. Initial population completion

The initial population is complete when:

```text
all major providers reviewed
all public lincats reviewed
all temporary source comments reconciled
all fallbacks registered
all blocked contracts registered
all disabled release capabilities registered
all release-critical coverage gaps registered
known issues cross-linked
release-blocking summary assessed
review date recorded
```

Only then replace:

```text
Ledger population state: Project-specific review required
```

with a reviewed state.

---

# Part XII — Automation

## 70. Project checker

GF Wordbench should support a project check capable of detecting ledger drift.

Suggested logical command:

```text
gf-wordbench project check
```

Exact command syntax belongs to the CLI reference.

---

## 71. Automated checks

The checker should verify:

```text
entry IDs are unique
entry states are canonical
priorities are canonical
release-impact values are canonical
providers exist when expected
consumer paths exist when expected
contract IDs exist
open temporary entries have next actions
open temporary entries have exit conditions
fallback entries have triggers
blocked entries name blockers
accepted exceptions name decisions and releases
resolved entries contain closing evidence
source status references resolve to ledger IDs
retired IDs are not reused
release blockers appear in the release-blocking summary
```

---

## 72. Optional source-reference check

A strict checker may scan source comments for:

```text
STATUS: STAT-
```

and verify:

```text
referenced ID exists
entry is not retired unless comment is historical
source path agrees with provider or consumer list
```

The checker must not require source comments for every entry.

---

## 73. No automatic state inference

Automation may flag candidates.

It must not automatically assign:

```text
stable
fallback
blocked
release exception
```

These states require project interpretation and review.

---

# Part XIII — Review cadence

## 74. Required review times

Review the ledger:

```text
before a release
after a breaking project change
after a major fallback introduction
after a GF or RGL upgrade
after project migration
after changing release scope
after adding or removing entrypoints
after adding or removing required scenarios
when a blocked dependency changes
during maintainer handoff
```

---

## 75. Routine review

During active development, review relevant entries whenever their providers or consumers change.

A fixed weekly or monthly review is optional.

Change-triggered review is mandatory.

---

## 76. Stale entry

An entry is stale when:

```text
provider no longer exists
consumer list is outdated
next action is no longer relevant
evidence predates a breaking source change
owner is no longer responsible
release exception expired
exit condition has already occurred
```

A stale entry must be updated, resolved or retired.

---

# Part XIV — Handoff

## 77. Maintainer handoff

A handoff should identify:

```text
open entry IDs
highest-priority entry
release blockers
accepted exceptions
blocked dependencies
recently resolved entries
entries needing evidence refresh
next smallest action
last relevant run
```

A chat message is not a substitute for updating this ledger.

---

## 78. AI-assisted handoff

AI-ready reports may reference ledger entries.

An AI system may help:

```text
summarize evidence
identify likely consumers
suggest a validation sequence
compare current and intended behavior
```

It must not silently change entry state or accept a release exception.

Human project review remains authoritative.

---

# Part XV — Migration and history

## 79. Migrating existing notes

When converting old project notes:

```text
TODO lists
source comments
old audit notes
issue descriptions
release checklists
chat records
```

classify each item into:

```text
contract
status ledger
known issue
decision
coverage gap
release criterion
ordinary task
```

Do not copy every old note into the ledger.

---

## 80. Historical entries

Historical entries may retain old module names when required to explain migration.

Mark them clearly as historical.

Current project paths must use current identity and module names.

---

## 81. Entry renaming

The entry title may change.

The stable entry ID does not.

When the domain was initially wrong, retain the ID and record the clarification unless project policy explicitly supports ID migration.

Avoid broken cross-references.

---

# Part XVI — Anti-drift indicators

## 82. Ledger drift

Probable drift exists when:

- source contains a temporary public implementation with no entry;
- source contains a fallback with no entry;
- a blocked contract is absent from the ledger;
- a required scenario is disabled without an entry;
- a release warning is accepted without an entry;
- a ledger provider no longer exists;
- a consumer is missing from the entry;
- a contract references an unknown ledger ID;
- a ledger entry references an unknown contract;
- a source comment says `temporary` while the ledger says `stable`;
- a fallback entry lacks a trigger;
- a temporary entry lacks an exit condition;
- a blocked entry lacks an unblock owner;
- a resolved entry lacks closing evidence;
- an accepted exception lacks a decision;
- an accepted exception has expired;
- a release blocker is omitted from the summary;
- a fallback is described as complete in project documentation;
- a disabled feature remains listed as required and passing;
- a retired provider remains in an entrypoint;
- an old-language status entry remains active after project reset;
- the ledger duplicates the full known-issue record;
- the ledger becomes a generic task backlog;
- stable state is inferred only from compilation;
- evidence points to a stale run;
- priority is used to override release criteria;
- `accepted-exception` is treated as stable.

Detected drift must be corrected before release claims.

---

## 83. Documentation drift

The ledger and these files must agree:

```text
INTERFILE_CONTRACT_LOCK.md
MODULE_DEPENDENCY_MAP.md
CATEGORY_AND_LINCAT_CONTRACT.md
MORPHOLOGY_SPEC.md
SYNTAX_AND_CONSTRUCTOR_RULES.md
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
KNOWN_ISSUES.md
DECISION_LOG.md
RELEASE_CRITERIA.md
```

A conflict is not resolved by choosing whichever file is convenient.

Identify the normative owner and update all dependent records.

---

# Part XVII — Checklists

## 84. New entry checklist

```text
[ ] stable entry ID assigned
[ ] implementation state selected
[ ] priority selected
[ ] release impact selected
[ ] confidence selected
[ ] provider identified
[ ] consumers identified
[ ] affected contracts linked
[ ] scope bounded
[ ] reason stated
[ ] current behavior stated
[ ] intended behavior stated
[ ] evidence linked
[ ] risk stated
[ ] next action concrete
[ ] exit condition objective
[ ] owner assigned or unassigned explicitly
[ ] dates recorded
[ ] known issues linked
[ ] decisions linked
```

---

## 85. Entry review checklist

```text
[ ] provider still exists
[ ] consumers still current
[ ] state still accurate
[ ] priority still accurate
[ ] release impact still accurate
[ ] evidence still current
[ ] blocker still current
[ ] next action still useful
[ ] exit condition still appropriate
[ ] owner still valid
[ ] contract references current
[ ] issue references current
[ ] decision references current
[ ] release exception not expired
```

---

## 86. Entry closure checklist

```text
[ ] exit condition met
[ ] provider validated
[ ] direct consumers validated
[ ] downstream checkpoints validated
[ ] affected scenarios run
[ ] gold reviewed
[ ] contracts updated
[ ] specifications updated
[ ] dependency map updated
[ ] coverage matrix updated
[ ] known issue updated
[ ] decision recorded when needed
[ ] closing evidence added
[ ] final state selected
[ ] closure date recorded
[ ] entry moved to resolved history
```

---

## 87. Release review checklist

```text
[ ] initial ledger population complete
[ ] every P0 reviewed
[ ] every P1 reviewed
[ ] every release blocker reviewed
[ ] every accepted exception reviewed
[ ] every fallback in release scope reviewed
[ ] every disabled required capability reviewed
[ ] every warning in release scope reviewed
[ ] expired exceptions removed or renewed
[ ] evidence refreshed after relevant source changes
[ ] release-blocking summary current
[ ] release criteria agree with ledger
[ ] known issues agree with ledger
[ ] release decision recorded
```

---

## 88. Project reset checklist

After replacing the active language project:

```text
[ ] remove old-language open entries
[ ] retain only clearly historical entries when needed
[ ] reset project-specific review dates
[ ] perform initial population review
[ ] verify project identity from project.toml
[ ] verify provider and consumer paths
[ ] verify contract IDs
[ ] verify scenarios and gold mappings
[ ] reassess release blockers
```

The generic template must not contain populated language-specific ledger entries.

---

# Part XVIII — Current project register

## 89. Open-entry register

The project-specific register begins here.

This generated baseline does not invent statuses for source files it has not inspected.

Replace this note with reviewed entries after the initial project status review.

```text
No project-specific open entries have been recorded in this generated baseline.
This is not a stability claim.
```

---

## 90. Resolved-entry register

Move closed or retired entries here using the canonical resolved-entry format.

```text
No project-specific resolved entries have been recorded in this generated baseline.
```

---

## 91. Release-exception register

Every accepted exception must also appear in the related detailed ledger entry.

| Entry ID | Release | Decision | Reviewer | Accepted risk | Expiry |
|---|---|---|---|---|---|
| — | — | No exception recorded in this generated baseline | — | — | — |

---

## 92. Review record

Record complete ledger reviews here.

| Review date | Reviewer | Source revision | Scope | Result | Evidence |
|---|---|---|---|---|---|
| — | — | — | Initial project-specific review not yet recorded | Pending | — |

---

# Part XIX — Final enforcement rule

The status ledger exists to make incomplete or exceptional project behavior impossible to mistake for stable capability.

Therefore:

> No temporary implementation, fallback, warning, block, disabled feature or release exception may remain implicit. It must have a stable ledger identity, named provider and consumers, current evidence, explicit release treatment, and an objective next action or exit condition.
