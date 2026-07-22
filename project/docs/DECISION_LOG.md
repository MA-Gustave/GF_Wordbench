# Albanian Project Decision Log

**Document ID:** `GF-WB-PROJECT-DECISION-LOG`  
**Status:** Normative project decision register  
**Applies to:** The active Albanian GF project in this GF Wordbench repository copy  
**Project ID:** `sqi`  
**Language:** Albanian  
**GF module suffix:** `Sqi`  
**Source root:** `lib/src/albanian`  
**Owner:** Active-project maintainers  
**Identity authority:** `project/project.toml`  
**Contract authority:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Status authority:** `project/docs/STATUS_LEDGER.md`  
**Validation authority:** `project/docs/VALIDATION_SPEC.md`  
**Last consolidated:** 2026-07-22

---

## 1. Purpose

This document records durable decisions for the active Albanian GF project.

It exists to answer:

- what was decided;
- why the decision was needed;
- which alternatives were rejected;
- which files and contracts are affected;
- which evidence validates the decision;
- whether the decision is active, conditional, superseded or still open;
- what must be reviewed before the decision changes.

This file is not a general progress diary.

It records decisions that affect one or more of:

```text
project identity
module ownership
module dependency direction
public GF contracts
lincat shapes
morphology
syntax
entrypoints
checkpoints
scenarios
gold files
release artifacts
linguistic policy
migration policy
release gates
```

The core rule is:

> A project decision is complete only when its implementation, consumers, validation evidence and documentation agree.

---

## 2. Relationship to other project records

This document owns the rationale and history of durable choices.

It does not replace:

| Document | Primary responsibility |
|---|---|
| `project/project.toml` | Current machine-readable project identity and validation configuration |
| `project/docs/INTERFILE_CONTRACT_LOCK.md` | Current provider/consumer contracts and locked invariants |
| `project/docs/LANGUAGE_OVERVIEW.md` | Current project scope and verified language-level overview |
| `project/docs/LANGUAGE_ARCHITECTURE.md` | Current module layers, ownership and entrypoints |
| `project/docs/MODULE_DEPENDENCY_MAP.md` | Current import and dependency relationships |
| `project/docs/CATEGORY_AND_LINCAT_CONTRACT.md` | Current category and lincat structures |
| `project/docs/MORPHOLOGY_SPEC.md` | Current morphological rules |
| `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md` | Current syntax and constructor rules |
| `project/docs/VALIDATION_SPEC.md` | Current required validation behavior |
| `project/docs/TEST_COVERAGE_MATRIX.md` | Mapping from requirements to evidence |
| `project/docs/STATUS_LEDGER.md` | Temporary, fallback, blocked, warning and disabled states |
| `project/docs/KNOWN_ISSUES.md` | Current defects, limitations and release impact |
| `project/docs/RELEASE_CRITERIA.md` | Current release gates |

A decision entry explains why a current rule exists.

The owning specification defines the rule in operational detail.

---

## 3. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless an explicit exception is documented.
- **MAY**: optional.
- **DECISION**: durable choice affecting project behavior or contracts.
- **ACCEPTED**: approved and currently normative.
- **CONDITIONAL**: approved only when stated preconditions apply.
- **PROPOSED**: documented candidate not yet authoritative.
- **OPEN**: required choice whose final resolution is not yet supported by authoritative evidence.
- **DEFERRED**: intentionally postponed with an explicit trigger for reconsideration.
- **SUPERSEDED**: replaced by a later decision.
- **REJECTED**: considered and deliberately not adopted.
- **RETIRED**: no longer active because the governed behavior was removed.
- **BREAKING DECISION**: decision requiring coordinated provider/consumer or project migration.
- **EVIDENCE**: compile result, scenario, gold, artifact, contract review or other proof.
- **OWNER**: maintainer or team accountable for implementing and reviewing a decision.

---

## 4. Decision statuses

Canonical decision statuses:

```text
accepted
conditional
proposed
open
deferred
superseded
rejected
retired
```

Status meanings:

### `accepted`

The decision is active and must be followed.

### `conditional`

The decision is active only when its stated applicability condition is true.

### `proposed`

The decision is under review and must not be treated as current policy.

### `open`

The project requires a decision, but the available authoritative evidence does not yet support one final choice.

### `deferred`

The decision is intentionally postponed until a named trigger occurs.

### `superseded`

A later entry replaces the decision.

### `rejected`

The alternative was evaluated and must not be introduced without reopening the decision.

### `retired`

The decision no longer applies because the relevant feature or contract was removed.

---

## 5. Decision identifiers

Project decision IDs use:

```text
PDEC-<NUMBER>
```

Examples:

```text
PDEC-0001
PDEC-0012
```

Open decisions use the same permanent numbering system.

They do not receive temporary IDs.

A decision ID:

- is unique;
- is never reused;
- remains in the log after supersession or retirement;
- is referenced from contracts and specifications when material;
- does not change when the title is clarified.

---

## 6. Required decision-entry fields

Each entry must contain:

```text
ID
title
status
decision
context
rationale
alternatives
consequences
affected contracts/files
validation evidence
change classification
review triggers
date/consolidation provenance
supersession links when applicable
```

An accepted entry must not contain unresolved required placeholders.

---

## 7. Evidence and provenance policy

This initial consolidation distinguishes:

### Confirmed project facts

Supported by current project locks, configuration schema, source naming or preserved implementation evidence.

### Accepted architectural policy

Already required by the maintained project/framework contract set.

### Open language-project choices

Not sufficiently supported by available authoritative records.

### Historical implementation evidence

Useful for context, but not automatically current policy or current defect status.

The consolidation date is not necessarily the original date on which each idea was first introduced.

Where the original acceptance date is unavailable, the entry records:

```text
Acceptance provenance: established by the active contract set before this consolidation
```

This avoids inventing historical dates.

---

# Accepted decisions

## PDEC-0001 — One active language per repository copy

**Status:** accepted  
**Acceptance provenance:** Established by the active project and framework contract set before this consolidation  
**Last reviewed:** 2026-07-22

### Decision

One GF Wordbench repository copy represents one active language project.

For this repository copy, the active project is Albanian.

### Context

Language-specific source paths, GF module suffixes, scenarios, gold files and release targets must remain coherent.

Supporting multiple simultaneously active language projects in one repository copy would require a different project model and substantially different configuration, artifact and validation contracts.

### Rationale

One active language per copy provides:

- unambiguous project identity;
- one source root;
- one module suffix;
- deterministic scenario selection;
- one set of project golds;
- one release contract;
- simpler migration and reset behavior;
- reduced risk of cross-language contamination.

### Rejected alternatives

#### Multiple active languages selected through GUI state

Rejected because UI state is local and disposable, not project authority.

#### Infer the active language from the selected file

Rejected because one file cannot define project-wide entrypoints, checkpoints, scenarios or release artifacts.

#### Infer the active language from previous run directories

Rejected because generated evidence must not define current project identity.

### Consequences

- Albanian-specific data belongs under `project/`, `project/validation/` and the active language source tree.
- Framework defaults must remain language-neutral.
- A second active language requires a duplicated repository copy or a future explicit project-model change.
- Cross-language migration must remove stale identifiers from active paths, scenarios, golds and project documentation.

### Affected files and contracts

```text
project/project.toml
project/docs/LANGUAGE_OVERVIEW.md
project/docs/INTERFILE_CONTRACT_LOCK.md
PIFC-CONFIG-001
PIFC-CONFIG-002
```

### Validation evidence

```text
project configuration validation
active-language identifier scan
source-root validation
scenario registry validation
```

### Change classification

Changing this decision is a framework- and project-architecture breaking change.

### Review triggers

- proposal for multiple active languages;
- proposal for runtime project switching;
- project configuration redesign;
- repository layout redesign.

---

## PDEC-0002 — `project/project.toml` owns active project identity

**Status:** accepted  
**Acceptance provenance:** Established by the active contract set before this consolidation  
**Last reviewed:** 2026-07-22

### Decision

`project/project.toml` is the authoritative machine-readable source for active project identity and validation configuration.

It must define or resolve:

```text
project ID
display name
language name
language code
module suffix
source root
source glob
entrypoints
checkpoints
required scenarios
optional scenarios
release targets
expected artifacts
GF path components
```

### Context

Historically, local application state and file-path conventions may contain language-specific values.

Those sources are not portable or authoritative.

### Rationale

A committed project-owned configuration:

- is version-controlled;
- is reviewable;
- is usable by CLI and GUI;
- supports non-interactive validation;
- survives machine changes;
- prevents implicit language selection;
- creates one owner for project identity.

### Rejected alternatives

#### GUI state as project authority

Rejected because local convenience state must remain disposable.

#### Filename inference for entrypoints

Rejected because filename shape does not prove role or release status.

#### Framework constants for Albanian paths

Rejected because the reusable framework must not embed active-language assumptions.

### Consequences

- CLI and GUI must consume the same loaded project configuration.
- Relative paths resolve from the project root.
- Required release constraints cannot be bypassed silently by UI state.
- Normal validation does not rewrite `project.toml`.
- Schema migration or initialization may update it explicitly and atomically.

### Affected files and contracts

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_OVERVIEW.md
PIFC-CONFIG-001
PIFC-CONFIG-002
```

### Validation evidence

```text
schema validation
required-field validation
path containment validation
entrypoint existence check
checkpoint registry check
scenario registry check
```

### Change classification

Changing identity ownership is a breaking project/framework contract change.

### Review triggers

- configuration schema major change;
- project-loader redesign;
- introduction of multi-project selection;
- migration of project root semantics.

---

## PDEC-0003 — Albanian identity uses `sqi`, `Sqi` and `lib/src/albanian`

**Status:** accepted  
**Acceptance provenance:** Supported by the project schema example, preserved active-project paths and module-family evidence  
**Last reviewed:** 2026-07-22

### Decision

The active project identity is:

```text
Project ID:       sqi
Language name:    Albanian
Language code:    sqi
GF module suffix: Sqi
Source root:      lib/src/albanian
```

### Context

The maintained source family and preserved project evidence use Albanian paths and modules such as:

```text
CatSqi
MorphoSqi
NounSqi
StructuralSqi
SymbolSqi
ExtendSqi
GrammarSqi
LangSqi
AllSqi
```

### Rationale

The identifier, language code, suffix and source root are already consistent across the available project evidence.

Locking them prevents:

- mixed suffixes;
- stale-language filenames;
- scenario-to-module mismatch;
- inconsistent release artifact naming;
- documentation drift.

### Rejected alternatives

#### Use `Albanian` as the GF suffix

Rejected because the existing active module family uses `Sqi`.

#### Use `alb` as the canonical project code

Not adopted because the supported project evidence uses `sqi`.

#### Infer the source root from the current target file

Rejected because project identity must be configuration-owned.

### Consequences

- New Albanian GF modules use the `Sqi` suffix unless a coordinated migration changes it.
- Project scenarios and documentation must use the same suffix.
- Historical names may remain only in migration records or archived evidence.
- Renaming the project ID, code, suffix or source root requires atomic project migration.

### Affected files and contracts

```text
project/project.toml
project/docs/LANGUAGE_OVERVIEW.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/validation/
lib/src/albanian/
PIFC-CONFIG-001
PIFC-CONFIG-002
```

### Validation evidence

```text
source-directory existence
module suffix scan
scenario module-name scan
gold identity scan
documentation identifier scan
```

### Change classification

Breaking project migration.

### Review triggers

- upstream module-family rename;
- source-tree relocation;
- language-code policy change;
- repository duplication/reset.

---

## PDEC-0004 — GF remains the authoritative execution engine

**Status:** accepted  
**Acceptance provenance:** Established by the framework architecture and project validation contracts  
**Last reviewed:** 2026-07-22

### Decision

Native GF execution is authoritative for:

- source parsing;
- type checking;
- module loading;
- concrete syntax validation;
- parsing;
- linearization;
- morphology execution;
- generation;
- missing-function inspection;
- `.gfo` production;
- `.pgf` production.

GF Wordbench orchestrates and interprets evidence but does not reimplement GF semantics.

### Context

Static analysis is useful for fast supplementary findings, but it cannot prove native GF correctness.

### Rationale

Keeping GF authoritative:

- avoids divergent semantic reimplementations;
- preserves compatibility with real GF behavior;
- provides native diagnostics;
- produces real GF artifacts;
- allows exact scenario validation.

### Rejected alternatives

#### Treat static scanning as sufficient validation

Rejected because scanners cannot replace GF parsing, typing or execution.

#### Reimplement Albanian morphology in Python for validation

Rejected because it would create a competing language engine.

#### Infer success from artifact existence alone

Rejected because stale artifacts may exist and process diagnostics matter.

### Consequences

- Every external invocation must follow the GF external-tool contract.
- Raw `stdout` and `stderr` are preserved separately.
- Static findings remain supplementary.
- Release evidence requires native GF execution where configured.
- `.gfo` and `.pgf` artifacts are trusted only when proven current.

### Affected files and contracts

```text
project/docs/VALIDATION_SPEC.md
project/docs/RELEASE_CRITERIA.md
project/validation/scenarios/
PIFC-ARTIFACT-001
PIFC-ARTIFACT-002
PIFC-RELEASE-001
```

### Validation evidence

```text
native compile tests
native scenario runs
GF version capture
artifact freshness checks
PGF build verification
```

### Change classification

Breaking architecture change.

### Review triggers

- proposal for a non-GF execution backend;
- introduction of a semantic cache;
- proposal to skip native compilation in release mode.

---

## PDEC-0005 — Static scanning remains supplementary

**Status:** accepted  
**Acceptance provenance:** Established by framework validation separation  
**Last reviewed:** 2026-07-22

### Decision

Static scanning may detect source-text risks, but scan findings do not replace native GF compilation or scenario execution.

### Context

Heuristic scanning can identify patterns such as suspicious syntax, untyped string-based constructs or formatting defects.

A text match alone cannot determine the exact GF semantic failure class.

### Rationale

Separation prevents:

- false type/syntax claims;
- duplicated compiler behavior;
- scan rules becoming hidden release semantics;
- scanner output being treated as native proof.

### Rejected alternatives

#### Map every scan finding directly to `TYPE` or `SYNTAX`

Rejected because the relationship is not generally reliable.

#### Skip GF compilation when scans are clean

Rejected because absence of scan findings does not prove correctness.

### Consequences

- Scan rules use stable IDs.
- Findings preserve source locations.
- Reports distinguish scan evidence from native diagnostics.
- Release criteria may require clean scan categories, but native validation still runs.

### Affected files and contracts

```text
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
```

### Validation evidence

```text
scanner unit fixtures
native GF comparison fixtures
release-mode integration tests
```

### Change classification

Compatible only when native authority remains unchanged.

### Review triggers

- new authoritative scan gate;
- scanner rewrite;
- proposal to bypass GF based on scan results.

---

## PDEC-0006 — Public project responsibilities have one authoritative provider

**Status:** accepted  
**Acceptance provenance:** Established by the project interfile contract lock  
**Last reviewed:** 2026-07-22

### Decision

Each public project responsibility has one authoritative provider unless an explicit deterministic selection rule is documented.

Responsibilities include:

```text
category/lincat definitions
noun morphology
verb morphology
adjective morphology
paradigms
structural vocabulary
shared helpers
extension families
grammar entrypoint
language/API entrypoint
release entrypoint
scenario identity
gold file
release artifact name
```

### Context

Duplicate helpers or parallel partial providers can compile locally while producing project-wide ambiguity.

### Rationale

Single ownership:

- makes consumer relationships reviewable;
- prevents hidden divergence;
- simplifies fixes;
- supports dependency classification;
- stabilizes public names.

### Rejected alternatives

#### Duplicate helpers wherever convenient

Rejected because fixes and behavior drift across copies.

#### Let consumers reconstruct structural entries

Rejected when a canonical provider exists.

#### Treat module-internal convenience as public automatically

Rejected because public contracts must be intentional.

### Consequences

- Every consumer depends only on documented public surfaces.
- Duplicate providers require a selection rule and tests.
- Moving ownership is a breaking contract change.
- The dependency map and contract lock must name the owner.

### Affected files and contracts

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/INTERFILE_CONTRACT_LOCK.md
PIFC-MODULE-*
PIFC-LINCAT-*
PIFC-HELPER-*
```

### Validation evidence

```text
import inventory
public helper registry
duplicate-provider check
checkpoint compilation
consumer compilation
```

### Change classification

Provider relocation or public-surface change is breaking unless all consumers remain compatible.

### Review triggers

- helper duplication;
- module split/merge;
- lincat owner change;
- entrypoint change.

---

## PDEC-0007 — Dependency direction follows linguistic architecture

**Status:** accepted  
**Acceptance provenance:** Established by the project contract set  
**Last reviewed:** 2026-07-22

### Decision

The expected dependency direction is:

```text
low-level morphology and resources
    → categories and syntax resources
    → paradigms and lexicon
    → syntax and structural modules
    → extension providers/coordinator
    → grammar and language/API entrypoints
    → release PGF
```

Lower-level modules must not import top-level entrypoints for convenience.

Circular imports are prohibited.

### Context

Top-level entrypoints aggregate lower layers.

Reversing the dependency direction creates cycles, hidden coupling and difficult downstream-failure analysis.

### Rationale

A layered direction:

- supports checkpoint ordering;
- clarifies failure causality;
- keeps low-level providers reusable;
- prevents orchestration concerns from entering resources;
- makes module migration reviewable.

### Rejected alternatives

#### Allow arbitrary imports when GF compiles

Rejected because successful compilation does not prove maintainable ownership.

#### Import a top-level grammar to reuse one helper

Rejected because the helper belongs in a lower authoritative provider.

### Consequences

- Exceptions require a decision-log entry and contract update.
- The module dependency map must match source imports.
- Checkpoints follow dependency order.
- Downstream failures may reference failed lower providers.

### Affected files and contracts

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/INTERFILE_CONTRACT_LOCK.md
PIFC-MODULE-001 through PIFC-MODULE-007
PIFC-RELEASE-001
```

### Validation evidence

```text
import graph
cycle check
checkpoint compilation
entrypoint compilation
```

### Change classification

Breaking when a provider/consumer direction changes.

### Review triggers

- new extension layer;
- module reorganization;
- interface/instance introduction;
- import cycle.

---

## PDEC-0008 — Structured lincats must not be flattened silently

**Status:** accepted  
**Acceptance provenance:** Established by project contract invariants  
**Last reviewed:** 2026-07-22

### Decision

Structured GF values such as:

```text
NP
AP
CN
VP
Cl
Prep
Pron
```

and Albanian-specific records must not be flattened to `Str` merely to make a local implementation compile.

Any intentional flattening that affects consumers requires an explicit architecture decision and coordinated migration.

### Context

A fallback `{s : Str}` may hide lost agreement, case, definiteness, polarity, complement or ordering information.

### Rationale

Preserving structure protects:

- morphology/syntax composition;
- agreement;
- downstream constructors;
- parse/linearization behavior;
- future extension;
- explicit incomplete-state reporting.

### Rejected alternatives

#### Replace an incomplete lincat with `{s : Str}` and call it final

Rejected because it can conceal missing semantic structure.

#### Let each consumer infer missing fields

Rejected because field ownership belongs to the provider.

### Consequences

- Shared fields are documented in `CATEGORY_AND_LINCAT_CONTRACT.md`.
- Adding mandatory fields requires constructor updates.
- Field removal or rename is breaking.
- Temporary flattening must appear in the status ledger.
- Scenario/gold evidence must cover affected behavior.

### Affected files and contracts

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/STATUS_LEDGER.md
project/docs/INTERFILE_CONTRACT_LOCK.md
PIFC-LINCAT-001
PIFC-LINCAT-002
```

### Validation evidence

```text
consumer compilation
missing-function inspection
representative linearization
parse scenarios
lincat contract review
```

### Change classification

Breaking when a consumer-visible shape changes.

### Review triggers

- new lincat field;
- field removal/rename;
- fallback record;
- GF default-lincat warning.

---

## PDEC-0009 — Checkpoints precede final entrypoint validation

**Status:** accepted  
**Acceptance provenance:** Established by active release contracts  
**Last reviewed:** 2026-07-22

### Decision

Required checkpoint modules must compile in configured dependency order before final entrypoint validation and release build.

### Context

A final entrypoint may fail because a lower provider already failed.

Running only the final module obscures ownership and creates noisy downstream evidence.

### Rationale

Checkpoints:

- localize failures;
- prove layer coherence;
- support direct/downstream classification;
- provide progress evidence;
- prevent omitted lower layers from being mistaken for success.

### Rejected alternatives

#### Compile only the final entrypoint

Rejected because lower-layer failures become harder to attribute.

#### Alphabetically order checkpoints

Rejected because semantic dependency order is authoritative.

#### Skip a required checkpoint when the entrypoint happens to compile

Rejected unless an explicit release exception is approved.

### Consequences

- `project.toml` stores deterministic checkpoint order.
- Release validation compiles every required checkpoint.
- Downstream checkpoint failures are not reported as independent roots.
- Skips remain explicit.

### Affected files and contracts

```text
project/project.toml
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/VALIDATION_SPEC.md
PIFC-RELEASE-001
```

### Validation evidence

```text
checkpoint-mode run
release-mode run
dependency-order test
downstream-classification test
```

### Change classification

Changing requiredness or order is contract-significant and may be breaking.

### Review triggers

- module layer added/removed;
- entrypoint changed;
- recurring downstream diagnostic;
- checkpoint performance proposal.

---

## PDEC-0010 — Project scenarios use native `.gfs` execution

**Status:** accepted  
**Acceptance provenance:** Established by project scenario contracts and framework ADR set  
**Last reviewed:** 2026-07-22

### Decision

Project scenarios are native GF shell scripts stored under:

```text
project/validation/scenarios/
```

Each registered scenario is executed as a bounded GF process invocation.

### Context

Project behavior often requires sequences of GF commands that should be exercised by GF itself.

### Rationale

Native `.gfs` scenarios:

- preserve GF command semantics;
- support loading, parsing, linearization and inspection;
- produce raw evidence;
- remain project-owned;
- allow exact marked output sections.

### Rejected alternatives

#### Reimplement scenario commands in Python

Rejected because it would duplicate GF behavior.

#### Use unregistered ad hoc scripts as release evidence

Rejected because release validation must be reproducible.

#### Let a scenario choose an undocumented project

Rejected because one repository copy already has one active project.

### Consequences

- Scenario IDs are unique and registered.
- Required and optional scenarios remain distinct.
- Scripts load documented entrypoints.
- Scripts terminate under bounded policy.
- External input files are project-owned and version-controlled.
- Unsupported commands are non-success.

### Affected files and contracts

```text
project/project.toml
project/validation/scenarios/
project/validation/inputs/
project/docs/VALIDATION_SPEC.md
PIFC-SCENARIO-001
PIFC-SCENARIO-002
PIFC-SCENARIO-003
```

### Validation evidence

```text
scenario registry check
real-GF scenario execution
timeout/cancellation tests
entrypoint-load evidence
```

### Change classification

Changing scenario identity, entrypoint or command semantics is a coordinated project contract change.

### Review triggers

- new scenario;
- scenario rename;
- external input addition;
- GF command compatibility change.

---

## PDEC-0011 — Scenario output uses stable section markers

**Status:** accepted  
**Acceptance provenance:** Established by the active project scenario contract  
**Last reviewed:** 2026-07-22

### Decision

Scenario output sections use stable GF Wordbench markers:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
GF_WORDBENCH_END <scenario-id>:<section-id>
```

### Context

GF shell output may contain prompts, banners, diagnostics and multiple command results.

Stable markers identify the exact project-owned comparison regions.

### Rationale

Markers provide:

- unambiguous section identity;
- deterministic extraction;
- missing-section detection;
- stable gold relationships;
- separation from incidental GF output.

### Rejected alternatives

#### Infer sections from blank lines

Rejected because formatting is not a reliable contract.

#### Search for one expected phrase

Rejected because it may ignore extra or missing output.

#### Treat missing end markers as partial success

Rejected because incomplete evidence is not exact scenario evidence.

### Consequences

- Section IDs are unique within a scenario.
- Begin and end markers must pair.
- Marker text is locale-independent.
- Normalization preserves marker identity.
- Missing markers produce scenario `ERROR`, not `OK`.

### Affected files and contracts

```text
project/validation/scenarios/
project/validation/gold/
PIFC-SCENARIO-004
PIFC-GOLD-001
```

### Validation evidence

```text
marker parser tests
missing-marker fixtures
duplicate-marker fixtures
real-GF scenario transcript
```

### Change classification

Marker-format change is a scenario/normalization/gold contract change.

### Review triggers

- scenario format major change;
- normalization profile redesign;
- multiple output channels.

---

## PDEC-0012 — Gold files are reviewed project assets

**Status:** accepted  
**Acceptance provenance:** Established by active gold contracts and golden-output architecture  
**Last reviewed:** 2026-07-22

### Decision

Gold files under:

```text
project/validation/gold/
```

represent reviewed accepted normalized Albanian scenario output.

They are project assets, not generated run artifacts.

### Context

Exact linguistic output must be compared against an independent accepted value.

### Rationale

Project-owned golds:

- make regressions reviewable;
- preserve language-specific expectations outside framework code;
- support deterministic release gates;
- keep acceptance separate from current implementation output.

### Rejected alternatives

#### Store expected Albanian output in framework Python tests

Rejected because active-language behavior belongs to the project.

#### Store expected output in run directories

Rejected because run directories are generated evidence and subject to retention.

#### Use current output as expected output automatically

Rejected because defects would become accepted behavior.

### Consequences

- Each required gold-backed scenario identifies one gold.
- Gold schema, scenario ID and normalization profile remain compatible.
- Missing required gold is non-success.
- Gold changes are version-controlled.
- Framework normalization fixtures remain separate from Albanian golds.

### Affected files and contracts

```text
project/validation/gold/
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
PIFC-GOLD-001
```

### Validation evidence

```text
gold discovery check
schema validation
scenario-to-gold mapping
exact comparison
release gate
```

### Change classification

Changing accepted semantic output is a project behavior change requiring review.

### Review triggers

- linguistic correction;
- scenario change;
- GF version change;
- normalization profile major change;
- entrypoint change.

---

## PDEC-0013 — Normal validation never updates gold files

**Status:** accepted  
**Acceptance provenance:** Established by active project and framework contracts  
**Last reviewed:** 2026-07-22

### Decision

A normal `quick`, `checkpoint`, `release` or `diagnostic` validation run must not create, replace or rewrite project gold files.

Gold updates occur only through a separate explicit reviewed operation.

### Context

Validation cannot remain trustworthy if it mutates the expected result it is checking.

### Rationale

Read-only normal validation:

- prevents accidental regression acceptance;
- keeps CI safe;
- preserves independent expectations;
- makes changes visible in version control;
- separates validation from project mutation.

### Rejected alternatives

#### Automatically update on mismatch

Rejected because a mismatch may be a defect.

#### Update golds in release mode after successful GF execution

Rejected because execution success does not prove linguistic correctness.

#### Let the GUI silently accept output

Rejected because CLI and GUI must follow the same project contract.

### Consequences

A gold update requires:

```text
intentional implementation/specification change
complete raw evidence
successful normalization
old/new review
deterministic diff
linguistic or architectural rationale
atomic replacement
documentation review
```

A gold file must not be changed merely to make a failing scenario pass.

### Affected files and contracts

```text
project/validation/gold/
project/docs/VALIDATION_SPEC.md
project/docs/INTERFILE_CONTRACT_LOCK.md
PIFC-GOLD-002
```

### Validation evidence

```text
before/after gold hash in normal audit
explicit update integration test
atomic-write failure test
release mismatch test
```

### Change classification

Breaking validation-integrity change.

### Review triggers

- automated gold proposal workflow;
- bulk update support;
- GUI gold-review feature.

---

## PDEC-0014 — Raw evidence is preserved before interpretation

**Status:** accepted  
**Acceptance provenance:** Established by the framework artifact and external-tool contracts  
**Last reviewed:** 2026-07-22

### Decision

Raw GF `stdout` and `stderr` are captured separately and preserved before diagnostic parsing, normalization, classification or reporting.

### Context

Derived results may be wrong or incomplete.

Raw evidence is required to verify interpretation and investigate new GF output.

### Rationale

Preservation enables:

- diagnostic review;
- parser improvement;
- GF-version comparison;
- timeout analysis;
- gold-update review;
- audit reproducibility.

### Rejected alternatives

#### Merge `stdout` and `stderr` before capture

Rejected because stream provenance is lost.

#### Keep only normalized output

Rejected because normalization intentionally changes non-semantic text.

#### Reconstruct raw logs from reports

Rejected because reports are projections.

### Consequences

- Raw files are immutable after capture.
- Normalized output is derived.
- Reports reference evidence but do not replace it.
- Timeout/cancelled output remains partial and untrusted for exact success.
- Parser/classifier behavior can be audited against source evidence.

### Affected files and contracts

```text
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/validation/
PIFC-ARTIFACT-003
```

### Validation evidence

```text
separate capture paths
raw hash/integrity check
parser fixture provenance
scenario result evidence paths
```

### Change classification

Breaking evidence-model change.

### Review triggers

- streaming redesign;
- output-size limits;
- redacted export support;
- remote execution.

---

## PDEC-0015 — Normalization removes execution instability, not Albanian meaning

**Status:** accepted  
**Acceptance provenance:** Established by project gold contracts and normalization policy  
**Last reviewed:** 2026-07-22

### Decision

Scenario-output normalization may remove or replace only approved execution instability.

It must preserve Albanian linguistic and GF-semantic content.

### Allowed examples

```text
absolute project paths
run-directory paths
temporary paths
timestamps
durations
known prompts
terminal control sequences
compatible non-semantic banners
```

### Prohibited examples

```text
case-folding Albanian output
removing diacritics
transliteration
spelling correction
punctuation repair
variant deduplication without policy
tree reordering without policy
removal of missing-function output
removal of unknown diagnostics
```

### Context

Gold comparison needs reproducibility across machines while remaining sensitive to real regressions.

### Rationale

A conservative boundary prevents both false mismatches and hidden semantic changes.

### Rejected alternatives

#### Broad regular-expression deletion

Rejected because it can remove meaningful output.

#### Comparator-specific cleanup

Rejected because normalization must have one owner and one version.

#### Unicode compatibility folding by default

Rejected because code-point distinctions may be meaningful.

### Consequences

- Normalization profiles are versioned.
- Profile-major changes trigger affected-gold review.
- Unknown output is preserved and surfaced.
- The comparator performs no hidden semantic normalization.
- Project orthographic policy remains separate from execution normalization.

### Affected files and contracts

```text
project/validation/gold/
project/validation/scenarios/
project/docs/VALIDATION_SPEC.md
PIFC-GOLD-001
PIFC-GOLD-002
```

### Validation evidence

```text
normalization fixture corpus
idempotence test
Unicode preservation test
gold comparison fixtures
unknown-output test
```

### Change classification

Output-changing normalization is a breaking profile/project comparison change.

### Review triggers

- GF output format change;
- cross-platform mismatch;
- Unicode policy proposal;
- new normalization rule.

---

## PDEC-0016 — Incomplete states remain explicit

**Status:** accepted  
**Acceptance provenance:** Established by project contract/status policy  
**Last reviewed:** 2026-07-22

### Decision

Incomplete implementation states are explicitly classified and recorded.

Canonical project maturity labels include:

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

### Context

The source family includes an explicitly named scaffolding module:

```text
ExtendSqiScaffolding
```

Historical evidence also contains incomplete/default behavior.

A compiling placeholder must not be confused with stable language support.

### Rationale

Explicit states:

- prevent false completion claims;
- make release impact visible;
- preserve next actions;
- distinguish temporary compromises;
- guide scenario and coverage requirements.

### Rejected alternatives

#### Rely only on source comments

Rejected because comments are difficult to aggregate and may drift.

#### Treat every compiling module as stable

Rejected because compile success does not prove complete behavior.

#### Hide fallback behavior from release reports

Rejected because accepted limitations must be explicit.

### Consequences

- `STATUS_LEDGER.md` records every temporary/fallback/blocked/disabled implementation.
- Entries state owner, reason, impact, evidence and exit condition.
- Source comments and ledger entries must agree.
- Release-blocking states cannot be ignored silently.
- Scaffolding cannot be presented as final without a later decision.

### Affected files and contracts

```text
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA.md
project/docs/INTERFILE_CONTRACT_LOCK.md
PIFC-DOC-004
PIFC-RELEASE-003
```

### Validation evidence

```text
status-ledger scan
scaffolding-name scan
release blocker check
documentation/source consistency review
```

### Change classification

Changing an item from incomplete to stable requires evidence; changing the status vocabulary is contract-significant.

### Review triggers

- new scaffold/fallback;
- completion of extension work;
- release preparation;
- accepted limitation.

---

## PDEC-0017 — Required scenarios and known issues determine release eligibility

**Status:** accepted  
**Acceptance provenance:** Established by active release contracts  
**Last reviewed:** 2026-07-22

### Decision

Release eligibility requires:

- every required checkpoint to pass;
- every required scenario to pass;
- every required gold comparison to match;
- scenario execution errors to remain distinct from semantic failures;
- accepted known issues to be explicit;
- every issue to state release-blocking impact;
- required functions not to remain blocked or disabled unless release policy explicitly permits it.

### Context

A release cannot be based on one successful top-level compile while lower layers, scenarios or accepted limitations remain unresolved.

### Rationale

This decision creates auditable release gates and prevents silent exceptions.

### Rejected alternatives

#### Allow optional scenario warnings to disappear

Rejected; optional results remain visible.

#### Treat missing scenarios as skipped success

Rejected; a missing required scenario is a release failure.

#### Ignore undocumented warnings

Rejected; release exceptions must be deliberate.

### Consequences

- The validation specification owns requiredness.
- The coverage matrix maps every criterion to evidence.
- Known issues and status ledger participate in release review.
- Gold mismatch blocks release until the implementation is fixed or the gold is deliberately reviewed and updated.

### Affected files and contracts

```text
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/KNOWN_ISSUES.md
project/docs/STATUS_LEDGER.md
project/docs/RELEASE_CRITERIA.md
PIFC-RELEASE-001
PIFC-RELEASE-002
PIFC-RELEASE-003
```

### Validation evidence

```text
release-mode audit
required scenario totals
gold comparison results
known-issue blocker review
manifest verification
```

### Change classification

Weakening a required release gate is a breaking project policy change.

### Review triggers

- release preparation;
- scenario requiredness change;
- accepted known issue;
- new final artifact.

---

## PDEC-0018 — Entrypoints and release artifacts are configured, not inferred

**Status:** accepted  
**Acceptance provenance:** Established by project configuration and entrypoint contracts  
**Last reviewed:** 2026-07-22

### Decision

The grammar, language/API and release entrypoints, plus the expected PGF artifact name, must be configured and documented explicitly.

They must not be inferred from:

- filename ordering;
- presence of `GrammarSqi`, `LangSqi` or `AllSqi`;
- the most recently compiled file;
- GUI state;
- existing `.gfo` or `.pgf` files.

### Context

The active module family contains several plausible top-level modules.

Their names alone do not establish their exact release roles.

### Rationale

Explicit configuration:

- prevents different tools choosing different entrypoints;
- stabilizes scenarios;
- makes the PGF contract reviewable;
- prevents stale artifact acceptance;
- supports repository migration.

### Rejected alternatives

#### Always select `AllSqi`

Not accepted because available evidence does not prove it is the final release entrypoint.

#### Always select `LangSqi`

Not accepted for the same reason.

#### Select whichever top-level module compiles

Rejected because compilation alone does not define public release intent.

### Consequences

- `project.toml` owns entrypoint lists and release target.
- Scenario scripts load the documented entrypoint.
- PGF builder targets the configured release module.
- Artifact name mismatch is non-success.
- Entry changes require scenario, gold, documentation and release review.

### Affected files and contracts

```text
project/project.toml
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/VALIDATION_SPEC.md
project/docs/RELEASE_CRITERIA.md
PIFC-ENTRY-001
PIFC-ENTRY-002
PIFC-ENTRY-003
PIFC-ARTIFACT-002
```

### Validation evidence

```text
entrypoint existence
scenario-to-entrypoint check
clean compile
PGF current-artifact verification
manifest role and hash
```

### Change classification

Entrypoint or release-artifact identity change is breaking unless explicitly compatible.

### Review triggers

- final release target selection;
- entrypoint rename;
- API split;
- PGF naming change.

---

## PDEC-0019 — Historical diagnostics do not define current status

**Status:** accepted  
**Acceptance provenance:** Established during this decision-log consolidation to preserve evidence semantics  
**Last reviewed:** 2026-07-22

### Decision

Historical audit evidence may inform investigation and regression tests, but it does not by itself define the current status of an Albanian module.

Current status comes from:

```text
current source
current project configuration
current contract lock
current status ledger
current known issues
current GF Wordbench validation evidence
```

### Context

Preserved audit fixtures and historical logs reference failures involving modules such as:

```text
CatSqi
GrammarSqi
LangSqi
AllSqi
NounSqi
StructuralSqi
```

Those records may represent older implementations, test fixtures or already resolved defects.

### Rationale

Separating historical evidence from current status prevents:

- resolved defects being reported as active;
- old defaults becoming current policy;
- fixture text becoming project truth;
- outdated entrypoint assumptions.

### Rejected alternatives

#### Copy every historical error into `KNOWN_ISSUES.md`

Rejected unless current validation reproduces or confirms the issue.

#### Ignore historical diagnostics entirely

Rejected because they are useful for regression tests and risk review.

### Consequences

- Historical errors may motivate tests.
- Current issue entries require current evidence or explicit unresolved provenance.
- The decision log may cite historical context without declaring current failure.
- Release review uses current run evidence.

### Affected files and contracts

```text
project/docs/KNOWN_ISSUES.md
project/docs/STATUS_LEDGER.md
project/docs/TEST_COVERAGE_MATRIX.md
```

### Validation evidence

```text
current reproduction
current compile/scenario result
regression fixture linkage
issue evidence field
```

### Change classification

Compatible evidence-governance rule.

### Review triggers

- migration of old project evidence;
- regression-test creation;
- release issue triage.

---

# Open decisions

## PDEC-0020 — Select the primary Albanian variety

**Status:** open  
**Opened:** 2026-07-22  
**Owner:** Active-project linguistic maintainers

### Required decision

Define the primary target variety of Albanian.

The final entry must state:

```text
primary variety
standardization source
accepted regional variants
excluded variants
input policy
canonical output policy
gold policy for variants
```

### Context

The available authoritative project records confirm Albanian identity but do not establish a reviewed dialect/variety target.

### Candidate approaches

#### One documented standard variety

Advantages:

- deterministic canonical output;
- simpler gold policy;
- clearer lexicon and morphology rules.

Risks:

- regional forms require explicit variant policy.

#### Standard variety with accepted input variants

Advantages:

- broader input support;
- canonical output remains stable.

Risks:

- parser and lexicon ambiguity require careful validation.

#### Multiple equal output varieties

Advantages:

- broader representation.

Risks:

- substantially more complex gold, ordering and release contracts.

### Decision criteria

- linguistic authority;
- existing module behavior;
- user requirements;
- RGL compatibility;
- deterministic testing;
- maintenance capacity.

### Blocking impact

Release policy cannot claim a complete language target while this decision remains unresolved.

### Required updates when resolved

```text
LANGUAGE_OVERVIEW.md
MORPHOLOGY_SPEC.md
SYNTAX_AND_CONSTRUCTOR_RULES.md
VALIDATION_SPEC.md
RESEARCH_EVIDENCE.md
project.toml when configuration fields are introduced
relevant scenarios and golds
```

---

## PDEC-0021 — Define canonical Albanian orthography and Unicode policy

**Status:** open  
**Opened:** 2026-07-22  
**Owner:** Active-project linguistic maintainers

### Required decision

Define:

```text
canonical spelling source
character inventory
Unicode normalization policy
capitalization
punctuation
apostrophe and hyphen behavior where applicable
accepted input variants
canonical output form
nonstandard/historical spelling policy
```

### Context

Normalization policy explicitly forbids silently repairing linguistic output.

Therefore the project itself must define canonical orthographic behavior.

### Candidate approaches

#### Preserve exact source code points

Strongest evidence preservation, but equivalent Unicode sequences may remain distinct.

#### Require NFC in project-owned lexical/input assets

Potentially simpler canonical data, but requires explicit migration and validation.

#### Accept multiple input forms and emit one canonical output

Useful for parsing, but requires tested normalization at the linguistic/project layer, not hidden execution-output normalization.

### Decision criteria

- Albanian orthographic standards;
- GF string behavior;
- Unicode reproducibility;
- source migration cost;
- parsing requirements;
- gold stability.

### Blocking impact

Release golds and lexical policy remain incomplete without an explicit decision.

### Required updates when resolved

```text
LANGUAGE_OVERVIEW.md
MORPHOLOGY_SPEC.md
SYNTAX_AND_CONSTRUCTOR_RULES.md
RESEARCH_EVIDENCE.md
VALIDATION_SPEC.md
input and gold assets
```

---

## PDEC-0022 — Select the canonical grammar, language/API and release entrypoints

**Status:** open  
**Opened:** 2026-07-22  
**Owner:** Active-project architecture maintainers

### Required decision

Assign explicit roles to the high-level Albanian modules.

Available evidence includes candidates:

```text
GrammarSqi
LangSqi
AllSqi
```

The final decision must identify:

```text
grammar entrypoint
language entrypoint
API/syntax entrypoint or not applicable
release/PGF entrypoint
checkpoint-only top-level modules
compatibility wrappers
```

### Context

PDEC-0018 requires configuration rather than inference.

The current available records do not prove the final role of each candidate.

### Decision criteria

- actual imports;
- complete concrete-language inclusion;
- required public functions;
- scenario load behavior;
- missing-function result;
- PGF contents;
- downstream consumers;
- compatibility with RGL conventions.

### Blocking impact

Final release PGF identity cannot be considered locked while this decision is open.

### Required evidence

```text
module dependency map
clean checkpoint compilation
entrypoint load scenario
missing-function inspection
PGF build and inspection
consumer review
```

### Required updates when resolved

```text
project/project.toml
LANGUAGE_ARCHITECTURE.md
MODULE_DEPENDENCY_MAP.md
INTERFILE_CONTRACT_LOCK.md
VALIDATION_SPEC.md
RELEASE_CRITERIA.md
scenario scripts
gold files when output changes
```

---

## PDEC-0023 — Define the expected PGF artifact name and contents

**Status:** open  
**Opened:** 2026-07-22  
**Owner:** Active-project release maintainers

### Required decision

Define:

```text
expected PGF filename
producing entrypoint
required concrete language
required public functions
artifact output location
artifact verification method
publication name
```

### Context

The release contracts require both process success and current artifact existence.

The available records do not establish one final expected PGF name.

### Candidate approaches

- name derived from a stable project release target;
- explicit fixed artifact name in project configuration;
- versioned publication copy derived from a fixed internal artifact.

### Decision criteria

- GF output behavior;
- consumer compatibility;
- artifact manifest semantics;
- project versioning;
- publication workflow.

### Blocking impact

Release artifact verification remains incomplete.

### Required updates when resolved

```text
project/project.toml
LANGUAGE_ARCHITECTURE.md
INTERFILE_CONTRACT_LOCK.md
VALIDATION_SPEC.md
RELEASE_CRITERIA.md
release documentation
```

---

## PDEC-0024 — Finalize required and optional scenario registry

**Status:** open  
**Opened:** 2026-07-22  
**Owner:** Active-project validation maintainers

### Required decision

Finalize the active registry and requiredness of scenarios such as:

```text
load
missing
linearize
parse
morphology
generation
```

The list above is a candidate coverage set, not an activation declaration.

### Required fields per scenario

```text
scenario ID
script path
loaded entrypoint
required or optional
validation modes
input assets
section IDs
assertion strategy
gold path/profile when applicable
timeout/output bounds
release impact
```

### Decision criteria

- project release requirements;
- language coverage;
- deterministic behavior;
- runtime cost;
- GF compatibility;
- maintenance capacity.

### Blocking impact

Release validation cannot be considered complete until required scenarios are explicit.

### Required updates when resolved

```text
project/project.toml
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
INTERFILE_CONTRACT_LOCK.md
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

---

## PDEC-0025 — Define missing-function acceptance policy

**Status:** open  
**Opened:** 2026-07-22  
**Owner:** Active-project architecture and release maintainers

### Required decision

Define whether release requires:

```text
zero missing functions
zero missing functions in selected public entrypoints
an explicit allowlist
different criteria for experimental modules
```

### Context

Missing-function inspection is a required validation domain, but the available project records do not define the exact Albanian acceptance threshold.

### Candidate approaches

#### Zero missing functions for the release entrypoint

Strong release completeness; may require retiring incomplete modules from the release surface.

#### Explicit allowlist for documented non-release functions

Supports staged work; requires precise scope and status-ledger entries.

#### Separate stable and experimental entrypoints

Allows incomplete experimental work without weakening the stable release contract.

### Decision criteria

- intended RGL coverage;
- public API;
- extension maturity;
- project version;
- consumer needs;
- release scope.

### Blocking impact

A release-completeness claim is not valid without this policy.

### Required updates when resolved

```text
LANGUAGE_OVERVIEW.md
LANGUAGE_ARCHITECTURE.md
STATUS_LEDGER.md
VALIDATION_SPEC.md
RELEASE_CRITERIA.md
missing scenario and gold/assertions
```

---

## PDEC-0026 — Define the retirement path for `ExtendSqiScaffolding`

**Status:** open  
**Opened:** 2026-07-22  
**Owner:** Albanian extension-layer maintainers

### Required decision

Determine whether `ExtendSqiScaffolding` will be:

```text
completed and renamed/promoted
kept as explicit experimental scaffolding
replaced by `ExtendSqi`
split into dedicated providers
retired and removed
```

### Context

The name explicitly represents scaffolding.

PDEC-0016 prohibits presenting scaffolding as stable implementation without evidence.

### Decision criteria

- actual consumers;
- provided functions;
- overlap with `ExtendSqi`;
- compile status;
- missing functions;
- scenario coverage;
- public release surface.

### Blocking impact

Release impact depends on whether the module is required by configured entrypoints.

The status ledger must state that relationship.

### Required updates when resolved

```text
LANGUAGE_ARCHITECTURE.md
MODULE_DEPENDENCY_MAP.md
INTERFILE_CONTRACT_LOCK.md
STATUS_LEDGER.md
KNOWN_ISSUES.md
VALIDATION_SPEC.md
source imports and scenarios
```

---

## PDEC-0027 — Define supported GF versions for the Albanian project

**Status:** open  
**Opened:** 2026-07-22  
**Owner:** Project toolchain maintainers

### Required decision

Define:

```text
tested GF versions
supported GF versions
unsupported versions
platform matrix
known diagnostic differences
normalization/profile compatibility
PGF compatibility expectations
```

### Context

Historical local evidence references GF 3.12 on Windows, but one historical machine path is not a support policy.

### Candidate approaches

- one exact supported GF version;
- bounded compatible version range;
- one stable version plus experimental newer versions.

### Decision criteria

- compile fixtures;
- scenario behavior;
- diagnostic parser compatibility;
- normalization stability;
- PGF output;
- platform availability.

### Blocking impact

Release reproducibility is incomplete without a tested compatibility declaration.

### Required updates when resolved

```text
project/project.toml
LANGUAGE_OVERVIEW.md
VALIDATION_SPEC.md
RELEASE_CRITERIA.md
framework GF compatibility matrix
CI/integration test matrix
```

---

## PDEC-0028 — Define Albanian linguistic research authorities

**Status:** open  
**Opened:** 2026-07-22  
**Owner:** Active-project linguistic maintainers

### Required decision

Select and rank the authorities used to resolve linguistic ambiguity.

The final policy should distinguish:

```text
normative grammar references
orthographic standards
lexicographic sources
corpora
RGL precedent
maintainer judgment
test examples
```

### Context

The project must not encode unexplained linguistic choices.

### Decision criteria

- authority and reliability;
- coverage;
- publication/version stability;
- accessibility to maintainers;
- compatibility with project scope;
- citation precision.

### Blocking impact

High-impact morphology, syntax, dialect and orthography decisions lack auditable provenance until this is resolved.

### Required updates when resolved

```text
RESEARCH_EVIDENCE.md
MORPHOLOGY_SPEC.md
SYNTAX_AND_CONSTRUCTOR_RULES.md
LANGUAGE_OVERVIEW.md
future decision entries
```

---

# Deferred decisions

No decision is currently marked `deferred`.

A future deferred entry must include a concrete reconsideration trigger such as:

```text
after the release entrypoint is selected
after GF version support is tested
after a named upstream RGL change
before project version 1.0.0
```

“Later” is not a valid trigger.

---

# Rejected decisions

## PDEC-0029 — Use GUI state as active-language authority

**Status:** rejected  
**Rejected:** Established by active configuration contracts before this consolidation  
**Last reviewed:** 2026-07-22

### Proposal

Use local GUI state to select or define the active Albanian project.

### Reason for rejection

GUI state is:

- machine-local;
- disposable;
- not reliably version-controlled;
- unsuitable for CI;
- unsuitable for release identity;
- capable of contradicting project configuration.

### Canonical alternative

```text
project/project.toml
```

owns project identity.

The GUI may remember convenience values but cannot override required project facts or release gates silently.

---

## PDEC-0030 — Infer entrypoints from module filenames

**Status:** rejected  
**Rejected:** Established by active entrypoint contracts before this consolidation  
**Last reviewed:** 2026-07-22

### Proposal

Select an entrypoint automatically from names such as:

```text
GrammarSqi
LangSqi
AllSqi
```

### Reason for rejection

Filename conventions do not establish:

- public role;
- required imports;
- scenario target;
- PGF target;
- completeness;
- consumer compatibility.

### Canonical alternative

Entrypoints and release targets are explicit in `project/project.toml` and project architecture.

---

## PDEC-0031 — Accept current scenario output automatically as gold

**Status:** rejected  
**Rejected:** Established by active gold contracts and golden-output architecture  
**Last reviewed:** 2026-07-22

### Proposal

When a gold comparison fails, replace the gold with current output automatically.

### Reason for rejection

This would:

- accept regressions;
- remove independent expectations;
- make CI unsafe;
- hide linguistic defects;
- conflate execution with approval.

### Canonical alternative

Use a separate explicit reviewed gold-update operation with raw evidence, normalization review and a deterministic diff.

---

## PDEC-0032 — Treat compiling scaffolding as stable coverage

**Status:** rejected  
**Rejected:** Established by explicit incomplete-state policy  
**Last reviewed:** 2026-07-22

### Proposal

Treat a scaffold, placeholder or string-based fallback as stable when the module compiles.

### Reason for rejection

Compilation does not prove:

- correct lincat structure;
- complete morphology;
- complete abstract function coverage;
- correct linguistic output;
- release suitability.

### Canonical alternative

Record the state in `STATUS_LEDGER.md`, define its consumers and validate completion before promotion to `stable`.

---

## PDEC-0033 — Flatten shared structured lincats to `Str` as a general repair

**Status:** rejected  
**Rejected:** Established by project contract invariants  
**Last reviewed:** 2026-07-22

### Proposal

Replace complex lincats with simple string records to resolve local compile problems.

### Reason for rejection

This can remove:

- agreement;
- case;
- definiteness;
- person/number;
- complement behavior;
- constructor information;
- downstream composition.

### Canonical alternative

Repair the authoritative provider or document a narrow temporary fallback with a migration path and validation evidence.

---

# Decision change process

## 8. When a new decision entry is required

Create or update a decision entry when a change affects:

- project identity;
- module suffix or source root;
- target variety;
- orthography;
- public GF category/function;
- lincat shape;
- public helper ownership;
- module dependency direction;
- entrypoint identity;
- checkpoint requiredness/order;
- scenario ID or semantics;
- gold normalization meaning;
- accepted gold behavior;
- missing-function policy;
- release artifact identity;
- supported GF versions;
- release-gate meaning;
- accepted project-wide fallback.

Routine private refactors do not require a decision entry when all public contracts and outputs remain compatible.

---

## 9. Decision proposal workflow

```text
[ ] Problem and scope stated
[ ] Existing contracts identified
[ ] Providers identified
[ ] Direct consumers identified
[ ] Downstream consumers reviewed
[ ] Linguistic evidence collected where relevant
[ ] Alternatives documented
[ ] Compatibility classified
[ ] Validation plan defined
[ ] Migration defined when breaking
[ ] Status-ledger impact reviewed
[ ] Gold impact reviewed
[ ] Release impact reviewed
[ ] Owner assigned
[ ] Decision status assigned
```

A proposal is not active policy until its status becomes `accepted` or applicable `conditional`.

---

## 10. Acceptance requirements

A decision may become `accepted` only when:

- the decision text is unambiguous;
- the owner is identified;
- affected contracts are known;
- required implementation changes are complete or explicitly staged;
- consumers are updated;
- validation evidence exists;
- documentation is aligned;
- migration is defined when needed;
- unresolved contradictions are removed.

A decision must not be marked accepted only because one source file compiles.

---

## 11. Breaking decision workflow

For a breaking decision:

```text
[ ] Existing decision ID identified
[ ] New decision ID created or explicit revision recorded
[ ] Reason documented
[ ] Provider changes defined
[ ] All consumers listed
[ ] Project configuration migrated
[ ] Source modules migrated
[ ] Scenarios migrated
[ ] Inputs migrated
[ ] Golds reviewed/migrated
[ ] Entry/release artifacts migrated
[ ] Contract lock updated
[ ] Architecture/dependency map updated
[ ] Validation specification updated
[ ] Status ledger updated
[ ] Known issues updated
[ ] Release criteria updated
[ ] Full checkpoint validation passed
[ ] Release validation passed where applicable
```

No isolated file edit completes a breaking decision.

---

## 12. Supersession policy

When a decision is replaced:

- the old entry remains;
- old status becomes `superseded`;
- the old entry names the replacing ID;
- the new entry names the replaced ID;
- migration and compatibility effects are documented;
- historical rationale is preserved.

Do not rewrite history to make the old decision disappear.

---

## 13. Rejection policy

A rejected proposal remains recorded when it is likely to recur.

The entry explains:

- what was proposed;
- why it was rejected;
- what canonical alternative applies;
- what new evidence would justify reopening it.

A rejected idea must not re-enter through an undocumented implementation shortcut.

---

## 14. Conditional decision policy

A conditional decision must state:

```text
condition
affected scope
behavior when condition is true
behavior when condition is false
validation proving the condition
```

Examples might include:

- an API entrypoint only when an external consumer exists;
- platform-specific gold only when semantic platform variation is proven;
- an allowlisted missing function only for an experimental entrypoint.

---

## 15. Open-decision policy

An open decision is not permission to invent a default silently.

While an entry is open:

- code may preserve existing behavior;
- new behavior must not claim the unresolved policy;
- golds must not imply undocumented linguistic authority;
- release criteria must state whether the open item blocks release;
- temporary behavior belongs in the status ledger.

---

## 16. Decision-to-contract traceability

Significant accepted decisions should be referenced from relevant contract entries.

Minimum traceability:

| Decision domain | Contract/document link |
|---|---|
| Project identity | `PIFC-CONFIG-*` |
| Module ownership | `PIFC-MODULE-*`, `PIFC-HELPER-*` |
| Lincats | `PIFC-LINCAT-*` |
| Entrypoints | `PIFC-ENTRY-*` |
| Scenarios | `PIFC-SCENARIO-*` |
| Golds | `PIFC-GOLD-*` |
| Artifacts | `PIFC-ARTIFACT-*` |
| Release | `PIFC-RELEASE-*` |
| Temporary states | `STATUS_LEDGER.md` |
| Linguistic rules | morphology/syntax specifications |
| Evidence | validation specification and coverage matrix |

---

## 17. Decision-to-validation traceability

Every accepted decision must have at least one proof type:

```text
configuration validation
source scan
module compile
checkpoint compile
entrypoint compile
native .gfs scenario
missing-function inspection
gold comparison
PGF build
artifact integrity check
documentation/contract review
```

Manual inspection is allowed only when automation is not practical and must state:

- reviewer role;
- method;
- evidence location;
- date or release.

---

## 18. Decision-to-release traceability

A decision affects release when it changes:

- public grammar behavior;
- required modules;
- entrypoints;
- missing-function policy;
- scenario requiredness;
- accepted gold output;
- supported GF version;
- PGF identity;
- known issue acceptance;
- stable/incomplete status.

Release-impacting entries must be reviewed in:

```text
project/docs/RELEASE_CRITERIA.md
project/docs/KNOWN_ISSUES.md
project/docs/STATUS_LEDGER.md
```

---

## 19. Decision log review cadence

Review this log:

- before every major project release;
- when a project contract changes;
- when a gold changes significantly;
- when the entrypoint changes;
- when a new GF version is supported;
- when scaffolding becomes stable or is retired;
- when dialect or orthographic policy changes;
- after a major regression or drift incident;
- during migration to a new repository copy or project schema.

---

## 20. Drift indicators

Decision drift exists when:

- code implements a choice absent from this log or its owning specification;
- a decision is marked open but documentation presents one option as settled;
- a rejected alternative appears in active code;
- an accepted decision has no current validation evidence;
- a provider changes without consumer review;
- a scenario loads an entrypoint different from the decision/configuration;
- a gold changes without linguistic or architectural rationale;
- a scaffold is called stable without a promotion decision;
- current policy is inferred from historical logs;
- the final PGF name differs from configuration;
- dialectal behavior appears in golds but has no documented policy;
- Unicode is normalized linguistically without an orthographic decision;
- a required release gate is weakened through UI state;
- a superseded entry is still referenced as active;
- decision IDs are reused.

Each drift indicator must be resolved by restoring current policy or accepting a coordinated new decision.

---

## 21. Decision log maintenance checklist

```text
[ ] IDs are unique
[ ] Status values are canonical
[ ] Accepted decisions have no placeholders
[ ] Open decisions have owners
[ ] Open decisions state blocking impact
[ ] Rejected decisions state canonical alternative
[ ] Superseded entries link both directions
[ ] Affected contracts are named
[ ] Validation evidence is named
[ ] Current project identity is correct
[ ] Historical evidence is labeled historical
[ ] Status ledger is synchronized
[ ] Known issues are synchronized
[ ] Release criteria are synchronized
[ ] No decision is inferred from GUI state
```

---

## 22. Current decision summary

### Accepted

| ID | Decision |
|---|---|
| `PDEC-0001` | One active language per repository copy |
| `PDEC-0002` | `project/project.toml` owns active project identity |
| `PDEC-0003` | Albanian identity uses `sqi`, `Sqi` and `lib/src/albanian` |
| `PDEC-0004` | GF remains the authoritative execution engine |
| `PDEC-0005` | Static scanning remains supplementary |
| `PDEC-0006` | Public responsibilities have one authoritative provider |
| `PDEC-0007` | Dependency direction follows linguistic architecture |
| `PDEC-0008` | Structured lincats must not be flattened silently |
| `PDEC-0009` | Checkpoints precede final entrypoint validation |
| `PDEC-0010` | Project scenarios use native `.gfs` execution |
| `PDEC-0011` | Scenario output uses stable section markers |
| `PDEC-0012` | Gold files are reviewed project assets |
| `PDEC-0013` | Normal validation never updates gold files |
| `PDEC-0014` | Raw evidence is preserved before interpretation |
| `PDEC-0015` | Normalization removes instability, not Albanian meaning |
| `PDEC-0016` | Incomplete states remain explicit |
| `PDEC-0017` | Required scenarios and known issues determine release eligibility |
| `PDEC-0018` | Entrypoints and release artifacts are configured, not inferred |
| `PDEC-0019` | Historical diagnostics do not define current status |

### Open

| ID | Required decision |
|---|---|
| `PDEC-0020` | Primary Albanian variety |
| `PDEC-0021` | Canonical orthography and Unicode policy |
| `PDEC-0022` | Grammar, language/API and release entrypoints |
| `PDEC-0023` | Expected PGF artifact name and contents |
| `PDEC-0024` | Required and optional scenario registry |
| `PDEC-0025` | Missing-function acceptance policy |
| `PDEC-0026` | Retirement path for `ExtendSqiScaffolding` |
| `PDEC-0027` | Supported GF versions |
| `PDEC-0028` | Linguistic research authorities |

### Rejected

| ID | Rejected approach |
|---|---|
| `PDEC-0029` | Use GUI state as active-language authority |
| `PDEC-0030` | Infer entrypoints from module filenames |
| `PDEC-0031` | Accept current scenario output automatically as gold |
| `PDEC-0032` | Treat compiling scaffolding as stable coverage |
| `PDEC-0033` | Flatten structured lincats to `Str` as a general repair |

### Conditional

None currently recorded.

### Deferred

None currently recorded.

### Superseded

None currently recorded.

### Retired

None currently recorded.

---

## 23. Related project documents

- `project/project.toml`
- `project/docs/00_PROJECT_START_HERE.md`
- `project/docs/LANGUAGE_OVERVIEW.md`
- `project/docs/LANGUAGE_ARCHITECTURE.md`
- `project/docs/MODULE_DEPENDENCY_MAP.md`
- `project/docs/CATEGORY_AND_LINCAT_CONTRACT.md`
- `project/docs/MORPHOLOGY_SPEC.md`
- `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md`
- `project/docs/VALIDATION_SPEC.md`
- `project/docs/TEST_COVERAGE_MATRIX.md`
- `project/docs/STATUS_LEDGER.md`
- `project/docs/KNOWN_ISSUES.md`
- `project/docs/RELEASE_CRITERIA.md`
- `project/docs/RESEARCH_EVIDENCE.md`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`

---

## 24. Related framework decisions and policies

- `docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md`
- `docs/decisions/ADR-0002-GF-AS-EXECUTION-ENGINE.md`
- `docs/decisions/ADR-0003-SEPARATE-SCAN-AND-COMPILE.md`
- `docs/decisions/ADR-0004-NATIVE-GFS-SCENARIOS.md`
- `docs/decisions/ADR-0005-FILE-AND-SCENARIO-RESULTS.md`
- `docs/decisions/ADR-0007-GOLDEN-OUTPUT-TESTING.md`
- `docs/projects/PROJECT_MODEL.md`
- `docs/gf/GF_VERSION_COMPATIBILITY.md`
- `docs/scenarios/GOLDEN_TESTS.md`
- `docs/release/VERSIONING_POLICY.md`

---

## 25. Final enforcement rule

This log records accepted Albanian project decisions and explicitly exposes choices that are still unresolved.

It must never convert:

- historical evidence into current status;
- a module filename into an entrypoint decision;
- current output into accepted gold automatically;
- scaffolding into stable coverage;
- an undocumented linguistic assumption into language policy.

Therefore:

> When a durable project choice affects more than one file, it must be recorded here or in a linked decision record, implemented as a coordinated contract change and proven by current validation evidence.
