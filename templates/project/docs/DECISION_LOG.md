# GF Wordbench Project Template — Decision Log

**Document ID:** `GF-WB-TEMPLATE-PROJECT-DECISION-LOG`  
**Document role:** Normative template  
**Decision status:** Accepted template contract  
**Implementation status:** Template available; active-project implementation depends on initialization  
**Verification status:** Requires placeholder, source, contract and validation checks after initialization  
**Applies to:** One active GF project initialized from `templates/project/`  
**Template owner:** GF Wordbench maintainers  
**Project owner after initialization:** `<PROJECT_OWNER>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**GF module suffix:** `<GF_SUFFIX>`  
**Decision-log version:** `1.0`  
**Last reviewed:** `<YYYY-MM-DD>`  

---

## 1. Purpose

This document records deliberate project decisions that affect the architecture, linguistic behavior, validation contract, release policy, or long-term maintainability of one active GF project.

It exists to preserve:

- why a choice was made;
- which alternatives were considered;
- which evidence supported the choice;
- which modules, contracts, scenarios, gold files, and artifacts are affected;
- whether the choice is temporary or permanent;
- what would cause the decision to be reviewed;
- how a later decision supersedes an earlier one without rewriting history.

This file is a decision record.

It is not:

- a task backlog;
- an issue tracker;
- a status ledger;
- a changelog;
- a module dependency map;
- a linguistic research bibliography;
- a substitute for executable validation evidence.

---

## 2. Core rule

> Record the reason before the implementation becomes the only surviving explanation.

A decision that changes a project contract is incomplete until:

```text
decision entry
provider implementation
all affected consumers
project configuration
validation scenarios
gold expectations
documentation
status ledger
known issues
contract lock
release evidence
```

agree.

---

## 3. Template versus active project

The reusable template lives at:

```text
templates/project/docs/DECISION_LOG.md
```

The active project copy lives at:

```text
project/docs/DECISION_LOG.md
```

The template:

- remains language-neutral;
- contains placeholders;
- contains no active project decisions;
- may contain generic examples clearly labeled as examples;
- must not claim that a real project chose or validated anything.

The active project:

- replaces required placeholders;
- records real accepted, rejected, superseded, or retired decisions;
- links current evidence;
- uses actual project identifiers and module paths;
- remains synchronized with project contracts and release criteria.

---

## 4. Related project documents

```text
project/project.toml
project/docs/00_PROJECT_START_HERE.md
project/docs/LANGUAGE_OVERVIEW.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA.md
project/docs/RESEARCH_EVIDENCE.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Framework references:

```text
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/validation/SCENARIO_VALIDATION.md
docs/release/VERSIONING_POLICY.md
docs/release/RELEASE_PROCESS.md
docs/release/MIGRATION_AND_DEPRECATION.md
docs/reference/SCHEMA_INDEX.md
docs/architecture/DEPENDENCY_RULES.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/gf/GF_TOOLCHAIN_BOUNDARY.md
```

---

## 5. Decision-log ownership

This document owns the history of deliberate project choices.

Other documents remain authoritative for current state.

| Question | Authoritative owner |
|---|---|
| What decision was made and why? | `DECISION_LOG.md` |
| What is the current module architecture? | `LANGUAGE_ARCHITECTURE.md` |
| What imports what? | `MODULE_DEPENDENCY_MAP.md` |
| What is the current lincat contract? | `CATEGORY_AND_LINCAT_CONTRACT.md` |
| What is temporarily incomplete? | `STATUS_LEDGER.md` |
| What is currently wrong or risky? | `KNOWN_ISSUES.md` |
| What evidence is required? | `VALIDATION_SPEC.md` |
| What blocks release? | `RELEASE_CRITERIA.md` |
| What cross-file promise is locked? | `INTERFILE_CONTRACT_LOCK.md` |
| What changed between releases? | project changelog or release notes |

The decision log records history.

It does not duplicate the full current specification.

---

# 6. When a decision entry is required

A decision entry is required when a choice materially affects one or more project contracts.

Required categories include:

```text
project identity
module ownership
module boundaries
import direction
abstract API
category or lincat structure
parameter domains
morphology representation
paradigm API
syntax constructor behavior
word order
agreement
case selection
clitic behavior
inheritance or override policy
entrypoint selection
checkpoint order
scenario acceptance
normalization behavior
gold acceptance
known-issue acceptance
release criteria
artifact identity
migration strategy
deprecation or retirement
```

---

## 7. Project identity decisions

Record a decision when selecting or changing:

```text
project ID
language code
GF suffix
source-root layout
project versioning policy
release artifact name
```

Renaming a language code or GF suffix is a breaking project migration.

The decision must identify every affected source, scenario, gold, configuration, documentation, and artifact path.

---

## 8. Module ownership decisions

Record a decision when:

- creating a new architectural layer;
- moving a public responsibility between modules;
- splitting one module;
- merging modules;
- selecting one provider among duplicates;
- retiring a provider;
- promoting a helper to public API;
- replacing an inherited provider with a local provider.

The decision must identify:

```text
old provider
new provider
consumers
migration sequence
validation evidence
```

---

## 9. Lincat and category decisions

Record a decision when changing:

```text
lincat record shape
public field name
field type
table index
parameter dimension
agreement representation
case representation
definiteness representation
word-order flag
clitic field
variant representation
```

A decision is also required when deliberately flattening a structured category or introducing a compatibility adapter.

---

## 10. Morphology decisions

Record decisions about:

- inflectional feature inventory;
- paradigm classification;
- irregular-form representation;
- stem-selection policy;
- default paradigm policy;
- missing-form behavior;
- productive versus lexicalized morphology;
- orthographic alternations;
- ambiguity in morphological analysis;
- inheritance from an upstream resource;
- local override policy.

---

## 11. Syntax decisions

Record decisions about:

- constituent order;
- agreement propagation;
- object placement;
- negation;
- question formation;
- relative-clause strategy;
- subordination;
- coordination;
- clitic order;
- auxiliary selection;
- tense/anteriority composition;
- punctuation;
- optional variation;
- idiomatic construction ownership.

---

## 12. Entrypoint decisions

Record decisions about:

```text
abstract entrypoint
concrete grammar entrypoint
syntax/API entrypoint
language entrypoint
aggregate diagnostic entrypoint
release PGF entrypoint
expected PGF filename
```

The decision must explain why the selected surface is appropriate for:

- compilation;
- scenarios;
- application clients;
- release packaging;
- compatibility.

---

## 13. Validation decisions

Record decisions when selecting or changing:

- required scenarios;
- optional scenarios;
- scenario IDs;
- scenario entrypoints;
- required markers;
- assertion strategy;
- bounded generation policy;
- normalization version;
- gold comparison policy;
- release gates;
- checkpoint order;
- accepted warning policy.

---

## 14. Gold decisions

A significant gold update requires a decision when it reflects:

- accepted linguistic behavior change;
- changed ambiguity policy;
- changed output ordering;
- changed variant policy;
- changed normalization semantics;
- changed entrypoint;
- accepted compatibility difference;
- intentional correction of historical expectation.

A gold update made only to match current output is not a valid decision.

---

## 15. Known-issue acceptance decisions

Record a decision when a known issue is accepted as nonblocking.

The decision must identify:

```text
issue ID
scope
user-visible consequence
reason for acceptance
evidence
release duration
review trigger
mitigation
```

Acceptance does not close the issue automatically.

---

## 16. Release decisions

Record a decision when:

- a blocking item is granted a release exception;
- a supported GF version range changes;
- a release entrypoint changes;
- an artifact is added or removed;
- a required scenario is reclassified;
- a compatibility break is accepted;
- a project version classification is disputed;
- a release limitation is accepted.

---

# 17. When a decision entry is not required

A decision entry is usually unnecessary for:

- local variable rename;
- formatting;
- comments;
- private helper refactor;
- performance improvement with identical observable behavior;
- test cleanup with unchanged contract;
- typo correction;
- documentation wording correction;
- adding evidence for an already accepted decision;
- routine lexical addition using an existing paradigm;
- bug fix whose correct behavior is already fully specified.

When uncertainty exists, record the decision if future maintainers would otherwise need to reconstruct the reason.

---

# 18. Decision identifiers

Canonical format:

```text
DEC-<LANGUAGE_CODE>-<NUMBER>
```

Examples after initialization:

```text
DEC-<LANGUAGE_CODE>-001
DEC-<LANGUAGE_CODE>-002
```

Rules:

- use a zero-padded monotonically increasing number;
- never reuse an identifier;
- never renumber accepted history;
- do not encode status in the identifier;
- do not encode a module name that may later change;
- retain the original ID after supersession or retirement;
- use one ID for one coherent decision.

The active project may adopt another stable format only through an initialization decision.

---

## 19. Template identifiers

The reusable template must not contain a real project decision ID.

Use placeholders in templates:

```text
DEC-<LANGUAGE_CODE>-<NUMBER>
```

Generic examples may use:

```text
DEC-EXAMPLE-001
```

only when explicitly labeled noncanonical and illustrative.

---

# 20. Decision statuses

Canonical statuses:

```text
Proposed
Accepted
Rejected
Deferred
Superseded
Deprecated
Retired
Withdrawn
```

Every decision has exactly one current status.

---

## 21. Proposed

The decision is under review.

Implementation may exist only in an experimental branch or explicitly experimental project path.

A proposed decision must not be treated as a stable contract.

---

## 22. Accepted

The project has adopted the decision.

An accepted decision must identify:

- affected contracts;
- implementation status;
- validation requirements;
- migration requirements;
- release impact.

Accepted does not mean fully implemented.

Implementation state remains in `STATUS_LEDGER.md`.

---

## 23. Rejected

The project considered and declined the option.

A rejected decision records:

- why it was rejected;
- what was selected instead, when applicable;
- what evidence or constraints mattered.

Rejected alternatives should not be deleted when they explain future constraints.

---

## 24. Deferred

The project postponed the decision.

Required fields:

```text
reason
temporary policy
review trigger
affected work
release impact
```

A deferred decision must not create an undocumented default.

---

## 25. Superseded

A newer decision replaces this decision.

Required link:

```text
Superseded by: DEC-<LANGUAGE_CODE>-<NUMBER>
```

The old record remains unchanged except for status and supersession link.

The new record explains the changed context.

---

## 26. Deprecated

The decision remains temporarily supported but should no longer guide new work.

Required fields:

```text
replacement
migration path
deprecation date or project version
earliest removal point
```

---

## 27. Retired

The affected behavior or architecture is no longer active.

The record remains historical.

Consumers must no longer depend on the retired decision.

---

## 28. Withdrawn

A proposed decision was removed before acceptance.

Record why it was withdrawn.

Do not use `Withdrawn` to erase an accepted decision.

Accepted decisions are superseded, deprecated, or retired.

---

# 29. Decision lifecycle

Canonical lifecycle:

```text
Proposed
    → Accepted
    → Deprecated
    → Retired
```

Alternative paths:

```text
Proposed → Rejected
Proposed → Deferred
Proposed → Withdrawn
Accepted → Superseded
Deferred → Proposed
Deprecated → Superseded
```

A decision status change is itself recorded in the entry history.

---

# 30. Decision classes

Canonical decision classes:

```text
Identity
Architecture
Module
Category
Lincat
Morphology
Syntax
Lexicon
Structural
Extension
Entrypoint
Validation
Scenario
Normalization
Gold
Compatibility
Migration
Issue acceptance
Release
Documentation
Research
```

One primary class is required.

Secondary classes may be listed.

---

# 31. Impact levels

Canonical impact:

```text
Local
Cross-module
Project-wide
Release-significant
Breaking
```

---

## 32. Local impact

The decision affects one provider and no external consumer contract.

A local decision may still be recorded when linguistically important.

---

## 33. Cross-module impact

The decision changes a provider-consumer relationship.

It requires contract and dependency review.

---

## 34. Project-wide impact

The decision affects several layers, the project registry, or broad validation.

---

## 35. Release-significant impact

The decision changes:

- required scenarios;
- release entrypoint;
- expected PGF;
- accepted known issues;
- supported GF version;
- release gates;
- published behavior.

---

## 36. Breaking impact

The decision invalidates an existing supported project contract.

Examples:

```text
module rename
public symbol rename
constructor arity change
lincat field change
parameter-domain change
scenario ID change
normalization change
expected PGF rename
public abstract API change
```

A breaking decision requires project-version review.

---

# 37. Evidence levels

Recommended evidence levels:

```text
D0 — rationale only
D1 — research or historical evidence
D2 — current static project evidence
D3 — current compile/checkpoint evidence
D4 — current scenario/gold evidence
D5 — current release/artifact evidence
```

A decision may be accepted at a lower level when implementation is pending.

Its required final evidence must still be stated.

---

## 38. D0 — rationale only

The decision is based on design reasoning without external or executable evidence.

Use cautiously.

Record what evidence remains required.

---

## 39. D1 — research or historical evidence

Evidence includes:

- linguistic reference;
- upstream GF documentation;
- historical project behavior;
- migration evidence;
- comparable implementation.

Research citations belong in `RESEARCH_EVIDENCE.md`.

---

## 40. D2 — current static evidence

Evidence includes:

- source inventory;
- contract analysis;
- type or lincat inspection;
- project configuration;
- dependency graph;
- unresolved duplicate ownership.

---

## 41. D3 — current compile/checkpoint evidence

Evidence includes:

- direct provider compile;
- consumer compile;
- checkpoint pass;
- missing-linearization inspection;
- controlled failure reproduction.

---

## 42. D4 — current scenario/gold evidence

Evidence includes:

- required scenario;
- parse result;
- linearization result;
- morphology table;
- bounded generation;
- normalized output;
- reviewed gold comparison.

---

## 43. D5 — current release/artifact evidence

Evidence includes:

- release-mode run;
- final entrypoint;
- verified PGF;
- manifest;
- artifact hash;
- release gate.

---

# 44. Required decision-entry fields

Every accepted, rejected, superseded, deprecated, or retired decision must include the following fields.

| Field | Meaning |
|---|---|
| Decision ID | Stable identity |
| Title | Concise choice |
| Status | Current lifecycle status |
| Date | Decision date |
| Deciders | Responsible role or maintainers |
| Primary class | Decision category |
| Impact | Local to breaking |
| Evidence level | `D0`–`D5` |
| Context | Problem and constraints |
| Decision | Chosen rule |
| Rationale | Why it was selected |
| Alternatives | Meaningful options considered |
| Consequences | Positive, negative, and neutral effects |
| Affected contracts | Project contract IDs |
| Affected files | Providers, consumers, configuration, docs |
| Validation | Required and completed evidence |
| Migration | Required transition |
| Compatibility | Supported prior behavior |
| Issue links | Related known issues |
| Status links | Related ledger entries |
| Research links | Supporting evidence |
| Release impact | Version and gate implications |
| Review triggers | Conditions requiring reconsideration |
| Supersession | Previous or next decision IDs |
| Implementation status | Link to current state, not prose duplication |

---

# 45. Context

The context section explains the decision problem.

It should state:

- current architecture;
- observed limitation;
- constraints;
- consumers;
- why the choice cannot remain implicit;
- consequences of doing nothing.

Do not begin with the chosen answer.

A reader should understand the problem before seeing the decision.

---

# 46. Decision statement

The decision statement must be direct.

Preferred style:

```text
The project will ...
The provider for ... is ...
The release entrypoint is ...
The lincat for ... includes ...
Required scenarios will ...
```

Avoid:

```text
We might ...
It seems ...
Probably ...
For now maybe ...
```

Temporary decisions are allowed, but their temporary nature must be explicit.

---

# 47. Rationale

The rationale explains why the chosen option best satisfies the project constraints.

Useful criteria include:

```text
linguistic adequacy
GF type safety
module ownership clarity
consumer compatibility
RGL alignment
determinism
scenario coverage
release stability
migration cost
maintainability
performance
platform compatibility
```

A rationale must not claim evidence that does not exist.

---

# 48. Alternatives

Record only meaningful alternatives.

For each alternative, identify:

```text
description
advantages
disadvantages
reason rejected or deferred
conditions under which it may be reconsidered
```

Do not create artificial alternatives merely to fill the template.

---

# 49. Consequences

Separate consequences into:

```text
Positive
Negative
Neutral or operational
```

Examples:

### Positive

- one provider owns the behavior;
- consumers become simpler;
- scenarios become deterministic.

### Negative

- migration required;
- additional record field;
- more explicit constructors;
- gold updates.

### Neutral or operational

- documentation and contract files must be updated;
- release requires a new checkpoint.

---

# 50. Affected contracts

List every affected project contract ID.

Examples of domains:

```text
PIFC-CONFIG-...
PIFC-MODULE-...
PIFC-LINCAT-...
PIFC-HELPER-...
PIFC-ENTRY-...
PIFC-SCENARIO-...
PIFC-GOLD-...
PIFC-ARTIFACT-...
PIFC-DOC-...
PIFC-RELEASE-...
```

Use:

```text
None
```

only when the decision truly has no cross-file contract.

---

# 51. Affected files

Classify files by role.

```text
Providers
Direct consumers
Downstream entrypoints
Configuration
Scenarios
Inputs
Gold files
Documentation
Artifacts
```

Use project-relative paths.

Do not use local absolute paths.

---

# 52. Validation section

The validation section separates:

```text
Required evidence
Completed evidence
Remaining evidence
```

Examples:

```text
direct compile
consumer compile
checkpoint
missing-linearization check
scenario
gold comparison
PGF build
manifest verification
manual linguistic review
```

A decision may be accepted before all implementation evidence exists.

It must not be marked fully implemented or release-ready until required evidence is complete.

---

# 53. Migration section

A breaking or compatibility-sensitive decision must define:

```text
source state
target state
ordered steps
temporary adapters
consumer migration
scenario migration
gold migration
rollback
completion criteria
```

No migration should depend on memory.

---

# 54. Compatibility section

State whether the decision is:

```text
compatible
compatible extension
breaking
experimental
temporary
release-only
```

For breaking decisions, record:

- project-version impact;
- supported legacy behavior;
- deprecation window when applicable;
- migration command or manual process;
- consumer notification.

---

# 55. Issue links

List related project issues.

Format:

```text
KI-<LANGUAGE_CODE>-<NUMBER>
```

A decision may:

- resolve an issue;
- mitigate an issue;
- accept an issue;
- create a follow-up issue;
- be blocked by an issue.

State the relationship.

---

# 56. Status-ledger links

List affected implementation entries.

Examples:

```text
temporary provider
fallback constructor
blocked scenario
experimental entrypoint
deprecated helper
```

An accepted decision does not make an implementation stable automatically.

---

# 57. Research links

Link to entries in:

```text
project/docs/RESEARCH_EVIDENCE.md
```

Use stable research IDs where the project defines them.

A linguistic decision should distinguish:

- attested language evidence;
- implementation convenience;
- upstream GF constraint;
- inference.

---

# 58. Release impact

State:

```text
No release impact
Blocks affected feature
Blocks project release
Requires project PATCH
Requires project MINOR
Requires project MAJOR
Requires release exception
```

The final classification must agree with `VERSIONING_POLICY.md` and project release policy.

---

# 59. Review triggers

Examples:

- supported GF version changes;
- upstream RGL interface changes;
- new linguistic evidence;
- consumer requires a new field;
- performance becomes unacceptable;
- scenario ambiguity changes;
- migration completes;
- deprecated provider has no consumers;
- release criterion changes;
- known issue is resolved.

A permanent decision may still have review triggers.

---

# 60. Supersession links

Use explicit relationships:

```text
Supersedes: DEC-<LANGUAGE_CODE>-<NUMBER>
Superseded by: DEC-<LANGUAGE_CODE>-<NUMBER>
Related decisions:
```

A superseding decision must summarize what changed.

It must not edit the old rationale to match current thinking.

---

# 61. Decision registry

Maintain a compact registry near the beginning of the active file.

Template registry:

| Decision ID | Title | Status | Class | Impact | Date |
|---|---|---|---|---|---|
| _No project decisions recorded in the reusable template._ |  |  |  |  |  |

In the active project:

- sort by decision number;
- retain retired and rejected entries;
- update current status;
- link each row to its detailed heading where supported;
- do not remove historical rows.

---

# 62. Pending decision queue

Optional active-project section:

| Candidate | Question | Owner | Needed by | Blocking |
|---|---|---|---|---|
| `<candidate>` | `<question>` | `<owner>` | `<date or milestone>` | `yes/no` |

A pending queue is not a replacement for proposed decision entries when work has begun.

---

# 63. Decision entry template

Copy the following block for a real active-project decision.

```markdown
## DEC-<LANGUAGE_CODE>-<NUMBER> — <Decision title>

**Status:** Proposed | Accepted | Rejected | Deferred | Superseded | Deprecated | Retired | Withdrawn  
**Date:** `<YYYY-MM-DD>`  
**Deciders:** `<PROJECT_OWNER or named maintainers>`  
**Primary class:** Identity | Architecture | Module | Category | Lincat | Morphology | Syntax | Lexicon | Structural | Extension | Entrypoint | Validation | Scenario | Normalization | Gold | Compatibility | Migration | Issue acceptance | Release | Documentation | Research  
**Impact:** Local | Cross-module | Project-wide | Release-significant | Breaking  
**Evidence level:** D0 | D1 | D2 | D3 | D4 | D5  
**Project version affected:** `<version or none>`  

### Context

Describe the problem, existing state, constraints, consumers, and why an explicit decision is required.

### Decision

State the selected rule directly.

### Rationale

Explain why this choice is preferred.

### Alternatives considered

#### Alternative A — `<name>`

**Advantages**

- advantage;

**Disadvantages**

- disadvantage;

**Disposition**

Accepted, rejected, or deferred, with reason.

#### Alternative B — `<name>`

**Advantages**

- advantage;

**Disadvantages**

- disadvantage;

**Disposition**

Accepted, rejected, or deferred, with reason.

### Consequences

#### Positive

- consequence;

#### Negative

- consequence;

#### Neutral or operational

- consequence.

### Affected contracts

- `PIFC-<DOMAIN>-<NUMBER>`

### Affected files

**Providers**

- `path/to/provider.gf`

**Direct consumers**

- `path/to/consumer.gf`

**Downstream entrypoints**

- `path/to/entrypoint.gf`

**Configuration**

- `project/project.toml`

**Scenarios and inputs**

- `project/validation/scenarios/<id>.gfs`
- `project/validation/inputs/<file>`

**Gold**

- `project/validation/gold/<id>.gold`

**Documentation**

- `project/docs/<document>.md`

**Artifacts**

- `<expected artifact or none>`

### Validation

**Required evidence**

- compile/checkpoint;
- scenario;
- gold;
- PGF;
- manual review when automation is impossible.

**Completed evidence**

- `<run ID, result, or none yet>`

**Remaining evidence**

- `<remaining proof>`

### Migration

**Source state**

`<current state>`

**Target state**

`<new state>`

**Steps**

1. step;
2. step;
3. step.

**Rollback**

`<rollback or not supported>`

### Compatibility

`Compatible | Compatible extension | Breaking | Experimental | Temporary`

Explain compatibility and project-version impact.

### Related issues

- `KI-<LANGUAGE_CODE>-<NUMBER>` — `<relationship>`

### Status-ledger entries

- `<entry ID or section>`

### Research evidence

- `<research evidence ID or path>`

### Release impact

`<explicit release effect>`

### Review triggers

- trigger;
- trigger.

### Supersession

**Supersedes:** `None | DEC-<LANGUAGE_CODE>-<NUMBER>`  
**Superseded by:** `None | DEC-<LANGUAGE_CODE>-<NUMBER>`  
**Related decisions:** `None | DEC-<LANGUAGE_CODE>-<NUMBER>`

### Implementation status

Link to the current status-ledger entry and current contract documentation.

### Change history

| Date | Status | Note |
|---|---|---|
| `<YYYY-MM-DD>` | `<status>` | `<what changed>` |
```

---

# 64. Short-form decision template

A short form may be used only for a narrow, nonbreaking decision.

```markdown
## DEC-<LANGUAGE_CODE>-<NUMBER> — <Title>

**Status:** Accepted  
**Date:** `<YYYY-MM-DD>`  
**Class:** `<class>`  
**Impact:** Local | Cross-module  
**Evidence:** `<D-level>`

### Context

<problem>

### Decision

<selected rule>

### Rationale

<why>

### Consequences

- consequence;
- consequence.

### Affected files and contracts

- `path`;
- `PIFC-...`.

### Validation

- evidence.

### Review trigger

- trigger.
```

Do not use the short form for:

- breaking changes;
- release exceptions;
- normalization changes;
- gold acceptance;
- known-issue acceptance;
- module ownership transfer;
- lincat changes;
- migration decisions.

---

# 65. Example decision — illustrative only

The following is a structural example.

It is not an active project decision and must not appear in the active registry as accepted evidence.

```markdown
## DEC-EXAMPLE-001 — Keep one provider for a shared agreement parameter

**Status:** Accepted  
**Date:** `<YYYY-MM-DD>`  
**Deciders:** `<PROJECT_OWNER>`  
**Primary class:** Architecture  
**Impact:** Cross-module  
**Evidence level:** D3  
**Project version affected:** `<PROJECT_VERSION>`

### Context

Two category modules define equivalent agreement parameters. Syntax consumers import both, creating incompatible pattern matches and duplicate ownership.

### Decision

The project will define the shared agreement parameter in one lower-level resource module. Category and syntax modules will import that provider.

### Rationale

One provider removes duplicated ownership, clarifies import direction, and allows all consumers to use the same finite domain.

### Alternatives considered

#### Keep both definitions

Rejected because values with similar names remain distinct GF types.

#### Define agreement separately in each syntax module

Rejected because the duplication would expand and make cross-module constructors incompatible.

### Consequences

#### Positive

- one authoritative parameter domain;
- simpler consumer contracts;
- clearer checkpoint order.

#### Negative

- provider and consumers require coordinated migration;
- historical gold may change when incomplete branches become explicit.

### Validation

- resource compile;
- category checkpoints;
- syntax entrypoint;
- agreement scenarios.

### Review triggers

- upstream interface introduces an authoritative compatible parameter;
- consumers require a distinction not represented by the shared domain.
```

Delete or retain this example according to the project’s documentation policy.

It must remain clearly marked as noncanonical.

---

# 66. Decision proposal workflow

```text
problem identified
    ↓
evidence preserved
    ↓
affected contracts identified
    ↓
decision entry created as Proposed
    ↓
alternatives reviewed
    ↓
validation plan defined
    ↓
decision Accepted, Rejected, Deferred, or Withdrawn
```

Do not implement a cross-file contract change first and document it only after release review.

---

# 67. Acceptance workflow

Before changing status to `Accepted`:

```text
[ ] decision problem is clear
[ ] owner and deciders identified
[ ] affected providers identified
[ ] affected consumers identified
[ ] affected contracts identified
[ ] alternatives considered
[ ] rationale is evidence-based
[ ] compatibility classified
[ ] migration defined
[ ] validation requirements defined
[ ] release impact defined
[ ] related issues linked
[ ] status-ledger impact reviewed
```

Acceptance may precede completed implementation.

The implementation status must remain explicit.

---

# 68. Implementation workflow

After acceptance:

```text
1. update provider
2. update direct consumers
3. update downstream entrypoints
4. update project.toml
5. update scenarios and inputs
6. review gold
7. update dependency map
8. update current architecture/specification
9. update status ledger
10. update known issues
11. update contract lock
12. run required validation
13. attach current evidence
14. review release impact
```

A decision does not authorize isolated edits.

---

# 69. Validation workflow

Decision validation should proceed from low-level evidence to release evidence.

```text
static review
    → provider compile
    → consumer compile
    → checkpoint
    → scenario
    → gold comparison
    → entrypoint
    → PGF
    → manifest
```

Use only the levels relevant to the decision.

A release-significant decision normally requires the complete affected chain.

---

# 70. Rejection workflow

When rejecting:

- state the reason;
- preserve meaningful alternatives;
- identify the accepted replacement if one exists;
- close or redirect related issues;
- remove experimental implementation or mark it retired;
- ensure current contracts still describe actual behavior.

Do not simply delete the proposal.

---

# 71. Deferral workflow

A deferred decision must define the temporary project policy.

Example fields:

```text
Until:
Temporary provider:
Temporary scenario policy:
Release effect:
Review trigger:
```

A deferred decision with no temporary policy creates hidden behavior and is invalid.

---

# 72. Supersession workflow

To supersede:

1. create a new decision ID;
2. state changed context;
3. link the previous decision;
4. classify migration;
5. update current specifications;
6. update contracts;
7. update scenarios and gold;
8. validate;
9. mark old decision `Superseded`;
10. add reciprocal links.

Do not rewrite the original decision statement.

---

# 73. Deprecation workflow

A deprecated decision must define:

```text
replacement decision
affected consumers
deprecation start
warning or documentation policy
migration steps
earliest retirement
release impact
```

New code must follow the replacement unless an explicit compatibility path applies.

---

# 74. Retirement workflow

Before retirement:

```text
[ ] no active provider depends on the retired choice
[ ] no active consumer depends on it
[ ] project.toml no longer selects it
[ ] scenarios no longer require it
[ ] gold no longer claims it
[ ] release artifacts no longer expose it
[ ] migration evidence is complete
[ ] current docs describe the replacement
```

The historical record remains.

---

# 75. Emergency decisions

An urgent security, data-integrity, or release-evidence issue may require implementation before full review.

Emergency procedure:

1. preserve evidence;
2. implement the minimum safe correction;
3. create a decision entry immediately;
4. identify compatibility impact;
5. add regression tests;
6. update contracts and migration;
7. complete review before the correction is considered closed.

Emergency does not mean undocumented.

---

# 76. Decision and issue relationship

Use a known issue when the project has a problem to investigate or resolve.

Use a decision when the project chooses a response.

Example:

```text
KI-<LANGUAGE_CODE>-014
    identifies duplicate morphology ownership

DEC-<LANGUAGE_CODE>-027
    selects one authoritative provider
```

Closing the issue requires implementation evidence.

Accepting the decision alone is insufficient.

---

# 77. Decision and status relationship

Use the status ledger to describe current implementation state.

Example:

```text
Decision:
    use a structured pronoun record

Status ledger:
    pronoun record migration = temporary

Known issue:
    two consumers still expect legacy Str
```

These three records answer different questions.

---

# 78. Decision and contract relationship

The decision explains why.

The contract lock defines what providers and consumers must now guarantee.

Every breaking or cross-module accepted decision should identify the affected `PIFC-*` entries.

The contract lock must not merely link to a decision without stating current invariants.

---

# 79. Decision and architecture relationship

`LANGUAGE_ARCHITECTURE.md` describes current architecture.

The decision log describes how and why architecture changed.

When a decision becomes accepted and implemented:

- update current architecture;
- retain historical architecture only in the decision;
- avoid contradictory current descriptions.

---

# 80. Decision and dependency map

A module split, merge, move, or ownership transfer requires:

- decision entry;
- dependency-map update;
- import validation;
- consumer review;
- checkpoint review.

The dependency map should reflect current state, not the historical state.

---

# 81. Decision and lincat contract

A lincat decision requires the category contract to show current:

```text
provider
record shape
fields
table indices
parameter domains
consumers
invariants
```

The decision log records alternatives and migration.

---

# 82. Decision and morphology specification

A morphology decision should link to the exact section defining current:

- forms;
- parameters;
- paradigms;
- irregularity policy;
- missing-form behavior;
- validation.

Do not duplicate the full paradigm tables in the decision entry unless needed to explain the change.

---

# 83. Decision and syntax specification

A syntax decision should link to the current constructor or word-order rule.

The decision may include a concise before/after model.

The syntax specification remains the current normative description.

---

# 84. Decision and validation specification

A decision changing acceptance criteria must update:

```text
required scenario
assertions
markers
normalization
gold policy
release gates
```

The decision must explain why the prior criterion is no longer sufficient.

---

# 85. Decision and coverage matrix

When a decision adds, removes, or changes a linguistic feature:

- update its coverage state;
- link tests or scenarios;
- record partial coverage;
- create issues for remaining gaps.

An accepted feature decision with no coverage plan is incomplete.

---

# 86. Decision and gold

A gold-affecting decision must preserve:

```text
old raw output
new raw output
old normalized output
new normalized output
old gold
new gold
normalization version
review reason
```

Large unexplained gold changes block acceptance.

---

# 87. Decision and release criteria

A release-impacting decision must update release criteria before the next release approval.

Examples:

- new required scenario;
- changed required entrypoint;
- accepted nonblocking issue;
- supported GF version change;
- new artifact requirement;
- changed manifest role.

---

# 88. Decision and research evidence

Research evidence supports claims.

It does not make the implementation automatically correct.

For a linguistic decision:

```text
research source
    → project interpretation
    → selected representation
    → GF implementation
    → scenario evidence
```

Record uncertainty and dialect scope.

---

# 89. Decision and project version

Review project version when a decision is:

```text
Release-significant
Breaking
```

Typical impact:

- incompatible abstract or public grammar API → `MAJOR`;
- compatible new construction or lexical API → `MINOR`;
- compatible correction → `PATCH`.

The project version remains independent of the GF Wordbench application version.

---

# 90. Decision and GF compatibility

A decision depending on GF behavior must record:

```text
GF versions tested
GF versions supported
command or shell behavior
upstream documentation
compatibility profile
fallback behavior
```

Do not claim general GF compatibility from one local version.

---

# 91. Decision and RGL compatibility

When the project depends on an upstream RGL category, interface, resource, or paradigm:

- identify upstream module;
- identify version or revision evidence;
- state whether the project inherits, overrides, or replaces behavior;
- define compatibility tests;
- record migration impact for upstream changes.

---

# 92. Decision and project template

A project-specific decision normally belongs only in:

```text
project/docs/DECISION_LOG.md
```

Update the reusable template only when the decision changes how all future projects should be initialized.

A template-level change requires framework/template review.

Do not copy project-specific decisions back into `templates/project/`.

---

# 93. Decision evidence references

Preferred references include:

```text
run ID
summary.json path
scenario ID
gold path
PGF path and hash
source revision
GF Wordbench version
GF version
contract ID
issue ID
ledger entry
research evidence ID
```

Use project-relative or run-relative paths where applicable.

Do not store developer-specific absolute paths.

---

# 94. Manual review evidence

Manual review is acceptable only when automation cannot prove the relevant property.

Examples:

- interpretation of a linguistic source;
- judgment between grammatical variants;
- orthographic policy;
- dialect-scope approval.

Record:

```text
reviewer
date
material reviewed
criterion
result
limitations
```

Manual review does not replace compilation or scenario evidence when those are automatable.

---

# 95. Decision review cadence

Review accepted decisions when:

- a related contract changes;
- a related issue reopens;
- supported GF or RGL version changes;
- a release criterion changes;
- a consumer requests incompatible behavior;
- a workaround becomes permanent;
- a project major release is prepared;
- the decision’s explicit review trigger occurs.

Not every accepted decision needs periodic rewriting.

Review may simply confirm that it remains valid.

---

# 96. Decision history

Every detailed decision should maintain a concise history.

Example:

| Date | Status | Note |
|---|---|---|
| `<YYYY-MM-DD>` | Proposed | Initial proposal |
| `<YYYY-MM-DD>` | Accepted | Approved after checkpoint evidence |
| `<YYYY-MM-DD>` | Superseded | Replaced by `DEC-...` |

Do not use the history table as a substitute for the main rationale.

---

# 97. Editing an accepted decision

After acceptance, correct only:

- spelling;
- broken links;
- factual metadata;
- evidence references;
- status and supersession links;
- clarifications that do not change meaning.

A changed decision meaning requires a new decision ID.

Historical rationale must not be rewritten to appear more certain than it was.

---

# 98. Correcting an error in a decision record

When a record contains a factual error:

1. correct the factual field;
2. add a history note;
3. preserve the original decision meaning;
4. create a new decision if the correction changes the chosen rule.

---

# 99. Decision index maintenance

The active registry should support navigation.

Recommended ordering:

```text
numeric decision ID
```

Optional secondary indexes:

```text
by status
by class
by affected module
by contract ID
by issue ID
by project release
```

Avoid maintaining several manual indexes when they drift easily.

One canonical registry is sufficient.

---

# 100. Release review of decisions

Before project release:

```text
[ ] every breaking change has a decision
[ ] every accepted release exception has a decision
[ ] every significant gold change has a decision
[ ] every ownership transfer has a decision
[ ] every lincat migration has a decision
[ ] every required scenario reclassification has a decision
[ ] every accepted blocking issue has a decision
[ ] superseded decisions link correctly
[ ] current docs reflect accepted decisions
[ ] proposed decisions are not treated as stable
[ ] deferred decisions have temporary policy
[ ] retired decisions have no active consumers
```

---

# 101. Initialization decisions

The first active project may need decisions for:

```text
project identity
GF suffix
source layout
entrypoint roles
module-layer model
lincat strategy
morphology scope
syntax scope
validation modes
required scenario set
normalization version
release PGF
project version policy
```

Do not create empty decisions for choices that are obvious and fully governed by existing standards.

Record only choices with meaningful project-specific consequences.

---

# 102. Initial decision sequence

Recommended order:

```text
identity
    → source and module architecture
    → category/lincat representation
    → morphology
    → syntax
    → entrypoints
    → validation
    → release artifact
```

Later decisions may revisit any layer through supersession.

---

# 103. Decision review meeting

A formal meeting is optional.

For significant decisions, record:

```text
participants
materials reviewed
unresolved objections
decision authority
follow-up actions
```

Asynchronous review is valid when the record preserves the same information.

---

# 104. Consensus and authority

The project should define who accepts decisions.

Possible policies:

```text
project owner decides
maintainer consensus
domain owner with project-owner approval
release manager for release-only decisions
```

Record the policy in the active project’s initialization section or governance documentation.

The reusable template does not choose a governance model.

---

# 105. Dissent

A decision may record unresolved dissent.

Useful fields:

```text
concern
proposed alternative
risk
mitigation
review trigger
```

Dissent should not be erased after acceptance.

---

# 106. Temporary decisions

A temporary accepted decision must include:

```text
temporary reason
scope
owner
expiration or review trigger
replacement target
release limit
```

Temporary decisions should have a matching status-ledger entry.

A temporary decision without a replacement criterion is likely to become hidden permanent architecture.

---

# 107. Experimental decisions

An experimental decision must define:

- isolated scope;
- affected entrypoints;
- whether it is enabled by default;
- scenario coverage;
- persisted-output policy;
- promotion criteria;
- retirement criteria;
- release status.

Experimental behavior must not silently become part of stable release artifacts.

---

# 108. Compatibility decisions

A compatibility decision should identify:

```text
legacy form
canonical form
reader or adapter
writer behavior
warning policy
migration
support window
removal trigger
```

Canonical writers should emit current forms only.

---

# 109. Migration decisions

A migration decision requires:

```text
source versions or shapes
target version or shape
lossless fields
transformed fields
dropped fields
defaulted fields
warnings
source preservation
rollback
tests
```

Never use “migrate automatically” without defining these details.

---

# 110. Deprecation decisions

A deprecation decision must define:

```text
deprecated item
replacement
first deprecated project version
warning/documentation behavior
migration path
earliest removal version
affected consumers
tests
```

---

# 111. Release-exception decisions

A release exception must include:

```text
criterion waived
reason
risk
scope
duration
mitigation
equivalent evidence
known issue
approver
next required review
```

A permanent exception should be converted into a normal release-policy decision.

---

# 112. Accepted known-issue decisions

When accepting an unresolved issue:

- link the issue;
- state why it is nonblocking;
- state who is affected;
- state what behavior remains unsupported;
- state how the limitation appears in release notes;
- state the review trigger;
- state whether future releases may continue the acceptance.

No issue is accepted by silence.

---

# 113. Performance decisions

Performance may justify a decision when it changes:

- generation bounds;
- table representation;
- module split;
- caching;
- scenario scope;
- release timeout;
- variant policy.

Performance evidence must remain secondary to linguistic and contract correctness.

---

# 114. Security and integrity decisions

Decisions involving:

```text
shell escape
external files
path containment
source overwrite
gold write
artifact overwrite
secret data
unsafe scenario commands
```

require explicit security review.

A project decision cannot override framework safety contracts silently.

---

# 115. Prohibited decision behavior

The following are prohibited:

- changing a contract without a decision when one is required;
- recording a decision only after release to justify undocumented behavior;
- deleting rejected or superseded history;
- rewriting old rationale to match current beliefs;
- treating a proposed decision as accepted;
- treating an accepted decision as implemented automatically;
- using free-form status values;
- leaving compatibility or release impact unstated;
- accepting a known issue without issue ID and review trigger;
- updating gold without explaining material behavior change;
- using a decision record as the only current architecture specification;
- storing local machine paths;
- including secrets;
- citing a historical fixture as current proof;
- claiming linguistic authority without research or review evidence;
- retaining an active consumer of a retired decision;
- copying project-specific decisions into the reusable template.

---

# 116. Decision-log anti-drift indicators

Drift exists when:

- a breaking contract change has no decision entry;
- a decision references a missing contract ID;
- an accepted decision contradicts current architecture;
- a superseded decision has no replacement link;
- a new decision claims to supersede an old one without reciprocal link;
- a retired decision still has active consumers;
- a deferred decision has no temporary policy;
- a temporary decision has no status-ledger entry;
- a release exception has no expiration or review trigger;
- a gold changes without a relevant decision or issue;
- a lincat changes without a decision;
- module ownership moves without a decision;
- a decision references an old language suffix;
- the active registry contains unresolved placeholders;
- the reusable template contains active project decisions;
- project version impact is omitted for breaking decisions;
- completed evidence is claimed without a run, scenario, or review reference;
- current specifications copy historical alternatives as current requirements.

Any drift indicator requires review.

---

# 117. Automated consistency checks

A future project checker should verify:

```text
unique decision IDs
valid statuses
valid classes
valid impact levels
valid evidence levels
supersession links resolve
related issue IDs resolve
contract IDs resolve
active-project placeholders are absent
template remains generic
retired decisions have no configured consumer where detectable
breaking changes referenced by release review
gold changes link to review evidence
```

Automation cannot judge the quality of the rationale.

Human review remains required.

---

# 118. Template validation checklist

Use for:

```text
templates/project/docs/DECISION_LOG.md
```

```text
[ ] file remains language-neutral
[ ] active project owner is not inserted
[ ] no active module name appears
[ ] no active source path appears
[ ] no local absolute path appears
[ ] no active issue ID appears
[ ] no active decision ID appears
[ ] placeholders are documented
[ ] statuses are canonical
[ ] decision template is complete
[ ] example is labeled noncanonical
[ ] document links match template structure
[ ] project contract lock relationship is current
[ ] no release claim is made
```

---

# 119. Active-project initialization checklist

Use after copying to:

```text
project/docs/DECISION_LOG.md
```

```text
[ ] metadata placeholders replaced
[ ] project decision-ID format confirmed
[ ] decision authority defined
[ ] registry initialized
[ ] example removed or retained as clearly illustrative
[ ] initial architecture choices reviewed
[ ] entrypoint choices reviewed
[ ] lincat choices reviewed
[ ] validation choices reviewed
[ ] release PGF choice reviewed
[ ] related contract IDs exist
[ ] related issue and ledger files initialized
[ ] no unresolved required placeholder remains
```

---

# 120. Decision proposal checklist

```text
[ ] problem is specific
[ ] decision is needed
[ ] owner is identified
[ ] consumers are identified
[ ] alternatives are real
[ ] rationale is evidence-based
[ ] compatibility is classified
[ ] migration is defined
[ ] validation is defined
[ ] issue and ledger relationships are defined
[ ] release impact is defined
[ ] review triggers are defined
```

---

# 121. Decision acceptance checklist

```text
[ ] decision ID is unique
[ ] status becomes Accepted
[ ] date is actual
[ ] deciders are listed
[ ] context is complete
[ ] decision statement is unambiguous
[ ] alternatives are documented
[ ] consequences are balanced
[ ] contracts are listed
[ ] affected files are listed
[ ] required evidence is listed
[ ] migration is actionable
[ ] project version impact is reviewed
[ ] current specifications are scheduled for update
```

---

# 122. Decision implementation checklist

```text
[ ] provider updated
[ ] direct consumers updated
[ ] downstream entrypoints reviewed
[ ] imports updated
[ ] public symbols reviewed
[ ] lincat fields reviewed
[ ] project.toml reviewed
[ ] scenarios reviewed
[ ] inputs reviewed
[ ] gold reviewed
[ ] dependency map updated
[ ] current specifications updated
[ ] status ledger updated
[ ] known issues updated
[ ] contract lock updated
[ ] checkpoint passes
[ ] release-level evidence passes when applicable
[ ] decision evidence links added
```

---

# 123. Decision supersession checklist

```text
[ ] new decision created
[ ] previous decision linked
[ ] changed context explained
[ ] migration classified
[ ] current documents updated
[ ] contracts updated
[ ] old decision marked Superseded
[ ] reciprocal link added
[ ] consumers migrated
[ ] scenarios and gold reviewed
[ ] release impact reviewed
```

---

# 124. Release decision checklist

```text
[ ] all release-significant decisions are Accepted
[ ] required implementation is complete
[ ] required evidence is current
[ ] no Proposed decision is used as policy
[ ] deferred decisions have release treatment
[ ] accepted issues have explicit decisions
[ ] release exceptions remain valid
[ ] expected PGF decision matches project.toml
[ ] required scenarios match validation spec
[ ] normalization and gold decisions agree
[ ] project version reflects breaking decisions
[ ] release notes mention user-visible consequences
```

---

# 125. Decision registry template

Replace the placeholder registry in the active project.

```markdown
## Decision registry

| Decision ID | Title | Status | Class | Impact | Project version | Date |
|---|---|---|---|---|---|---|
| `DEC-<LANGUAGE_CODE>-001` | `<title>` | `<status>` | `<class>` | `<impact>` | `<version>` | `<YYYY-MM-DD>` |
```

Add detailed entries after the registry.

---

# 126. Governance initialization template

The active project may add:

```markdown
## Decision authority

**Project owner:** `<PROJECT_OWNER>`

**Acceptance policy**

- `<who may propose>`;
- `<who reviews linguistic decisions>`;
- `<who reviews architecture decisions>`;
- `<who approves release exceptions>`;
- `<how unresolved disagreement is handled>`.

**Required review**

- breaking decisions;
- release-significant decisions;
- accepted known issues;
- normalization changes;
- gold behavior changes.
```

The reusable template does not select one governance model.

---

# 127. Decision metadata normalization

Use:

```text
date: YYYY-MM-DD
project version: MAJOR.MINOR.PATCH
status: canonical capitalization
impact: canonical value
evidence: D0–D5
paths: project-relative with /
```

Do not use:

```text
today
latest
current
TBD
maybe
n/a
```

without an owning field that explicitly allows them.

Use `None` or `Not applicable` when appropriate.

---

# 128. Versioning of this log

The decision-log template version identifies the structure of this documentation template.

It is not:

- the project version;
- a decision version;
- the contract-lock version;
- the GF Wordbench application version;
- the GF version.

Changing the template structure may require a template-version change.

Existing active decision history should be migrated without losing meaning.

---

# 129. Migrating an existing decision log

When importing historical notes:

1. preserve the original file;
2. inventory decisions;
3. assign stable IDs;
4. identify current status;
5. distinguish decisions from issues and tasks;
6. preserve original dates when known;
7. mark unknown dates honestly;
8. link current contracts;
9. link superseded choices;
10. avoid inventing rationale;
11. add current evidence separately;
12. validate the resulting current specifications.

Historical ambiguity must remain visible.

---

# 130. Converting meeting notes

Meeting notes become a decision entry only when they contain an actual choice.

Conversion should preserve:

```text
date
participants
question
choice
alternatives
reason
actions
```

Do not copy unrelated discussion into the decision log.

Retain original meeting evidence when required.

---

# 131. Converting source comments

A source comment describing an architectural choice may be migrated into a decision entry.

After migration:

- source comment may summarize and link;
- decision log owns historical rationale;
- current specification owns the current rule.

Do not leave the only explanation in one source file.

---

# 132. Converting issue resolutions

When an issue resolution selects a durable architecture:

- keep the issue history;
- create a decision entry;
- link both records;
- update current contracts;
- close the issue only after validation.

---

# 133. Converting gold-review notes

When a gold review accepts a meaningful behavior change:

- create or update the decision;
- record old and new behavior;
- identify normalization version;
- link scenario and gold;
- update release impact.

Minor correction to an already specified expected form may only require issue and changelog updates.

---

# 134. Project clone behavior

When a project is cloned:

- retain its decision history;
- update only project metadata that actually changes;
- do not reset accepted decisions to template placeholders;
- add new decisions for deliberate divergence;
- preserve supersession chains;
- update research and evidence paths when locations change.

The reusable template contains no active history.

---

# 135. Project reset behavior

A project reset must not silently delete decision history.

Before reset:

- preserve active project decisions;
- preserve issues and status ledger;
- preserve release evidence;
- identify whether reset creates a new project identity.

A genuinely new GF project should begin with the generic template, not inherited unrelated decisions.

---

# 136. Decision portability

Decision records should remain portable.

Use:

```text
project-relative source paths
project-relative scenario/gold paths
run IDs or run-relative evidence paths
stable contract IDs
stable issue IDs
```

Avoid:

```text
local drive paths
developer home directories
IDE links unavailable to other maintainers
ephemeral terminal output without retained evidence
```

---

# 137. Confidential information

Do not record:

- secrets;
- tokens;
- private keys;
- personal credentials;
- complete environment dumps;
- sensitive unpublished source text beyond what the project policy permits.

A private security decision may reference a restricted evidence location.

The public log should retain enough nonsecret rationale to explain the resulting contract.

---

# 138. Historical accuracy

The log should distinguish:

```text
known at the time
learned later
current interpretation
```

Do not rewrite old decisions to pretend later evidence was available earlier.

Use change-history notes and superseding decisions.

---

# 139. Decision quality criteria

A high-quality decision is:

- specific;
- bounded;
- evidence-aware;
- explicit about uncertainty;
- explicit about compatibility;
- explicit about migration;
- linked to current contracts;
- linked to validation;
- understandable without private memory;
- stable enough to guide consumers.

Length alone does not determine quality.

---

# 140. Common decision-log mistakes

## 140.1 Recording implementation without the reason

Result:

- future maintainers cannot judge alternatives.

Correction:

- add context and rationale.

## 140.2 Recording the reason without the selected rule

Result:

- consumers cannot know the contract.

Correction:

- write a direct decision statement.

## 140.3 Treating a proposal as policy

Result:

- implementation and documentation diverge.

Correction:

- enforce status semantics.

## 140.4 Editing old decisions instead of superseding

Result:

- historical reasoning disappears.

Correction:

- create a new ID and link both records.

## 140.5 Duplicating current specifications

Result:

- the decision log becomes stale.

Correction:

- summarize the choice and link to current owner documents.

## 140.6 Omitting negative consequences

Result:

- migration and maintenance cost are hidden.

Correction:

- record tradeoffs honestly.

## 140.7 Accepting gold changes without cause

Result:

- regressions become expected.

Correction:

- preserve and review raw and normalized differences.

## 140.8 Leaving temporary choices without expiry

Result:

- fallback becomes permanent.

Correction:

- define review trigger and ledger entry.

## 140.9 Using historical fixtures as current proof

Result:

- decision appears better supported than it is.

Correction:

- classify evidence accurately.

---

# 141. Template anti-contamination rules

This reusable file must not contain active identifiers such as:

```text
a real language name
a real GF suffix
real module names
real project issue IDs
real project decision IDs
real release artifacts
local absolute paths
```

Generic technical names such as:

```text
project.toml
summary.json
manifest.json
.gfs
.gold
.pgf
```

are allowed because they belong to the framework/project contract.

---

# 142. Final invariants

1. The reusable decision log remains language-neutral.
2. The active decision log records real project choices.
3. Every decision has one stable ID.
4. Decision IDs are never reused.
5. Accepted history is never deleted.
6. Changed meaning requires a new decision.
7. Superseded decisions link to replacements.
8. Proposed decisions are not stable policy.
9. Accepted decisions are not automatically implemented.
10. Current state remains in current specification documents.
11. Issues record problems; decisions record choices.
12. The status ledger records implementation state.
13. Contract locks record current provider-consumer promises.
14. Significant module ownership changes require decisions.
15. Significant lincat changes require decisions.
16. Significant constructor and word-order changes require decisions.
17. Entrypoint and PGF changes require decisions.
18. Required scenario and normalization changes require decisions.
19. Significant gold behavior changes require decisions.
20. Accepted known issues require decisions.
21. Release exceptions require decisions.
22. Breaking decisions review project version.
23. Decision evidence is classified honestly.
24. Historical fixtures are not current proof.
25. Paths remain project-relative or run-relative.
26. Temporary decisions have review triggers.
27. Deprecated decisions have migration paths.
28. Retired decisions have no active consumers.
29. Project-specific decisions do not leak into the reusable template.
30. Implementation, contracts, validation, and release evidence must agree with accepted decisions.

---

# 143. Final rule

The project decision log follows one durable reasoning chain:

```text
project problem
    → preserved context and evidence
    → explicit alternatives
    → deliberate choice
    → compatibility and migration
    → coordinated implementation
    → contract and documentation updates
    → validation
    → release evidence
    → later review or supersession
```

A decision is complete only when future maintainers can understand:

```text
what was chosen
why it was chosen
what it changed
how it was proven
what would cause it to change again
```

The log preserves that reasoning without replacing the current project specifications or executable evidence.
