# GF Wordbench — Validation Modes

**Document ID:** `GF-WB-VALIDATION-MODES`  
**Status:** Normative  
**Applies to:** CLI, GUI, bootstrap, audit orchestration, project configuration, reports, automation, and release gates  
**Owner:** GF Wordbench maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Canonical path:** `docs/validation/VALIDATION_MODES.md`  
**Contract version:** `1.0.0`  
**Last reviewed:** 2026-08-05

---


## ADR-0015 alignment — selected source and optional validation profile

The current startup model is path-resolved:

- the user selects a GF source file or an RGL language directory directly;
- Wordbench reads that source tree in place and does not copy it into this repository;
- `ResolvedLanguageContext` owns the selected path, resolved language identity, source root, RGL root, discovered entrypoints and effective GF-path facts;
- an explicit `ValidationProfile` is optional and may add only non-derivable policy such as additional selection filters, required or release entrypoints, checkpoints, scenarios, inputs, golds, PGF targets, required artifacts and release gates;
- a legacy `project/project.toml` may be read only when explicitly supplied as a validation profile; it is not a mandatory root file or startup authority;
- run state, logs and artifacts are written under the configured output root, normally `<output-root>/<language-key>/run_<run-id>` (with `_gf_wordbench` as the framework default), never into the selected source tree.

Unless a section is explicitly describing legacy migration input, references to an “active project” or a root `project/` directory are superseded by this model.

---
## 1. Purpose

This document defines the canonical validation modes of GF Wordbench.

The canonical supported modes are:

```text
quick
checkpoint
release
diagnostic
```

A validation mode is a named validation policy.

It determines:

- what is selected;
- which validation stages are required;
- which stages are optional;
- how much evidence is collected;
- which failures block success;
- which artifacts must exist;
- whether the result may be used as release evidence.

A mode is not merely a user-interface label.

CLI, GUI, automation, reports, state, and persisted summaries must use the same mode semantics.

---

## 2. Core rule

> A validation mode defines a minimum contract that callers may strengthen but must not silently weaken.

A caller may request:

- extra files;
- extra checkpoints;
- extra scenarios;
- stricter output comparison;
- additional diagnostics;
- longer evidence retention.

A caller must not silently remove a required stage from the selected mode.

In particular, `release` must never be reduced to a faster workflow by:

- GUI state;
- CLI convenience flags;
- previous-run state;
- missing optional tools;
- an absent scenario;
- an unavailable gold file;
- a timeout;
- a failed version probe;
- a hidden fallback.

A missing required capability is a mode failure, not permission to skip it.

### 2.1 Workspace and product boundary

One GF Wordbench workspace contains exactly one selected GF language context at `project/`.
Every validation run resolves exactly one selected language context and one normative language target.

Validation modes do not provide:

- a multi-project registry;
- simultaneous validation of several selected language contexts in one run;
- cross-workspace orchestration;
- multilingual portfolio aggregation.

Those capabilities belong to the independent `gf-portfolio` product. Portfolio may consume public, versioned Wordbench artifacts, but GF Wordbench does not require or read Portfolio runtime state.

---

## 3. Scope

This document governs:

- mode names;
- mode selection;
- mode aliases;
- default stage inclusion;
- minimum success criteria;
- target requirements;
- checkpoint behavior;
- scenario behavior;
- PGF requirements;
- report requirements;
- diff behavior;
- allowed and prohibited overrides;
- mode persistence;
- CLI and GUI parity;
- CI use;
- release-evidence eligibility.

This document does not define:

- exact GF commands;
- detailed stage implementation;
- project-specific module names;
- project-specific scenario content;
- persisted JSON field layouts;
- CLI syntax beyond mode-level examples;
- GUI layout.

Those belong to their dedicated documents and locks.

---

## 4. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **MODE**: named policy selecting a minimum validation contract.
- **STAGE**: bounded validation operation.
- **TARGET**: file, module, checkpoint, entrypoint, scenario, or subsystem explicitly selected for validation.
- **CHECKPOINT**: configured module or subsystem boundary whose successful validation proves a development layer is coherent.
- **ENTRYPOINT**: top-level GF module used for loading, compilation, or PGF construction.
- **REQUIRED SCENARIO**: scenario that must pass for the applicable mode.
- **OPTIONAL SCENARIO**: scenario whose result remains visible but does not block mode success unless promoted.
- **RELEASE GATE**: condition that must pass before a run is release-eligible.
- **OVERRIDE**: explicit caller-provided value that changes a configurable aspect of a run.
- **STRENGTHENING OVERRIDE**: override that adds validation or evidence.
- **WEAKENING OVERRIDE**: override that removes or bypasses a required check.
- **EVIDENCE LEVEL**: quantity and detail of retained execution evidence.
- **ELIGIBLE RUN**: run whose mode and outcome may be used for the declared purpose.
- **PARTIAL RUN**: run that did not complete all selected stages.
- **EXECUTION STATE**: operational state such as completed, timed out, cancelled, or launch failed.
- **VALIDATION STATUS**: semantic result such as OK, FAIL, ERROR, or SKIPPED.

---

# 5. Canonical modes

## 5.1 `quick`

Purpose:

> Provide fast, focused feedback during active editing.

Typical use:

- validate one changed GF file;
- validate a small explicitly selected set;
- run static checks;
- compile the selected target;
- detect obvious local breakage;
- optionally execute a lightweight smoke scenario.

`quick` optimizes feedback time.

It is not release evidence.

---

## 5.2 `checkpoint`

Purpose:

> Validate a declared subsystem boundary and its required supporting evidence.

Typical use:

- finish morphology;
- finish one category layer;
- validate an extension family;
- validate a structural layer;
- validate one configured development milestone.

`checkpoint` proves more than one local file.

It validates a project-defined layer through configured checkpoints, relevant dependencies, entrypoint reachability, and applicable scenarios.

It is development evidence, not release evidence.

---

## 5.3 `release`

Purpose:

> Produce complete, reproducible evidence that the selected language context satisfies its declared release contract.

Typical use:

- complete project release validation;
- pre-tag or pre-publication check;
- release candidate verification;
- CI release gate;
- archival validation.

`release` is the only mode that may produce release-eligible success.

Every required stage and artifact must pass.

---

## 5.4 `diagnostic`

Purpose:

> Maximize useful evidence for understanding complex, cascading, intermittent, or poorly classified failures.

Typical use:

- investigate many failing modules;
- distinguish direct and downstream failures;
- inspect complete logs;
- rerun a focused failing area with expanded evidence;
- compare against previous results;
- disable nonessential optimization to improve diagnostics.

`diagnostic` optimizes explanation rather than speed or release eligibility.

It may cover more files than `release`, but it is not automatically release evidence.

---

# 6. Mode comparison

| Capability | `quick` | `checkpoint` | `release` | `diagnostic` |
|---|---:|---:|---:|---:|
| Validate configuration | Required | Required | Required | Required |
| Resolve GF executable and paths | Required | Required | Required | Required |
| GF version probe | Required by default | Required | Required | Required by default |
| Select explicit target | Common | Optional | Not sufficient alone | Optional |
| Select configured checkpoints | No, unless requested | Required | Required | Optional or all |
| Scan selected source files | Required | Required | Required | Required |
| Compile selected files | Required | Required | Required | Required unless explicitly scan-only |
| Compile configured entrypoints | Optional smoke | Required when affected or configured | Required | Optional or all |
| Build PGF | No | Optional | Required when configured | Optional |
| Run required scenarios | Optional smoke only | Applicable checkpoint scenarios | All required release scenarios | Selected or all |
| Run optional scenarios | No by default | Optional | Visible; project policy decides blocking | Common |
| Gold comparison | Only requested smoke | Required where checkpoint declares it | Required where declared | Common |
| Previous-run diff | Optional | Recommended | Required when previous compatible run exists | Recommended |
| Detailed raw evidence | Bounded | Standard | Complete required evidence | Expanded |
| Aggregate reports | Required | Required | Required | Required |
| Manifest verification | Optional | Recommended | Required | Recommended |
| Release-eligible | No | No | Yes | No |
| May weaken required stages | No | No | No | Only through explicit diagnostic subprofile |
| Main optimization | Speed | Milestone confidence | Completeness | Explainability |

---

# 7. Validation stages

The canonical pipeline contains the following semantic stages:

```text
configuration
environment
version_probe
selection
static_scan
fingerprint
compile_files
compile_checkpoints
compile_entrypoints
build_pgf
run_scenarios
normalize_outputs
evaluate_assertions
compare_gold
classify_failures
compare_previous
evaluate_release_gates
write_reports
write_manifest
verify_manifest
```

Not every mode requires every stage.

Stage names are stable semantic identifiers.

Implementation may split or combine internal functions while preserving these observable responsibilities.

---

# 8. Common mandatory preflight

Every mode must begin with common preflight validation.

## 8.1 Project configuration

The run must load one authoritative selected language context from:

```text
<validation-profile-root>/project.toml
```

Required project information must be validated before GF execution.

At minimum, the run must resolve:

- project ID;
- project name;
- language identifier;
- source directory;
- source-selection policy;
- GF path components;
- entrypoints;
- checkpoints;
- scenario registry;
- release requirements.

## 8.2 Environment

The run must resolve:

- workspace root;
- GF executable;
- RGL root or equivalent library path;
- output root;
- working directories;
- required path components.

Required paths must exist before relevant stages begin.

## 8.3 Version probe

GF version probing is required unless the selected mode explicitly permits a documented skip.

`release` must not skip the version probe.

A version below the minimum supported version fails before language validation.

An unknown newer version may warn in non-release modes.

Release handling for an unknown newer version follows the version-compatibility policy.

## 8.4 Run identity

Every run must receive:

- unique run ID;
- start timestamp;
- selected mode;
- resolved resolved language identity;
- resolved environment;
- owned run directory.

## 8.5 Configuration failure

A preflight configuration error produces:

```text
validation_status = ERROR
error_kind = CONFIG
```

No language result should be reported as a GF failure when execution never began.

---

# 9. `quick` mode specification

## 9.1 Intent

`quick` provides the shortest useful evidence loop.

It should answer:

```text
Did the selected local change introduce an obvious source, scan, or compilation problem?
```

## 9.2 Target requirement

A `quick` run must have a bounded target.

Allowed target forms:

```text
one GF file
one GF module
one configured entrypoint
one explicitly named scenario
one small selected file set
changed files supplied by automation
```

When no target is supplied, GF Wordbench may use a documented project quick target.

It must not silently expand to the full project unless the user explicitly requests that behavior.

## 9.3 Required stages

A standard `quick` run requires:

```text
configuration
environment
version_probe
selection
static_scan
fingerprint
compile_files
classify_failures
write_reports
```

When the target is a scenario, the required stages become:

```text
configuration
environment
version_probe
scenario validation prerequisites
run_scenarios
normalize_outputs
evaluate_assertions
compare_gold when declared
write_reports
```

## 9.4 Optional stages

A project may define lightweight quick smoke checks:

- load one entrypoint;
- run one smoke `.gfs`;
- compare one small gold file;
- compile one immediately dependent checkpoint;
- calculate previous-run diff.

These checks remain bounded.

## 9.5 File selection

Selection must include:

- the explicit target;
- any directly required files that the selected stage contract needs;
- no unrelated source files by default.

GF itself remains authoritative for imported dependencies during compilation.

GF Wordbench may compile additional configured dependents only when explicitly requested.

## 9.6 Success criteria

A standard file-target `quick` run succeeds when:

- configuration is valid;
- required environment is available;
- target selection is valid;
- static scanning completes;
- target compilation completes successfully;
- no required quick assertion fails;
- required reports are written.

Scan warnings block success only when project policy classifies them as blocking.

## 9.7 Non-goals

`quick` does not prove:

- checkpoint completeness;
- all entrypoint compilation;
- PGF construction;
- all required scenarios;
- full regression stability;
- release readiness.

## 9.8 Allowed overrides

Allowed:

```text
target
extra target
extra scenario
timeout increase
keep full details
enable previous diff
enable extra compile dependent
strict scan policy
```

Conditionally allowed:

```text
skip version probe
scan-only
no compile
```

These are permitted only for explicitly non-release exploratory use.

When compilation is skipped, the result must state:

```text
compile stage = SKIPPED
quick result is not compilation evidence
```

## 9.9 Prohibited overrides

A `quick` run must not be relabeled as `checkpoint` or `release` after completion.

Adding a PGF build to a `quick` run does not make it release-eligible.

---

# 10. `checkpoint` mode specification

## 10.1 Intent

`checkpoint` validates a configured development boundary.

It should answer:

```text
Is this declared subsystem coherent enough for downstream work to continue?
```

## 10.2 Checkpoint identity

A checkpoint must have a stable configured ID.

Example conceptual IDs:

```text
morphology
noun_phrase
verb_phrase
structural
extend
grammar_entry
```

Actual IDs are profile-owned.

Each checkpoint should define:

- checkpoint ID;
- primary modules;
- prerequisite checkpoints;
- required entrypoints or smoke loads;
- applicable scenarios;
- applicable gold files;
- blocking scan policy;
- expected artifacts;
- completion evidence.

## 10.3 Target requirement

A `checkpoint` run must identify one or more configured checkpoints.

The target must not be an arbitrary undocumented group presented as a checkpoint.

Ad hoc groups may be validated in `quick` or `diagnostic`.

## 10.4 Dependency closure

Checkpoint validation must include its configured prerequisites.

Example:

```text
syntax checkpoint
    requires morphology checkpoint
```

The orchestrator must validate prerequisites in deterministic order.

A failed prerequisite must be represented as a blocker.

Dependent failures should not be misreported as independent root failures.

## 10.5 Required stages

A standard `checkpoint` run requires:

```text
configuration
environment
version_probe
selection
static_scan
fingerprint
compile_files
compile_checkpoints
compile relevant entrypoints
run applicable required scenarios
normalize_outputs
evaluate_assertions
compare declared gold
classify_failures
write_reports
```

Recommended:

```text
compare_previous
write_manifest
verify_manifest
```

## 10.6 Entrypoint reachability

A checkpoint must not be considered complete solely because its internal module compiles.

The project must define one of:

- a downstream entrypoint that consumes the checkpoint;
- a checkpoint-specific smoke grammar;
- a documented reason no entrypoint proof is possible.

## 10.7 Scenario policy

Scenarios may be assigned to checkpoints.

A scenario assigned as required to the selected checkpoint must run and pass.

A scenario assigned only to another checkpoint does not run by default.

Shared scenarios may run for several checkpoints.

## 10.8 Gold policy

A checkpoint gold file is required when the checkpoint contract declares exact normalized output.

A missing required gold file fails the run.

A normal checkpoint run must never update gold.

## 10.9 Success criteria

A checkpoint run succeeds when:

- all selected checkpoints exist;
- all required prerequisites pass;
- all configured checkpoint modules compile;
- required downstream reachability evidence passes;
- all applicable required scenarios pass;
- all required gold comparisons match;
- no checkpoint-blocking known issue remains;
- required reports exist.

## 10.10 Partial checkpoint outcome

A checkpoint run may complete with a failing result.

It must not mark later dependent work as independently failed when the actual result is blocked.

Possible file or checkpoint causal classes include:

```text
direct
downstream
ambiguous
skipped
```

## 10.11 Allowed overrides

Allowed strengthening overrides:

```text
additional checkpoints
additional scenarios
additional entrypoints
strict scan policy
manifest verification
full previous-run diff
expanded evidence
longer timeout
```

Allowed narrowing:

```text
select one checkpoint from the configured set
```

This is not weakening because the mode contract applies to the selected checkpoint and its closure.

## 10.12 Prohibited overrides

Prohibited:

- skipping a required prerequisite;
- skipping a required scenario;
- skipping declared checkpoint gold;
- disabling compilation;
- converting a missing checkpoint to optional;
- accepting a failed downstream reachability check silently.

---

# 11. `release` mode specification

## 11.1 Intent

`release` is the complete project acceptance workflow.

It should answer:

```text
Does the selected language context satisfy every declared release requirement with reproducible evidence?
```

## 11.2 Release authority

Release requirements are defined by:

```text
<validation-profile-root>/project.toml
<validation-profile-root>/docs/VALIDATION_SPEC__PROJECT_DOCS.md
<validation-profile-root>/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
<validation-profile-root>/docs/KNOWN_ISSUES.md
<validation-profile-root>/docs/INTERFILE_CONTRACT_LOCK.md
```

Machine-enforced requirements must have a structured representation.

Human documents may add review obligations but must not conflict with structured release configuration.

## 11.3 Required scope

Release mode includes the complete configured release scope:

- all required source selections;
- all required checkpoints;
- all required entrypoints;
- all required scenarios;
- all required gold comparisons;
- all required PGF targets;
- all required artifact checks;
- all required schemas;
- all required reports;
- manifest verification.

A target-file override cannot reduce this scope.

## 11.4 Required stages

A standard `release` run requires:

```text
configuration
environment
version_probe
selection
static_scan
fingerprint
compile_files
compile_checkpoints
compile_entrypoints
build_pgf when configured
run_scenarios
normalize_outputs
evaluate_assertions
compare_gold
classify_failures
compare_previous when compatible history exists
evaluate_release_gates
write_reports
write_manifest
verify_manifest
```

## 11.5 GF version policy

Release mode must record:

- executable used;
- GF version;
- supported-version decision;
- GF path;
- command evidence.

Known incompatible versions fail.

A version below the minimum fails.

An unknown newer version may proceed only when the compatibility policy explicitly permits release under warning or exception.

## 11.6 Static scan policy

Every release-selected source file must be scanned.

Project-defined blocking patterns fail release.

Nonblocking warnings remain visible.

A scan pass does not substitute for GF compilation.

## 11.7 Compilation policy

Every required checkpoint and entrypoint must compile.

A release run must not rely solely on stale `.gfo` artifacts.

Required compilation must occur in the current run or through a verified cache contract that proves source-equivalent freshness.

No such cache may be assumed implicitly.

## 11.8 PGF policy

When the project declares a PGF release target:

- the PGF build must run;
- command execution must succeed;
- no fatal diagnostic may remain;
- expected `.pgf` must exist;
- the artifact must be nonempty;
- it must be registered in the manifest;
- its size and hash must be recorded;
- optional load verification should run when configured.

Individual `.gfo` success is insufficient.

## 11.9 Scenario policy

Every required release scenario must:

- exist;
- be registered;
- execute with finite timeout;
- complete required markers;
- satisfy required assertions;
- produce required artifacts;
- pass required gold comparison.

A missing required scenario is a release failure.

An optional scenario may warn or fail without blocking only when project release policy explicitly permits it.

Its result must remain visible.

## 11.10 Gold policy

Every required gold comparison must match.

Normal release validation must never modify gold.

A mismatch is a release failure until:

1. the source or specification change is reviewed;
2. the new output is judged acceptable;
3. gold is updated through an explicit workflow;
4. release validation is rerun.

## 11.11 Previous-run comparison

When a compatible previous release or release candidate exists, release mode should compare against it.

Regressions must remain visible.

A configured regression gate may block release.

Absence of previous history does not automatically fail the first release, but it must be reported.

## 11.12 Known-issue policy

Every known issue affecting release must have an explicit release disposition.

Release fails when:

- a release-blocking issue remains unresolved;
- a required function remains unavailable;
- an undocumented warning appears where project policy requires registration;
- a temporary fallback violates release criteria;
- a disabled required capability remains.

Accepted nonblocking issues and their dispositions must be listed in release evidence.

## 11.13 Schema and manifest policy

Release mode must validate:

- project schema;
- run summary schema;
- scenario-output schema;
- gold headers where applicable;
- artifact manifest;
- required artifact existence;
- artifact hashes.

A malformed release summary or manifest makes the run ineligible even when GF stages passed.

## 11.14 Success criteria

A release run succeeds only when:

```text
all required preflight checks pass
and all required scans pass policy
and all required compilations pass
and all required checkpoints pass
and all required entrypoints pass
and all required PGF builds pass
and all required scenarios pass
and all required assertions pass
and all required gold comparisons match
and all release gates pass
and all required artifacts exist
and all required reports are written
and manifest verification passes
```

## 11.15 Release eligibility

A run is release-eligible only when:

```text
mode = release
overall_status = OK
execution_state = completed
partial = false
release_gates_passed = true
manifest_verified = true
```

A successful `diagnostic`, `checkpoint`, or `quick` run is never automatically release-eligible.

## 11.16 Prohibited overrides

Release mode must reject:

```text
--no-compile
--scan-only
--skip-required-scenarios
--skip-required-gold
--skip-required-pgf
--skip-manifest
--skip-version-probe
--ignore-blocking-issues
--target-file as scope reduction
```

Equivalent GUI controls are prohibited.

## 11.17 Explicit release exceptions

A release exception may exist only when:

- project policy defines exception handling;
- the exception has a stable ID;
- affected gate is identified;
- owner is identified;
- reason is documented;
- expiration or review condition exists;
- reports include the exception;
- release status distinguishes normal pass from pass-with-exception.

The default policy treats release exceptions as failures unless a deliberate project governance decision enables them.

---

# 12. `diagnostic` mode specification

## 12.1 Intent

`diagnostic` maximizes causal and technical evidence.

It should answer:

```text
What failed, where did it first fail, what is blocked by it, and what evidence explains the failure?
```

## 12.2 Scope forms

Diagnostic mode may target:

```text
one file
one module
one checkpoint
one entrypoint
one scenario
all selected files
all checkpoints
all scenarios
a previous regression
a known failing dependency chain
```

## 12.3 Default scope

When no explicit target is provided, diagnostic mode may select the complete project validation inventory.

This behavior must be visible before execution.

### 12.3.1 Path-resolved GUI Global Scan

The desktop GUI maps `Diagnostic` with no explicit source target to **Global
Scan**. This is a Diagnostic scope form, not a fifth validation mode. It selects
the complete resolved source inventory (subject to `max_files`) and executes
independent per-source scan/compile work without fail-fast behavior.

The inventory records every selected source even when earlier sources fail.
Causal classification may mark a failed source as `downstream` when compiler
evidence identifies another failed module as its blocker; otherwise the failure
remains `direct` or `ambiguous` according to available evidence.

Global Scan writes expanded machine-readable inventory views under `details/`
while preserving the canonical raw scan and compile streams. A validation FAIL
does not mean that the scan execution itself aborted.

## 12.4 Required stages

A standard diagnostic run requires:

```text
configuration
environment
version_probe
selection
static_scan
fingerprint
compile selected scope
classify_failures
write expanded reports
```

Depending on target and options, it commonly includes:

```text
compile_checkpoints
compile_entrypoints
build_pgf
run_scenarios
normalize_outputs
evaluate_assertions
compare_gold
compare_previous
write_manifest
```

## 12.5 Evidence level

Diagnostic mode should preserve:

- full structured command;
- working directory;
- environment overrides;
- stdout;
- stderr;
- duration;
- timeout state;
- launch state;
- scan details;
- source fingerprints;
- primary and detailed diagnostics;
- blocker candidates;
- dependency evidence;
- normalized scenario output;
- gold diff;
- previous-run diff;
- complete detail reports.

Output-size limits still apply.

Any truncation must be explicit.

## 12.6 Continue-after-failure policy

Diagnostic mode should continue after independent failures when safe.

It may:

- compile additional files;
- run unrelated scenarios;
- gather dependency evidence;
- preserve several root failures.

It must not continue when doing so would:

- corrupt evidence;
- violate process safety;
- exceed configured limits;
- depend on missing mandatory preflight;
- execute an untrusted prohibited command.

## 12.7 Optimization policy

Diagnostic mode may disable nonessential PGF optimization when this improves diagnostic clarity.

Any command difference from release mode must be recorded.

A nonoptimized diagnostic PGF is not release evidence.

## 12.8 Scenario policy

Diagnostic mode may run:

- one failing scenario;
- all scenarios;
- optional introspection scenarios;
- bounded generation;
- morphology inspection;
- missing-linearization checks.

Random or unstable output should not be exact-gold compared unless deterministic seeding and normalization are defined.

## 12.9 Gold behavior

Diagnostic mode may compare gold and produce detailed diffs.

It must not update gold during normal execution.

## 12.10 No-compile and scan-only subprofiles

Diagnostic mode may support explicit subprofiles:

```text
diagnostic --scan-only
diagnostic --no-compile
diagnostic --scenario-only
diagnostic --compile-only
```

These are evidence-gathering workflows.

They must record every skipped stage explicitly.

They are never release-eligible.

## 12.11 Success semantics

Diagnostic mode may finish successfully as an execution even when validation failures are found.

The system must keep separate:

```text
execution completed successfully
validation found failures
```

Canonical interpretation:

- `execution_state = completed` means the requested diagnostic workflow finished;
- `validation_status = FAIL` means selected validation criteria failed;
- `validation_status = ERROR` means the workflow could not evaluate required criteria.

CLI exit codes should still distinguish found failures from framework execution errors.

## 12.12 Allowed overrides

Diagnostic mode permits the broadest explicit control:

- select target scope;
- include or exclude optional scenarios;
- scan-only;
- compile-only;
- scenario-only;
- skip version probe where policy permits;
- increase detail retention;
- alter bounded generation limits;
- extend timeout;
- disable PGF optimization;
- compare chosen previous run;
- continue after independent failures.

Overrides must be persisted in run metadata.

## 12.13 Prohibited behavior

Diagnostic mode must not:

- claim release eligibility;
- rewrite gold automatically;
- suppress raw evidence;
- hide skipped stages;
- turn a failed criterion into OK;
- execute without finite timeouts;
- use a different hidden GF path.

---

# 13. Stage requirement matrix

Legend:

```text
R = required
C = conditional on project or selected target
O = optional
P = prohibited as a normal mode behavior
```

| Stage | `quick` | `checkpoint` | `release` | `diagnostic` |
|---|---:|---:|---:|---:|
| Configuration validation | R | R | R | R |
| Environment resolution | R | R | R | R |
| GF version probe | R | R | R | R/O by explicit policy |
| Deterministic selection | R | R | R | R |
| Static scan | R | R | R | R |
| Fingerprinting | R | R | R | R |
| Selected-file compile | R | R | R | R/C |
| Checkpoint compile | O | R | R | C |
| Entrypoint compile | C | R/C | R | C |
| PGF build | P/O explicit | C | R when configured | C |
| Required scenarios | C smoke | R for checkpoint | R all | C |
| Optional scenarios | P/O explicit | O | C visible | O/common |
| Output normalization | C | R when scenario uses it | R | C |
| Assertion evaluation | C | R when declared | R | C |
| Gold comparison | C | R when declared | R when declared | C |
| Failure classification | R | R | R | R |
| Previous-run diff | O | O/recommended | R when compatible history exists | O/recommended |
| Release-gate evaluation | P | P | R | O informational |
| Human summary | R | R | R | R |
| Machine summary | R | R | R | R |
| AI-ready report | O | O | R | R |
| Manifest write | O | O/recommended | R | O/recommended |
| Manifest verify | O | O | R | O |

---

# 14. Evidence levels

Each mode has a default evidence level.

```text
quick       = bounded
checkpoint  = standard
release     = complete
diagnostic  = expanded
```

## 14.1 Bounded evidence

Includes:

- selected file results;
- scan counts;
- compile summary;
- primary diagnostics;
- raw stdout/stderr for failures;
- basic reports.

Successful target details may be compacted according to policy.

## 14.2 Standard evidence

Includes:

- all selected module evidence;
- checkpoint relationships;
- required scenario evidence;
- relevant gold diffs;
- classification;
- standard reports.

## 14.3 Complete evidence

Includes:

- full required-run configuration;
- all required stage evidence;
- all required raw streams;
- required artifacts;
- hashes;
- schema identifiers;
- release gates;
- manifest;
- AI-ready report.

## 14.4 Expanded evidence

Includes:

- complete raw streams where limits permit;
- additional parsing detail;
- dependency and blocker evidence;
- optional scenarios;
- comparison details;
- diagnostic-only metadata.

Evidence level affects retention and detail.

It must not alter validation truth.

---

# 15. Target model

A mode may receive one or more typed targets.

Canonical target kinds:

```text
file
module
checkpoint
entrypoint
scenario
project
regression
```

Target identity must be explicit.

Examples:

```text
file:lib/src/language/NounX.gf
checkpoint:morphology
entrypoint:GrammarX
scenario:parse-basic
project:<project-id>
```

Free-form ambiguous target strings should be resolved before orchestration.

Release mode always resolves to the project release target set.

---

# 16. Scenario applicability

A scenario should declare applicable modes or purposes.

Recommended scenario metadata includes:

```text
scenario_id
required
applicable_modes
checkpoint_ids
entrypoint
gold_path
timeout_class
assertion_profile
```

Example conceptual mapping:

| Scenario | Quick | Checkpoint | Release | Diagnostic |
|---|---:|---:|---:|---:|
| load smoke | Optional | Required for relevant checkpoint | Required | Optional |
| missing linearizations | No | Optional | Required | Common |
| representative linearization | Optional | Required | Required | Common |
| representative parse | No | Optional | Required | Common |
| bounded generation | No | Optional | Optional/required by policy | Common |
| morphology introspection | No | Optional | Optional | Common |

The selected language context owns the actual mapping.

Framework defaults must not hardcode one language’s scenario IDs.

---

# 17. Required and optional scenarios

## 17.1 Required scenario

A required applicable scenario that is:

- missing;
- unreadable;
- timed out;
- incomplete;
- marker-invalid;
- assertion-failing;
- gold-mismatching;

fails the applicable mode.

## 17.2 Optional scenario

An optional scenario result must remain visible.

Project policy defines whether:

- failure is informational;
- failure produces warning status;
- failure blocks release.

A scenario must not become effectively required through hidden report logic.

## 17.3 Mode promotion

A caller may promote an optional scenario to required for one run.

A caller must not demote a required scenario in `checkpoint` or `release`.

---

# 18. Scan policy by mode

## 18.1 Separation from compilation

Static scan findings and GF compile results remain separate.

## 18.2 Quick

Scan selected targets.

Use fast bounded detail.

## 18.3 Checkpoint

Scan all source files owned by the selected checkpoint and prerequisites.

## 18.4 Release

Scan the complete release-selected source set.

Apply all release-blocking scan rules.

## 18.5 Diagnostic

Scan the selected diagnostic scope.

Preserve expanded hit detail.

## 18.6 Blocking policy

A scan rule must declare severity:

```text
info
warning
error
```

Mode policy determines blocking:

| Severity | Quick | Checkpoint | Release | Diagnostic |
|---|---:|---:|---:|---:|
| `info` | visible | visible | visible | visible |
| `warning` | project policy | project policy | visible; policy may block | visible |
| `error` | blocks selected target | blocks | blocks | validation FAIL |

---

# 19. Compilation policy by mode

## 19.1 Quick compilation

Compile the selected target.

May stop after the first direct target failure.

## 19.2 Checkpoint compilation

Compile prerequisites and checkpoint modules in deterministic order.

Continue enough to classify independent and downstream failures.

## 19.3 Release compilation

Compile all required checkpoints and entrypoints.

Failure does not permit omission of remaining evidence unless continuing is unsafe or meaningless.

Skipped stages must be recorded.

## 19.4 Diagnostic compilation

May compile broadly to expose causal structure.

May continue after failure.

May preserve complete output.

## 19.5 Compilation omission

Compilation omission is permitted only for an explicit non-release diagnostic or quick exploratory subprofile.

It must never be the default behavior of a canonical mode.

---

# 20. Previous-run comparison

## 20.1 Compatible comparison

Comparison requires compatible structured summaries.

At minimum, comparison must consider:

- schema compatibility;
- resolved language identity;
- subject identity;
- relevant mode or target context.

## 20.2 Quick

Diff is optional and normally compares the same target when available.

## 20.3 Checkpoint

Diff is recommended and should compare the same checkpoint scope.

## 20.4 Release

Diff is required when a compatible previous release or release candidate exists.

## 20.5 Diagnostic

The caller may select a specific previous run.

## 20.6 Missing history

Missing history is not a failure unless project policy explicitly requires a baseline.

Reports must state that no compatible baseline was available.

---

# 21. Status semantics

Modes do not redefine status values.

Canonical validation statuses:

```text
OK
FAIL
ERROR
SKIPPED
```

Canonical execution states:

```text
completed
timed_out
cancelled
launch_failed
```

Canonical causal diagnostic classes:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

These dimensions must remain distinct.

Example:

```text
mode = diagnostic
execution_state = completed
validation_status = FAIL
diagnostic_class = direct
```

This means the diagnostic run completed and found a direct validation failure.

---

# 22. Overall outcome rules

## 22.1 `OK`

The selected mode’s complete required contract passed.

## 22.2 `FAIL`

Execution completed sufficiently to evaluate required criteria, and one or more criteria failed.

Examples:

- GF compile failure;
- blocking scan finding;
- scenario assertion failure;
- gold mismatch;
- release gate failure;
- missing required artifact discovered after execution.

## 22.3 `ERROR`

The system could not reliably evaluate the required contract.

Examples:

- invalid configuration;
- GF launch failure;
- unreadable required source;
- internal framework exception;
- malformed required schema;
- unusable output directory.

## 22.4 `SKIPPED`

A stage or subject was deliberately not executed under an allowed policy.

A complete canonical run should not use `SKIPPED` to hide required work.

---

# 23. Cancellation and partial runs

A cancelled run must preserve completed evidence.

Run metadata must record:

```text
execution_state = cancelled
partial = true
```

A partial run is never release-eligible.

Reports must distinguish:

- user cancellation;
- timeout;
- launch failure;
- validation failure.

A cancelled `quick`, `checkpoint`, or `diagnostic` run may still provide useful evidence.

Its overall validation status must not be presented as a complete mode pass.

---

# 24. Timeouts

Every external execution has a finite timeout.

Modes may select different timeout classes:

```text
version_probe
file_compile
checkpoint_compile
entrypoint_compile
pgf_build
scenario
generation
diagnostic_introspection
```

Default tendency:

```text
quick       shortest practical timeout
checkpoint  standard timeout
release     complete but finite timeout
diagnostic  configurable extended timeout
```

A timeout is not a normal GF compile failure.

It must be represented explicitly.

Increasing a timeout is a strengthening or neutral override.

Setting an infinite timeout is prohibited.

---

# 25. Mode selection precedence

Mode resolution follows this order:

1. explicit CLI or GUI selection;
2. explicit automation configuration;
3. documented project default;
4. framework default.

Recommended framework default:

```text
quick
```

for an explicit target, otherwise:

```text
diagnostic
```

only when the interface clearly shows that the project-wide diagnostic scope will run.

A default must never silently choose `release`.

---

# 26. Configuration ownership

## 26.1 Framework-owned semantics

The framework owns the semantic meaning of:

```text
quick
checkpoint
release
diagnostic
```

A project may configure content for each mode.

It must not redefine the meaning so radically that the same mode name becomes incompatible.

## 26.2 Profile-owned content

The project owns:

- checkpoint inventory;
- entrypoint inventory;
- scenario registry;
- scenario applicability;
- release targets;
- blocking scan rules;
- required artifacts;
- known-issue policy;
- project release gates.

## 26.3 Interface-owned selection

CLI and GUI own only the user’s mode and target selection.

They do not own mode semantics.

---

# 27. Override model

Overrides must be classified before application.

## 27.1 Strengthening overrides

Examples:

- add scenarios;
- add targets;
- enable strict scan;
- verify manifest;
- retain more evidence;
- compare additional baseline;
- compile additional entrypoints.

Allowed in every mode.

## 27.2 Neutral overrides

Examples:

- output root;
- timeout increase;
- report display preference;
- CPU timing capture;
- detail retention;
- explicit equivalent GF executable.

Allowed when valid.

## 27.3 Weakening overrides

Examples:

- skip compile;
- skip version probe;
- skip required scenario;
- skip gold;
- skip PGF;
- ignore required artifact;
- disable release gate.

Allowed only where this document explicitly permits exploratory non-release use.

## 27.4 Override recording

Every nondefault override affecting validation must appear in:

- resolved run configuration;
- `summary.json`;
- human summary;
- AI-ready report when diagnostically relevant.

---

# 28. CLI requirements

The CLI should expose canonical mode names directly.

Conceptual examples:

```text
gf-wordbench validate --mode quick --target file:path/to/File.gf
gf-wordbench validate --mode checkpoint --target checkpoint:morphology
gf-wordbench validate --mode release
gf-wordbench validate --mode diagnostic --target entrypoint:GrammarX
```

The exact syntax is owned by `CLI_REFERENCE.md`.

CLI validation must reject invalid combinations before execution.

Examples:

```text
release + no_compile                 invalid
release + skip_version_probe         invalid
checkpoint + unknown checkpoint      invalid
quick + no target and no project default  invalid
```

---

# 29. GUI requirements

The GUI must:

- show the selected mode;
- explain its purpose;
- show resolved target scope;
- disable prohibited override controls;
- display required stages before execution;
- warn when a non-release mode cannot prove release readiness;
- preserve parity with CLI configuration;
- show skipped stages in results;
- display release eligibility separately from run completion.

The GUI must not provide a hidden “force success” control.

---

# 30. Automation and CI

Recommended CI roles:

```text
pull request focused check     → quick or checkpoint
subsystem milestone            → checkpoint
nightly broad investigation    → diagnostic
release candidate              → release
```

CI must archive the run directory or required evidence according to retention policy.

A CI job named “release” must execute `mode = release`.

It must not use `quick` or `diagnostic` and infer release readiness externally.

---

# 31. Legacy mode migration

The predecessor system used:

```text
file
all
```

Canonical migration aliases:

```text
file → quick
all  → diagnostic
```

These aliases exist only for migration and backward-compatible input.

Canonical writers must emit:

```text
quick
checkpoint
release
diagnostic
```

Legacy aliases must not appear in new:

- project configuration;
- application state;
- run summaries;
- CLI help;
- GUI selections;
- documentation examples.

A migrated `all` run is not retroactively release-eligible.

---

# 32. Persistence requirements

Run summaries must persist:

```text
mode
target kind
target identity
resolved scope
selected stages
required stages
skipped stages
overrides
evidence level
release eligibility
```

Application state may remember the last selected mode.

It must not persist `release` as an automatic unattended default without explicit product policy.

Mode values are governed by the persisted schema lock.

---

# 33. Report requirements

Every report must identify:

- mode;
- target;
- project;
- completed stages;
- skipped stages;
- validation status;
- execution state;
- release eligibility;
- relevant overrides.

## 33.1 Quick report

Focus on:

- target;
- scan findings;
- compile result;
- primary diagnosis;
- next useful evidence.

## 33.2 Checkpoint report

Focus on:

- checkpoint;
- prerequisites;
- module results;
- downstream reachability;
- scenarios;
- completion status.

## 33.3 Release report

Focus on:

- all release gates;
- entrypoints;
- PGF artifacts;
- required scenarios;
- gold comparisons;
- known issues;
- regressions;
- manifest verification;
- release eligibility.

## 33.4 Diagnostic report

Focus on:

- root-cause candidates;
- downstream failures;
- ambiguous failures;
- raw evidence;
- comparison details;
- skipped or narrowed stages.

Reports derive from structured results.

They must not infer missing mode metadata from folder names.

---

# 34. Mode transition guidance

Typical progression:

```text
quick
  ↓
checkpoint
  ↓
release
```

Diagnostic mode may be entered from any stage:

```text
quick failure       → diagnostic
checkpoint failure  → diagnostic
release failure     → diagnostic
```

After diagnostic fixes, the original proving mode must be rerun.

Examples:

```text
release fails
→ diagnostic identifies root cause
→ sources are fixed
→ release must run again
```

A successful diagnostic rerun does not replace the failed release run.

---

# 35. Mode anti-drift rules

The following are prohibited:

- defining different mode semantics in CLI and GUI;
- treating `diagnostic` as synonymous with `release`;
- treating `quick` as the old `file` mode without target validation;
- treating `checkpoint` as an arbitrary file list;
- allowing release mode to skip required scenarios;
- allowing UI state to override release policy;
- hiding skipped stages from reports;
- using mode name only as an evidence-detail preference;
- changing scenario applicability in a report writer;
- letting one stage inspect raw CLI arguments;
- marking a partial run as mode success;
- promoting a run to release eligibility after completion;
- persisting legacy aliases in canonical summaries;
- updating gold automatically in any mode;
- treating zero process exit as complete scenario success;
- treating individual `.gfo` success as release completion.

---

# 36. Required tests

Recommended tests:

```text
tests/validation/test_mode_quick.py
tests/validation/test_mode_checkpoint.py
tests/validation/test_mode_release.py
tests/validation/test_mode_diagnostic.py
tests/validation/test_mode_overrides.py
tests/validation/test_mode_migration.py
tests/validation/test_mode_reports.py
tests/validation/test_release_eligibility.py
```

## 36.1 Quick tests

- explicit file target;
- missing target;
- target compile success;
- target compile failure;
- scan warning;
- scan-only explicit subprofile;
- quick smoke scenario;
- cannot become release-eligible.

## 36.2 Checkpoint tests

- valid checkpoint;
- unknown checkpoint;
- prerequisite closure;
- failed prerequisite;
- required checkpoint scenario;
- missing checkpoint gold;
- downstream classification;
- prohibited no-compile override.

## 36.3 Release tests

- complete release success;
- missing required scenario;
- missing PGF;
- zero exit with missing artifact;
- gold mismatch;
- blocking known issue;
- malformed manifest;
- prohibited skip flags;
- cancelled release;
- release eligibility only after verified success.

## 36.4 Diagnostic tests

- project-wide default scope;
- focused target;
- continue after independent failures;
- expanded evidence;
- scan-only;
- compile-only;
- scenario-only;
- nonoptimized PGF;
- never release-eligible.

## 36.5 Migration tests

- `file` loads as `quick`;
- `all` loads as `diagnostic`;
- canonical writer emits no legacy alias;
- migrated `all` is not release-eligible.

---

# 37. Automated validation

The contract checker should verify:

```text
gf-wordbench contracts check
```

Mode-specific checks should include:

1. exactly four canonical mode names exist;
2. CLI and GUI use the same mode enum;
3. persisted schema accepts canonical names;
4. canonical writers reject legacy output names;
5. release mode cannot enable weakening flags;
6. required release stages are present;
7. checkpoint targets resolve from project configuration;
8. quick mode validates bounded target scope;
9. diagnostic partial profiles mark skipped stages;
10. only successful release mode can set release eligibility;
11. reports display mode and release eligibility;
12. normal validation never updates gold.

---

# 38. Change policy

Changing mode semantics is an architectural contract change.

A change requires:

```text
[ ] Mode affected
[ ] Problem and use case documented
[ ] Stage matrix reviewed
[ ] Override impact reviewed
[ ] CLI impact reviewed
[ ] GUI impact reviewed
[ ] Project configuration impact reviewed
[ ] Persisted schema impact reviewed
[ ] Report impact reviewed
[ ] Release eligibility impact reviewed
[ ] Migration defined
[ ] Tests updated
[ ] ADR created or updated
[ ] This document updated
```

Adding a fifth canonical mode requires an ADR.

A new mode is justified only when its validation purpose cannot be expressed clearly as:

- a target;
- an evidence level;
- a strengthening override;
- a diagnostic subprofile;
- a project-defined checkpoint.

---

# 39. Decision guide

Use `quick` when:

```text
the question is local
the target is bounded
fast feedback matters
release proof is not required
```

Use `checkpoint` when:

```text
a declared subsystem milestone must be proven
prerequisites and downstream reachability matter
checkpoint scenarios or golds apply
```

Use `release` when:

```text
the project must be declared releasable
all required evidence must be complete
PGF, scenarios, gates, and manifest must be verified
```

Use `diagnostic` when:

```text
the cause is unclear
several failures cascade
expanded raw evidence is needed
the run must continue after independent failures
a partial exploratory profile is required
```

---

# 40. Mode contract

The canonical mode set is:

```text
quick
checkpoint
release
diagnostic
```

Their meanings are:

```text
quick       = focused development feedback
checkpoint  = declared subsystem proof
release     = complete release proof
diagnostic  = expanded failure investigation
```

The mode invariants are:

```text
mode semantics are shared by CLI, GUI, and automation
project configuration supplies content, not incompatible meanings
required checks cannot be silently weakened
all skips are explicit
release is the only release-eligible mode
diagnostic does not replace release
gold is never updated by normal validation
execution state remains separate from validation status
legacy file/all names are migration aliases only
```

A mode is correct only when its name, selected stages, evidence, success criteria, and persisted result all describe the same validation contract.
