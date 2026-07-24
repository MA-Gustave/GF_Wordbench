# GF Wordbench Project — Release Exceptions Register

| Field | Value |
|---|---|
| Document role | Project release-exception and constraint register |
| Decision status | Accepted |
| Canonical path | `project/docs/STATUS_LEDGER__PROJECT_DOCS.md` |
| Applies to | The single active GF language project in this GF Wordbench workspace |
| Project identity authority | `project/project.toml` |
| Project contract authority | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Release authority | `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md` |
| Alignment authority | `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` |
| Owner | Active project maintainers |
| Document version | `2.0.0` |
| Last reviewed | `2026-07-24` |

---

## 1. Purpose

This document records only project conditions that materially affect a release decision and are not already fully owned by another project document.

It exists for:

- unresolved release blockers;
- explicitly accepted release exceptions;
- external constraints that prevent a required release gate;
- migration exceptions that affect current project artifacts;
- closure evidence for previously recorded exceptions.

It does not track ordinary development progress.

The governing rule is:

> Record only conditions that change what may be claimed, validated, packaged or released for the active project.

---

## 2. No implementation-status tracking

This document does not classify source, modules, features or documents as:

```text
implemented
partially implemented
planned
proposed
experimental
temporary
fallback
stable
historical
unknown
```

It does not require updates after every source change.

It does not record:

- development milestones;
- ordinary unfinished work;
- temporary coding choices that do not affect a release claim;
- task ownership;
- sprint priorities;
- progress percentages;
- feature-completion states;
- speculative future work;
- routine refactoring;
- every warning emitted during development.

Project documentation describes the accepted product and language contracts directly.

---

## 3. Relationship to other project records

Use the authoritative owner for each type of information.

| Information | Authoritative owner |
|---|---|
| Active project identity | `project/project.toml` |
| Provider and consumer contracts | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Language architecture | `project/docs/LANGUAGE_ARCHITECTURE.md` |
| Linguistic behavior | `project/docs/MORPHOLOGY_SPEC.md` and `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| Validation obligations | `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md` |
| Requirement-to-evidence mapping | `project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md` |
| Confirmed defects and limitations | `project/docs/KNOWN_ISSUES.md` |
| Accepted design decisions | `project/docs/DECISION_LOG.md` |
| Release gates | `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md` |
| Research sources and unresolved research conflicts | `project/docs/RESEARCH_EVIDENCE.md` |
| Release blockers and accepted exceptions | this document |

This document links to those owners instead of duplicating their full content.

---

## 4. Scope

A record belongs here only when all of the following are true:

1. the condition affects the active project;
2. the condition changes a release claim, release gate or distributed artifact;
3. the condition is supported by evidence;
4. the condition cannot be represented completely by a link to an existing known issue, decision or release criterion;
5. the condition requires explicit release treatment.

Examples:

- a required entrypoint cannot compile because of an external GF/RGL constraint;
- a required PGF cannot be produced for the intended release;
- a required scenario is excluded by a documented release decision;
- a known issue is accepted for one named release;
- a migration leaves one documented compatibility limitation;
- a required research decision remains unresolved and blocks a linguistic claim.

---

## 5. Non-scope

Do not create entries here for:

- ordinary coding work;
- incomplete internal helpers;
- placeholders that do not affect the documented release surface;
- routine warnings with no release effect;
- defects already fully described in `KNOWN_ISSUES.md`;
- decisions already fully described in `DECISION_LOG.md`;
- missing tests already represented in `TEST_COVERAGE_MATRIX__PROJECT_DOCS.md`;
- release gates already represented without exception in `RELEASE_CRITERIA__PROJECT_DOCS.md`;
- framework defects outside the active language project;
- generated run artifacts;
- local editor or machine-state files;
- `gf-portfolio` concerns.

`gf-portfolio` is an independent product and does not participate in Wordbench project release decisions.

---

## 6. Record kinds

Each entry uses one of these kinds:

```text
release_blocker
accepted_exception
external_constraint
migration_exception
```

### 6.1 `release_blocker`

A mandatory release criterion cannot currently be satisfied.

A blocker remains open until:

- the criterion passes;
- the release scope is changed by an accepted decision; or
- the affected capability is removed from the release.

### 6.2 `accepted_exception`

A named release explicitly accepts a bounded deviation.

An accepted exception requires:

- a decision reference;
- a named release;
- a bounded scope;
- a risk statement;
- a reviewer;
- current evidence;
- an expiry or closure condition.

An accepted exception does not rewrite the underlying specification or contract.

### 6.3 `external_constraint`

A required result depends on a tool, source, platform, license or external decision outside the project’s direct control.

The entry identifies:

- the external dependency;
- the affected project claim;
- the evidence;
- the condition that removes the constraint.

### 6.4 `migration_exception`

A migration preserves a documented compatibility limitation that affects current release artifacts or consumers.

The entry identifies:

- the source format or project state;
- the canonical destination;
- the retained limitation;
- the affected consumers;
- the closure condition.

---

## 7. Entry identifiers

Each entry has a stable identifier:

```text
EXC-<DOMAIN>-<NUMBER>
```

Examples:

```text
EXC-RELEASE-001
EXC-PGF-001
EXC-SCENARIO-002
EXC-MIGRATION-001
EXC-RESEARCH-001
```

IDs are never reused.

Recommended domains:

```text
CONFIG
MODULE
MORPH
SYNTAX
LEXICON
ENTRY
SCENARIO
GOLD
PGF
VALIDATION
RESEARCH
TOOL
MIGRATION
RELEASE
```

---

## 8. Required entry fields

Every open entry contains:

| Field | Requirement |
|---|---|
| Entry ID | Stable `EXC-<DOMAIN>-<NUMBER>` |
| Kind | One registered record kind |
| Title | Concise description |
| Affected release | Named release or release family |
| Affected scope | Exact project capability, artifact or claim |
| Release effect | What cannot be claimed, validated, packaged or released |
| Authority | Contract, specification, issue or criterion owning the rule |
| Evidence | Current project-relative or run-relative evidence |
| Decision | Required for accepted exceptions |
| Owner | Maintainer, role or external owner |
| Introduced | ISO date, commit or release |
| Last reviewed | ISO date or release |
| Closure condition | Objective condition for removal from the open register |

Conditional fields:

```text
external dependency
known issue
affected entrypoints
affected scenarios
affected gold files
affected artifacts
risk
reviewer
expiry
migration path
```

---

## 9. Evidence rules

Evidence must be:

- current;
- specific;
- traceable;
- associated with the relevant source state;
- associated with the GF and RGL identity when relevant;
- sufficient to support the stated release effect.

Accepted evidence includes:

```text
checkpoint compilation
entrypoint compilation
native .gfs scenario
normalized scenario output
gold comparison
PGF build
run summary
artifact manifest
raw GF diagnostic
source fingerprint
manual review with named method
research source
```

Use project-relative or run-relative paths.

Examples:

```text
project/validation/scenarios/parse.gfs
project/validation/gold/parse.gold
run_<run-id>/summary.json
run_<run-id>/raw/compile/<target>.stderr.txt
run_<run-id>/manifest.json
```

A chat message or unpreserved console output is not sufficient release evidence.

---

## 10. Entry template

```markdown
## EXC-<DOMAIN>-<NUMBER> — <title>

**Kind:** `release_blocker | accepted_exception | external_constraint | migration_exception`  
**Affected release:** `<release or release family>`  
**Owner:** `<maintainer, role, external owner, or unassigned>`  
**Introduced:** `<YYYY-MM-DD, release, or commit>`  
**Last reviewed:** `<YYYY-MM-DD or release>`

### Affected scope

Describe the exact project capability, artifact or claim.

### Release effect

Describe what cannot be claimed, validated, packaged or released.

### Authority

```text
<contract ID, specification, release criterion, known issue or decision>
```

### Evidence

```text
<project-relative or run-relative evidence>
```

### Risk

Describe the consequence of releasing with the condition.

### Decision

Required only for `accepted_exception`.

```text
<decision ID or not applicable>
```

### External dependency

Use when applicable.

```text
<tool, source, platform, license, authority or none>
```

### Closure condition

Describe the objective condition for removing the entry from the open register.

### Related records

```text
<known issues, decisions, contracts, scenarios, golds or none>
```
```

---

## 11. Open release blockers

| Entry ID | Affected release | Scope | Release effect | Authority | Owner | Evidence |
|---|---|---|---|---|---|---|
| — | — | No blocker recorded | — | — | — | — |

The empty table is not evidence that all release gates pass.

Release readiness is established by current validation evidence and `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md`.

---

## 12. Accepted release exceptions

| Entry ID | Release | Scope | Decision | Reviewer | Risk | Expiry |
|---|---|---|---|---|---|---|
| — | — | No exception recorded | — | — | — | — |

No exception exists unless it is entered here and linked to an accepted decision.

---

## 13. External constraints

| Entry ID | Affected release | Dependency | Scope | Release effect | Owner | Closure condition |
|---|---|---|---|---|---|---|
| — | — | No external constraint recorded | — | — | — | — |

---

## 14. Migration exceptions

| Entry ID | Source | Canonical destination | Retained limitation | Affected consumers | Closure condition |
|---|---|---|---|---|---|
| — | — | No migration exception recorded | — | — | — |

---

## 15. Resolved history

Move an entry here when its closure condition is satisfied.

A resolved record retains:

```text
entry ID
former kind
resolution
closing evidence
affected consumer review
contract or specification updates
closed date
```

Resolved entries may be removed only when they have no continuing migration, release or architectural value.

---

## 16. Review triggers

Review this document:

- before a release decision;
- when a release blocker is introduced or removed;
- when an exception is proposed, accepted, expires or closes;
- when a relevant external constraint changes;
- when a migration exception changes;
- when the active project is replaced;
- during maintainer handoff.

No fixed weekly or monthly status-maintenance cycle is required.

Ordinary source changes do not require an update unless they change an entry governed by this document.

---

## 17. Release review

Before approving a release:

```text
[ ] every open release blocker is reviewed
[ ] every accepted exception names a release and decision
[ ] every accepted exception has current evidence
[ ] every exception expiry is checked
[ ] every external constraint is reassessed
[ ] every migration exception is reassessed
[ ] RELEASE_CRITERIA__PROJECT_DOCS.md agrees with this register
[ ] KNOWN_ISSUES.md agrees with this register
[ ] DECISION_LOG.md contains the referenced decisions
[ ] current run evidence supports the release decision
```

A release cannot rely on an exception that is absent, expired or unsupported by evidence.

---

## 18. Automated checks

`docs/usage/CLI_REFERENCE.md` owns the exact command surface for project-document validation.

Automated checks verify:

```text
entry IDs are unique
record kinds are canonical
required fields are present
evidence paths use approved bases
authority references resolve
accepted exceptions reference decisions
accepted exceptions name releases
accepted exceptions include expiry or closure conditions
open blockers appear in the blocker summary
resolved IDs are not reused
```

Automation must not create or accept release exceptions automatically.

---

## 19. Drift indicators

Drift exists when:

- ordinary implementation progress is tracked here;
- a release blocker has no entry;
- an exception is accepted only in chat or source comments;
- an accepted exception lacks a decision;
- an accepted exception lacks current evidence;
- an accepted exception has expired;
- a known issue and this register contradict one another;
- release criteria and this register contradict one another;
- an external constraint no longer exists but remains open;
- a resolved entry lacks closing evidence;
- a Portfolio dependency appears in a Wordbench release condition;
- the file becomes a generic task backlog.

A contradiction is resolved through the authoritative owner, not by choosing the most convenient document.

---

## 20. Project reset

When the active language project is replaced:

```text
[ ] close or archive project-specific open records
[ ] retain only necessary migration history
[ ] verify the new project identity from project.toml
[ ] reassess release blockers
[ ] reassess accepted exceptions
[ ] reassess external constraints
[ ] reassess migration exceptions
[ ] record the review
```

The generic project template must not contain populated project-specific entries.

---

## 21. Governing rule

> GF Wordbench project documentation describes the accepted project directly. This register records only explicit release blockers, accepted exceptions, external constraints and migration exceptions that materially change a release decision.

No implementation-progress vocabulary is required, and no entry is updated merely because development advances.
