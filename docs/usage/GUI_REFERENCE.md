# GF Wordbench — GUI Reference

**Document ID:** `GF-WB-GUI-REFERENCE`  
**Status:** Normative user-interface and interaction reference  
**Applies to:** GF Wordbench desktop GUI, shared validation services, application state, and generated run artifacts  
**Owner:** GF Wordbench maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\usage\GUI_REFERENCE.md`  
**Document version:** `1.0.0`  
**Primary platform:** Windows  
**GUI toolkit:** PySide6 / Qt  
**Execution model:** Desktop client over the shared GF Wordbench bootstrap and validation pipeline

---

## 1. Purpose

This document defines the final GF Wordbench graphical user interface.

It specifies:

- the GUI’s responsibilities and limits;
- application startup and shutdown;
- the main-window structure;
- project and environment selection;
- validation-mode behavior;
- advanced execution options;
- preflight validation;
- run confirmation;
- background execution;
- progress, cancellation, and completion behavior;
- results navigation;
- persisted GUI state;
- error presentation;
- accessibility and keyboard behavior;
- equivalence with the CLI;
- security and path-handling rules;
- migration from the current GF Audit interface;
- required tests and anti-drift checks.

The GUI is a client of the GF Wordbench framework.

It must not become a separate validation engine.

---

## 2. Related normative documents

Read this document with:

```text
docs/00_START_HERE.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/EXECUTION_FLOW.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/usage/CLI_REFERENCE.md
docs/reports/REPORTING_OVERVIEW.md
docs/reports/RAW_LOGS_REFERENCE.md
```

When this document conflicts with a contract lock, the contract lock governs.

---

## 3. Core GUI rule

> The GUI collects user intent, validates local inputs, calls the shared bootstrap and audit APIs, displays structured results, and opens generated artifacts.

The GUI must not:

- compile GF modules directly;
- execute `.gfs` scenarios directly;
- construct a separate GF command model;
- implement independent status aggregation;
- parse reports to discover run results;
- reclassify diagnostics;
- update gold files during a normal run;
- silently rewrite `project.toml`;
- store language-project facts only in GUI state;
- use different defaults or semantics from the CLI.

Equivalent GUI and CLI inputs must produce equivalent `RunConfig` values and equivalent pipeline behavior.

---

## 4. Final product model

GF Wordbench operates on one active language project.

The GUI presents three conceptual layers.

### 4.1 Project layer

Portable language-project facts loaded from:

```text
project/project.toml
```

Examples:

- project name;
- language code;
- source directory;
- entrypoints;
- checkpoints;
- required scenarios;
- optional scenarios;
- release artifact policy.

These values are normally read-only in the run interface.

### 4.2 Environment layer

Machine-local values selected or discovered by the user.

Examples:

- GF executable;
- RGL root;
- output root;
- optional path overrides.

These values may be persisted in local application state.

### 4.3 Run layer

Values specific to the next validation request.

Examples:

- validation mode;
- target file;
- selected checkpoint;
- scenario filter;
- timeout override;
- diagnostic options;
- previous-run comparison.

Run values are validated before execution.

---

## 5. GUI authority boundaries

### 5.1 GUI owns

The GUI owns:

- visual layout;
- widget state;
- file and directory dialogs;
- user confirmation;
- local input feedback;
- background-worker lifecycle;
- progress presentation;
- cancellation request;
- result navigation;
- safe display of errors;
- application-state synchronization.

### 5.2 Bootstrap owns

Bootstrap owns:

- loading framework defaults;
- loading `project.toml`;
- resolving configuration precedence;
- building canonical `RunConfig`;
- creating run paths;
- resolving environment values;
- validating mode-level prerequisites.

### 5.3 Validation pipeline owns

The validation pipeline owns:

- file selection;
- scans;
- compilation;
- diagnostics;
- scenarios;
- gold comparison;
- PGF build;
- release gates;
- previous-run comparison;
- final result;
- reports;
- manifest.

### 5.4 Report readers own

Report and summary loaders own:

- reading `summary.json`;
- rendering completed historical runs;
- verifying supported schema versions;
- exposing artifact links.

The GUI must not parse `summary.md` as the machine source of truth.

---

## 6. Technology baseline

The final desktop GUI uses:

```text
Python 3
PySide6
Qt Widgets
```

Expected implementation zone:

```text
app/main_gui.py
app/gui/
```

Recommended structure:

```text
app/
├── main_gui.py
└── gui/
    ├── __init__.py
    ├── main_window.py
    ├── controllers.py
    ├── workers.py
    ├── dialogs.py
    ├── models.py
    ├── validators.py
    ├── widgets.py
    └── resources/
```

The structure may be simplified while the codebase is small.

The following boundaries must remain:

```text
view widgets
→ GUI controller
→ shared bootstrap
→ audit_core
```

Worker code must not contain business rules that belong to the pipeline.

---

## 7. Application startup

### 7.1 Canonical launcher

Windows convenience launcher:

```text
launch_gui.bat
```

Canonical Python entrypoint:

```text
python -m app.main_gui
```

A packaged executable may be added later.

All launch methods must call the same `main()` entrypoint.

### 7.2 Startup sequence

The final startup sequence is:

```text
create QApplication
→ install top-level exception handler
→ build AppConfig
→ load canonical application state
→ migrate legacy state when applicable
→ load active project summary
→ create MainWindow
→ apply restored window and selection state
→ validate passive environment hints
→ show window
→ enter Qt event loop
```

### 7.3 Startup failure

A fatal startup error should show:

- concise error title;
- actionable message;
- optional technical details;
- log location when available.

The application should exit with a non-zero status when the main window cannot be initialized safely.

### 7.4 No automatic validation

Startup must not automatically launch a full validation run.

Passive project and environment checks may run when they:

- are read-only;
- do not invoke expensive GF work;
- do not create a completed run;
- do not modify project files.

---

## 8. Application shutdown

### 8.1 Normal shutdown

On normal close:

1. synchronize widgets into application state;
2. persist allowed local state atomically;
3. preserve last-run pointers;
4. close child dialogs;
5. release worker resources;
6. exit the Qt event loop.

### 8.2 Shutdown during a run

If a validation run is active, the GUI must not silently exit.

Display a confirmation:

```text
A validation run is still active.
Cancel the run and close GF Wordbench?
```

Available choices:

```text
Continue running
Cancel and close
```

Where supported, an additional choice may minimize the application instead of closing.

### 8.3 Cancellation before close

The GUI must:

- send a cancellation request through the pipeline cancellation interface;
- wait for worker termination without blocking the event loop indefinitely;
- enforce a bounded shutdown timeout;
- preserve partial run evidence;
- persist `is_running = false`;
- never record the run as successful.

---

## 9. Main-window objectives

The main window must let the user:

1. identify the active project;
2. verify local GF environment;
3. select a validation mode;
4. set mode-relevant options;
5. inspect the resolved plan;
6. launch or cancel a run;
7. observe progress;
8. understand the final status;
9. open the run directory and reports;
10. inspect recent or historical results.

The main window should not expose every internal framework option by default.

Advanced settings belong in an expandable section or dedicated dialog.

---

## 10. Recommended main-window layout

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ GF Wordbench — <Project Name>                             <App Version>     │
├────────────────────────────────────────────────────────────────────────────┤
│ Project                                                                  │
│ Name | Language | Project root | Configuration status                    │
├────────────────────────────────────────────────────────────────────────────┤
│ Environment                                                              │
│ GF executable | GF version | RGL root | Output root                       │
├────────────────────────────────────────────────────────────────────────────┤
│ Validation                                                               │
│ Mode | Target/checkpoint | Scenario scope | Main options                  │
├────────────────────────────────────────────────────────────────────────────┤
│ Resolved Plan                                                            │
│ Files | Entrypoints | Scenarios | PGF | Previous-run comparison           │
├────────────────────────────────────────────────────────────────────────────┤
│ [Run Validation] [Cancel] [Open Last Run] [Open Summary] [More Results]   │
├────────────────────────────────────────────────────────────────────────────┤
│ Progress / Current Stage                                                  │
│ Overall status | Stage | Subject | Progress | Elapsed time                │
├────────────────────────────────────────────────────────────────────────────┤
│ Results / Activity                                                        │
│ Summary cards, diagnostics, warnings, and bounded activity log            │
└────────────────────────────────────────────────────────────────────────────┘
```

The exact visual arrangement may evolve.

The information architecture and ownership rules are normative.

---

# 11. Project section

## 11.1 Required fields

Display:

```text
Project name
Project ID
Language code
Project root
project.toml status
Source directory
Entrypoint count
Checkpoint count
Required scenario count
```

### 11.1.1 Read-only project identity

Project identity values are read-only in the validation screen.

Editing project configuration requires a dedicated project-configuration workflow.

### 11.1.2 Project root selector

The user may browse to another GF Wordbench root or active project root when project switching is supported.

Selection must resolve a valid:

```text
project/project.toml
```

or the configured equivalent.

### 11.1.3 Invalid project

An invalid project is shown with:

```text
Project status: Invalid
```

The GUI must list precise configuration errors.

The run action remains disabled until required project errors are resolved.

### 11.1.4 Uninitialized template

A copied project containing unresolved template placeholders must be identified as uninitialized.

The GUI may offer:

```text
Initialize Project
Open Project Documentation
```

It must not guess language identifiers.

---

## 12. Project switching

### 12.1 One active project

Only one project is active in one GUI session.

Switching project:

1. confirms no run is active;
2. loads the new `project.toml`;
3. clears project-derived selections that no longer exist;
4. retains compatible environment preferences;
5. updates the window title;
6. revalidates mode options;
7. does not rewrite the prior project.

### 12.2 State separation

Project-specific recent selections should be keyed by stable project ID if persisted.

Machine-local environment values may remain global.

### 12.3 Stale paths

When the previously used project no longer exists:

- show a non-fatal startup notice;
- keep the project field empty or invalid;
- do not select an unrelated directory automatically.

---

# 13. Environment section

## 13.1 GF executable

Display:

```text
GF executable path
resolution source
detected GF version
compatibility state
```

Resolution source examples:

```text
explicit GUI
application state
environment
PATH discovery
```

### 13.1.1 Browse behavior

File filter on Windows:

```text
GF executable (gf.exe)
Executables (*.exe)
All files (*)
```

On POSIX:

```text
All files (*)
```

### 13.1.2 Validation

Before a required run:

- path exists or command resolves;
- selection is not a directory;
- executable can be launched where platform checks permit;
- the final resolved executable is shown in the run plan.

The GUI must not silently substitute another GF installation after confirmation.

---

## 13.2 RGL root

Display and allow selection of the local RGL root.

Validation should verify:

- path exists;
- path is a directory;
- required project-declared subpaths can be resolved;
- selected RGL is compatible with project policy where known.

A missing RGL root blocks runs that require it.

---

## 13.3 Output root

The output root is machine-local.

Requirements:

- path is explicit after resolution;
- directory exists or can be created;
- write access can be verified;
- output is not inside a protected source directory unless policy allows it;
- current run directory is never overwritten.

The GUI should display available disk-space warnings when practical.

---

## 13.4 Environment status

Recommended states:

```text
Ready
Warning
Invalid
Checking
Unknown
```

These are UI presentation states.

They are not canonical run validation statuses.

The detailed reason must remain accessible.

---

## 14. Environment test action

Provide an optional action:

```text
Test Environment
```

It may:

- resolve GF executable;
- run the bounded version probe;
- validate RGL path;
- validate output-root write access;
- display compatibility.

It must not compile active project files unless explicitly named as a smoke test.

Environment-test results are not a release run.

---

# 15. Validation modes

The GUI exposes exactly the canonical modes:

```text
quick
checkpoint
release
diagnostic
```

Display labels may be title-cased:

```text
Quick
Checkpoint
Release
Diagnostic
```

Persisted and structured values remain lowercase canonical identifiers.

Legacy values:

```text
file
all
```

may be migrated on state load but must not appear as final choices.

---

## 16. Quick mode

### 16.1 Purpose

Fast validation during normal editing.

### 16.2 Required control

```text
Target file or module
```

### 16.3 Selection behavior

The target selector should:

- default to the last valid project-local target;
- list project source files;
- allow browsing;
- convert absolute browser selection to project-relative identity;
- reject files outside the active project unless explicit diagnostic policy permits them.

### 16.4 Typical enabled options

```text
Run static scan
Compile target
Run configured smoke scenario
Compare with previous compatible quick run
Keep OK details
```

### 16.5 Run-plan preview

Show:

```text
1 target file
dependent smoke entrypoint, if applicable
selected smoke scenarios
PGF build: not required
```

---

## 17. Checkpoint mode

### 17.1 Purpose

Validate a declared subsystem or development milestone.

### 17.2 Required control

```text
Checkpoint
```

The checkpoint list comes from `project.toml`.

### 17.3 Checkpoint display

Recommended row fields:

```text
checkpoint ID
display name
module count
scenario count
last status
last run date
```

Historical fields are derived from compatible `summary.json` files.

### 17.4 Checkpoint options

The user may view:

- included modules;
- required entrypoints;
- required scenarios;
- expected gold files;
- gate criteria.

The GUI must not allow arbitrary editing of checkpoint membership in the run screen.

---

## 18. Release mode

### 18.1 Purpose

Evaluate the active project’s declared release criteria.

### 18.2 Required confirmation

Release mode requires a stronger confirmation than other modes.

The dialog must summarize:

```text
Project
GF version
RGL root
Entrypoints
Required checkpoints
Required scenarios
Gold comparisons
PGF targets
Output root
Strict validation state
```

Recommended confirmation text:

```text
Start release validation?
This run will execute every required release stage and may take longer.
Gold files will not be modified.
```

### 18.3 Locked constraints

The GUI must disable or reject:

```text
no_compile = true
skip required scenarios
skip required PGF build
automatic gold update
ignore required artifact failure
```

### 18.4 Release completion

The GUI must not display “Release passed” unless:

```text
overall_status = OK
```

and required manifest verification passed.

---

## 19. Diagnostic mode

### 19.1 Purpose

Collect broad evidence for difficult failures.

### 19.2 Typical controls

```text
Subject scope
Verbose GF output
Keep OK detail reports
Run dependency introspection
Run selected scenarios
Extended timeout
Maximum files
Previous-run comparison
```

### 19.3 Safety

Diagnostic mode may expose advanced options.

It must still enforce:

- finite timeout;
- output containment;
- no shell injection;
- no automatic gold update;
- one resolved GF executable;
- bounded generation.

### 19.4 No-compile option

`Scan only` may be available in diagnostic mode.

The GUI must show:

```text
Compilation-dependent conclusions will be unavailable.
This run cannot satisfy checkpoint or release criteria.
```

---

# 20. Mode-dependent widgets

Widgets must enable or disable according to selected mode.

Recommended matrix:

| Control | Quick | Checkpoint | Release | Diagnostic |
|---|:---:|:---:|:---:|:---:|
| Target file | Required | Hidden | Hidden | Optional |
| Checkpoint selector | Hidden | Required | Read-only all | Optional |
| Scenario filter | Optional | Limited | Read-only required set | Optional |
| Scan only | Optional | Disabled | Disabled | Optional |
| Skip version probe | Optional warning | Restricted | Disabled | Optional |
| Keep OK details | Optional | Optional | Recommended/locked by policy | Optional |
| CPU stats | Optional | Optional | Optional | Optional |
| Max files | Hidden | Hidden | Disabled | Optional |
| PGF build | Hidden | Conditional | Required by project | Optional |
| Previous diff | Optional | Recommended | Required by policy | Optional |

Disabled controls should explain why through accessible tooltip or inline text.

---

# 21. Advanced options

Advanced options should be collapsed by default.

Potential controls:

```text
Timeout override
Keep OK details
Compare previous run
Skip version probe
Scan only
Emit GF CPU stats
Maximum files
Explicit GF path override
Verbose GF output
Strict mode
```

### 21.1 Project-owned options

The GUI must not expose project-owned source rules as ordinary transient fields when they are authoritative in `project.toml`.

Examples that should normally be read-only or hidden:

```text
source directory
source glob
include regex
exclude regex
entrypoints
checkpoint membership
required scenarios
```

### 21.2 Expert override

An expert override may be provided for diagnosis.

When enabled:

- show a warning;
- record the override;
- display it in confirmation;
- store it only when safe;
- never modify project configuration silently;
- prevent release success if the override invalidates release policy.

---

# 22. Resolved-plan panel

Before a run starts, the GUI should show the resolved plan.

Required fields:

```text
Mode
Project ID
GF executable
GF version or probe state
RGL root
Output root
Target/checkpoint
Files selected
Entrypoints selected
Scenarios selected
Gold comparisons
PGF targets
Timeouts
Previous-run comparison
Strict constraints
Overrides
```

### 22.1 Preview source

The plan must be built by shared bootstrap/selection preview services.

The GUI must not duplicate selection algorithms.

### 22.2 Preview freshness

Any relevant widget change invalidates the preview.

The GUI should mark it:

```text
Plan changed — refresh required
```

or rebuild it automatically using a bounded read-only operation.

### 22.3 Preview limitations

If exact file selection requires run-directory creation or expensive discovery, the preview may show estimates.

It must label them as estimates.

---

# 23. Local input validation

The GUI validates obvious inputs before confirmation.

Examples:

- required field empty;
- directory missing;
- file missing;
- invalid integer;
- invalid regex;
- target outside project;
- checkpoint unknown;
- output unwritable;
- contradictory options.

### 23.1 Shared validators

Where the rule affects CLI behavior, use shared validation services.

GUI-only validators may check presentation-specific concerns.

### 23.2 Validation presentation

Show errors:

- adjacent to the field when possible;
- in a concise summary panel;
- with focus moved to the first invalid field;
- without losing entered values.

### 23.3 No false success

Passing GUI validation means only:

```text
the request is ready for bootstrap/pipeline validation
```

It does not prove the language project passes.

---

# 24. Run confirmation

A confirmation is required before launching:

- checkpoint;
- release;
- broad diagnostic runs;
- any run with explicit risky override.

Quick mode may support a preference to skip confirmation after the first successful configuration, but release confirmation cannot be disabled.

### 24.1 Confirmation content

Show only resolved facts.

Do not show raw widget values that bootstrap has replaced or normalized.

### 24.2 Warning grouping

Separate:

```text
Blocking errors
Warnings
Run plan
```

The Run button must remain unavailable when blocking errors exist.

---

# 25. Run execution

## 25.1 Background worker

Validation runs outside the Qt GUI thread.

The final design may use:

```text
QThread + worker QObject
QThreadPool + QRunnable
background controller service
```

Requirements:

- UI remains responsive;
- worker receives immutable resolved configuration;
- progress crosses thread boundaries through signals;
- GUI widgets are updated only on the GUI thread;
- exceptions are captured and returned structurally;
- worker cleanup is deterministic.

### 25.1.1 Current foundation

The current implementation already uses a worker moved to a `QThread` and emits started, finished, and failed signals.

The final implementation extends this with:

```text
progress
stage_changed
subject_changed
warning
cancellation_acknowledged
```

---

## 25.2 Shared pipeline call

The worker calls the canonical orchestration API:

```python
run_audit(run_config)
```

or its deliberate successor.

It must not call:

```text
scanner directly
compiler directly
scenario runner directly
report writers directly
```

### 25.2.1 Result

The worker returns:

```text
RunResult
```

A Python exception is reserved for infrastructure or unhandled framework failure.

Ordinary project validation failure should still return a structured result.

---

# 26. Running-state behavior

While a run is active:

- Run button is disabled;
- project switching is disabled;
- environment path editing is disabled;
- mode and target editing are disabled;
- advanced execution settings are disabled;
- Cancel is enabled;
- artifact-opening actions remain enabled for completed prior runs;
- progress and activity remain visible.

The GUI must not erase the last completed run pointers when a new run begins.

It should distinguish:

```text
Last completed run
Current in-progress run
```

If the current run fails before finalization, the last completed run remains accessible.

---

# 27. Cancellation

## 27.1 Cancel button

A visible Cancel button is required while work is active.

### 27.1.1 First click

The first click:

- requests cancellation;
- changes status to `Cancelling…`;
- disables repeated cancel clicks temporarily;
- does not kill the GUI thread.

### 27.1.2 Pipeline response

The pipeline:

- stops scheduling new work;
- terminates owned external processes according to policy;
- preserves partial evidence;
- builds a non-successful result when possible.

### 27.1.3 Completion display

Display:

```text
Run cancelled
```

not:

```text
Run failed
```

unless an additional framework error occurred.

Cancellation remains an execution state, not a successful validation status.

---

# 28. Progress presentation

## 28.1 Required progress fields

Show:

```text
current stage
current subject
completed subjects
total subjects, when known
elapsed time
warning count
failure count
```

### 28.1.1 Unknown total

Use an indeterminate progress bar when exact total is not known.

### 28.1.2 Stage IDs

The GUI may display friendly stage names.

Technical details may include pipeline IDs such as:

```text
VAL-110
VAL-140
VAL-170
```

### 28.1.3 Progress truth

Progress must come from pipeline events.

The GUI must not infer progress by counting activity-log lines.

---

## 29. Activity panel

The activity panel is a bounded UI view.

It is not `raw/master.log`.

It may show:

- stage transitions;
- current subject;
- concise warnings;
- final counts;
- artifact paths.

### 29.1 Activity retention

The UI may cap visible lines for performance.

The full lifecycle record remains in:

```text
raw/master.log
```

### 29.2 Clear action

`Clear Activity` clears only the UI view.

It must not delete run logs.

### 29.3 Sensitive content

Activity text must not display secrets or full environment dumps.

---

# 30. Result summary

After completion, show a structured result panel.

Required top-level fields:

```text
Overall status
Mode
Project
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

### 30.1 Status rendering

Canonical statuses:

```text
OK
FAIL
ERROR
```

`SKIPPED` is an item or stage status, not the completed overall run status.

### 30.2 Color is supplemental

Status must be conveyed by:

- text;
- icon or shape;
- accessible name.

Color alone is insufficient.

### 30.3 Completion wording

Use:

```text
Validation passed
Validation failed
Validation error
Run cancelled
```

Do not say:

```text
Audit completed successfully
```

when `RunResult.overall_status` is `FAIL` or `ERROR`.

---

# 31. Diagnostic result view

The result view should separate:

```text
Framework/environment errors
Direct failures
Downstream failures
Ambiguous failures
Scenario failures
Gold mismatches
Artifact failures
Non-blocking scan findings
Regressions
```

### 31.1 Direct-first order

Likely direct failures appear before downstream cascades.

### 31.2 Blocker navigation

A downstream row should link to its blocker when known.

### 31.3 Evidence actions

Per result:

```text
Open stdout
Open stderr
Open scan log
Open detail report
Open source location
Open scenario output
Open gold diff
```

Only existing paths are enabled.

### 31.4 No independent classification

The GUI reads classification from structured results.

It does not inspect message text to guess direct/downstream status.

---

# 32. Results navigation actions

Required actions after a completed run:

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
```

### 32.1 Machine summary

“Open Machine Summary” opens:

```text
summary.json
```

### 32.2 Human summary

“Open Human Summary” opens:

```text
summary.md
```

The current generic “Open Summary” label should be replaced because the two summaries serve different audiences.

### 32.3 Missing artifact

When a referenced path is missing:

- show a clear error;
- keep the run result visible;
- offer to open the containing run directory;
- do not reconstruct the missing artifact silently.

---

# 33. Historical runs

A final GUI should provide a recent-runs view.

Recommended columns:

```text
Run ID
Date
Project
Mode
Overall status
GF version
Duration
Direct failures
Scenario failures
Regression count
```

### 33.1 Data source

Load from:

```text
summary.json
```

and optionally verify with:

```text
manifest.json
```

### 33.2 Compatibility

Unsupported schema versions should appear as:

```text
Unsupported historical schema
```

The GUI may offer migration through an explicit tool.

### 33.3 No Markdown parsing

Historical status must not be extracted from `summary.md`.

---

# 34. Compare-runs view

The GUI may provide comparison between compatible runs.

It should display:

```text
Improved
Regressed
New
Removed
Unchanged
```

Data source:

```text
structured diff entries
```

or a shared diff service.

The GUI must not implement separate status-transition rules.

---

# 35. Application state

## 35.1 Canonical state file

```text
.gf_wordbench_state.json
```

Canonical schema:

```text
gf-wordbench.app-state/1.0
```

Legacy file:

```text
.gf_audit_state.json
```

may be imported during migration.

## 35.2 State purpose

Application state stores disposable local preferences.

Deleting it must not damage the project.

## 35.3 Persisted environment fields

Permitted:

```text
project_root
rgl_root
gf_executable
output_root
```

## 35.4 Persisted selection fields

Permitted:

```text
mode
target_file
timeout_sec
max_files
keep_ok_details
diff_previous
skip_version_probe
no_compile
emit_cpu_stats
```

The final schema may add optional GUI-only presentation preferences after schema review.

## 35.5 Persisted last-run fields

Permitted:

```text
run_dir
summary_path
status_message
```

## 35.6 Runtime-only fields

Must not be persisted:

```text
is_running = true
current_run_config
current_run_result
worker object
thread object
open dialog objects
progress subscriptions
cancellation token
```

On startup:

```text
is_running = false
```

---

## 36. Project facts not stored in GUI state

After `project.toml` becomes authoritative, do not persist these as independent GUI facts:

```text
scan directory
scan glob
include regex
exclude regex
GF project path parts
entrypoint list
checkpoint list
required scenarios
optional scenarios
release artifact names
language code
```

Temporary expert overrides may be persisted only under an explicit override structure and must never replace project configuration silently.

---

## 37. State-saving policy

State should be saved:

- after meaningful preference changes, with debounce; or
- on normal application close;
- after a completed run;
- after selecting a project or environment path.

Requirements:

- atomic replacement;
- UTF-8;
- versioned schema;
- no secrets;
- malformed prior state does not crash startup;
- failed save shows a warning without losing the current run.

### 37.1 Path normalization

State paths may be absolute local paths.

Canonical writers should normalize separators to `/`.

Readers accept native separators.

---

# 38. State migration

Legacy flat fields may include:

```text
selected_mode
selected_target_file
selected_project_root
selected_rgl_root
selected_gf_exe
selected_out_root
selected_scan_dir
selected_scan_glob
selected_gf_path
selected_timeout_sec
selected_max_files
selected_include_regex
selected_exclude_regex
selected_keep_ok_details
selected_diff_previous
selected_skip_version_probe
selected_no_compile
selected_emit_cpu_stats
is_running
last_run_dir
last_summary_path
status_message
```

Migration rules:

```text
all → diagnostic
file → quick
```

Local paths move into `environment`.

Run preferences move into `selection`.

Last-run pointers move into `last_run`.

Project-owned fields are discarded once `project.toml` is authoritative.

`is_running` is discarded.

The legacy file remains untouched until the new state is written successfully.

---

# 39. Error dialogs

Error dialogs should separate:

```text
summary
action
technical details
evidence path
```

### 39.1 Configuration error

Example:

```text
Invalid configuration

GF executable does not exist:
C:/tools/gf/gf.exe

Select another executable and try again.
```

### 39.2 Validation failure

Ordinary project `FAIL` should normally be shown in the results view, not as an exception dialog.

A brief completion notice may say:

```text
Validation completed with failures.
```

### 39.3 Framework error

Show:

- concise message;
- run directory if created;
- machine summary if available;
- expandable traceback or technical details;
- Copy Details action.

### 39.4 Fatal GUI error

The top-level exception handler should:

- log the traceback;
- show a critical dialog;
- avoid exposing secrets;
- preserve state where safe.

---

# 40. Warning presentation

Warnings do not block the run unless policy promotes them.

Examples:

- GF version newer than tested range;
- output root low on disk space;
- previous baseline unavailable;
- optional scenario missing;
- expert override active;
- scan-only diagnostic run;
- non-blocking static findings.

Warnings must be visible in:

- confirmation;
- running activity when discovered;
- final result;
- reports when applicable.

---

# 41. File and directory dialogs

### 41.1 Initial directory

Use, in order:

1. current valid field path;
2. active project root;
3. last relevant directory;
4. user home.

### 41.2 Cancel behavior

Cancelling a dialog leaves the current value unchanged.

### 41.3 Target file conversion

When a selected target belongs to the active project:

- display project-relative form where practical;
- retain resolved absolute path internally only through bootstrap;
- persist a stable project-relative target when the state schema supports it.

### 41.4 Symlinks and junctions

Path validation must use the shared containment policy.

The GUI must not decide containment through string-prefix comparison.

---

# 42. Keyboard behavior

Minimum shortcuts:

```text
Ctrl+R        Run validation
Esc           Close non-critical dialog / request cancellation where safe
Ctrl+O        Open project
Ctrl+Shift+O  Open last run directory
Ctrl+L        Focus activity/results log
Ctrl+,        Open settings
F1            Open documentation/help
```

Release validation should not start from an unconfirmed single shortcut.

### 42.1 Default buttons

- confirmation dialog default: Cancel/No for release;
- normal quick confirmation may default to Run;
- error dialog default: Close.

### 42.2 Focus order

Focus follows logical top-to-bottom input order.

Disabled fields are skipped.

---

# 43. Accessibility

The GUI must support:

- keyboard-only navigation;
- screen-reader labels;
- visible focus;
- high-DPI scaling;
- text resizing through platform settings;
- status text independent of color;
- accessible names for icon-only buttons;
- selectable error details;
- sufficient contrast;
- no information conveyed solely by hover.

### 43.1 Dynamic updates

Progress and final status changes should expose accessible announcements without flooding assistive technology.

### 43.2 Tables

Result tables require:

- column headers;
- meaningful row labels;
- keyboard navigation;
- accessible status text;
- sortable behavior that does not change canonical data.

---

# 44. Localization

The first canonical UI language may be English.

The code should keep user-facing strings separable from logic.

Requirements:

- do not compare translated labels as canonical mode identifiers;
- store stable internal values;
- use Qt translation facilities if localization is introduced;
- preserve GF and source diagnostics verbatim;
- do not translate raw GF error messages inside evidence logs.

Documentation language may differ from UI language without changing runtime identifiers.

---

# 45. Window state and appearance

Optional presentation state may include:

```text
window size
window position
splitter positions
selected results tab
column widths
theme preference
```

These fields require addition to the application-state schema before canonical persistence.

### 45.1 Safe restoration

Restored windows must remain visible on current monitors.

Invalid geometry falls back to platform defaults.

### 45.2 Minimum size

The layout should remain usable at a documented minimum window size.

The current foundation uses approximately:

```text
1100 × 760
```

The final GUI may adapt responsively.

---

# 46. Settings dialog

A settings dialog may manage machine-local preferences.

Recommended sections:

```text
Environment
Execution defaults
Reports
Retention
Appearance
Advanced
```

### 46.1 Environment

```text
GF executable
RGL root
Output root
```

### 46.2 Execution defaults

```text
Default mode
Default timeout
Compare previous run
Keep OK details
CPU stats
```

### 46.3 Reports

Only presentation preferences.

Artifact names and required schemas remain framework-owned.

### 46.4 Retention

Links to cleanup policy and retention configuration.

### 46.5 Advanced

```text
Strict compatibility
Diagnostic maximum files
Explicit GF path override
Debug activity logging
```

### 46.6 No project editor by accident

Do not place project entrypoints, scenarios, or language rules in general application settings.

---

# 47. Project configuration workflow

A future project editor may be provided.

It is separate from the run interface.

Requirements:

- validate `gf-wordbench.project/1.0`;
- show exact diff before save;
- write atomically;
- preserve comments only if the chosen TOML writer can do so safely;
- never edit during an active run;
- distinguish project facts from local environment paths;
- update dependent project documentation when contracts change.

Until this workflow exists, the GUI should open `project.toml` in the user’s configured editor rather than provide partial unsafe editing.

---

# 48. Gold update workflow

Gold update is not part of normal validation.

A dedicated GUI workflow may:

1. select one scenario;
2. execute it;
3. normalize output;
4. display expected versus actual diff;
5. require explicit approval;
6. write gold atomically;
7. record the update.

Requirements:

- unavailable during an active normal run;
- disabled for unsupported scenario contracts;
- never triggered automatically after mismatch;
- confirmation clearly states the file to change;
- release validation never updates gold.

---

# 49. GUI and CLI equivalence

For equivalent explicit inputs:

```text
GUI RunConfig == CLI RunConfig
```

after canonical normalization.

Equivalence includes:

- mode;
- project;
- environment;
- target/checkpoint;
- timeouts;
- flags;
- selected scenarios;
- output root;
- strict policy.

### 49.1 Shared builders

Both GUI and CLI must use:

```text
build_app_config
project loader
build_run_config
shared validators
run_audit
```

or their deliberate successors.

### 49.2 Allowed differences

Allowed presentation differences:

- confirmation dialogs;
- visual progress;
- browser dialogs;
- interactive cancellation;
- artifact-opening buttons.

Not allowed:

- different file selection;
- different GF arguments;
- different status mapping;
- different report set;
- different release gates.

---

# 50. Result loading

The GUI may open a completed run without re-executing it.

Loading sequence:

```text
select run directory
→ read summary.json
→ validate schema
→ optionally verify manifest
→ build read-only result view
```

### 50.1 Unsupported schema

Show:

```text
This run uses an unsupported summary schema.
```

Offer:

- open raw directory;
- open JSON as text;
- explicit migration tool when available.

### 50.2 Corrupt manifest

Display:

```text
Artifact integrity warning
```

Do not hide the summary.

Clearly mark unverified artifact links.

---

# 51. Security boundaries

### 51.1 No shell construction

The GUI passes structured values to bootstrap.

It does not construct operating-system command strings.

### 51.2 Untrusted text

Escape or safely render:

- GF diagnostics;
- source excerpts;
- scenario output;
- project names;
- paths;
- report snippets.

### 51.3 External links

Opening local artifacts uses platform-safe local-file APIs.

The GUI should confirm before opening untrusted external URLs found in project content.

### 51.4 Scenario trust

The GUI may warn when a project contains `.gfs` shell-escape features prohibited by policy.

It must not bypass the pipeline’s security validation.

### 51.5 Secrets

Do not persist or display:

- tokens;
- passwords;
- private keys;
- full environment dumps.

---

# 52. Performance

### 52.1 UI thread

Never perform in the GUI thread:

- GF execution;
- broad filesystem scans;
- large hash computation;
- manifest verification across large runs;
- historical-run indexing;
- report generation.

### 52.2 Bounded rendering

Large logs should be:

- streamed in bounded chunks;
- virtualized;
- truncated in the UI with a link to the full file.

The GUI must not load a multi-gigabyte raw log into one text widget.

### 52.3 Recent-run indexing

Index in the background.

Cache only derived metadata.

Invalidate cache when summary or manifest fingerprints change.

---

# 53. Multi-run policy

The final baseline permits one active validation run per GUI instance.

Starting a second run while one is active is prohibited.

A future queue may be added through an architectural change.

Multiple independent GUI instances may be restricted through a project lock or warning to avoid:

- output collisions;
- competing project edits;
- excessive GF resource use.

Run-directory collision protection remains mandatory.

---

# 54. Crash recovery

On startup, the GUI may detect incomplete run directories.

It should display:

```text
Incomplete runs found
```

Actions:

```text
Open
Inspect
Archive
Delete through cleanup workflow
```

It must not mark them successful.

Application state must never restore `is_running=true`.

---

# 55. Current implementation baseline

The current GF Audit GUI already provides:

- PySide6 main window;
- project, RGL, GF executable, and output path fields;
- scan directory and scan glob;
- target-file browser;
- `all` and `file` modes;
- timeout;
- include and exclude regex;
- keep-OK-details option;
- previous-run comparison;
- skip-version-probe option;
- scan-only option;
- CPU-statistics option;
- run confirmation;
- background worker through `QThread`;
- read-only activity widget;
- last-run and summary opening;
- local application state synchronization;
- fatal-error dialog handling.

These capabilities form the migration base.

---

# 56. Required migration to final GUI

## 56.1 Mode migration

Replace visible modes:

```text
all
file
```

with:

```text
diagnostic
quick
checkpoint
release
```

State migration:

```text
all → diagnostic
file → quick
```

## 56.2 Project configuration migration

Remove ordinary editable run-screen fields for:

```text
scan directory
scan glob
include regex
exclude regex
```

Load them from:

```text
project/project.toml
```

Advanced temporary overrides may remain under explicit expert mode.

## 56.3 Target migration

Quick target becomes a project-relative source selector.

Checkpoint mode receives a declared checkpoint selector.

Release mode receives a read-only complete release plan.

## 56.4 Completion semantics

The current UI may describe a returned run as “completed successfully” without first checking final `overall_status`.

Final behavior must map:

```text
OK    → Validation passed
FAIL  → Validation completed with failures
ERROR → Validation could not be completed reliably
```

## 56.5 Result counts

Migrate from legacy:

```text
ok_count
fail_count
```

to canonical:

```text
files_ok
files_fail
files_error
files_skipped
scenarios_ok
scenarios_fail
scenarios_error
scenarios_skipped
```

## 56.6 Last summary action

Replace ambiguous:

```text
Open Summary
```

with separate:

```text
Open Machine Summary
Open Human Summary
```

## 56.7 Running state

Do not clear last completed run pointers when a new run starts.

Track current and previous completed run separately.

## 56.8 Cancellation

Add a supported cancellation action and pipeline cancellation token.

Closing the application during a run must follow the cancellation policy.

## 56.9 Progress

Extend worker signals beyond:

```text
started
finished
failed
```

to structured stage and subject progress.

## 56.10 State migration

Move from `.gf_audit_state.json` and flat fields to:

```text
.gf_wordbench_state.json
gf-wordbench.app-state/1.0
```

---

# 57. Recommended final controller flow

```python
def on_run_requested() -> None:
    ui_request = view.collect_request()

    validation = gui_validator.validate(ui_request)
    if validation.has_errors:
        view.show_validation_errors(validation)
        return

    resolved_plan = bootstrap.preview_run(ui_request)
    view.show_plan(resolved_plan)

    if not view.confirm_run(resolved_plan):
        return

    controller.start_run(resolved_plan.run_config)
```

Worker flow:

```python
def worker_run(run_config: RunConfig) -> None:
    try:
        result = run_audit(
            run_config,
            progress_callback=emit_progress,
            cancellation_token=cancellation_token,
        )
        emit_finished(result)
    except Exception as exc:
        emit_failed(capture_framework_error(exc))
```

Presentation flow:

```python
def on_finished(result: RunResult) -> None:
    state.record_completed_run(result)
    view.set_running(False)
    view.render_result(result)
    state_store.save(state)
```

These signatures are illustrative.

Public APIs remain governed by the interfile contract lock.

---

# 58. Widget-state model

Recommended GUI request model:

```text
project_root
gf_executable
rgl_root
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

The GUI request is not yet a `RunConfig`.

Bootstrap resolves it.

This separation prevents widgets from becoming the canonical configuration model.

---

# 59. Signals and events

Recommended worker/controller events:

```text
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

Event payloads should be immutable structured values.

The activity panel renders them.

Automation and reports do not depend on Qt signals.

---

# 60. Testing strategy

Recommended test directories:

```text
tests/gui/
tests/contracts/
tests/integration/
```

## 60.1 Unit tests

Test:

- state-to-widget loading;
- widget-to-request collection;
- mode-dependent enabling;
- path-browser cancel behavior;
- project-relative target conversion;
- validation message mapping;
- result-status wording;
- artifact action enabling;
- last-run pointer retention;
- state migration;
- close-during-run logic.

## 60.2 Controller tests

Use fake bootstrap and audit services.

Test:

- invalid request does not start worker;
- confirmation rejection does not start worker;
- one worker per run;
- progress routing;
- cancellation routing;
- structured `FAIL` is not treated as exception;
- exception is shown as `ERROR`;
- completed result updates state;
- state-save failure produces warning;
- worker cleanup.

## 60.3 Qt tests

Use Qt-compatible test tooling to verify:

- signals;
- button states;
- focus order;
- keyboard shortcuts;
- modal dialogs;
- thread-safe updates;
- window close behavior;
- accessibility labels where testable.

## 60.4 Integration tests

With a tiny fixture project:

- launch GUI;
- load project;
- run quick validation;
- render `OK`;
- run failing validation;
- render direct failure;
- open run directory;
- open summary files;
- cancel a bounded long-running fake process;
- reopen and restore state.

## 60.5 CLI equivalence tests

For equivalent input:

```text
GUI request → RunConfig
CLI args    → RunConfig
```

must compare equal after canonical normalization.

---

# 61. Required GUI contract tests

Recommended files:

```text
tests/contracts/test_gui_bootstrap_contract.py
tests/contracts/test_gui_audit_contract.py
tests/contracts/test_gui_state_contract.py
tests/contracts/test_gui_cli_equivalence.py
tests/contracts/test_gui_no_stage_bypass.py
tests/contracts/test_gui_result_contract.py
tests/contracts/test_gui_artifact_paths.py
tests/contracts/test_gui_cancellation_contract.py
```

### 61.1 No-stage-bypass test

Verify GUI modules do not import or directly call:

```text
scanner
compiler
scenario_runner
gold comparator
report writers
```

The permitted path is through shared orchestration.

### 61.2 Artifact-path test

Verify the GUI reads paths from structured results.

It must not reconstruct:

```text
summary.json
AI_READY.md
raw/master.log
```

from hard-coded filenames when an owned path field exists.

---

# 62. GUI drift indicators

Probable drift exists when:

- GUI and CLI create different `RunConfig` values;
- GUI directly imports the compiler or scanner;
- visible mode values remain `all` or `file`;
- language-specific source paths remain in GUI defaults;
- `project.toml` fields are duplicated in application state;
- a returned `FAIL` is displayed as successful;
- last-run paths are cleared before the current run completes;
- GUI parses `summary.md` for status;
- GUI reconstructs artifact paths;
- report generation starts from a button independently of the run result;
- release mode allows `no_compile`;
- required scenario controls can be disabled in release mode;
- a normal mismatch offers automatic gold overwrite without explicit workflow;
- cancellation is represented as `OK`;
- worker modifies widgets outside the GUI thread;
- a large log is loaded without bounds;
- state persists `is_running=true`;
- invalid state crashes startup;
- hidden environment values override confirmed visible values;
- project switching occurs during an active run.

Any drift indicator requires contract and test review.

---

# 63. GUI change workflow

A GUI contract change is complete only when:

```text
[ ] User goal identified
[ ] Widget ownership identified
[ ] Bootstrap impact reviewed
[ ] RunConfig impact reviewed
[ ] CLI equivalence reviewed
[ ] Application-state schema reviewed
[ ] Mode matrix reviewed
[ ] Accessibility reviewed
[ ] Threading reviewed
[ ] Cancellation reviewed
[ ] Error presentation reviewed
[ ] Artifact-path ownership reviewed
[ ] Unit tests updated
[ ] Qt tests updated
[ ] Contract tests updated
[ ] Documentation updated
[ ] Migration behavior documented
```

Examples of contract-changing edits:

- adding a validation mode;
- adding a persisted GUI field;
- changing run confirmation;
- changing worker/result signals;
- adding direct stage execution;
- changing cancellation semantics;
- adding project editing;
- adding gold update;
- changing result-status wording;
- changing artifact-opening behavior.

No such change may be implemented in one GUI file only.

---

# 64. Quick user workflow

## 64.1 First launch

1. Start GF Wordbench.
2. Select or confirm the project root.
3. Select the GF executable.
4. Select the RGL root.
5. Select the output root.
6. Test the environment.
7. Choose a validation mode.
8. Review the resolved plan.
9. Run validation.
10. Open the generated summary.

## 64.2 Quick validation

1. Choose `Quick`.
2. Select a project source target.
3. Confirm timeout and optional comparison.
4. Select `Run Validation`.
5. Review direct failures first.
6. Open individual evidence as needed.

## 64.3 Checkpoint validation

1. Choose `Checkpoint`.
2. Select a declared checkpoint.
3. Review included modules and scenarios.
4. Run validation.
5. Inspect checkpoint gates and regressions.

## 64.4 Release validation

1. Choose `Release`.
2. Resolve all environment warnings.
3. Review the complete release plan.
4. Confirm the strict run.
5. Wait for required stages.
6. Verify final status and manifest.
7. Open release artifacts.

## 64.5 Diagnostic validation

1. Choose `Diagnostic`.
2. Select scope.
3. Enable only necessary advanced options.
4. Run validation.
5. Inspect framework errors, then direct failures.
6. Use `AI_READY.md` and raw logs for deeper analysis.

---

# 65. Troubleshooting the GUI

## 65.1 GUI does not start

Check:

```text
Python environment
PySide6 installation
application traceback
launch_gui.bat working directory
```

Run:

```text
python -m app.main_gui
```

from a terminal to expose startup errors.

## 65.2 Run button disabled

Possible reasons:

- invalid project;
- missing GF executable;
- missing RGL root;
- required target/checkpoint not selected;
- active run already in progress;
- release constraints unresolved.

The GUI should display the specific blocking reason.

## 65.3 Run appears frozen

Check:

- current stage;
- elapsed time;
- active subject;
- timeout policy;
- `raw/master.log`.

The GUI thread should remain responsive.

Use Cancel when the operation exceeds expected duration.

## 65.4 Last run cannot open

The stored path may no longer exist.

Use the recent-runs browser or select the output root.

The GUI must not claim the run was deleted by GF Wordbench unless cleanup records prove it.

## 65.5 State is corrupt

GF Wordbench should ignore or quarantine malformed state and start with safe defaults.

Project files remain unaffected.

---

# 66. Canonical interface labels

Recommended final English labels:

```text
Project
Environment
Validation
Resolved Plan
Results
Activity
Run Validation
Cancel
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

Mode labels:

```text
Quick
Checkpoint
Release
Diagnostic
```

Status labels:

```text
Validation passed
Validation completed with failures
Validation error
Run cancelled
Ready
Running
Cancelling
```

Labels may be localized.

Internal identifiers remain canonical English tokens.

---

# 67. Final invariants

The final GUI must satisfy all of the following.

1. One active project per session.
2. Project facts come from `project.toml`.
3. Environment preferences remain local.
4. Four canonical modes are exposed.
5. GUI and CLI share builders and orchestration.
6. GUI never bypasses `run_audit`.
7. Validation runs outside the GUI thread.
8. Cancellation preserves evidence.
9. A returned `FAIL` is not displayed as success.
10. `summary.json` is the machine source for completed runs.
11. Artifact paths come from structured results.
12. State is versioned and atomic.
13. Runtime worker objects are not persisted.
14. Normal validation never updates gold.
15. Release mode enforces required stages.
16. Raw diagnostics remain accessible.
17. Color is not the only status signal.
18. Large logs are rendered with bounds.
19. Closing during a run requires explicit cancellation.
20. No active-language identifiers are hard-coded in generic GUI code.

---

# 68. Final rule

The GUI is a trustworthy control surface only when it remains equivalent to the framework it represents.

> GF Wordbench’s GUI must make the resolved validation plan visible, execute it only through shared orchestration, preserve responsiveness and evidence, display structured outcomes accurately, and keep project facts separate from local interface state.

The GUI may simplify interaction.

It must not simplify away required evidence, required stages, diagnostic uncertainty, or release constraints.
