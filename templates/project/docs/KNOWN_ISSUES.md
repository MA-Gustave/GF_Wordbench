# Project Template — Known Issues

**Document ID:** `GF-WB-TEMPLATE-PROJECT-KNOWN-ISSUES`  
**Document role:** Normative project-template document  
**Decision status:** Accepted template contract  
**Implementation status:** Template available; active-project implementation depends on initialization  
**Verification status:** Requires placeholder, source, contract and validation checks after initialization  
**Template scope:** One future active GF project  
**Canonical active-project destination:** `project/docs/KNOWN_ISSUES.md`  
**Primary project source:** `project/project.toml`  
**Primary implementation-state source:** `project/docs/STATUS_LEDGER__PROJECT_DOCS.md`  
**Primary contract source:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Primary coverage source:** `project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md`  
**Primary release source:** `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md`  
**Template owner:** GF Wordbench project-template maintainers  
**Project owner after initialization:** Active-project maintainers  
**Last structural review:** `<YYYY-MM-DD>`

---

## 1. Purpose

This document is the canonical template for recording known defects, limitations, unresolved risks, compatibility restrictions, accepted behavioral differences, validation weaknesses, and release-relevant problems in an active GF project.

Its purpose is to ensure that every known issue is:

- explicit;
- uniquely identifiable;
- scoped;
- reproducible where possible;
- connected to the affected provider and consumers;
- connected to relevant project contracts;
- connected to validation evidence;
- classified by user and release impact;
- assigned to an owner;
- given a workaround where one exists;
- given an exit condition;
- reviewed before release;
- retained after resolution as historical evidence.

The governing rule is:

> A known issue is not acceptable merely because it is documented. Documentation makes the issue visible; project contracts and release criteria determine whether the issue may remain.

This file must not become:

- a substitute for `STATUS_LEDGER__TEMPLATES_PROJECT_DOCS.md`;
- a substitute for executable tests;
- a list of vague future ideas;
- an archive of every closed development task;
- a place to normalize release blockers into harmless notes;
- a place to hide undocumented fallbacks;
- a place to record framework bugs that do not affect the active project.

---

## 2. Template use

When initializing an active project:

1. copy this file to `project/docs/KNOWN_ISSUES.md`;
2. replace all required project placeholders;
3. delete template-only example issue rows;
4. add every known active issue;
5. link temporary implementation states to `STATUS_LEDGER__TEMPLATES_PROJECT_DOCS.md`;
6. link contract-impacting issues to `INTERFILE_CONTRACT_LOCK.md`;
7. link evidence gaps to `TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md`;
8. link release impact to `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md`;
9. record baseline-known issues before declaring the project migrated;
10. retain resolved entries in the resolution archive;
11. review the registry before every release.

The active project may have zero open known issues.

When no issue is open, retain the registry structure and record:

```text
Open known issues: 0
```

Do not remove the document.

---

## 3. Related project files

The completed active document must remain consistent with:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_OVERVIEW.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
project/docs/DECISION_LOG.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/docs/RESEARCH_EVIDENCE.md
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

Relevant framework references include:

```text
docs/architecture/ERROR_HANDLING_MODEL.md
docs/diagnostics/DIAGNOSTIC_CLASSIFICATION.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/SCENARIO_VALIDATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/projects/PROJECT_COMPLETION_CHECKLIST.md
docs/release/VERSIONING_POLICY.md
docs/release/MIGRATION_AND_DEPRECATION.md
docs/reference/STATUS_VALUES.md
docs/reference/FILE_NAMING_CONVENTIONS.md
```

When this document disagrees with the project contract lock about required behavior, the contract lock remains authoritative.

The disagreement is itself a release-relevant issue until resolved.

---

# 4. Known issue versus other records

Different project records have different owners.

| Record | Purpose | Example |
|---|---|---|
| `KNOWN_ISSUES.md` | Observable defect, limitation, risk, or compatibility restriction | A required parse family remains ambiguous |
| `STATUS_LEDGER__TEMPLATES_PROJECT_DOCS.md` | Implementation maturity and temporary state | A constructor uses a temporary fallback |
| `TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md` | Proof status and evidence gaps | Negative cases are not yet covered |
| `DECISION_LOG.md` | Deliberate architectural or linguistic decision | A non-default word order is accepted |
| `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md` | Gate interpretation | Issue class blocks release |
| Source comments | Local implementation context | Reason for a narrow workaround |
| Issue tracker | Work planning and discussion | Task assignment and conversation |
| Run results | Observed validation evidence | Scenario `parse` returned `FAIL` |
| Migration record | Old-to-new compatibility work | Scenario ID renamed |

A single project problem may require entries in several records.

Example:

```text
temporary fallback in a morphology provider
→ STATUS_LEDGER entry

user-visible incorrect form caused by the fallback
→ KNOWN_ISSUES entry

missing regression scenario
→ TEST_COVERAGE_MATRIX gap

planned provider redesign
→ DECISION_LOG entry when approved
```

These records must cross-reference rather than duplicate contradictory descriptions.

---

# 5. Normative terms

- **ISSUE**: known condition where actual, supported, documented, or desired behavior differs in a meaningful way.
- **DEFECT**: implementation behavior that violates an active contract or accepted specification.
- **LIMITATION**: documented boundary of implemented or supported behavior.
- **RISK**: condition that may cause future failure or uncertainty but has not necessarily produced one.
- **COMPATIBILITY ISSUE**: problem dependent on GF, RGL, platform, project version, consumer, or migration state.
- **VALIDATION ISSUE**: problem preventing reliable proof, such as nondeterminism or missing evidence.
- **DOCUMENTATION ISSUE**: mismatch or material omission in project documentation.
- **ARTIFACT ISSUE**: problem involving `.gfo`, `.pgf`, gold, report, manifest, or run evidence.
- **SECURITY ISSUE**: condition involving unsafe execution, path escape, secret exposure, or destructive behavior.
- **DATA-INTEGRITY ISSUE**: condition involving loss, corruption, stale evidence, or incorrect provenance.
- **LINGUISTIC ISSUE**: incorrect or unsupported morphology, syntax, parsing, linearization, lexicon, or grammar behavior.
- **ARCHITECTURAL ISSUE**: provider/consumer, dependency, ownership, or contract problem.
- **OPEN**: issue remains applicable.
- **CONFIRMED**: issue is reproduced and understood sufficiently to track.
- **TRIAGED**: scope, severity, ownership, and release impact are assigned.
- **IN_PROGRESS**: corrective work is active.
- **MONITORING**: fix or mitigation exists and awaits sufficient validation.
- **RESOLVED**: exit condition is satisfied.
- **CLOSED_AS_DESIGNED**: reported behavior matches intentional documented design.
- **DUPLICATE**: same root issue is tracked by another issue ID.
- **WONT_FIX**: issue remains but maintainers explicitly decline correction.
- **DEFERRED**: correction is postponed to a stated target.
- **BLOCKING**: issue prevents checkpoint, release, migration, or another declared milestone.
- **NON_BLOCKING**: issue may remain for a declared milestone after explicit review.
- **WORKAROUND**: safe documented method that reduces user impact without resolving the root cause.
- **MITIGATION**: change reducing likelihood or impact.
- **ROOT CAUSE**: underlying provider, contract, tool, or process condition.
- **TRIGGER**: action or input that exposes the issue.
- **AFFECTED SCOPE**: modules, functions, categories, scenarios, artifacts, consumers, or environments affected.
- **UNAFFECTED SCOPE**: similar areas explicitly proven not affected.
- **EXIT CONDITION**: objective evidence required to resolve the issue.
- **ACCEPTED ISSUE**: open issue explicitly reviewed and permitted for a specific release or scope.
- **WAIVER**: time-bounded approval for a permitted release exception.
- **REGRESSION**: behavior that previously passed and now fails.
- **HISTORICAL ISSUE**: resolved or retired issue retained for traceability.

---

# 6. Issue identifier convention

Every tracked issue must have one stable identifier.

Recommended format:

```text
KI-<DOMAIN>-<NUMBER>
```

Recommended domains:

```text
CONFIG
IDENTITY
MODULE
LINCAT
MORPH
SYNTAX
LEXICON
STRUCT
ENTRY
SCENARIO
GOLD
PGF
ARTIFACT
REPORT
DOC
COVERAGE
TOOLCHAIN
PLATFORM
MIGRATION
PERFORMANCE
SECURITY
DATA
RELEASE
```

Examples:

```text
KI-MORPH-001
KI-SYNTAX-004
KI-SCENARIO-002
KI-PGF-001
KI-TOOLCHAIN-003
```

Rules:

- IDs are uppercase ASCII;
- sequence numbers are zero-padded consistently;
- IDs are never reused;
- issue title may change while ID remains stable;
- merged issues retain redirects to the canonical ID;
- resolved issues retain IDs;
- IDs may be referenced by coverage rows, status entries, decisions, commits, scenarios, and release notes.

---

# 7. Issue lifecycle

Canonical lifecycle statuses:

```text
REPORTED
CONFIRMED
TRIAGED
IN_PROGRESS
MONITORING
RESOLVED
CLOSED_AS_DESIGNED
DUPLICATE
WONT_FIX
DEFERRED
RETIRED
```

## 7.1 `REPORTED`

Use when a credible issue is observed but not yet reproduced or classified.

Required minimum:

```text
issue ID
summary
report source
observed behavior
```

A release-relevant reported issue must be triaged before approval.

## 7.2 `CONFIRMED`

Use when the issue is reproducible or supported by strong evidence.

Required:

```text
reproduction
affected scope
evidence
```

## 7.3 `TRIAGED`

Use when:

```text
category assigned
severity assigned
release impact assigned
owner assigned
next action assigned
```

## 7.4 `IN_PROGRESS`

Use only while corrective or investigative work is active.

## 7.5 `MONITORING`

Use when a candidate correction or mitigation exists but exit evidence is incomplete.

## 7.6 `RESOLVED`

Use only when the issue's exit condition is satisfied and evidence is recorded.

## 7.7 `CLOSED_AS_DESIGNED`

Use when:

- behavior is intentional;
- documentation and contracts are corrected if needed;
- no defect remains;
- users are given the correct interpretation.

## 7.8 `DUPLICATE`

Reference the canonical issue ID.

Do not maintain independent severity or resolution state afterward.

## 7.9 `WONT_FIX`

Requires explicit rationale and release-impact review.

`WONT_FIX` does not imply non-blocking.

## 7.10 `DEFERRED`

Requires:

```text
reason
target milestone
owner
interim risk
release impact
```

## 7.11 `RETIRED`

Use when the affected feature or contract is retired and the issue is no longer applicable.

Retirement must reference the corresponding migration or contract change.

---

# 8. Issue category

Each issue has one primary category.

Canonical categories:

```text
LINGUISTIC
IMPLEMENTATION
ARCHITECTURE
CONTRACT
CONFIGURATION
VALIDATION
COVERAGE
SCENARIO
GOLD
ARTIFACT
TOOLCHAIN
PLATFORM
PERFORMANCE
DOCUMENTATION
MIGRATION
SECURITY
DATA_INTEGRITY
RELEASE_PROCESS
```

Secondary tags may refine classification.

Example tags:

```text
noun
verb
agreement
word-order
parse
linearize
generation
Windows
GF-version
RGL
nondeterminism
regression
fallback
blocked-contract
stale-artifact
```

Do not create a new primary category for every issue.

---

# 9. Severity

Canonical severity:

```text
CRITICAL
HIGH
MEDIUM
LOW
INFORMATIONAL
```

Severity describes impact, not urgency or implementation difficulty.

## 9.1 `CRITICAL`

Examples:

```text
unsafe source overwrite
secret exposure
false successful release
corrupt gold update
wrong project identity released
PGF cannot be loaded by required consumers
systemic data loss
```

Default release impact:

```text
BLOCKING
```

## 9.2 `HIGH`

Examples:

```text
required construction produces materially incorrect output
required entrypoint fails
required scenario cannot execute
public lincat contract is inconsistent
major parse regression
required PGF is incomplete
```

Default release impact:

```text
BLOCKING
```

## 9.3 `MEDIUM`

Examples:

```text
important optional construction incorrect
limited irregular morphology defect
known ambiguity exceeding preferred policy
non-critical platform incompatibility
manual workaround required
```

Release impact depends on declared scope.

## 9.4 `LOW`

Examples:

```text
minor formatting inconsistency
rare edge case outside release scope
non-gating diagnostic noise
minor documentation mismatch with no behavioral effect
```

## 9.5 `INFORMATIONAL`

Examples:

```text
accepted limitation
future compatibility concern
upstream behavior note
monitoring item
```

Informational issues must not be used to downgrade a serious defect.

---

# 10. Priority

Priority is separate from severity.

Canonical priority:

```text
P0
P1
P2
P3
P4
```

Suggested interpretation:

| Priority | Meaning |
|---|---|
| `P0` | Immediate stop-work or release incident |
| `P1` | Must resolve for current release/milestone |
| `P2` | Resolve soon; significant project impact |
| `P3` | Planned correction |
| `P4` | Backlog or monitoring |

Priority may change as release plans change.

Severity changes only when impact understanding changes.

---

# 11. Release impact

Canonical release-impact values:

```text
BLOCKS_RELEASE
BLOCKS_CHECKPOINT
BLOCKS_MIGRATION
BLOCKS_FEATURE
NON_BLOCKING_ACCEPTED
NON_BLOCKING_OUT_OF_SCOPE
OPTIONAL_ONLY
UNKNOWN_PENDING_TRIAGE
```

Rules:

- `UNKNOWN_PENDING_TRIAGE` prevents release approval when the issue may affect required behavior;
- `BLOCKS_FEATURE` requires the feature to be excluded from release claims;
- `NON_BLOCKING_ACCEPTED` requires explicit review;
- `NON_BLOCKING_OUT_OF_SCOPE` requires the scope boundary to be documented;
- severity alone does not determine release impact;
- release criteria remain authoritative.

---

# 12. Acceptance state

Issue acceptance values:

```text
NOT_REVIEWED
REJECTED_FOR_RELEASE
ACCEPTED_FOR_BASELINE
ACCEPTED_FOR_RELEASE
ACCEPTED_WITH_WAIVER
```

Meaning:

## 12.1 `NOT_REVIEWED`

No release decision has been made.

## 12.2 `REJECTED_FOR_RELEASE`

Issue blocks the candidate.

## 12.3 `ACCEPTED_FOR_BASELINE`

Issue may remain in a development or migration baseline.

This does not imply release acceptance.

## 12.4 `ACCEPTED_FOR_RELEASE`

Issue is explicitly non-blocking for a named release scope.

Required:

```text
release identifier
approver
reason
user impact
workaround or limitation
```

## 12.5 `ACCEPTED_WITH_WAIVER`

Issue is covered by a permitted time-bounded waiver.

The waiver does not change validation result fields.

---

# 13. Core issue fields

Every active issue must define:

| Field | Required | Meaning |
|---|---:|---|
| Issue ID | Yes | Stable identity |
| Title | Yes | Concise behavior summary |
| Lifecycle status | Yes | Current issue state |
| Category | Yes | Primary category |
| Severity | Yes | Impact level |
| Priority | Yes | Work priority |
| Release impact | Yes | Gate interpretation |
| Acceptance state | Yes | Review decision |
| First observed | Yes | Date, run, release, or source revision |
| Last reproduced | Yes for confirmed issues | Latest evidence |
| Affected scope | Yes | Modules, scenarios, artifacts, consumers |
| Unaffected scope | Recommended | Explicitly validated unaffected areas |
| Contract IDs | When applicable | Affected project contracts |
| Coverage IDs/gaps | When applicable | Related proof gaps |
| Status-ledger IDs | When applicable | Related implementation states |
| Issue/decision IDs | When applicable | External tracker or decisions |
| Preconditions | Recommended | Environment and configuration |
| Reproduction | Yes when reproducible | Minimal repeatable steps |
| Expected behavior | Yes | Contract/spec expectation |
| Actual behavior | Yes | Observed behavior |
| Evidence | Yes | Logs, run paths, scenario sections |
| Root cause | When known | Underlying cause |
| Workaround | When available | Safe temporary action |
| Risk | Yes | Consequences of leaving open |
| Owner | Yes | Responsible maintainer |
| Next action | Yes for open issues | Concrete work |
| Exit condition | Yes | Objective resolution proof |
| Target | Recommended | Milestone/release |
| User-facing note | When applicable | Release/documentation wording |
| Resolution | Required when closed | What changed |
| Resolved evidence | Required when closed | Test/run/review proof |
| Last reviewed | Yes | Date or release |

---

# 14. Issue registry summary

Fill and maintain this table.

| Issue ID | Title | Status | Severity | Priority | Release impact | Owner | Target | Last reviewed |
|---|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<TITLE>` | `<STATUS>` | `<SEVERITY>` | `<PRIORITY>` | `<RELEASE_IMPACT>` | `<OWNER>` | `<TARGET>` | `<DATE_OR_RELEASE>` |

When no issue is open:

| Metric | Value |
|---|---:|
| Open known issues | `0` |
| Release blockers | `0` |
| Checkpoint blockers | `0` |
| Accepted release issues | `0` |
| Issues pending triage | `0` |

---

# 15. Release-blocker registry

List every open release blocker.

| Issue ID | Gate | Blocking condition | Required correction | Owner | Target candidate | Status |
|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<RELEASE_GATE>` | `<CONDITION>` | `<CORRECTION>` | `<OWNER>` | `<TARGET>` | `<STATUS>` |

Rules:

- every `BLOCKS_RELEASE` issue appears here;
- an issue cannot disappear from this table without resolution or release-impact change;
- changing release impact requires review and rationale;
- a blocked required function cannot be removed from this table by reclassifying the scenario as optional without a project contract change.

---

# 16. Accepted issue registry

List every open issue accepted for a release.

| Issue ID | Release | Reason accepted | Scope limitation | Workaround | Risk | Approver | Review date |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<RELEASE>` | `<RATIONALE>` | `<LIMITATION>` | `<WORKAROUND_OR_NONE>` | `<RISK>` | `<APPROVER>` | `<DATE>` |

Accepted issues must also remain in the main registry.

Acceptance is release-specific unless project policy states otherwise.

---

# 17. Issue domains

The following sections provide project-specific registries.

Remove sections that are not applicable only when the project clearly cannot produce that issue class.

Retaining empty sections is acceptable.

---

# 18. Project identity issues

Use for:

```text
project ID mismatch
language code mismatch
module suffix drift
old-language identifier
wrong source root
conflicting active project copies
wrong release artifact identity
```

| Issue ID | Identity subject | Expected | Actual | Affected files | Release impact | Status | Notes |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<SUBJECT>` | `<EXPECTED>` | `<ACTUAL>` | `<FILES>` | `<IMPACT>` | `<STATUS>` | `<NOTES>` |

Identity issues are normally high impact because they can invalidate all downstream evidence.

---

# 19. Configuration issues

Use for:

```text
invalid project.toml
missing entrypoint
missing checkpoint
duplicate scenario ID
unsafe path
ambiguous release artifact
incorrect required/optional classification
hidden environment dependency
```

| Issue ID | Configuration key/domain | Observed problem | Affected consumer | Workaround | Release impact | Status |
|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<KEY_OR_DOMAIN>` | `<PROBLEM>` | `<CONSUMER>` | `<WORKAROUND>` | `<IMPACT>` | `<STATUS>` |

---

# 20. Module and dependency issues

Use for:

```text
compile failure
circular dependency
forbidden import direction
unreachable active module
duplicate provider
wrong module/file name
stale import
test-only dependency in release entrypoint
```

| Issue ID | Module/provider | Consumers | Problem | Contract IDs | Compile evidence | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<MODULE>` | `<CONSUMERS>` | `<PROBLEM>` | `<CONTRACT_IDS>` | `<EVIDENCE>` | `<IMPACT>` | `<STATUS>` |

---

# 21. Lincat and shared-type issues

Use for:

```text
missing field
wrong field type
undocumented consumer field
incorrect initialization
removed agreement dimension
parameter mismatch
flattened structure
unsafe coercion
```

| Issue ID | Category/type | Provider | Affected fields | Consumers | Observed behavior | Required contract | Release impact | Status |
|---|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<CATEGORY>` | `<MODULE>` | `<FIELDS>` | `<CONSUMERS>` | `<ACTUAL>` | `<EXPECTED>` | `<IMPACT>` | `<STATUS>` |

A shared-type issue must link to `CATEGORY_AND_LINCAT_CONTRACT.md`.

---

# 22. Morphology issues

Use for:

```text
wrong inflection
missing paradigm cell
incorrect stem operation
irregular-family failure
orthographic alternation error
feature agreement error
defective paradigm mishandling
duplicate morphology logic
```

| Issue ID | Domain | Paradigm/class | Representative input | Expected | Actual | Scenario/gold | Scope | Release impact | Status |
|---|---|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<NOUN_VERB_ETC>` | `<CLASS>` | `<INPUT>` | `<EXPECTED>` | `<ACTUAL>` | `<EVIDENCE>` | `<SCOPE>` | `<IMPACT>` | `<STATUS>` |

---

# 23. Syntax and constructor issues

Use for:

```text
incorrect word order
missing agreement propagation
wrong constructor arity use
incorrect complement handling
negation placement
question formation
relative formation
coordination behavior
subordination behavior
empty-string fallback
```

| Issue ID | Construction | Provider | Input/tree | Expected | Actual | Affected consumers | Scenario/gold | Release impact | Status |
|---|---|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<CONSTRUCTION>` | `<MODULE>` | `<INPUT>` | `<EXPECTED>` | `<ACTUAL>` | `<CONSUMERS>` | `<EVIDENCE>` | `<IMPACT>` | `<STATUS>` |

---

# 24. Lexicon issues

Use for:

```text
wrong paradigm assignment
duplicate abstract identifier
missing required closed-class item
incorrect orthography
temporary lexical placeholder
wrong category
unsupported multiword entry
```

| Issue ID | Lexical item/family | Provider | Expected category/form | Actual | User impact | Scenario | Release impact | Status |
|---|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<ITEM_OR_FAMILY>` | `<MODULE>` | `<EXPECTED>` | `<ACTUAL>` | `<IMPACT>` | `<SCENARIO>` | `<RELEASE_IMPACT>` | `<STATUS>` |

Open-class lexicon incompleteness is not automatically an issue.

It becomes an issue when it violates a declared inventory or release scope.

---

# 25. Structural lexicon issues

Use for:

```text
preposition case
pronoun features
determiner agreement
conjunction structure
subjunction behavior
placeholder structural item
```

| Issue ID | Family/item | Provider | Expected behavior | Actual behavior | Affected constructions | Evidence | Release impact | Status |
|---|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<FAMILY>` | `<MODULE>` | `<EXPECTED>` | `<ACTUAL>` | `<CONSTRUCTIONS>` | `<EVIDENCE>` | `<IMPACT>` | `<STATUS>` |

---

# 26. Entrypoint issues

Use for:

```text
entrypoint compile failure
missing import
wrong module identity
unloadable grammar
undeclared local dependency
stale artifact dependency
missing required function
```

| Issue ID | Entrypoint | Role | Problem | Checkpoint prerequisites | Scenario impact | PGF impact | Release impact | Status |
|---|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<ENTRYPOINT>` | `<ROLE>` | `<PROBLEM>` | `<CHECKPOINTS>` | `<SCENARIOS>` | `<PGF_IMPACT>` | `<IMPACT>` | `<STATUS>` |

---

# 27. Scenario issues

Use for:

```text
script missing
unsupported GF command
missing marker
nondeterministic output
wrong entrypoint
unbounded generation
timeout
incorrect assertion
input not loaded
interactive prompt
```

| Issue ID | Scenario ID | Script | Problem | Required/optional | Evidence | Workaround | Release impact | Status |
|---|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<SCENARIO_ID>` | `<SCRIPT>` | `<PROBLEM>` | `<REQUIREDNESS>` | `<RUN_PATH>` | `<WORKAROUND>` | `<IMPACT>` | `<STATUS>` |

A required scenario issue is normally release-blocking.

---

# 28. Input-data issues

Use for:

```text
missing input
wrong encoding
ambiguous format
unstable ordering
insufficient representative cases
licensed/private data problem
stale scenario reference
```

| Issue ID | Input file | Consumer scenarios | Problem | Data impact | Workaround | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<INPUT_FILE>` | `<SCENARIOS>` | `<PROBLEM>` | `<IMPACT>` | `<WORKAROUND>` | `<RELEASE_IMPACT>` | `<STATUS>` |

---

# 29. Gold issues

Use for:

```text
missing required gold
malformed header
scenario ID mismatch
normalization-version mismatch
unreviewed update
nondeterministic expectation
meaningful output normalized away
stale accepted behavior
```

| Issue ID | Scenario | Gold file | Problem | Expected policy | Current comparison | Review state | Release impact | Status |
|---|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<SCENARIO_ID>` | `<GOLD_FILE>` | `<PROBLEM>` | `<EXPECTED>` | `<RESULT>` | `<REVIEW>` | `<IMPACT>` | `<STATUS>` |

A gold mismatch is not resolved by updating the gold unless the implementation or specification change is intentional and reviewed.

---

# 30. PGF issues

Use for:

```text
PGF build failure
missing PGF
empty PGF
wrong artifact name
wrong entrypoint
missing concrete language
runtime load failure
consumer incompatibility
nondeterministic artifact concern
```

| Issue ID | PGF target | Provider | Problem | Build evidence | Runtime/consumer evidence | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<PGF_NAME>` | `<ENTRYPOINT>` | `<PROBLEM>` | `<EVIDENCE>` | `<EVIDENCE>` | `<IMPACT>` | `<STATUS>` |

---

# 31. Artifact and evidence issues

Use for:

```text
stale .gfo
missing raw stdout/stderr
manifest omission
hash mismatch
unsafe path
wrong producer
artifact changed after hashing
source-adjacent artifact accepted
run evidence incomplete
```

| Issue ID | Artifact role/path | Producer | Problem | Integrity impact | Evidence | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<ARTIFACT>` | `<PRODUCER>` | `<PROBLEM>` | `<IMPACT>` | `<EVIDENCE>` | `<RELEASE_IMPACT>` | `<STATUS>` |

---

# 32. Report and schema issues

Use for:

```text
invalid summary.json
count invariant mismatch
wrong schema version
missing required report
incorrect artifact path
status inconsistency
legacy alias emitted
manifest/summary disagreement
```

| Issue ID | Report/schema | Problem | Affected readers | Data integrity | Workaround | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<REPORT_OR_SCHEMA>` | `<PROBLEM>` | `<READERS>` | `<IMPACT>` | `<WORKAROUND>` | `<RELEASE_IMPACT>` | `<STATUS>` |

---

# 33. Toolchain issues

Use for:

```text
unsupported GF version
version-probe failure
RGL incompatibility
GF command behavior change
diagnostic output change
normalization affected by GF banner
missing executable
```

| Issue ID | Tool/version | Environment | Problem | Affected operations | Supported workaround | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<TOOL_VERSION>` | `<ENVIRONMENT>` | `<PROBLEM>` | `<OPERATIONS>` | `<WORKAROUND>` | `<IMPACT>` | `<STATUS>` |

Support claims must be evidence-based.

---

# 34. Platform issues

Use for:

```text
Windows path handling
Unicode path
spaces in path
process termination
CRLF behavior
filesystem permissions
path-length limits
case-insensitive collision
```

| Issue ID | Platform | Environment | Problem | Reproduction | Workaround | Supported status | Release impact | Status |
|---|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<PLATFORM>` | `<ENVIRONMENT>` | `<PROBLEM>` | `<STEPS>` | `<WORKAROUND>` | `<SUPPORTED_BEST_EFFORT>` | `<IMPACT>` | `<STATUS>` |

---

# 35. Performance issues

Use for:

```text
compile duration
scenario timeout risk
PGF size
memory use
unbounded output
slow diagnostic stage
```

| Issue ID | Operation | Baseline | Observed | Threshold/policy | User impact | Workaround | Release impact | Status |
|---|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<OPERATION>` | `<BASELINE>` | `<OBSERVED>` | `<POLICY>` | `<IMPACT>` | `<WORKAROUND>` | `<RELEASE_IMPACT>` | `<STATUS>` |

Performance is release-blocking only when the declared policy says so or execution times out.

---

# 36. Documentation issues

Use for material mismatch between documentation and implementation.

| Issue ID | Document | Claim/section | Actual implementation | Risk | Required update | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<DOCUMENT>` | `<CLAIM>` | `<ACTUAL>` | `<RISK>` | `<UPDATE>` | `<IMPACT>` | `<STATUS>` |

Minor editorial corrections need not become known issues unless they affect use, contracts, or release interpretation.

---

# 37. Coverage issues

Use for:

```text
required claim has no scenario
provider has no consumer proof
negative behavior untested
evidence stale
required release criterion unmapped
manual-only evidence where automation is required
```

| Issue ID | Coverage ID/gap | Claim | Missing proof | Current evidence | Risk | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<COV_OR_GAP_ID>` | `<CLAIM>` | `<MISSING>` | `<EVIDENCE>` | `<RISK>` | `<IMPACT>` | `<STATUS>` |

The coverage matrix remains authoritative for proof status.

---

# 38. Migration issues

Use for:

```text
legacy identifier remains active
source path cannot migrate safely
unknown legacy status
module rename incomplete
scenario/gold rename incomplete
project schema migration blocked
lossy migration
rollback unavailable
```

| Issue ID | Migration ID | Source form | Target form | Problem/loss | Workaround | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<MIGRATION_ID>` | `<SOURCE>` | `<TARGET>` | `<PROBLEM>` | `<WORKAROUND>` | `<IMPACT>` | `<STATUS>` |

---

# 39. Security issues

Security issue details may require restricted handling.

Public project records should contain enough information to identify risk and required action without exposing secrets or exploit details.

| Issue ID | Security class | Affected surface | Risk | Immediate mitigation | Disclosure policy | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<CLASS>` | `<SURFACE>` | `<RISK>` | `<MITIGATION>` | `<POLICY>` | `BLOCKS_RELEASE` | `<STATUS>` |

Normally blocking:

```text
arbitrary command execution
path traversal
unsafe source overwrite
secret leakage
artifact substitution
untrusted code loading
```

---

# 40. Data-integrity issues

Use for:

```text
source corruption
gold corruption
manifest mismatch
wrong fingerprint
stale evidence accepted
migration loss
incorrect provenance
summary/result disagreement
```

| Issue ID | Data/artifact | Integrity invariant | Violation | Recovery | Evidence | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<SUBJECT>` | `<INVARIANT>` | `<VIOLATION>` | `<RECOVERY>` | `<EVIDENCE>` | `BLOCKS_RELEASE` | `<STATUS>` |

---

# 41. Release-process issues

Use for:

```text
approval missing
rollback unavailable
version mismatch
release note incomplete
candidate changed after validation
wrong run selected
waiver expired
```

| Issue ID | Release subject | Problem | Candidate/release | Required action | Owner | Release impact | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<SUBJECT>` | `<PROBLEM>` | `<CANDIDATE>` | `<ACTION>` | `<OWNER>` | `BLOCKS_RELEASE` | `<STATUS>` |

---

# 42. Issue reproduction requirements

A confirmed reproducible issue should include:

```text
source revision
project configuration hash or relevant configuration
GF Wordbench version
GF version
RGL revision when applicable
platform
entrypoint/checkpoint
scenario
input
command or validation mode
expected behavior
actual behavior
run ID
evidence paths
```

Use the smallest reproduction that preserves the defect.

Do not replace project-owned scenario evidence with an ad hoc shell command when the issue belongs to a required scenario.

---

# 43. Reproduction quality

Reproduction quality levels:

```text
R0 — anecdotal
R1 — manual steps
R2 — repeatable local command
R3 — version-controlled fixture/scenario
R4 — automated regression proof
```

A high-severity confirmed issue should progress toward `R3` or `R4`.

An issue may remain at `R1` when reproduction depends on an external environment that cannot be captured, but the limitation must be explicit.

---

# 44. Evidence requirements

Accepted evidence includes:

```text
compile stdout/stderr
scenario stdout/stderr
normalized output
gold diff
summary.json
manifest.json
PGF artifact result
source diff
contract diff
coverage row
manual linguistic review
toolchain probe
platform reproduction
migration report
```

Evidence must be current enough to support the issue state.

Do not use:

```text
memory
unretained console output
unidentified screenshot
old run from another source revision
stale source-adjacent artifact
```

as the sole proof of a release-blocking issue.

---

# 45. Expected versus actual behavior

Expected behavior must come from one or more of:

```text
project contract
language specification
morphology specification
syntax/constructor rules
validation specification
gold
approved decision
external GF contract
release criterion
```

Do not define expected behavior only after seeing the current output unless the behavior is being intentionally redesigned.

Actual behavior should quote or summarize evidence without overstating scope.

---

# 46. Scope analysis

Every confirmed issue should answer:

```text
Which provider is wrong?
Which direct consumers are affected?
Which downstream entrypoints are affected?
Which scenarios expose the issue?
Which inputs trigger it?
Which golds or artifacts are affected?
Which similar cases are proven unaffected?
Which versions/environments are affected?
```

Avoid assuming that one observed example proves a whole family is defective.

Avoid assuming that one passing example proves a whole family is safe.

---

# 47. Root-cause classification

Suggested root-cause classes:

```text
SPECIFICATION_GAP
CONTRACT_DRIFT
PROVIDER_DEFECT
CONSUMER_DEFECT
INITIALIZATION_DEFECT
MORPHOLOGY_RULE
SYNTAX_RULE
LEXICON_DATA
SCENARIO_DEFECT
INPUT_DEFECT
GOLD_DEFECT
NORMALIZATION_DEFECT
TOOLCHAIN_CHANGE
PLATFORM_BEHAVIOR
CONFIGURATION_DEFECT
MIGRATION_DEFECT
ARTIFACT_FRESHNESS
REPORTING_DEFECT
UNKNOWN
```

Root cause may change as investigation progresses.

Do not mark an issue resolved merely because a downstream symptom was patched if the provider defect remains.

---

# 48. Diagnostic causality

When compilation or scenario failures occur, distinguish:

```text
direct
downstream
ambiguous
noise
```

A downstream issue record should reference the root issue rather than becoming a duplicate root cause.

Example:

```text
KI-LINCAT-003
  provider lincat field removed

downstream failures:
  Syntax module compile
  Question module compile
  release entrypoint compile
```

Track the provider defect as canonical unless downstream recovery requires separate work.

---

# 49. Workaround policy

A workaround must be:

- safe;
- reproducible;
- bounded;
- clearly temporary when appropriate;
- non-destructive;
- consistent with project contracts or explicitly outside them;
- accompanied by risks and limitations.

Prohibited workaround examples:

```text
skip required checkpoint
mark required scenario optional
delete failing gold
accept stale PGF
flatten lincat to Str without contract change
ignore unsupported GF command
hide warning from reports
```

A workaround that changes the intended contract requires a decision and migration, not only an issue note.

---

# 50. Mitigation policy

A mitigation reduces impact but may leave root cause open.

Examples:

```text
disable optional feature
add input validation
limit generation depth
pin supported GF version
add explicit warning
exclude unsupported platform
```

Mitigation must not cause the issue to be marked `RESOLVED` unless the exit condition says the reduced scope is the accepted final design.

---

# 51. Exit condition

Every issue needs an objective exit condition.

Good examples:

```text
provider and all listed consumers compile
required scenario returns OK
gold match is true after reviewed change
no missing functions outside accepted set
PGF builds and loads
migration completes without semantic loss
coverage row reaches required evidence level
documentation and source identifiers agree
two clean release runs reproduce the result
```

Weak exit conditions:

```text
looks fixed
seems better
review later
no longer noticed
probably upstream
```

---

# 52. Resolution evidence

A resolved issue must record:

```text
fix revision
changed providers
changed consumers
changed scenarios/inputs
changed golds
changed contracts
changed documentation
regression proof
release run or verification run
```

If the issue was closed as designed, record the contract or documentation correction proving the design.

---

# 53. Resolution categories

Canonical resolution categories:

```text
FIXED
SPECIFICATION_CORRECTED
DOCUMENTATION_CORRECTED
SCOPE_REDUCED
UPSTREAM_FIXED
MIGRATED
DUPLICATE
CLOSED_AS_DESIGNED
WONT_FIX
FEATURE_RETIRED
```

Resolution category does not replace lifecycle status.

---

# 54. Reopening policy

Reopen a resolved issue when:

- the same root condition returns;
- resolution evidence was invalid;
- affected scope was underestimated;
- a supported environment still fails;
- the fix introduced an equivalent regression.

Use the same issue ID when root cause is materially the same.

Create a new issue when the symptom is similar but the root cause is independent.

Record reopening date and evidence.

---

# 55. Duplicate policy

When marking duplicate:

```text
canonical issue ID
reason for duplication
unique evidence to retain
```

Move any unique affected-scope or reproduction information to the canonical issue.

Do not delete historical duplicate IDs.

---

# 56. `WONT_FIX` policy

`WONT_FIX` requires:

```text
reason
affected users
scope boundary
workaround
release impact
approver
reconsideration trigger
```

Valid reasons may include:

```text
outside declared scope
upstream limitation
cost disproportionate to supported use
feature scheduled for retirement
behavior intentionally unsupported
```

Invalid reason:

```text
issue has existed for a long time
```

A high-severity contract violation cannot become non-blocking solely through `WONT_FIX`.

---

# 57. Deferred issue policy

A deferred issue must specify:

```text
target release/milestone
reason
interim risk
interim validation
owner
revisit date or trigger
```

A deferred release blocker still blocks the current release.

---

# 58. Accepted limitation policy

A limitation may be accepted when:

- it is outside declared release scope; or
- it is inherent to a supported upstream tool; or
- behavior is intentionally bounded; or
- the feature is explicitly optional; or
- the issue is user-visible but contract-compliant.

Required documentation:

```text
scope boundary
user impact
workaround
coverage
release note when relevant
```

Accepted limitation does not imply that a corresponding required contract is satisfied.

---

# 59. Temporary implementation linkage

Every issue caused by:

```text
temporary implementation
fallback
disabled function
shallow constructor
string-based substitute
inherited placeholder
blocked provider
```

must link to a `STATUS_LEDGER__TEMPLATES_PROJECT_DOCS.md` entry.

The known issue describes observed or expected impact.

The ledger describes implementation maturity, owner, and exit action.

Example:

```text
Known issue:
  KI-MORPH-004 — irregular verb family yields fallback forms

Status ledger:
  STATUS-MORPH-007 — temporary fallback in irregular constructor
```

---

# 60. Coverage linkage

Every issue exposing missing or insufficient proof should link to:

```text
coverage row ID
coverage gap ID
regression row
```

Examples:

```text
issue discovered because negative parse cases were absent
issue remains unverified on Windows
fix lacks regression scenario
manual-only morphology review
```

A resolved defect normally requires a regression proof.

---

# 61. Contract linkage

Link affected project contracts when an issue involves:

```text
public GF symbol
lincat field
provider/consumer relationship
entrypoint
scenario ID
gold ownership
release artifact
documentation guarantee
release gate
```

A contract violation normally blocks release until:

- the implementation is restored; or
- the contract is deliberately changed and migrated.

---

# 62. Decision-log linkage

Use a decision entry when issue resolution requires:

```text
new architecture
scope reduction
accepted linguistic variant policy
entrypoint change
module ownership change
lincat redesign
normalization change
gold acceptance-policy change
supported-GF-version change
permanent workaround
feature retirement
```

Routine local bug fixes do not require a decision entry unless project policy says otherwise.

---

# 63. Scenario and gold linkage

An issue involving linguistic behavior should reference:

```text
scenario ID
section ID
input ID/file
gold file
normalized output
gold diff
```

When no scenario exists, record the coverage gap and create one when practical.

Gold must not be updated before deciding whether actual behavior or expected behavior is wrong.

---

# 64. Issue discovery sources

Issues may be discovered through:

```text
source review
static scan
direct compile
checkpoint compile
entrypoint compile
missing-function inspection
load scenario
linearization scenario
parse scenario
generation scenario
morphology scenario
gold comparison
PGF build/load
previous-run diff
manual linguistic review
migration
toolchain upgrade
platform testing
user report
release incident
```

Record the discovery source.

---

# 65. Validation-result mapping

Validation results are observations, not issue lifecycle states.

Examples:

```text
FileResult status = FAIL
→ may create or update a known issue

ScenarioResult status = ERROR
→ may indicate toolchain, configuration, or scenario issue

gold_match = false
→ may indicate implementation, specification, gold, or normalization issue

diagnostic_class = downstream
→ usually references a provider issue
```

Do not automatically create one permanent issue per failed target.

First classify root cause.

---

# 66. Status semantics

Use project validation meanings consistently:

```text
OK
FAIL
ERROR
SKIPPED
```

Typical issue interpretation:

| Validation status | Issue interpretation |
|---|---|
| `OK` | Current validation passed; issue may still exist outside covered cases |
| `FAIL` | Expected validation was executed and not satisfied |
| `ERROR` | Validation could not reliably determine the intended result |
| `SKIPPED` | Evidence absent because validation did not run |

A required `ERROR` or `SKIPPED` is not evidence that the feature is correct.

---

# 67. Issue review before release

Before each release:

```text
[ ] Every open issue is triaged
[ ] Every open issue has release impact
[ ] Every blocker is in the blocker registry
[ ] Every accepted issue is in the accepted registry
[ ] Every accepted issue has approver and rationale
[ ] Every required-function issue is reviewed
[ ] Every temporary implementation issue links to the ledger
[ ] Every issue with a fix has regression evidence
[ ] Every resolved issue has resolution evidence
[ ] Every user-visible issue appears in release notes when required
[ ] No unknown-pending-triage issue affects required scope
[ ] No expired waiver remains
```

---

# 68. Normal release rules

For a normal release:

```text
open CRITICAL issues:
  zero

open HIGH issues affecting required scope:
  zero

BLOCKS_RELEASE issues:
  zero

UNKNOWN_PENDING_TRIAGE issues affecting required scope:
  zero

open data-integrity blockers:
  zero

open security blockers:
  zero

accepted release issues:
  explicitly reviewed
```

A project may release with non-blocking known issues only when release criteria permit them.

---

# 69. Baseline rules

A migration or development baseline may retain blocking issues.

Baseline requirements:

- every blocker is explicit;
- every blocker has owner and exit condition;
- baseline is not labeled release-ready;
- observed failures remain visible;
- required evidence is not fabricated;
- source state and run ID are recorded.

---

# 70. Waiver policy

A waiver may apply only where `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md` permits it.

The issue remains open and retains its real severity and release result.

Waiver fields:

```text
waiver ID
issue ID
release
criterion
reason
risk
compensating evidence
approver
approval date
expiration
follow-up
```

A waiver must not:

- change `FAIL` to `OK`;
- change `ERROR` to `OK`;
- make missing gold exist;
- make stale PGF current;
- make a security issue safe without mitigation;
- redefine a required contract silently.

---

# 71. User-facing issue notes

A user-facing note should state:

```text
affected behavior
affected versions
trigger
observable effect
workaround
planned correction when known
```

Avoid exposing:

```text
secrets
personal paths
unsafe exploit detail
unsupported speculation
```

Use neutral, precise language.

---

# 72. Issue tracker linkage

An external issue tracker may manage work discussion.

This project document remains the source of release-relevant issue classification.

For each linked tracker item, record:

```text
tracker ID or URL reference
relationship
canonical project issue ID
```

Do not depend on tracker labels alone for release impact.

---

# 73. Source-comment linkage

Source comments may reference issue IDs:

```gf
-- KI-MORPH-004: temporary irregular fallback; see STATUS-MORPH-007.
```

Rules:

- comment must not be the only issue record;
- resolved comments are removed or updated;
- comments and known-issue state must agree;
- source must not contain stale old issue IDs.

---

# 74. Commit and change linkage

Commits or changes may reference issue IDs.

Recommended:

```text
Fix KI-SYNTAX-003: preserve object agreement
```

Issue resolution should list the relevant revision.

Do not mark resolved merely because a commit message mentions the issue.

Validation evidence remains required.

---

# 75. Issue metrics

Metrics are diagnostic.

Suggested summary:

| Metric | Value |
|---|---:|
| Open issues | `<COUNT>` |
| Confirmed issues | `<COUNT>` |
| Pending triage | `<COUNT>` |
| Release blockers | `<COUNT>` |
| Checkpoint blockers | `<COUNT>` |
| Accepted release issues | `<COUNT>` |
| Monitoring | `<COUNT>` |
| Resolved this release | `<COUNT>` |
| Open coverage-related issues | `<COUNT>` |
| Open toolchain/platform issues | `<COUNT>` |

Do not use total issue count alone as a quality measure.

---

# 76. Aging review

Issue age may inform priority but not severity.

Review old issues for:

```text
still reproducible
still in declared scope
still correctly classified
workaround still safe
owner still valid
target still realistic
upstream behavior changed
coverage improved
feature retired
```

Do not close an issue solely because it is old.

---

# 77. Stale issue criteria

An issue record is stale when:

- evidence points to a deleted run;
- affected modules no longer exist;
- owner is invalid;
- target release passed without review;
- workaround references old project paths;
- contract IDs were retired;
- issue status contradicts current validation;
- last review exceeds project policy.

Stale issues must be reviewed before release.

---

# 78. Issue change workflow

For each issue update:

1. preserve issue ID;
2. update evidence;
3. update affected scope;
4. update severity only when impact changed;
5. update priority when plan changed;
6. update release impact through review;
7. update related ledger/coverage/contract references;
8. update owner and next action;
9. record review date;
10. retain status history when material.

---

# 79. New issue workflow

```text
observe
→ assign issue ID
→ record minimal evidence
→ reproduce
→ classify root cause
→ determine scope
→ link contracts
→ link coverage/ledger
→ assign severity and priority
→ determine release impact
→ assign owner
→ define next action and exit condition
→ add regression proof plan
```

A critical observation should be escalated before full documentation is complete.

---

# 80. Fix workflow

```text
confirm current issue
→ identify provider/root cause
→ review consumers
→ update implementation
→ update contracts if intended behavior changed
→ update scenarios/inputs
→ review gold
→ add regression proof
→ run direct validation
→ run downstream validation
→ run release-relevant validation
→ record resolution evidence
→ move to monitoring or resolved
```

Do not fix only the symptom when a shared provider remains wrong.

---

# 81. Gold-related fix workflow

When an issue changes output:

1. determine whether implementation or expectation is wrong;
2. update specification/decision first when expectation changes;
3. fix provider and consumers;
4. run scenario;
5. preserve raw old/new evidence;
6. normalize;
7. review diff linguistically;
8. explicitly update gold when justified;
9. rerun comparison;
10. update issue and coverage records.

---

# 82. Toolchain-related fix workflow

When an issue depends on GF/RGL:

```text
record old/new versions
reproduce on supported baseline
reproduce on target version
review command behavior
review diagnostics
review normalization
review gold differences
update compatibility policy
pin or migrate as appropriate
```

Do not describe an untested newer version as fixed or supported.

---

# 83. Issue closure checklist

```text
[ ] Root cause understood or final design documented
[ ] Provider corrected or scope changed deliberately
[ ] Direct consumers reviewed
[ ] Downstream entrypoints validated
[ ] Scenario added or updated
[ ] Inputs added or updated
[ ] Gold reviewed when affected
[ ] Regression proof passes
[ ] Contract lock updated when affected
[ ] Coverage matrix updated
[ ] Status ledger updated
[ ] Decision log updated when required
[ ] Documentation updated
[ ] Release impact cleared
[ ] Resolution evidence recorded
[ ] Last reviewed updated
```

---

# 84. Issue reopening checklist

```text
[ ] Same root issue confirmed
[ ] New evidence recorded
[ ] Affected versions updated
[ ] Scope re-evaluated
[ ] Severity re-evaluated
[ ] Release impact re-evaluated
[ ] Previous resolution analyzed
[ ] Regression proof corrected
[ ] Owner and target updated
```

---

# 85. Template issue summary

Complete this section after project initialization.

```text
Project ID: <PROJECT_ID>
Project version or baseline: <VERSION_OR_BASELINE>
Source revision: <SOURCE_REVISION>
GF Wordbench version: <GF_WORDBENCH_VERSION>
GF version: <GF_VERSION>
RGL revision: <RGL_REVISION_OR_NONE>
Last full issue review: <DATE_OR_RELEASE>

Open issues: <COUNT>
Release blockers: <COUNT>
Checkpoint blockers: <COUNT>
Issues pending triage: <COUNT>
Accepted release issues: <COUNT>
Issues under monitoring: <COUNT>
Resolved issues: <COUNT>
```

---

# 86. Detailed issue template

Copy this section for each issue.

```markdown
## <ISSUE_ID> — <CONCISE_TITLE>

**Lifecycle status:** `REPORTED | CONFIRMED | TRIAGED | IN_PROGRESS | MONITORING | RESOLVED | CLOSED_AS_DESIGNED | DUPLICATE | WONT_FIX | DEFERRED | RETIRED`

**Category:** `<CATEGORY>`

**Severity:** `CRITICAL | HIGH | MEDIUM | LOW | INFORMATIONAL`

**Priority:** `P0 | P1 | P2 | P3 | P4`

**Release impact:** `BLOCKS_RELEASE | BLOCKS_CHECKPOINT | BLOCKS_MIGRATION | BLOCKS_FEATURE | NON_BLOCKING_ACCEPTED | NON_BLOCKING_OUT_OF_SCOPE | OPTIONAL_ONLY | UNKNOWN_PENDING_TRIAGE`

**Acceptance state:** `NOT_REVIEWED | REJECTED_FOR_RELEASE | ACCEPTED_FOR_BASELINE | ACCEPTED_FOR_RELEASE | ACCEPTED_WITH_WAIVER`

**First observed**

`<DATE_RUN_RELEASE_OR_REVISION>`

**Last reproduced**

`<DATE_RUN_OR_NONE>`

**Discovery source**

`<COMPILE_SCENARIO_REVIEW_MIGRATION_USER_REPORT_ETC>`

**Affected scope**

- Provider: `<MODULE_OR_FILE>`;
- Direct consumers: `<CONSUMERS>`;
- Entrypoints: `<ENTRYPOINTS>`;
- Scenarios: `<SCENARIOS>`;
- Inputs: `<INPUTS>`;
- Golds: `<GOLDS>`;
- Artifacts: `<ARTIFACTS>`;
- Environments: `<ENVIRONMENTS>`.

**Unaffected scope**

- `<PROVEN_UNAFFECTED_SCOPE_OR_UNKNOWN>`.

**Related records**

- Contract IDs: `<CONTRACT_IDS_OR_NONE>`;
- Coverage IDs/gaps: `<COVERAGE_IDS_OR_NONE>`;
- Status-ledger IDs: `<STATUS_IDS_OR_NONE>`;
- Decision IDs: `<DECISION_IDS_OR_NONE>`;
- Migration IDs: `<MIGRATION_IDS_OR_NONE>`;
- External tracker: `<TRACKER_REFERENCE_OR_NONE>`.

**Preconditions**

```text
Project configuration:
Source revision:
GF Wordbench version:
GF version:
RGL revision:
Platform:
Validation mode:
Entrypoint/checkpoint:
Scenario:
Input:
```

**Reproduction**

1. `<STEP>`;
2. `<STEP>`;
3. `<STEP>`.

**Expected behavior**

`<EXPECTED_BEHAVIOR_AND_SOURCE_OF_EXPECTATION>`

**Actual behavior**

`<ACTUAL_BEHAVIOR>`

**Evidence**

- Run ID: `<RUN_ID_OR_NONE>`;
- Summary: `<SUMMARY_PATH_OR_NONE>`;
- Compile stdout: `<PATH_OR_NONE>`;
- Compile stderr: `<PATH_OR_NONE>`;
- Scenario stdout: `<PATH_OR_NONE>`;
- Scenario stderr: `<PATH_OR_NONE>`;
- Normalized output: `<PATH_OR_NONE>`;
- Gold diff: `<PATH_OR_NONE>`;
- Artifact: `<PATH_OR_NONE>`;
- Manual review: `<REVIEW_RECORD_OR_NONE>`;
- Reproduction quality: `<R0_R1_R2_R3_R4>`.

**Diagnostic classification**

- Error kind: `<ERROR_KIND_OR_NONE>`;
- Diagnostic class: `<DIRECT_DOWNSTREAM_AMBIGUOUS_NOISE_SKIPPED_OR_NONE>`;
- Root-cause class: `<ROOT_CAUSE_CLASS_OR_UNKNOWN>`;
- Primary message: `<MESSAGE>`.

**Root cause**

`<KNOWN_ROOT_CAUSE_OR_UNKNOWN_WITH_INVESTIGATION_PLAN>`

**Risk**

`<USER_PROJECT_RELEASE_DATA_OR_SECURITY_RISK>`

**Workaround**

`<SAFE_WORKAROUND_OR_NONE>`

**Workaround limitations**

`<LIMITATIONS_OR_NONE>`

**Mitigation**

`<MITIGATION_OR_NONE>`

**Owner**

`<OWNER>`

**Next action**

`<CONCRETE_ACTION>`

**Exit condition**

`<OBJECTIVE_PASS_CONDITION>`

**Target**

`<MILESTONE_OR_RELEASE>`

**User-facing note**

`<RELEASE_NOTE_OR_NONE>`

**Acceptance/waiver**

- Accepted for: `<BASELINE_RELEASE_OR_NONE>`;
- Approver: `<APPROVER_OR_NONE>`;
- Review date: `<DATE_OR_NONE>`;
- Waiver ID: `<WAIVER_ID_OR_NONE>`;
- Expiration: `<DATE_RELEASE_OR_NONE>`.

**Resolution**

- Resolution category: `<CATEGORY_OR_NONE>`;
- Fix revision: `<REVISION_OR_NONE>`;
- Changed providers: `<FILES_OR_NONE>`;
- Changed consumers: `<FILES_OR_NONE>`;
- Changed scenarios/inputs: `<FILES_OR_NONE>`;
- Changed golds: `<FILES_OR_NONE>`;
- Changed contracts/docs: `<FILES_OR_NONE>`;
- Regression evidence: `<EVIDENCE_OR_NONE>`;
- Resolved run: `<RUN_ID_OR_NONE>`;
- Resolved date: `<DATE_OR_NONE>`.

**Last reviewed**

`<DATE_OR_RELEASE>`
```

---

# 87. Compact issue template

Use only for low-complexity non-blocking issues.

```markdown
## <ISSUE_ID> — <TITLE>

- Status: `<STATUS>`;
- Category: `<CATEGORY>`;
- Severity: `<SEVERITY>`;
- Release impact: `<RELEASE_IMPACT>`;
- Affected scope: `<SCOPE>`;
- Expected: `<EXPECTED>`;
- Actual: `<ACTUAL>`;
- Evidence: `<EVIDENCE>`;
- Workaround: `<WORKAROUND_OR_NONE>`;
- Owner: `<OWNER>`;
- Exit condition: `<EXIT_CONDITION>`;
- Last reviewed: `<DATE_OR_RELEASE>`.
```

Do not use the compact form for:

```text
release blockers
security issues
data-integrity issues
multi-module contract drift
migration loss
complex linguistic defects
```

---

# 88. Accepted-issue template

```markdown
## Acceptance for <ISSUE_ID>

**Release/baseline**

`<RELEASE_OR_BASELINE>`

**Decision**

`ACCEPTED_FOR_RELEASE | ACCEPTED_FOR_BASELINE | ACCEPTED_WITH_WAIVER`

**Reason**

`<RATIONALE>`

**Declared limitation**

`<LIMITATION>`

**Affected users/consumers**

`<SCOPE>`

**Workaround**

`<WORKAROUND_OR_NONE>`

**Residual risk**

`<RISK>`

**Compensating evidence**

`<EVIDENCE>`

**Approver**

`<APPROVER>`

**Approval date**

`<DATE>`

**Expiration/review trigger**

`<DATE_RELEASE_OR_TRIGGER>`

**Release-note requirement**

`<YES_NO_AND_TEXT>`
```

---

# 89. Resolution template

```markdown
## Resolution of <ISSUE_ID>

**Resolution category**

`FIXED | SPECIFICATION_CORRECTED | DOCUMENTATION_CORRECTED | SCOPE_REDUCED | UPSTREAM_FIXED | MIGRATED | DUPLICATE | CLOSED_AS_DESIGNED | WONT_FIX | FEATURE_RETIRED`

**Summary**

`<WHAT_CHANGED>`

**Root-cause correction**

`<CORRECTION>`

**Affected files**

- `<FILE>`;
- `<FILE>`.

**Contract/document updates**

- `<CONTRACT_OR_DOC>`;
- `<CONTRACT_OR_DOC>`.

**Regression proof**

- `<SCENARIO_OR_TEST>`;
- `<RUN_AND_EVIDENCE>`.

**Exit condition result**

`<PASS_RESULT>`

**Resolved by**

`<OWNER>`

**Resolved in revision**

`<REVISION>`

**Resolved in release**

`<RELEASE_OR_NONE>`

**Resolved date**

`<DATE>`
```

---

# 90. Issue history template

Use when material state changes should be retained.

| Date/release | Status | Severity | Release impact | Change | Evidence | Reviewer |
|---|---|---|---|---|---|---|
| `<DATE>` | `<STATUS>` | `<SEVERITY>` | `<IMPACT>` | `<CHANGE>` | `<EVIDENCE>` | `<REVIEWER>` |

Do not record every editorial update.

Record changes affecting interpretation, scope, priority, acceptance, or resolution.

---

# 91. Resolved issue archive

Move resolved entries to this section only after their resolution evidence is complete.

Suggested summary:

| Issue ID | Title | Resolution | Resolved in | Regression evidence | Last reviewed |
|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<TITLE>` | `<RESOLUTION_CATEGORY>` | `<RELEASE_OR_REVISION>` | `<EVIDENCE>` | `<DATE>` |

Detailed historical entries may remain below the table.

Do not delete resolved issue records needed to interpret prior releases or gold changes.

---

# 92. Closed-as-designed archive

| Issue ID | Reported behavior | Final design interpretation | Documentation/contract update | Closed in | Last reviewed |
|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<BEHAVIOR>` | `<INTERPRETATION>` | `<REFERENCE>` | `<RELEASE>` | `<DATE>` |

---

# 93. Deferred issue registry

| Issue ID | Reason deferred | Interim risk | Interim mitigation | Owner | Target | Revisit trigger |
|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<REASON>` | `<RISK>` | `<MITIGATION>` | `<OWNER>` | `<TARGET>` | `<TRIGGER>` |

A deferred blocker remains blocking for any milestone it affects.

---

# 94. Upstream issue registry

Use when the active project depends on an unresolved upstream GF/RGL issue.

| Issue ID | Upstream project | Upstream reference | Local impact | Local workaround | Supported versions | Review trigger | Status |
|---|---|---|---|---|---|---|---|
| `<ISSUE_ID>` | `<GF_RGL_OTHER>` | `<REFERENCE>` | `<IMPACT>` | `<WORKAROUND>` | `<VERSIONS>` | `<TRIGGER>` | `<STATUS>` |

Local maintainers remain responsible for accurate release impact.

“Upstream” is not a valid substitute for triage.

---

# 95. Issue summary by release

| Release/baseline | Open blockers | Accepted issues | New issues | Resolved issues | Known limitations | Review record |
|---|---:|---:|---:|---:|---:|---|
| `<RELEASE>` | `<COUNT>` | `<COUNT>` | `<COUNT>` | `<COUNT>` | `<COUNT>` | `<REFERENCE>` |

---

# 96. Initialization checklist

When creating a new project from this template:

```text
[ ] Replace project summary placeholders
[ ] Delete template-only issue examples
[ ] Import known issues from the existing GF project
[ ] Import known toolchain/platform restrictions
[ ] Link every temporary implementation to STATUS_LEDGER__TEMPLATES_PROJECT_DOCS.md
[ ] Link every contract issue to INTERFILE_CONTRACT_LOCK.md
[ ] Link every validation gap to TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md
[ ] Mark every issue with release impact
[ ] Assign every open issue to an owner
[ ] Define every open issue exit condition
[ ] Record baseline run evidence
[ ] Separate blockers from accepted limitations
[ ] Remove stale old-language issue references
[ ] Verify no required placeholder remains before release
```

---

# 97. Migration from an existing issue list

When importing issues from another document or tracker:

1. preserve old identifier as a reference;
2. create one canonical project issue ID;
3. determine whether the issue remains reproducible;
4. identify current provider and consumers;
5. identify affected contracts;
6. identify current validation evidence;
7. classify severity and release impact under current policy;
8. link any temporary code to the status ledger;
9. link any evidence gap to the coverage matrix;
10. define an exit condition;
11. retain historical resolution notes;
12. avoid importing obsolete discussion as active facts.

Do not copy an issue as open merely because it existed in the old project.

Do not close it merely because the old project marked it closed.

Revalidate against the current source.

---

# 98. Migration from `gf-audit` issue records

Legacy audit failures may be evidence for a project issue.

They are not automatically one-to-one issue entries.

Migration steps:

```text
legacy run failure
→ identify current source equivalent
→ reproduce with GF Wordbench
→ classify direct/downstream cause
→ create or update canonical issue
→ link historical evidence
```

Legacy modes map:

```text
file → quick
all → diagnostic
```

Historical summaries may lack scenario evidence.

Do not invent missing scenario results.

---

# 99. Release checklist

```text
[ ] No open CRITICAL issue
[ ] No open HIGH issue affecting required scope
[ ] No BLOCKS_RELEASE issue
[ ] No UNKNOWN_PENDING_TRIAGE issue affecting required scope
[ ] No unresolved security blocker
[ ] No unresolved data-integrity blocker
[ ] Every accepted issue has approval
[ ] Every accepted issue appears in release notes when user-visible
[ ] Every waiver is valid and unexpired
[ ] Every issue caused by temporary code links to status ledger
[ ] Every fixed issue has regression evidence
[ ] Every resolved issue has exit evidence
[ ] Every issue was reviewed for the candidate
[ ] Issue counts agree with release records
```

---

# 100. Project-completion checklist

A project must not be declared complete while:

```text
a required behavior issue is untriaged
a release blocker remains
a required provider is disabled
a required contract is blocked
a required scenario issue remains
a required gold issue remains
the expected PGF issue remains
a security or data-integrity issue remains
an issue lacks owner or exit condition
```

A project may be complete with intentional limitations only when those limitations define the declared scope and are validated accordingly.

---

# 101. Known-issue review questions

For every open issue, ask:

```text
Is the issue still reproducible?
What exact contract or claim is affected?
Is this a root issue or downstream symptom?
Which users and consumers are affected?
Is the severity accurate?
Does it block release?
Is the workaround safe?
Does temporary code exist?
Does coverage expose the issue?
Does a regression test exist?
Has toolchain behavior changed?
Is the owner active?
Is the exit condition objective?
Should the issue instead become a design decision or scope exclusion?
```

---

# 102. Known-issue anti-patterns

Prohibited:

## 102.1 Vague issue

```text
Morphology needs work.
```

No scope, evidence, or exit condition exists.

## 102.2 Permanent “temporary” issue

A fallback remains for multiple releases with no owner or plan.

## 102.3 Release-blocker downgrade

A required failure is labeled informational to permit release.

## 102.4 One issue per downstream failure

A provider defect creates separate duplicate issue records for every consumer.

## 102.5 Issue without contract

A public behavior defect does not identify its governing contract or specification.

## 102.6 Closed without proof

A code change exists but no scenario, compile, or review evidence verifies it.

## 102.7 Gold-as-fix

Expected output is changed solely to make the issue disappear.

## 102.8 Tracker-only release decision

Release impact exists only in external tracker labels.

## 102.9 Stale workaround

Workaround references an old module, scenario, path, or GF version.

## 102.10 Hidden accepted issue

Release proceeds with a known limitation absent from this file and release notes.

## 102.11 Mixed issue and roadmap

Feature requests unrelated to defects or declared limitations dominate the issue registry.

## 102.12 Template examples treated as active issues

Placeholder rows remain in the active project and are counted.

---

# 103. Balanced issue policy

This file should be detailed enough to support safe maintenance and release decisions without duplicating an entire issue tracker.

Keep a project issue here when it:

- affects declared behavior;
- affects release decisions;
- affects cross-file contracts;
- requires a persistent workaround;
- represents a known limitation;
- requires historical interpretation;
- affects migration or compatibility;
- affects validation reliability.

Keep ordinary implementation tasks only in the issue tracker when they do not represent a known project problem or release-relevant limitation.

---

# 104. Drift indicators

Probable known-issue drift exists when:

- source contains a fallback with no issue or status entry;
- an issue names a deleted module;
- a blocker is absent from the release checklist;
- an accepted issue lacks approval;
- an issue says non-blocking while release criteria say blocking;
- a fixed issue lacks regression evidence;
- gold changed but the related issue was not reviewed;
- a coverage gap exists but no issue tracks its release risk;
- an issue references an old language suffix;
- an issue references a legacy scenario ID;
- a resolved issue still reproduces;
- an issue owner is unknown;
- an issue has no exit condition;
- an upstream issue is assumed fixed without retest;
- a `WONT_FIX` issue violates an active required contract;
- open counts disagree with the registry.

Every drift indicator must be reviewed before release.

---

# 105. Automated checks

GF Wordbench should eventually validate:

```text
issue IDs unique
required issue fields present
lifecycle values valid
severity values valid
release-impact values valid
contract IDs resolve
coverage IDs resolve
status-ledger IDs resolve
scenario IDs resolve
gold paths resolve
owner present for open issues
exit condition present for open issues
resolution evidence present for resolved issues
release blockers appear in blocker registry
accepted issues appear in accepted registry
no unresolved required placeholder in active project
```

A future machine-readable companion requires a registered schema.

---

# 106. Suggested machine-readable companion

A future project may use:

```text
project/issues.toml
```

or another registered format.

It must not be introduced without:

```text
schema ID
schema version
owner
reader
writer or manual-authoring policy
migration
validation command
template support
release integration
```

Until then, this Markdown file remains the reviewed source for project-known-issue classification.

---

# 107. Template placeholder rules

This template intentionally uses placeholders such as:

```text
<PROJECT_ID>
<ISSUE_ID>
<TITLE>
<STATUS>
<OWNER>
<CONTRACT_IDS>
<RUN_ID_OR_NONE>
```

Rules:

- do not replace placeholders by guessing;
- remove unused example rows;
- active open issues must have concrete values;
- release-ready active projects must not retain unresolved required placeholders;
- placeholder text in this template is not an issue and not evidence.

---

# 108. Definition of issue-triage complete

Triage is complete when:

1. the issue has a stable ID;
2. actual and expected behavior are clear;
3. affected scope is defined;
4. category and severity are assigned;
5. root cause is known or investigation is planned;
6. release impact is assigned;
7. related contracts and evidence are linked;
8. owner and next action are assigned;
9. workaround and risk are documented;
10. exit condition is objective;
11. last review is recorded.

---

# 109. Definition of issue-resolved

An issue is resolved when:

1. its root cause is corrected or final design is documented;
2. direct providers validate;
3. affected consumers validate;
4. downstream entrypoints validate where applicable;
5. affected scenarios pass;
6. golds are reviewed where affected;
7. regression evidence exists;
8. related contracts and documents are updated;
9. coverage and status records agree;
10. the exit condition is satisfied;
11. resolution evidence is retained;
12. release impact is cleared.

---

# 110. Definition of known-issue review complete

A release-level review is complete when:

1. every open issue is triaged;
2. every open issue has current evidence or a stated evidence limitation;
3. every issue has release impact;
4. every blocker is explicit;
5. every accepted issue is approved;
6. every waiver is valid;
7. every fix has regression evidence;
8. every resolved issue has an objective resolution;
9. the status ledger, coverage matrix, contracts, and known issues agree;
10. release notes include required user-facing limitations;
11. issue counts are accurate;
12. the reviewer records the review date and candidate.

---

# 111. Definition of template-complete

This template is complete when:

1. it supports all major project issue domains;
2. placeholders are explicit;
3. no project-specific fact is embedded;
4. severity, status, priority, and release impact are distinct;
5. known issues are separated from implementation status;
6. contracts, coverage, scenarios, golds, and release gates can be cross-referenced;
7. open, accepted, deferred, and resolved records are represented;
8. initialization, migration, review, and closure workflows are explicit;
9. it does not claim project evidence of its own.

---

# 112. Final invariants

The active project's known-issue registry must preserve:

1. one stable ID per issue;
2. no ID reuse;
3. explicit lifecycle status;
4. explicit severity;
5. explicit priority;
6. explicit release impact;
7. explicit acceptance state;
8. clear expected and actual behavior;
9. current evidence;
10. provider and consumer scope;
11. contract linkage where applicable;
12. coverage linkage where applicable;
13. status-ledger linkage for temporary implementation;
14. safe workaround information;
15. objective exit condition;
16. active owner;
17. release review;
18. regression proof for fixes;
19. retained resolution history;
20. no hidden blocker;
21. no issue accepted silently;
22. no gold update used as an unreviewed fix;
23. no stale evidence presented as current;
24. no template placeholder presented as a real issue.

---

# 113. Final rule

> Known issues must make project risk actionable, not merely visible.

Every active issue must state what is wrong or limited, who and what it affects, which contract or claim governs it, what evidence proves it, whether it blocks release, what safe action exists now, and what objective evidence will close it.

Anything less is an observation awaiting triage, not a maintained project issue.
