# GF Wordbench — Execution Flow

**Document ID:** `GF-WB-ARCH-EXECUTION-FLOW`  
**Status:** Normative architecture specification  
**Applies to:** GF Wordbench framework  
**Primary entry point:** `app/audit/audit_core.py::run_audit(...)`  
**Owner:** GF Wordbench maintainers  
**Last structural review:** 2026-07-22  

---

## 1. Purpose

This document defines the canonical execution flow of GF Wordbench from user request to finalized run artifacts.

It answers:

- where execution begins;
- how configuration is resolved;
- how the active project is loaded;
- how validation mode selects stages;
- when files are selected, scanned, fingerprinted, and compiled;
- when scenarios and gold comparisons run;
- when a PGF release build runs;
- how results are classified and aggregated;
- how previous runs are compared;
- how reports and manifests are finalized;
- how partial failures, timeouts, and cancellation are represented;
- what CLI and GUI layers may and may not do.

This file describes orchestration order and stage boundaries.

It does not duplicate:

- GF command syntax;
- persisted field-by-field schemas;
- file-to-file public contracts;
- language-specific module dependencies;
- report layout details.

Those are owned by the corresponding contract and reference documents.

---

## 2. Core execution rule

> Every supported validation request must pass through one authoritative orchestration flow.

The authoritative application-level entry point is:

```python
run_audit(
    run_config: RunConfig,
    run_paths: RunPaths | None = None,
) -> RunResult
```

Equivalent resolved configuration must produce equivalent stage selection, ordering, and success semantics regardless of whether the request originates from:

- the CLI;
- the GUI;
- automation;
- tests;
- a future supported API wrapper.

CLI and GUI code must not reconstruct the pipeline independently.

---

## 3. Execution authority

### 3.1 CLI and GUI own interaction

The CLI and GUI own:

- collecting user input;
- presenting validation errors before execution when possible;
- calling the shared configuration builder;
- calling `run_audit`;
- presenting the returned result;
- mapping the final result to an exit code or GUI state.

They do not own:

- file selection rules;
- scanner invocation;
- GF process invocation;
- scenario execution;
- classification;
- regression comparison;
- report generation;
- artifact naming.

### 3.2 Bootstrap owns resolved configuration and run paths

Bootstrap and project-configuration loading own:

- application defaults;
- active project loading;
- explicit override precedence;
- path resolution;
- configuration validation;
- creation of `RunConfig`;
- creation of `RunPaths`.

### 3.3 Audit core owns orchestration

The audit core owns:

- stage ordering;
- stage inclusion by mode;
- partial-result preservation;
- aggregation;
- report finalization;
- final run status.

### 3.4 Stages own their local work

Each stage owns one bounded responsibility:

| Stage | Responsibility |
|---|---|
| Project loader | Read and validate `project/project.toml` |
| File selector | Determine included and excluded GF source files |
| Scanner | Produce heuristic source findings |
| Fingerprint provider | Produce source identity |
| Compiler | Invoke GF for file compilation |
| Classifier | Determine direct, downstream, ambiguous, noise, skipped |
| Scenario runner | Execute project-owned `.gfs` scenarios |
| Gold comparator | Compare normalized scenario output with reviewed gold |
| PGF build stage | Build and verify the release PGF |
| Diff stage | Compare with a prior structured run |
| Result builder | Construct coherent result models and totals |
| Report writers | Serialize existing evidence |
| Manifest writer | Inventory finalized run artifacts |

No stage may silently assume ownership of another stage's behavior.

---

## 4. Canonical high-level flow

```text
User / automation
        |
        v
CLI or GUI
        |
        v
Load application defaults
        |
        v
Load active project configuration
        |
        v
Apply explicit overrides
        |
        v
Validate and resolve RunConfig
        |
        v
run_audit(...)
        |
        +--> Build or accept RunPaths
        |
        +--> Initialize run context and master evidence
        |
        +--> External-tool preflight
        |
        +--> Resolve mode-specific execution plan
        |
        +--> Select source files
        |
        +--> Execute per-file pipeline
        |       scan
        |       fingerprint
        |       compile or skip
        |       build FileResult
        |
        +--> Classify file results
        |
        +--> Execute selected scenarios
        |       run GF
        |       preserve raw output
        |       verify markers
        |       normalize
        |       compare gold
        |       build ScenarioResult
        |
        +--> Build PGF when required
        |
        +--> Build aggregate RunResult
        |
        +--> Compare with previous structured run
        |
        +--> Write reports and aggregate logs
        |
        +--> Write and verify manifest
        |
        +--> Finalize overall status
        |
        v
Return RunResult
        |
        +--> CLI prints summary and returns exit code
        |
        +--> GUI renders result and persists convenience state
```

---

## 5. Flow phases

The execution flow is divided into twelve phases.

```text
Phase 0   Request intake
Phase 1   Configuration resolution
Phase 2   Run initialization
Phase 3   External-tool preflight
Phase 4   Execution-plan resolution
Phase 5   Source selection
Phase 6   Per-file validation
Phase 7   Cross-file classification
Phase 8   Scenario validation
Phase 9   PGF and release gates
Phase 10  Aggregation and regression comparison
Phase 11  Reporting, manifest, and completion
```

A phase may contain multiple stages, but phase order is stable.

---

# 6. Phase 0 — Request intake

## 6.1 CLI path

Canonical logical flow:

```text
parse arguments
    -> convert values to plain Python types
    -> call shared configuration builder
    -> call run_audit
    -> print returned result summary
    -> map result to process exit code
```

The CLI must not determine success by parsing generated reports.

The CLI must use structured fields on `RunResult`.

## 6.2 GUI path

Canonical logical flow:

```text
read form and persisted convenience state
    -> validate obvious UI errors
    -> convert widget values to plain Python types
    -> call shared configuration builder
    -> call run_audit in the supported execution context
    -> render returned result
    -> save convenience state
```

The GUI must not call:

- `compile_file`;
- `scan_file`;
- scenario execution;
- report writers;
- manifest generation.

GUI validation may fail earlier than bootstrap, but it must not replace bootstrap validation.

## 6.3 Automation path

Automation must use the same public configuration and audit entry points.

It may:

- disable interactive output;
- select strict mode;
- choose deterministic output roots;
- inspect `summary.json`;
- use exit codes.

It must not bypass required release gates.

---

# 7. Phase 1 — Configuration resolution

## 7.1 Configuration sources

Configuration is resolved from these domains:

```text
application metadata and safe framework defaults
active project configuration
environment-specific tool paths
CLI or GUI explicit overrides
documented compatibility aliases
```

The active project configuration is authoritative for:

- project identity;
- language identity;
- source directory;
- source glob and filters;
- GF path parts owned by the project;
- entrypoints;
- checkpoints;
- required scenarios;
- optional scenarios;
- release requirements.

The application state is not authoritative project configuration.

## 7.2 Precedence

Recommended precedence from lowest to highest:

```text
1. framework-safe defaults
2. active project configuration
3. environment-specific configured values
4. explicit CLI or GUI values
```

Correctness-critical values must not rely silently on inherited environment variables.

Explicit values may override project defaults only where the project contract permits it.

Required release constraints must not be bypassed silently.

## 7.3 Compatibility aliases

Legacy aliases may be accepted at input or migration boundaries:

```text
file -> quick
all  -> diagnostic
```

Canonical resolved modes are:

```text
quick
checkpoint
release
diagnostic
```

Canonical writers and reports must emit canonical mode values only.

## 7.4 Configuration validation

Validation occurs before external execution.

At minimum, validate:

- project root exists;
- active project configuration exists and is readable;
- schema ID and schema version are supported;
- source directory is valid;
- GF executable resolves;
- RGL root is valid when required;
- output root is permitted and writable;
- timeout values are positive;
- mode is supported;
- target file is present when required;
- entrypoints and checkpoints are deterministic;
- required scenario IDs are unique;
- required scenario files exist;
- required gold files exist where the project contract requires them;
- project-owned paths remain inside the project root;
- run-owned paths remain inside the output root.

A configuration failure before run-path creation normally produces no run directory.

A configuration failure after run-path creation must be represented in the partial run evidence.

## 7.5 Resolved configuration

The output of configuration resolution is one immutable logical request:

```text
RunConfig
```

Once execution begins, stages must read the resolved configuration.

They must not independently consult:

- GUI widgets;
- command-line parser objects;
- mutable application state;
- undeclared environment values;
- language-specific framework constants.

---

# 8. Phase 2 — Run initialization

## 8.1 Run path creation

Unless explicitly supplied by a test or supported embedding layer:

```python
run_paths = build_run_paths(run_config)
```

The builder creates a unique run directory.

Canonical shape:

```text
run_<run-id>/
├── summary.json
├── summary.md
├── AI_READY.md
├── top_errors.txt
├── manifest.json
├── details/
├── raw/
│   ├── master.log
│   ├── ALL_SCAN_LOGS.TXT
│   ├── ALL_LOGS.TXT
│   ├── compile/
│   ├── scan/
│   └── scenarios/
└── artifacts/
    ├── gfo/
    ├── out/
    └── pgf/
```

A stage must use paths supplied by `RunPaths`.

It must not invent an alternate run filename or directory.

## 8.2 Run identity

The run receives:

- a unique `run_id`;
- a UTC start timestamp;
- a monotonic start clock;
- a resolved run directory;
- initialized evidence collections.

The wall-clock timestamp is for persisted metadata.

The monotonic clock is for duration measurement.

## 8.3 Initial evidence

The master evidence should record:

- run ID;
- canonical mode;
- project ID;
- project root;
- resolved GF executable;
- effective GF path;
- RGL root;
- output root;
- run directory;
- timeout policy;
- target file when applicable;
- enabled and disabled stages;
- strict-mode state.

Secrets and full environment dumps are prohibited.

## 8.4 Initial in-memory collections

The orchestrator initializes deterministic collections for:

```text
file_results
scenario_results
diff_entries
top_errors
run_warnings
run_errors
produced_artifacts
```

A collection remains empty when its stage does not apply.

Absence must not be represented through an undocumented sentinel.

---

# 9. Phase 3 — External-tool preflight

## 9.1 Purpose

Preflight confirms that the external execution boundary is usable before expensive project validation begins.

## 9.2 Required checks

Depending on mode and strictness:

- resolve the exact GF executable;
- confirm that it is a file and executable by policy;
- probe the GF version unless explicitly and permissibly disabled;
- verify minimum supported version;
- warn or fail for unknown versions according to compatibility policy;
- resolve the effective GF search path;
- validate the working directory;
- validate output directories;
- validate operation timeouts;
- record the resolved executable and search path.

## 9.3 Version-probe failure

A version-probe failure is not automatically a language failure.

Policy:

- strict or release mode may treat it as a blocking framework error;
- permissive diagnostic mode may retain a warning and continue;
- launch failure must remain distinguishable from unsupported version;
- raw probe stdout and stderr must be retained when a process was launched.

## 9.4 No implicit shell

All normal GF invocations use:

```text
explicit executable
ordered argument list
explicit working directory
explicit timeout
separate stdout and stderr capture
```

The process layer does not classify linguistic or dependency errors.

---

# 10. Phase 4 — Execution-plan resolution

## 10.1 Purpose

The resolved mode determines which stages are required, optional, or disabled.

The execution plan is derived from:

- canonical mode;
- project configuration;
- explicit target;
- strictness;
- documented feature flags;
- release requirements.

It must not be derived separately by CLI and GUI.

## 10.2 Mode matrix

| Stage | quick | checkpoint | release | diagnostic |
|---|---:|---:|---:|---:|
| Configuration validation | Required | Required | Required | Required |
| GF preflight | Required | Required | Required | Required |
| Targeted source selection | Required | Project-defined | No | No |
| Project checkpoint selection | No | Required | Included where applicable | Optional |
| Broad source selection | No | No | Required | Required |
| Static scan | Required | Required | Required | Required |
| Fingerprint | Required | Required | Required | Required |
| Per-file compile | Required unless explicitly skipped | Required | Required | Required unless diagnostic option disables it |
| File classification | Required | Required | Required | Required |
| Required checkpoint scenarios | Project-defined | Required | Required where declared | Required where declared |
| Required release scenarios | No | No | Required | Optional unless explicitly selected |
| Optional diagnostic scenarios | No | Optional | Optional | Included by policy |
| Gold comparison | When selected scenario declares gold | Required where declared | Required where declared | When selected |
| PGF build | No | No | Required when project requires it | Optional diagnostic build |
| Release gates | No | No | Required | No |
| Previous-run diff | Optional | Optional | Recommended | Recommended |
| Full reports | Required | Required | Required | Required |
| Manifest | Required | Required | Required | Required |

The detailed stage set is documented in `docs/validation/VALIDATION_MODES.md`.

This table defines architecture-level expectations.

## 10.3 Quick mode

Purpose:

```text
Fast feedback on an explicit target.
```

Expected behavior:

- requires a target file or an explicitly resolved quick target;
- selects exactly the valid target set defined by policy;
- scans and fingerprints selected files;
- compiles selected files unless compilation is explicitly disabled;
- does not perform a release PGF build;
- does not run release-only scenarios;
- still produces a complete run result and reports.

## 10.4 Checkpoint mode

Purpose:

```text
Validate a project-defined development layer.
```

Expected behavior:

- selects configured checkpoint modules or checkpoint entrypoints;
- runs required checkpoint scenarios;
- applies checkpoint gold comparisons;
- does not claim release readiness;
- preserves deterministic checkpoint order.

## 10.5 Release mode

Purpose:

```text
Prove that the active project satisfies its declared release contract.
```

Expected behavior:

- uses strict configuration and external-tool checks;
- validates the complete required source set;
- runs all required release scenarios;
- verifies required gold output;
- builds the required PGF;
- verifies PGF existence and non-empty content;
- applies every release gate;
- writes a complete manifest;
- returns `OK` only when all required gates pass.

## 10.6 Diagnostic mode

Purpose:

```text
Collect broad evidence for debugging and project analysis.
```

Expected behavior:

- selects the broad configured source set;
- scans and normally compiles all selected files;
- runs required diagnostic scenarios;
- may run optional scenarios;
- collects richer evidence;
- may continue after non-blocking failures;
- does not imply release readiness.

---

# 11. Phase 5 — Source selection

## 11.1 Single authority

Source selection belongs to the file selector.

The audit core supplies configuration and consumes the selection.

It must not duplicate filtering rules.

## 11.2 Selection inputs

Selection uses:

- project root;
- configured source directory;
- glob;
- include pattern;
- exclude pattern;
- canonical mode;
- explicit target;
- checkpoint registry;
- maximum-file policy when applicable.

## 11.3 Selection output

The selector returns deterministic collections:

```text
included files
excluded files
exclusion reasons or counts
noise exclusions
```

## 11.4 Invariants

- included files satisfy the configured policy;
- excluded files are never compiled accidentally;
- order is deterministic;
- a quick explicit target resolves to exactly the intended target set;
- selection does not create run directories;
- selection does not scan;
- selection does not invoke GF;
- selection does not modify source files.

## 11.5 Empty selection

An empty required selection is a configuration or validation error.

It must not be reported as a successful run with zero files.

An intentionally empty optional selection may be represented as skipped with a documented reason.

---

# 12. Phase 6 — Per-file validation

## 12.1 Canonical per-file order

For every selected source file:

```text
1. mark file start in master evidence
2. resolve project-relative identity
3. extract module name
4. run static scan
5. build source fingerprint
6. compile or create an explicit skipped compile result
7. construct FileResult
8. append FileResult
9. mark file completion
```

Current baseline order is intentionally preserved:

```text
scan
    -> fingerprint
    -> compile
    -> FileResult
```

## 12.2 Per-file isolation

An unexpected error for one file should normally produce a structured file-level error result and allow the remaining selected files to continue.

Continuation is prohibited only when:

- the external execution boundary is unusable for all remaining files;
- the output root is unsafe or unwritable;
- cancellation is requested;
- evidence integrity cannot be preserved;
- release policy defines the error as immediately blocking.

## 12.3 Module identity

Module-name extraction occurs before result construction.

The module name is not inferred from report formatting.

Project-relative file identity is canonical for cross-run comparison.

## 12.4 Static scan

The scanner:

- reads the source;
- masks comments and string literals according to GF-aware rules;
- counts configured suspicious patterns;
- writes a per-file scan log;
- returns structured `ScanCounts`.

The scanner must not:

- invoke GF;
- modify source;
- classify dependency cascades;
- generate final reports.

Scan findings remain separate from GF compile status.

## 12.5 Fingerprint

The fingerprint stage produces source identity.

Canonical target algorithm:

```text
SHA-256
```

Fingerprint failure must not erase:

- scan evidence;
- compile evidence;
- file identity.

A recoverable fingerprint failure may produce an error detail while allowing compilation to proceed.

## 12.6 Compilation

The compiler:

- builds the ordered GF argument list;
- uses the configured GF executable;
- uses the resolved GF path;
- sets an explicit working directory;
- sets a finite timeout;
- invokes the shared process runner;
- captures stdout and stderr separately;
- preserves raw evidence;
- interprets compile-local diagnostics;
- returns `CompileSummary`.

The compiler does not classify a failure as downstream.

## 12.7 Skipped compilation

When compilation is disabled by an allowed mode option:

- no GF compile process is launched;
- status is explicitly `SKIPPED`;
- execution state records that no invocation occurred;
- scan and fingerprint evidence remain available;
- skipped must not be interpreted as compile success.

## 12.8 File result construction

A `FileResult` combines:

- file path;
- module name;
- validation status;
- diagnostic class;
- directness flag;
- blockers;
- scan counts;
- fingerprint;
- compile summary;
- evidence paths.

Initial compile failures may be provisionally `ambiguous`.

Cross-file classification occurs later.

## 12.9 File-level exception

When an unexpected exception occurs after the file begins:

- preserve existing file evidence;
- create a structured error result;
- record the exception in master evidence;
- do not invent a GF syntax or type diagnosis;
- continue when policy permits.

Technical errors belong to `error_kind` and execution state.

They do not create a new causal diagnostic class.

---

# 13. Phase 7 — Cross-file classification

## 13.1 Timing

Classification occurs after the per-file result set is complete for the selected source scope.

It does not run after every individual file.

This allows the classifier to inspect relationships among failures.

## 13.2 Canonical diagnostic classes

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Technical categories such as:

```text
SCRIPT
CONFIG
IO
TOOL
TIMEOUT
INTERNAL
```

belong to `error_kind`, not `diagnostic_class`.

## 13.3 Classification rules

The classifier:

- consumes existing structured evidence;
- does not rerun GF;
- identifies likely direct failures;
- identifies dependency cascades;
- retains ambiguity when evidence is insufficient;
- collapses downstream blockers toward known roots;
- preserves raw diagnostics;
- returns deterministic ordering and classification.

## 13.4 No report-side reclassification

Report writers may group results by diagnostic class.

They must not independently change or recompute classification.

## 13.5 Classification failure

If classification itself fails:

- raw file results remain valid evidence;
- the run becomes `ERROR` when causal classification is required;
- a diagnostic warning may be acceptable in explicitly permissive modes;
- reports must disclose that classification was incomplete.

---

# 14. Phase 8 — Scenario validation

## 14.1 Scenario selection

Scenario IDs are selected from:

- project configuration;
- canonical mode;
- required/optional status;
- strictness;
- explicit supported scenario selectors.

Ordering follows project declaration order.

## 14.2 Required and optional scenarios

Required scenarios affect run success.

Optional scenarios:

- still produce `ScenarioResult`;
- still preserve evidence;
- may fail without failing the run only when project policy explicitly allows it;
- must never be silently promoted to required or demoted from required.

## 14.3 Canonical scenario order

For each selected scenario:

```text
1. validate scenario registration
2. validate script path
3. validate input and gold references
4. construct GF process request
5. execute GF
6. preserve raw stdout and stderr
7. verify launch and timeout state
8. verify required markers
9. normalize output
10. compare with gold when applicable
11. verify declared artifacts
12. construct ScenarioResult
```

## 14.4 Native GF execution

The scenario runner executes GF.

It does not implement a competing:

- GF parser;
- GF linearizer;
- GF generator;
- GF shell;
- GF type checker;
- PGF runtime.

Scenario files remain project assets.

## 14.5 Raw evidence first

Raw stdout and stderr are captured before normalization.

Normalization writes a separate `.out` artifact.

Raw evidence must never be replaced with normalized text.

## 14.6 Marker validation

Stable markers prove that required scenario sections completed.

A required marker contract includes:

- unique section ID;
- one begin marker;
- one matching end marker;
- deterministic order when required.

A zero exit code does not override:

- missing end marker;
- duplicate marker;
- malformed marker;
- incomplete required section.

## 14.7 Output normalization

Normalization may remove documented instability such as:

- CRLF differences;
- approved prompts;
- run-directory prefixes;
- temporary-directory prefixes;
- unstable durations;
- documented timestamps;
- platform path separators.

Normalization must not remove linguistically meaningful output or GF diagnostics required by assertions.

## 14.8 Gold comparison

Gold comparison occurs after normalization.

Normal validation is read-only.

A missing required gold file is a failure.

A mismatch creates a scenario failure and a reviewable diff.

Gold updates occur only through an explicit separate operation.

## 14.9 Scenario result

A `ScenarioResult` records at least:

- scenario ID;
- script path;
- required flag;
- validation status;
- execution state;
- ordered command;
- working directory;
- exit code;
- timeout state;
- duration;
- stdout path;
- stderr path;
- normalized output path;
- gold path;
- gold comparison state;
- diagnostic class;
- error kind;
- primary message;
- marker-section results;
- produced artifacts.

## 14.10 Scenario continuation

After one scenario fails:

- required later scenarios may still run in diagnostic mode to maximize evidence;
- release mode may continue when evidence collection remains safe;
- immediate stop is permitted for unsafe execution, cancellation, invalid global configuration, or unusable GF process infrastructure.

The stop policy must be deterministic and documented.

---

# 15. Phase 9 — PGF build and release gates

## 15.1 Separation from file compilation

Individual `.gf` to `.gfo` success does not prove release readiness.

PGF construction is a separate stage.

## 15.2 PGF build input

The PGF build uses:

- project-declared entrypoints;
- deterministic entrypoint order;
- resolved GF executable;
- resolved GF path;
- project root as working directory;
- release-build timeout;
- run-owned PGF output directory.

## 15.3 PGF build success

PGF build success requires:

- process launched;
- no timeout;
- acceptable exit code;
- no recognized fatal diagnostic;
- expected `.pgf` exists;
- expected `.pgf` is non-empty;
- artifact path remains inside the run-owned artifact root;
- artifact is registered for the manifest.

## 15.4 Release gates

Release mode evaluates all project-declared required gates.

Typical gates:

```text
configuration valid
GF version supported
required files selected
required file compilation successful
required scenarios successful
required gold comparisons successful
required PGF produced
required artifacts present
manifest valid
no blocking framework error
```

The authoritative gate set is defined by project configuration and release documentation.

## 15.5 Diagnostic PGF build

Diagnostic mode may execute a PGF build when explicitly selected.

A diagnostic PGF result does not by itself declare release readiness.

---

# 16. Phase 10 — Aggregation

## 16.1 Build preliminary run result

After file and scenario stages, the result builder constructs the run-level model.

It receives:

- resolved configuration;
- run paths;
- file results;
- scenario results;
- PGF/release results where modeled;
- start and finish timestamps;
- duration;
- GF version;
- selection counts;
- warnings and errors;
- artifact references.

## 16.2 Counts

Counts must be derived from structured result collections.

They must not be maintained independently through competing mutable counters when derivation is possible.

Required consistency includes:

```text
files_included =
    files_ok
  + files_fail
  + files_error
  + files_skipped
```

```text
scenarios_seen =
    scenarios_ok
  + scenarios_fail
  + scenarios_error
  + scenarios_skipped
```

## 16.3 Top errors

Top-error grouping occurs from structured result messages.

Ordering is deterministic:

```text
descending count
then case-insensitive message
```

Empty messages are excluded.

## 16.4 Overall status

Canonical run validation status:

```text
OK
FAIL
ERROR
```

Rules:

- `ERROR` means a required stage could not execute or be interpreted reliably;
- `FAIL` means execution completed sufficiently but one or more required criteria failed;
- `OK` means every required criterion passed.

`SKIPPED` is valid for individual optional or disabled stages, not as the normal final status of a completed run.

Cancellation is an execution state, not a validation status.

---

# 17. Regression comparison

## 17.1 Timing

Regression comparison occurs after the current structured results are coherent.

It occurs before final report serialization.

## 17.2 Previous-run discovery

The diff stage searches for the most recent eligible earlier run under the configured output root.

It must exclude the current run directory.

## 17.3 Structured source

The source of previous-run truth is:

```text
summary.json
```

Markdown reports are not parsed for regression comparison.

## 17.4 Compatibility

The loader may read supported legacy summary forms through explicit migration logic.

It must not silently reinterpret unsupported schema meaning.

## 17.5 Failure behavior

A missing previous run produces:

```text
no diff
```

An invalid previous run:

- does not corrupt current results;
- produces a warning;
- yields an empty diff unless strict policy requires failure.

## 17.6 Diff identity

File identity uses normalized project-relative paths.

Scenario identity uses stable scenario IDs.

Change kinds:

```text
unchanged
improved
regressed
new
removed
```

Diff ordering is deterministic.

---

# 18. Phase 11 — Reporting and finalization

## 18.1 Reporting principle

Reports serialize existing evidence.

They must not:

- rerun GF;
- rescan source;
- reclassify results;
- reconstruct hidden configuration;
- mutate project files;
- update gold files.

## 18.2 Report order

Recommended finalization order:

```text
1. write or update master log
2. write per-file and per-scenario details
3. write aggregate raw logs
4. write top_errors.txt
5. write summary.json
6. write summary.md
7. write AI_READY.md
8. verify required artifacts
9. write manifest.json
10. validate manifest
11. finalize run completion state
```

A concrete implementation may reorder independent human-facing report writers if:

- ownership remains unchanged;
- `summary.json` is coherent;
- manifest hashes are computed after final writes;
- deterministic output is preserved.

## 18.3 Primary machine summary

`summary.json` is the primary machine-readable run summary.

It contains the canonical structured result.

It must be complete before consumers are told that the run is finalized.

## 18.4 Human summary

`summary.md` presents a concise human-readable interpretation.

It is not a machine migration source.

## 18.5 AI packet

`AI_READY.md` is derived from the same structured evidence.

It may include bounded diagnostic excerpts and artifact references.

It must not rerun validation to fill missing data.

## 18.6 Raw and aggregate logs

Aggregate logs combine or index existing evidence.

They must preserve links to per-stage raw files.

## 18.7 Manifest

The manifest is written after final artifact bytes exist.

It records:

- run ID;
- generation timestamp;
- hash algorithm;
- artifact path;
- role;
- media type;
- required flag;
- byte size;
- SHA-256;
- writer identity.

The manifest does not hash itself.

## 18.8 Manifest failure

A manifest failure after otherwise successful validation changes the final run to `ERROR` when manifest integrity is required.

Release mode requires a valid manifest.

Other modes may retain a clearly reported framework error according to policy.

## 18.9 Completion marker

A run is finalized only after:

- required reports are closed;
- required artifacts are verified;
- manifest policy is satisfied;
- final status is stable;
- no owned process can continue writing into the run directory.

A future explicit completion marker may be added, but it must be schema-controlled.

---

# 19. Exception and partial-result flow

## 19.1 Before run creation

Errors before run-path creation normally propagate as configuration or invocation errors.

Examples:

- unsupported CLI arguments;
- missing project root;
- unreadable project configuration;
- invalid mode;
- missing required target;
- unsafe output root.

No run directory is required.

## 19.2 After run creation

After a run directory exists, the orchestrator must preserve recoverable evidence.

It should construct a partial `RunResult` containing:

- completed file results;
- completed scenario results;
- known configuration;
- timing;
- warnings;
- framework error;
- artifact paths already created.

Best-effort report writing then attempts each independent writer.

## 19.3 Best-effort reporting

Best-effort reporting means:

- each report writer is attempted independently;
- one writer failure does not automatically suppress all others;
- failures are recorded in master evidence;
- an already valid primary artifact is not deleted;
- final status reflects required report or manifest failures.

Best effort does not mean silently ignoring errors.

## 19.4 Unsafe continuation

Execution must stop when:

- output containment is violated;
- the resolved executable changes unexpectedly;
- process termination fails and an owned process remains active;
- disk exhaustion prevents safe evidence capture;
- cancellation is requested;
- project source mutation is detected;
- a security policy is violated;
- result integrity can no longer be trusted.

---

# 20. Timeout and cancellation flow

## 20.1 Timeout

A timeout is local to one external process request unless policy declares the infrastructure unusable.

On timeout:

```text
mark timed_out
attempt process-tree termination
retain partial stdout
retain partial stderr
record duration
construct structured stage result
continue or stop according to mode policy
```

A timeout is not a normal GF failure.

## 20.2 Cancellation

Cancellation is an execution state.

Recommended canonical values:

```text
completed
timed_out
cancelled
launch_failed
```

Cancellation behavior:

- no new stage begins after cancellation is accepted;
- active owned processes are terminated;
- completed evidence is preserved;
- in-progress stage receives a structured cancelled result when possible;
- reports are written best-effort;
- final validation status is `ERROR`;
- execution state records `cancelled`.

## 20.3 GUI cancellation

The GUI may request cancellation through a documented orchestration mechanism.

It must not terminate compiler subprocesses directly.

## 20.4 Keyboard interruption

CLI interruption should follow the same cancellation path when feasible.

Abrupt process termination may leave an incomplete run, which must not be represented as finalized.

---

# 21. Determinism

## 21.1 Required deterministic elements

The following are deterministic:

- selected-file order;
- checkpoint order;
- scenario order;
- entrypoint order;
- file-result serialization order;
- scenario-result serialization order;
- diff ordering;
- top-error ordering;
- manifest ordering;
- report section ordering.

## 21.2 Time-dependent elements

These may vary:

- run ID;
- timestamps;
- durations;
- temporary paths;
- GF process scheduling.

They must be isolated from exact gold comparison or normalized where documented.

## 21.3 Concurrency policy

The canonical architecture does not require parallel stage execution.

A future parallel implementation is compatible only when it preserves:

- deterministic result order;
- per-file and per-scenario log isolation;
- timeout isolation;
- cancellation behavior;
- bounded resource use;
- artifact ownership;
- equivalent classification;
- equivalent final status.

Report writing and manifest generation occur only after all result-producing workers are complete.

---

# 22. Stage dependency graph

```text
configuration
    |
    v
run paths
    |
    v
preflight
    |
    v
execution plan
    |
    +----------------------+
    |                      |
    v                      v
file selection       scenario selection
    |                      |
    v                      |
per-file pipeline          |
    |                      |
    v                      v
file classification   scenario execution
    |                      |
    +----------+-----------+
               |
               v
         PGF build/gates
               |
               v
         run aggregation
               |
               v
       previous-run diff
               |
               v
            reports
               |
               v
           manifest
               |
               v
         final RunResult
```

Dependency arrows indicate data flow, not import permission.

Import directions remain governed by the interfile contract lock.

---

# 23. Artifact timeline

| Moment | Artifacts allowed |
|---|---|
| Run initialization | Directories, initial master evidence |
| File scan | Per-file scan logs |
| File compile | Per-file stdout, stderr, `.gfo` where produced |
| Scenario execution | Scenario stdout, stderr |
| Scenario normalization | Scenario `.out`, gold diff |
| PGF stage | `.pgf`, PGF stdout and stderr |
| Aggregation | In-memory `RunResult` |
| Reporting | JSON, Markdown, AI packet, top errors, details, aggregate logs |
| Finalization | `manifest.json` |
| Completion | Stable finalized run directory |

A later stage may observe an earlier artifact.

It may not silently rewrite it unless it is the declared owner and the artifact has not been finalized.

---

# 24. Final result flow to callers

## 24.1 Return value

`run_audit` returns `RunResult`.

Callers inspect structured fields.

## 24.2 CLI exit codes

The detailed exit-code registry is authoritative.

Architecture-level mapping:

```text
0  completed and required validation passed
1  completed with required validation failure
2  invocation or configuration error
3  framework/runtime execution error
```

Additional codes may be introduced only through the exit-code reference and compatibility policy.

The CLI must not map every non-zero GF exit directly to the process exit code.

## 24.3 GUI completion

The GUI displays:

- overall status;
- important counts;
- direct failures;
- scenario failures;
- artifact paths;
- warnings;
- run directory.

GUI convenience state may store recent paths and preferences.

It must not store the full `RunResult` as application state.

---

# 25. Canonical orchestration pseudocode

```python
def run_audit(run_config, run_paths=None):
    validate_resolved_run_config(run_config)

    started_at = utc_now()
    started_clock = monotonic_now()

    paths = run_paths or build_run_paths(run_config)
    context = initialize_run_context(run_config, paths, started_at)

    try:
        preflight = run_external_preflight(run_config, paths)

        plan = resolve_execution_plan(
            run_config=run_config,
            project_config=context.project_config,
            preflight=preflight,
        )

        selection = select_files(plan.file_selection)

        file_results = []
        for file_path in selection.included_files:
            file_results.append(
                run_file_pipeline(
                    file_path=file_path,
                    run_config=run_config,
                    run_paths=paths,
                    plan=plan,
                )
            )

        file_results = classify_file_results(file_results)

        scenario_results = run_selected_scenarios(
            plan=plan,
            run_config=run_config,
            run_paths=paths,
        )

        pgf_result = run_pgf_stage_if_required(
            plan=plan,
            run_config=run_config,
            run_paths=paths,
        )

        run_result = build_run_result(
            configuration=run_config,
            paths=paths,
            preflight=preflight,
            selection=selection,
            file_results=file_results,
            scenario_results=scenario_results,
            pgf_result=pgf_result,
            timing=finish_timing(started_at, started_clock),
        )

        run_result = apply_release_gates(run_result, plan)
        run_result = add_top_errors(run_result)

        if plan.compare_previous:
            run_result.diff_entries = build_previous_run_diff(run_result)

        write_reports_best_effort(run_result)
        write_and_validate_manifest(run_result)
        finalize_run_status(run_result)

        return run_result

    except CancellationRequested as exc:
        run_result = build_partial_cancelled_result(context, exc)
        write_reports_best_effort(run_result)
        write_manifest_if_safe(run_result)
        return run_result

    except Exception as exc:
        run_result = build_partial_error_result(context, exc)
        write_reports_best_effort(run_result)
        write_manifest_if_safe(run_result)
        return_or_raise_according_to_boundary(run_result, exc)
```

This pseudocode defines ordering and responsibility.

It does not prescribe private helper names.

---

# 26. Run state machine

```text
CREATED
   |
   v
CONFIGURED
   |
   v
INITIALIZED
   |
   v
PREFLIGHTED
   |
   v
EXECUTING_FILES
   |
   v
CLASSIFYING
   |
   v
EXECUTING_SCENARIOS
   |
   v
BUILDING_RELEASE_ARTIFACTS
   |
   v
AGGREGATING
   |
   v
REPORTING
   |
   v
MANIFESTING
   |
   v
FINALIZED
```

Exceptional terminal states:

```text
CANCELLED_PARTIAL
ERROR_PARTIAL
UNFINALIZED
```

Only `FINALIZED` represents a fully completed run directory.

A partial run may still contain useful evidence.

---

# 27. Observability

## 27.1 Master evidence

Master evidence records stage transitions and important decisions.

Recommended events:

```text
run_start
configuration_resolved
preflight_start
preflight_done
selection_done
file_start
file_done
file_error
classification_done
scenario_start
scenario_done
scenario_error
pgf_start
pgf_done
diff_done
report_start
report_done
manifest_done
run_finalized
run_cancelled
run_error
```

## 27.2 Structured before prose

Whenever structured fields exist, reports and tools use them.

They must not parse master-log prose to recover:

- status;
- counts;
- path identity;
- exit code;
- timeout state;
- diagnostic class.

## 27.3 Evidence on non-zero exit

Non-zero external-tool exit still produces:

- process result;
- stdout path;
- stderr path;
- duration;
- error interpretation;
- stage result.

---

# 28. Security-sensitive execution rules

- External processes use ordered arguments.
- Normal GF execution uses no implicit shell.
- Working directories are explicit.
- Project-controlled paths are validated.
- Run-owned output remains inside approved roots.
- `.gfs` scenarios are treated as executable input.
- Shell-capable scenario commands are disabled unless explicitly authorized.
- Timeouts are finite.
- Process-tree termination is platform-aware.
- Raw evidence is preserved before normalization.
- Reports do not contain secrets or full environment dumps.
- Gold files are read-only during normal validation.
- Cleanup is not part of normal audit execution.
- A run does not become finalized while an owned process may still write to it.

The full policy is defined in `SECURITY.md`.

---

# 29. Prohibited execution behavior

The following are prohibited:

```text
CLI -> compiler directly
GUI -> compiler directly
GUI -> scanner directly
GUI -> report writer directly
report -> GF process
report -> scanner
report -> scenario runner
scanner -> compiler
compiler -> report
classifier -> GF process
process runner -> diagnostic classification
normal audit -> gold update
normal audit -> source mutation
diff -> Markdown parsing
manifest writer -> artifact mutation
```

Also prohibited:

- selecting files in more than one component;
- building different GF paths for compilation and scenarios;
- treating zero process exit as sufficient scenario success;
- treating skipped compilation as success;
- treating missing PGF as release success;
- finalizing before report and manifest policy completes;
- dropping partial stdout or stderr after timeout;
- hiding launch failure as GF syntax failure;
- reconstructing artifact filenames outside `RunPaths`;
- changing pipeline order without contract review.

---

# 30. Required execution-flow tests

Recommended test structure:

```text
tests/execution/
├── test_cli_flow.py
├── test_gui_flow.py
├── test_configuration_flow.py
├── test_mode_planning.py
├── test_file_pipeline.py
├── test_classification_flow.py
├── test_scenario_flow.py
├── test_pgf_flow.py
├── test_diff_flow.py
├── test_reporting_flow.py
├── test_manifest_flow.py
├── test_partial_failure_flow.py
├── test_timeout_flow.py
├── test_cancellation_flow.py
└── test_deterministic_flow.py
```

## 30.1 Entry-point tests

Verify:

- CLI and GUI produce equivalent `RunConfig` for equivalent values;
- both call `run_audit`;
- neither calls stages directly;
- CLI exit code derives from `RunResult`.

## 30.2 Configuration tests

Verify:

- precedence;
- canonical mode aliases;
- project-relative paths;
- invalid required scenarios;
- invalid target;
- unsafe output root;
- state does not override project identity.

## 30.3 File-flow tests

Verify exact ordering:

```text
select
scan
fingerprint
compile
build result
classify
```

Verify one file error does not erase earlier evidence.

## 30.4 Scenario-flow tests

Verify:

```text
execute
capture raw
validate markers
normalize
compare gold
build result
```

Verify normal execution does not modify gold.

## 30.5 Release-flow tests

Verify:

- required scenarios run;
- PGF build is distinct from file compilation;
- missing PGF fails release;
- invalid manifest prevents release success;
- optional diagnostic success cannot bypass required release failure.

## 30.6 Partial-flow tests

Verify:

- configuration failure before run creation;
- failure after run creation;
- best-effort independent report writing;
- partial `RunResult`;
- cancellation;
- timeout;
- manifest failure;
- previous-run diff failure does not corrupt current evidence.

## 30.7 Determinism tests

Verify stable:

- source order;
- scenario order;
- result order;
- top errors;
- diff;
- manifest;
- report sections.

---

# 31. Change control

A change to execution order or stage selection must identify:

```text
Affected phase:
Current order:
New order:
Reason:
Modes affected:
Configuration impact:
External-tool impact:
Result-model impact:
Artifact impact:
Persisted-schema impact:
Failure-semantics impact:
Compatibility:
Migration:
Tests:
```

Required checklist:

```text
[ ] audit orchestration updated
[ ] all affected stages reviewed
[ ] RunConfig reviewed
[ ] RunPaths reviewed
[ ] RunResult reviewed
[ ] external-tool lock reviewed
[ ] interfile lock reviewed
[ ] persisted-schema lock reviewed
[ ] mode documentation updated
[ ] report documentation updated
[ ] security impact reviewed
[ ] unit tests updated
[ ] integration tests updated
[ ] migration documented when needed
```

A local reordering that changes observable evidence is an architectural change.

---

# 32. Implementation completion checklist

The final implementation satisfies this execution flow when:

```text
[ ] CLI and GUI share configuration resolution
[ ] run_audit is the authoritative entry point
[ ] project.toml owns active-language rules
[ ] run paths are explicit and unique
[ ] preflight records the actual GF executable
[ ] canonical modes are implemented
[ ] file selection is deterministic
[ ] scan and compile remain separate
[ ] fingerprints are stable
[ ] file classification runs after file collection
[ ] scenario runner executes native GF
[ ] raw scenario evidence precedes normalization
[ ] required markers are verified
[ ] gold comparison is read-only in normal runs
[ ] PGF build is a separate release stage
[ ] release gates are explicit
[ ] RunResult counts are coherent
[ ] previous-run diff uses structured summaries
[ ] reports do not rerun stages
[ ] manifest hashes finalized artifacts
[ ] partial failures preserve evidence
[ ] timeouts and cancellation are structured
[ ] deterministic order is tested
[ ] security-sensitive paths are contained
[ ] contract locks match implementation
```

---

# 33. Related documents

```text
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
docs/scenarios/SCENARIO_FORMAT.md
docs/reports/REPORTING_OVERVIEW.md
docs/reference/STATUS_VALUES.md
SECURITY.md
```

---

# 34. Final rule

GF Wordbench is an orchestrator.

GF remains authoritative for grammar execution.

The active project remains authoritative for language-specific validation requirements.

GF Wordbench remains authoritative for:

- configuration resolution;
- stage ordering;
- evidence capture;
- classification;
- comparison;
- reporting;
- final status.

Therefore:

> No caller may bypass the orchestration flow, no stage may silently take ownership of another stage, and no run may be declared complete before its required evidence, reports, artifacts, and manifest are finalized.
