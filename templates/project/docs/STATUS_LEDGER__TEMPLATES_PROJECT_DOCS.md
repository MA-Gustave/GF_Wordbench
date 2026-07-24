# GF Wordbench Project Template — Issues and Release Blockers

**Document ID:** `GF-WB-PROJECT-ISSUES-AND-BLOCKERS`  
**Status:** Normative project template  
**Applies to:** One active GF language project created from `templates/project/`  
**Template owner:** GF Wordbench maintainers  
**Project owner after initialization:** `<PROJECT_OWNER>`  
**Project ID:** `<PROJECT_ID>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**GF module suffix:** `<GF_SUFFIX>`  
**Configuration authority:** `project/project.toml`  
**Known-issue authority:** `project/docs/KNOWN_ISSUES.md`  
**Validation authority:** `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md`  
**Coverage authority:** `project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md`  
**Release authority:** `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md`  
**Decision authority:** `project/docs/DECISION_LOG.md`  
**Contract authority:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Template version:** `2.0.0`  
**Last reviewed:** `<YYYY-MM-DD>`  
**Repository path:** `templates/project/docs/STATUS_LEDGER__TEMPLATES_PROJECT_DOCS.md`

---

## 1. Purpose

This document records only concrete unresolved project problems, release blockers and approved release exceptions that require coordinated visibility.

It does not track implementation maturity, development progress or changing implementation status.

The repository filename is retained for project-template path compatibility. Its content is an issue-and-blocker register.

Use this register when an unresolved condition materially affects one or more of:

- linguistic correctness;
- GF compilation;
- required scenarios;
- gold comparison;
- artifact integrity;
- security;
- portability;
- reproducibility;
- public project contracts;
- release criteria.

Do not create entries merely because work is planned, incomplete, experimental, temporary or under active development.

The governing rule is:

> Record concrete unresolved impact and the evidence required to resolve it; describe ordinary project behavior directly in its owning specification.

---

## 2. Template use

The reusable template remains generic.

When initializing an active project, copy this file to:

```text
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
```

Then:

1. replace the required project metadata placeholders;
2. remove template examples that do not apply;
3. record only active issues, blockers or release exceptions;
4. assign one owner to every entry;
5. identify current evidence;
6. state validation and release impact;
7. define an objective resolution condition;
8. link the authoritative issue, decision, contract and requirement records.

An active project must not retain unresolved metadata placeholders while claiming release readiness.

---

## 3. Intentional placeholders

The template may use placeholders such as:

```text
<PROJECT_OWNER>
<PROJECT_ID>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
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
<YYYY-MM-DD>
```

Rules:

- placeholders are valid in `templates/project/`;
- active entries must use concrete project values;
- placeholders are never interpreted as real project facts;
- examples remain clearly labeled;
- active-project checks reject unresolved required placeholders.

---

## 4. What belongs here

Create an entry when a concrete unresolved condition:

- prevents a required module, entrypoint or scenario from validating;
- makes causal diagnosis ambiguous for a required failure;
- leaves a required gold file unavailable or unreviewed;
- prevents production or verification of a required artifact;
- creates a known security or containment risk;
- makes a required contract inconsistent across providers and consumers;
- blocks a release gate;
- requires a documented release exception;
- prevents reliable support for a required GF, Python or platform combination;
- leaves required evidence unavailable for a claimed release criterion.

Examples:

```text
required scenario cannot execute because its entrypoint does not compile
required PGF identity is unresolved
required gold file is missing
source and contract lock disagree on a public lincat
GF version changes diagnostic output in a way not yet normalized safely
release artifact cannot be verified through the manifest
security review found an unbounded or unsafe scenario operation
```

---

## 5. What does not belong here

Do not use this file to track:

- implementation progress;
- planned features;
- ordinary backlog tasks;
- scaffolding inventories;
- provisional or experimental labels;
- temporary implementation labels;
- promotion to stable;
- completed work;
- general documentation completeness;
- routine refactoring;
- private implementation details;
- issue-tracker milestones;
- deprecated API schedules already owned by compatibility documentation;
- historical conditions that no longer affect the active project.

Use the appropriate owner instead:

| Information | Owner |
|---|---|
| Defect analysis and limitations | `KNOWN_ISSUES.md` |
| Durable architectural or linguistic decisions | `DECISION_LOG.md` |
| Required validation behavior | `VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md` |
| Requirement-to-evidence mapping | `TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md` |
| Release gates and accepted exceptions | `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md` |
| Provider and consumer contracts | `INTERFILE_CONTRACT_LOCK.md` |
| Work planning | Issue tracker |
| Local implementation explanation | Source comments |
| Compatibility and deprecation | Framework compatibility documentation |

This register provides a concise cross-reference for unresolved project impact. It does not replace those owners.

---

## 6. Entry identifiers

Entry IDs use:

```text
PROJ-ISSUE-<NUMBER>
```

Examples:

```text
PROJ-ISSUE-001
PROJ-ISSUE-002
```

Rules:

- IDs are unique within the active project;
- IDs are never reused;
- titles may change without changing the ID;
- closed entries are removed from the active register after their resolution is recorded by the owning issue, decision or release record;
- version control preserves document history.

No domain-specific status vocabulary is encoded in the ID.

---

## 7. Entry categories

A category identifies the nature of the unresolved condition. It is not an implementation status.

Allowed categories:

```text
defect
dependency blocker
validation gap
evidence gap
artifact integrity
contract conflict
security risk
tool compatibility
release exception
migration constraint
```

A project may add a category only when its meaning is documented and it does not create a maturity or progress classification scheme.

---

## 8. Required fields

Every entry contains:

```text
ID
title
category
problem statement
affected objects
owner
evidence
validation impact
release impact
dependencies
resolution condition
related records
last reviewed
```

Use `not applicable` explicitly where necessary.

Do not add fields for:

```text
implementation status
expected stable behavior
promotion state
target maturity
completion percentage
experimental state
temporary state
fallback state
```

---

## 9. Compact active register

The active project keeps a compact table near the top of this file.

Template:

| ID | Category | Affected object | Problem | Validation impact | Release impact | Owner |
|---|---|---|---|---|---|---|
| `PROJ-ISSUE-001` | `<category>` | `<FILE/MODULE/SCENARIO>` | `<concise problem>` | `<impact>` | `<blocking/nonblocking/conditional>` | `<OWNER>` |

Remove the example row from the active project.

When no entry exists, use:

```text
No active project issues or release blockers are recorded in this register.
```

An empty register does not itself prove release readiness. `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md` remains authoritative.

---

## 10. Detailed entry template

```markdown
## PROJ-ISSUE-<NUMBER> — <Title>

**Category:** <category>  
**Owner:** <OWNER>  
**Last reviewed:** <YYYY-MM-DD>  
**Release impact:** blocking | nonblocking | conditional

### Problem

<Describe the concrete unresolved condition and why it matters.>

### Affected objects

- `<FILE or MODULE>`;
- `<ENTRYPOINT>`;
- `<SCENARIO_ID>`;
- `<GOLD_FILE>`;
- `<ARTIFACT>`;
- `<DOCUMENT>`.

### Evidence

- Structured result: `<run-relative result or record>`;
- Raw evidence: `<run-relative artifact path>`;
- Source evidence: `<project-relative path>`;
- Contract evidence: `<CONTRACT_ID>`;
- Manual review: `<record or not applicable>`.

### Validation impact

- Requirement: `<REQUIREMENT_ID>`;
- Checkpoint or entrypoint: `<identifier>`;
- Scenario: `<SCENARIO_ID or not applicable>`;
- Gold or assertion: `<reference or not applicable>`;
- Observable result: `<FAIL/ERROR/SKIPPED/unknown condition>`.

### Release impact

<State exactly which release criterion is affected.>

For a conditional impact, define the condition and its evidence.

### Dependencies

- Blocking dependency: `<ID, object or none>`;
- Affected consumers: `<consumers>`;
- Downstream effects: `<effects or none>`.

### Resolution condition

<Define objective evidence required to remove this entry from the active register.>

### Related records

- Known issue: `<ISSUE_ID>`;
- Decision: `<DECISION_ID or not applicable>`;
- Contract: `<CONTRACT_ID>`;
- Coverage row: `<reference>`;
- Release criterion: `<reference>`.
```

---

## 11. Evidence requirements

Evidence preference:

1. current project configuration;
2. current source;
3. current project contract lock;
4. current structured validation result;
5. current raw evidence;
6. current scenario and gold result;
7. current artifact and manifest;
8. current manual review;
9. historical evidence as supporting context only.

Historical logs do not establish current project behavior by themselves.

Every blocking entry must identify evidence that can be reproduced or reviewed.

A report excerpt is not a substitute for its structured result or raw source artifact.

---

## 12. Validation impact

An entry states how validation exposes the condition.

Examples:

```text
direct module compilation failure
entrypoint compilation failure
required scenario failure
required scenario skipped because a provider failed
gold mismatch
required artifact absence
configuration validation error
manifest verification error
manual contract review
```

Do not classify downstream effects as independent root causes when a blocker is known.

A validation gap identifies:

- the unproven requirement;
- existing evidence;
- missing evidence;
- risk;
- required scenario, assertion or review;
- release impact.

“Not tested” is not equivalent to “works.”

---

## 13. Release impact

Allowed values:

```text
blocking
nonblocking
conditional
```

These values describe release impact, not implementation status.

### Blocking

The release criterion cannot pass while the issue remains unresolved.

### Nonblocking

The issue is outside the declared release scope or is accepted by the release authority.

A nonblocking entry links the supporting decision or release criterion.

### Conditional

Impact depends on a named condition.

The entry defines:

- the condition;
- how it is evaluated;
- required evidence;
- behavior when the condition is true;
- behavior when the condition is false.

`RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md` remains the authority for the release decision.

---

## 14. Release exceptions

A release exception is allowed only when:

- the affected criterion is identified;
- the limitation is explicit;
- user and consumer impact is known;
- evidence is retained;
- a decision owner accepts the exception;
- the release criteria define its scope;
- the exception does not conceal a security or integrity failure.

An exception must not:

- convert `ERROR` into `OK`;
- suppress raw evidence;
- accept stale artifacts;
- auto-update gold;
- hide missing functions;
- bypass a required release stage silently;
- make GUI state authoritative for the project.

A permanent accepted limitation belongs in project scope, specifications, decisions and release criteria. It must not remain indefinitely as an active issue entry.

---

## 15. Dependency blockers

A dependency blocker names the actual prerequisite.

Avoid:

```text
Blocked by other work.
```

Use:

```text
Blocked by PROJ-ISSUE-002 because <ENTRYPOINT> requires the missing provider contract.
```

Record:

- blocking object or issue;
- blocked object;
- owners;
- direct evidence;
- downstream impact;
- objective unblock condition.

When a blocker resolves, rerun affected validation before removing dependent entries.

---

## 16. Required gold and scenario issues

### Missing required gold

Record:

- scenario ID;
- expected gold path;
- normalization identity;
- actual-output availability;
- review owner;
- release impact;
- creation and approval condition.

Normal validation never creates or approves gold automatically.

### Disabled or unavailable required scenario

Record:

- scenario ID and path;
- reason execution is unavailable;
- requirement coverage lost;
- alternative evidence, if any;
- release impact;
- restoration or replacement condition.

A required scenario cannot be counted as passing when it did not execute.

### Normalization uncertainty

Record:

- profile and version;
- unstable source of output;
- potentially lossy rules;
- affected golds;
- evidence required to approve the comparison contract.

---

## 17. Artifact issues

Artifact entries may cover:

- missing current `.gfo`;
- unresolved required `.pgf` identity;
- stale artifact risk;
- missing manifest role;
- unavailable source fingerprint;
- failed integrity verification.

A release-required artifact issue is blocking unless the release criteria explicitly establish an acceptable alternative.

A pre-existing artifact never substitutes for current-run provenance without an approved cache contract.

---

## 18. Tool compatibility issues

A required tool-compatibility issue records:

```text
tool and version
platform
required capability
compile evidence
scenario evidence
diagnostic parsing impact
normalization impact
PGF impact
release impact
resolution evidence
```

A successful version probe alone is insufficient evidence of compatibility.

Executable tools remain governed by the static allowlist and external-tool contract.

---

## 19. Security issues

Security issues may include:

- unreviewed GF shell escape;
- path traversal;
- unsafe symlink handling;
- unbounded generation;
- secret exposure;
- unsafe cleanup;
- untrusted executable provenance.

Security issues are blocking unless a formal security review and release decision explicitly establish otherwise.

This register must not contain secret values.

---

## 20. Relationship to owner documents

### `KNOWN_ISSUES.md`

Contains analysis, symptoms, scope, workarounds and technical detail.

This register links only the active issue's validation and release impact.

### `DECISION_LOG.md`

Contains durable decisions and accepted limitations.

This register links a decision when it authorizes an exception or resolves ambiguity.

### `INTERFILE_CONTRACT_LOCK.md`

Contains provider, consumer, invariant and forbidden-behavior contracts.

A contract conflict entry identifies the exact inconsistent contracts. It does not redefine them locally.

### `VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md`

Defines required validation behavior.

Every blocking entry identifies the affected validation requirement.

### `TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md`

Maps requirements to evidence.

Every release-significant entry links the affected coverage row.

### `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md`

Defines release gates and accepted exceptions.

The register does not compute release readiness independently.

---

## 21. Resolution workflow

When an issue is resolved:

```text
[ ] Verify the objective resolution condition
[ ] Rerun affected validation
[ ] Verify required raw and structured evidence
[ ] Update the owning known issue
[ ] Update contracts when behavior changed
[ ] Update validation and coverage documents when evidence changed
[ ] Update release criteria when an exception changed
[ ] Update decisions when a durable choice changed
[ ] Remove the entry from the active register
[ ] Preserve rationale in the owning record and version history
```

There is no promotion to a maturity state.

The active register contains unresolved issues only.

---

## 22. Review policy

Review the register:

- before a release or release candidate;
- after entrypoint or required-scenario changes;
- after GF-version policy changes;
- after normalization or gold-contract changes;
- after project migration;
- after a security finding;
- when a linked issue, decision or contract changes.

Release review verifies:

```text
[ ] Every active entry has an owner
[ ] Every active entry has current evidence
[ ] Every active entry has validation impact
[ ] Every active entry has release impact
[ ] Every conditional impact has an evaluable condition
[ ] Every blocking entry appears in release criteria
[ ] No required gold or artifact issue is hidden
[ ] No unresolved template placeholder remains
[ ] Linked issues, decisions and contracts exist
[ ] Resolved entries have been removed
[ ] No active-language fact appears in the reusable template
```

---

## 23. Automated checks

Project checks may verify this document when the canonical CLI contract provides such a command.

Checks may include:

1. entry IDs are unique;
2. every entry has an owner;
3. categories are recognized;
4. release impact is present;
5. conditional impact defines a condition;
6. affected project paths or identifiers exist where required;
7. linked requirements and contracts exist;
8. linked issues and decisions exist;
9. linked scenarios and golds exist when referenced;
10. active project metadata contains no template placeholders;
11. the reusable template contains no active-language facts.

This document does not invent a command name. Command availability and syntax belong to `docs/usage/CLI_REFERENCE.md`.

---

## 24. Template example

The following example must be removed or replaced in an active project.

```markdown
## PROJ-ISSUE-001 — Required scenario has no reviewed gold

**Category:** evidence gap  
**Owner:** <OWNER>  
**Last reviewed:** <YYYY-MM-DD>  
**Release impact:** blocking

### Problem

Scenario `<SCENARIO_ID>` produces normalized output, but no reviewed gold exists for the declared normalization identity.

### Affected objects

- `<SCENARIO_ID>`;
- `<GOLD_FILE>`;
- `<ENTRYPOINT>`.

### Evidence

- Raw output: `<run-relative path>`;
- Normalized output: `<run-relative path>`;
- Coverage row: `<reference>`.

### Validation impact

The required exact comparison cannot be evaluated.

### Release impact

The release criterion requiring this scenario and gold comparison cannot pass.

### Dependencies

- Blocking dependency: review of normalized output;
- Affected consumers: release gate and report readers.

### Resolution condition

The normalized output is reviewed, the gold is created through the explicit gold-update workflow, and the required scenario comparison passes.

### Related records

- Known issue: `<ISSUE_ID>`;
- Decision: `not applicable`;
- Contract: `<CONTRACT_ID>`;
- Release criterion: `<reference>`.
```

---

## 25. Template preservation

The reusable template must contain:

```text
[ ] no active-language name
[ ] no active-language code
[ ] no real GF module suffix
[ ] no real source root
[ ] no real project module
[ ] no active scenario ID
[ ] no active gold filename
[ ] no active issue or decision presented as project fact
[ ] clearly labeled examples
[ ] intentional placeholders only
[ ] generic paths
```

---

## 26. Related documents

```text
templates/project/README.md
templates/project/project.toml
templates/project/docs/00_PROJECT_START_HERE__TEMPLATES_PROJECT_DOCS.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md
templates/project/docs/TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md
templates/project/docs/KNOWN_ISSUES.md
templates/project/docs/DECISION_LOG.md
templates/project/docs/RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md
templates/project/docs/RESEARCH_EVIDENCE.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/projects/PROJECT_MODEL.md
docs/projects/CREATING_A_PROJECT.md
docs/projects/PROJECT_COMPLETION_CHECKLIST.md
docs/validation/RELEASE_GATES.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/architecture/ARTIFACT_MODEL.md
docs/release/VERSIONING_POLICY.md
docs/reference/TERMINOLOGY_REFERENCE.md
```

---

## 27. Enforcement

This register contains only concrete unresolved project issues, release blockers and approved exceptions.

Therefore:

> Do not document implementation maturity here. Record the unresolved condition, its evidence, its validation and release impact, its owner and the objective condition that removes it from the active register.
