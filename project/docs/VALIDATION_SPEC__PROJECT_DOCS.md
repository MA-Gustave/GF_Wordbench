# GF Wordbench Project — Validation Specification

**Document ID:** `GF-WB-PROJECT-VALIDATION-SPEC`  
**Status:** Normative  
**Scope:** Active GF language project only  
**Applies to:** Project configuration, GF source modules, checkpoints, entrypoints, native `.gfs` scenarios, validation inputs, reviewed gold files, generated GF artifacts, validation records, known issues, release decisions, and project evidence  
**Authoritative project identity:** `project/project.toml`  
**Project contract lock:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Documentation alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Framework validation policy:** `docs/validation/VALIDATION_MODES.md`  
**Scenario validation policy:** `docs/validation/SCENARIO_VALIDATION.md`  
**Canonical path:** `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md`  
**Last reviewed:** `2026-07-24`  
**Specification version:** `1.1.0`

---

## 1. Purpose

This document defines what the active GF language project must prove before a change, checkpoint, or release may be accepted.

It connects project requirements to executable and reviewable evidence.

The validation relationship is:

```text
project requirement
→ validation target
→ validation stage
→ evidence
→ acceptance rule
→ project status
```

This specification is authoritative for project-level validation intent.

It applies to exactly one active GF project in one Wordbench workspace. Cross-workspace aggregation and multilingual readiness belong to the independent `gf-portfolio` product. Portfolio may consume completed public Wordbench artifacts, but it does not select, execute, mutate, or validate project assets through Wordbench's private runtime.

It must agree with:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/validation/SCENARIO_VALIDATION.md
docs/decisions/ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

Individual GF-file compilation proves only the corresponding source target.

Checkpoint and release claims require current, traceable, passing evidence for every applicable required contract.

---

## 2. Core validation rule

> Every required project behavior must have a defined proof, and every required proof must be executed or reviewed before the corresponding project claim is accepted.

A requirement is not proven by:

- an undocumented manual command;
- a stale `.gfo`;
- an old `.pgf`;
- a console message that was not preserved;
- a scenario with missing completion markers;
- a zero process exit code alone;
- an unreviewed gold update;
- a report generated from incomplete evidence;
- a successful lower-level module when its consumers fail;
- a successful diagnostic run when release proof is required.

A valid proof must identify:

```text
requirement ID
scope
provider or subject
consumer or behavior
validation method
expected result
blocking policy
evidence location
current or most recent accepted evidence
```

---

## 3. Project identity and inventory

The active project has one authoritative identity:

```text
project/project.toml
```

This specification does not duplicate project-specific module names, language identifiers, scenario IDs, or artifact names.

The executable inventory is resolved from project configuration and validated against project files.

The project inventory includes:

```text
source root
selected GF source files
entrypoints
checkpoints
required scenarios
optional scenarios
scenario inputs
gold files
release PGF targets
release artifacts
```

Any difference between the configured inventory and the actual project files is a configuration or contract failure.

---

## 4. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented project exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **REQUIREMENT**: project behavior, structure, property, or artifact that must be proven.
- **PROOF**: executable or manual evidence demonstrating a requirement.
- **TARGET**: file, module, checkpoint, entrypoint, scenario, project, or regression selected for validation.
- **CHECKPOINT**: configured subsystem boundary whose successful validation proves a development layer is coherent.
- **ENTRYPOINT**: top-level GF module used for loading, entrypoint compilation, PGF construction, or external use.
- **SCENARIO**: project-owned native `.gfs` script executed by GF Wordbench.
- **INPUT**: project-owned validation data consumed by a scenario.
- **GOLD**: reviewed expected normalized scenario output.
- **REQUIRED SCENARIO**: applicable scenario that must pass.
- **OPTIONAL SCENARIO**: scenario whose result remains visible but blocks only when project policy declares it blocking.
- **BLOCKING**: failure prevents the selected checkpoint or release from passing.
- **NONBLOCKING**: failure or warning remains visible but does not prevent the selected project decision.
- **EXECUTABLE EVIDENCE**: evidence produced by scanning, GF execution, scenario assertions, comparison, or artifact verification.
- **MANUAL EVIDENCE**: controlled review used only when executable proof is not currently practical.
- **CURRENT EVIDENCE**: evidence generated from the current source fingerprint, configuration, GF executable, and toolchain identity.
- **DIRECT FAILURE**: likely local or root failure at the subject under validation.
- **DOWNSTREAM FAILURE**: failure caused by a known earlier blocker.
- **AMBIGUOUS FAILURE**: failure whose causal source is not sufficiently proven.
- **RELEASE-ELIGIBLE**: successful completed `release` run satisfying all release gates and artifact verification.
- **WAIVER**: explicit time-bounded project decision permitting a documented exception.
- **BASELINE**: accepted prior evidence used for regression comparison.

---

# 5. Authority boundaries

## 5.1 GF authority

GF is authoritative for:

- GF syntax;
- type checking;
- module loading;
- compilation;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- GF-produced `.gfo` and `.pgf` artifacts;
- GF diagnostics.

## 5.2 GF Wordbench authority

GF Wordbench is authoritative for:

- project configuration loading;
- file selection;
- process invocation;
- timeouts;
- evidence capture;
- scenario marker validation;
- assertion evaluation;
- normalization;
- gold comparison;
- failure classification;
- reports;
- release-gate evaluation;
- manifest creation and verification.

## 5.3 Active-project authority

The active project is authoritative for:

- linguistic scope;
- GF module ownership;
- category and lincat contracts;
- morphology design;
- syntax and constructor rules;
- entrypoint inventory;
- checkpoint inventory;
- scenario purpose;
- scenario inputs;
- accepted gold output;
- blocking known issues;
- release criteria.

No layer may silently replace another layer’s authority.

## 5.4 Diagnostic-tool authority

Executable diagnostic tools other than GF are permitted only through the static
registry governed by `ADR-0013-DIAGNOSTIC-TOOL-REGISTRY.md`.

Each registered tool has explicit argument, timeout, output, mutability, network,
evidence, and failure contracts. Arbitrary commands and dynamically loaded
executable plugins are prohibited. AI-assisted tools remain optional, visible,
bounded, and non-normative.

## 5.5 Portfolio boundary

GF Wordbench validates one active project and emits public versioned artifacts.

`gf-portfolio` may consume those completed artifacts. It does not:

- provide Wordbench project identity;
- launch GF or project scenarios through Wordbench;
- mutate project evidence;
- define Wordbench validation statuses;
- require a reverse runtime dependency from Wordbench.

---

# 6. Validation objectives

The project validation system must answer seven questions.

## 6.1 Configuration integrity

```text
Does project configuration identify real, consistent, portable project assets?
```

## 6.2 Source integrity

```text
Do selected GF source files satisfy project scan policy and compile under the resolved toolchain?
```

## 6.3 Contract coherence

```text
Do provider and consumer modules still agree about public categories, functions, operations, lincats, parameters, helpers, and entrypoints?
```

## 6.4 Runtime behavior

```text
Do registered native GF scenarios produce the required behavior and evidence?
```

## 6.5 Regression stability

```text
Does current normalized behavior match reviewed gold and accepted baselines?
```

## 6.6 Artifact integrity

```text
Are required .gfo and .pgf artifacts current, present, nonempty, attributable, and manifest-verified?
```

## 6.7 Release readiness

```text
Are all blocking requirements proven with current evidence and no unresolved blocking project status?
```

---

# 7. Validation layers

Project validation is organized into layers.

```text
V0  configuration and environment
V1  source inventory and static scanning
V2  direct module compilation
V3  checkpoint validation
V4  entrypoint validation
V5  scenario behavior
V6  regression comparison
V7  PGF and artifact verification
V8  status, issue, and documentation review
V9  release gates and archive evidence
```

A higher validation layer does not erase failures at a lower layer.

Release validation includes every required lower layer.

---

# 8. Requirement identifiers

Every stable project requirement should use a unique identifier.

Recommended namespaces:

```text
VAL-CONFIG
VAL-SOURCE
VAL-CONTRACT
VAL-CHECKPOINT
VAL-ENTRY
VAL-SCENARIO
VAL-GOLD
VAL-PGF
VAL-STATUS
VAL-DOC
VAL-RELEASE
VAL-MANUAL
```

Canonical form:

```text
VAL-DOMAIN-NNN
```

Examples defined by this specification:

```text
VAL-CONFIG-001
VAL-SOURCE-001
VAL-CHECKPOINT-001
VAL-ENTRY-001
VAL-SCENARIO-001
VAL-GOLD-001
VAL-PGF-001
VAL-RELEASE-001
```

Identifiers are stable.

A retired identifier must not be reassigned to a different requirement.

---

# 9. Requirement record

Each project requirement must define:

```text
Requirement ID
Title
Status
Purpose
Scope
Provider or subject
Consumers or affected behavior
Applicable modes
Validation method
Expected result
Blocking policy
Evidence artifacts
Failure classification
Owner
Last review
```

Allowed lifecycle statuses:

```text
Active
Deprecated
Retired
```

Requirement lifecycle records whether the contract is active, deprecated, or retired. Neither this field nor `STATUS_LEDGER__PROJECT_DOCS.md` records coding progress.

---

# 10. Evidence types

Allowed evidence types include:

```text
configuration validation
static scan
source fingerprint
direct GF compilation
checkpoint compilation
entrypoint compilation
GF version probe
native .gfs scenario
marker validation
assertion result
normalized output
gold comparison
previous-run comparison
PGF construction
artifact existence
artifact hash
manifest verification
validation-ledger review
known-issue review
documentation review
manual review
```

A requirement may use several evidence types.

Release-significant evidence must be traceable to one run or review record.

---

# 11. Evidence hierarchy

When evidence conflicts, use this order:

```text
current preserved raw GF evidence
→ current structured stage result
→ current normalized result
→ current comparison result
→ current machine summary
→ current human report
→ historical report
→ undocumented recollection
```

Human reports are derived views.

They must not override raw or structured evidence.

---

# 12. Validation modes

The project uses the canonical framework modes:

```text
quick
checkpoint
release
diagnostic
```

The framework owns mode semantics.

The project owns the configured content assigned to each mode.

---

## 12.1 Quick mode

Purpose:

```text
focused development feedback
```

Typical project targets:

- one source file;
- one module;
- one entrypoint smoke check;
- one small scenario;
- one explicitly selected changed-file set.

Required project expectation:

```text
the selected target is real, bounded, scanned, and compiled or executed according to its target kind
```

Quick mode is not release proof.

---

## 12.2 Checkpoint mode

Purpose:

```text
prove one configured subsystem boundary
```

A checkpoint run includes:

- configured prerequisite closure;
- owned source files;
- checkpoint module compilation;
- relevant downstream reachability;
- required checkpoint scenarios;
- required checkpoint gold;
- checkpoint-specific artifacts;
- status review applicable to the checkpoint.

Checkpoint mode is subsystem proof, not release proof.

---

## 12.3 Diagnostic mode

Purpose:

```text
collect expanded evidence and identify blockers
```

Diagnostic mode may:

- continue after independent failures;
- run additional scenarios;
- inspect complete diagnostics;
- compare a selected previous run;
- use explicit scan-only, compile-only, or scenario-only subprofiles;
- preserve expanded evidence.

Diagnostic mode never becomes release-eligible.

---

## 12.4 Release mode

Purpose:

```text
prove the complete active-project release contract
```

Release mode includes:

- full required configuration;
- full required source inventory;
- all required scans;
- all required checkpoints;
- all required entrypoints;
- all required scenarios;
- all required assertions;
- all required gold comparisons;
- all required PGF builds;
- all blocking status and issue checks;
- required reports;
- manifest creation and verification;
- release evidence archive requirements.

Only release mode can produce release-eligible status.

---

# 13. Common preflight requirements

## VAL-CONFIG-001 — Project schema

**Status:** Active  
**Applicable modes:** All  
**Blocking:** Yes

The canonical project file must:

```text
exist
be readable as UTF-8 TOML
contain the expected schema ID
contain a supported schema version
contain every required field
contain no invalid required enum
```

Failure is:

```text
validation_status = ERROR
error_kind = CONFIG
```

---

## VAL-CONFIG-002 — Project identity

**Status:** Active  
**Applicable modes:** All  
**Blocking:** Yes

Project ID, language identity, module suffix, source root, and configured inventories must be internally consistent.

The project identity must not come from:

- application state;
- old reports;
- run directories;
- framework language defaults.

---

## VAL-CONFIG-003 — Path safety

**Status:** Active  
**Applicable modes:** All  
**Blocking:** Yes

Project-owned paths must:

- resolve under approved project roots;
- avoid unauthorized parent traversal;
- use portable project-relative serialization;
- identify existing required source assets;
- remain distinct from run output where policy requires.

---

## VAL-CONFIG-004 — GF executable

**Status:** Active  
**Applicable modes:** All  
**Blocking:** Yes

The resolved GF executable must:

- be explicit after resolution;
- be launchable;
- remain fixed for the run;
- have its raw version text recorded;
- satisfy minimum compatibility policy.

---

## VAL-CONFIG-005 — RGL and GF path

**Status:** Active  
**Applicable modes:** All  
**Blocking:** Yes

The effective GF path must:

- be deterministically ordered;
- include required project and RGL components;
- exclude missing required components;
- be recorded in evidence;
- be shared by compilation, scenario, and PGF stages.

---

## VAL-CONFIG-006 — Output root

**Status:** Active  
**Applicable modes:** All  
**Blocking:** Yes

The output root must:

- be writable;
- not be a project source root;
- support one unique run directory;
- permit atomic evidence writes where required;
- have sufficient space for the selected mode or fail clearly.

---

# 14. Source inventory requirements

## VAL-SOURCE-001 — Deterministic source selection

**Status:** Active  
**Applicable modes:** All source-targeted modes  
**Blocking:** Yes

Selection must use configured:

```text
source directory
source glob
include rules
exclude rules
target scope
mode scope
```

Ordering must be deterministic.

The selected source inventory must be recorded.

---

## VAL-SOURCE-002 — Source existence

**Status:** Active  
**Applicable modes:** All  
**Blocking:** Yes

Every configured required source file, checkpoint module, and entrypoint must exist.

GF Wordbench must not guess replacements for missing configured files.

---

## VAL-SOURCE-003 — Module-name consistency

**Status:** Active  
**Applicable modes:** Checkpoint, release, diagnostic contract checks  
**Blocking:** Yes for required modules

GF module declarations must agree with:

- filenames;
- project configuration;
- dependency map;
- scenario imports;
- entrypoint registry.

A renamed module must be updated across all consumers.

---

## VAL-SOURCE-004 — Encoding and readability

**Status:** Active  
**Applicable modes:** All  
**Blocking:** Yes

Required GF source files must be readable under the project encoding policy.

Canonical project text uses:

```text
UTF-8 without BOM
LF
terminating newline
```

Compatible legacy newline input may be accepted without changing semantic content.

---

## VAL-SOURCE-005 — Source fingerprint

**Status:** Active  
**Applicable modes:** All compiling or scenario modes  
**Blocking:** Yes for release evidence

Each selected source must have a stable fingerprint recorded before dependent execution.

The fingerprint supports:

- artifact freshness;
- regression identity;
- release reproducibility;
- stale-output detection.

---

# 15. Static scanning requirements

## VAL-SCAN-001 — Scan selected source

**Status:** Active  
**Applicable modes:** Quick, checkpoint, release, diagnostic  
**Blocking:** According to scan severity policy

Every selected source file must be scanned before or alongside compilation.

Scan findings remain separate from GF diagnostics.

---

## VAL-SCAN-002 — String and comment masking

**Status:** Active  
**Applicable modes:** All scans  
**Blocking:** Framework correctness requirement

The scanner must not report code patterns found only inside valid comments or strings according to its documented heuristic contract.

Scan results remain advisory or blocking according to project policy.

GF compilation remains authoritative.

---

## VAL-SCAN-003 — Blocking scan findings

**Status:** Active  
**Applicable modes:** Project-defined  
**Blocking:** Yes when severity is `error` or project policy promotes the rule

Blocking project scan rules must be documented.

A new recurring scan warning must be:

- fixed;
- marked nonblocking with rationale;
- or registered as a known issue.

---

# 16. Compilation requirements

## VAL-COMPILE-001 — Direct source compilation

**Status:** Active  
**Applicable modes:** Quick, checkpoint, release, diagnostic  
**Blocking:** Yes for selected required subjects

GF must compile selected source through the approved external-tool contract.

Evidence must include:

```text
executable
arguments
working directory
GF path
source fingerprint
exit code
stdout
stderr
timeout
produced artifacts
```

---

## VAL-COMPILE-002 — Current-run artifacts

**Status:** Active  
**Applicable modes:** Checkpoint and release; diagnostic where artifacts are evaluated  
**Blocking:** Yes

Stale `.gfo` artifacts must not satisfy current validation.

Artifact evidence is valid only when tied to:

```text
current source fingerprint
current run
current GF executable
current effective GF path
successful process outcome
```

---

## VAL-COMPILE-003 — Timeout distinction

**Status:** Active  
**Applicable modes:** All GF execution  
**Blocking:** Yes

A timeout is:

```text
execution_state = timed_out
error_kind = TIMEOUT
```

It must not be reported as ordinary GF syntax or type failure.

---

## VAL-COMPILE-004 — Diagnostic stream preservation

**Status:** Active  
**Applicable modes:** All GF execution  
**Blocking:** Evidence integrity requirement

Stdout and stderr must be preserved separately.

Success or failure must not be inferred from stdout alone.

---

# 17. Checkpoint requirements

## VAL-CHECKPOINT-001 — Registered checkpoint

**Status:** Active  
**Applicable modes:** Checkpoint, release, diagnostic  
**Blocking:** Yes

Every checkpoint target must be registered in project configuration.

An arbitrary file list must not be presented as a configured checkpoint.

---

## VAL-CHECKPOINT-002 — Stable checkpoint identity

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes

Each checkpoint must have:

```text
stable ID
purpose
owned modules
prerequisites
expected consumers or reachability proof
applicable scenarios
blocking status policy
completion evidence
```

---

## VAL-CHECKPOINT-003 — Prerequisite closure

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes

A checkpoint run must include all configured prerequisites in deterministic dependency order.

A failed prerequisite blocks dependent checkpoints.

The dependent failure must not be misreported as an independent root failure when evidence identifies the blocker.

---

## VAL-CHECKPOINT-004 — Owned module compilation

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes

Every required module assigned to the selected checkpoint must compile from the current source state.

---

## VAL-CHECKPOINT-005 — Downstream reachability

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes unless explicitly not applicable

A checkpoint must prove that its public contract is consumed successfully.

Valid proofs include:

```text
downstream checkpoint compilation
configured entrypoint compilation
checkpoint-specific smoke grammar
required scenario loading the consuming entrypoint
```

Internal module success alone is insufficient when downstream reachability is required.

---

## VAL-CHECKPOINT-006 — Checkpoint scenarios

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes for required applicable scenarios

All scenarios assigned as required to the checkpoint must pass.

---

## VAL-CHECKPOINT-007 — Checkpoint completion record

**Status:** Active  
**Applicable modes:** Checkpoint  
**Blocking:** Evidence completeness requirement

Checkpoint evidence should record:

```text
checkpoint ID
prerequisite results
owned module results
entrypoint reachability
scenario results
gold results
validation-ledger blockers
overall checkpoint status
```

---

# 18. Entrypoint requirements

## VAL-ENTRY-001 — Entrypoint registration

**Status:** Active  
**Applicable modes:** Checkpoint, release, diagnostic  
**Blocking:** Yes

Every entrypoint used for loading, compilation, scenarios, PGF construction, or release must be registered in project configuration.

---

## VAL-ENTRY-002 — Entrypoint compilation

**Status:** Active  
**Applicable modes:** Checkpoint where applicable, release, diagnostic  
**Blocking:** Yes for required entrypoints

Every required entrypoint must compile from current source and current-run artifacts.

---

## VAL-ENTRY-003 — Entrypoint load

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes when configured

Every release-significant entrypoint should be loaded in a fresh native GF scenario.

The scenario must confirm:

- load section completion;
- intended grammar identity;
- no fatal load diagnostic;
- required marker completion.

---

## VAL-ENTRY-004 — Entrypoint dependency consistency

**Status:** Active  
**Applicable modes:** Contract checks, checkpoint, release  
**Blocking:** Yes

The entrypoint import chain must agree with:

```text
LANGUAGE_ARCHITECTURE.md
MODULE_DEPENDENCY_MAP.md
INTERFILE_CONTRACT_LOCK.md
actual GF source
```

---

# 19. Category and lincat contract validation

## VAL-CONTRACT-001 — Category coverage

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes for required categories

Public categories defined by project architecture must be covered by the required concrete layers.

---

## VAL-CONTRACT-002 — Lincat shape

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes

Consumers may depend only on documented lincat fields and invariants.

A lincat field change requires coordinated validation of:

```text
provider
constructors
consumer modules
entrypoints
scenarios
gold
documentation
```

---

## VAL-CONTRACT-003 — Parameter and pattern coverage

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes where parameters are public

Public parameter values and pattern consumers must remain aligned.

Compile and generation evidence should cover material parameter branches.

---

## VAL-CONTRACT-004 — Helper ownership

**Status:** Active  
**Applicable modes:** Contract checks and release  
**Blocking:** According to project contract

A public helper or operation must have one documented owner.

Copied or conflicting helper definitions require correction or an explicit decision.

---

## VAL-CONTRACT-005 — Interface and instance coherence

**Status:** Active when applicable  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes when the project uses interfaces and instances

Every required instance must satisfy its documented interface.

Consumers must not depend on undocumented instance-specific behavior.

---

# 20. Morphology validation

## VAL-MORPH-001 — Morphology provider compilation

**Status:** Active when applicable  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes

Configured morphology providers and paradigm modules must compile.

---

## VAL-MORPH-002 — Inflectional coverage

**Status:** Active when applicable  
**Applicable modes:** Checkpoint and release  
**Blocking:** Project-defined

The project must define representative evidence for material inflectional dimensions such as:

```text
number
gender
case
person
tense
aspect
mood
polarity
definiteness
agreement
```

Only dimensions relevant to the active language are required.

Evidence may use:

- linearization scenarios;
- morphology analysis;
- operation introspection;
- reviewed generated forms;
- exact gold.

---

## VAL-MORPH-003 — Irregular behavior

**Status:** Active when applicable  
**Applicable modes:** Checkpoint and release  
**Blocking:** Project-defined

Documented irregular paradigms must have targeted evidence.

An irregular form must not be considered proven only because a regular paradigm compiles.

---

## VAL-MORPH-004 — Lexicon integration

**Status:** Active when applicable  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes for required lexicon coverage

Required lexical entries must:

- use approved paradigms;
- avoid duplicate abstract identifiers;
- compile through the relevant entrypoint;
- satisfy representative scenario evidence.

---

# 21. Syntax validation

## VAL-SYNTAX-001 — Constructor compilation

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes

Required syntax and constructor modules must compile with their providers and consumers.

---

## VAL-SYNTAX-002 — Agreement behavior

**Status:** Active when applicable  
**Applicable modes:** Checkpoint and release  
**Blocking:** Project-defined

Representative scenarios must validate documented agreement behavior.

---

## VAL-SYNTAX-003 — Word-order behavior

**Status:** Active when applicable  
**Applicable modes:** Checkpoint and release  
**Blocking:** Project-defined

Representative linearization and parse scenarios must validate documented ordering constraints.

---

## VAL-SYNTAX-004 — Composition behavior

**Status:** Active when applicable  
**Applicable modes:** Checkpoint and release  
**Blocking:** Project-defined

The project must validate required combinations across:

```text
noun phrases
verb phrases
clauses
questions
relative clauses
coordination
subordination
extensions
structural expressions
```

Only project-declared coverage is required.

---

## VAL-SYNTAX-005 — Negative and rejection behavior

**Status:** Active when applicable  
**Applicable modes:** Release or diagnostic  
**Blocking:** Project-defined

When rejection or ambiguity is part of the contract, scenarios must state:

- accepted parse count;
- forbidden tree;
- required rejection;
- bounded ambiguity;
- accepted canonicalization.

---

# 22. Scenario registry requirements

## VAL-SCENARIO-001 — Unique scenario ID

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Yes

Every scenario ID must be unique within the active project.

---

## VAL-SCENARIO-002 — Registered script

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Yes for required scenarios

Every configured scenario must resolve to one project-owned `.gfs` file.

A required script that is missing is a configuration failure.

---

## VAL-SCENARIO-003 — Documented purpose

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes for required scenarios

Every required scenario must have one documented primary purpose in this specification or an associated project validation registry.

---

## VAL-SCENARIO-004 — Entrypoint relationship

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Yes

Each scenario must load only documented entrypoints or resources.

A scenario loading an obsolete or undocumented local module is invalid.

---

## VAL-SCENARIO-005 — Input relationship

**Status:** Active when inputs are used  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Yes

Every scenario input must:

- exist;
- be registered;
- be UTF-8 unless documented otherwise;
- have stable ordering when order affects output;
- have a declared purpose;
- remain under approved roots.

---

## VAL-SCENARIO-006 — Native GF execution

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Yes

The scenario runner must execute the real GF shell.

It must not emulate or translate GF commands into a second execution language.

---

## VAL-SCENARIO-007 — Fresh process

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Yes

Each scenario runs in a fresh GF process.

No scenario may depend on another scenario’s shell state.

---

## VAL-SCENARIO-008 — Marker protocol

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Yes

Each registered scenario must emit:

```text
one scenario begin marker
one scenario end marker
valid ordered section markers when sections are declared
```

A missing or invalid marker is a scenario contract failure.

---

## VAL-SCENARIO-009 — Explicit termination

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Yes

A scenario must terminate GF explicitly according to the native scenario contract.

Canonical termination command:

```gf
q
```

---

## VAL-SCENARIO-010 — Finite execution

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Yes

Every scenario has a finite timeout.

Potentially expansive commands have explicit command-level bounds.

---

## VAL-SCENARIO-011 — Prohibited system commands

**Status:** Active  
**Applicable modes:** All  
**Blocking:** Yes

Normal project scenarios must not invoke unrestricted operating-system commands, shell escapes, network clients, or external processes. Any auxiliary executable must be invoked by Wordbench through an ADR-0013 registry entry, never directly from project scenario text.

---

## VAL-SCENARIO-012 — Raw evidence

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Evidence integrity requirement

The scenario result must preserve:

```text
script hash
GF executable
GF version
working directory
effective GF path
stdout
stderr
exit code
timeout state
markers
assertions
artifacts
```

---

# 23. Scenario purpose classes

The project may register scenarios in the following purpose classes.

## 23.1 Load

Proves that a configured entrypoint loads in a fresh GF process.

## 23.2 Missing linearizations

Proves the accepted set of missing concrete linearizations.

For a complete release, the accepted set should normally be empty unless project policy explicitly documents exceptions.

## 23.3 Linearization

Proves reviewed abstract trees produce accepted concrete output.

## 23.4 Parsing

Proves reviewed strings produce accepted abstract trees or accepted ambiguity.

## 23.5 Round trip

Proves parse-linearize coherence or documented canonicalization.

## 23.6 Morphology

Proves reviewed analysis, paradigms, or missing-word expectations.

## 23.7 Bounded generation

Exercises a finite controlled abstract-syntax region.

## 23.8 Operation or source introspection

Proves retained source interfaces where those interfaces are project contracts.

## 23.9 PGF runtime smoke

Proves the release artifact can be loaded or queried when the project requires this evidence.

A project may add another purpose class when documented.

---

# 24. Assertion requirements

## VAL-ASSERT-001 — Explicit assertion strategy

**Status:** Active  
**Applicable modes:** Required scenarios  
**Blocking:** Yes

Every required scenario must have one or more explicit assertion strategies.

Allowed strategies include:

```text
required marker
forbidden marker
required text
forbidden text
required regular expression
forbidden regular expression
exact normalized section
empty normalized section
nonempty normalized section
expected result count
bounded result count
required artifact
forbidden fatal diagnostic
gold match
```

---

## VAL-ASSERT-002 — Assertion independence

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Yes

Assertions are evaluated from captured evidence.

They must not rely solely on:

- process exit zero;
- a human report;
- a GUI display;
- an unstored console message.

---

## VAL-ASSERT-003 — Deterministic assertion order

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Evidence consistency requirement

Assertions must be evaluated and reported in stable configured order.

---

# 25. Normalization requirements

## VAL-NORM-001 — Versioned profile

**Status:** Active  
**Applicable modes:** Scenario comparison  
**Blocking:** Yes for gold-backed required scenarios

Every normalized scenario result must identify its normalization profile and version.

---

## VAL-NORM-002 — Raw preservation

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Evidence integrity requirement

Normalization occurs only after raw output is preserved.

---

## VAL-NORM-003 — Semantic preservation

**Status:** Active  
**Applicable modes:** All scenario-enabled modes  
**Blocking:** Yes

Normalization must not remove or rewrite:

```text
linguistic strings
abstract trees
function names
missing linearization names
ambiguity
word order
inflection
category identity
assertion-relevant diagnostics
```

---

## VAL-NORM-004 — Approved noise

**Status:** Active  
**Applicable modes:** Scenario comparison  
**Blocking:** Contract review

Approved normalization may cover:

```text
GF prompts
approved version banner noise
absolute run paths
platform newline differences
temporary run identifiers
documented timing noise
```

Every normalized noise class must be documented and tested.

---

# 26. Gold requirements

## VAL-GOLD-001 — Registered gold

**Status:** Active when gold is required  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes

Every required gold-backed scenario must identify exactly one registered gold source or an explicitly documented section-to-gold strategy.

---

## VAL-GOLD-002 — Gold existence

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes

A missing required gold file is a validation failure.

It must not trigger baseline creation during normal validation.

---

## VAL-GOLD-003 — Gold comparison

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes for required gold

Comparison must use normalized output under the declared normalization profile.

---

## VAL-GOLD-004 — Gold immutability during validation

**Status:** Active  
**Applicable modes:** All  
**Blocking:** Safety requirement

Normal validation must never modify a gold file.

---

## VAL-GOLD-005 — Reviewed update

**Status:** Active  
**Applicable modes:** Explicit gold update only  
**Blocking:** Yes

A valid gold update requires:

```text
intentional source or specification change
old raw output review
new raw output review
normalized diff review
linguistic correctness review
scenario-purpose confirmation
normalization review
documentation update
release-impact review
rerun of proving mode
```

---

# 27. Previous-run comparison

## VAL-DIFF-001 — Compatible baseline

**Status:** Active  
**Applicable modes:** Checkpoint, release, diagnostic; optional quick  
**Blocking:** Project policy

A previous run is compatible only when identity is sufficiently aligned.

At minimum:

```text
project ID
schema compatibility
target identity
mode or scope compatibility
normalization compatibility
```

---

## VAL-DIFF-002 — Structured comparison

**Status:** Active  
**Applicable modes:** All comparisons  
**Blocking:** Evidence integrity requirement

Regression comparison must use structured summaries, not Markdown reports.

---

## VAL-DIFF-003 — Missing baseline

**Status:** Active  
**Applicable modes:** All comparisons  
**Blocking:** No unless project policy requires one

Missing compatible history must be reported.

It must not corrupt the current run.

---

## VAL-DIFF-004 — Release regression review

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Project-defined

When a compatible accepted release baseline exists, release mode must compare against it.

Configured regressions may block release.

---

# 28. PGF requirements

## VAL-PGF-001 — Configured PGF target

**Status:** Active when PGF is required  
**Applicable modes:** Release; diagnostic when selected  
**Blocking:** Yes for release

The expected release PGF target must be declared by project configuration and project contract documentation.

---

## VAL-PGF-002 — Current-run build

**Status:** Active when PGF is required  
**Applicable modes:** Release  
**Blocking:** Yes

The PGF must be produced during the current release run from current source state.

Stale PGF artifacts are invalid release evidence.

---

## VAL-PGF-003 — Process success and artifact existence

**Status:** Active when PGF is required  
**Applicable modes:** Release  
**Blocking:** Yes

PGF success requires both:

```text
successful GF build process
and expected artifact existence
```

A zero exit without the expected PGF is failure.

---

## VAL-PGF-004 — Artifact integrity

**Status:** Active when PGF is required  
**Applicable modes:** Release  
**Blocking:** Yes

The PGF must:

- be nonempty;
- have a recorded byte size;
- have a recorded SHA-256;
- be registered in the manifest;
- match the configured entrypoint;
- use the same source state as required scenarios.

---

## VAL-PGF-005 — Runtime verification

**Status:** Active when project policy requires it  
**Applicable modes:** Release  
**Blocking:** Project-defined

The project may require a native GF or approved PGF-runtime smoke test against the built release artifact.

---

# 29. Documentation validation

## VAL-DOC-001 — Architecture agreement

**Status:** Active  
**Applicable modes:** Checkpoint review and release  
**Blocking:** Yes for release-significant drift

`LANGUAGE_ARCHITECTURE.md` must match the current source layers and entrypoint design.

---

## VAL-DOC-002 — Dependency-map agreement

**Status:** Active  
**Applicable modes:** Contract check and release  
**Blocking:** Yes

`MODULE_DEPENDENCY_MAP.md` must match actual direct imports and current entrypoint chains.

---

## VAL-DOC-003 — Category contract agreement

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes

`CATEGORY_AND_LINCAT_CONTRACT.md` must agree with public GF categories, lincats, fields, parameters, and consumers.

---

## VAL-DOC-004 — Validation inventory agreement

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Yes

This specification, `project.toml`, scenario files, inputs, golds, and coverage matrix must agree.

---

## VAL-DOC-005 — Release criteria agreement

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

Every release criterion must map to an executable or explicit manual proof.

---

# 30. Validation-ledger review

`project/docs/STATUS_LEDGER__PROJECT_DOCS.md` records project-owned validation facts, release
blockers, accepted exceptions, evidence references, and resolution history.

It must not classify coding progress or require status updates after ordinary code
changes.

## VAL-STATUS-001 — Registered validation fact or blocker

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** According to entry

A ledger entry is required when a project claim is affected by:

- a reproducible validation failure;
- a release blocker;
- a time-bounded accepted exception;
- missing or stale required evidence;
- a contract contradiction;
- a known limitation with explicit release impact.

Each entry identifies the affected requirement, evidence, owner, blocking policy,
and review trigger.

---

## VAL-STATUS-002 — Release-blocking ledger entry

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

An unresolved release-blocking ledger entry prevents release.

---

## VAL-STATUS-003 — Resolution record

**Status:** Active  
**Applicable modes:** Release review  
**Blocking:** Evidence consistency requirement

Resolved entries retain:

```text
resolution
date
affected requirements or assets
validation evidence
run ID when applicable
reviewer or owner
```

Resolution is based on evidence, not on a coding-progress label.

---

## VAL-STATUS-004 — Evidence and ledger consistency

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** Project-defined

Source comments, project documentation, validation evidence, known issues, release
criteria, and ledger records must not contradict one another.

---

# 31. Known-issue validation

## VAL-ISSUE-001 — Issue registration

**Status:** Active  
**Applicable modes:** Checkpoint and release  
**Blocking:** According to severity

Recurring known defects or accepted warnings must be registered in `KNOWN_ISSUES.md`.

---

## VAL-ISSUE-002 — Release impact

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes when issue is blocking

Every open issue must state whether it blocks release.

---

## VAL-ISSUE-003 — Reproduction evidence

**Status:** Active  
**Applicable modes:** Diagnostic and release review  
**Blocking:** Project-defined

A known issue should identify:

```text
reproduction
expected behavior
actual behavior
affected modules
scenario or command
evidence path
workaround
status
```

---

## VAL-ISSUE-004 — Accepted issue

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** According to approved policy

A nonblocking accepted issue must have:

- stable issue ID;
- rationale;
- scope;
- owner;
- review date;
- release impact;
- explicit acceptance.

Undocumented warnings must not be silently accepted.

---

# 32. Manual validation

Executable evidence is preferred.

Manual validation is permitted only when automation is impractical or cannot assess the required linguistic judgment.

## VAL-MANUAL-001 — Manual criterion record

**Status:** Active when applicable  
**Applicable modes:** Release review  
**Blocking:** Yes for required manual criteria

Every manual criterion must identify:

```text
criterion ID
reason automation is insufficient
review method
reviewer role
input material
expected decision
evidence location
review date
outcome
```

---

## VAL-MANUAL-002 — No undocumented manual pass

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

A verbal statement or undocumented visual inspection is not release evidence.

---

## VAL-MANUAL-003 — Repeatability

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

Another qualified reviewer must be able to repeat the manual procedure from the documented inputs.

---

# 33. Requirement-to-evidence registry

The active project must maintain a current registry in this document or in `TEST_COVERAGE_MATRIX__PROJECT_DOCS.md`.

Minimum columns:

| Requirement ID | Subject | Mode | Evidence | Blocking | Current owner |
|---|---|---|---|---:|---|
| `VAL-CONFIG-001` | Project schema | all | configuration validation | Yes | Project configuration owner |
| `VAL-SOURCE-001` | Source selection | all | selected-file manifest | Yes | Project maintainer |
| `VAL-COMPILE-001` | Required GF modules | quick/checkpoint/release | compile results | Yes | Module owners |
| `VAL-CHECKPOINT-001` | Registered checkpoints | checkpoint/release | checkpoint results | Yes | Architecture owner |
| `VAL-ENTRY-001` | Registered entrypoints | checkpoint/release | entrypoint compile/load | Yes | Entrypoint owner |
| `VAL-SCENARIO-001` | Scenario inventory | scenario modes | registry and run result | Yes | Scenario owner |
| `VAL-GOLD-001` | Gold-backed behavior | checkpoint/release | normalized comparison | Yes | Gold reviewer |
| `VAL-PGF-001` | Release artifact | release | PGF build and manifest | When applicable | Release owner |
| `VAL-STATUS-002` | Blocking project status | release | ledger review | Yes | Project owner |
| `VAL-RELEASE-001` | Full release contract | release | release gates | Yes | Release owner |

The project adds language-specific requirements without inventing framework behavior.

---

# 34. Scenario registry contract

The scenario registry must expose at least:

| Field | Requirement |
|---|---|
| Scenario ID | Unique stable ID |
| Script | Existing project-relative `.gfs` path |
| Purpose | One primary validation purpose |
| Required | Required or optional |
| Modes | Applicable modes |
| Checkpoints | Applicable checkpoint IDs |
| Entrypoint | Registered entrypoint or resource |
| Inputs | Registered project-relative inputs |
| Gold | Registered gold or explicit no-gold strategy |
| Assertions | Explicit assertion profile |
| Timeout | Finite operation class |
| Normalization | Versioned profile |
| Owner | Maintainer or role |

The exact persisted syntax belongs to the project schema.

---

# 35. Checkpoint registry contract

The checkpoint registry must expose at least:

| Field | Requirement |
|---|---|
| Checkpoint ID | Unique stable ID |
| Purpose | Subsystem boundary proven |
| Owned modules | Required module set |
| Prerequisites | Ordered dependency closure |
| Reachability proof | Entrypoint, consumer, or smoke grammar |
| Required scenarios | Applicable required scenario IDs |
| Optional scenarios | Applicable optional scenario IDs |
| Gold requirements | Required comparison inventory |
| Blocking ledger scope | Applicable status entries |
| Evidence | Required output set |
| Owner | Maintainer or role |

---

# 36. Entrypoint registry contract

The entrypoint registry must expose at least:

| Field | Requirement |
|---|---|
| Entrypoint ID | Stable project identity |
| GF file | Existing project-relative source |
| Purpose | Grammar, syntax, API, or release entry |
| Required modes | Checkpoint/release applicability |
| Checkpoint dependencies | Required checkpoint closure |
| Load scenarios | Registered scenario IDs |
| PGF target | Expected artifact when applicable |
| External consumers | Documented consumers |
| Owner | Maintainer or role |

---

# 37. Blocking policy

A requirement blocks the selected mode when:

- it is marked blocking;
- it applies to the selected target or release scope;
- it fails;
- it errors;
- its required evidence is missing;
- it is skipped without an allowed non-release policy;
- its evidence is stale or unverifiable.

Release mode treats every required release criterion as blocking.

A warning is nonblocking only when project policy explicitly says so.

---

# 38. Failure semantics

Project validation uses:

```text
validation_status = OK | FAIL | ERROR | SKIPPED
execution_state = completed | timed_out | cancelled | launch_failed
diagnostic_class = ok | direct | downstream | ambiguous | noise | skipped
```

These dimensions remain separate.

---

## 38.1 FAIL

Use when the validation operation completed sufficiently and the project criterion failed.

Examples:

- GF type error;
- missing linearization;
- assertion failure;
- gold mismatch;
- blocking scan finding;
- missing expected artifact after a completed build;
- open blocking issue.

---

## 38.2 ERROR

Use when the project criterion could not be evaluated reliably.

Examples:

- malformed project configuration;
- GF launch failure;
- unreadable required input;
- unsupported schema major;
- internal framework failure;
- output root failure.

---

## 38.3 SKIPPED

Use only when an allowed policy deliberately omits the stage or subject.

A required release criterion must not become `SKIPPED` and still permit release success.

---

# 39. Causal classification

The project dependency map supports causal review.

## 39.1 Direct

Evidence points to a local or root failure.

## 39.2 Downstream

Evidence identifies at least one blocking upstream relationship.

## 39.3 Ambiguous

Evidence is insufficient to identify a single blocker.

## 39.4 Noise

The result is noncausal diagnostic noise under documented policy.

## 39.5 Skipped

The subject was not executed under explicit policy.

Classification must not modify raw status or diagnostics.

---

# 40. Release requirements

## VAL-RELEASE-001 — Release mode

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

The proving run must have:

```text
mode = release
execution_state = completed
partial = false
```

---

## VAL-RELEASE-002 — Required checkpoint completion

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

Every configured required checkpoint must pass.

---

## VAL-RELEASE-003 — Required entrypoint completion

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

Every configured required entrypoint must compile and satisfy required load evidence.

---

## VAL-RELEASE-004 — Required scenarios

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

Every required release scenario must pass.

---

## VAL-RELEASE-005 — Required gold

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

Every required gold comparison must match.

---

## VAL-RELEASE-006 — PGF

**Status:** Active when configured  
**Applicable modes:** Release  
**Blocking:** Yes

Every required PGF target must build and verify.

---

## VAL-RELEASE-007 — Status and known issues

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

No unresolved blocking validation-ledger entry or known issue may remain.

---

## VAL-RELEASE-008 — Documentation

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

Project architecture, dependency map, validation inventory, coverage matrix, validation records, and release criteria must reflect current contracts, assets, and evidence.

---

## VAL-RELEASE-009 — Reports

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

Required reports must be written successfully from structured evidence.

At minimum:

```text
summary.json
summary.md
AI_READY.md
manifest.json
```

Additional required files follow framework report policy.

---

## VAL-RELEASE-010 — Manifest verification

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

The release manifest must validate and all required file hashes must match.

---

## VAL-RELEASE-011 — Release eligibility

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** Yes

Release eligibility requires:

```text
mode = release
overall validation status = OK
execution state = completed
partial = false
all release gates passed
manifest verified
```

---

## VAL-RELEASE-012 — Archive readiness

**Status:** Active  
**Applicable modes:** Release  
**Blocking:** According to release publication policy

Accepted release evidence must be archivable with:

```text
project identity
project version
GF Wordbench version
GF version
RGL identity when available
source fingerprints
release run ID
manifest
artifact hashes
```

---

# 41. Release exceptions

The default policy is:

```text
no release exception converts a failed required criterion to ordinary OK
```

When project governance permits an exception, it must include:

```text
exception ID
affected requirement
reason
scope
owner
approval
created date
expiration or review trigger
risk
mitigation
evidence
release labeling
```

A release with an exception must remain distinguishable from an ordinary unqualified pass.

Security, manifest integrity, or missing authoritative project identity should not be waivable.

---

# 42. Change impact

A project change must identify affected validation.

## 42.1 Private internal refactor

Minimum validation:

```text
direct compile
affected consumer compile
relevant quick or checkpoint proof
```

## 42.2 Public helper or lincat change

Required review:

```text
provider
all consumers
checkpoint closure
entrypoints
scenarios
gold
category contract
dependency map
interfile lock
```

## 42.3 Entrypoint change

Required review:

```text
project.toml
entrypoint consumers
load scenarios
PGF target
release criteria
artifact names
documentation
release validation
```

## 42.4 Scenario change

Required review:

```text
scenario purpose
commands
markers
inputs
assertions
normalization
gold
mode applicability
coverage matrix
```

## 42.5 Gold change

Required review:

```text
source or specification cause
old and new raw output
normalized diff
linguistic correctness
scenario purpose
release impact
```

## 42.6 Toolchain change

Required review:

```text
GF version
RGL revision
compatibility policy
compile behavior
scenario output
normalization
gold
PGF
release validation
```

---

# 43. Validation sequence by change type

## 43.1 One local GF file

```text
configuration preflight
→ static scan
→ direct compile
→ direct diagnostics
→ quick report
```

## 43.2 Shared provider

```text
provider quick
→ direct consumers
→ checkpoint closure
→ entrypoint reachability
→ relevant scenarios
→ gold review
```

## 43.3 Scenario or expected behavior

```text
scenario lint
→ focused scenario run
→ raw evidence review
→ assertion review
→ normalization review
→ gold comparison
→ checkpoint or release rerun
```

## 43.4 Release candidate

```text
clean configuration
→ complete source scan
→ all checkpoints
→ all entrypoints
→ required scenarios
→ gold comparisons
→ PGF build
→ status and issue review
→ reports
→ manifest verification
→ archive verification
```

---

# 44. Determinism requirements

Release validation must be deterministic under declared inputs.

The project must define:

```text
source ordering
checkpoint ordering
entrypoint ordering
scenario ordering
input ordering
assertion ordering
normalization version
artifact naming
```

Avoid release evidence based on:

- random generation without deterministic policy;
- current time in semantic output;
- directory enumeration without sorting;
- unspecified default language;
- unspecified material category;
- inherited terminal state;
- mutable external inputs;
- another scenario’s process state.

---

# 45. Timeouts

Every external GF operation must have a finite timeout.

Timeout classes include:

```text
version probe
file compile
checkpoint compile
entrypoint compile
PGF build
scenario
generation
diagnostic introspection
```

A longer timeout does not weaken validation.

An infinite timeout is prohibited.

A timeout must preserve partial raw evidence where possible.

---

# 46. Cancellation

A cancelled run must record:

```text
execution_state = cancelled
partial = true
```

Completed evidence must remain available.

A cancelled run is not checkpoint-complete or release-eligible.

---

# 47. Evidence locations

Release-significant evidence must be stored under the current run directory.

Expected categories:

```text
summary.json
summary.md
AI_READY.md
manifest.json
raw/compile/
raw/scan/
raw/scenarios/
details/
artifacts/gfo/
artifacts/pgf/
```

Exact paths belong to framework artifact contracts.

Project documents reference evidence by run ID and run-relative path.

---

# 48. Evidence retention

The project should protect:

```text
latest successful checkpoint per checkpoint
latest failed checkpoint with unresolved direct failure
latest successful release
latest failed release
current regression baseline
runs referenced by decisions or issues
release archives
```

Retention policy is defined in:

```text
docs/operations/CLEANUP_BACKUP_AND_RECOVERY.md
```

---

# 49. Coverage matrix requirements

`TEST_COVERAGE_MATRIX__PROJECT_DOCS.md` must map every active requirement to evidence.

It should include:

| Requirement | Feature or contract | Proof | Scenario or target | Mode | Blocking | Last evidence |
|---|---|---|---|---|---:|---|

The matrix must not claim coverage from a removed scenario or renamed module.

Manual coverage must identify its review procedure.

---

# 50. Validation inventory consistency

The following inventories must agree:

```text
project.toml
VALIDATION_SPEC__PROJECT_DOCS.md
TEST_COVERAGE_MATRIX__PROJECT_DOCS.md
INTERFILE_CONTRACT_LOCK.md
scenario directory
input directory
gold directory
RELEASE_CRITERIA__PROJECT_DOCS.md
```

Drift examples:

- configured scenario missing from disk;
- script exists but is not registered;
- gold exists without a scenario;
- required scenario lacks an assertion strategy;
- checkpoint references an unknown module;
- entrypoint is renamed only in one document;
- release criteria require an artifact not configured;
- coverage matrix points to stale evidence;
- a validation record uses coding-progress labels;
- Wordbench evidence contains `gf-portfolio` registry or aggregation state;
- a project scenario launches an unregistered executable.

Every drift finding must be corrected or deliberately accepted through a coordinated contract change.

---

# 51. Validation anti-patterns

Prohibited:

```text
declare project complete because all files individually compile
skip a required checkpoint because a top-level entrypoint compiled once
accept zero scenario exit without marker and assertion evidence
treat missing gold as first-run success
update gold automatically
reuse stale .gfo or .pgf as current proof
parse summary.md as primary automation input
hide release-blocking issue in prose
call optional scenario failure invisible
classify downstream failures as independent without evidence
normalize away meaningful linguistic output
run scenario through an undocumented shell wrapper
accept undocumented local GF path
allow project configuration to depend on generated output
track coding progress in requirement or validation-ledger statuses
let project text choose an executable or interpreter
introduce a GF Wordbench runtime dependency on `gf-portfolio`
```

---

# 52. Required project checks

Recommended command:

```text
gf-wordbench project contracts check
```

It should verify:

1. project schema;
2. project identity;
3. source-root existence;
4. module-name consistency;
5. entrypoint existence;
6. checkpoint uniqueness;
7. prerequisite validity;
8. scenario uniqueness;
9. required scenario existence;
10. scenario-to-entrypoint mappings;
11. input existence;
12. required gold existence;
13. scenario marker structure;
14. terminating `q`;
15. forbidden scenario commands;
16. PGF target declaration;
17. documentation existence;
18. coverage-matrix references;
19. blocking validation records;
20. known-issue release flags;
21. stale language identifiers;
22. unresolved required placeholders;
23. artifact-name consistency;
24. release-criteria coverage;
25. absence of coding-progress labels in validation records;
26. ADR-0013 registration for every optional executable;
27. absence of `gf-portfolio` runtime or status fields.

---

# 53. Required automated tests

Project validation infrastructure should test:

```text
valid project configuration
missing required project field
missing source root
missing entrypoint
unknown checkpoint
checkpoint prerequisite cycle
missing required scenario
duplicate scenario ID
scenario with obsolete entrypoint
missing input
missing required gold
gold mismatch
scenario marker failure
scenario timeout
direct compile failure
downstream compile failure
ambiguous failure
current-run artifact verification
missing PGF
manifest mismatch
blocking validation-ledger entry
blocking known issue
manual criterion without evidence
complete successful release
```

---

# 54. Baseline establishment

The initial project baseline must be explicit.

Baseline procedure:

1. validate configuration;
2. inventory source modules;
3. run project-wide diagnostic validation;
4. identify direct and downstream failures;
5. establish checkpoint order;
6. register required scenarios;
7. review initial normalized outputs;
8. create gold only through explicit review;
9. record known issues;
10. record validation failures, blockers, accepted exceptions, and missing evidence;
11. run required checkpoints;
12. run release when all release criteria are satisfied;
13. protect the accepted baseline run.

A failing baseline may be retained for diagnosis and comparison.

It must not be labeled as release-ready.

---

# 55. Project validation registry

The project should maintain a concise current registry.

The registry is derived from current configuration and project documents.

It must identify:

```text
required checkpoints
required entrypoints
required scenarios
optional scenarios
gold-backed scenarios
manual criteria
PGF targets
blocking known issues
blocking validation records
```

The registry must contain current real IDs and paths.

This normative specification intentionally avoids duplicating those volatile values.

---

# 56. Review cadence

Review this specification:

- before every project release;
- after entrypoint changes;
- after checkpoint changes;
- after scenario inventory changes;
- after normalization changes;
- after gold policy changes;
- after a new blocking known issue;
- after validation-ledger policy changes;
- after GF or RGL compatibility changes;
- after a significant drift incident.

---

# 57. Validation review questions

A project reviewer should ask:

```text
Does every configured target exist?
Does every checkpoint prove a real subsystem boundary?
Does every required scenario have one documented purpose?
Does every scenario load a registered entrypoint?
Does every required behavior have an assertion or gold?
Does normalization preserve linguistic meaning?
Does every required gold have reviewed provenance?
Are current artifacts tied to current fingerprints?
Are all blocking issues visible?
Does the coverage matrix match reality?
Can release evidence be reproduced?
```

---

# 58. Validation change checklist

```text
[ ] Requirement ID identified
[ ] Project owner identified
[ ] Affected modes identified
[ ] Target inventory reviewed
[ ] Checkpoint impact reviewed
[ ] Entrypoint impact reviewed
[ ] Scenario impact reviewed
[ ] Input impact reviewed
[ ] Assertion impact reviewed
[ ] Normalization impact reviewed
[ ] Gold impact reviewed
[ ] PGF impact reviewed
[ ] Validation-ledger impact reviewed
[ ] Known-issue impact reviewed
[ ] Coverage matrix updated
[ ] Interfile lock updated
[ ] Release criteria updated
[ ] Focused validation passed
[ ] Checkpoint validation passed
[ ] Release validation passed when applicable
```

---

# 59. Release validation checklist

```text
[ ] Project schema valid
[ ] Project identity consistent
[ ] GF executable supported
[ ] RGL identity recorded
[ ] Effective GF path valid
[ ] Source inventory complete
[ ] Static scan complete
[ ] Source fingerprints recorded
[ ] All required checkpoints pass
[ ] All required entrypoints compile
[ ] Required entrypoints load
[ ] Missing-linearization policy passes
[ ] All required scenarios pass
[ ] Required assertions pass
[ ] Required gold comparisons match
[ ] Required PGF builds pass
[ ] PGF hashes recorded
[ ] No blocking validation-ledger entries
[ ] No blocking known issues
[ ] No coding-progress labels in validation records
[ ] Every optional executable is registered under ADR-0013
[ ] No Wordbench runtime dependency on `gf-portfolio`
[ ] Manual criteria reviewed
[ ] Documentation current
[ ] Coverage matrix complete
[ ] summary.json valid
[ ] Required reports exist
[ ] Manifest valid
[ ] Manifest hashes verify
[ ] Run is complete and nonpartial
[ ] Release evidence protected or archived
```

---

# 60. Completion rule

The active project may claim a requirement only when its evidence is:

```text
current
applicable
complete
traceable
reviewable
passing
```

The active project may claim checkpoint completion only when:

```text
all required prerequisites pass
all checkpoint-owned modules pass
required reachability passes
applicable required scenarios pass
required gold matches
no checkpoint-blocking validation record remains
```

The active project may claim release readiness only when:

```text
a complete release-mode run passes
all release gates pass
all required artifacts exist
manifest verification passes
all blocking validation records and known issues are resolved
```

---

# 61. Validation contract

The project validation relationship is:

```text
project architecture
    defines what exists

interfile contracts
    define what files promise to one another

project.toml
    registers targets and release inventory

this validation specification
    defines what must be proven

checkpoints
    prove subsystem coherence

entrypoint validation
    proves integration

native .gfs scenarios
    prove executable GF behavior

gold files
    preserve reviewed expected behavior

PGF validation
    proves the release artifact

validation-ledger and issue review
    prevents hidden blockers and unsupported claims

GF Wordbench
    captures and evaluates evidence

release criteria
    decide whether the project is complete
```

The governing invariant is:

> No project claim is valid without current evidence, and no required evidence may be omitted, weakened, rewritten, or inferred silently.