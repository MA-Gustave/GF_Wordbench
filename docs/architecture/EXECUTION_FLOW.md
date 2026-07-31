# GF Wordbench — Execution Flow

**Document ID:** `GF-WB-ARCH-EXECUTION-FLOW`  
**Status:** Normative architecture specification  
**Applies to:** one GF Wordbench run for one resolved language context and, when supplied, one explicit validation profile  
**Owner:** GF Wordbench maintainers  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Framework boundary:** `docs/INTERFILE_CONTRACT_LOCK.md`  
**External-tool boundary:** `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Persisted-artifact boundary:** `docs/PERSISTED_SCHEMA_LOCK.md`  
**Governing startup decision:** `docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md`  
**Last structural review:** `2026-07-30`

---

## 1. Purpose

This document defines the canonical execution flow of GF Wordbench from an explicit language-path selection to finalized run artifacts.

It answers:

- where GUI, CLI and automation execution begins;
- how one selected language directory or `.gf` file becomes a resolved language context;
- how optional validation profiles are loaded without becoming startup authorities;
- how validation mode selects stages;
- when files are selected, scanned, fingerprinted and compiled;
- when scenarios and gold comparisons run;
- when a PGF release build runs;
- how results are classified and aggregated;
- how previous runs are compared;
- how reports and manifests are finalized;
- how partial failures, timeouts and cancellation are represented;
- what entrypoints and orchestration layers may and may not do.

This file describes startup orchestration, run ordering and stage boundaries.

It does not duplicate:

- GF command syntax;
- persisted field-by-field schemas;
- file-to-file public contracts;
- language-specific module dependencies;
- report layout details;
- validation-profile field definitions.

Those are owned by the corresponding contract and reference documents.

---

## Product, language and run boundary

GF Wordbench is multi-language capable but single-language at runtime.

Before the main runtime exists, the user or caller explicitly supplies one language directory or one `.gf` file. Wordbench resolves that selection through the shared language-probe, file-selection, GF-path and preflight boundaries. A running session then contains exactly one immutable `ResolvedLanguageContext`, and one ordinary run records exactly one language identity.

An optional validation profile may add scenarios, golds, checkpoints, entrypoints and release policy. It is not required for browsing, static scanning or targeted compilation of a standard RGL language source tree.

GF Wordbench owns validation orchestration, evidence capture, classification, comparison, reporting and run finalization for the resolved language context.

GF Wordbench does not:

- maintain several simultaneously active language contexts;
- mutate language identity during a run;
- discover unrelated workspaces or source trees through an unbounded search;
- maintain a portfolio registry;
- aggregate multilingual readiness across contexts;
- depend on `gf-portfolio` code, runtime, schemas, storage or configuration.

The independent `gf-portfolio` product may consume finalized, public, versioned Wordbench artifacts. That consumer relationship does not alter Wordbench execution flow.

---

## 2. Core execution rules

> Every supported validation request passes through one authoritative application use case, and no run begins without one validated resolved language context.

The canonical logical operations are:

```python
probe_language(
    request: LanguageProbeRequest,
) -> LanguageProbeResult

execute_run(
    request: RunRequest,
) -> RunResult
```

`LanguageProbeRequest` represents the explicit selected language path and any explicit nonstandard-layout or profile choices.

`RunRequest` represents resolved user intent for one `ResolvedLanguageContext`, one mode and one optional validation profile.

Private class and function names may vary, but all supported entrypoints call the same application boundaries.

Equivalent resolved requests produce equivalent:

- language identity;
- source selection;
- stage selection;
- stage ordering;
- GF path resolution;
- evidence policy;
- success and failure semantics;
- artifact contracts.

This rule applies whether the request originates from:

- the CLI;
- the GUI;
- automation;
- tests;
- a supported API adapter.

CLI, GUI and adapters must not reconstruct the probe or run pipeline independently.

---

## 3. Execution authority

### 3.1 Entrypoints own interaction

CLI, GUI and supported API adapters own:

- collecting explicit user intent;
- accepting one language directory or `.gf` file;
- presenting candidate choices and remediation when the probe reports ambiguity;
- accepting an optional validation profile;
- converting external values into application requests;
- invoking the language-probe and run application use cases;
- rendering returned structured results;
- mapping results to an exit code, response or GUI state.

Entrypoints do not own:

- filesystem language discovery rules;
- source selection;
- path containment;
- module-name extraction;
- GF path construction;
- static scanning;
- GF command construction;
- process execution;
- scenario execution;
- classification;
- regression comparison;
- report generation;
- artifact naming.

### 3.2 The projects module owns language-context resolution

The `projects` module owns the bounded `LanguageProbeService` application use case.

It coordinates public services to:

- interpret the explicit selected path;
- derive the candidate language directory;
- locate a supported RGL source root by walking selected-path ancestors only;
- request deterministic GF source enumeration from the existing file selector;
- classify standard RGL module candidates without claiming GF semantic validity;
- request centralized GF path resolution;
- collect structural diagnostics and capability statuses;
- validate an explicitly supplied optional profile against the selected context;
- produce one immutable `ResolvedLanguageContext`.

The projects module does not implement a second recursive selector, GF compiler, process runner, GF diagnostic parser or reporting system.

Application state and entrypoint state cannot override resolved language identity.

### 3.3 The runs module owns orchestration and lifecycle

The `runs` module owns:

- accepting one resolved language context;
- creating the run identity;
- resolving or creating run paths;
- building the execution plan;
- coordinating validation stages;
- preserving partial results;
- applying run budgets and cancellation;
- aggregating results;
- coordinating report publication;
- finalizing the run lifecycle.

The runs module depends on application ports, not concrete GUI, CLI, filesystem or process implementations.

### 3.4 Functional modules own bounded work

| Module or stage | Responsibility |
|---|---|
| Projects — language probe | Coordinate one selected path into one resolved language context |
| Projects — optional profile | Load and validate explicit advanced validation policy |
| Runs | Plan, orchestrate and finalize one run |
| Validation — file selector | Determine included and excluded GF source files |
| Validation — scanner | Produce heuristic source findings |
| Validation — fingerprint provider | Produce source identity |
| Validation — compiler | Request GF file compilation |
| Diagnostics — classifier | Determine direct, downstream, ambiguous, noise or skipped |
| Validation — scenario runner | Execute explicit profile-owned `.gfs` scenarios through the GF port |
| Validation — gold comparator | Compare normalized scenario output with reviewed gold |
| Validation — PGF stage | Build and verify an explicitly configured release PGF |
| Runs — diff stage | Compare with a compatible prior structured run |
| Reporting | Serialize existing structured evidence |
| Reporting — manifest writer | Inventory finalized run artifacts |

No module may silently assume ownership of another module's behavior.

### 3.5 Ports and adapters own external boundaries

Application ports define requests and results for:

- selected-path and optional-profile storage;
- filesystem access;
- clocks and identifiers;
- GF and diagnostic tool execution;
- cancellation;
- artifact publication.

Adapters implement those ports. Domain and application code do not construct shell command strings, read GUI widgets or depend on operating-system process APIs directly.

---

## 4. Canonical high-level flow

```text
User / automation
        |
        v
CLI / GUI / API adapter
        |
        +--> explicit language directory or .gf file
        |
        v
LanguageProbeService
        |
        +--> normalize selected path
        +--> derive language directory and RGL source root
        +--> enumerate source candidates through SelectionService
        +--> classify candidate module roles
        +--> resolve candidate GF path through the central resolver
        +--> validate optional profile when supplied
        +--> publish ResolvedLanguageContext
        |
        v
Build RunRequest
        |
        v
Runs application use case
        |
        +--> validate resolved request and requested capability
        |
        +--> create run identity and paths
        |
        +--> external-tool preflight when required
        |
        +--> resolve execution plan
        |
        +--> select source files
        |
        +--> execute per-file validation
        |       scan
        |       fingerprint
        |       compile or skip
        |       build FileResult
        |
        +--> classify file results
        |
        +--> execute selected profile scenarios when configured
        |       run GF
        |       preserve raw output
        |       verify markers
        |       normalize
        |       compare gold
        |       build ScenarioResult
        |
        +--> build PGF when explicitly required
        |
        +--> aggregate RunResult
        |
        +--> compare with a compatible previous structured run
        |
        +--> publish reports and aggregate logs
        |
        +--> write and verify manifest
        |
        +--> finalize run lifecycle
        |
        v
Return RunResult
        |
        +--> CLI renders summary and exit code
        +--> GUI renders result and stores convenience state
        +--> API adapter returns the documented representation
```

---

## 5. Flow phases

The execution flow is divided into twelve phases.

```text
Phase 0   Request intake and language-context resolution
Phase 1   Run configuration and optional-profile resolution
Phase 2   Run initialization
Phase 3   External-tool preflight
Phase 4   Execution-plan resolution
Phase 5   Source selection
Phase 6   Per-file validation
Phase 7   Cross-file classification
Phase 8   Scenario validation
Phase 9   PGF and release gates
Phase 10  Aggregation and regression comparison
Phase 11  Reporting, manifest and completion
```

A phase may contain multiple stages, but phase order is stable.

# 6. Phase 0 — Request intake and language-context resolution

## 6.1 CLI path

Canonical logical flow:

```text
parse arguments
    → convert values to plain Python types
    → require one explicit language path or an explicit remembered-path action
    → call the shared LanguageProbeService
    → render structured ambiguity or invalid-selection diagnostics when needed
    → obtain ResolvedLanguageContext
    → call the shared run-request builder
    → invoke the run application use case
    → print returned result summary
    → map result to process exit code
```

The CLI must not determine success by parsing generated reports.

The CLI must use structured probe and `RunResult` fields.

In noninteractive mode, unresolved ambiguity is an explicit invocation error unless the caller supplies the missing choice.

## 6.2 GUI path

Canonical logical flow:

```text
create QApplication
    → load persisted convenience state
    → show the introduction window
    → choose Open last language, Choose language path or Quit
    → call the shared LanguageProbeService in the supported worker context
    → present exact candidates or remediation when required
    → obtain ResolvedLanguageContext
    → compose the main runtime
    → convert widgets and preferences to plain run-request values
    → invoke the run application use case
    → render returned result
    → save convenience state
```

The main Wordbench window must not be composed before a resolved language context exists.

The GUI must not call:

- recursive filesystem enumeration directly;
- `compile_file`;
- `scan_file`;
- GF path serialization;
- scenario execution;
- report writers;
- manifest generation.

GUI validation may reject obvious input earlier than the probe or bootstrap, but it must not replace application validation.

## 6.3 Automation path

Automation uses the same public language-probe, request-builder and run application use cases.

It may:

- disable interactive output;
- provide an explicit language directory or `.gf` file;
- provide an explicit optional validation profile;
- select strict mode;
- choose deterministic output roots;
- inspect structured probe output and `summary.json`;
- use exit codes.

It must not:

- choose the first ambiguous candidate;
- bypass required release gates;
- restore a stale resolved context without revalidation;
- use the retired catalog as a startup authority.

# 7. Phase 1 — Run configuration and optional-profile resolution

## 7.1 Configuration sources

Run configuration is resolved from these domains:

```text
immutable ResolvedLanguageContext
application metadata and safe framework defaults
environment-specific tool paths
explicit CLI or GUI run values
optional explicitly selected validation profile
documented compatibility aliases
```

`ResolvedLanguageContext` is authoritative for:

- portable language key;
- selected-path provenance;
- language directory;
- RGL source root and RGL root when resolved;
- optional module suffix;
- focused target when a file was selected;
- detected entrypoint candidates;
- source inventory or stable inventory reference;
- GF path requirements and provenance;
- base capability statuses.

An optional validation profile is authoritative only for explicitly configured advanced policy:

- source glob and filters;
- required entrypoints;
- checkpoints;
- required and optional scenarios;
- inputs and golds;
- release targets;
- release requirements and gates.

The application state is not authoritative language or run configuration.

## 7.2 Precedence

Recommended precedence from lowest to highest:

```text
1. framework-safe defaults
2. immutable resolved language context
3. explicit optional validation profile
4. environment-specific configured tool values
5. explicit CLI or GUI run values permitted by policy
```

Correctness-critical values must not rely silently on inherited environment variables.

Explicit values may override profile defaults only where the profile contract permits it.

An override must not change language identity, escape the resolved roots or bypass required release constraints silently.

## 7.3 Compatibility aliases

Legacy mode aliases may be accepted at input or migration boundaries:

```text
file → quick
all  → diagnostic
```

Canonical resolved modes are:

```text
quick
checkpoint
release
diagnostic
```

Canonical writers and reports must emit canonical mode values only.

A temporary catalog-era compatibility adapter may translate an explicit legacy catalog selection into a selected path. It must not preserve catalog authority in the resolved context.

## 7.4 Configuration validation

Validation occurs before external execution.

Base validation includes:

- one immutable resolved language context exists;
- selected path and language directory remain valid and readable;
- language directory remains contained in the resolved source root;
- source inventory is deterministic and non-empty for source-backed modes;
- mode is supported;
- output root is permitted and writable;
- timeout values are positive;
- explicit target is present when required;
- GF path requirements remain valid;
- run-owned paths remain inside the output root.

When an optional profile is supplied, also validate:

- schema ID and version are supported;
- profile identity agrees with the resolved language context;
- profile-owned paths remain inside approved language or profile roots;
- configured entrypoints and checkpoints are deterministic;
- required scenario IDs are unique;
- required scenario files exist;
- required inputs exist;
- required gold files exist where profile policy requires them;
- release requirements are complete for release mode.

When the requested capability uses GF, also validate:

- GF executable resolves;
- effective GF path is valid;
- working directory policy is valid.

A probe or configuration failure before run-path creation normally produces no run directory.

A configuration failure after run-path creation must be represented in partial run evidence.

## 7.5 Resolved configuration

The outputs of startup and run configuration are:

```text
ResolvedLanguageContext
RunRequest
```

The language context is produced before the main runtime is composed.

The runs module derives the immutable execution configuration used by stages from the language context, requested mode, explicit target and optional profile.

Once execution begins, stages read only the resolved execution request and run context.

They must not independently consult:

- GUI widgets;
- command-line parser objects;
- mutable application state;
- the retired runtime catalog;
- undeclared environment values;
- hard-coded language-specific constants;
- implicit ancestor project files.

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
- portable language key;
- selected-path kind;
- language directory relative to the RGL source root;
- optional validation-profile identity and digest;
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

Preflight confirms that the external execution boundary is usable before expensive language validation begins.

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

The resolved mode and capability status determine which stages are required, optional or disabled.

The execution plan is derived from:

- canonical mode;
- immutable resolved language context;
- optional validation profile;
- explicit focused target or target selection;
- strictness;
- documented feature flags;
- release requirements when configured.

It must not be derived separately by CLI and GUI.

## 10.2 Mode matrix

| Stage | quick | checkpoint | release | diagnostic |
|---|---:|---:|---:|---:|
| Language-context validation | Required | Required | Required | Required |
| GF preflight | Required when compiling | Required | Required | Required when GF work is enabled |
| Targeted source selection | Required | Profile-defined or explicit | No | Optional |
| Checkpoint selection | No | Required from explicit profile | Included where applicable | Optional |
| Broad source selection | No | No | Required by release profile | Required |
| Static scan | Required | Required | Required | Required |
| Fingerprint | Required | Required | Required | Required |
| Per-file compile | Required unless explicitly skipped | Required | Required | Required unless disabled by diagnostic policy |
| File classification | Required | Required | Required | Required |
| Checkpoint scenarios | No unless explicitly selected | Required where profile declares them | Required where declared | Required where declared |
| Release scenarios | No | No | Required where declared | Optional when selected |
| Optional diagnostic scenarios | No | Optional | Optional | Included by profile policy |
| Gold comparison | When selected scenario declares gold | Required where declared | Required where declared | When selected |
| PGF build | No | No | Required when release profile requires it | Optional diagnostic build |
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

- uses the selected `.gf` file or requires an explicit target from the resolved language inventory;
- selects exactly the valid target set defined by policy;
- scans and fingerprints selected files;
- compiles selected files unless compilation is explicitly disabled;
- does not require a validation profile;
- does not perform a release PGF build;
- does not run release-only scenarios;
- still produces a complete run result and reports.

## 10.4 Checkpoint mode

Purpose:

```text
Validate an explicitly configured development layer.
```

Expected behavior:

- requires an optional validation profile that declares checkpoints;
- selects configured checkpoint modules or checkpoint entrypoints;
- runs required checkpoint scenarios when declared;
- applies checkpoint gold comparisons when declared;
- does not claim release readiness;
- preserves deterministic checkpoint order.

Without a checkpoint profile, the mode is unavailable rather than guessed from filenames.

## 10.5 Release mode

Purpose:

```text
Prove that the resolved language context satisfies one explicit release profile.
```

Expected behavior:

- requires an explicit complete release-capable validation profile;
- uses strict configuration and external-tool checks;
- validates the complete required source set;
- runs all required release scenarios;
- verifies required gold output;
- builds the required PGF;
- verifies PGF existence and non-empty content;
- applies every release gate;
- writes a complete manifest;
- returns `OK` only when all required gates pass.

A source-ready language without a release profile cannot claim release readiness.

## 10.6 Diagnostic mode

Purpose:

```text
Collect broad evidence for debugging and language-source analysis.
```

Expected behavior:

- selects the broad resolved source set;
- scans and normally compiles all selected files;
- runs explicit diagnostic scenarios when a profile provides them;
- may continue after non-blocking failures;
- collects richer evidence;
- does not require a profile for file-level analysis;
- does not imply release readiness.

# 11. Phase 5 — Source selection

## 11.1 Single authority

Source selection belongs to the existing file selector.

The language probe and runs application service supply configuration and consume its result.

Neither may duplicate enumeration, filtering, containment, deduplication or ordering rules.

## 11.2 Selection inputs

Selection uses:

- resolved language directory;
- resolved RGL source root where required for containment;
- source glob;
- include pattern;
- exclude pattern;
- canonical mode;
- explicit focused target;
- optional profile checkpoint or entrypoint registry;
- maximum-file policy when applicable.

Base path-resolved startup supplies safe generic source-selection defaults. An explicit validation profile may narrow or extend those defaults within approved roots.

## 11.3 Selection output

The selector returns deterministic collections:

```text
included files
excluded files
exclusion reasons or counts
noise exclusions
```

## 11.4 Invariants

- included files satisfy the resolved policy;
- every included file remains inside the approved source boundary;
- excluded files are never compiled accidentally;
- order is deterministic;
- a quick explicit target resolves to exactly the intended target set;
- source identity is language-directory-relative for portable comparison;
- selection does not create run directories;
- selection does not scan;
- selection does not invoke GF;
- selection does not modify source files.

## 11.5 Empty selection

An empty required selection is a configuration or planning failure.

It must not silently become a successful run.

# 12. Phase 6 — Per-file validation

## 12.1 Canonical per-file order

For every selected source file:

```text
1. mark file start in master evidence
2. resolve language-context-relative identity
3. extract module name
4. run static scan
5. build source fingerprint
6. compile or create an explicit skipped compile result
7. construct FileResult
8. append FileResult
9. mark file completion
```

The canonical order is:

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

Language-directory-relative file identity is canonical for cross-run comparison.

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

Canonical algorithm:

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

- the explicit optional validation profile;
- canonical mode;
- required/optional status;
- strictness;
- explicit supported scenario selectors.

Ordering follows explicit profile declaration order.

## 14.2 Required and optional scenarios

Required scenarios affect run success.

Optional scenarios:

- still produce `ScenarioResult`;
- still preserve evidence;
- may fail without failing the run only when explicit profile policy allows it;
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

Scenario files remain explicit validation-profile assets.

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

The PGF build requires an explicit release-capable validation profile and uses:

- profile-declared entrypoints;
- deterministic entrypoint order;
- resolved GF executable;
- one resolved effective GF path;
- the validated language or profile working directory;
- release-build timeout;
- run-owned PGF output directory.

Detected standard entrypoint candidates may assist profile authoring, but they do not become release authority automatically.

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

Release mode evaluates all required gates declared by the explicit validation profile.

Typical gates:

```text
resolved language context valid
release profile valid
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

The authoritative gate set is defined by the explicit validation profile and its release documentation.

## 15.5 Diagnostic PGF build

Diagnostic mode may execute a PGF build when explicitly selected and sufficiently configured.

A diagnostic PGF result does not by itself declare release readiness.

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

Eligibility requires compatible resolved-language identity and comparison policy.

## 17.3 Structured source

The source of previous-run truth is:

```text
summary.json
```

Markdown reports are not parsed for regression comparison.

## 17.4 Compatibility

At minimum, compatibility considers:

- portable language key;
- language-directory identity relative to the RGL source root;
- relevant source or profile digest policy;
- target or mode compatibility;
- persisted schema compatibility.

The loader may read supported legacy summary forms through explicit migration logic.

It must not silently reinterpret unsupported schema meaning or compare evidence from another language context.

## 17.5 Failure behavior

A missing compatible previous run produces:

```text
no diff
```

An invalid or incompatible previous run:

- does not corrupt current results;
- produces a warning when useful;
- yields an empty diff unless strict policy requires failure.

## 17.6 Diff identity

File identity uses normalized paths relative to the resolved language directory or another explicitly versioned portable source identity.

Scenario identity uses stable scenario IDs from the explicit profile.

Change kinds:

```text
unchanged
improved
regressed
new
removed
```

Diff ordering is deterministic.

# 18. Phase 11 — Reporting and finalization

## 18.1 Reporting principle

Reports serialize existing evidence.

They must not:

- rerun GF;
- rescan source;
- reclassify results;
- reconstruct hidden configuration;
- mutate source or validation-profile files;
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

Finalized public artifacts may be consumed read-only by `gf-portfolio`; publication does not create a reverse runtime dependency.

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

An explicit completion marker, when used, is schema-controlled.

---

# 19. Exception and partial-result flow

## 19.1 Before run creation

Errors before run-path creation normally propagate as probe, configuration or invocation errors.

Examples:

- unsupported CLI arguments;
- missing or unreadable selected language path;
- selected non-`.gf` file;
- selected directory with no eligible GF sources;
- unresolved or ambiguous RGL source root;
- ambiguous module suffix or candidate choice;
- invalid optional validation profile;
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
- selected source mutation is detected;
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

Parallel execution is compatible only when it preserves:

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

# 24. Run result flow to callers

## 24.1 Return value

`execute_run` returns `RunResult`.

Callers inspect structured fields. No caller receives or mutates private module state.

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

- active portable language key and language directory;
- focused target when applicable;
- capability statuses;
- overall run status;
- important counts;
- direct failures;
- scenario failures when configured;
- artifact paths;
- warnings;
- run directory.

GUI convenience state may store the last successfully selected language path, explicit profile path and preferences.

It must not store the full `ResolvedLanguageContext` or `RunResult` as future execution authority.

# 25. Canonical orchestration pseudocode

```python
def open_language(request: LanguageProbeRequest) -> ResolvedLanguageContext:
    probe_result = projects.probe_language_path(
        selected_path=request.selected_path,
        explicit_profile=request.validation_profile,
    )
    if not probe_result.is_resolved:
        raise LanguageResolutionError(probe_result.diagnostics)
    return probe_result.context


def execute_run(request: RunRequest) -> RunResult:
    validate_resolved_language_context(request.language_context)
    resolved = runs.resolve_run_request(request)

    started_at = clock.utc_now()
    started_clock = clock.monotonic_now()
    run = runs.initialize(resolved, started_at)

    try:
        preflight = validation.preflight_requested_capability(
            language_context=resolved.language_context,
            profile=resolved.validation_profile,
            tool_policy=resolved.tool_policy,
            run_paths=run.paths,
            mode=resolved.mode,
        )

        plan = runs.resolve_execution_plan(
            request=resolved,
            preflight=preflight,
        )

        selection = validation.select_files(plan.file_selection)

        file_results = [
            validation.run_file_pipeline(
                file_path=file_path,
                language_context=resolved.language_context,
                run_paths=run.paths,
                plan=plan,
            )
            for file_path in selection.included_files
        ]

        file_results = diagnostics.classify_file_results(file_results)

        scenario_results = validation.run_selected_scenarios(
            plan=plan,
            language_context=resolved.language_context,
            profile=resolved.validation_profile,
            run_paths=run.paths,
            file_results=file_results,
        )

        scenario_results = diagnostics.classify_scenario_results(
            scenario_results=scenario_results,
            file_results=file_results,
        )

        pgf_result = validation.run_pgf_stage_if_required(
            plan=plan,
            language_context=resolved.language_context,
            profile=resolved.validation_profile,
            run_paths=run.paths,
        )

        result = runs.aggregate(
            request=resolved,
            run=run,
            preflight=preflight,
            selection=selection,
            file_results=file_results,
            scenario_results=scenario_results,
            pgf_result=pgf_result,
            timing=runs.finish_timing(started_at, started_clock),
        )

        result = runs.apply_release_gates(result, plan)
        result = diagnostics.add_top_errors(result)

        if plan.compare_previous:
            result.diff_entries = runs.compare_previous_result(result)

        reporting.publish_reports_best_effort(result)
        reporting.write_and_validate_manifest(result)
        runs.finalize(result)

        return result

    except CancellationRequested as exc:
        result = runs.build_cancelled_result(run, exc)
        reporting.publish_partial_result_if_safe(result)
        runs.finalize_partial(result)
        return result

    except Exception as exc:
        result = runs.build_error_result(run, exc)
        reporting.publish_partial_result_if_safe(result)
        runs.finalize_partial(result)
        return_or_raise_at_entrypoint_boundary(result, exc)
```

This pseudocode defines ordering, ownership and dependency direction. It does not prescribe private helper names or concrete adapter classes.

# 26. Startup and run state machines

## 26.1 Startup state machine

```text
INTRODUCTION
   |
   v
PATH_SELECTED
   |
   v
PROBING_LANGUAGE
   |
   +--> NEEDS_USER_INPUT --> INTRODUCTION or PROBING_LANGUAGE
   +--> INVALID_SELECTION --> INTRODUCTION
   |
   v
LANGUAGE_RESOLVED
   |
   v
RUNTIME_COMPOSED
```

The main runtime exists only after `LANGUAGE_RESOLVED`.

A language switch disposes `RUNTIME_COMPOSED` and returns to `INTRODUCTION`.

## 26.2 Run state machine

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

# 27. Observability

## 27.1 Master evidence

Master evidence records stage transitions and important decisions.

Recommended events:

```text
language_context_resolved
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
- Selected source and validation-profile paths are validated.
- Run-owned output remains inside approved roots.
- `.gfs` scenarios are treated as executable input.
- Shell-capable scenario commands are disabled unless explicitly authorized.
- Timeouts are finite.
- Process-tree termination is platform-aware.
- Raw evidence is preserved before normalization.
- Reports do not contain secrets or full environment dumps.
- Gold files are read-only during normal validation.
- Cleanup is not part of normal run execution.
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
normal validation run -> gold update
normal validation run -> source mutation
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
├── test_language_probe_flow.py
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

## 30.1 Entry-point and startup tests

Verify:

- GUI always begins at the introduction surface;
- CLI and GUI produce equivalent `LanguageProbeRequest` for equivalent values;
- both accept a language directory and a `.gf` file;
- both invoke the same language-probe application use case;
- neither enumerates GF sources or builds GF paths directly;
- the main runtime is not composed after unresolved or invalid probe results;
- remembered paths are fully revalidated;
- CLI exit code derives from structured probe or `RunResult` status.

## 30.2 Language-context and configuration tests

Verify:

- selected file maps to its parent language directory;
- selected directory remains the candidate language directory;
- nearest supported RGL source root is resolved deterministically;
- unsupported layouts fail closed or require an explicit profile;
- source inventory is delegated to the file selector;
- module suffix detection is unique or explicitly ambiguous;
- focused target is preserved;
- application state does not override language identity;
- optional profile conflicts are rejected;
- release mode requires a release-capable profile;
- source-ready and scan-ready operation can succeed without GF;
- unsafe output or source roots are rejected.

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

Verify file identity is portable and relative to the resolved language context.

## 30.4 GF-path and compilation tests

Verify:

- one effective GF path resolution is reused by compilation, scenarios and PGF work;
- the probe does not construct subprocess commands;
- exact missing-module remediation is bounded;
- zero, one and multiple exact matches have distinct results;
- no all-language GF path is constructed;
- raw GF evidence is preserved.

## 30.5 Scenario-flow tests

Verify:

```text
execute
capture raw
validate markers
normalize
compare gold
build result
```

Verify scenarios require an explicit profile or registration.

Verify normal execution does not modify gold.

## 30.6 Release-flow tests

Verify:

- release mode without a release profile is unavailable;
- required scenarios run;
- PGF build is distinct from file compilation;
- missing PGF fails release;
- invalid manifest prevents release success;
- optional diagnostic success cannot bypass required release failure.

## 30.7 Partial-flow tests

Verify:

- probe failure before run creation;
- configuration failure before run creation;
- failure after run creation;
- best-effort independent report writing;
- partial `RunResult`;
- cancellation;
- timeout;
- manifest failure;
- previous-run incompatibility does not corrupt current evidence.

## 30.8 Language-switch isolation tests

Verify:

- switching is rejected during an active run;
- switching disposes the old runtime before resolving the new one;
- source files, GF paths, targets, scenarios, golds and previous-run baselines from language A do not survive in language B;
- exactly one language identity appears in every ordinary run.

## 30.9 Determinism tests

Verify stable:

- source order;
- candidate role order;
- GF path order and provenance;
- scenario order;
- result order;
- top errors;
- diff;
- manifest;
- report sections.

# 31. Change control

A change to startup resolution, execution order or stage selection must identify:

```text
Affected startup or run phase:
Current behavior:
New behavior:
Reason:
Selected-path impact:
ResolvedLanguageContext impact:
Modes affected:
Optional-profile impact:
GF-path impact:
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
[ ] ADR-0015 reviewed
[ ] language-probe ownership reviewed
[ ] public file-selection contracts reviewed
[ ] ResolvedLanguageContext reviewed
[ ] run orchestration updated
[ ] all affected stages reviewed
[ ] RunRequest and RunConfig reviewed
[ ] RunPaths reviewed
[ ] RunResult reviewed
[ ] application-state migration reviewed
[ ] GF-path resolver reviewed
[ ] external-tool lock reviewed
[ ] interfile lock reviewed
[ ] persisted-schema lock reviewed
[ ] mode documentation updated
[ ] GUI and CLI startup documentation updated
[ ] report documentation updated
[ ] security impact reviewed
[ ] unit tests updated
[ ] integration tests updated
[ ] two-language isolation test updated
[ ] migration documented when needed
```

A local change that alters selected-path interpretation, resolved identity, effective GF path or observable evidence is an architectural change.

---

# 32. Related documents

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/architecture/PRODUCT_BOUNDARIES.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/DEPENDENCY_RULES.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0002-GF-AS-EXECUTION-ENGINE.md
docs/decisions/ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md
docs/decisions/ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md
docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md
docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS.md
docs/decisions/ADR-0014-CATALOG-DRIVEN-LANGUAGE-STARTUP.md
docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/gf/GF_PATH_RESOLUTION.md
docs/validation/FILE_SELECTION.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
docs/scenarios/SCENARIO_FORMAT.md
docs/reports/REPORTING_OVERVIEW.md
docs/reference/STATUS_VALUES.md
SECURITY.md
```

ADR-0014 is retained as a superseded historical decision and is not a runtime authority.

---

# 33. Governing rule

GF Wordbench is a path-resolved, single-language runtime orchestrator.

The user or caller remains authoritative for the initial selected language path.

`ResolvedLanguageContext` remains authoritative for the active language, source boundary and startup path facts during the session.

An explicit validation profile remains authoritative only for the advanced policy it declares, such as checkpoints, scenarios, golds and release gates.

GF remains authoritative for grammar parsing, type checking, compilation and module resolution.

GF Wordbench remains authoritative for:

- bounded language-path probing;
- configuration resolution;
- stage ordering;
- evidence capture;
- classification;
- comparison;
- reporting;
- final status.

Therefore:

> No caller may bypass language-context resolution or run orchestration, no stage may silently take ownership of another stage, and no run may be declared complete before its required evidence, reports, artifacts and manifest are finalized.
