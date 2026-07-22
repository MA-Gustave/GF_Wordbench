# GF Wordbench — Architecture Decision Records

**Document ID:** `GF-WB-ADR-INDEX`  
**Status:** Normative process and registry  
**Applies to:** `docs/decisions/`  
**Owner:** GF Wordbench maintainers  
**Initial registry version:** `1.0`  
**Last structural review:** 2026-07-22  

---

## 1. Purpose

This directory contains the Architecture Decision Records (ADRs) for GF Wordbench.

An ADR records a durable architectural choice that:

- affects more than one component;
- establishes or changes a public or interfile contract;
- constrains future implementation choices;
- changes ownership, execution flow, persisted meaning, or external-tool behavior;
- would otherwise be easy to reverse accidentally;
- needs a reviewable rationale and migration history.

The ADR system exists to preserve the reasoning behind the architecture.

Contract locks state what is currently required.

ADRs explain why an important requirement was chosen and which alternatives were rejected.

---

## 2. Core rule

> Record durable architectural choices before implementation drift turns them into undocumented facts.

An ADR is required when a decision changes a stable boundary.

An ADR is not required for every code edit.

---

## 3. Directory role

Canonical directory:

```text
docs/decisions/
```

Canonical contents:

```text
docs/decisions/
├── README.md
├── ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
├── ADR-0002-GF-AS-EXECUTION-ENGINE.md
├── ADR-0003-SEPARATE-SCAN-AND-COMPILE.md
├── ADR-0004-NATIVE-GFS-SCENARIOS.md
├── ADR-0005-FILE-AND-SCENARIO-RESULTS.md
├── ADR-0006-AI-READY-REPORT.md
└── ADR-0007-GOLDEN-OUTPUT-TESTING.md
```

Future ADRs continue with the next unused number.

Numbers are never reused.

---

## 4. Scope boundary

This directory owns framework-level architectural decisions.

It does not replace:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/DECISION_LOG.md
CHANGELOG.md
```

Each document has a distinct role.

| Document | Purpose |
|---|---|
| Framework ADR | Why a durable framework architecture choice was made |
| Framework interfile lock | Current Python-to-Python public contracts |
| External-tool lock | Current contracts with GF and other executables |
| Persisted-schema lock | Current persistent formats and migrations |
| Project interfile lock | Current GF-project provider/consumer contracts |
| Project decision log | Language-project-specific decisions |
| Changelog | What changed in each release |

---

## 5. Framework ADR versus project decision

Use a framework ADR when the decision affects:

- the reusable Python engine;
- the public CLI or GUI behavior;
- the shared execution model;
- shared result models;
- run artifact ownership;
- external-tool integration;
- persisted schemas;
- project-template architecture;
- all active or future language projects.

Use `project/docs/DECISION_LOG.md` when the decision affects only:

- the active language;
- one morphology design;
- one syntax strategy;
- one language-specific helper;
- one constructor interpretation;
- one lexicon policy;
- one project-specific scenario;
- one language-specific release exception.

A project decision also needs a framework ADR when it changes a reusable framework or template rule.

---

## 6. ADRs are immutable history

An accepted ADR is historical evidence.

Do not rewrite it to make an old decision appear as though it had always reflected the current architecture.

Allowed edits after acceptance:

- typographical corrections;
- broken-link corrections;
- metadata corrections that do not change meaning;
- explicit clarification notes;
- status updates;
- links to superseding ADRs.

A changed architectural decision requires a new ADR.

The old ADR remains in the repository with status:

```text
Superseded
```

and a link to the replacement.

---

## 7. ADR identifier

Canonical format:

```text
ADR-NNNN-UPPERCASE-KEBAB-TITLE.md
```

Examples:

```text
ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
ADR-0008-EXPLICIT-RUN-FINALIZATION.md
ADR-0012-PARALLEL-FILE-COMPILATION.md
```

Rules:

- four-digit number;
- number allocated sequentially;
- uppercase ASCII title;
- words separated by `-`;
- `.md` extension;
- stable filename after creation;
- no number reuse;
- no renaming solely to improve wording after acceptance.

---

## 8. ADR document ID

Inside the file:

```text
GF-WB-ADR-NNNN
```

Example:

```text
GF-WB-ADR-0004
```

The document ID remains stable even if the ADR status changes.

---

## 9. ADR statuses

Canonical statuses:

```text
Proposed
Accepted
Rejected
Deprecated
Superseded
```

### 9.1 Proposed

The decision is under review.

Implementation may be prototyped, but stable contracts must not depend on the proposal as final architecture.

### 9.2 Accepted

The decision is approved and governs implementation.

Related contracts, documentation, and tests must agree with it.

### 9.3 Rejected

The proposal was reviewed and not adopted.

The ADR remains as evidence that the alternative was considered.

### 9.4 Deprecated

The decision remains historically relevant but should not guide new design.

A replacement may be underway but not fully accepted.

### 9.5 Superseded

A later accepted ADR replaces the decision.

The superseded ADR must link to the new ADR.

The new ADR must list the superseded ADR.

---

## 10. Status transition rules

Allowed transitions:

```text
Proposed -> Accepted
Proposed -> Rejected
Accepted -> Deprecated
Accepted -> Superseded
Deprecated -> Superseded
```

Normally prohibited:

```text
Rejected -> Accepted
Superseded -> Accepted
```

When reconsidering a rejected or superseded decision, create a new ADR.

---

## 11. Decision date

Every ADR includes:

```text
Decision date: YYYY-MM-DD
```

For a proposed ADR, this may be:

```text
Decision date: Pending
```

The accepted date is the date the decision became authoritative.

Do not use file-modification time as the decision date.

---

## 12. Decision owner

Every ADR identifies one accountable owner.

Examples:

```text
GF Wordbench maintainers
Release owner
Architecture owner
Active project owner
```

The owner coordinates review.

The owner does not approve the ADR alone when other contract owners are affected.

---

## 13. Reviewers

Reviewers should represent affected ownership domains.

Possible reviewers:

```text
configuration owner
model owner
audit orchestration owner
process integration owner
reporting owner
schema owner
CLI owner
GUI owner
active project owner
release owner
security reviewer
```

Not every ADR needs every reviewer.

The ADR must list the domains actually affected.

---

## 14. When an ADR is required

Create an ADR before or during implementation when changing any of these:

### 14.1 Architecture ownership

- moving responsibility between modules;
- introducing a new major component;
- removing an architectural layer;
- changing the authoritative orchestration entry point;
- changing which component owns an artifact.

### 14.2 Execution model

- changing validation-stage ordering;
- adding parallel execution;
- changing cancellation architecture;
- changing run-finalization semantics;
- adding network execution;
- adding plugin execution;
- changing sandbox assumptions.

### 14.3 External-tool strategy

- replacing GF as the execution authority;
- adding a required external executable;
- changing from direct process launch to shell execution;
- changing GF scenario execution strategy;
- adding a PGF runtime dependency;
- changing capability-detection strategy.

### 14.4 Data and schemas

- introducing a new persistent artifact family;
- changing canonical identity;
- changing path-base semantics;
- replacing a schema family;
- changing migration architecture;
- changing raw-evidence ownership.

### 14.5 Public interface

- changing validation modes;
- changing CLI command structure;
- changing exit-code meaning;
- changing the public Python entry point;
- changing the shared result-model architecture;
- changing the project layout required by templates.

### 14.6 Validation philosophy

- replacing golden output testing;
- merging scan and compilation truth;
- changing direct/downstream causal classification principles;
- changing release-gate philosophy;
- changing how incomplete scenarios are detected.

### 14.7 Security and trust

- allowing system commands in scenarios;
- introducing remote execution;
- loading third-party plugins;
- changing project trust assumptions;
- changing source or gold mutation rules.

---

## 15. When an ADR is not required

An ADR is normally unnecessary for:

- a local bug fix;
- a scanner pattern correction;
- documentation wording;
- an optional report column;
- a test fixture addition;
- a private helper refactor;
- a compatible optional model field already permitted by architecture;
- implementation of an already accepted ADR;
- a project-specific linguistic choice;
- a routine dependency patch;
- a code-style change;
- a performance optimization that preserves ordering, evidence, and contracts.

These changes may still require:

- contract updates;
- schema updates;
- changelog entries;
- project decision-log entries;
- tests.

---

## 16. ADR content requirements

Every ADR must contain:

```text
Title
Document ID
Status
Decision date
Owners
Affected domains
Context
Decision
Decision drivers
Consequences
Alternatives considered
Rejected alternatives
Compatibility impact
Migration impact
Security impact
Validation and evidence
Related contracts
Related documentation
Supersedes
Superseded by
Implementation status
```

A section may state:

```text
None.
```

when genuinely not applicable.

Do not omit compatibility or security analysis merely because the expected impact is small.

---

## 17. Canonical ADR template

```markdown
# ADR-NNNN — Decision title

**Document ID:** `GF-WB-ADR-NNNN`  
**Status:** Proposed | Accepted | Rejected | Deprecated | Superseded  
**Decision date:** YYYY-MM-DD | Pending  
**Owners:** GF Wordbench maintainers  
**Affected domains:** architecture, configuration, execution, schemas, reports, CLI, GUI, GF integration, project template, security  
**Supersedes:** None | `ADR-NNNN`  
**Superseded by:** None | `ADR-NNNN`  

---

## 1. Context

Describe the architectural problem.

State:

- current behavior;
- constraints;
- affected consumers;
- why a durable decision is required;
- what would drift without a decision.

## 2. Decision drivers

- driver;
- driver;
- driver.

## 3. Decision

State the selected architecture clearly.

Use direct normative language.

## 4. Detailed rules

Define the stable boundaries created by the decision.

## 5. Consequences

### 5.1 Positive consequences

- benefit;
- benefit.

### 5.2 Negative consequences

- cost;
- limitation.

### 5.3 Neutral consequences

- tradeoff;
- operational effect.

## 6. Alternatives considered

### 6.1 Alternative A

Description.

**Why not selected**

Reason.

### 6.2 Alternative B

Description.

**Why not selected**

Reason.

## 7. Compatibility impact

Describe:

- public API;
- CLI;
- schemas;
- projects;
- historical runs;
- reports;
- external tools.

## 8. Migration impact

Describe required migrations or state `None`.

## 9. Security impact

Describe trust-boundary and safety effects.

## 10. Validation and evidence

List:

- tests;
- scenarios;
- gold files;
- integration checks;
- release gates;
- manual review where automation is impossible.

## 11. Related contracts

- contract ID and file;
- contract ID and file.

## 12. Related documentation

- path;
- path.

## 13. Implementation status

```text
[ ] models updated
[ ] configuration updated
[ ] orchestration updated
[ ] tools updated
[ ] reports updated
[ ] schemas updated
[ ] migrations updated
[ ] tests updated
[ ] documentation updated
[ ] release checks passed
```

## 14. Decision review notes

Record important review conclusions without rewriting the original context.
```

---

## 18. Writing quality

An ADR should be:

- concise enough to review;
- complete enough to prevent reinterpretation;
- explicit about tradeoffs;
- based on actual constraints;
- independent of transient implementation details where possible;
- precise about stable boundaries;
- honest about disadvantages;
- clear about what remains flexible.

Avoid:

- marketing language;
- vague claims such as “more scalable” without context;
- undocumented certainty;
- implementation dumps;
- full contract duplication;
- source-code listings longer than necessary;
- retrospective rewriting.

---

## 19. Decision versus implementation detail

An ADR should state:

```text
what must remain true
```

It should avoid freezing:

```text
one private helper name
one local algorithm
one temporary library
one GUI layout
one incidental file order
```

unless that detail is itself the decision.

Example:

Good:

```text
All supported front ends invoke one shared audit orchestration entry point.
```

Too implementation-specific:

```text
ButtonValidate_clicked must call helper_7 on line 241.
```

---

## 20. Decision versus contract lock

ADRs and contract locks must agree, but they are not duplicates.

Example:

ADR:

```text
GF remains the execution engine.
```

External-tool lock:

```text
Exact executable, arguments, working directory, stdin, stdout, stderr,
timeouts, artifacts, and success criteria for each GF operation.
```

The ADR explains the architectural choice.

The lock defines the current enforceable boundary.

---

## 21. Decision versus implementation guide

An ADR does not replace detailed documentation.

Example:

ADR:

```text
Use native .gfs scenarios.
```

Detailed documents:

```text
docs/gf/GF_SCRIPT_EXECUTION.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/WRITING_GFS_SCENARIOS.md
```

The ADR should link to those documents.

It should not reproduce their complete operational reference.

---

## 22. Decision versus changelog

The changelog records:

```text
what changed in a release
```

The ADR records:

```text
why the durable architecture changed
```

One architectural change may create:

- one ADR;
- multiple contract updates;
- multiple code changes;
- one or more schema migrations;
- one changelog entry.

---

## 23. Decision versus status ledger

`project/docs/STATUS_LEDGER.md` records temporary project implementation states such as:

```text
temporary
fallback
warning
blocked
```

An ADR is required only when the temporary state leads to a durable architectural decision.

Do not create an ADR for every unfinished project function.

---

## 24. Review process

Canonical process:

```text
1. identify architectural decision
2. reserve next ADR number
3. create Proposed ADR
4. identify affected owners and contracts
5. review alternatives and impacts
6. revise proposal
7. accept or reject
8. update status and decision date
9. implement
10. update contract locks and schemas
11. add tests and evidence
12. complete implementation checklist
13. include release note
```

---

## 25. Number allocation

Use the next unused number.

Current highest reserved number:

```text
0007
```

Next available:

```text
0008
```

A number may be reserved by creating a minimal proposed ADR.

Do not reserve a block of speculative numbers.

If a proposed ADR is abandoned before review, keep the file and mark it:

```text
Rejected
```

or retain a short tombstone explaining why the number was not used.

---

## 26. File creation rule

A new ADR begins from the canonical template.

Do not copy an old ADR and leave stale metadata, alternatives, or links.

The first commit may use:

```text
Status: Proposed
Decision date: Pending
```

---

## 27. Acceptance rule

An ADR becomes `Accepted` only when:

- the decision is explicit;
- affected owners were reviewed;
- alternatives were considered;
- compatibility impact is understood;
- migration requirements are known;
- security impact is reviewed;
- required contract updates are identified;
- validation evidence is defined;
- no unresolved contradiction remains with an accepted ADR.

Implementation may follow acceptance or be completed in the same change.

The `Implementation status` section shows whether the accepted decision is fully realized.

---

## 28. Accepted but incomplete decision

An ADR may be accepted before all implementation is complete.

Required behavior:

- implementation checklist remains visible;
- incomplete items are tracked;
- contract locks must not claim unimplemented behavior as active unless the contract status supports it;
- release gates must not claim completion;
- final stable release requires all mandatory accepted ADR items complete.

Do not change the ADR status back to `Proposed` merely because implementation remains.

---

## 29. Rejection rule

A rejected ADR must state:

- why it was rejected;
- whether the problem still exists;
- whether another ADR is expected;
- whether prototype code must be removed;
- which alternative remains current.

Rejected ADRs do not govern implementation.

---

## 30. Supersession rule

A superseding ADR must explain:

- what changed;
- why the old decision is no longer sufficient;
- compatibility impact;
- migration;
- retained invariants;
- removed invariants.

Update both files:

Old ADR:

```text
Status: Superseded
Superseded by: ADR-NNNN
```

New ADR:

```text
Supersedes: ADR-OOOO
```

Do not delete the old file.

---

## 31. Contradiction rule

When two accepted ADRs appear to conflict:

1. stop the affected architectural change;
2. identify the later decision and intended precedence;
3. create a superseding ADR if meaning changed;
4. update statuses;
5. update contract locks;
6. add tests;
7. document migration.

Do not resolve the conflict only in code.

---

## 32. Versioning

Individual ADRs do not need a numeric document version.

Their history is represented by:

- source control;
- status;
- decision date;
- supersession links;
- review notes.

This index may have an internal registry version because its process rules are normative.

Changing the ADR process incompatibly requires review of this file.

---

## 33. Release integration

A release containing an accepted architectural change must include:

```text
ADR accepted
implementation checklist complete for release scope
affected contracts updated
affected schemas versioned
migrations implemented
tests passing
documentation updated
changelog entry
release note
```

A release must not claim an ADR implemented when mandatory checklist items remain incomplete.

---

## 34. Security review

An ADR requires explicit security review when it changes:

- shell use;
- executable discovery;
- scenario trust;
- remote communication;
- authentication;
- plugin loading;
- file deletion;
- source or gold mutation;
- path containment;
- deserialization;
- manifest integrity;
- secret handling;
- external dependencies;
- privilege assumptions.

The review should link to:

```text
SECURITY.md
```

and any affected security tests.

---

## 35. Compatibility review

An ADR requires explicit backward-compatibility review when it changes:

- CLI commands or options;
- exit codes;
- public Python APIs;
- model fields;
- persisted schemas;
- artifact names;
- report required headings;
- validation statuses;
- diagnostic classes;
- scenario IDs;
- normalization rules;
- project layout;
- supported GF or Python versions.

The review should link to:

```text
docs/development/BACKWARD_COMPATIBILITY.md
docs/release/VERSIONING_POLICY.md
```

---

## 36. Evidence requirements

An accepted ADR must identify how the architecture is proven.

Evidence may include:

```text
unit tests
contract tests
integration tests
real-GF tests
.gfs scenarios
gold comparisons
schema fixtures
migration fixtures
CLI tests
GUI equivalence tests
manifest verification
release gates
security tests
manual review when automation is impossible
```

“Covered by tests” without paths or named test domains is insufficient.

---

## 37. ADR registry

The canonical registry is below.

| ADR | Title | Status | Primary decision |
|---|---|---|---|
| [ADR-0001](ADR-0001-SINGLE-ACTIVE-LANGUAGE.md) | Single Active Language | Accepted | One replaceable active language project is loaded at a time |
| [ADR-0002](ADR-0002-GF-AS-EXECUTION-ENGINE.md) | GF as Execution Engine | Accepted | GF remains authoritative for grammar execution |
| [ADR-0003](ADR-0003-SEPARATE-SCAN-AND-COMPILE.md) | Separate Scan and Compile | Accepted | Heuristic scanning and GF compilation remain distinct evidence stages |
| [ADR-0004](ADR-0004-NATIVE-GFS-SCENARIOS.md) | Native GFS Scenarios | Accepted | Runtime scenarios use reviewed native `.gfs` scripts executed by GF |
| [ADR-0005](ADR-0005-FILE-AND-SCENARIO-RESULTS.md) | File and Scenario Results | Accepted | File validation and scenario validation use separate structured result types |
| [ADR-0006](ADR-0006-AI-READY-REPORT.md) | AI-Ready Report | Accepted | AI handoff is a bounded derived report, not a machine source of truth |
| [ADR-0007](ADR-0007-GOLDEN-OUTPUT-TESTING.md) | Golden Output Testing | Accepted | Stable normalized scenario outputs are compared with reviewed gold files |

The table must remain synchronized with the files in this directory.

---

## 38. ADR-0001 summary

```text
ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
```

Decision:

```text
GF Wordbench operates on one active language project at a time.
```

Core consequences:

- stable reusable framework;
- replaceable `project/`;
- language-specific rules stay outside framework code;
- application state does not own language identity;
- project templates can create new active projects;
- cross-language batch management is outside the initial architecture.

Primary related documents:

```text
docs/projects/PROJECT_MODEL.md
docs/configuration/PROJECT_TOML_REFERENCE.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

---

## 39. ADR-0002 summary

```text
ADR-0002-GF-AS-EXECUTION-ENGINE.md
```

Decision:

```text
GF remains authoritative for parsing, type checking, compilation,
PGF construction, parsing, linearization, generation, morphology,
introspection, and GF shell semantics.
```

GF Wordbench owns:

```text
orchestration
command construction
process control
evidence capture
normalization
classification
comparison
reporting
```

Primary related documents:

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/architecture/EXECUTION_FLOW.md
```

---

## 40. ADR-0003 summary

```text
ADR-0003-SEPARATE-SCAN-AND-COMPILE.md
```

Decision:

```text
Static source scans and GF compilation remain separate stages and separate evidence.
```

Consequences:

- scan findings never masquerade as GF truth;
- compilation does not erase scanner evidence;
- successful files may still have scan findings;
- scanner rules can evolve without redefining GF status;
- reports show scan notes separately.

Primary related documents:

```text
docs/validation/STATIC_SCANNING.md
docs/validation/COMPILATION_VALIDATION.md
docs/diagnostics/ERROR_CLASSIFICATION.md
```

---

## 41. ADR-0004 summary

```text
ADR-0004-NATIVE-GFS-SCENARIOS.md
```

Decision:

```text
GF Wordbench executes reviewed native GF shell scripts through stdin.
```

Consequences:

- no competing Python GF shell;
- `.gfs` scripts are executable project assets;
- stable markers prove completion;
- raw streams are captured before normalization;
- system-command features are prohibited by default;
- scenarios are registered by ID.

Primary related documents:

```text
docs/gf/GF_SCRIPT_EXECUTION.md
docs/scenarios/SCENARIO_FORMAT.md
SECURITY.md
```

---

## 42. ADR-0005 summary

```text
ADR-0005-FILE-AND-SCENARIO-RESULTS.md
```

Decision:

```text
FileResult and ScenarioResult remain separate structured models.
```

Consequences:

- file compilation and scenario assertions keep distinct semantics;
- totals remain coherent;
- status vocabulary is shared;
- scenario markers, gold state, and artifacts are not forced into file fields;
- future generalized subjects can be used for regression comparison.

Primary related documents:

```text
docs/architecture/DATA_MODEL.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/validation/SCENARIO_VALIDATION.md
```

---

## 43. ADR-0006 summary

```text
ADR-0006-AI-READY-REPORT.md
```

Decision:

```text
AI_READY.md is a bounded derived diagnostic packet.
```

Consequences:

- `summary.json` remains machine-authoritative;
- raw evidence remains separate;
- AI content is derived from structured results;
- secrets and full environment dumps are excluded;
- direct failures and important evidence are prioritized;
- report generation never reruns validation.

Primary related documents:

```text
docs/reports/AI_READY_REFERENCE.md
docs/reports/REPORTING_OVERVIEW.md
SECURITY.md
```

---

## 44. ADR-0007 summary

```text
ADR-0007-GOLDEN-OUTPUT-TESTING.md
```

Decision:

```text
Stable normalized scenario output is compared with reviewed `.gold` files.
```

Consequences:

- raw output is preserved;
- normalization is versioned;
- normal validation is read-only;
- gold updates require explicit action;
- nondeterministic output needs bounded semantic assertions;
- changes to gold require review.

Primary related documents:

```text
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/UPDATING_GOLD_FILES.md
```

---

## 45. Registry update rule

When adding an ADR:

```text
[ ] allocate next number
[ ] create file
[ ] add registry row
[ ] add summary section only when useful
[ ] link affected contracts
[ ] link affected documentation
[ ] update documentation map
[ ] update changelog when release-visible
```

A registry row must not point to a nonexistent final-release file.

During a development branch, a proposed ADR file must exist before its registry link is added.

---

## 46. Required ADR metadata

Canonical header:

```markdown
# ADR-NNNN — Title

**Document ID:** `GF-WB-ADR-NNNN`  
**Status:** Accepted  
**Decision date:** 2026-07-22  
**Owners:** GF Wordbench maintainers  
**Affected domains:** execution, models, reports  
**Supersedes:** None  
**Superseded by:** None  
```

Metadata field order remains stable for readability.

The fields are human-facing.

No code should parse ADR metadata as a machine schema unless a future explicit registry format is introduced.

---

## 47. Machine-readable ADR registry

The initial architecture does not require a JSON or TOML ADR registry.

The Markdown registry is sufficient because:

- ADRs guide human architecture review;
- no runtime behavior depends on them;
- contract locks and schemas carry machine-relevant identifiers;
- adding another persistent format would create unnecessary complexity.

A machine-readable registry may be added only when a real automated consumer exists.

---

## 48. Linking conventions

Use repository-relative Markdown links.

Example:

```markdown
[ADR-0004](ADR-0004-NATIVE-GFS-SCENARIOS.md)
```

Related files outside this directory may be shown as code paths when viewer portability is uncertain:

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
```

Do not use machine-specific absolute paths inside ADR documents.

---

## 49. Contract references

Reference stable contract IDs when available.

Examples:

```text
EXT-GF-005
EXT-GF-006
IFC-AUDIT-001
PIFC-SCENARIO-004
```

Also include the owning contract-lock path.

Do not copy the full contract entry into the ADR.

---

## 50. Schema references

When an ADR changes persisted data, identify:

```text
schema_id
current version
target version
migration owner
legacy support
```

Example:

```text
gf-wordbench.run-summary
1.0 -> 2.0
```

The ADR does not replace the schema lock or migration specification.

---

## 51. Implementation status

Implementation status is a checklist, not the ADR status.

Possible state:

```text
ADR status = Accepted
implementation checklist = incomplete
```

This means the direction is decided but not fully delivered.

For final stable release, all mandatory checklist items must be complete.

---

## 52. Review notes

Review notes may record:

- final tradeoff;
- important dissent;
- constraint discovered after proposal;
- reason one alternative was rejected;
- reason implementation was staged.

Review notes must not become an unstructured replacement for the decision.

---

## 53. ADR tests

The repository should include lightweight documentation tests.

Recommended:

```text
tests/docs/test_adr_registry.py
tests/docs/test_adr_filenames.py
tests/docs/test_adr_metadata.py
tests/docs/test_adr_links.py
tests/docs/test_adr_statuses.py
tests/docs/test_adr_supersession.py
```

Checks:

- filename pattern;
- unique number;
- unique document ID;
- canonical status;
- required metadata;
- registry/file agreement;
- valid relative links;
- reciprocal supersession links;
- no number reuse;
- no duplicate accepted decisions with contradictory meaning.

These tests validate document structure.

They do not decide architecture.

---

## 54. Optional ADR checker

A future command may be:

```text
gf-wordbench project docs check
```

or a release-only documentation checker.

A dedicated public:

```text
gf-wordbench adr check
```

is unnecessary unless ADR checking becomes a stable user workflow.

Avoid adding a command only for symmetry.

---

## 55. Change control for this README

Changing the ADR process requires review when it affects:

- status meanings;
- required metadata;
- numbering rules;
- acceptance rules;
- supersession rules;
- framework/project decision boundary;
- release requirements.

Compatible improvements:

- clarify wording;
- add optional guidance;
- add optional tests;
- add a new accepted ADR to the registry.

Breaking process changes should update:

```text
Initial registry version
```

to the next appropriate value.

---

## 56. Anti-drift indicators

Probable decision-record drift exists when:

- a major architecture choice exists only in code;
- contract locks change with no rationale for a fundamental choice;
- two accepted ADRs contradict each other;
- an accepted ADR points to unimplemented behavior presented as complete;
- an old ADR is rewritten instead of superseded;
- an ADR number is reused;
- an ADR filename changes after acceptance;
- project-specific linguistic details fill the framework ADR directory;
- framework decisions are buried only in the project decision log;
- status values vary between files;
- a superseded ADR lacks a replacement link;
- a new ADR omits compatibility or security impact;
- a contract-breaking change has no ADR when the underlying architecture changed;
- the registry and directory disagree;
- an ADR duplicates an entire contract lock;
- a proposed ADR is treated as authoritative;
- a rejected ADR remains implemented as though accepted;
- changelog prose is used as the only architecture rationale;
- a runtime component parses ADR Markdown to decide behavior.

Any indicator requires documentation and architecture review.

---

## 57. Review checklist for a proposed ADR

```text
[ ] Problem is architectural, not merely local
[ ] Next unused number allocated
[ ] Canonical filename used
[ ] Required metadata complete
[ ] Context describes current state
[ ] Decision is explicit
[ ] Decision drivers are concrete
[ ] Alternatives are real
[ ] Negative consequences are stated
[ ] Affected owners reviewed
[ ] Compatibility impact reviewed
[ ] Migration impact reviewed
[ ] Security impact reviewed
[ ] Schema impact reviewed
[ ] External-tool impact reviewed
[ ] Project impact reviewed
[ ] Evidence is identified
[ ] Related contracts are linked
[ ] Related documents are linked
[ ] No accepted ADR conflict remains
[ ] Status and decision date are correct
```

---

## 58. Review checklist for implementation

```text
[ ] Shared models updated
[ ] Configuration updated
[ ] Execution flow updated
[ ] External command contracts updated
[ ] Artifact ownership updated
[ ] Schemas versioned
[ ] Migrations implemented
[ ] CLI updated
[ ] GUI updated
[ ] Reports updated
[ ] Project template updated
[ ] Active project updated
[ ] Contract locks updated
[ ] Security tests updated
[ ] Compatibility tests updated
[ ] Integration tests updated
[ ] Real-GF tests updated
[ ] Documentation updated
[ ] Changelog updated
[ ] Release notes updated
[ ] Release gates pass
```

Only applicable items are required.

Non-applicable items should be marked explicitly.

---

## 59. Minimal accepted ADR example

```markdown
# ADR-0008 — Explicit Run Finalization

**Document ID:** `GF-WB-ADR-0008`  
**Status:** Accepted  
**Decision date:** 2026-09-01  
**Owners:** GF Wordbench maintainers  
**Affected domains:** execution, artifacts, reports  
**Supersedes:** None  
**Superseded by:** None  

## 1. Context

A run directory can contain useful partial evidence before reports and the
manifest are complete. Consumers need to distinguish partial and finalized runs.

## 2. Decision drivers

- prevent incomplete baselines;
- preserve partial evidence;
- support reliable cleanup;
- make release verification deterministic.

## 3. Decision

A run becomes finalized only after required reports and manifest validation
complete. Partial runs remain readable but are not automatic regression baselines.

## 4. Consequences

### 4.1 Positive consequences

- reliable baseline discovery;
- explicit partial-run semantics.

### 4.2 Negative consequences

- finalization state must be persisted;
- migrations are required for historical runs.

## 5. Alternatives considered

### 5.1 Treat any directory with summary.json as complete

Rejected because summary creation may precede artifact finalization.

## 6. Compatibility impact

Historical runs require legacy eligibility rules.

## 7. Migration impact

Add optional finalization metadata, then make it required in the next schema major.

## 8. Security impact

Reduces risk of trusting partially written evidence.

## 9. Validation and evidence

- baseline discovery tests;
- manifest tests;
- partial-run tests.

## 10. Related contracts

- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/INTERFILE_CONTRACT_LOCK.md`
```

This example demonstrates scale.

It is not a reserved or accepted GF Wordbench decision unless the corresponding ADR file is created and reviewed.

---

## 60. Related documents

```text
docs/00_START_HERE.md
docs/DOCUMENTATION_MAP.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/EXECUTION_FLOW.md
docs/development/BACKWARD_COMPATIBILITY.md
docs/release/VERSIONING_POLICY.md
docs/release/RELEASE_PROCESS.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/DECISION_LOG.md
project/docs/STATUS_LEDGER.md
CHANGELOG.md
SECURITY.md
```

---

## 61. Final rule

An ADR records a durable choice, not merely a completed edit.

Therefore:

> Create an ADR when architecture, ownership, public behavior, persisted meaning, trust boundaries, or long-term validation strategy changes; keep accepted decisions immutable; supersede them explicitly; and update every affected contract, migration, test, and release artifact as one coordinated change.
