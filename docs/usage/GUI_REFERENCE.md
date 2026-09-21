# GF Wordbench — GUI Reference

**Document ID:** `GF-WB-GUI-REFERENCE`  
**Status:** Normative user-interface and interaction reference  
**Applies to:** GF Wordbench desktop GUI, shared language-probe and validation services, application state, optional validation profiles and generated run artifacts  
**Owner:** GF Wordbench maintainers  
**Document version:** `3.0.0`  
**Last reviewed:** 2026-08-05  
**Primary platform:** Windows  
**GUI toolkit:** PySide6 / Qt Widgets  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related decisions:** `docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md`, `docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md`  
**Related locks:** `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`, `docs/PERSISTED_SCHEMA_LOCK.md`

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

This document defines the GF Wordbench desktop graphical interface.

It specifies:

- GUI responsibilities and limits;
- path-resolved language startup;
- introduction, language-probe and main-window flows;
- one active resolved language context per session;
- optional validation-profile selection;
- capability presentation;
- validation modes and run options;
- resolved-plan preview;
- input validation and confirmation;
- background execution and cancellation;
- progress and result presentation;
- artifact navigation;
- local application state;
- GUI and CLI equivalence;
- accessibility, security and performance;
- testing and anti-drift rules.

The GUI is an entrypoint into the shared GF Wordbench application.

It is not a separate language detector, file selector, GF path resolver, validation engine or reporting engine.

---

## 2. Product boundary

One GUI session has either:

```text
no loaded language
or
exactly one immutable ResolvedLanguageContext
```

One ordinary validation run records exactly one language identity and one resolved source context.

The GUI does not provide:

- several simultaneously active languages;
- a multilingual workspace registry;
- cross-language result aggregation;
- portfolio readiness or comparison;
- `gf-portfolio` storage or services.

The user may replace the active language when no run is active. Replacement disposes the previous runtime and resolves a new language context.

The independent product `gf-portfolio` may open or consume public versioned Wordbench artifacts.

GF Wordbench GUI functionality remains complete when `gf-portfolio` is absent.

---

## 3. Related authorities

Read this document with:

```text
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/PRODUCT_BOUNDARIES.md
docs/architecture/EXECUTION_FLOW.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/validation/FILE_SELECTION.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/gf/GF_PATH_RESOLUTION.md
docs/usage/CLI_REFERENCE.md
docs/reports/REPORTING_OVERVIEW.md
docs/reports/RAW_LOGS_REFERENCE.md
```

Specialized locks and owner documents govern their respective contracts.

Where an older document still makes the catalog, a language bundle or `<validation-profile-root>/project.toml` mandatory for startup, ADR-0015 and this reference govern the GUI behavior until the coordinated documentation update is complete.

---

## 4. Core GUI rule

> The GUI collects user intent, calls shared application services, displays structured language resolution, progress and results, and opens owned artifacts.

The GUI must not:

- enumerate GF language sources independently;
- infer language identity inside widgets;
- construct an independent GF path;
- compile GF modules directly;
- execute `.gfs` scenarios directly;
- construct an independent GF command model;
- implement separate file-selection or status aggregation;
- parse raw GF output independently when canonical diagnostics exist;
- parse Markdown reports to discover run results;
- reclassify diagnostics;
- normalize scenario output;
- update gold files during normal validation;
- silently create or rewrite a catalog;
- silently create or rewrite a language bundle;
- silently rewrite a validation profile;
- store resolved language facts only in GUI state;
- use different defaults or semantics from the CLI;
- depend on `gf-portfolio`.

Equivalent GUI and CLI inputs produce equivalent language-probe results, resolved language contexts, run configurations and pipeline behavior after canonical normalization.

---

## 5. Information model

The GUI presents four distinct layers.

### 5.1 Selected language intent

The user supplies exactly one primary path:

```text
a GF language directory
or
a .gf file inside a GF language directory
```

Examples:

```text
C:/mycode/Grammatical_Framework/gf-rgl/src/english
C:/mycode/Grammatical_Framework/gf-rgl/src/english/LangEng.gf
C:/mycode/Grammatical_Framework/gf-rgl/src/english/AdjectiveEng.gf
```

The selected path is machine-local intent. It is not by itself the portable language identity.

### 5.2 Resolved language context

Portable and runtime language facts come from `ResolvedLanguageContext`, including:

- portable language key;
- selected path kind;
- language directory;
- RGL source root;
- RGL root when resolved;
- focused file when selected;
- module suffix when unambiguous;
- available entrypoint candidates;
- selected source inventory or stable inventory reference;
- GF path requirements and provenance;
- structural diagnostics;
- capability statuses;
- optional validation-profile identity and digest.

These facts are read-only in ordinary run controls.

### 5.3 Environment

Machine-local values include:

- GF executable;
- output root;
- approved explicit path overrides;
- optional nonstandard-layout root hints.

The RGL root is normally derived from the selected language path. An explicit override is used only when the standard structure cannot be resolved or a supported nonstandard layout requires one.

These values may be stored in versioned local application state.

### 5.4 Run request

Run-specific choices include:

- validation mode;
- target file;
- checkpoint when a profile declares checkpoints;
- scenario scope when scenarios are configured;
- timeout override;
- diagnostic options;
- previous-run comparison.

Widgets collect a request. Shared application services resolve the canonical run configuration.

---

## 6. Ownership

### GUI entrypoint and presentation adapters own

- visual layout;
- widget state;
- file and directory dialogs;
- user confirmation;
- local presentation validation;
- background-worker lifecycle;
- progress presentation;
- cancellation requests;
- result rendering;
- artifact-opening actions;
- application-state synchronization.

### Language-probe application service owns

- selected-path interpretation;
- bounded source-root discovery;
- coordination of existing file-selection services;
- standard RGL candidate classification;
- ambiguity and remediation results;
- capability computation;
- construction of `ResolvedLanguageContext`.

### Bootstrap and application services own

- framework defaults;
- dependency composition;
- optional validation-profile loading;
- configuration precedence;
- environment resolution;
- canonical run configuration;
- run-path creation;
- mode prerequisites;
- plan preview.

### Validation application services own

- file selection;
- static scanning;
- GF path resolution through the GF boundary;
- GF compilation;
- diagnostics;
- scenario execution;
- gold comparison;
- PGF construction;
- release gates;
- previous-run comparison;
- run result;
- reports and manifest.

### Result readers own

- reading `summary.json`;
- schema validation;
- loading completed runs;
- optional manifest verification;
- exposing artifact references.

The GUI does not parse `summary.md` as a machine source.

---

## 7. Architecture

The GUI is an entrypoint and adapter in the hexagonal modular monolith.

Dependency direction:

```text
Qt widgets
    → GUI controller/presenter
    → language-probe and validation application use cases
    → ports
    → adapters
```

The GUI does not import validation-stage implementations directly.

Conceptual placement:

```text
src/gf_wordbench/
├── entrypoints/
│   └── gui/
├── projects/
│   └── languages/
├── validation/
├── runs/
├── diagnostics/
├── reporting/
├── state/
└── bootstrap.py
```

Internal filenames may vary while dependency direction remains fixed.

Worker code contains transport and lifecycle logic, not language-resolution or validation business rules.

---

## 8. Startup

Canonical launch forms may include:

```text
launch_gui.bat
python -m gf_wordbench.entrypoints.gui.main
```

All launch methods call one GUI entrypoint.

### 8.1 Canonical startup sequence

```text
create QApplication
→ install top-level exception handling
→ build startup-only dependencies
→ load versioned local state
→ import supported legacy state when present
→ show the introduction window
→ obtain one explicit language path or explicit “Open last language” action
→ run LanguageProbeService
→ present blocking diagnostics or ambiguity when required
→ publish one immutable ResolvedLanguageContext
→ compose the main runtime
→ create the main window
→ restore compatible presentation and run-selection state
→ persist the successful selected path as local convenience state
→ show the main window
→ enter the Qt event loop
```

The full main runtime does not exist before a resolved language context is available.

Startup does not automatically launch a validation run.

Language probing and passive environment checks are read-only, bounded and do not create a completed run.

### 8.2 Introduction actions

The introduction window provides at least:

```text
Open Last Language
Choose Language Directory
Choose GF File
Settings
Quit
```

`Open Last Language` is enabled only when local state contains a previously successful selected path.

Using that action reruns complete path and containment validation. It does not restore a previously serialized runtime context.

### 8.3 Source-ready startup

The main window may open when the context is `source-ready`, even when:

- GF is not installed;
- GF cannot be launched;
- no scenarios are configured;
- no gold files exist;
- no validation profile is loaded;
- release requirements are unavailable.

Unavailable capabilities are shown explicitly and only their dependent controls are disabled.

### 8.4 Fatal and nonfatal startup errors

A malformed application installation or unrecoverable bootstrap failure is fatal.

An invalid selected language path is not a fatal application error. It produces a structured probe result and returns to the introduction window.

Fatal startup errors show:

- concise title;
- actionable message;
- technical details when requested;
- log path when available.

---

## 9. Shutdown

### Normal close

On close:

1. synchronize permitted preferences;
2. persist state atomically;
3. retain completed-run pointers;
4. close dialogs;
5. release worker resources;
6. dispose the active language runtime;
7. exit the Qt event loop.

### Close during an active run

The GUI displays:

```text
A validation run is active.
Cancel the run and close GF Wordbench?
```

Choices:

```text
Continue Running
Cancel and Close
```

When cancellation is requested, the GUI:

- uses the shared cancellation interface;
- keeps the event loop responsive;
- applies a bounded shutdown wait;
- preserves partial evidence;
- does not record success;
- persists no active-running state.

---

## 10. Main-window goals

The main window lets the user:

1. identify the active resolved language;
2. inspect the selected source context;
3. understand available capabilities;
4. validate the local GF environment;
5. optionally load or inspect a validation profile;
6. choose a validation mode;
7. set mode-relevant options;
8. inspect the resolved plan;
9. start or cancel a run;
10. observe structured progress;
11. understand the run outcome;
12. open generated artifacts;
13. inspect recent compatible runs;
14. replace the active language when no run is active.

Advanced controls remain collapsed or placed in a dedicated dialog.

---

## 11. Main-window information architecture

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ GF Wordbench — <Language>                                  <App Version>    │
├────────────────────────────────────────────────────────────────────────────┤
│ Language                                                                  │
│ Key | Source directory | Focused file | Profile | Resolution status       │
├────────────────────────────────────────────────────────────────────────────┤
│ Capabilities                                                              │
│ Source | Scan | Compile | Scenario | Release                              │
├────────────────────────────────────────────────────────────────────────────┤
│ Environment                                                               │
│ GF executable | GF version | RGL source root | Output root                │
├────────────────────────────────────────────────────────────────────────────┤
│ Validation                                                                │
│ Mode | Target/checkpoint | Scenario scope | Main options                  │
├────────────────────────────────────────────────────────────────────────────┤
│ Resolved Plan                                                             │
│ Files | Entrypoints | GF path | Scenarios | PGF | Previous comparison     │
├────────────────────────────────────────────────────────────────────────────┤
│ [Run Validation] [Cancel] [Change Language] [Open Last Run] [Reports]      │
├────────────────────────────────────────────────────────────────────────────┤
│ Progress                                                                  │
│ Status | Stage | Subject | Progress | Elapsed time                        │
├────────────────────────────────────────────────────────────────────────────┤
│ Results / Activity                                                        │
│ Summary, diagnostics, warnings and bounded activity                       │
└────────────────────────────────────────────────────────────────────────────┘
```

Visual arrangement may evolve.

Information ownership and semantics are normative.

---

## 12. Language section

Display:

```text
Language key
Display name
Module suffix, when available
Selected path
Selected path kind
Language directory
RGL source root
Focused GF file, when applicable
Detected entrypoint candidates
Resolution status
Validation-profile status
```

Resolved language identity and paths are read-only in the validation screen.

### 12.1 Language selection

The introduction window accepts:

```text
one directory
or
one .gf file
```

The GUI passes the path unchanged as user intent to `LanguageProbeService`, subject only to platform path normalization required by the public request contract.

The GUI does not enumerate the directory, derive a suffix or identify entrypoints itself.

### 12.2 Probe result

A successful probe displays:

- portable language key;
- language directory;
- RGL source root;
- focused target if one was selected;
- detected module suffix when unique;
- detected entrypoint candidates;
- capability statuses;
- nonblocking warnings;
- resolution provenance.

A probe requiring input displays exact candidate choices and the reason a choice is required.

### 12.3 Focused file

Selecting a file such as:

```text
AdjectiveEng.gf
```

keeps that file as the focused target.

Detected `LangEng.gf`, `GrammarEng.gf` or `AllEng.gf` files may be offered as additional candidates. The GUI does not silently replace the user-selected file.

### 12.4 Language replacement

Only one language is active in one session.

Replacement:

1. requires no active run;
2. asks for confirmation when unsaved UI-only edits would be discarded;
3. disposes the current runtime and workers;
4. returns to the introduction window;
5. resolves another explicit selected path;
6. clears language-derived choices and previous-run eligibility;
7. retains compatible machine-local preferences;
8. creates a new runtime only after successful resolution;
9. does not modify the previous source tree.

A missing previously selected path produces a nonfatal notice. The GUI does not select an unrelated directory automatically.

---

## 13. Capability section

The GUI displays five independent capability states:

```text
Source Ready
Scan Ready
Compile Ready
Scenario Ready
Release Ready
```

Each capability is one of:

```text
Ready
Unavailable
Warning
Checking
Unknown
```

These presentation states are not run validation statuses.

### 13.1 Source Ready

Enables:

- source browsing;
- target selection;
- metadata display;
- source fingerprinting.

### 13.2 Scan Ready

Enables deterministic static scanning without requiring GF.

### 13.3 Compile Ready

Requires:

- a resolved GF executable;
- valid effective GF path;
- at least one explicit compile target;
- successful compilation preflight.

### 13.4 Scenario Ready

Requires an explicit scenario registry or validation profile with valid scenario inputs.

### 13.5 Release Ready

Requires an explicit validation profile with complete release targets, required stages, scenarios, golds and artifact policy.

### 13.6 Isolation

An unavailable capability disables only dependent controls.

Examples:

```text
GF unavailable
→ browsing and static scan remain available
→ compilation, scenarios and release are unavailable

No validation profile
→ quick source validation remains available
→ checkpoint, scenario and release controls may be unavailable
```

---

## 14. Environment section

### 14.1 GF executable

Display:

```text
executable path
resolution source
detected GF version
compatibility result
```

Before a required GF-backed run:

- the path or command resolves;
- the selection is not a directory;
- launchability is checked where appropriate;
- the resolved executable appears in the plan.

After confirmation, the GUI does not silently substitute another installation.

### 14.2 RGL source root

Display the RGL source root resolved from the selected path.

Validate:

- path exists;
- path is a directory;
- it contains the active language directory;
- resolved shared paths remain contained;
- compatibility policy is satisfied.

An unresolved RGL source root does not necessarily prevent an unrelated source-ready operation on a standalone GF directory, but it blocks operations whose path policy requires the standard RGL layout.

### 14.3 Explicit root override

An override is available only for supported nonstandard layouts or failed standard-root detection.

It:

- is clearly marked;
- is validated through shared path services;
- appears in resolution provenance and run evidence;
- never rewrites source files;
- is not silently reused for an unrelated selected language.

### 14.4 Output root

Requirements:

- resolved path is explicit;
- directory exists or can be created;
- write access is available;
- source directories are protected;
- a run directory is never overwritten.

### 14.5 Test Environment

A bounded environment check may:

- resolve and probe GF;
- validate the resolved source root;
- validate the effective GF path;
- validate output access;
- show compatibility.

It does not compile active sources unless an explicit GF verification or smoke operation is selected.

---

## 15. Optional validation profile

A validation profile may define:

```text
source filters
entrypoints
checkpoints
GF path requirements
scenarios
inputs
golds
PGF targets
release gates
expected artifacts
project-specific documentation
```

An existing legacy `project/project.toml`, or a profile created from `templates/validation-profile/`, may be loaded explicitly as a validation profile.

The profile is not required for basic startup, browsing, source selection, static scan or focused compilation.

### 15.1 Profile actions

The GUI may provide:

```text
Load Validation Profile
Remove Validation Profile
Open Validation Profile
Validate Profile
```

### 15.2 Profile conflicts

A profile is rejected when it conflicts with the active language context, including:

- source root outside the selected context;
- language identity disagreement;
- target or scenario path escape;
- GF path selecting another language directory;
- gold or release assets belonging to another language.

### 15.3 Profile change

Changing or removing a profile:

- requires no active run;
- triggers complete context re-resolution;
- recreates the main runtime;
- clears incompatible choices;
- does not modify the profile unless an explicit editor workflow is used.

---

## 16. Validation modes

The GUI exposes exactly:

```text
quick
checkpoint
release
diagnostic
```

Display labels:

```text
Quick
Checkpoint
Release
Diagnostic
```

Persisted and structured values remain canonical lowercase identifiers.

Legacy state values may be imported as:

```text
file → quick
all  → diagnostic
```

They are not displayed as canonical modes.

Mode availability depends on the active context capabilities.

---

## 17. Quick mode

Purpose:

```text
fast validation during editing
```

Required control:

```text
Target file or module
```

The selector:

- lists active-language GF sources through shared selection services;
- preserves a focused file selected at startup;
- supports browsing inside approved roots;
- converts valid selections to stable source-relative identity;
- rejects paths outside allowed roots.

Typical options:

```text
Run static scan
Compile target
Run configured smoke scenario, when available
Compare with previous compatible run
Keep OK details
```

When GF is unavailable, `Run static scan` may remain enabled while `Compile target` is disabled with an accessible reason.

The plan shows target count, effective GF path, selected scenarios and whether PGF construction is excluded.

---

## 18. Checkpoint mode

Purpose:

```text
validate a declared subsystem from an explicit validation profile
```

Required control:

```text
Checkpoint
```

The checkpoint list comes from the active validation profile.

When no checkpoints are configured:

- checkpoint mode is disabled;
- the GUI explains that an explicit validation profile is required;
- quick and diagnostic source operations remain available when their capabilities are ready.

The GUI may show:

```text
checkpoint ID
display name
module count
scenario count
previous compatible outcome
previous run date
```

Historical values come from compatible `summary.json` files.

Checkpoint membership is not edited in the run screen.

---

## 19. Release mode

Purpose:

```text
evaluate all declared release criteria from an explicit validation profile
```

Release mode is enabled only when `Release Ready` is satisfied.

Confirmation shows:

```text
Language identity
Selected source context
Validation profile
GF version
Effective GF path
Entrypoints
Required checkpoints
Required scenarios
Gold comparisons
PGF targets
Output root
Strict policy
```

Required confirmation text clearly states that:

- every required stage executes;
- the run may take longer;
- gold files are not modified.

Release mode rejects:

```text
no_compile = true
skip required scenarios
skip required PGF construction
automatic gold update
ignore required artifact failure
missing release profile
```

The GUI displays release success only when:

```text
overall_status = OK
```

and required artifact integrity checks pass.

---

## 20. Diagnostic mode

Purpose:

```text
collect broad evidence for difficult source, path, environment or validation failures
```

Typical controls:

```text
subject scope
verbose GF output
keep OK details
dependency introspection
selected scenarios, when configured
extended timeout
maximum files
previous-run comparison
scan only
language-resolution evidence
```

### Global Scan from the GUI

For source-ready path-resolved sessions, Diagnostic mode has an explicit global
source-inventory behavior:

```text
Mode = Diagnostic
Target = empty
Run action = Run Global Scan
```

Leaving `Target` empty selects the complete resolved GF source inventory. The
run performs a static scan and an independent GF compilation for each selected
`.gf` source, continues after independent file failures, and preserves one raw
compile log pair per source. `Maximum files` bounds the inventory when a smaller
diagnostic sample is required.

Selecting a target keeps Diagnostic mode focused on that source instead of the
complete inventory. `Scan only` remains an evidence-only Diagnostic subprofile.

A completed Global Scan writes the normal human summary plus:

```text
details/global_scan.json
details/global_scan.csv
```

These expanded inventory artifacts distinguish direct, downstream (`BLOCKED`),
ambiguous, timeout and process-error outcomes and include a coarse failure
signature for grouping repeated compiler symptoms. They are diagnostic evidence,
not release evidence.

Diagnostic mode still enforces:

- finite timeouts;
- output containment;
- no shell injection;
- no automatic gold update;
- one resolved GF executable per GF-backed run;
- one effective GF path;
- bounded generation;
- bounded missing-module assistance.

When `Scan only` is selected, the GUI states:

```text
Compilation-dependent conclusions are unavailable.
This run cannot satisfy checkpoint or release criteria.
```

---

## 21. Mode-dependent controls

| Control | Quick | Checkpoint | Release | Diagnostic |
|---|:---:|:---:|:---:|:---:|
| Target file | Required | Hidden | Hidden | Optional |
| Checkpoint selector | Hidden | Required from profile | Read-only all | Optional from profile |
| Scenario filter | Optional when configured | Limited by profile | Read-only required set | Optional when configured |
| Scan only | Optional | Disabled | Disabled | Optional |
| Skip version probe | Warning | Restricted | Disabled | Optional |
| Keep OK details | Optional | Optional | Policy-controlled | Optional |
| CPU statistics | Optional | Optional | Optional | Optional |
| Maximum files | Hidden | Hidden | Disabled | Optional |
| PGF build | Hidden | Conditional | Profile-required | Optional |
| Previous comparison | Optional | Recommended | Policy-controlled | Optional |
| Validation profile | Optional | Required | Required | Optional |

Disabled controls explain their policy through accessible text or tooltips.

---

## 22. Advanced options

Possible advanced controls:

```text
timeout override
keep OK details
previous-run comparison
skip version probe
scan only
GF CPU statistics
maximum files
explicit GF path override
verbose GF output
strict mode
missing-module assistance policy
```

Resolved-context facts remain read-only:

```text
language key
selected language directory
RGL source root
selected source inventory
module suffix
resolution provenance
```

Profile-owned facts remain read-only in ordinary run controls:

```text
source filters
entrypoints
checkpoint membership
required scenarios
release gates
```

An expert override:

- is clearly marked;
- appears in the resolved plan;
- is recorded in run evidence;
- never rewrites source or profile configuration;
- cannot produce release success when it violates release policy.

---

## 23. Resolved-plan panel

Before execution, show:

```text
Mode
Language key
Selected source context
Validation-profile identity, when present
GF executable
GF version or probe state
RGL source root
Effective GF path and provenance
Output root
Target or checkpoint
Selected files
Selected entrypoints
Selected scenarios
Gold comparisons
PGF targets
Timeouts
Previous-run comparison
Capability prerequisites
Strict constraints
Overrides
```

The plan comes from shared bootstrap and preview services.

The GUI does not duplicate selection or GF path algorithms.

Any relevant widget, profile or environment change invalidates or rebuilds the preview.

Estimates are labeled explicitly when exact selection requires a full operation.

---

## 24. Input validation

The GUI checks obvious local errors before confirmation:

- required field empty;
- file or directory missing;
- selected startup file is not `.gf`;
- invalid integer;
- invalid regex;
- target outside the resolved source context;
- unknown checkpoint;
- unwritable output;
- contradictory options;
- requested mode unavailable for the current capability state.

Rules shared with CLI use shared validators.

Errors appear beside fields and in a concise summary, with focus moved to the first invalid field.

Passing GUI validation means only that the request is ready for application validation.

---

## 25. Confirmation

Confirmation is required for:

- checkpoint runs;
- release runs;
- broad diagnostic runs;
- risky expert overrides;
- proposed GF path remediation when policy requires user approval.

Release confirmation cannot be disabled.

The dialog separates:

```text
Blocking errors
Warnings
Resolved plan
```

Only resolved values are shown.

The Run action remains disabled while blocking errors exist.

---

## 26. Execution

Language probing, broad inventory work and validation runs execute outside the Qt GUI thread when they may block perceptibly.

Supported mechanisms may include:

```text
QThread with worker QObject
QThreadPool with QRunnable
background controller service
```

Requirements:

- the UI remains responsive;
- workers receive immutable requests or resolved configuration;
- progress crosses thread boundaries through structured events;
- widgets update only on the GUI thread;
- exceptions return as structured framework errors;
- cleanup is deterministic.

A validation worker calls one application use case.

It does not call scanner, compiler, scenario runner or report writers directly.

Ordinary source or project failure returns a structured result, not an exception.

---

## 27. Running state

While a run is active:

- Run is disabled;
- language replacement is disabled;
- validation-profile replacement is disabled;
- environment editing is disabled;
- mode and target editing are disabled;
- advanced options are disabled;
- Cancel is enabled;
- completed prior-run artifacts remain accessible;
- progress remains visible.

The GUI keeps separate references to:

```text
last completed run
current active run
```

Starting a run does not erase the last completed run.

---

## 28. Cancellation

A visible Cancel action is available during work.

First request:

- sends cancellation through the shared token or port;
- displays `Cancelling…`;
- prevents repeated duplicate requests;
- does not block or terminate the GUI thread.

The application:

- stops scheduling new work;
- terminates owned processes according to policy;
- preserves partial evidence;
- returns a non-successful result when possible.

Completion wording:

```text
Run cancelled
```

Cancellation is not displayed as success or ordinary source failure unless an additional framework error exists.

---

## 29. Progress

Show:

```text
current stage
current subject
completed subjects
total subjects when known
elapsed time
warning count
failure count
```

Language-probe progress may show bounded stages such as:

```text
Validating selected path
Resolving source root
Selecting source files
Classifying language modules
Resolving capabilities
```

Use indeterminate progress when totals are unknown.

Progress comes from structured application events.

The GUI does not infer progress from activity-log line counts.

---

## 30. Activity panel

The activity view is bounded presentation, not `raw/master.log`.

It may show:

- language-resolution stages;
- path or capability warnings;
- validation-stage transitions;
- current subject;
- concise diagnostics;
- counts;
- artifact paths.

The GUI may cap lines for performance.

`Clear Activity` clears only the widget.

It does not delete run evidence.

Secrets and full environment dumps are prohibited.

---

## 31. Completion summary

Display:

```text
Overall status
Mode
Language
Resolved source context
Validation profile, when present
Run ID
GF version
Duration
Files OK / FAIL / ERROR / SKIPPED
Scenarios OK / FAIL / ERROR / SKIPPED
Direct failures
Downstream failures
Ambiguous failures
Release gates
Regression summary
Run directory
```

Completion wording:

```text
Validation passed
Validation completed with failures
Validation error
Run cancelled
```

Color is supplemental.

Status is also conveyed through text, icon or shape and accessible name.

---

## 32. Diagnostic result view

Separate:

```text
Language-resolution errors
Framework and environment errors
Direct failures
Required scenario failures
Ambiguous failures
Downstream failures
Gold mismatches
Artifact failures
Nonblocking scan findings
Regressions
```

Direct failures appear before cascades.

Downstream rows link to blockers when known.

Evidence actions may include:

```text
Open stdout
Open stderr
Open scan log
Open detail report
Open source location
Open scenario output
Open gold diff
Open path-resolution evidence
```

Only existing owned paths are enabled.

The GUI consumes diagnostic classification from structured results.

---

## 33. Artifact navigation

Required actions:

```text
Open Run Directory
Open Machine Summary
Open Human Summary
Open AI Ready Packet
Open Master Log
Open All Operation Logs
Open All Scan Logs
Open Manifest
```

Conditional actions:

```text
Open PGF Directory
Open Scenario Output
Open Gold Diff
Open Detail Report
Open Resolution Evidence
```

Machine summary opens:

```text
summary.json
```

Human summary opens:

```text
summary.md
```

When an artifact is missing:

- show a clear error;
- retain the result view;
- offer the run directory;
- do not reconstruct or regenerate the artifact silently.

---

## 34. Completed runs

A recent-runs view may show:

```text
Run ID
Date
Language
Source-context identity
Validation profile
Mode
Overall status
GF version
Duration
Direct failures
Scenario failures
Regression count
```

Data comes from:

```text
summary.json
```

and may be verified with:

```text
manifest.json
```

Unsupported schemas are labeled explicitly.

Historical status is not extracted from Markdown.

---

## 35. Run comparison

Compatible runs may be compared using structured diff entries.

Display categories:

```text
Regressed
New
Improved
Removed
Unchanged
```

Eligibility requires compatible:

- language identity;
- resolved source-context policy;
- target or checkpoint identity;
- relevant validation-profile identity and digest;
- schema and normalization contracts.

The GUI does not implement independent transition or compatibility rules.

Cross-language portfolio comparison remains outside Wordbench.

---

## 36. Application state

Canonical state file:

```text
.gf_wordbench_state.json
```

Schema:

```text
gf-wordbench.app-state/1.1
```

Application state stores disposable local preferences.

Deleting it does not damage source, profiles or run artifacts.

### 36.1 Permitted environment fields

```text
last_selected_language_path
last_selected_validation_profile
last_rgl_root
gf_executable
output_root
```

### 36.2 Permitted selection fields

```text
mode
target_file
checkpoint_id
timeout_sec
max_files
keep_ok_details
diff_previous
skip_version_probe
no_compile
emit_cpu_stats
```

Only fields compatible with the newly resolved language context are restored.

### 36.3 Permitted completed-run fields

```text
run_dir
summary_path
status_message
language_key
```

### 36.4 Runtime-only fields

Never persist:

```text
is_running = true
resolved_language_context
current_run_config
current_run_result
worker object
thread object
dialogs
progress subscriptions
cancellation token
```

Startup always begins with no active run and no trusted resolved language context.

---

## 37. Resolved facts excluded from GUI state

Do not store independent authoritative copies of:

```text
portable language key
language directory
RGL source root
selected source inventory
module suffix
resolved GF path
entrypoints
checkpoints
required scenarios
optional scenarios
release artifact policy
capability statuses
resolution diagnostics
```

These facts come from fresh language resolution and an optional explicit validation profile.

Application state may remember paths and presentation choices only.

Expert overrides remain explicitly separate from resolved authority.

---

## 38. State persistence

State is saved:

- after meaningful preference changes, with debounce;
- on normal close;
- after a completed run;
- after successful language resolution;
- after selecting an environment or optional validation-profile path.

Requirements:

- atomic replacement;
- UTF-8;
- versioned schema;
- no secrets;
- safe recovery from malformed state;
- save failure shown as a warning;
- no loss of the current run result.

Local state paths may be absolute.

Canonical writers use `/`; readers accept native separators.

A failed state write after successful language resolution does not invalidate the active context.

---

## 39. Legacy state import

The GUI may import predecessor state files and prior schema versions.

Supported mode mapping includes:

```text
all  → diagnostic
file → quick
```

Legacy `project_root` may be retained as a candidate validation-profile path only when it resolves explicitly and is compatible with a newly selected language context.

A legacy catalog language ID is not converted through an unbounded filesystem search.

When no reliable selected path is available, the user is asked to choose a language directory or `.gf` file.

`is_running` and serialized runtime objects are never imported.

Import is atomic: the predecessor file remains untouched until the canonical state is written and verified.

---

## 40. Error presentation

Error dialogs separate:

```text
summary
recommended action
technical details
evidence path
candidate choices, when applicable
```

### 40.1 Language-resolution error

Example:

```text
Language could not be resolved

No eligible GF source files were found in:
C:/work/gf-rgl/src/english

Choose another language directory or GF file.
```

### 40.2 Ambiguous resolution

Example:

```text
More than one language module group was detected.

Choose the module group to use:
- Eng
- EngExt
```

The GUI does not preselect an arbitrary candidate.

### 40.3 Configuration error

Example:

```text
Invalid configuration

GF executable does not exist:
C:/tools/gf/gf.exe

Select another executable and try again.
```

### 40.4 Validation failure

Ordinary source or profile `FAIL` appears in the result view rather than as an exception.

### 40.5 Framework error

Show:

- concise message;
- run directory when created;
- machine summary when available;
- expandable technical details;
- Copy Details action.

### 40.6 Fatal GUI error

The top-level handler:

- logs technical details;
- shows a critical dialog;
- avoids secrets;
- preserves state where safe.

---

## 41. Warnings

Warnings are visible in:

- language-probe results;
- confirmation;
- running activity;
- completion results;
- reports when applicable.

Examples:

- module suffix could not be established;
- no standard entrypoint candidate found;
- GF version outside the tested range;
- missing optional shared path;
- low output disk space;
- unavailable previous baseline;
- no validation profile loaded;
- optional scenario unavailable;
- expert override active;
- scan-only diagnostic request;
- nonblocking static findings.

Warnings block only when the governing capability or validation policy makes them blocking.

---

## 42. File and directory dialogs

### 42.1 Language selection dialogs

Initial location precedence:

1. current valid selected-language path;
2. last successfully selected language path;
3. last resolved RGL source root;
4. user home.

The language-directory dialog accepts directories.

The GF-file dialog filters primarily for:

```text
*.gf
```

Cancelling preserves the introduction state and current value.

### 42.2 Target dialogs

Initial location precedence:

1. current target;
2. active language directory;
3. last relevant directory;
4. user home.

Valid selected target paths are displayed relative to the active source context where practical.

Containment uses shared normalized path policy, not string-prefix comparison.

### 42.3 Profile dialogs

Validation-profile dialogs do not automatically search ancestors. The user selects the profile explicitly.

---

## 43. Keyboard and accessibility

Minimum shortcuts:

```text
Ctrl+R        Run validation
Esc           Close dialog or request cancellation where safe
Ctrl+O        Choose language directory
Ctrl+Shift+O  Choose GF file
Ctrl+Alt+O    Open last run directory
Ctrl+L        Focus activity/results
Ctrl+,        Open settings
F1            Open help
```

Release validation always requires confirmation.

Accessibility requirements:

- keyboard-only navigation;
- screen-reader labels;
- visible focus;
- high-DPI scaling;
- platform text scaling;
- status independent of color;
- accessible names for icon-only controls;
- selectable error details;
- sufficient contrast;
- no information conveyed only by hover.

Result and candidate tables provide headers, row labels, keyboard navigation and accessible status text.

---

## 44. Localization

User-facing strings remain separate from logic.

Canonical identifiers are not translated:

```text
quick
checkpoint
release
diagnostic
source-ready
scan-ready
compile-ready
scenario-ready
release-ready
OK
FAIL
ERROR
SKIPPED
```

Raw GF diagnostics remain verbatim in evidence.

Qt translation facilities may localize presentation labels.

---

## 45. Window and settings state

Optional presentation state may include:

```text
window size and position
splitter positions
selected results tab
column widths
theme preference
introduction-window geometry
```

Such fields require schema definition before persistence.

Restored windows must remain visible on current monitors.

Invalid geometry falls back to safe defaults.

A settings dialog may contain:

```text
Environment
Execution defaults
Reports
Retention
Appearance
Advanced
```

Resolved language identity, profile entrypoints, scenarios and release rules do not belong in general application settings.

---

## 46. Validation-profile workflow

Profile editing is separate from ordinary run controls.

A profile editor must:

- validate the canonical profile schema;
- validate compatibility with the active language context;
- show an exact diff before saving;
- write atomically;
- avoid edits during active runs;
- separate profile facts from local environment values;
- preserve or explicitly manage TOML comments;
- coordinate dependent profile contracts.

When no safe editor is provided, the GUI opens the selected profile in the configured external editor.

The GUI does not create a profile merely to open a language.

---

## 47. Gold update workflow

Gold updates are separate from normal validation.

A dedicated workflow:

1. requires an explicit scenario-capable validation profile;
2. selects one scenario;
3. executes it;
4. normalizes output;
5. displays expected and actual diff;
6. requires explicit approval;
7. writes the gold file atomically;
8. records the update.

It is unavailable during normal active runs, never triggered automatically and prohibited during release validation.

---

## 48. GUI and CLI equivalence

For equivalent explicit inputs:

```text
GUI LanguageProbeRequest == CLI LanguageProbeRequest
GUI ResolvedLanguageContext == CLI ResolvedLanguageContext
GUI resolved RunConfig == CLI resolved RunConfig
```

following canonical normalization and presentation-independent path representation.

Equivalence includes:

- selected language path;
- selected path kind;
- language identity;
- resolved source root;
- module candidate classification;
- capability status;
- optional validation-profile identity;
- mode;
- environment;
- target or checkpoint;
- timeouts;
- flags;
- selected scenarios;
- output root;
- strict policy;
- release gates;
- report set.

Allowed differences are presentation-only:

- dialogs;
- visual progress;
- browser controls;
- interactive cancellation;
- artifact-opening actions.

---

## 49. Loading an existing run

Sequence:

```text
select run directory
→ read summary.json
→ validate schema
→ optionally verify manifest
→ build read-only result view
```

Unsupported schema:

```text
This run uses an unsupported summary schema.
```

Available actions may include opening raw files or using an explicit migration tool.

A corrupt manifest produces an integrity warning without hiding the summary.

Unverified artifact links are marked clearly.

Loading a historical run does not change the active language context.

---

## 50. Security

The GUI:

- passes structured values to application services;
- does not construct host command strings;
- does not perform unbounded filesystem discovery;
- safely renders diagnostics, source excerpts, scenario output, labels and paths;
- uses platform-safe local-file opening APIs;
- confirms untrusted external URLs;
- does not bypass scenario security policy;
- does not persist or display tokens, passwords, private keys or full environment dumps;
- validates path containment through shared policy;
- records expert path overrides in evidence;
- never writes inside source directories during language probing.

---

## 51. Performance

Never perform on the GUI thread:

- GF execution;
- broad filesystem scanning;
- bounded but potentially large RGL source indexing;
- large hash computation;
- large manifest verification;
- historical-run indexing;
- report generation.

Simple selected-path checks may run synchronously only when their bounded latency is demonstrably negligible.

Large logs are streamed, virtualized or bounded with a link to the complete file.

Recent-run indexing occurs in the background.

Derived caches are invalidated when source, summary or manifest fingerprints change.

---

## 52. Active-run policy

One GUI instance permits one active validation run.

Starting a second run while one is active is prohibited.

Language replacement, profile replacement and resolved-path mutation are prohibited while a run is active.

Independent instances must still respect run-directory collision protection and source-write safety.

A queued multi-run engine requires a separate architectural contract.

---

## 53. Crash recovery

On startup, incomplete run directories may be presented as:

```text
Incomplete runs found
```

Actions may include:

```text
Open
Inspect
Archive
Delete through cleanup workflow
```

Incomplete runs are never marked successful.

Application state never restores an active-running flag or trusted resolved context.

A remembered language path is revalidated independently of incomplete-run recovery.

---

## 54. Controller flows

### 54.1 Introduction flow

```python
def on_language_path_selected(path: Path) -> None:
    view.set_probing(True)
    controller.start_language_probe(LanguageProbeRequest(selected_path=path))
```

```python
def on_language_probe_finished(result: LanguageProbeResult) -> None:
    view.set_probing(False)

    if result.needs_user_input:
        view.show_probe_choices(result)
        return

    if not result.is_resolved:
        view.show_probe_error(result)
        return

    runtime = bootstrap.build_language_runtime(result.context)
    state.record_last_selected_language_path(result.context.selected_path)
    show_main_window(runtime)
```

### 54.2 Run-request flow

```python
def on_run_requested() -> None:
    ui_request = view.collect_request()

    validation = gui_validator.validate(ui_request)
    if validation.has_errors:
        view.show_validation_errors(validation)
        return

    plan = bootstrap.preview_run(active_context, ui_request)
    view.show_plan(plan)

    if not view.confirm_run(plan):
        return

    controller.start_run(plan.run_config)
```

### 54.3 Worker flow

```python
def worker_run(run_config: RunConfig) -> None:
    try:
        result = run_validation(
            run_config,
            progress_callback=emit_progress,
            cancellation_token=cancellation_token,
        )
        emit_finished(result)
    except Exception as exc:
        emit_failed(capture_framework_error(exc))
```

### 54.4 Presentation flow

```python
def on_finished(result: RunResult) -> None:
    state.record_completed_run(result)
    view.set_running(False)
    view.render_result(result)
    state_store.save(state)
```

Signatures are illustrative. Public contracts remain owned by the interfile lock.

---

## 55. GUI request models

### 55.1 Language probe request

The introduction widgets produce conceptually:

```text
selected_path
optional_validation_profile
nonstandard_root_override
probe_options
```

This request is not a `ResolvedLanguageContext`.

### 55.2 Run request

The main-window widgets may produce:

```text
gf_executable
output_root
mode
target_file
checkpoint_id
scenario_filter
timeout_override
keep_ok_details
diff_previous
skip_version_probe
no_compile
emit_cpu_stats
strict
advanced_overrides
```

This request does not duplicate language context fields and is not a `RunConfig`.

Bootstrap resolves and validates it against the active immutable context.

---

## 56. Events

Structured events may include:

```text
language_probe_started
language_probe_stage_started
language_probe_warning
language_probe_needs_input
language_probe_finished
language_runtime_created
language_runtime_disposed
run_started
plan_resolved
stage_started
stage_progress
subject_started
subject_completed
warning_emitted
cancellation_requested
cancellation_acknowledged
run_finished
run_failed
```

Payloads are immutable structured values.

Qt signals transport events to the presentation layer.

Reports and automation do not depend on Qt.

---

## 57. Testing

### 57.1 Unit tests

Cover:

- state-to-introduction loading;
- file and directory path collection;
- dialog cancellation;
- probe-result presentation;
- ambiguity-choice presentation;
- capability-to-control mapping;
- state-to-main-window loading;
- widget-to-request collection;
- mode-dependent controls;
- source-relative target conversion;
- validation-message mapping;
- result wording;
- artifact-action enabling;
- last-run retention;
- legacy state import;
- close-during-run logic.

### 57.2 Controller tests

Use fake probe, bootstrap and application services.

Cover:

- introduction always appears before main runtime;
- invalid path does not construct main runtime;
- source-ready context can construct main runtime without GF;
- ambiguity does not auto-select a candidate;
- successful resolution persists only the selected path;
- state-save failure produces a warning;
- rejected run confirmation does not start work;
- one worker per run;
- progress routing;
- cancellation routing;
- structured `FAIL` is not an exception;
- infrastructure exception maps to `ERROR`;
- completed result updates state;
- worker cleanup;
- language replacement disposes the old runtime.

### 57.3 Qt tests

Cover:

- introduction actions;
- language file and directory dialogs;
- signals;
- button states;
- capability indicators;
- focus order;
- shortcuts;
- modal dialogs;
- thread-safe updates;
- close behavior;
- accessibility labels where testable.

### 57.4 Integration tests

With small fixture source trees:

- launch GUI to introduction;
- open a standard language directory;
- open one `.gf` file;
- browse and scan without GF;
- run successful quick compilation with real GF;
- display a missing-GF capability state;
- resolve a language requiring one shared path;
- present an ambiguous candidate without guessing;
- load a compatible optional validation profile;
- reject an incompatible profile;
- run a checkpoint profile;
- open run artifacts;
- cancel a bounded long operation;
- replace one language with another without contamination;
- restart and revalidate the remembered path;
- handle a stale remembered path safely.

### 57.5 CLI equivalence tests

Equivalent GUI and CLI path inputs must resolve to equal canonical probe results, contexts and run configuration.

### 57.6 Boundary tests

Verify GUI modules do not import or directly call:

```text
filesystem scanner
selection implementation
GF path implementation
compiler
scenario runner
gold comparator
report writers
```

Verify artifact paths come from structured results rather than hard-coded reconstruction.

---

## 58. Drift indicators

GUI drift exists when:

- the main runtime is constructed before language resolution;
- GUI and CLI resolve different language contexts or run configuration;
- GUI widgets enumerate GF source trees;
- GUI widgets infer module suffixes or entrypoints;
- GUI code constructs an independent GF path;
- GUI imports validation-stage implementations;
- normal startup requires a catalog or language bundle;
- normal startup requires scenarios or golds;
- visible modes use legacy identifiers;
- language-specific paths appear in framework GUI defaults;
- resolved facts are duplicated as application-state authority;
- `FAIL` is displayed as success;
- completed-run pointers are cleared at run start;
- Markdown is parsed for status;
- artifact paths are reconstructed;
- report generation is launched independently of run results;
- release mode permits forbidden skips;
- gold mismatch offers automatic overwrite;
- cancellation is represented as `OK`;
- workers update widgets outside the GUI thread;
- large logs are rendered without bounds;
- state persists an active-running flag or resolved runtime context;
- malformed state crashes startup;
- hidden values override confirmed visible values;
- language or profile switching occurs during a run;
- a stale remembered path selects an unrelated directory;
- ambiguity is resolved by first match;
- GUI behavior depends on `gf-portfolio`.

Any drift indicator requires coordinated contract and test correction.

---

## 59. Change checklist

```text
[ ] User goal identified
[ ] Introduction-flow impact reviewed
[ ] LanguageProbeRequest impact reviewed
[ ] ResolvedLanguageContext impact reviewed
[ ] Capability-state impact reviewed
[ ] Widget and application owner identified
[ ] Bootstrap impact reviewed
[ ] RunConfig impact reviewed
[ ] CLI equivalence reviewed
[ ] Application-state schema reviewed
[ ] Validation-profile impact reviewed
[ ] Mode matrix reviewed
[ ] Accessibility reviewed
[ ] Threading and cancellation reviewed
[ ] Error and ambiguity presentation reviewed
[ ] Artifact ownership reviewed
[ ] Security and path containment reviewed
[ ] Unit and Qt tests updated
[ ] Contract and integration tests updated
[ ] Owner documentation and locks updated
[ ] Compatibility behavior defined when public contracts change
[ ] Wordbench/Portfolio boundary preserved
```

A public GUI contract change is not implemented only in a widget file.

---

## 60. User workflows

### 60.1 First launch

1. Start GF Wordbench.
2. Choose a language directory or `.gf` file.
3. Review the resolved language and capability status.
4. Configure the GF executable when compilation is needed.
5. Select or confirm the output root.
6. optionally load a validation profile.
7. choose a validation mode.
8. review the resolved plan.
9. run validation.
10. open the generated reports.

### 60.2 Reopen last language

1. Start GF Wordbench.
2. Select `Open Last Language`.
3. Wordbench revalidates the remembered path.
4. Resolve any path or environment issue.
5. Continue in the main window.

### 60.3 Quick source validation

1. Choose `Quick`.
2. Select a GF source target or keep the focused startup file.
3. Select scan and compilation options according to available capabilities.
4. Review the effective GF path and target.
5. Run validation.
6. Review direct failures first.
7. Open evidence as needed.

### 60.4 Checkpoint validation

1. Load a validation profile that declares checkpoints.
2. Choose `Checkpoint`.
3. Select a declared checkpoint.
4. Review modules and scenarios.
5. Run validation.
6. Inspect gates and regressions.

### 60.5 Release validation

1. Load a complete release validation profile.
2. Resolve blocking environment and profile issues.
3. Choose `Release`.
4. Review the release plan.
5. Confirm the run.
6. Observe required stages.
7. Verify outcome and manifest.
8. Open release artifacts.

### 60.6 Diagnostic validation

1. Choose `Diagnostic`.
2. Select scope.
3. Enable only necessary advanced options.
4. Run validation.
5. Inspect language-resolution and framework errors first.
6. Inspect direct failures before downstream failures.
7. Use `AI_READY.md` and raw logs for deeper analysis.

### 60.7 Change language

1. Ensure no run is active.
2. Select `Change Language`.
3. Confirm runtime replacement when asked.
4. Choose another language directory or `.gf` file.
5. Review the new resolved context.
6. Continue with a newly composed runtime.

---

## 61. Troubleshooting

### GUI does not start

Check:

```text
Python environment
PySide6 installation
application traceback
launcher working directory
```

Run the Python module entrypoint from a terminal to expose startup errors.

### Language cannot be opened

Possible causes:

- path does not exist;
- path is unreadable;
- selected file is not `.gf`;
- selected directory contains no eligible GF sources;
- RGL source root is ambiguous or unsupported;
- resolved path escapes the approved root;
- module grouping is ambiguous.

The introduction window displays the blocking reason and remediation.

### Main window opens but Compile is unavailable

Possible causes:

- GF executable not configured;
- GF version probe failed;
- required GF path unresolved;
- no compile target selected.

Source browsing and static scan may remain available.

### Checkpoint or Release mode is disabled

Possible causes:

- no validation profile loaded;
- profile declares no checkpoints;
- profile is incompatible with the active language;
- scenarios, golds or release targets are incomplete;
- required capability preflight failed.

### Run button disabled

Possible causes:

- required target not selected;
- requested mode capability unavailable;
- missing GF executable for a compile-backed request;
- active run already in progress;
- unresolved release constraints;
- invalid output root.

The GUI displays the blocking reason.

### Run appears frozen

Inspect:

- current stage;
- elapsed time;
- current subject;
- timeout policy;
- `raw/master.log`.

The GUI thread remains responsive.

### Last language cannot open

The remembered path may no longer exist or may no longer satisfy the supported layout.

Choose another language directory or `.gf` file.

The GUI does not search the filesystem for a replacement automatically.

### Last run cannot open

The stored path may no longer exist.

Use recent runs or select the output root.

The GUI does not claim deletion without cleanup evidence.

### State is corrupt

Malformed state is ignored or quarantined.

The GUI starts at the introduction window with safe defaults.

Source and profile files remain unaffected.

---

## 62. Canonical labels

Introduction labels:

```text
Open Last Language
Choose Language Directory
Choose GF File
Settings
Quit
```

Main section labels:

```text
Language
Capabilities
Environment
Validation Profile
Validation
Resolved Plan
Results
Activity
Run Validation
Cancel
Change Language
Open Run Directory
Open Machine Summary
Open Human Summary
Open AI Ready Packet
Open Master Log
Open Manifest
Test Environment
Settings
Advanced Options
```

Capability labels:

```text
Source Ready
Scan Ready
Compile Ready
Scenario Ready
Release Ready
```

Mode labels:

```text
Quick
Checkpoint
Release
Diagnostic
```

Status labels:

```text
Language ready
Language needs attention
Language could not be resolved
Validation passed
Validation completed with failures
Validation error
Run cancelled
Ready
Running
Cancelling
Checking
Unavailable
```

Labels may be localized.

Internal identifiers remain stable tokens.

---

## 63. Invariants

1. Every interactive launch shows the introduction window before the main runtime.
2. The user supplies one language directory or one `.gf` file.
3. The GUI delegates path resolution and source selection to shared services.
4. One immutable resolved language context exists per active GUI runtime.
5. One language identity exists per ordinary run.
6. The GUI may open in source-ready mode without GF or a validation profile.
7. A catalog, language bundle, scenario registry and gold set are not basic startup prerequisites.
8. Validation profiles are explicit and optional except for profile-dependent modes.
9. Environment preferences remain local.
10. Four canonical validation modes are exposed.
11. Capability status controls mode availability.
12. GUI and CLI share probe, bootstrap and application services.
13. The GUI never bypasses shared validation orchestration.
14. Validation and potentially expensive probing run outside the GUI thread.
15. Cancellation preserves evidence.
16. `FAIL` is never displayed as success.
17. `summary.json` is the machine source for completed runs.
18. Artifact paths come from structured results.
19. Application state is versioned and atomic.
20. Runtime contexts and worker objects are never persisted.
21. Remembered paths are revalidated on every load.
22. Normal validation never updates gold.
23. Release mode enforces required profile stages.
24. Raw diagnostics remain accessible.
25. Color is not the only status signal.
26. Large logs are rendered with bounds.
27. Closing during a run requires explicit cancellation.
28. Language replacement is prohibited during an active run.
29. Replacing a language recreates the runtime.
30. Generic GUI code contains no active-language identifiers or hard-coded RGL language paths.
31. Ambiguity is never resolved by implicit first match.
32. The GUI remains independent from `gf-portfolio`.

---

## 64. Enforcement

> GF Wordbench's GUI begins from one explicit language source path, makes the resolved language and validation plan visible, executes only through shared application services, preserves responsiveness and evidence, displays structured outcomes accurately, and keeps machine-local intent separate from resolved runtime authority.

The GUI may simplify interaction.

It must not simplify away explicit language intent, path containment, ambiguity, capability limits, required evidence, required stages, diagnostic uncertainty, security constraints or release policy.
