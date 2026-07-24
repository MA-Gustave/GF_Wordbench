# GF Wordbench — Release Gates

**Document ID:** `GF-WB-RELEASE-GATES`  
**Status:** Normative specification  
**Applies to:** GF Wordbench `release` mode and active-language release decisions  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** GF Wordbench maintainers  
**Gate policy version:** `1.1.0`  
**Primary project authorities:**
- `project/project.toml`
- `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md`
- `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md`
- `project/docs/KNOWN_ISSUES.md`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`

**Framework authorities:**
- `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/gf/GF_VERSION_COMPATIBILITY.md`
- `docs/validation/VALIDATION_MODES.md`

**Document version:** `1.1.0`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This document defines the conditions under which GF Wordbench may declare an active GF language project ready for release.

A release decision must not depend on:

- one successful source compilation;
- a previously generated `.pgf`;
- a developer's memory;
- an unrecorded manual command;
- a report that omits raw evidence;
- a locally ignored failure;
- an automatic gold-file rewrite;
- a scenario that did not complete its required assertions.

Release readiness is a compound decision.

> A project is release-ready only when every applicable required gate has passed in one coherent release run.

The release run must prove the state of the current project, current toolchain, current scenarios, current expectations, and current generated artifacts.

---

## 2. Release decision

GF Wordbench produces one release decision:

```text
READY
NOT_READY
ERROR
```

### 2.1 `READY`

All applicable required gates completed with status:

```text
OK
```

No release blocker remains.

### 2.2 `NOT_READY`

The release process completed sufficiently to evaluate the project, but one or more required criteria failed.

Examples:

- required module does not compile;
- required scenario fails;
- gold output differs;
- missing linearizations exceed the accepted project policy;
- expected PGF is absent;
- a release-blocking known issue remains open.

### 2.3 `ERROR`

GF Wordbench could not execute or interpret one or more required gates correctly.

Examples:

- invalid project configuration;
- GF executable cannot launch;
- required gate times out;
- result schema is invalid;
- required evidence is missing;
- manifest verification fails;
- contract checker crashes;
- release run is cancelled.

### 2.4 Decision precedence

Decision precedence is:

```text
ERROR > NOT_READY > READY
```

Rules:

- any required gate with `ERROR` makes the release decision `ERROR`;
- otherwise, any required gate with `FAIL` makes the release decision `NOT_READY`;
- otherwise, any required gate with `SKIPPED` makes the release decision `ERROR`;
- otherwise, the release decision is `READY`.

---

## 3. Gate status model

Every gate uses the canonical validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

### 3.1 Meaning

| Status | Gate meaning |
|---|---|
| `OK` | The gate ran and all its required criteria passed |
| `FAIL` | The gate ran but at least one release criterion was not satisfied |
| `ERROR` | The gate could not run or its result could not be interpreted reliably |
| `SKIPPED` | The gate was intentionally not executed |

### 3.2 Applicability

Applicability is represented separately:

```text
required
conditional
not_applicable
```

Rules:

- a `required` gate MUST NOT be `SKIPPED`;
- a `conditional` gate becomes required when its activation condition is true;
- a `not_applicable` gate may be recorded as `SKIPPED` with an explicit reason;
- absence of a gate result is not equivalent to `not_applicable`.

### 3.3 Warnings

Warnings do not replace status.

A gate may be:

```text
status = OK
warnings = [...]
```

A warning becomes release-blocking only when framework or project policy classifies it as a blocker.

---

## 4. Release-run invariants

A valid release decision requires one coherent run.

### 4.1 Mode

The run mode MUST be:

```text
release
```

A `quick`, `checkpoint`, or `diagnostic` run cannot produce `READY`.

### 4.2 Current source state

All release-significant evidence MUST correspond to the current source fingerprints.

Stale artifacts from an earlier run MUST NOT count as release evidence.

### 4.3 Clean output ownership

Release artifacts MUST be produced in the current run's owned directories.

Source files MUST NOT be overwritten.

### 4.4 Deterministic scope

The release scope MUST come from resolved project configuration.

It MUST include:

- configured release entrypoints;
- required checkpoints;
- required scenarios;
- required gold comparisons;
- required project release criteria;
- required framework checks.

### 4.5 No hidden execution

Every release-significant external command MUST be recorded with:

```text
executable
arguments
working directory
effective GF path
GF version
stdout
stderr
exit code
timeout state
duration
produced artifacts
```

### 4.6 No evidence reconstruction

Reports consume recorded results.

They MUST NOT rerun GF or reconstruct missing release evidence.

### 4.7 Immutable accepted expectations

Normal release validation MUST NOT modify:

- source files;
- scenario files;
- input fixtures;
- gold files;
- project documentation;
- contract locks;
- project configuration.

### 4.8 Portfolio independence

`gf-portfolio` may consume completed public release artifacts after the Wordbench run is published.

Portfolio availability, ingestion, indexing, comparison, or aggregation MUST NOT:

- participate in release-gate evaluation;
- change a Wordbench release decision;
- become required for Wordbench execution;
- write into the Wordbench run directory;
- introduce Portfolio state into Wordbench schemas.

---

## 5. Gate ordering

The canonical gate order is:

```text
RG-00 Release request
RG-01 Project identity and configuration
RG-02 Environment and toolchain
RG-03 Release scope and project contracts
RG-04 Source inventory and static policy
RG-05 Clean checkpoint compilation
RG-06 Release entrypoint compilation
RG-07 Required grammar-load and runtime scenarios
RG-08 Golden regression validation
RG-09 Missing-function and completeness policy
RG-10 PGF release build
RG-11 Regression and known-issue review
RG-12 Framework contract and schema integrity
RG-13 Evidence, reports, and manifest integrity
RG-14 Release decision
```

A later gate SHOULD NOT execute when a prior failure makes its result meaningless.

It MAY execute after a non-fatal project failure when additional diagnostic evidence is useful and safe.

Every blocked downstream gate MUST record:

```text
status = SKIPPED
blocked_by = <gate-id>
```

A required skipped gate still prevents `READY`.

---

# 6. RG-00 — Release request

**Applicability:** Required  
**Owner:** Release orchestrator

## 6.1 Purpose

Confirm that the run is intentionally requesting a release decision.

## 6.2 Required criteria

- run mode is `release`;
- project root is explicit and resolved;
- output root is explicit and writable;
- no single-file target narrows the release scope;
- `no_compile` is false;
- version probing is not skipped;
- release configuration has been finalized before execution;
- run ID and run directory are created successfully.

## 6.3 Failure classification

Use `FAIL` when the request intentionally selects settings incompatible with release.

Use `ERROR` when configuration cannot be interpreted.

## 6.4 Examples of blockers

```text
mode = quick
mode = diagnostic
no_compile = true
skip_version_probe = true
target_file is set
output root unavailable
```

## 6.5 Evidence

```text
resolved RunConfig
resolved RunPaths
release invocation metadata
```

---

# 7. RG-01 — Project identity and configuration

**Applicability:** Required  
**Owner:** Project loader and configuration validator

## 7.1 Purpose

Prove that one coherent active language project is defined.

## 7.2 Required criteria

`project/project.toml` MUST:

- exist;
- use a supported schema;
- contain one active project;
- define a stable project ID;
- define a display name and language code;
- resolve its project root;
- resolve its source directory;
- define at least one release entrypoint;
- define required checkpoints or explicitly document why none apply;
- define required scenarios;
- define whether PGF is required;
- use valid path declarations;
- contain no unresolved placeholders;
- contain no duplicate scenario identifiers;
- contain no stale active-language identity from a previous project.

## 7.3 Cross-document criteria

The following MUST agree with `project.toml`:

- project README;
- project interfile lock;
- language architecture;
- dependency map;
- validation specification;
- release criteria;
- scenario registry;
- expected artifact names.

## 7.4 Blockers

- missing `project.toml`;
- unsupported schema major version;
- missing entrypoint;
- duplicate scenario ID;
- active language mismatch;
- project root escape;
- unresolved template placeholder;
- stale previous-language identifier in active paths or configuration.

## 7.5 Evidence

```text
validated project configuration
project identity report
configuration warnings and blockers
```

---

# 8. RG-02 — Environment and toolchain

**Applicability:** Required  
**Owner:** Toolchain compatibility service

## 8.1 Purpose

Prove that the release uses an accepted GF and RGL environment.

## 8.2 Required criteria

- GF executable resolves to the executable actually launched;
- version probe succeeds;
- normalized GF version is available;
- compatibility tier permits release certification;
- required GF capabilities pass;
- project minimum GF version is satisfied;
- no known-incompatible version/build/platform rule applies;
- RGL root exists;
- required RGL identity is captured;
- required RGL modules are available;
- effective GF path resolves successfully;
- platform is certified or explicitly accepted by project policy;
- locale and encoding policy are compatible with deterministic output.

## 8.3 Certified toolchain

A fully certified release normally requires:

```text
compatibility tier = certified
```

A secondary compatible line MAY be accepted when:

- the full release capability suite passes;
- project release policy allows it;
- the result records the exact compatibility tier;
- no known incompatibility applies.

An `untested_newer`, `unknown`, or `legacy_unsupported` GF toolchain MUST NOT produce a fully certified `READY` decision under the default policy.

## 8.4 RGL identity

The strongest available identity SHOULD be recorded:

```text
release tag
Git commit
distribution manifest
directory manifest hash
explicit project label with fingerprints
```

A dirty RGL checkout requires project-policy approval and MUST be visible in the release result.

## 8.5 Blockers

- version probe skipped;
- GF version unknown;
- unsupported version;
- failed required capability;
- invalid GF search path;
- missing required RGL module;
- incompatible GF/RGL pairing;
- uncertified platform without project permission;
- unrecorded toolchain override.

## 8.6 Evidence

```text
GFCompatibilityResult
GF executable hash
raw version probe
capability results
RGL identity
GF path resolution
```

---

# 9. RG-03 — Release scope and project contracts

**Applicability:** Required  
**Owner:** Project contract checker

## 9.1 Purpose

Verify that the files and relationships intended for release are completely declared.

## 9.2 Required criteria

- every configured entrypoint exists;
- every configured checkpoint exists;
- module names match filenames where required by project policy;
- every required scenario maps to exactly one `.gfs` file;
- every required gold-backed scenario maps to exactly one `.gold` file;
- every scenario loads its documented entrypoint;
- required scenario inputs exist;
- expected PGF name is declared or deterministically derived;
- module ownership contracts are complete;
- dependency map does not contradict actual imports;
- lincat/category contracts match the active design;
- no required contract is missing, contradictory, ambiguous, or unresolved for release;
- required project documents exist.

## 9.3 Required document set

At minimum:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC__PROJECT_DOCS.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

A project may declare additional required documents.

## 9.4 Placeholder prohibition

Release-significant project documents MUST NOT contain unresolved placeholders such as:

```text
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<MODULE>
<SCENARIO_ID>
<TODO>
TBD
```

A project may permit literal examples only when clearly fenced and excluded from placeholder validation.

## 9.5 Evidence

```text
project contract-check result
module/scenario/gold registry validation
required-document inventory
```

---

# 10. RG-04 — Source inventory and static policy

**Applicability:** Required  
**Owner:** File selector and scanner

## 10.1 Purpose

Prove that the intended source inventory is known and free from release-blocking static findings.

## 10.2 Inventory criteria

- source directory exists;
- release file selection is deterministic;
- expected entrypoints and checkpoints are included;
- backup, copy, temporary, disabled, and generated noise files are excluded;
- no required source file is excluded accidentally;
- source file identities are unique;
- source fingerprints are recorded;
- no stale generated `.gfo` or `.pgf` is treated as source evidence.

## 10.3 Static findings

Static scan rules are classified as:

```text
blocking
warning
informational
```

The active project or framework policy MUST define which rules block release.

A heuristic finding does not replace GF compilation evidence.

## 10.4 Typical release blockers

- malformed source encoding;
- unresolved conflict marker;
- prohibited unresolved placeholder or conflict marker;
- project-specific forbidden construct;
- duplicate source identity;
- required file excluded by filtering;
- source path outside the project contract;
- stale previous-language identifier in active source where prohibited.

## 10.5 Non-blocking examples

A project MAY classify style-only findings as warnings.

Warnings remain visible in the release result.

## 10.6 Evidence

```text
selected-file inventory
excluded-file inventory with reasons
source fingerprints
per-file scan results
blocking scan summary
```

---

# 11. RG-05 — Clean checkpoint compilation

**Applicability:** Required when checkpoints are declared  
**Owner:** Compiler and audit orchestrator

## 11.1 Purpose

Prove that the project layers required before release entrypoints compile from current source in a clean artifact context.

## 11.2 Required criteria

For every required checkpoint:

- source exists;
- command launches;
- command does not time out;
- exit code indicates success;
- no fatal GF diagnostic is recognized;
- expected current-run `.gfo` exists when required;
- compile result status is `OK`;
- result fingerprint matches current source;
- raw stdout and stderr are preserved.

## 11.3 Clean compilation

Release validation MUST NOT accept success based only on pre-existing artifacts.

The release stage SHOULD:

- use a clean run-owned GFO directory;
- compile in deterministic checkpoint order;
- retain all compile commands and output;
- verify artifact timestamps or hashes belong to the current run.

## 11.4 Failure classification

A checkpoint compile failure is a project `FAIL` when GF executed correctly and rejected the source.

It is an `ERROR` when GF could not launch, timed out, or the result could not be interpreted.

## 11.5 Downstream handling

Direct/downstream classification may aid diagnosis.

It MUST NOT convert a failed required checkpoint into a passing release gate.

## 11.6 Evidence

```text
FileResult for every checkpoint
compile commands
stdout/stderr
GFO artifact entries
source fingerprints
failure classification
```

---

# 12. RG-06 — Release entrypoint compilation

**Applicability:** Required  
**Owner:** Compiler and release orchestrator

## 12.1 Purpose

Prove that every configured release entrypoint compiles after its required lower layers.

## 12.2 Required criteria

For every release entrypoint:

- configured path exists;
- GF module name matches project configuration;
- required imports resolve;
- compile executes in the resolved release environment;
- compile status is `OK`;
- expected `.gfo` exists when applicable;
- no alternate entrypoint is substituted;
- evidence belongs to the current release run.

## 12.3 Separate entrypoints

Grammar, syntax, language API, and other public entrypoints are separate proofs when the project declares them separately.

Success of one does not imply success of another.

## 12.4 Blockers

- missing entrypoint;
- compile failure;
- unresolved import;
- stale GFO;
- entrypoint mismatch;
- unregistered substitute;
- output artifact missing after apparent success.

## 12.5 Evidence

```text
entrypoint compile results
entrypoint-to-artifact mapping
raw compile evidence
```

---

# 13. RG-07 — Required grammar-load and runtime scenarios

**Applicability:** Required  
**Owner:** Scenario runner

## 13.1 Purpose

Prove that the release grammar behaves through GF, not only that individual files compile.

## 13.2 Required scenario classes

The active project defines exact required scenarios.

A complete project normally includes evidence for:

```text
load
linearize
parse
missing
```

It may also require:

```text
round_trip
generation
morphology
structural
lexicon
introspection
application_api
```

## 13.3 Scenario success criteria

Each required scenario MUST satisfy all applicable conditions:

- script exists;
- declared entrypoint loads;
- process launches;
- no timeout;
- required begin/end markers complete;
- no fatal diagnostic violates the scenario;
- declared assertions pass;
- expected output sections are present;
- required artifacts exist;
- exit policy passes;
- normalized output is generated;
- scenario status is `OK`.

A zero process exit code alone is insufficient.

## 13.4 Required scenario skip

A required scenario with `SKIPPED` blocks release.

## 13.5 Bounded execution

Generation or broad enumeration scenarios MUST use documented limits.

Runaway output or uncontrolled execution is an `ERROR`.

## 13.6 Evidence

```text
ScenarioResult
scenario hash
script path
loaded entrypoint
command and working directory
stdout/stderr
marker results
assertion results
normalized output
```

---

# 14. RG-08 — Golden regression validation

**Applicability:** Required for every required gold-backed scenario  
**Owner:** Gold comparator

## 14.1 Purpose

Prove that accepted linguistic and structural outputs remain stable or changed deliberately.

## 14.2 Required criteria

- required gold file exists;
- gold schema/header is valid;
- scenario ID matches;
- normalization version matches;
- scenario completed successfully;
- normalized current output exists;
- exact normalized comparison passes;
- no gold file changed during the run.

## 14.3 Mismatch behavior

A gold mismatch is:

```text
status = FAIL
diagnostic = gold_mismatch
```

It is not an automatic prompt to update gold.

## 14.4 Gold update prohibition

The release command MUST NOT update gold files.

A gold update is a separate reviewed operation completed before the release run.

## 14.5 Semantic preservation

Normalization MUST NOT remove:

- abstract trees;
- linearized text;
- ambiguity counts;
- missing-function lists;
- morphology results;
- language-significant Unicode;
- meaningful punctuation;
- evidence of an incomplete scenario section.

## 14.6 Evidence

```text
gold path and hash
normalized output path and hash
normalization version
comparison result
diff artifact on failure
```

---

# 15. RG-09 — Missing-function and completeness policy

**Applicability:** Required  
**Owner:** Project validation policy and scenario runner

## 15.1 Purpose

Prove that known incompleteness is within the project's explicit release policy.

Compilation and PGF build success do not by themselves prove concrete completeness.

## 15.2 Required criteria

The project MUST define how it evaluates:

- missing linearizations;
- incomplete concrete functions;
- placeholders;
- fallbacks;
- incomplete or fallback release behavior;
- incomplete lexical categories;
- unsupported constructors;
- intentional omissions.

## 15.3 Default release policy

Default release policy:

```text
unapproved missing function      -> FAIL
unapproved placeholder           -> FAIL
release-blocking temporary code  -> FAIL
documented accepted omission     -> allowed only when project policy explicitly permits it
```

## 15.4 Approved omission

An approved omission requires:

- stable identifier;
- scope;
- reason;
- owner;
- release impact;
- validation evidence;
- explicit non-blocking classification;
- record in `KNOWN_ISSUES.md` when the omission affects correctness, validation, compatibility, or release.

Absence of an explicit project-policy decision is not approval.

## 15.5 Zero-missing policy

A project MAY require:

```text
missing_count = 0
```

This SHOULD be the default for a complete production concrete grammar unless project goals explicitly define a partial grammar.

## 15.6 Evidence

```text
missing-function scenario result
missing inventory
approved omission registry
placeholder scan
known-issue and release-policy cross-check
```

---

# 16. RG-10 — PGF release build

**Applicability:** Required when `release_requires_pgf = true`  
**Owner:** PGF builder

## 16.1 Purpose

Build the Portable Grammar Format release artifact from the configured current release entrypoints.

## 16.2 Required criteria

- project declares PGF requirement;
- configured entrypoints exist and passed prior gates;
- command launches;
- command does not time out;
- exit code indicates success;
- no fatal diagnostic is recognized;
- expected `.pgf` exists;
- PGF is non-empty;
- PGF is produced inside the current run's owned artifact directory;
- PGF filename matches the project contract;
- PGF hash and size are recorded;
- PGF is registered in the manifest;
- build command and GF/RGL identities are recorded.

## 16.3 Optimization

When release policy requires optimized PGF:

```text
-optimize-pgf
```

or the supported equivalent MUST be used and recorded.

A diagnostic non-optimized PGF is not a substitute.

## 16.4 Stale artifact protection

Before build:

- expected release artifact location MUST be empty or isolated;
- previous PGF artifacts MUST NOT remain at the target path.

After build:

- artifact must be attributable to the current command and run.

## 16.5 Optional runtime smoke check

A project MAY require loading or querying the generated PGF as an additional condition.

When declared, it becomes part of this gate.

## 16.6 Evidence

```text
PGF build result
command
stdout/stderr
entrypoints
PGF path
size
SHA-256
manifest entry
optional PGF smoke result
```

---

# 17. RG-11 — Regression and known-issue review

**Applicability:** Required  
**Owner:** Diff engine and project release policy

## 17.1 Purpose

Prevent release while known regressions or release-blocking issues remain unresolved.

## 17.2 Run-to-run regression criteria

The release run SHOULD compare against the previous compatible baseline.

Each difference is classified as:

```text
unchanged
improved
regressed
new
removed
```

## 17.3 Blocking regression

A regression is release-blocking when it affects:

- required compilation;
- required scenario behavior;
- required gold output;
- missing-function count;
- PGF construction;
- required artifact integrity;
- required documentation/contract consistency;
- performance or timeout limits defined as release criteria.

## 17.4 Baseline absence

The first valid release candidate may have no previous compatible run.

Baseline absence is not automatically a failure when:

- all current gates pass;
- the release result records `previous_baseline = none`;
- project release policy permits first-release certification.

## 17.5 Known issues

Every open known issue that affects correctness, validation, compatibility, performance thresholds, security, or release MUST declare:

```text
issue ID
severity
release impact
owner
workaround, if any
resolution criteria
decision
```

Any issue marked release-blocking causes `FAIL`.

An issue may be non-blocking only when `RELEASE_CRITERIA.md` explicitly permits the affected limitation and the release run contains evidence for that decision.

## 17.6 Decision log

Significant accepted changes since the previous release SHOULD have corresponding decision records.

## 17.7 Evidence

```text
diff entries
regression summary
known-issues release review
release-criteria review
decision-log review
```

---

# 18. RG-12 — Framework contract and schema integrity

**Applicability:** Required  
**Owner:** Contract and schema validators

## 18.1 Purpose

Prove that GF Wordbench itself did not produce release evidence through drifted interfaces or invalid persisted formats.

## 18.2 Required framework checks

At minimum:

- Python interfile contract checks;
- external-tool contract checks;
- persisted-schema checks;
- active-project interfile contract checks;
- project configuration schema validation;
- run-summary schema validation;
- scenario-output schema validation;
- gold schema validation;
- artifact-manifest schema validation.

## 18.3 Required behavior

- every required checker runs;
- every checker returns `OK`;
- unsupported schema versions fail;
- unknown required enum values fail;
- required artifact paths resolve;
- no report module reruns GF;
- GUI/CLI parity does not affect headless release execution;
- no active-language identifier is embedded in language-neutral framework configuration.

## 18.4 Test-suite relationship

Framework release policy may require the GF Wordbench test suite to pass before shipping the framework.

For an active-language release, the project may consume a previously certified GF Wordbench framework build.

The release result MUST record the GF Wordbench version.

## 18.5 Evidence

```text
contract-check results
schema-check results
GF Wordbench package version
checker versions
```

---

# 19. RG-13 — Evidence, reports, and manifest integrity

**Applicability:** Required  
**Owner:** Result finalizer, report writers, and manifest writer

## 19.1 Purpose

Ensure the release decision is reproducible and reviewable.

## 19.2 Required artifacts

At minimum:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
raw/master.log
raw compile evidence
raw scenario evidence
normalized required scenario outputs
required GFO artifacts
required PGF artifact, when applicable
```

The exact artifact set is declared by run configuration and project release policy.

## 19.3 `summary.json`

Must:

- use the current supported schema;
- identify release mode;
- record project identity;
- record toolchain identity;
- record source fingerprints;
- contain all file and scenario results;
- contain gate results;
- contain the release decision;
- reference required artifacts using run-relative paths.

## 19.4 Human reports

Reports must derive from the finalized structured result.

They must not contradict `summary.json`.

## 19.5 Manifest

The manifest MUST:

- use the supported manifest schema;
- list every required release artifact;
- use unique run-relative paths;
- record required role, size, and SHA-256;
- exclude itself from hashing;
- verify every listed artifact;
- identify missing required artifacts as failure.

## 19.6 Raw evidence immutability

Once captured, raw process evidence MUST NOT be rewritten by normalizers or reports.

## 19.7 Finalization order

Recommended finalization order:

```text
1. complete validation stages
2. finalize structured result
3. write summary.json
4. write human reports
5. write raw aggregate indexes
6. verify required artifacts
7. write manifest
8. verify manifest
9. finalize release decision
```

When the release decision is embedded in `summary.json`, serialization must avoid circular hashing or rewriting. The artifact model must define one stable finalization strategy.

## 19.8 Evidence failure

Missing or invalid release evidence is an `ERROR`, even when underlying project checks appeared to pass.

---

# 20. RG-14 — Release decision

**Applicability:** Required  
**Owner:** Release decision engine

## 20.1 Purpose

Aggregate required gate outcomes without reinterpretation.

## 20.2 Algorithm

```text
required_gates = every gate with applicability required
               + every conditional gate whose condition is true

if any required gate status == ERROR:
    decision = ERROR
else if any required gate status == FAIL:
    decision = NOT_READY
else if any required gate status == SKIPPED:
    decision = ERROR
else:
    decision = READY
```

Warnings do not change the decision unless a policy maps a warning code to a blocker.

## 20.3 No majority rule

Release readiness is not a score or percentage.

Thirteen passing gates do not compensate for one failed required gate.

## 20.4 Required output

The decision result MUST include:

```text
decision
gate policy version
project ID
run ID
GF Wordbench version
GF version
RGL identity
required gate count
passed gate count
failed gate IDs
error gate IDs
skipped required gate IDs
warning count
release artifact paths
decision timestamp
```

## 20.5 Release statement

Only `READY` permits the statement:

```text
GF Wordbench release gates passed.
```

`NOT_READY` and `ERROR` must use unambiguous wording.

---

## 21. Hard gates and configurable gates

### 21.1 Hard gates

The following cannot be waived for a certified release:

- valid release request;
- valid project identity;
- executable GF toolchain;
- supported schemas;
- release entrypoint compilation;
- all required scenarios;
- all required gold comparisons;
- current-run required PGF when configured;
- absence of unapproved release blockers;
- complete release evidence;
- valid manifest;
- successful release-decision computation.

### 21.2 Project-configurable gates

The project may configure:

- checkpoint list;
- scenario list;
- which scenarios use gold;
- missing-function threshold;
- required runtime operations;
- PGF requirement;
- optimized PGF requirement;
- static blocking rules;
- acceptable known omissions;
- performance thresholds;
- optional platform requirements.

Configuration changes must be versioned or reviewed according to their owning contracts.

### 21.3 Conditional gates

Examples:

- PGF gate when `release_requires_pgf = true`;
- parse gate when parsing is in project scope;
- morphology gate when a morphology API is part of the release;
- external API entrypoint gate when present;
- specific platform gate for a platform-targeted release.

---

## 22. Exception and waiver policy

A release gate should normally be fixed, not waived.

### 22.1 No waiver for hard evidence

The following cannot be waived:

```text
required gate did not run
required source did not compile
required scenario failed
required gold mismatched
required PGF is missing
manifest is invalid
release evidence is missing
toolchain identity is unknown
```

### 22.2 Accepted project limitation

A project limitation is not a waiver when it is part of the approved release definition.

It must be:

- explicitly documented in `RELEASE_CRITERIA.md`;
- represented in `KNOWN_ISSUES.md` when it affects correctness, validation, compatibility, or release;
- covered by validation;
- classified non-blocking before the release run;
- consistent with product scope.

### 22.3 Emergency release

GF Wordbench SHOULD NOT declare `READY` by emergency override.

An organization may distribute a build despite `NOT_READY`, but it must be labelled outside GF Wordbench as an exceptional or pre-release distribution.

The recorded GF Wordbench decision remains unchanged.

### 22.4 Override transparency

Every override must be visible in `summary.json` and `summary.md`.

An override cannot silently transform `FAIL` or `ERROR` into `OK`.

---

## 23. Release baseline and reproducibility

### 23.1 Baseline identity

A release baseline SHOULD record:

```text
project source revision
project configuration hash
scenario hashes
gold hashes
GF Wordbench version
GF executable hash
GF normalized version
RGL identity
platform
gate policy version
normalization version
```

### 23.2 Rebuild expectation

A release should be reproducible from:

- archived source;
- project configuration;
- scenario and gold files;
- compatible GF/RGL toolchain;
- GF Wordbench version or compatible release;
- documented commands.

Bit-for-bit PGF reproducibility is required only when project and toolchain policy explicitly guarantee it.

Semantic and gate reproducibility remain required.

### 23.3 Source-control state

Project policy SHOULD record:

```text
revision
branch or tag
dirty state
```

A dirty project working tree may be blocked by release policy.

### 23.4 Archive

A release evidence bundle SHOULD include or reference:

```text
summary.json
manifest.json
reports
raw logs
PGF artifact
source revision
configuration
scenario/gold revision
```

---

## 24. Performance and resource gates

Performance is release-blocking only when thresholds are declared.

Potential thresholds:

```text
maximum checkpoint compile duration
maximum release build duration
maximum scenario duration
maximum normalized output size
maximum generation count
maximum PGF size
```

Rules:

- thresholds belong to project or framework policy;
- timeouts are not performance failures; they are execution errors;
- one anomalous local measurement SHOULD NOT define a regression without policy;
- performance evidence should identify hardware/environment when relevant.

---

## 25. Security gates

A release MUST fail or error when:

- project paths escape permitted roots;
- scenarios contain prohibited shell escape behavior;
- reports contain detected secrets;
- run-owned paths traverse outside the run root;
- required artifacts are symlinks to untrusted external locations under strict policy;
- executable identity changes after compatibility resolution;
- scenario input integrity cannot be established;
- manifest paths are duplicated or unsafe.

Security findings use stable diagnostic identifiers.

---

## 26. Gate-result data model

Recommended immutable model:

```python
@dataclass(frozen=True, slots=True)
class ReleaseGateResult:
    gate_id: str
    name: str
    applicability: str
    status: str
    summary: str
    criteria_total: int
    criteria_passed: int
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    evidence_paths: tuple[Path, ...]
    blocked_by: tuple[str, ...] = ()
    duration_ms: int = 0
```

Release decision model:

```python
@dataclass(frozen=True, slots=True)
class ReleaseDecision:
    decision: str
    gate_policy_version: str
    project_id: str
    run_id: str
    gate_results: tuple[ReleaseGateResult, ...]
    failed_gate_ids: tuple[str, ...]
    error_gate_ids: tuple[str, ...]
    skipped_required_gate_ids: tuple[str, ...]
    warning_count: int
```

### 26.1 Persisted schema coordination

Adding these fields to `summary.json` requires a coordinated update to:

```text
docs/PERSISTED_SCHEMA_LOCK.md
report writer
summary loader
GUI result reader
diff reader when applicable
schema tests
migration tests
```

### 26.2 Deterministic ordering

Gate results MUST be serialized in canonical gate order.

---

## 27. Suggested persisted representation

Recommended `summary.json` section:

```json
{
  "release": {
    "gate_policy_version": "1.0.0",
    "decision": "READY",
    "required_gate_count": 14,
    "passed_gate_count": 14,
    "failed_gate_ids": [],
    "error_gate_ids": [],
    "skipped_required_gate_ids": [],
    "warning_count": 0,
    "gates": [
      {
        "gate_id": "RG-00",
        "name": "Release request",
        "applicability": "required",
        "status": "OK",
        "summary": "Release mode and mandatory execution settings validated.",
        "criteria_total": 8,
        "criteria_passed": 8,
        "blockers": [],
        "warnings": [],
        "evidence_paths": []
      }
    ]
  }
}
```

This representation becomes canonical only after inclusion in the persisted-schema lock.

---

## 28. CLI behavior

Recommended command:

```text
gf-wordbench validate --mode release
```

Optional explicit command:

```text
gf-wordbench release check
```

Suggested concise output:

```text
Release decision: NOT_READY

FAILED
  RG-08 Golden regression validation
    parse.gold differs from normalized parse output

OK
  12 required gates

ERROR
  none

Artifacts:
  summary.json
  summary.md
  AI_READY.md
  manifest.json
```

### 28.1 Exit codes

The authoritative exit-code mapping belongs to:

```text
docs/reference/EXIT_CODES.md
```

Recommended behavior:

```text
READY      -> success exit
NOT_READY  -> validation-failure exit
ERROR      -> runtime/configuration error exit
```

---

## 29. GUI behavior

The GUI SHOULD display:

- release decision;
- gate list in canonical order;
- status per gate;
- first blocker;
- warnings;
- evidence links;
- PGF artifact link;
- summary and manifest links.

The GUI MUST NOT:

- recompute gate semantics independently;
- hide failed required gates;
- label `NOT_READY` as success;
- allow gold updates inside a release run;
- allow a skipped required gate to appear passed.

---

## 30. CI behavior

A CI release job SHOULD:

1. use a clean checkout;
2. use an explicit GF/RGL toolchain;
3. use release mode;
4. disable interactive prompts;
5. avoid compatibility overrides unless declared;
6. preserve the run directory;
7. publish summary and manifest;
8. publish PGF only when decision is `READY`;
9. fail the job for `NOT_READY` or `ERROR`.

### 30.1 Artifact publication

CI MUST NOT publish the PGF as a release artifact when the release decision is not `READY`.

Diagnostic artifacts may still be published for investigation.

---

## 31. Required tests

Recommended files:

```text
tests/release/test_gate_engine.py
tests/release/test_release_decision.py
tests/release/test_release_pipeline.py
tests/release/test_release_manifest.py
tests/contracts/test_release_gate_contract.py
tests/integration/test_release_fixture_project.py
```

### 31.1 Gate engine tests

- all required gates OK;
- one required FAIL;
- one required ERROR;
- one required SKIPPED;
- conditional gate inactive;
- conditional gate active and failed;
- warning-only gate;
- deterministic gate order;
- blocked downstream gate;
- unknown gate status rejected.

### 31.2 Project gate tests

- missing project configuration;
- unresolved template placeholder;
- duplicate scenario ID;
- missing required scenario;
- missing required gold;
- stale language identifier;
- missing entrypoint;
- missing, contradictory, or unresolved required project contract.

### 31.3 Toolchain gate tests

- certified GF;
- compatible GF with passing suite;
- untested newer GF;
- unsupported older GF;
- skipped version probe;
- dirty RGL policy;
- missing RGL module;
- invalid GF path.

### 31.4 Compilation tests

- clean checkpoint success;
- direct compile failure;
- downstream failure;
- timeout;
- stale GFO;
- missing GFO after success;
- entrypoint substitution prohibited.

### 31.5 Scenario and gold tests

- scenario marker success;
- missing end marker;
- zero exit with failed assertion;
- required scenario skipped;
- gold match;
- gold mismatch;
- gold file modified during release;
- normalization-version mismatch.

### 31.6 PGF tests

- successful current-run PGF;
- stale PGF;
- empty PGF;
- wrong filename;
- missing manifest entry;
- optimized requirement not met.

### 31.7 Evidence tests

- missing summary;
- invalid summary schema;
- report contradiction;
- raw evidence missing;
- manifest hash mismatch;
- duplicate manifest path;
- secret-detection blocker.

### 31.8 End-to-end fixture

A minimal language-neutral GF fixture SHOULD exercise:

- project loading;
- checkpoint compile;
- entrypoint compile;
- load scenario;
- parse;
- linearize;
- gold comparison;
- missing-function policy;
- PGF build;
- verified manifest;
- `READY` decision.

---

## 32. Release-gate component ownership

Recommended modules:

```text
app/release/gates.py
app/release/policy.py
app/release/decision.py
app/release/models.py
```

Suggested separation:

| Module | Responsibility |
|---|---|
| `gates.py` | gate registry and gate execution adapters |
| `policy.py` | required/conditional policy resolution |
| `decision.py` | deterministic aggregation |
| `models.py` | typed gate and decision results |

The audit core orchestrates release stages.

Report writers consume finalized release results.

No report writer may execute a gate.

---

## 33. Change policy

A change is release-contract-breaking when it:

- removes a required gate;
- changes gate decision semantics;
- converts a hard gate into a warning;
- changes `READY`, `NOT_READY`, or `ERROR` meaning;
- permits required gates to be skipped;
- changes PGF requirement behavior;
- changes gold acceptance behavior;
- changes missing-function default policy;
- changes required evidence;
- changes manifest integrity requirements.

A coordinated change MUST update:

1. this document;
2. gate engine;
3. result models;
4. persisted schema;
5. project configuration reference when affected;
6. validation modes;
7. CLI and GUI;
8. reports;
9. project release-criteria template;
10. unit and integration tests;
11. contract locks;
12. migration and release notes.

---

## 34. Release checklist

The machine evaluates the gates.

The following checklist is a human review aid and MUST NOT replace machine results.

```text
[ ] Run mode is release
[ ] Project identity is valid
[ ] Toolchain is release-compatible
[ ] GF path and RGL identity are recorded
[ ] Project contracts are complete
[ ] Source inventory is correct
[ ] Blocking static findings are zero
[ ] Required checkpoints compile cleanly
[ ] Release entrypoints compile
[ ] Required scenarios pass
[ ] Required gold files match
[ ] Missing-function policy passes
[ ] Required PGF is current and verified
[ ] No blocking regression remains
[ ] No release-blocking known issue remains
[ ] Known issues have release decisions
[ ] Contract checks pass
[ ] Schema checks pass
[ ] Reports are complete
[ ] Manifest verifies
[ ] Release decision is READY
```

---

## 35. Enforcement rule

A release is not ready because most checks passed.

A release is not ready because a previous run passed.

A release is not ready because a PGF file exists.

A release is not ready because a maintainer intends to fix a known problem later.

> GF Wordbench may declare `READY` only when every applicable required release gate is `OK` in the same current, traceable, evidence-complete release run.
