# GF Wordbench — GUI Reference

**Document ID:** `GF-WB-GUI-REFERENCE`  
**Status:** Normative user-interface and interaction reference  
**Applies to:** GF Wordbench desktop GUI, shared application services, application state and generated run artifacts  
**Owner:** GF Wordbench maintainers  
**Document version:** `2.0.0`  
**Last reviewed:** `2026-07-24`  
**Primary platform:** Windows  
**GUI toolkit:** PySide6 / Qt Widgets  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related locks:** `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`, `docs/PERSISTED_SCHEMA_LOCK.md`

---

## 1. Purpose

This document defines the GF Wordbench desktop graphical interface.

It specifies:

- GUI responsibilities and limits;
- startup and shutdown;
- main-window information architecture;
- active-project and environment selection;
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

It is not a separate validation engine.

---

## 2. Product boundary

One GUI session controls one active GF language project.

The GUI does not provide:

- several simultaneously active projects;
- a multilingual workspace registry;
- cross-workspace aggregation;
- portfolio readiness or comparison;
- `gf-portfolio` storage or services.

The independent product `gf-portfolio` may open or consume public versioned Wordbench artifacts.

GF Wordbench GUI functionality remains complete when `gf-portfolio` is absent.

---

## 3. Related authorities

Read this document with:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/PRODUCT_BOUNDARIES.md
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

Specialized locks and owner documents govern their respective contracts.

---

## 4. Core GUI rule

> The GUI collects user intent, calls shared application services, displays structured progress and results, and opens owned artifacts.

The GUI must not:

- compile GF modules directly;
- execute `.gfs` scenarios directly;
- construct an independent GF command model;
- implement separate file-selection or status aggregation;
- parse Markdown reports to discover run results;
- reclassify diagnostics;
- normalize scenario output;
- update gold files during normal validation;
- silently rewrite `project.toml`;
- store project facts only in GUI state;
- use different defaults or semantics from the CLI;
- depend on `gf-portfolio`.

Equivalent GUI and CLI inputs produce equivalent resolved run configuration and pipeline behavior.

---

## 5. Information model

The GUI presents three distinct layers.

### 5.1 Project

Portable project facts come from:

```text
project/project.toml
```

Examples:

- project name and ID;
- language code;
- project root and source directory;
- entrypoints and checkpoints;
- required and optional scenarios;
- release artifact policy.

Project facts are read-only in the ordinary run screen.

### 5.2 Environment

Machine-local values include:

- GF executable;
- RGL root;
- output root;
- approved local path overrides.

These values may be stored in versioned local application state.

### 5.3 Run request

Run-specific choices include:

- validation mode;
- target file;
- checkpoint;
- scenario scope;
- timeout override;
- diagnostic options;
- previous-run comparison.

Widgets collect a request. Bootstrap resolves the canonical run configuration.

---

## 6. Ownership

### GUI entrypoint and presentation adapters own

- visual layout;
- widget state;
- file and directory dialogs;
- user confirmation;
- local validation feedback;
- background-worker lifecycle;
- progress presentation;
- cancellation requests;
- result rendering;
- artifact-opening actions;
- application-state synchronization.

### Bootstrap and application services own

- framework defaults;
- project loading;
- configuration precedence;
- environment resolution;
- canonical run configuration;
- run-path creation;
- mode prerequisites;
- plan preview.

### Validation application services own

- file selection;
- static scanning;
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
    → application use cases
    → ports
    → adapters
```

The GUI does not import validation-stage implementations directly.

Conceptual placement:

```text
app/
├── entrypoints/
│   └── gui/
├── application/
├── ports/
├── adapters/
└── bootstrap/
```

Internal filenames may vary while dependency direction remains fixed.

Worker code contains transport and lifecycle logic, not validation business rules.

---

## 8. Startup

Canonical launch forms may include:

```text
launch_gui.bat
python -m app.main_gui
```

All launch methods call one GUI entrypoint.

Startup sequence:

```text
create QApplication
→ install top-level exception handling
→ build application configuration
→ load versioned local state
→ import supported legacy state when present
→ load the active project
→ create the main window
→ restore safe presentation and selection state
→ validate passive environment hints
→ show the window
→ enter the Qt event loop
```

Startup does not automatically launch a validation run.

Passive checks are read-only, bounded and do not create a completed run.

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
6. exit the Qt event loop.

### Close during an active run

The GUI displays:

```text
A validation run is active.
Cancel the run and close GF Wordbench?
```

Choices:

```text
Continue running
Cancel and close
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

1. identify the active project;
2. validate the local GF environment;
3. choose a validation mode;
4. set mode-relevant options;
5. inspect the resolved plan;
6. start or cancel a run;
7. observe structured progress;
8. understand the run outcome;
9. open generated artifacts;
10. inspect recent compatible runs.

Advanced controls remain collapsed or placed in a dedicated dialog.

---

## 11. Main-window information architecture

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
│ [Run Validation] [Cancel] [Open Last Run] [Open Reports]                  │
├────────────────────────────────────────────────────────────────────────────┤
│ Progress                                                                 │
│ Status | Stage | Subject | Progress | Elapsed time                        │
├────────────────────────────────────────────────────────────────────────────┤
│ Results / Activity                                                       │
│ Summary, diagnostics, warnings and bounded activity                       │
└────────────────────────────────────────────────────────────────────────────┘
```

Visual arrangement may evolve.

Information ownership and semantics are normative.

---

## 12. Project section

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

Project identity is read-only in the validation screen.

A dedicated project-configuration workflow may edit project facts.

### Project selection

A selected root must resolve the canonical active project configuration:

```text
project/project.toml
```

An invalid project shows precise configuration errors and disables validation.

A template containing unresolved placeholders is shown as uninitialized.

The GUI does not guess project or language identifiers.

### Project switching

Only one project is active in one session.

Switching:

1. requires no active run;
2. loads the new project configuration;
3. clears incompatible project-derived choices;
4. retains compatible machine-local preferences;
5. updates the window;
6. rebuilds the run plan;
7. does not modify the previous project.

A missing previously selected project produces a nonfatal notice. The GUI does not select an unrelated directory automatically.

---

## 13. Environment section

### GF executable

Display:

```text
executable path
resolution source
detected GF version
compatibility result
```

Before a required run:

- the path or command resolves;
- the selection is not a directory;
- launchability is checked where appropriate;
- the resolved executable appears in the plan.

After confirmation, the GUI does not silently substitute another installation.

### RGL root

Validate:

- path exists;
- path is a directory;
- project-required subpaths resolve;
- compatibility policy is satisfied.

A missing required RGL root blocks the run.

### Output root

Requirements:

- resolved path is explicit;
- directory exists or can be created;
- write access is available;
- source directories are protected;
- a run directory is never overwritten.

### Environment presentation state

UI-only states may include:

```text
Ready
Warning
Invalid
Checking
Unknown
```

These are not run validation statuses.

Detailed reasons remain accessible.

### Test Environment

A bounded environment check may:

- resolve and probe GF;
- validate the RGL root;
- validate output access;
- show compatibility.

It does not compile active project files unless an explicit smoke operation is selected.

---

## 14. Validation modes

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

---

## 15. Quick mode

Purpose:

```text
fast validation during editing
```

Required control:

```text
Target file or module
```

The selector:

- lists active-project GF sources;
- supports browsing;
- converts valid selections to project-relative identity;
- rejects paths outside allowed roots.

Typical options:

```text
Run static scan
Compile target
Run configured smoke scenario
Compare with previous compatible run
Keep OK details
```

The plan shows target count, selected scenarios and whether PGF construction is excluded.

---

## 16. Checkpoint mode

Purpose:

```text
validate a declared project subsystem
```

Required control:

```text
Checkpoint
```

The checkpoint list comes from project configuration.

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

## 17. Release mode

Purpose:

```text
evaluate all declared release criteria
```

Confirmation shows:

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
```

The GUI displays release success only when:

```text
overall_status = OK
```

and required artifact integrity checks pass.

---

## 18. Diagnostic mode

Purpose:

```text
collect broad evidence for difficult failures
```

Typical controls:

```text
subject scope
verbose GF output
keep OK details
dependency introspection
selected scenarios
extended timeout
maximum files
previous-run comparison
scan only
```

Diagnostic mode still enforces:

- finite timeouts;
- output containment;
- no shell injection;
- no automatic gold update;
- one resolved GF executable;
- bounded generation.

When `Scan only` is selected, the GUI states:

```text
Compilation-dependent conclusions are unavailable.
This run cannot satisfy checkpoint or release criteria.
```

---

## 19. Mode-dependent controls

| Control | Quick | Checkpoint | Release | Diagnostic |
|---|:---:|:---:|:---:|:---:|
| Target file | Required | Hidden | Hidden | Optional |
| Checkpoint selector | Hidden | Required | Read-only all | Optional |
| Scenario filter | Optional | Limited | Read-only required set | Optional |
| Scan only | Optional | Disabled | Disabled | Optional |
| Skip version probe | Warning | Restricted | Disabled | Optional |
| Keep OK details | Optional | Optional | Policy-controlled | Optional |
| CPU statistics | Optional | Optional | Optional | Optional |
| Maximum files | Hidden | Hidden | Disabled | Optional |
| PGF build | Hidden | Conditional | Project-required | Optional |
| Previous comparison | Optional | Recommended | Policy-controlled | Optional |

Disabled controls explain their policy through accessible text or tooltips.

---

## 20. Advanced options

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
```

Project-owned facts remain read-only:

```text
source directory
source glob
include and exclude rules
entrypoints
checkpoint membership
required scenarios
```

An expert override:

- is clearly marked;
- appears in the resolved plan;
- is recorded in run evidence;
- never rewrites project configuration;
- cannot produce release success when it violates release policy.

---

## 21. Resolved-plan panel

Before execution, show:

```text
Mode
Project ID
GF executable
GF version or probe state
RGL root
Output root
Target or checkpoint
Selected files
Selected entrypoints
Selected scenarios
Gold comparisons
PGF targets
Timeouts
Previous-run comparison
Strict constraints
Overrides
```

The plan comes from shared bootstrap and preview services.

The GUI does not duplicate selection algorithms.

Any relevant widget change invalidates or rebuilds the preview.

Estimates are labeled explicitly when exact selection requires a full operation.

---

## 22. Input validation

The GUI checks obvious local errors before confirmation:

- required field empty;
- file or directory missing;
- invalid integer;
- invalid regex;
- target outside project;
- unknown checkpoint;
- unwritable output;
- contradictory options.

Rules shared with CLI use shared validators.

Errors appear beside fields and in a concise summary, with focus moved to the first invalid field.

Passing GUI validation means only that the request is ready for bootstrap and application validation.

---

## 23. Confirmation

Confirmation is required for:

- checkpoint runs;
- release runs;
- broad diagnostic runs;
- risky expert overrides.

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

## 24. Execution

Validation runs outside the Qt GUI thread.

Supported mechanisms may include:

```text
QThread with worker QObject
QThreadPool with QRunnable
background controller service
```

Requirements:

- the UI remains responsive;
- the worker receives immutable resolved configuration;
- progress crosses thread boundaries through structured events;
- widgets update only on the GUI thread;
- exceptions return as structured framework errors;
- cleanup is deterministic.

The worker calls one application use case.

It does not call scanner, compiler, scenario runner or report writers directly.

Ordinary project failure returns a structured `RunResult`, not an exception.

---

## 25. Running state

While a run is active:

- Run is disabled;
- project switching is disabled;
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

## 26. Cancellation

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

Cancellation is not displayed as success or ordinary project failure unless an additional framework error exists.

---

## 27. Progress

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

Use indeterminate progress when totals are unknown.

Progress comes from structured application events.

The GUI does not infer progress from activity-log line counts.

---

## 28. Activity panel

The activity view is bounded presentation, not `raw/master.log`.

It may show:

- stage transitions;
- current subject;
- concise warnings;
- counts;
- artifact paths.

The GUI may cap lines for performance.

`Clear Activity` clears only the widget.

It does not delete run evidence.

Secrets and full environment dumps are prohibited.

---

## 29. Completion summary

Display:

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

## 30. Diagnostic result view

Separate:

```text
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
```

Only existing owned paths are enabled.

The GUI consumes diagnostic classification from structured results.

---

## 31. Artifact navigation

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

## 32. Completed runs

A recent-runs view may show:

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

## 33. Run comparison

Compatible runs may be compared using structured diff entries.

Display categories:

```text
Regressed
New
Improved
Removed
Unchanged
```

The GUI does not implement independent transition rules.

Cross-workspace portfolio comparison remains outside Wordbench.

---

## 34. Application state

Canonical state file:

```text
.gf_wordbench_state.json
```

Schema:

```text
gf-wordbench.app-state/1.0
```

Application state stores disposable local preferences.

Deleting it does not damage the project.

### Permitted environment fields

```text
project_root
rgl_root
gf_executable
output_root
```

### Permitted selection fields

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

### Permitted completed-run fields

```text
run_dir
summary_path
status_message
```

### Runtime-only fields

Never persist:

```text
is_running = true
current_run_config
current_run_result
worker object
thread object
dialogs
progress subscriptions
cancellation token
```

Startup always begins with no active run.

---

## 35. Project facts excluded from GUI state

Do not store independent copies of:

```text
source directory
source glob
include regex
exclude regex
GF project path parts
entrypoints
checkpoints
required scenarios
optional scenarios
release artifact names
language code
```

These facts belong to `project.toml` and project-owned documents.

Expert overrides remain explicitly separate from project authority.

---

## 36. State persistence

State is saved:

- after meaningful preference changes, with debounce;
- on normal close;
- after a completed run;
- after selecting a project or environment path.

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

---

## 37. Legacy state import

The GUI may import the predecessor state file:

```text
.gf_audit_state.json
```

Supported mapping includes:

```text
all  → diagnostic
file → quick
```

Local paths move to environment state.

Run preferences move to selection state.

Completed-run references move to the completed-run section.

Project-owned fields are discarded once `project.toml` is authoritative.

`is_running` is never imported.

Import is atomic: the predecessor file remains untouched until the canonical state is written and verified.

---

## 38. Error presentation

Error dialogs separate:

```text
summary
recommended action
technical details
evidence path
```

### Configuration error

Example:

```text
Invalid configuration

GF executable does not exist:
C:/tools/gf/gf.exe

Select another executable and try again.
```

### Validation failure

Ordinary project `FAIL` appears in the result view rather than as an exception.

### Framework error

Show:

- concise message;
- run directory when created;
- machine summary when available;
- expandable technical details;
- Copy Details action.

### Fatal GUI error

The top-level handler:

- logs technical details;
- shows a critical dialog;
- avoids secrets;
- preserves state where safe.

---

## 39. Warnings

Warnings are visible in:

- confirmation;
- running activity;
- completion results;
- reports when applicable.

Examples:

- GF version outside the tested range;
- low output disk space;
- unavailable previous baseline;
- optional scenario unavailable;
- expert override active;
- scan-only diagnostic request;
- nonblocking static findings.

Warnings block only when the governing policy makes them blocking.

---

## 40. File and directory dialogs

Initial location precedence:

1. current valid field path;
2. active project root;
3. last relevant directory;
4. user home.

Cancelling a dialog preserves the current value.

Valid selected target paths are displayed project-relatively where practical.

Containment uses shared normalized path policy, not string-prefix comparison.

---

## 41. Keyboard and accessibility

Minimum shortcuts:

```text
Ctrl+R        Run validation
Esc           Close dialog or request cancellation where safe
Ctrl+O        Open project
Ctrl+Shift+O  Open last run directory
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

Result tables provide headers, row labels, keyboard navigation and accessible status text.

---

## 42. Localization

User-facing strings remain separate from logic.

Canonical identifiers are not translated:

```text
quick
checkpoint
release
diagnostic
OK
FAIL
ERROR
SKIPPED
```

Raw GF diagnostics remain verbatim in evidence.

Qt translation facilities may localize presentation labels.

---

## 43. Window and settings state

Optional presentation state may include:

```text
window size and position
splitter positions
selected results tab
column widths
theme preference
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

Project entrypoints, scenarios and language rules do not belong in general application settings.

---

## 44. Project configuration workflow

Project editing is separate from ordinary run controls.

A project editor must:

- validate the canonical project schema;
- show an exact diff before saving;
- write atomically;
- avoid edits during active runs;
- separate project facts from local environment values;
- preserve or explicitly manage TOML comments;
- coordinate dependent project contracts.

When no safe editor is provided, the GUI opens `project.toml` in the configured external editor.

---

## 45. Gold update workflow

Gold updates are separate from normal validation.

A dedicated workflow:

1. selects one scenario;
2. executes it;
3. normalizes output;
4. displays expected and actual diff;
5. requires explicit approval;
6. writes the gold file atomically;
7. records the update.

It is unavailable during normal active runs, never triggered automatically and prohibited during release validation.

---

## 46. GUI and CLI equivalence

For equivalent explicit inputs:

```text
GUI resolved RunConfig == CLI resolved RunConfig
```

after canonical normalization.

Equivalence includes:

- mode;
- project identity;
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

## 47. Loading an existing run

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

---

## 48. Security

The GUI:

- passes structured values to application services;
- does not construct host command strings;
- safely renders diagnostics, source excerpts, scenario output, project names and paths;
- uses platform-safe local-file opening APIs;
- confirms untrusted external URLs;
- does not bypass scenario security policy;
- does not persist or display tokens, passwords, private keys or full environment dumps;
- validates path containment through shared policy.

---

## 49. Performance

Never perform on the GUI thread:

- GF execution;
- broad filesystem scanning;
- large hash computation;
- large manifest verification;
- historical-run indexing;
- report generation.

Large logs are streamed, virtualized or bounded with a link to the complete file.

Recent-run indexing occurs in the background.

Derived caches are invalidated when summary or manifest fingerprints change.

---

## 50. Active-run policy

One GUI instance permits one active validation run.

Starting a second run while one is active is prohibited.

Independent instances must still respect run-directory collision protection and project-write safety.

A queued multi-run engine requires a separate architectural contract.

---

## 51. Crash recovery

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

Application state never restores an active-running flag.

---

## 52. Controller flow

Conceptual controller flow:

```python
def on_run_requested() -> None:
    ui_request = view.collect_request()

    validation = gui_validator.validate(ui_request)
    if validation.has_errors:
        view.show_validation_errors(validation)
        return

    plan = bootstrap.preview_run(ui_request)
    view.show_plan(plan)

    if not view.confirm_run(plan):
        return

    controller.start_run(plan.run_config)
```

Worker flow:

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

Presentation flow:

```python
def on_finished(result: RunResult) -> None:
    state.record_completed_run(result)
    view.set_running(False)
    view.render_result(result)
    state_store.save(state)
```

Signatures are illustrative. Public contracts remain owned by the interfile lock.

---

## 53. GUI request model

The widget request may contain:

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

This request is not a `RunConfig`.

Bootstrap resolves and validates it.

---

## 54. Events

Structured events may include:

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

Payloads are immutable structured values.

Qt signals transport events to the presentation layer.

Reports and automation do not depend on Qt.

---

## 55. Testing

### Unit tests

Cover:

- state-to-widget loading;
- widget-to-request collection;
- mode-dependent controls;
- dialog cancellation;
- project-relative target conversion;
- validation-message mapping;
- result wording;
- artifact-action enabling;
- last-run retention;
- legacy state import;
- close-during-run logic.

### Controller tests

Use fake bootstrap and application services.

Cover:

- invalid request does not start work;
- rejected confirmation does not start work;
- one worker per run;
- progress routing;
- cancellation routing;
- structured `FAIL` is not an exception;
- infrastructure exception maps to `ERROR`;
- completed result updates state;
- state-save failure produces a warning;
- worker cleanup.

### Qt tests

Cover:

- signals;
- button states;
- focus order;
- shortcuts;
- modal dialogs;
- thread-safe updates;
- close behavior;
- accessibility labels where testable.

### Integration tests

With a small fixture project:

- launch GUI;
- load project;
- run successful quick validation;
- render failure correctly;
- open run artifacts;
- cancel a bounded long operation;
- restart and restore safe state.

### CLI equivalence tests

Equivalent GUI and CLI input must resolve to equal canonical run configuration.

### Boundary tests

Verify GUI modules do not import or directly call:

```text
scanner
compiler
scenario runner
gold comparator
report writers
```

Verify artifact paths come from structured results rather than hard-coded reconstruction.

---

## 56. Drift indicators

GUI drift exists when:

- GUI and CLI resolve different run configuration;
- GUI imports validation-stage implementations;
- visible modes use legacy identifiers;
- language-specific paths appear in framework GUI defaults;
- project facts are duplicated in local state;
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
- state persists an active-running flag;
- malformed state crashes startup;
- hidden values override confirmed visible values;
- project switching occurs during a run;
- GUI behavior depends on `gf-portfolio`.

Any drift indicator requires coordinated contract and test correction.

---

## 57. Change checklist

```text
[ ] User goal identified
[ ] Widget and application owner identified
[ ] Bootstrap impact reviewed
[ ] RunConfig impact reviewed
[ ] CLI equivalence reviewed
[ ] Application-state schema reviewed
[ ] Mode matrix reviewed
[ ] Accessibility reviewed
[ ] Threading and cancellation reviewed
[ ] Error presentation reviewed
[ ] Artifact ownership reviewed
[ ] Security reviewed
[ ] Unit and Qt tests updated
[ ] Contract and integration tests updated
[ ] Owner documentation and locks updated
[ ] Compatibility behavior defined when public contracts change
[ ] Wordbench/Portfolio boundary preserved
```

A public GUI contract change is not implemented only in a widget file.

---

## 58. User workflows

### First launch

1. Start GF Wordbench.
2. Select or confirm the active project.
3. select the GF executable.
4. select the RGL root.
5. select the output root.
6. test the environment.
7. choose a validation mode.
8. review the resolved plan.
9. run validation.
10. open the generated reports.

### Quick validation

1. Choose `Quick`.
2. Select a project source target.
3. Confirm relevant options.
4. Run validation.
5. Review direct failures first.
6. Open evidence as needed.

### Checkpoint validation

1. Choose `Checkpoint`.
2. Select a declared checkpoint.
3. Review modules and scenarios.
4. Run validation.
5. Inspect gates and regressions.

### Release validation

1. Choose `Release`.
2. Resolve blocking environment issues.
3. Review the release plan.
4. Confirm the run.
5. Observe required stages.
6. verify outcome and manifest.
7. open release artifacts.

### Diagnostic validation

1. Choose `Diagnostic`.
2. Select scope.
3. Enable only necessary advanced options.
4. Run validation.
5. Inspect framework errors, then direct failures.
6. Use `AI_READY.md` and raw logs for deeper analysis.

---

## 59. Troubleshooting

### GUI does not start

Check:

```text
Python environment
PySide6 installation
application traceback
launcher working directory
```

Run the Python module entrypoint from a terminal to expose startup errors.

### Run button disabled

Possible causes:

- invalid project;
- missing GF executable;
- missing RGL;
- required target or checkpoint not selected;
- active run already in progress;
- unresolved release constraints.

The GUI displays the blocking reason.

### Run appears frozen

Inspect:

- current stage;
- elapsed time;
- current subject;
- timeout policy;
- `raw/master.log`.

The GUI thread remains responsive.

### Last run cannot open

The stored path may no longer exist.

Use recent runs or select the output root.

The GUI does not claim deletion without cleanup evidence.

### State is corrupt

Malformed state is ignored or quarantined.

The GUI starts with safe defaults.

Project files remain unaffected.

---

## 60. Canonical labels

Section labels:

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

Internal identifiers remain stable tokens.

---

## 61. Invariants

1. One active project exists per GUI session.
2. Project facts come from `project.toml`.
3. Environment preferences remain local.
4. Four canonical validation modes are exposed.
5. GUI and CLI share bootstrap and application services.
6. The GUI never bypasses shared validation orchestration.
7. Validation runs outside the GUI thread.
8. Cancellation preserves evidence.
9. `FAIL` is never displayed as success.
10. `summary.json` is the machine source for completed runs.
11. Artifact paths come from structured results.
12. Application state is versioned and atomic.
13. Runtime worker objects are never persisted.
14. Normal validation never updates gold.
15. Release mode enforces required stages.
16. Raw diagnostics remain accessible.
17. Color is not the only status signal.
18. Large logs are rendered with bounds.
19. Closing during a run requires explicit cancellation.
20. Generic GUI code contains no active-language identifiers.
21. The GUI remains independent from `gf-portfolio`.

---

## 62. Enforcement

> GF Wordbench's GUI makes the resolved validation plan visible, executes it only through shared application services, preserves responsiveness and evidence, displays structured outcomes accurately, and keeps project facts separate from local interface state.

The GUI may simplify interaction.

It must not simplify away required evidence, required stages, diagnostic uncertainty, security constraints or release policy.
