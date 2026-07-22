# GF Wordbench — Codebase Guide

**Document ID:** `GF-WB-DEVELOPMENT-CODEBASE-GUIDE`  
**Status:** Normative developer guide  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\development\CODEBASE_GUIDE.md`  
**Applies to:** GF Wordbench framework source, tests, project boundary, templates, generated artifacts, and coordinated code changes  
**Owner:** GF Wordbench maintainers  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This document explains how the GF Wordbench codebase is organized and how its components cooperate.

It is intended for developers who need to:

- understand the system before editing it;
- locate the owner of a responsibility;
- trace a validation run from CLI or GUI to generated artifacts;
- add or modify a validation stage;
- extend shared models without causing drift;
- change reports safely;
- integrate scenarios and gold comparisons;
- maintain compatibility with persisted schemas;
- distinguish framework code from active-language project code;
- identify the tests and lock files affected by a change.

This is a navigation and ownership guide.

It does not replace:

- architecture specifications;
- public API contracts;
- persisted schema definitions;
- external GF command contracts;
- project-specific GF module contracts;
- testing procedures;
- coding-style rules.

The central rule is:

> Every responsibility has one owner, and every cross-file change must update its provider, consumers, tests, schemas, and documentation together.

---

## 2. Audience

Primary audience:

```text
GF Wordbench maintainers
Python contributors
GF integration developers
report and schema maintainers
GUI and CLI developers
test authors
project-template maintainers
```

Secondary audience:

```text
active-language project maintainers
release engineers
automation authors
AI-assisted development workflows
```

A contributor editing only GF language modules should begin with:

```text
project/docs/00_PROJECT_START_HERE.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/MODULE_DEPENDENCY_MAP.md
```

A contributor editing the Python framework should begin with this guide and:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
```

---

## 3. Architectural summary

GF Wordbench is a Python orchestration framework around the external Grammatical Framework toolchain.

The runtime structure is:

```text
CLI or GUI
    → bootstrap and validation
    → immutable/resolved run configuration
    → audit orchestrator
    → validation stages
    → structured results
    → classification and comparison
    → reports and artifacts
```

GF remains authoritative for:

```text
GF syntax
GF type checking
module resolution
.gf → .gfo compilation
PGF construction
parsing
linearization
generation
morphology
grammar introspection
GF diagnostics
```

GF Wordbench remains authoritative for:

```text
configuration
file selection
command construction
process execution
timeouts
evidence capture
scenario assertions
gold comparison
diagnostic normalization
failure classification
run history
reports
artifact manifests
```

GF Wordbench MUST NOT reimplement GF semantics.

---

## 4. High-level repository layout

Final repository shape:

```text
GF_Wordbench/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE.md
├── launch_cli.bat
├── launch_gui.bat
│
├── app/
│   ├── __init__.py
│   ├── main_cli.py
│   ├── main_gui.py
│   ├── bootstrap.py
│   ├── config.py
│   ├── models.py
│   ├── state.py
│   │
│   ├── audit/
│   │   ├── __init__.py
│   │   ├── audit_core.py
│   │   ├── file_selector.py
│   │   ├── scanner.py
│   │   ├── compiler.py
│   │   ├── scenario_runner.py
│   │   ├── diagnostics.py
│   │   ├── classifier.py
│   │   ├── fingerprint.py
│   │   ├── diff.py
│   │   └── result_model.py
│   │
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── report_json.py
│   │   ├── report_md.py
│   │   ├── report_ai_ready.py
│   │   ├── report_logs.py
│   │   └── report_details.py
│   │
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── validators.py
│   │   ├── dialogs.py
│   │   └── widgets.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── process_utils.py
│       ├── path_utils.py
│       ├── io_utils.py
│       ├── logging_utils.py
│       └── gf_utils.py
│
├── tests/
│   ├── contracts/
│   ├── fixtures/
│   ├── integration/
│   └── test_*.py
│
├── docs/
│   └── ...
│
├── project/
│   ├── project.toml
│   ├── docs/
│   └── validation/
│       ├── scenarios/
│       ├── gold/
│       └── inputs/
│
└── templates/
    └── project/
        ├── project.toml
        ├── docs/
        └── validation/
```

The final tree may gain narrowly focused files when a responsibility becomes independently owned.

It MUST NOT gain layers only to mirror documentation headings.

---

## 5. Current migration baseline

The inherited GF Audit code already contains the main framework layers:

```text
entrypoints
bootstrap
configuration defaults
shared models
state
file selection
static scan
compilation
classification
fingerprinting
previous-run diff
result construction
audit orchestration
JSON, Markdown, AI, detail and aggregate reports
GUI
process, path, I/O, logging and GF helpers
tests
```

The final GF Wordbench design adds or formalizes:

```text
canonical quick/checkpoint/release/diagnostic modes
project/project.toml loading
ScenarioResult
app/audit/scenario_runner.py
app/audit/diagnostics.py
native .gfs scenarios
gold comparison
PGF release build
artifact manifest
versioned schemas and migrations
contract tests
```

Migration code may temporarily support GF Audit names and formats.

New canonical code MUST use GF Wordbench terminology.

---

# 6. Layer model

The framework is divided into six layers.

```text
1. presentation
2. configuration
3. orchestration
4. validation stages
5. shared infrastructure
6. persistence and reporting
```

---

## 6.1 Presentation layer

Files:

```text
app/main_cli.py
app/main_gui.py
app/gui/
launch_cli.bat
launch_gui.bat
```

Responsibilities:

- gather user input;
- display validation errors;
- call bootstrap;
- call `run_audit`;
- show run completion;
- expose generated artifacts.

The presentation layer MUST NOT:

- compile GF directly;
- scan files directly;
- run scenarios directly;
- construct GF paths independently;
- write reports independently;
- define different audit semantics for CLI and GUI.

---

## 6.2 Configuration layer

Files:

```text
app/config.py
app/bootstrap.py
app/state.py
project/project.toml
```

Responsibilities:

- define framework defaults;
- load active-project configuration;
- load disposable application state;
- apply precedence;
- validate paths and modes;
- construct `AppConfig`, `ProjectConfig`, `RunConfig`, and `RunPaths`.

The configuration layer MUST produce enough information for a non-interactive run.

---

## 6.3 Orchestration layer

File:

```text
app/audit/audit_core.py
```

Responsibilities:

- coordinate run lifecycle;
- invoke stages in mode-defined order;
- preserve partial evidence;
- construct final results;
- trigger classification and comparison;
- invoke report writers;
- return `RunResult`.

The orchestrator decides sequence.

It does not own stage algorithms.

---

## 6.4 Validation-stage layer

Files:

```text
app/audit/file_selector.py
app/audit/scanner.py
app/audit/compiler.py
app/audit/scenario_runner.py
app/audit/diagnostics.py
app/audit/classifier.py
app/audit/fingerprint.py
app/audit/diff.py
app/audit/result_model.py
```

Each file owns one stable concern.

A stage MUST return structured evidence.

A stage MUST NOT produce user-facing reports.

---

## 6.5 Shared infrastructure layer

Files:

```text
app/models.py
app/utils/process_utils.py
app/utils/path_utils.py
app/utils/io_utils.py
app/utils/logging_utils.py
app/utils/gf_utils.py
```

Responsibilities:

- stable typed data;
- process launch;
- path normalization;
- atomic and safe I/O;
- reusable logging;
- shared GF output helpers.

Infrastructure MUST remain independent of GUI presentation.

---

## 6.6 Persistence and reporting layer

Files:

```text
app/reports/
app/state.py
project/project.toml
run_<run-id>/
```

Responsibilities:

- serialize canonical machine data;
- create human reports;
- create AI handoff reports;
- aggregate raw evidence;
- maintain application state;
- preserve artifact ownership.

Reports observe results.

They do not reconstruct missing execution evidence by rerunning stages.

---

# 7. Architectural ownership map

| Responsibility | Owner |
|---|---|
| Application identity and version | `app/__init__.py` |
| Packaging and entrypoint declarations | `pyproject.toml` |
| Application defaults | `app/config.py` |
| Project and run configuration construction | `app/bootstrap.py` |
| Shared data contracts | `app/models.py` |
| Persistent GUI/application state | `app/state.py` |
| CLI behavior | `app/main_cli.py` |
| GUI startup | `app/main_gui.py` |
| GUI interaction | `app/gui/main_window.py` |
| GUI-only validation feedback | `app/gui/validators.py` |
| GUI dialogs | `app/gui/dialogs.py` |
| Reusable GUI widgets | `app/gui/widgets.py` |
| Run orchestration | `app/audit/audit_core.py` |
| File discovery and exclusion | `app/audit/file_selector.py` |
| Static source heuristics | `app/audit/scanner.py` |
| GF module compilation | `app/audit/compiler.py` |
| `.gfs` scenario execution | `app/audit/scenario_runner.py` |
| Diagnostic normalization | `app/audit/diagnostics.py` |
| Causal classification | `app/audit/classifier.py` |
| Source fingerprints | `app/audit/fingerprint.py` |
| Previous-run comparison | `app/audit/diff.py` |
| Result aggregation | `app/audit/result_model.py` |
| External process execution | `app/utils/process_utils.py` |
| GF helper parsing and normalization | `app/utils/gf_utils.py` |
| Filesystem primitives | `app/utils/io_utils.py` |
| Path normalization and safe names | `app/utils/path_utils.py` |
| Shared log formatting | `app/utils/logging_utils.py` |
| Canonical JSON summary | `app/reports/report_json.py` |
| Human Markdown summary | `app/reports/report_md.py` |
| AI handoff | `app/reports/report_ai_ready.py` |
| Aggregate logs and top errors | `app/reports/report_logs.py` |
| Per-result detail artifacts | `app/reports/report_details.py` |
| Artifact manifest | one designated manifest writer |
| Active-language project identity | `project/project.toml` |
| Project GF contracts | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Native GF scenarios | `project/validation/scenarios/` |
| Reviewed expectations | `project/validation/gold/` |
| Scenario input fixtures | `project/validation/inputs/` |
| Generic new-project source | `templates/project/` |

No second owner may be introduced without an explicit contract change.

---

# 8. Application entrypoints

## 8.1 `app/__init__.py`

Owns:

```text
__app_name__
__version__
```

Expected final identity:

```python
__app_name__ = "gf-wordbench"
```

`pyproject.toml` may load the version dynamically from this file.

Rules:

- keep import side effects minimal;
- do not initialize GUI;
- do not load project configuration;
- do not execute validation;
- do not import reports or audit stages.

---

## 8.2 `app/main_cli.py`

Purpose:

```text
command-line presentation and exit-code boundary
```

Typical flow:

```text
parse arguments
    → build configuration through bootstrap
    → call run_audit
    → show concise result paths
    → return stable exit code
```

Owns:

- parser construction;
- command and subcommand routing;
- terminal summaries;
- exit-code mapping;
- CLI-specific input normalization.

Does not own:

- default configuration values;
- project TOML schema;
- file-selection logic;
- GF command construction;
- audit execution details;
- report serialization.

Expected imports:

```text
bootstrap
audit_core
shared models or exit-code reference
```

Forbidden direct imports:

```text
compiler
scanner
scenario_runner
report internals
GUI widgets
```

---

## 8.3 `app/main_gui.py`

Purpose:

```text
Qt application startup and fatal GUI error boundary
```

Owns:

- `QApplication` construction;
- global GUI initialization;
- top-level exception handling;
- main-window creation;
- optional application metadata.

Does not own:

- validation forms;
- run configuration semantics;
- audit stages;
- state schema;
- generated reports.

`main_gui.py` should remain small.

---

# 9. Bootstrap and configuration

## 9.1 `app/config.py`

Purpose:

```text
framework-owned defaults and stable constants
```

Appropriate contents:

```text
default timeouts
default output names
default mode
supported schema IDs
supported version ranges
application name
default state filename
generic scan defaults
```

Inappropriate contents:

```text
active language name
active module suffix
active source directory
project entrypoints
project scenarios
absolute local GF path
absolute local RGL path
user preferences
```

A value that varies by active language belongs in:

```text
project/project.toml
```

A value that varies by machine belongs in:

```text
environment configuration or application state
```

---

## 9.2 `app/bootstrap.py`

Purpose:

```text
turn defaults, project config, environment values and user choices into validated typed configuration
```

Expected public responsibilities:

```python
build_app_config(...)
load_project_config(...)
build_run_config(...)
build_run_paths(...)
load_app_state(...)
```

Exact function names must follow the interfile lock.

Bootstrap owns:

- configuration precedence;
- legacy alias migration;
- mode normalization;
- path resolution;
- required-value validation;
- construction of typed config objects;
- construction of run-owned paths.

Bootstrap MUST NOT:

- execute an audit;
- compile GF;
- run scenarios;
- write user reports;
- mutate project source;
- infer active language identity from GUI state;
- hide unresolved required values.

CLI and GUI MUST use the same builder.

---

## 9.3 `app/state.py`

Purpose:

```text
read and write disposable application convenience state
```

Canonical artifact:

```text
.gf_wordbench_state.json
```

State may contain:

```text
recently selected paths
last UI mode
window preferences
recent output root
non-authoritative convenience settings
```

State MUST NOT contain:

```text
active project identity
required scenarios
project entrypoints
audit results
gold expectations
credentials
secrets
```

A corrupt state file must not make the framework unusable.

The state loader should fall back safely.

Writes should be atomic.

---

# 10. Shared models

## 10.1 `app/models.py`

Purpose:

```text
authoritative Python data contracts shared across framework modules
```

Expected major models:

```text
AppConfig
ProjectConfig
RunConfig
RunPaths
ScanCounts
SourceFingerprint
ProcessResult
CompileSummary
FileResult
ScenarioResult
DiffEntry
RunResult
TopError
ArtifactRecord
```

The exact final set may consolidate small records when doing so preserves clear ownership.

### Model rules

Shared models MUST:

- use typed fields;
- use stable field meanings;
- avoid shared mutable defaults;
- use consistent internal path types;
- separate runtime fields from serialized fields;
- centralize serialization;
- use documented enums;
- provide safe defaults only for genuinely optional values.

Shared models MUST NOT:

- import GUI;
- import report writers;
- launch processes;
- depend on one active language;
- acquire dynamic undocumented attributes.

### Enum dimensions

Keep separate:

```text
validation status
execution state
error kind
diagnostic class
change kind
validation mode
```

Do not use one enum to answer several questions.

---

## 10.2 Runtime paths versus persisted paths

Runtime:

```python
Path
```

Canonical persistence:

```text
project-relative or run-relative POSIX string
```

Conversion belongs to centralized serialization or path helpers.

Individual report writers MUST NOT invent competing path conversion.

---

## 10.3 Model evolution

Adding or changing a public field requires review of:

```text
app/models.py
all constructors
all consumers
JSON serialization
JSON readers
diff loading
reports
fixtures
contract tests
PERSISTED_SCHEMA_LOCK.md
INTERFILE_CONTRACT_LOCK.md
migration code
```

A required field rename is a breaking change.

An optional field needs a documented default and compatibility behavior.

---

# 11. Audit orchestration

## 11.1 `app/audit/audit_core.py`

Canonical public boundary:

```python
run_audit(
    run_config: RunConfig,
    run_paths: RunPaths | None = None,
) -> RunResult
```

Purpose:

```text
coordinate a complete run without owning individual stage algorithms
```

Typical final flow:

```text
validate resolved run configuration
build or receive RunPaths
initialize run evidence
probe GF version when required
select source files
scan and fingerprint selected files
compile according to mode
classify file failures
run scenarios according to mode
compare scenario output with gold
build RunResult
load compatible previous run
build diff entries
write reports and manifest
return RunResult
```

### Orchestrator responsibilities

- mode-specific stage order;
- continuation and stop policy;
- partial failure containment;
- aggregation of stage results;
- final run status;
- report invocation;
- master run lifecycle.

### Orchestrator non-responsibilities

- regex filtering internals;
- scanner pattern logic;
- GF argument details;
- diagnostic text patterns;
- gold normalization;
- report prose;
- low-level process handling.

### Failure containment

The orchestrator should continue independent checks when safe.

It should stop when:

```text
configuration is unusable
output root is unusable
GF cannot be launched for any required stage
cancellation is requested
continuation risks evidence corruption
```

It must preserve already captured evidence.

---

# 12. File selection

## 12.1 `app/audit/file_selector.py`

Purpose:

```text
build the exact deterministic GF source target set for one run
```

Owns:

- source-root discovery;
- recursive glob enumeration;
- include and exclude regexes;
- explicit target resolution;
- quick-mode cardinality;
- checkpoint order;
- release ordered union;
- diagnostic sorting;
- deduplication;
- exclusion reasons;
- `max_files` behavior;
- module-name expectation from filename.

Expected public boundary:

```python
select_files(run_config: RunConfig)
```

The selector does not:

- open GF;
- scan source contents;
- compile;
- classify failures;
- write reports;
- create run directories.

Only selected files proceed to scanner and compiler.

Detailed behavior:

```text
docs/validation/FILE_SELECTION.md
```

---

# 13. Static scanner

## 13.1 `app/audit/scanner.py`

Purpose:

```text
perform deterministic non-authoritative source heuristics
```

Current useful checks include:

```text
suspicious lambda arrow spelling
suspicious table arrow spelling
runtime string matching patterns
untyped case string patterns
untyped table string patterns
trailing whitespace
```

The scanner may strip comments and mask string literals for pattern accuracy.

It MUST preserve the distinction:

```text
scan finding ≠ GF compile error
```

Expected result:

```text
ScanCounts
scan evidence path
```

Scanner owns per-file scan logs.

It does not:

- type-check GF;
- assign direct/downstream;
- compile;
- rewrite source;
- change selection;
- generate summary reports.

---

# 14. GF compiler

## 14.1 `app/audit/compiler.py`

Purpose:

```text
compile one selected GF module and produce authoritative process and artifact evidence
```

Canonical module compilation:

```text
<gf> -batch -s <path-options> <artifact-options> <source-file>
```

Owns:

- GF version probe adapter;
- compile-argument construction;
- compiler working directory;
- per-file raw stdout/stderr locations;
- call to process runner;
- `.gfo` artifact verification;
- `CompileSummary`.

Does not own:

- process implementation;
- downstream classification;
- PGF release policy;
- user reports;
- source selection;
- source mutation.

Detailed behavior:

```text
docs/gf/GF_COMPILATION.md
```

PGF build remains a separate release stage.

It may be implemented in this module only while the ownership remains explicit and the API remains distinct.

A dedicated PGF builder becomes justified when it has independent configuration, artifacts, tests, and failure policy.

---

# 15. Scenario runner

## 15.1 `app/audit/scenario_runner.py`

Purpose:

```text
execute registered native GF `.gfs` scenarios and return ScenarioResult
```

Expected public boundaries:

```python
run_scenario(...)
run_required_scenarios(...)
```

Owns:

- scenario registration resolution;
- `.gfs` script path;
- scenario process request;
- stdin or script invocation mode;
- scenario stdout/stderr paths;
- marker verification;
- normalized scenario output;
- scenario assertions;
- gold path association;
- scenario-produced artifact records.

Required `ScenarioResult` information:

```text
scenario ID
script path
required or optional flag
status
command
working directory
exit code
execution state
duration
stdout path
stderr path
normalized output path
gold path
diagnostic kind
primary message
produced artifacts
```

The runner MUST NOT:

- update gold during a normal run;
- hide missing markers;
- treat zero exit alone as scenario success;
- implement GF shell semantics in Python;
- launch through an undocumented shell;
- produce user-facing reports.

---

# 16. Diagnostic normalization

## 16.1 `app/audit/diagnostics.py`

Purpose:

```text
centralize normalized interpretation of raw GF and stage evidence
```

This module separates raw tool text from stable diagnostic fields.

May own:

```text
GF compile diagnostic patterns
scenario diagnostic patterns
normalized references
first error extraction
error-kind assignment
fatal-diagnostic detection
```

It MUST NOT:

- launch GF;
- assign downstream causality;
- write reports;
- replace raw logs;
- remove unknown evidence;
- contain language-specific grammar rules.

`app/utils/gf_utils.py` may retain low-level reusable parsing helpers.

Ownership must not be duplicated.

Recommended division:

```text
gf_utils.py     → low-level GF text utilities
diagnostics.py  → framework diagnostic normalization policy
classifier.py   → causal relationship
```

---

# 17. Failure classifier

## 17.1 `app/audit/classifier.py`

Purpose:

```text
classify failed results as direct, downstream, or ambiguous and resolve blockers
```

Consumes:

```text
structured statuses
normalized diagnostic references
peer results
module and file identities
```

Owns:

```text
diagnostic_class
is_direct
blocked_by
blocker graph
cycle handling
root blocker normalization
```

Does not own:

```text
process execution
raw diagnostic parsing
status creation
report formatting
source dependency parsing
```

Canonical precedence:

```text
known failing external blocker
    → downstream

otherwise strong local evidence
    → direct

otherwise
    → ambiguous
```

Detailed behavior:

```text
docs/diagnostics/ERROR_CLASSIFICATION.md
```

---

# 18. Fingerprints

## 18.1 `app/audit/fingerprint.py`

Purpose:

```text
create stable source identity evidence
```

Expected data:

```text
size
cryptographic hash
last-modified timestamp where retained
```

Canonical new hashing:

```text
SHA-256
```

Legacy `sha1_short` may be read during migration but should not remain the final canonical fingerprint.

Fingerprints support:

- stale artifact detection;
- run comparison;
- source identity;
- release evidence.

Fingerprints do not decide whether source is correct.

---

# 19. Previous-run diff

## 19.1 `app/audit/diff.py`

Purpose:

```text
compare the current RunResult with one compatible previous run
```

Owns:

- previous-run discovery;
- canonical summary loading;
- legacy summary migration;
- subject matching;
- `DiffEntry`;
- change-kind assignment.

Canonical change kinds:

```text
unchanged
improved
regressed
new
removed
```

The diff engine compares structured data.

It MUST NOT parse `summary.md` as the source of truth.

It MUST reject or label incompatible schemas rather than guessing.

---

# 20. Result construction

## 20.1 `app/audit/result_model.py`

Purpose:

```text
construct and aggregate shared result models without executing stages
```

Expected responsibilities:

```text
build FileResult
build ScenarioResult
build RunResult
update totals
bucket top errors
normalize deterministic ordering
validate aggregate coherence
```

Result construction should be centralized.

Stages should not each invent partial `RunResult` shapes.

This module MUST NOT:

- launch GF;
- run scans;
- classify raw diagnostics independently;
- write reports;
- load GUI state.

---

# 21. Reports

## 21.1 Reporting rule

All report writers:

- consume `RunResult`;
- use paths from `RunPaths`;
- preserve deterministic ordering;
- reference existing raw evidence;
- never rerun validation;
- never mutate project files;
- never update gold;
- never define new status semantics.

---

## 21.2 `app/reports/report_json.py`

Owns:

```text
summary.json
```

Purpose:

```text
write the canonical machine-readable run summary
```

It must follow:

```text
docs/PERSISTED_SCHEMA_LOCK.md
docs/reports/SUMMARY_JSON_REFERENCE.md
```

The writer should centralize path serialization and schema fields.

Readers should not depend on Python dataclass layout directly.

---

## 21.3 `app/reports/report_md.py`

Owns:

```text
summary.md
```

Purpose:

```text
human-readable run overview
```

It must derive every factual statement from structured results.

It must not become a machine source of truth.

---

## 21.4 `app/reports/report_ai_ready.py`

Owns:

```text
AI_READY.md
```

Purpose:

```text
bounded self-contained diagnostic handoff for humans and AI systems
```

It should prioritize:

```text
direct failures
ambiguous execution errors
downstream failures grouped by blocker
relevant evidence excerpts
artifact paths
```

It must not perform a second compilation.

---

## 21.5 `app/reports/report_logs.py`

Owns:

```text
master.log
ALL_SCAN_LOGS.TXT
ALL_LOGS.TXT
top_errors.txt
```

Responsibilities:

- deterministic aggregation;
- bounded or explicit output policies;
- top-error text rendering;
- references to source logs.

It does not own the raw logs created by stages.

---

## 21.6 `app/reports/report_details.py`

Owns:

```text
details/
```

Purpose:

```text
create per-result convenient evidence bundles or references
```

Detail artifacts must preserve source identity and avoid filename collisions.

They copy or reference existing evidence.

They do not regenerate evidence.

---

## 21.7 Artifact manifest

Canonical artifact:

```text
manifest.json
```

One writer must own it.

Before implementing or moving the writer:

```text
1. choose and record the owner
2. update architectural ownership map
3. update RunPaths
4. update schema lock
5. update all artifact producers
6. update verifier and tests
```

No report module may invent a separate manifest format.

---

# 22. GUI package

## 22.1 `app/gui/main_window.py`

Purpose:

```text
coordinate user interaction without owning audit semantics
```

Typical responsibilities:

- render fields;
- load state into fields;
- gather plain values;
- request bootstrap validation;
- run audit in a worker thread;
- display progress;
- display result summary;
- open generated paths;
- persist convenience state.

It may import:

```text
bootstrap
models
state
audit_core
GUI validators
dialogs
widgets
```

It MUST NOT import:

```text
compiler
scanner
scenario_runner
report writers
```

Equivalent GUI and CLI inputs must produce equivalent `RunConfig`.

---

## 22.2 `app/gui/validators.py`

Purpose:

```text
provide early GUI feedback
```

GUI validation may check:

```text
required fields
path existence
integer ranges
visible mode requirements
regex syntax
```

It does not replace bootstrap validation.

The authoritative builder must reject invalid input even when GUI checks are bypassed.

---

## 22.3 `app/gui/dialogs.py`

Purpose:

```text
centralize file and directory dialogs and message-box helpers
```

Dialog helpers should return plain paths or values.

They do not mutate configuration models directly.

---

## 22.4 `app/gui/widgets.py`

Purpose:

```text
provide reusable visual controls without audit logic
```

Widgets may own display behavior.

They must not launch GF or construct run configuration.

---

# 23. Utility package

## 23.1 `app/utils/process_utils.py`

Purpose:

```text
run external processes with explicit arguments, working directory, timeout, and stream capture
```

Owns:

```text
Popen/subprocess interaction
process duration
timeout containment
termination
exit code
stdout/stderr capture
launch-failure representation
```

Does not own:

```text
GF diagnostic parsing
audit status
mode semantics
reports
project configuration
```

Preferred API accepts:

```text
executable
ordered argument sequence
working directory
environment mapping
stdin or input path
stdout path
stderr path
timeout
```

Normal execution uses:

```text
shell = false
```

---

## 23.2 `app/utils/path_utils.py`

Purpose:

```text
centralize stable and safe path operations
```

May own:

```text
project-relative conversion
run-relative conversion
safe artifact keys
containment checks
separator normalization
deduplication identity
Windows-safe filenames
```

A consumer MUST NOT reproduce these rules privately.

---

## 23.3 `app/utils/io_utils.py`

Purpose:

```text
safe text and structured file I/O
```

May own:

```text
UTF-8 reads
atomic writes
JSON loading
JSON writing
bounded excerpts
directory creation
hashing helpers
```

Writers remain responsible for schema meaning.

I/O utilities own mechanics.

---

## 23.4 `app/utils/logging_utils.py`

Purpose:

```text
shared log formatting and logger configuration
```

May own:

```text
UTC timestamp formatting
safe message formatting
logger creation
bounded diagnostic rendering
```

It must not define validation status.

---

## 23.5 `app/utils/gf_utils.py`

Purpose:

```text
low-level reusable GF-specific helpers
```

May own:

```text
GF path rendering
version text extraction
diagnostic text utilities
module reference extraction helpers
output normalization primitives
```

It MUST NOT become:

```text
a second compiler
a second scenario runner
a second classifier
a report generator
```

---

# 24. Active project boundary

## 24.1 `project/`

The active project contains replaceable language-specific content.

Framework code MUST NOT hardcode its language identity.

Canonical project areas:

```text
project/project.toml
project/docs/
project/validation/scenarios/
project/validation/gold/
project/validation/inputs/
project GF source root
```

The active project owns:

- language identity;
- module suffix;
- source tree;
- entrypoints;
- checkpoints;
- scenario IDs;
- required scenarios;
- gold outputs;
- release criteria;
- module contracts.

---

## 24.2 `project/project.toml`

Authoritative for:

```text
project ID
display name
language code
source root
source filters
GF path parts
entrypoints
checkpoints
required scenarios
optional scenarios
release PGF policy
```

It is consumed through the project loader and bootstrap.

No GUI state may override it silently.

---

## 24.3 `project/docs/`

Contains language-specific design truth.

Important files:

```text
INTERFILE_CONTRACT_LOCK.md
LANGUAGE_ARCHITECTURE.md
MODULE_DEPENDENCY_MAP.md
CATEGORY_AND_LINCAT_CONTRACT.md
MORPHOLOGY_SPEC.md
SYNTAX_AND_CONSTRUCTOR_RULES.md
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
STATUS_LEDGER.md
DECISION_LOG.md
KNOWN_ISSUES.md
RELEASE_CRITERIA.md
```

Framework documentation must not duplicate these language-specific contracts.

---

## 24.4 `project/validation/`

Contains executable project validation assets.

```text
scenarios/  → native GF `.gfs`
gold/       → reviewed normalized expected output
inputs/     → reviewed input fixtures
```

Normal validation is read-only with respect to scenarios, inputs, and gold.

---

# 25. Project template boundary

## 25.1 `templates/project/`

This directory mirrors the active-project structure.

It contains:

- generic placeholders;
- language-neutral documentation;
- starter scenario directories;
- starter `project.toml`.

It MUST NOT contain:

- active-language identifiers;
- old source paths;
- run history;
- local GF executable paths;
- completed active-project decisions;
- copied gold from another language unless explicitly marked as a generic example.

Initialization copies or renders the template into `project/`.

The active project is then independently maintained.

Template updates do not silently overwrite an active project.

---

# 26. Generated run boundary

A run directory is generated evidence, not source.

Canonical conceptual layout:

```text
run_<run-id>/
├── summary.json
├── summary.md
├── AI_READY.md
├── top_errors.txt
├── manifest.json
├── master.log
├── raw/
│   ├── scan/
│   ├── compile/
│   └── scenarios/
├── details/
└── artifacts/
    ├── gfo/
    ├── pgf/
    └── out/
```

Rules:

- `RunPaths` owns actual locations;
- stages write only their owned evidence;
- reports read existing evidence;
- a run never rewrites project source;
- a run never rewrites gold;
- a new run uses a new run ID;
- previous runs are immutable evidence unless cleanup policy removes them.

---

# 27. End-to-end data flow

## 27.1 Configuration flow

```text
app/config.py defaults
    +
project/project.toml
    +
environment or application state
    +
CLI or GUI values
    ↓
app/bootstrap.py
    ↓
ProjectConfig
RunConfig
RunPaths
```

---

## 27.2 File validation flow

```text
RunConfig
    ↓
file_selector.select_files
    ↓
selected Path
    ├── scanner.scan_file
    ├── fingerprint.build_source_fingerprint
    └── compiler.compile_file
            ↓
        CompileSummary
    ↓
result_model.build_file_result
    ↓
FileResult
```

---

## 27.3 Classification flow

```text
deterministic list[FileResult]
    +
normalized references
    ↓
classifier.classify_file_results
    ↓
diagnostic_class
is_direct
blocked_by
```

---

## 27.4 Scenario flow

```text
ProjectConfig scenario IDs
    ↓
scenario_runner
    ↓
GF process
    ↓
raw stdout/stderr
    ↓
marker checks
normalization
assertions
gold comparison
    ↓
ScenarioResult
```

---

## 27.5 Run aggregation flow

```text
FileResult[]
ScenarioResult[]
DiffEntry[]
artifact records
metadata
    ↓
result_model.build_run_result
    ↓
RunResult
```

---

## 27.6 Reporting flow

```text
RunResult
RunPaths
existing evidence
    ├── report_json
    ├── report_md
    ├── report_ai_ready
    ├── report_logs
    ├── report_details
    └── manifest writer
```

---

# 28. Dependency directions

Expected directions:

```text
CLI/GUI → bootstrap
CLI/GUI → audit_core
audit_core → validation stages
validation stages → process_utils
validation stages → models
audit_core → result_model
audit_core → classifier
audit_core → diff
audit_core → reports
reports → models
reports → existing evidence
bootstrap → config/models/state/project loader
```

Prohibited directions:

```text
reports → compiler
reports → scanner
reports → scenario_runner
models → reports
models → GUI
process_utils → audit models
scanner → compiler
compiler → reports
classifier → process execution
project configuration → GUI state
utils → presentation layer
active project → Python framework internals
```

Circular dependencies between architectural layers are prohibited.

---

# 29. Import rules

## 29.1 Public imports

Cross-module consumers should import documented public symbols.

Example:

```python
from app.audit.compiler import compile_file
```

A private helper beginning with `_` is not a stable interfile API.

## 29.2 Package `__init__.py`

Package exports may provide stable convenience imports.

They should not export every internal helper.

Changing `__all__` is a public API change when other files rely on it.

## 29.3 Relative versus absolute imports

Within the installed package, use one consistent policy.

Recommended:

```python
from app.models import RunConfig
```

or consistent package-relative imports:

```python
from ..models import RunConfig
```

Do not maintain fallback imports that allow running the same file both as a package and as an unstructured script indefinitely.

Canonical execution is:

```text
installed entrypoint
python -m app.main_cli
python -m app.main_gui
```

Direct file execution compatibility may be removed after migration.

---

# 30. Status and error flow

Four dimensions remain separate:

```text
validation_status
execution_state
error_kind
diagnostic_class
```

Example compile timeout:

```text
validation_status = ERROR
execution_state = timed_out
error_kind = TIMEOUT
diagnostic_class = ambiguous
```

Example local GF syntax failure:

```text
validation_status = FAIL
execution_state = completed
error_kind = SYNTAX
diagnostic_class = direct
```

Example dependency cascade:

```text
validation_status = FAIL
execution_state = completed
error_kind = OTHER
diagnostic_class = downstream
blocked_by = ["<dependency-path>"]
```

No module may introduce new values locally.

Canonical values are defined in:

```text
docs/GLOSSARY.md
docs/reference/STATUS_VALUES.md
docs/reference/DIAGNOSTIC_KINDS.md
```

---

# 31. Exception boundaries

Exceptions should become structured errors at the nearest layer that has enough context.

Recommended boundaries:

```text
bootstrap
    → configuration error

process_utils
    → launch or timeout result

compiler/scenario runner
    → stage result

audit_core
    → run-level containment

CLI
    → exit code and concise terminal message

GUI
    → visible error dialog and preserved traceback log
```

Avoid broad exception swallowing.

When broad containment is necessary:

- preserve original exception details in safe logs;
- produce a structured `ERROR`;
- do not fabricate success;
- continue only when safe.

---

# 32. Determinism rules

The following must be deterministic:

```text
selected file order
checkpoint order
entrypoint order
scenario order
blocker order
artifact path order
top-error order
report sections
JSON list order where semantically meaningful
previous-run matching
```

Determinism MUST NOT depend on:

```text
filesystem traversal order
unordered set iteration
localized strings
current working directory
random generation without seed
GUI widget order
dictionary order from legacy data
```

---

# 33. Adding a new validation stage

Use this sequence:

```text
1. define the criterion
2. identify the owner
3. define typed inputs
4. define typed result
5. define raw evidence
6. define status and error semantics
7. define RunPaths locations
8. implement stage without reports
9. add audit_core orchestration
10. add result aggregation
11. add JSON serialization
12. add human reporting
13. add tests
14. update lock files
15. update architecture and validation docs
```

A new stage is justified when it has:

- a distinct criterion;
- distinct inputs;
- distinct evidence;
- distinct failure behavior;
- an independent owner.

Do not create a stage merely to wrap one trivial helper call.

---

# 34. Adding a shared model field

Checklist:

```text
[ ] field owner identified
[ ] meaning documented
[ ] required or optional decided
[ ] default defined when optional
[ ] constructors updated
[ ] stage producers updated
[ ] consumers searched
[ ] JSON writer updated
[ ] JSON reader/migrator updated
[ ] reports reviewed
[ ] diff behavior reviewed
[ ] fixtures updated
[ ] schema version impact classified
[ ] contract tests updated
[ ] lock files updated
```

Never add a field only to satisfy one report when it can be derived safely from existing structured data.

Never make reports parse another report to obtain it.

---

# 35. Adding a CLI option

Checklist:

```text
[ ] option belongs to CLI rather than project.toml
[ ] parser updated
[ ] normalized plain value produced
[ ] bootstrap accepts value
[ ] precedence documented
[ ] RunConfig field exists or is intentionally reused
[ ] GUI equivalence reviewed
[ ] validation added
[ ] help text added
[ ] CLI tests added
[ ] smoke tests added
[ ] CLI reference updated
```

The CLI MUST NOT mutate `RunConfig` after bootstrap returns it.

---

# 36. Adding a GUI setting

Checklist:

```text
[ ] setting is presentation or convenience data
[ ] authoritative project fact remains in project.toml
[ ] widget returns plain Python value
[ ] GUI validator provides early feedback
[ ] bootstrap remains authoritative
[ ] state persistence classified as safe or prohibited
[ ] CLI equivalent reviewed
[ ] worker-thread behavior reviewed
[ ] GUI tests added
[ ] GUI reference updated
```

Do not make a GUI-only value required for headless execution.

---

# 37. Adding a report field or section

Checklist:

```text
[ ] source exists in RunResult or owned evidence
[ ] report does not rerun stages
[ ] JSON schema impact assessed
[ ] Markdown section purpose defined
[ ] AI report size impact assessed
[ ] deterministic ordering defined
[ ] path semantics defined
[ ] legacy reader impact reviewed
[ ] report tests updated
[ ] schema/reference docs updated
```

A JSON field is a persisted schema change.

A Markdown wording change may be internal unless another tool parses it.

---

# 38. Adding a diagnostic rule

Checklist:

```text
[ ] raw evidence pattern documented
[ ] error_kind selected
[ ] causal classification kept separate
[ ] false-positive risk assessed
[ ] stdout and stderr fixtures added
[ ] Windows and POSIX paths tested
[ ] Unicode tested
[ ] unrecognized fallback preserved
[ ] raw logs unchanged
[ ] diagnostic docs updated
```

A diagnostic rule should live in:

```text
diagnostics.py
```

or a low-level helper used exclusively by it.

It should not be copied into reports or classifier.

---

# 39. Adding an external tool

Before adding another executable:

```text
[ ] GF or Python cannot already provide the capability sufficiently
[ ] tool purpose documented
[ ] version policy documented
[ ] license reviewed
[ ] installation method documented
[ ] command contract defined
[ ] executable resolution defined
[ ] arguments ordered
[ ] working directory explicit
[ ] environment explicit
[ ] stdin/stdout/stderr behavior defined
[ ] timeout defined
[ ] artifacts defined
[ ] failure semantics defined
[ ] security reviewed
[ ] fake-process tests added
[ ] real integration tests added
[ ] EXT-OPTIONAL contract created
```

Do not add an executable only for convenience.

---

# 40. Adding or changing scenarios

Checklist:

```text
[ ] scenario ID unique
[ ] scenario registered in project.toml
[ ] required/optional status defined
[ ] entrypoint relationship documented
[ ] input files registered
[ ] markers unique and complete
[ ] termination behavior defined
[ ] normalization profile selected
[ ] gold requirement decided
[ ] ScenarioResult fields populated
[ ] normal run proven not to update gold
[ ] tests added
[ ] project validation spec updated
[ ] project lock updated
```

Scenario logic belongs in `.gfs`.

Python should orchestrate and validate the observable contract.

---

# 41. Changing gold normalization

This is a high-risk change.

Required coordinated review:

```text
normalizer
scenario runner
all affected gold files
comparison logic
scenario fixtures
schema version
project validation spec
gold-update workflow
release notes
migration notes
```

A normal run MUST NOT update gold automatically.

A normalization change must not erase meaningful GF output.

---

# 42. Changing run-directory layout

Required coordinated review:

```text
RunPaths
all stage writers
all report writers
manifest writer
diff loader
cleanup and retention
GUI artifact openers
tests and fixtures
PERSISTED_SCHEMA_LOCK.md
migration guide
```

No component may independently choose a new filename.

---

# 43. Tests layout

Recommended final test structure:

```text
tests/
├── contracts/
│   ├── test_interfile_contracts.py
│   ├── test_schema_contracts.py
│   ├── test_gf_compile_contract.py
│   ├── test_scenario_contract.py
│   ├── test_process_contract.py
│   ├── test_report_contracts.py
│   └── test_project_contracts.py
│
├── fixtures/
│   ├── gf/
│   ├── diagnostics/
│   ├── summaries/
│   ├── scenarios/
│   ├── gold/
│   └── projects/
│
├── integration/
│   ├── test_real_gf_compile.py
│   ├── test_real_gf_scenarios.py
│   ├── test_pgf_build.py
│   └── test_end_to_end.py
│
├── test_bootstrap.py
├── test_models.py
├── test_file_selector.py
├── test_scanner.py
├── test_classifier.py
├── test_diff.py
├── test_reports.py
├── test_state.py
├── test_cli.py
├── test_gui.py
└── test_smoke.py
```

Exact file grouping may remain compact while the suite is small.

The ownership categories are more important than creating every file immediately.

---

# 44. Unit versus integration tests

## Unit tests

Should use:

```text
temporary directories
fake process results
fake executables
small fixtures
deterministic inputs
```

Unit tests MUST NOT depend on a developer-global GF installation.

## Integration tests

May require:

```text
real GF executable
compatible RGL
small fixture grammar
platform-specific process behavior
```

They should be marked separately.

## Contract tests

Verify boundaries rather than algorithms.

Examples:

```text
CLI and GUI produce equivalent RunConfig
report modules do not import compiler
RunPaths owns artifact locations
summary writer matches schema
normal run does not modify gold
project config matches loader fields
public symbols in lock exist
```

---

# 45. Development command map

Install development environment:

```text
python -m pip install -e ".[dev]"
```

Run tests:

```text
python -m pytest
```

Run one module:

```text
python -m pytest tests/test_classifier.py
```

Run one test:

```text
python -m pytest tests/test_classifier.py::test_name
```

Lint:

```text
python -m ruff check .
```

Type check:

```text
python -m mypy app
```

Compile Python sources:

```text
python -m compileall app tests
```

CLI help:

```text
python -m app.main_cli --help
```

GUI diagnostic startup:

```text
python -m app.main_gui
```

Detailed setup:

```text
docs/development/DEVELOPMENT_SETUP.md
```

---

# 46. Navigation by task

## “Where are defaults defined?”

```text
app/config.py
```

## “Where is project.toml loaded?”

```text
app/bootstrap.py or its dedicated loader called by bootstrap
```

## “Where is RunConfig created?”

```text
app/bootstrap.py
```

## “Where are run paths created?”

```text
app/bootstrap.py
RunPaths in app/models.py
```

## “Where are source files selected?”

```text
app/audit/file_selector.py
```

## “Where are scan rules?”

```text
app/audit/scanner.py
```

## “Where are GF compile arguments built?”

```text
app/audit/compiler.py
```

## “Where are subprocesses launched?”

```text
app/utils/process_utils.py
```

## “Where are GF diagnostics normalized?”

```text
app/audit/diagnostics.py
low-level helpers in app/utils/gf_utils.py
```

## “Where is direct/downstream decided?”

```text
app/audit/classifier.py
```

## “Where are scenarios executed?”

```text
app/audit/scenario_runner.py
```

## “Where are results aggregated?”

```text
app/audit/result_model.py
```

## “Where is the run coordinated?”

```text
app/audit/audit_core.py
```

## “Where is summary.json written?”

```text
app/reports/report_json.py
```

## “Where is AI_READY.md written?”

```text
app/reports/report_ai_ready.py
```

## “Where is application state persisted?”

```text
app/state.py
```

## “Where is active language identity defined?”

```text
project/project.toml
```

## “Where are GF module contracts defined?”

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

---

# 47. Common debugging routes

## Configuration differs between CLI and GUI

Inspect:

```text
main_cli.py
main_window.py
bootstrap.py
RunConfig equality
state fallback
```

## Wrong files selected

Inspect:

```text
project.toml sources
bootstrap resolution
file_selector.py
FILE_SELECTION.md
```

## GF command is wrong

Inspect:

```text
RunConfig executable and path
compiler.py
process_utils.py
GF_COMPILATION.md
EXTERNAL_TOOL_CONTRACT_LOCK.md
```

## Error classified incorrectly

Inspect:

```text
raw stdout/stderr
diagnostics.py
normalized references
classifier.py
ERROR_CLASSIFICATION.md
```

## Report disagrees with JSON

Inspect:

```text
RunResult
report_json.py
affected report writer
schema lock
```

Do not fix by parsing one report from another.

## Scenario reports success incorrectly

Inspect:

```text
scenario process result
required markers
normalization
assertions
gold comparison
ScenarioResult
```

Zero exit is insufficient.

## Old active-language names appear

Inspect:

```text
project.toml
project source
project scenarios
project gold
project docs
framework fixtures
template files
state migration
```

Framework production code must be language-neutral.

---

# 48. Anti-patterns

Do not introduce:

```text
a second RunConfig builder
a second path normalizer
report-time GF execution
GUI-only audit behavior
language-specific framework defaults
shell command strings from project text
dynamic result attributes
report parsing as data exchange
silent gold updates
global mutable run state
shared cross-run artifact cache without a contract
one generic “status” field for every dimension
one giant audit_core implementation containing all algorithms
one class per trivial option
a workflow engine for a linear pipeline
a plugin system without multiple real implementations
```

Complexity is justified only when it owns a stable, independently testable responsibility.

---

# 49. Refactoring rules

A safe internal refactor:

- preserves public symbols;
- preserves model meaning;
- preserves artifact paths;
- preserves schemas;
- preserves status semantics;
- preserves deterministic output;
- preserves tests;
- does not alter project behavior.

A contract refactor requires coordinated migration.

Before moving a function:

```text
search all imports
identify lock contract
review public/private status
move tests
update owner documentation
remove old duplicate implementation
```

Do not leave forwarding wrappers indefinitely unless they are documented compatibility adapters.

---

# 50. Current-to-final migration priorities

Recommended implementation order:

```text
1. rename package and command identity to GF Wordbench
2. finalize canonical configuration and project loader
3. normalize quick/checkpoint/release/diagnostic modes
4. finalize shared enums and result models
5. separate diagnostic normalization from classification
6. implement ScenarioResult
7. implement scenario_runner.py
8. implement gold comparison
9. implement PGF release build
10. implement manifest writer and verifier
11. migrate persisted schemas
12. add contract tests
13. remove legacy import fallbacks
14. retire gf-audit names after compatibility window
```

This order reduces rework because configuration and models are upstream of stages and reports.

---

# 51. Change-impact matrix

| Change | Primary owner | Required secondary review |
|---|---|---|
| Default timeout | `config.py` | bootstrap, CLI/GUI, tests, docs |
| Project field | project loader/schema | bootstrap, template, tests, migration |
| RunConfig field | `models.py`/bootstrap | CLI, GUI, stages, serialization |
| RunPaths field | `models.py`/bootstrap | writer, readers, manifest, tests |
| Scan rule | `scanner.py` | fixtures, scan docs |
| GF flag | `compiler.py` | external lock, version policy, integration tests |
| Scenario marker | `scenario_runner.py` | `.gfs`, gold, schema, docs |
| Error kind | diagnostics/models | classifier, JSON, reports, tests |
| Diagnostic class | classifier/models | reports, schemas, tests |
| Report JSON field | `report_json.py` | schema, readers, diff, migrations |
| Markdown section | report owner | tests, consumers if parsed |
| Gold normalization | scenario runner | all affected gold, release review |
| Artifact filename | `RunPaths` owner | writer, readers, manifest, schemas |
| GUI field | GUI/bootstrap | state, CLI equivalence, tests |
| CLI option | CLI/bootstrap | GUI equivalence, reference docs |
| Project template | `templates/project/` | initializer, project docs, tests |

---

# 52. Documentation ownership

Framework behavior is documented under:

```text
docs/
```

Active-language behavior is documented under:

```text
project/docs/
```

Template guidance is documented under:

```text
templates/project/docs/
```

Rules:

- do not duplicate one normative rule across several documents;
- use cross-references;
- assign one authoritative document;
- update documentation in the same change as code;
- mark examples as examples;
- do not treat future plans as implemented behavior without status.

---

# 53. Required review checklist

For every non-trivial code change:

```text
[ ] responsibility owner identified
[ ] contract ID identified
[ ] provider reviewed
[ ] direct consumers reviewed
[ ] downstream consumers reviewed
[ ] shared models reviewed
[ ] path ownership reviewed
[ ] status and error semantics reviewed
[ ] raw evidence preservation reviewed
[ ] persisted schema impact reviewed
[ ] project boundary reviewed
[ ] CLI and GUI equivalence reviewed
[ ] unit tests updated
[ ] contract tests updated
[ ] integration tests updated when needed
[ ] fixtures and gold reviewed intentionally
[ ] lock files updated
[ ] documentation updated
[ ] migration or deprecation recorded
```

---

# 54. Codebase acceptance criteria

The codebase architecture is healthy when:

```text
[ ] one owner exists for every major responsibility
[ ] CLI and GUI use one configuration path
[ ] RunConfig is sufficient for non-interactive execution
[ ] RunPaths owns generated locations
[ ] audit_core orchestrates without absorbing stage algorithms
[ ] validation stages return typed evidence
[ ] process execution is centralized
[ ] raw stdout and stderr are preserved
[ ] diagnostic normalization is centralized
[ ] causal classification is separate
[ ] reports consume RunResult only
[ ] reports never execute GF
[ ] project identity comes from project.toml
[ ] framework production code is language-neutral
[ ] scenario execution uses native .gfs
[ ] normal runs never modify gold
[ ] persisted schemas are versioned
[ ] tests do not require hidden developer environment
[ ] dependency directions remain acyclic
[ ] contract changes update every consumer
```

---

# 55. Cross-references

| Topic | Document |
|---|---|
| Architecture | `docs/architecture/ARCHITECTURE_OVERVIEW.md` |
| Components | `docs/architecture/COMPONENT_MAP.md` |
| Execution flow | `docs/architecture/EXECUTION_FLOW.md` |
| Dependency rules | `docs/architecture/DEPENDENCY_RULES.md` |
| Framework contracts | `docs/INTERFILE_CONTRACT_LOCK.md` |
| External tools | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted schemas | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Terminology | `docs/GLOSSARY.md` |
| Installation | `docs/usage/INSTALLATION.md` |
| Development setup | `docs/development/DEVELOPMENT_SETUP.md` |
| Coding standards | `docs/development/CODING_STANDARDS.md` |
| Testing | `docs/development/TESTING_GF_WORDBENCH.md` |
| Extension process | `docs/development/EXTENDING_GF_WORDBENCH.md` |
| Backward compatibility | `docs/development/BACKWARD_COMPATIBILITY.md` |
| Debugging | `docs/development/DEBUGGING_THE_FRAMEWORK.md` |
| File selection | `docs/validation/FILE_SELECTION.md` |
| GF compilation | `docs/gf/GF_COMPILATION.md` |
| Error classification | `docs/diagnostics/ERROR_CLASSIFICATION.md` |
| Project schema | `docs/configuration/PROJECT_TOML_REFERENCE.md` |
| Active project contracts | `project/docs/INTERFILE_CONTRACT_LOCK.md` |

---

# 56. Final rule

> Follow ownership before implementation.

When a change appears to require edits in many unrelated places, first identify the missing or duplicated owner.

When a change crosses a file boundary, treat every provider, consumer, schema, test, artifact, and document as one coordinated change unit.
