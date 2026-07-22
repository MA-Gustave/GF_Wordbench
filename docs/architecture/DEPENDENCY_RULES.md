# GF Wordbench — Dependency Rules

**Document ID:** `GF-WB-ARCH-DEPENDENCY-RULES`  
**Status:** Normative  
**Applies to:** GF Wordbench framework, framework tests, project integration boundaries, and generated-artifact consumers  
**Owner:** GF Wordbench maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\architecture\DEPENDENCY_RULES.md`  
**Rules version:** `1.0.0`  
**Last reviewed:** `2026-07-21`

---

## 1. Purpose

This document defines the allowed dependency directions in GF Wordbench.

It prevents architectural drift caused by:

- circular imports;
- user interfaces bypassing orchestration;
- reports launching validation;
- multiple components resolving the same configuration differently;
- low-level utilities importing application models;
- framework code depending on one active language;
- project files controlling framework internals;
- duplicated artifact ownership;
- hidden process execution;
- readers rewriting data owned by writers;
- tests depending on a developer’s local environment.

A module may be locally correct and still damage the system when it imports, invokes, mutates, or interprets another layer through the wrong boundary.

The core rule is:

> A higher-level component may coordinate lower-level capabilities, but a lower-level component must not depend on the higher-level policy that coordinates it.

---

## 2. Relationship to other normative documents

This document owns architectural dependency direction.

It complements, but does not replace:

| Topic | Authoritative document |
|---|---|
| Exact provider-consumer contracts | `docs/INTERFILE_CONTRACT_LOCK.md` |
| External executables and process behavior | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted formats and migrations | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Product boundary | `docs/SCOPE_AND_NON_GOALS.md` |
| Component responsibilities | `docs/architecture/COMPONENT_MAP.md` |
| Runtime order | `docs/architecture/EXECUTION_FLOW.md` |
| Shared data structures | `docs/architecture/DATA_MODEL.md` |
| Artifact ownership | `docs/architecture/ARTIFACT_MODEL.md` |
| Active-language GF dependencies | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Active-language module graph | `project/docs/MODULE_DEPENDENCY_MAP.md` |

This document defines whether one layer may depend on another.

The interfile contract lock defines the exact public symbols and behavior at permitted boundaries.

---

## 3. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **DEPENDENCY**: an import, function call, class reference, schema assumption, file read, file write, process invocation, shared constant, or runtime callback.
- **COMPILE-TIME DEPENDENCY**: a Python import or symbol reference required to load a module.
- **RUNTIME DEPENDENCY**: a call or data flow that occurs after modules are loaded.
- **POLICY LAYER**: a layer that decides what operation should occur.
- **MECHANISM LAYER**: a layer that performs a bounded operation without deciding global workflow.
- **OWNER**: the component allowed to create or mutate an artifact or state domain.
- **OBSERVER**: a component allowed to read, summarize, compare, or display an owned artifact.
- **UPWARD DEPENDENCY**: a lower-level layer importing or controlling a higher-level layer.
- **DOWNWARD DEPENDENCY**: a higher-level layer invoking a lower-level capability.
- **LATERAL DEPENDENCY**: a dependency between components at the same architectural level.
- **CYCLE**: direct or indirect dependency path that returns to its origin.
- **PRIVATE SYMBOL**: a symbol not declared as public by its provider.
- **ACTIVE PROJECT**: the single language project represented by `project/`.
- **FRAMEWORK**: reusable language-neutral code under `app/`, `tests/`, `docs/`, and `templates/`.

---

# 4. Dependency dimensions

Dependency control applies to more than Python imports.

## 4.1 Import dependencies

Examples:

```python
from app.models import RunResult
from app.audit.compiler import compile_file
```

Import direction must respect the layer model.

## 4.2 Call dependencies

A module may import an abstract type safely but still violate architecture by invoking the wrong operation.

Example of prohibited behavior:

```text
report writer → compiler execution
```

## 4.3 Data dependencies

A consumer depends on a provider when it assumes:

- a field exists;
- a status has a particular meaning;
- an array is ordered;
- a path is relative to a particular root;
- a result is mutable;
- an exception indicates a specific failure.

Shared data assumptions must be defined by models or schemas.

## 4.4 Artifact dependencies

A reader depends on an artifact owner when it:

- reads a report;
- reads a raw log;
- compares a gold file;
- loads application state;
- verifies a manifest;
- discovers a generated `.pgf`.

Readers must use the documented artifact path or model.

They must not reconstruct owned filenames independently.

## 4.5 Configuration dependencies

A component depends on configuration when behavior changes based on:

- project identity;
- source paths;
- entrypoints;
- scenarios;
- timeouts;
- output roots;
- external executable paths;
- validation mode.

Configuration must flow through the canonical configuration pipeline.

## 4.6 External-process dependencies

A component depends on an external tool when it constructs or executes a command, interprets its result, or consumes its generated artifact.

Only designated execution stages may own such dependencies.

## 4.7 Documentation dependencies

A document becomes a dependency when code, configuration, release policy, or another document treats it as authoritative.

Normative rules must have one documentation owner.

---

# 5. Canonical framework layers

The final GF Wordbench framework uses the following logical layers.

The exact number of Python files may evolve, but every file must belong to one primary layer.

```text
L0  shared primitives and pure utilities
L1  shared models, schemas, and bounded configuration readers
L2  execution mechanisms and validation stages
L3  orchestration and result assembly
L4  reports and application services
L5  user interfaces and launchers
```

The active project is a separate policy and content domain.

```text
P0  project configuration and documentation
P1  GF source modules
P2  validation inputs, scenarios, and gold files
```

External tools are outside the Python layer graph.

```text
E0  GF executable and approved external tools
```

Generated run artifacts form an output domain.

```text
A0  raw evidence, normalized evidence, summaries, manifests, GF artifacts
```

---

# 6. Layer L0 — Shared primitives and pure utilities

Typical owners:

```text
app/utils/io_utils.py
app/utils/path_utils.py
app/utils/logging_utils.py
app/utils/process_utils.py
small pure parsing or normalization helpers
```

## 6.1 Responsibilities

L0 may provide:

- filesystem-safe read and write primitives;
- path normalization;
- safe directory creation;
- atomic file replacement;
- hash calculation;
- bounded text handling;
- command rendering;
- subprocess execution primitives;
- time measurement;
- logging helpers;
- pure text normalization;
- generic value validation.

## 6.2 Allowed dependencies

L0 may depend on:

```text
Python standard library
explicitly approved low-level third-party libraries
other L0 modules when acyclic
```

## 6.3 Prohibited dependencies

L0 must not depend on:

```text
app.bootstrap
app.state
app.gui
app.main_cli
app.main_gui
app.audit.audit_core
app.audit.compiler
app.audit.scanner
app.audit.scenario_runner
app.reports
active project modules
active project identity
RunResult policy
release policy
```

## 6.4 Process utility rule

`process_utils` owns process mechanism, not GF policy.

It may know:

- executable;
- ordered arguments;
- working directory;
- environment overrides;
- stdin;
- timeout;
- encoding;
- cancellation request;
- output limits.

It must not know:

- which GF module should compile;
- which scenario is required;
- whether a release passes;
- how a GF diagnostic should be classified;
- where project entrypoints come from;
- which report should be written.

## 6.5 Utility purity rule

A utility must not become a hidden service locator.

A utility function must not silently read:

- global GUI state;
- application state;
- `project.toml`;
- environment variables unrelated to its explicit parameters;
- current working directory as policy;
- previous run folders.

Required context must be passed explicitly.

---

# 7. Layer L1 — Shared models, schemas, and configuration readers

Typical owners:

```text
app/models.py
app/config.py
app/project_config.py
designated schema and migration modules
```

## 7.1 Responsibilities

L1 may define:

- immutable or controlled shared data models;
- enums and status vocabularies;
- application defaults;
- project configuration parsing;
- persisted-schema validation;
- migration of supported legacy data;
- stable serialization helpers;
- configuration validation;
- path-resolution inputs and outputs.

## 7.2 Models are passive

Shared models must remain passive data contracts.

They may contain:

- fields;
- validation of their own field invariants;
- small pure derived properties;
- deterministic serialization helpers;
- safe constructors.

They must not:

- launch processes;
- scan source files;
- compile GF;
- load GUI widgets;
- generate reports;
- discover external tools;
- select project files;
- mutate application state;
- read arbitrary files during property access.

## 7.3 Allowed dependencies

L1 may depend on:

```text
Python standard library
L0 utilities
other L1 primitives when acyclic
```

A schema module may depend on the model it serializes.

A model should not depend on the schema writer that serializes it.

## 7.4 Prohibited dependencies

L1 must not depend on:

```text
app.gui
app.main_cli
app.main_gui
app.audit.audit_core
app.audit compiler/scanner/scenario stages
app.reports
release orchestration
generated run directories as configuration truth
```

## 7.5 Configuration ownership

Configuration domains must have distinct owners.

```text
app/config.py
    framework identity and language-neutral defaults

project/project.toml
    active-language project identity and validation policy

app state
    disposable local UI and environment preferences

resolved RunConfig
    immutable or controlled configuration for one execution
```

A configuration value must not have competing authoritative definitions.

## 7.6 Project loader rule

The project loader may read and validate `project/project.toml`.

It must not:

- inspect GUI widgets;
- read previous summaries to infer project identity;
- alter project configuration during normal loading;
- import active-language GF files as Python;
- reinterpret unknown required fields silently.

## 7.7 Schema dependency rule

Persisted-schema readers and writers must depend on shared schema definitions.

Reports, state, and migration components must not each invent independent field names.

---

# 8. Layer L2 — Execution mechanisms and validation stages

Typical owners:

```text
app/audit/file_selector.py
app/audit/scanner.py
app/audit/compiler.py
app/audit/scenario_runner.py
app/audit/fingerprint.py
bounded GF command builders
gold comparison and output normalization components
```

## 8.1 Responsibilities

L2 performs bounded operations.

Each stage should have:

- explicit input;
- explicit output;
- documented side effects;
- finite execution;
- structured failure representation;
- no knowledge of global UI behavior;
- no control over full-run policy.

## 8.2 Allowed dependencies

L2 may depend on:

```text
L0 utilities
L1 models
L1 resolved configuration
other narrowly scoped L2 helpers when acyclic
approved external tools through process_utils
active project files through explicit paths and contracts
```

## 8.3 Prohibited dependencies

L2 must not depend on:

```text
app.gui
app.main_cli
app.main_gui
app.reports
full audit orchestration
release decision rendering
application state mutation
human Markdown reports
```

## 8.4 File selector rule

The file selector may depend on:

- resolved project configuration;
- path utilities;
- selection models;
- filesystem metadata.

It must not depend on:

- compiler results;
- report output;
- GUI selections directly;
- previous Markdown reports;
- language-specific hardcoded paths.

## 8.5 Scanner rule

The scanner may depend on:

- source paths;
- scan configuration;
- pure text helpers;
- scan result models;
- scan log ownership.

The scanner must not depend on:

```text
compiler
scenario runner
reports
classifier policy
GUI
```

Scan and compile truth remain separate.

## 8.6 Compiler rule

The compiler may depend on:

- resolved GF executable;
- resolved GF path;
- process runner;
- compile request models;
- raw evidence paths;
- diagnostic parsing helpers.

The compiler must not depend on:

```text
reports
GUI
previous-run comparison
release decision
scanner internals
```

The compiler may receive scan metadata only when the orchestration contract explicitly supplies it; it must not invoke the scanner.

## 8.7 Scenario runner rule

The scenario runner may depend on:

- scenario registry;
- `.gfs` paths;
- process runner;
- result models;
- output normalization;
- assertion evaluation;
- gold comparator;
- artifact paths.

It must not depend on:

```text
reports
GUI
release presentation
gold update during normal validation
compiler private helpers
```

Compiler and scenario runner may share a documented GF command builder or process mechanism.

Neither should import the other merely to reuse private code.

## 8.8 Fingerprint rule

Fingerprinting may depend on:

- filesystem reads;
- hash utilities;
- fingerprint models.

It must not depend on:

- classifier;
- report generation;
- GUI;
- compilation semantics.

## 8.9 Gold comparator rule

Gold comparison may read:

- normalized current output;
- registered expected gold;
- normalization version;
- comparison policy.

It must not:

- execute GF;
- normalize through a second inconsistent implementation;
- update gold during ordinary validation;
- determine full release status.

## 8.10 Stage isolation

A validation stage must not invoke another stage unless that composition is its explicit responsibility.

Default composition belongs to orchestration.

Examples:

```text
scanner → compiler                 prohibited
compiler → scanner                 prohibited
report → compiler                  prohibited
scenario runner → release gate     prohibited
```

A dedicated composite stage may be introduced only when its combined contract is stable and documented.

---

# 9. Layer L3 — Orchestration and result assembly

Typical owners:

```text
app/audit/audit_core.py
app/audit/result_model.py
app/audit/classifier.py
app/audit/diff.py
release-gate evaluation
run-path construction
```

## 9.1 Responsibilities

L3 coordinates lower-level stages.

It may:

- establish run identity;
- build run paths;
- execute stages in order;
- aggregate results;
- invoke classification;
- compare previous runs;
- evaluate release gates;
- finalize run status;
- request reports;
- handle cancellation;
- preserve partial evidence after failures.

## 9.2 Allowed dependencies

L3 may depend on:

```text
L0 utilities
L1 models and resolved configuration
L2 stages
L3 peer components through explicit acyclic flow
L4 report facade for final output requests
```

## 9.3 Prohibited dependencies

L3 must not depend on:

```text
GUI widgets
CLI parser objects
launcher scripts
human interaction dialogs
active-language hardcoded names
report prose as data
```

## 9.4 Audit-core rule

`audit_core` is the principal validation coordinator.

It may call:

```text
run-path builder
file selector
scanner
compiler
fingerprint
scenario runner
result builder
classifier
diff engine
release-gate evaluator
report facade
```

It must not:

- parse CLI arguments;
- read widget state;
- display dialogs;
- implement scanner internals;
- construct subprocess calls directly when a process layer exists;
- serialize schemas independently;
- rewrite gold files;
- infer project identity from generated output.

## 9.5 Result-builder rule

The result builder may combine stage results into shared models.

It must not:

- execute stages;
- write reports;
- read GUI state;
- hide missing required evidence;
- attach undocumented dynamic fields.

## 9.6 Classifier rule

The classifier may depend on:

- structured file results;
- structured scenario results;
- diagnostic data;
- dependency evidence;
- shared status vocabularies.

It must not:

```text
launch GF
read GUI state
mutate raw evidence
rewrite compile results
generate reports
```

Classification is derived interpretation.

It does not replace raw stage status.

## 9.7 Diff rule

The diff engine may depend on:

- current structured results;
- previous compatible structured summary;
- schema readers;
- normalized subject identity.

It must not depend on:

- Markdown reports;
- GUI;
- compiler;
- scanner;
- external process execution.

## 9.8 Release-gate rule

Release-gate evaluation may depend on:

- resolved project release policy;
- final structured run result;
- required scenario results;
- required artifact verification;
- known-issue status where represented structurally.

It must not:

- alter a failing stage result;
- skip missing evidence;
- invoke a replacement stage silently;
- update gold;
- read human prose as the only source of a machine decision.

---

# 10. Layer L4 — Reports and application services

Typical owners:

```text
app/reports/report_json.py
app/reports/report_md.py
app/reports/report_ai_ready.py
app/reports/report_logs.py
app/reports/report_details.py
designated manifest writer
state service
report facade
```

## 10.1 Responsibilities

L4 may:

- serialize completed structured results;
- write human summaries;
- write AI-ready reports;
- aggregate existing logs;
- write detail reports;
- write and verify manifests;
- save disposable application state;
- expose report paths to interfaces.

## 10.2 Allowed dependencies

Reports may depend on:

```text
L0 I/O utilities
L1 models
L1 schemas
artifact path models
bounded formatting helpers
```

State services may depend on:

```text
L0 I/O utilities
L1 state schema
safe application-state models
```

## 10.3 Prohibited dependencies

Reports must not depend on:

```text
compiler
scanner
scenario runner
process runner
audit_core execution entrypoint
GUI widgets
CLI parser
active-language implementation modules
```

## 10.4 Observation-only rule

A report observes completed or partial structured results.

It must not:

- rerun GF;
- rerun a scan;
- recalculate project selection;
- fill missing evidence by external execution;
- modify stage results;
- change release status;
- update gold;
- rewrite raw evidence.

## 10.5 Report-to-report rule

Reports should derive from the same structured source.

Default rule:

```text
RunResult → summary.json
RunResult → summary.md
RunResult → AI_READY.md
RunResult → details
RunResult → aggregate logs
```

Prohibited default:

```text
summary.md → AI_READY.md
AI_READY.md → summary.json
top_errors.txt → run status
```

A report may link to another report.

It must not parse another human report to recover authoritative data.

## 10.6 JSON authority rule

`summary.json` is the canonical machine-readable run summary.

Other reports may depend on the same model or schema, but they must not create conflicting status vocabularies.

## 10.7 State separation rule

Application state is not project configuration and not run truth.

The state service may store:

- selected local paths;
- UI preferences;
- last-run pointers;
- last selected mode.

It must not become authoritative for:

- active language identity;
- required entrypoints;
- required scenarios;
- release policy;
- current run result;
- `is_running = true` across restarts.

---

# 11. Layer L5 — User interfaces and launchers

Typical owners:

```text
app/main_cli.py
app/main_gui.py
app/gui/
launch_cli.bat
launch_gui.bat
```

## 11.1 Responsibilities

L5 may:

- collect user input;
- parse command-line arguments;
- validate surface-level input;
- call bootstrap;
- request an audit;
- display progress;
- display structured outcomes;
- expose report and artifact paths;
- map final results to process exit codes.

## 11.2 Allowed dependencies

L5 may depend on:

```text
bootstrap
application service facade
shared public models needed for display
state service
audit_core public entrypoint
report path results
```

## 11.3 Prohibited dependencies

L5 must not depend directly on:

```text
compiler internals
scanner internals
scenario-runner internals
process_utils
diagnostic-parser private helpers
report writer private helpers
project TOML parser internals
```

## 11.4 CLI/GUI parity rule

Equivalent inputs must resolve to equivalent run configuration.

CLI and GUI may differ in presentation.

They must not differ in:

- GF executable resolution;
- project loading;
- GF path construction;
- default timeout semantics;
- required validation stages;
- release-gate policy;
- result classification;
- persisted schema.

## 11.5 GUI boundary rule

GUI widgets must not launch GF directly.

The path must be:

```text
GUI widget
→ GUI controller
→ bootstrap/application service
→ audit_core
→ execution stage
→ process_utils
→ GF
```

## 11.6 CLI boundary rule

The CLI parser must not embed validation implementation.

The path must be:

```text
CLI arguments
→ bootstrap/application service
→ resolved RunConfig
→ audit_core
```

## 11.7 Launcher rule

Batch or shell launchers may:

- locate the Python entrypoint;
- activate a documented environment;
- forward arguments;
- set explicitly documented launcher-only values.

They must not:

- define hidden validation defaults;
- construct GF commands;
- alter release policy;
- become the only supported execution route;
- cause CLI and GUI semantics to diverge.

---

# 12. Bootstrap boundary

`bootstrap` is the composition boundary between interfaces and application logic.

## 12.1 Bootstrap may

- load language-neutral application defaults;
- load project configuration;
- merge documented CLI or GUI overrides;
- resolve local environment paths;
- validate configuration;
- construct immutable or controlled runtime configuration;
- construct application services;
- expose public entrypoints to CLI and GUI.

## 12.2 Bootstrap must not

- run the full audit while being imported;
- display GUI dialogs;
- parse raw CLI arguments;
- implement compile or scan algorithms;
- write reports;
- redefine project-owned language policy;
- hide missing required configuration through implicit fallback.

## 12.3 Import-side-effect rule

Importing `bootstrap` must not:

- launch GF;
- create a run directory;
- mutate state;
- scan project files;
- prompt the user;
- write logs.

Composition occurs through explicit function calls.

---

# 13. Canonical dependency flow

The expected high-level dependency flow is:

```text
CLI / GUI / launcher
        ↓
bootstrap and application services
        ↓
resolved configuration and shared models
        ↓
audit orchestration
        ↓
validation stages
        ↓
process and filesystem mechanisms
        ↓
GF and approved external tools
```

Result flow returns upward as data:

```text
GF raw response
        ↑
process result
        ↑
stage result
        ↑
classification and run result
        ↑
reports, CLI exit status, GUI display
```

Project policy enters through the configuration boundary:

```text
project.toml
project scenarios
project inputs
project gold
project documentation contracts
        ↓
project loader and registered validation stages
```

Generated artifacts leave through the artifact boundary:

```text
stage owners
        ↓
run paths
        ↓
raw evidence / normalized evidence / summaries / manifest
```

---

# 14. Canonical allowed-direction matrix

`✓` means generally allowed through public contracts.  
`C` means allowed only through a specifically documented contract.  
`—` means no dependency should exist.

| From \ To | L0 Utilities | L1 Models/Config | L2 Stages | L3 Orchestration | L4 Reports/State | L5 Interfaces | Active Project | External Tools |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| L0 Utilities | C | — | — | — | — | — | — | C |
| L1 Models/Config | ✓ | C | — | — | — | — | C | — |
| L2 Stages | ✓ | ✓ | C | — | — | — | ✓ | C |
| L3 Orchestration | ✓ | ✓ | ✓ | C | C | — | C | — |
| L4 Reports/State | ✓ | ✓ | — | — | C | — | C | — |
| L5 Interfaces | C | ✓ | — | ✓ | ✓ | C | — | — |
| Active Project | — | C | — | — | — | — | C | C through scenarios |
| External Tools | — | — | — | — | — | — | tool-defined | — |

Interpretation:

- L3 may request L4 report generation, but reports must not call back into L3 execution.
- L5 may call public orchestration but not individual stages.
- L2 may use active-project files only through resolved paths and project contracts.
- L0 process utilities may invoke external executables mechanically, but they must not interpret project semantics.
- Active-project scenarios may issue approved GF commands, but they do not import Python framework internals.

---

# 15. Explicitly allowed dependency directions

The following directions are expected:

```text
CLI → bootstrap
GUI → bootstrap
CLI → audit_core public entrypoint
GUI controller → audit_core public entrypoint
bootstrap → app defaults
bootstrap → project loader
bootstrap → resolved models
audit_core → run paths
audit_core → file selector
audit_core → scanner
audit_core → compiler
audit_core → fingerprint
audit_core → scenario runner
audit_core → result builder
audit_core → classifier
audit_core → diff
audit_core → release gates
audit_core → report facade
compiler → process_utils
scenario runner → process_utils
stages → shared models
reports → shared models
reports → schema writers
state service → state schema
project loader → project schema
diff → summary schema reader
manifest writer → artifact paths and hash utilities
```

All arrows mean dependency on public contracts only.

---

# 16. Explicitly prohibited dependency directions

The following are prohibited:

```text
reports → compiler
reports → scanner
reports → scenario_runner
reports → process_utils
models → reports
models → GUI
models → audit_core
process_utils → audit models
process_utils → project policy
scanner → compiler
compiler → scanner
scanner → reports
compiler → reports
scenario_runner → reports
classifier → process execution
classifier → GUI
diff → compiler
diff → Markdown reports
project configuration → GUI state
project loader → generated run output as identity source
GUI widgets → GF process
CLI parser → GF process
state → active project identity
framework defaults → active-language assumptions
active project → Python framework internals
```

Equivalent indirect paths are also prohibited.

Example:

```text
report → helper → compiler
```

is still a prohibited report-to-compiler dependency.

---

# 17. Circular dependency rules

## 17.1 General prohibition

Circular imports between architectural layers are prohibited.

Examples:

```text
models ↔ reports
audit_core ↔ report writer
compiler ↔ classifier
bootstrap ↔ GUI
project loader ↔ state
```

## 17.2 Same-layer cycles

Cycles inside one layer are also prohibited unless a narrowly justified runtime callback avoids import-time coupling.

A cycle is not acceptable merely because Python can load it under some import order.

## 17.3 Cycle-breaking order

Break a cycle using this preference order:

1. move a passive shared type into the model layer;
2. pass a value explicitly;
3. introduce a small protocol or callable type in a lower neutral layer;
4. split policy from mechanism;
5. create a narrow facade;
6. use a local import only as a temporary migration step.

A local import is not a permanent architectural solution when the conceptual cycle remains.

## 17.4 Callback rule

Callbacks may flow upward only as injected behavior.

Example:

```text
audit_core receives progress callback
```

Allowed callback payloads must use neutral progress models.

A lower stage must not import GUI code to emit progress.

---

# 18. Public and private API rules

## 18.1 Public symbols

A cross-file dependency must use:

- an explicitly exported function;
- an explicitly exported class;
- a documented dataclass or enum;
- a documented facade;
- a documented artifact or schema.

## 18.2 Private symbols

Names beginning with `_` are private unless a contract document explicitly states otherwise.

Consumers must not import private helpers to avoid creating a public API accidentally.

## 18.3 Package re-export rules

`__init__.py` may re-export stable public symbols.

It must not:

- import every submodule eagerly;
- create circular initialization;
- hide the true owner of a mutable global;
- launch work on import;
- re-export private implementation helpers.

## 18.4 Wildcard imports

Wildcard imports are prohibited in framework production code:

```python
from module import *
```

Explicit imports are required for dependency visibility.

## 18.5 Type-only imports

Type-only imports should use:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    ...
```

when this avoids a runtime cycle without hiding a real architectural dependency.

String annotations may be used where appropriate.

---

# 19. Side-effect rules

## 19.1 Import side effects

Importing a module must not:

- create directories;
- write files;
- load active project content;
- execute GF;
- start GUI event loops;
- parse process arguments;
- mutate environment variables;
- update gold;
- migrate schemas automatically;
- delete stale runs.

## 19.2 Explicit mutation

State and artifact mutation must occur through named functions or services.

The caller must be able to identify:

- what will change;
- who owns the change;
- whether the operation is atomic;
- whether the operation is destructive.

## 19.3 Global mutable state

Global mutable application state is prohibited.

Constants and immutable lookup tables are permitted.

Runtime state must be represented through:

- explicit objects;
- function parameters;
- controlled services;
- event or callback payloads.

---

# 20. Artifact ownership dependencies

An artifact has one writer and zero or more observers.

| Artifact | Writer | Allowed observers |
|---|---|---|
| `project/project.toml` | project initializer, migrator, maintainer | project loader, documentation checks |
| application state | state service | bootstrap, GUI |
| scan log | scanner | orchestration, detail reports |
| compile stdout/stderr | compiler | classifier, reports, diagnostics |
| scenario stdout/stderr | scenario runner | assertion engine, reports |
| normalized scenario output | normalization/scenario stage | gold comparator, reports |
| `.gold` | explicit gold updater or maintainer | gold comparator |
| `summary.json` | JSON report writer | diff, GUI, CLI, automation |
| `summary.md` | Markdown report writer | users, GUI |
| `AI_READY.md` | AI report writer | users, AI systems |
| `manifest.json` | manifest writer | verifier, cleanup, export tooling |
| `.gfo` / `.pgf` copies | artifact collector | release gates, reports, external consumers |

Observers must not rewrite owned artifacts.

A derived artifact must reference its source evidence.

---

# 21. Framework and active-project boundary

## 21.1 Framework domain

Framework code includes:

```text
app/
tests/
docs/
templates/
```

It owns reusable orchestration and validation behavior.

## 21.2 Active-project domain

The active project includes:

```text
project/project.toml
project/docs/
project/validation/
active language GF source files
```

It owns language-specific policy and content.

## 21.3 Prohibited framework dependencies

Framework production code must not depend on active-language identifiers such as:

```text
a language name
a language code
a language-specific module suffix
a specific Grammar<Lang>.gf filename
a specific language source directory
a project-specific known warning
```

Exceptions are limited to:

- clearly named migration fixtures;
- historical compatibility tests;
- examples explicitly marked as examples.

## 21.4 Prohibited project dependencies

Project files must not depend on:

- Python private module paths;
- GUI widget names;
- report implementation classes;
- internal process runner symbols;
- framework test fixtures;
- generated run-directory names as configuration.

The project depends on documented configuration, scenario, and artifact contracts.

## 21.5 Project GF dependency rules

GF module-to-module rules belong to:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/MODULE_DEPENDENCY_MAP.md
```

This framework document does not prescribe one language’s morphology or syntax module graph.

---

# 22. External-tool dependency boundary

## 22.1 Single process mechanism

External process execution must use one designated mechanism layer.

Individual stages may construct tool-specific requests through documented command builders.

They must not each create incompatible subprocess behavior.

## 22.2 GF path ownership

GF path construction must have one owner.

Compilation and scenario execution must consume the same resolved path model unless a documented operation-specific extension exists.

## 22.3 No implicit shell

Normal external execution must use structured arguments and avoid an intermediate shell.

Shell use requires an explicit external-tool contract.

## 22.4 Evidence dependency

Diagnostic interpretation depends on preserved stdout, stderr, exit state, timeout state, and artifacts.

No classifier or report may depend only on rendered command text or one output stream.

## 22.5 Version adapters

Version-specific GF behavior should be isolated in:

- capability probes;
- compatibility adapters;
- documented command builders.

Version checks must not be duplicated across stages.

---

# 23. Persisted-schema dependency rules

## 23.1 Writers

Each persisted format must have one canonical writer.

## 23.2 Readers

Readers must validate:

- `schema_id`;
- `schema_version`;
- required fields;
- enums;
- path semantics;
- migration compatibility.

## 23.3 Migration boundary

Legacy migration must be isolated from normal canonical writing.

A normal reader may call a migrator.

A report writer must not contain ad hoc legacy-field aliases.

## 23.4 Human-report boundary

Structured readers must not parse Markdown when a JSON schema exists.

## 23.5 State boundary

Application-state readers must not treat state as project configuration.

## 23.6 Artifact-path boundary

Consumers must use path fields from the canonical run model or manifest.

They must not independently concatenate expected filenames.

---

# 24. Test dependency rules

## 24.1 Test direction

Tests may depend on public production contracts.

Production code must never depend on test modules or test fixtures.

## 24.2 Unit tests

Unit tests should isolate:

- pure utilities;
- models;
- command construction;
- scanners;
- classifiers;
- schema handling;
- reports.

They should not require real GF unless marked as integration tests.

## 24.3 Integration tests

Integration tests may depend on:

- a controlled GF installation;
- a small neutral fixture grammar;
- temporary directories;
- explicit environment configuration.

They must not depend on:

- one developer’s global `GF_LIB_PATH`;
- the active language project unless testing that project explicitly;
- existing personal run directories;
- GUI interaction;
- network access unless separately marked and justified.

## 24.4 Fixture rules

Framework fixtures must be language-neutral where possible.

Historical language-specific fixtures must be clearly named and isolated.

## 24.5 Mock boundary

Mocks should replace external boundaries, not internal architecture indiscriminately.

Preferred mocking points:

```text
process runner
filesystem clock
environment resolver
state storage
```

Avoid mocking every internal function in `audit_core`, because this can hide broken integration contracts.

## 24.6 Contract tests

Contract tests should verify forbidden imports and required boundaries.

Suggested categories:

```text
tests/contracts/test_dependency_layers.py
tests/contracts/test_no_report_execution.py
tests/contracts/test_no_gui_process_calls.py
tests/contracts/test_framework_language_neutrality.py
tests/contracts/test_artifact_ownership.py
tests/contracts/test_schema_ownership.py
tests/contracts/test_no_circular_imports.py
```

---

# 25. Optional dependency policy

A new dependency may be:

- Python standard library;
- external Python package;
- external executable;
- operating-system service;
- project file format;
- runtime plugin or adapter.

It may be added only when:

1. the capability is required by the product scope;
2. the capability does not sufficiently exist in GF, Python, or the framework;
3. ownership is clear;
4. failure behavior is defined;
5. platform support is known;
6. security impact is reviewed;
7. version compatibility is documented;
8. tests exist;
9. licensing is acceptable;
10. the dependency can be removed or replaced through a bounded adapter.

## 25.1 Third-party Python packages

A third-party package should be imported behind the narrowest practical boundary.

Core models must not inherit from optional framework-specific base classes solely for convenience.

## 25.2 Optional imports

Optional dependencies must fail with a clear capability error.

They must not produce partial imports that corrupt unrelated workflows.

## 25.3 Dependency injection

Dependency injection should remain explicit and small.

Allowed examples:

- inject process runner into compiler tests;
- inject clock into run-ID generation;
- inject state store into GUI controller;
- inject report facade into orchestration tests.

A general runtime service container is not required.

---

# 26. Error dependency rules

## 26.1 Low-level errors

L0 may raise bounded mechanism errors such as:

- filesystem failure;
- decoding failure;
- launch failure;
- timeout mechanism failure.

## 26.2 Stage errors

L2 should convert expected mechanism outcomes into structured stage results.

It should not force every expected GF failure into a Python exception.

## 26.3 Orchestration errors

L3 distinguishes:

- validation failure;
- tool-reported failure;
- launch failure;
- timeout;
- cancellation;
- configuration error;
- framework error;
- artifact failure.

## 26.4 Interface mapping

L5 maps the final structured outcome to:

- CLI exit codes;
- GUI messages;
- process completion state.

Lower layers must not depend on CLI exit-code constants or GUI wording.

## 26.5 Report mapping

Reports display structured errors.

They must not create new causal or technical classifications independently.

---

# 27. Progress and cancellation dependencies

## 27.1 Progress

Lower layers may emit neutral progress events through injected callbacks.

A progress event may contain:

- stage ID;
- subject ID;
- completed count;
- total count;
- short message;
- severity;
- timestamp.

It must not contain GUI widget references.

## 27.2 Cancellation

Cancellation may flow downward through:

- a cancellation token;
- an event object;
- a neutral callable;
- a process-runner cancellation contract.

Stages must not inspect GUI state to decide whether to stop.

## 27.3 Partial results

Cancellation should preserve completed evidence.

Reports may summarize partial results only after orchestration finalizes a structured cancelled execution state.

---

# 28. Concurrency dependency rules

Concurrency is optional.

When introduced:

- orchestration owns scheduling policy;
- stages remain safe for isolated execution;
- artifact paths remain unique;
- report generation waits for finalized results;
- state mutation is serialized;
- log writes avoid corruption;
- cancellation propagates through neutral mechanisms;
- result ordering remains deterministic.

Stages must not create independent unmanaged thread or process pools.

---

# 29. Dependency exceptions

An exception is permitted only when no simpler compliant design satisfies a real requirement.

The exception must include:

```text
Exception ID:
Requester:
Affected modules:
Forbidden or unusual direction:
Reason:
Alternatives considered:
Risk:
Containment:
Tests:
Expiry or review trigger:
ADR:
```

## 29.1 Required approval

An exception affecting:

- layer direction;
- external execution;
- persisted schemas;
- project/framework separation;
- artifact ownership;
- security boundaries;

requires an ADR.

## 29.2 Temporary exceptions

Temporary exceptions must have:

- explicit status;
- removal condition;
- tracking issue or ledger entry;
- test preventing expansion of the exception.

## 29.3 No accidental precedent

One exception does not authorize similar dependencies elsewhere.

---

# 30. Automated enforcement

GF Wordbench should provide:

```text
gf-wordbench contracts check
```

Dependency validation should check:

1. no forbidden package imports;
2. no cycles between architectural layers;
3. reports do not import execution stages;
4. GUI modules do not import process utilities;
5. scanners and compilers do not import each other;
6. models do not import reports or UI;
7. process utilities do not import audit policy models;
8. production code does not import tests;
9. framework code does not contain active-language identifiers;
10. consumers do not import private symbols across modules;
11. artifact constants have one owner;
12. report writers do not launch subprocesses;
13. project configuration does not depend on GUI state;
14. normal runs do not rewrite gold files;
15. schema field definitions are centralized;
16. launchers do not define hidden audit policy.

Strict mode:

```text
gf-wordbench contracts check --strict
```

Strict mode may also detect:

- duplicate status literals;
- duplicate artifact filenames;
- undocumented public exports;
- import-time filesystem writes;
- environment access outside approved resolvers;
- direct `subprocess` use outside process utilities;
- direct JSON/TOML parsing outside schema owners;
- direct state-file writes outside state service;
- Markdown parsing by machine-result consumers.

---

# 31. Suggested static enforcement model

The checker may assign each module to a layer.

Example configuration:

```toml
[layers]
L0 = [
  "app.utils",
]
L1 = [
  "app.models",
  "app.config",
  "app.project_config",
  "app.schemas",
]
L2 = [
  "app.audit.file_selector",
  "app.audit.scanner",
  "app.audit.compiler",
  "app.audit.scenario_runner",
  "app.audit.fingerprint",
]
L3 = [
  "app.audit.audit_core",
  "app.audit.result_model",
  "app.audit.classifier",
  "app.audit.diff",
  "app.audit.release_gates",
]
L4 = [
  "app.reports",
  "app.state",
]
L5 = [
  "app.main_cli",
  "app.main_gui",
  "app.gui",
]
```

The exact checker format may differ.

The semantic layer rules in this document remain authoritative.

---

# 32. Dependency review checklist

A change that adds or changes a dependency is complete only when:

```text
[ ] Caller layer identified
[ ] Provider layer identified
[ ] Direction permitted
[ ] Public contract used
[ ] No private symbol imported
[ ] No cycle introduced
[ ] Configuration ownership preserved
[ ] Artifact ownership preserved
[ ] External process boundary preserved
[ ] Project/framework separation preserved
[ ] Error semantics preserved
[ ] Tests updated
[ ] Contract lock updated when public behavior changed
[ ] ADR added when an exception is required
```

---

# 33. Drift indicators

Probable dependency drift exists when:

- a report imports the compiler;
- a GUI widget imports `subprocess`;
- two stages build the GF path differently;
- a utility imports `RunResult` only to determine policy;
- a model imports a formatter or report;
- a classifier reads raw files that should already be represented in results;
- a diff component parses `summary.md`;
- a project loader reads the last run to infer language identity;
- a state file contains required project scenarios;
- a framework source file contains an active-language module suffix;
- a stage imports another stage’s private helper;
- a new artifact filename constant appears in several modules;
- a report modifies a result to make output easier;
- an `__init__.py` import causes process execution;
- a launcher supplies hidden defaults;
- a test passes only when run from one working directory;
- direct `subprocess` calls appear outside the process layer;
- direct JSON serialization appears in unrelated consumers;
- a circular import is hidden by local imports;
- generated output becomes an input to project identity;
- a normal validation path can update gold.

Each indicator requires review.

Resolution must be either:

1. restore the permitted dependency direction; or
2. approve and document a deliberate architectural change.

---

# 34. Migration from the predecessor layout

The predecessor `gf-audit` layout already contains useful separation:

```text
app/audit/
app/gui/
app/reports/
app/utils/
app/models.py
app/config.py
app/state.py
app/bootstrap.py
```

Migration to final GF Wordbench should preserve the useful boundaries while tightening them.

Required migration principles:

- keep shared dataclasses in the model layer;
- keep scanner and compiler separate;
- centralize external process execution;
- route CLI and GUI through bootstrap and audit orchestration;
- keep reports observational;
- introduce project configuration through one loader;
- introduce scenario execution as a peer validation stage;
- introduce schema ownership rather than distributed JSON assumptions;
- remove active-language defaults from framework configuration;
- retain legacy readers only in migration boundaries;
- avoid renaming modules solely for cosmetic architecture.

The target is clearer responsibility, not maximum folder depth.

---

# 35. Final dependency contract

The final architecture must preserve this flow:

```text
interfaces
    → bootstrap
        → resolved configuration
            → audit orchestration
                → validation stages
                    → process and filesystem mechanisms
                        → GF
```

Results flow back as structured data:

```text
GF evidence
    → process result
        → stage result
            → classified run result
                → reports, CLI status, GUI display
```

The following rules are absolute unless changed through an approved architectural decision:

```text
models remain passive
utilities remain policy-neutral
stages do not control the full run
orchestration does not contain UI logic
reports do not execute validation
interfaces do not bypass orchestration
framework code remains language-neutral
project policy remains project-owned
external execution remains centralized
persisted schemas remain versioned
cycles remain prohibited
```

A dependency is acceptable only when it makes responsibility clearer.

A dependency is rejected when it creates hidden policy, duplicate authority, reverse control, or evidence that cannot be traced to its owner.
