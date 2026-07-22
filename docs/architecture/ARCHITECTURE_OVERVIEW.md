# GF Wordbench — Architecture Overview

**Document ID:** `GF-WB-ARCH-OVERVIEW`  
**Status:** Normative architectural overview  
**Applies to:** GF Wordbench framework, active language project, project template, and generated run artifacts  
**Owner:** GF Wordbench maintainers  
**Architecture version:** `1.0`  
**Target product state:** Final architecture  
**Last reviewed:** 2026-07-22  

---

## 1. Purpose

This document defines the final high-level architecture of GF Wordbench.

It explains:

- what the system is;
- what the system is not;
- where each responsibility belongs;
- how the main components collaborate;
- how GF is invoked;
- how validation results and artifacts flow through the system;
- how one active language project is separated from the permanent framework;
- which architectural constraints prevent drift.

This document is an overview. Detailed contracts remain authoritative in:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

When this overview and a contract lock appear to disagree, the contract lock governs the affected boundary.

---

## 2. Product definition

GF Wordbench is a local development, validation, diagnostic, and release workbench for one active Grammatical Framework language project.

A GF Wordbench repository contains:

```text
one permanent Python framework
one active GF language project
one reusable clean project template
zero or more generated validation runs
```

The intended workflow is:

```text
clone GF Wordbench
        ↓
initialize or migrate one language project
        ↓
develop and validate the language
        ↓
produce evidence and release artifacts
        ↓
clone or reset another copy for another language
```

GF Wordbench does not manage several active languages concurrently inside one project configuration.

A multi-language GF grammar may still be compiled when the active project itself intentionally defines such a grammar. The architectural rule concerns project ownership and configuration, not GF’s language capabilities.

---

## 3. Architectural goals

The final architecture is designed to achieve the following goals.

### 3.1 Correctness

- Use GF as the authority for GF semantics.
- Preserve raw tool evidence.
- Separate execution failures from language validation failures.
- Make validation results deterministic and reviewable.
- Require explicit release criteria.

### 3.2 Reusability

- Keep the framework independent of any active language.
- Store language-specific facts in `project/`.
- provide a clean `templates/project/` source for initialization.
- Make project replacement possible without rewriting framework code.

### 3.3 Traceability

- Record the resolved configuration used for each run.
- Record the executable, arguments, working directory, timeout, and outputs.
- Link normalized diagnostics to raw evidence.
- Catalog generated artifacts in a manifest.
- Keep previous-run comparison explicit.

### 3.4 Anti-drift

- Give each responsibility and artifact one owner.
- Use typed shared models at component boundaries.
- Version persisted schemas.
- Lock provider-consumer relationships.
- Prohibit duplicated path construction and duplicated execution logic.

### 3.5 Maintainability

- Prefer cohesive modules with narrow responsibilities.
- Keep CLI and GUI thin.
- Keep reports passive.
- Keep process handling centralized.
- Add complexity only when it corresponds to a stable responsibility.

### 3.6 Portability

- Support Windows as a first-class platform.
- Avoid dependence on shell-specific behavior.
- Normalize persisted paths.
- Keep local environment paths separate from portable project configuration.
- Avoid mandatory network services.

---

## 4. Non-goals

The final architecture does not include:

- a replacement GF parser;
- a replacement GF type checker;
- a replacement GF module resolver;
- a replacement GF runtime;
- a competing PGF implementation;
- a general-purpose integrated development environment;
- a hosted validation service;
- a mandatory database;
- a mandatory web server;
- a package marketplace;
- an unrestricted runtime plugin system;
- simultaneous management of unrelated active language projects;
- automatic linguistic design decisions;
- automatic acceptance of changed gold outputs;
- report generators that rerun validation stages.

These capabilities may exist in external tools or future companion products, but they are outside the GF Wordbench core.

---

## 5. System context

```text
┌─────────────────────────────────────────────────────────────┐
│                         User or CI                          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                     CLI or desktop GUI
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                      GF Wordbench                           │
│                                                             │
│  configuration → orchestration → validation → reporting    │
└───────────────┬───────────────────────────────┬─────────────┘
                │                               │
         active project                    run artifacts
                │                               │
┌───────────────▼──────────────┐   ┌────────────▼─────────────┐
│ GF modules, .gfs, inputs,    │   │ raw logs, summaries,     │
│ gold files, project docs     │   │ manifests, .gfo, .pgf    │
└───────────────┬──────────────┘   └──────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│         Grammatical Framework executable and RGL           │
└─────────────────────────────────────────────────────────────┘
```

External actors are:

- the user;
- CI or automation;
- the GF executable;
- the GF Resource Grammar Library;
- the local filesystem;
- optional explicitly contracted tools.

The core architecture does not require remote services.

---

## 6. Authority boundaries

### 6.1 GF is authoritative for

- GF syntax;
- GF type checking;
- module loading;
- GF dependency resolution;
- `.gf` to `.gfo` compilation;
- PGF construction;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- native GF diagnostics.

### 6.2 GF Wordbench is authoritative for

- configuration loading and validation;
- executable selection;
- command construction;
- process launch;
- working-directory selection;
- environment preparation;
- timeouts and cancellation;
- stdout and stderr capture;
- static source checks;
- scenario coordination;
- output normalization;
- assertion and gold comparison;
- failure classification;
- run history;
- artifact collection;
- report production;
- schema migration;
- release gates.

### 6.3 Active language project is authoritative for

- project identity;
- source layout;
- entrypoints;
- checkpoints;
- required and optional scenarios;
- expected gold output;
- linguistic architecture;
- category and lincat contracts;
- morphology and syntax design;
- release criteria;
- known language-specific limitations.

### 6.4 Framework maintainers are authoritative for

- framework architecture;
- shared models;
- process semantics;
- persisted schemas;
- public command behavior;
- diagnostic vocabulary;
- artifact layout;
- compatibility policy;
- framework release policy.

---

## 7. Repository partitions

The repository is divided into four architectural partitions.

```text
GF_Wordbench/
├── app/                 permanent Python framework
├── docs/                permanent framework documentation
├── tests/               framework and contract tests
├── project/             one active language project
├── templates/project/   clean reusable project template
└── <output-root>/       generated run directories
```

### 7.1 Permanent framework

The permanent framework contains:

- application assembly;
- configuration and schema loading;
- orchestration;
- static scanning;
- GF process execution;
- scenario execution;
- diagnostics;
- result models;
- report generation;
- state handling;
- CLI and GUI interfaces.

It must not contain active-language source facts.

### 7.2 Active language project

The active project contains:

```text
project/
├── project.toml
├── README.md
├── docs/
├── validation/
│   ├── scenarios/
│   ├── gold/
│   └── inputs/
└── language source tree or declared source references
```

It contains exactly one project identity and one coherent validation policy.

### 7.3 Project template

`templates/project/` mirrors the active-project structure but contains:

- generic placeholders;
- generic instructions;
- no active-language decisions;
- no copied local paths;
- no stale gold expectations;
- no generated artifacts.

### 7.4 Generated runs

Run directories contain evidence and derived reports.

They are outputs, not source configuration.

A run must be reproducible from:

- the project revision;
- the resolved run configuration;
- the GF version;
- the captured command contracts;
- the scenario and gold revisions.

---

## 8. Layered architecture

GF Wordbench uses the following logical layers.

```text
1. Presentation
2. Application assembly
3. Configuration and project loading
4. Orchestration
5. Validation stages
6. External process integration
7. Diagnostics and classification
8. Shared domain models
9. Reporting and persistence
10. Filesystem artifacts
```

Dependencies flow downward or laterally through explicit contracts.

A lower layer must not depend on a presentation layer.

---

## 9. Presentation layer

### 9.1 Command-line interface

Canonical owner:

```text
app/main_cli.py
```

Responsibilities:

- define CLI syntax;
- validate syntactic argument constraints;
- request application and run configuration;
- invoke the application orchestrator;
- render concise terminal output;
- convert final outcomes into documented process exit codes.

The CLI must not:

- implement audit stages;
- launch GF directly;
- parse GF diagnostics directly;
- construct report files;
- duplicate project-loading rules;
- invent its own artifact paths.

### 9.2 Desktop GUI

Canonical owners:

```text
app/main_gui.py
app/gui/
app/state.py
```

Responsibilities:

- collect user choices;
- display validated configuration;
- start a run through the same application boundary as the CLI;
- display progress and completed results;
- persist disposable local preferences;
- link to generated artifacts.

The GUI must not:

- launch GF from widgets;
- own project semantics;
- mutate gold files during a normal run;
- derive results by scraping human reports;
- hold a second implementation of validation logic.

### 9.3 Shared interface rule

CLI and GUI are alternative front ends over the same application services.

Equivalent resolved inputs must produce equivalent validation behavior.

Interface differences may affect presentation, not audit semantics.

---

## 10. Application assembly layer

Canonical owner:

```text
app/bootstrap.py
```

Related owners:

```text
app/config.py
app/project_config.py
```

Responsibilities:

- load framework defaults;
- load and validate `project/project.toml`;
- apply local environment configuration;
- apply explicit CLI or GUI overrides;
- construct immutable or controlled run configuration;
- construct run paths;
- select required services;
- reject invalid combinations before execution.

Bootstrap is a composition boundary.

It must not:

- perform validation stages;
- contain language-specific defaults;
- generate reports;
- call GF directly;
- silently bypass release requirements.

---

## 11. Configuration model

Configuration is divided by ownership.

### 11.1 Framework defaults

Owned by:

```text
app/config.py
```

Examples:

- application name;
- package version;
- default timeout policy;
- supported schema versions;
- default output conventions;
- framework-wide limits.

Framework defaults must not name an active language or active-language module.

### 11.2 Project configuration

Owned by:

```text
project/project.toml
```

Loaded by:

```text
app/project_config.py
```

Examples:

- project ID and language code;
- source directory;
- source inclusion rules;
- GF path parts;
- entrypoints;
- checkpoints;
- required scenarios;
- optional scenarios;
- release requirements.

### 11.3 Local application state

Owned by:

```text
app/state.py
.gf_wordbench_state.json
```

Examples:

- local project root;
- local RGL root;
- local GF executable;
- output root;
- last selected mode;
- display preferences;
- previous run pointer.

Local state is disposable.

Deleting it must not alter the language project.

### 11.4 Explicit run overrides

CLI or GUI values may override documented local defaults.

They must not silently disable mandatory release gates.

### 11.5 Configuration precedence

The final resolved configuration follows:

```text
framework defaults
        ↓
project configuration
        ↓
local environment/state
        ↓
explicit invocation overrides
        ↓
cross-field validation
        ↓
resolved RunConfig
```

The source of each significant resolved value should remain inspectable.

---

## 12. Shared domain models

Canonical owner:

```text
app/models.py
```

Supporting construction logic:

```text
app/audit/result_model.py
```

The final model set includes, at minimum:

```text
AppConfig
ProjectConfig
RunConfig
RunPaths
ProcessRequest
ProcessResult
ScanCounts
SourceFingerprint
CompileSummary
FileResult
ScenarioResult
DiffEntry
ArtifactRecord
RunResult
```

### 12.1 Model responsibilities

Shared models:

- define stable component boundaries;
- make status and path semantics explicit;
- prevent consumers from depending on private dictionaries;
- centralize serialization meaning;
- provide safe defaults for optional fields;
- distinguish runtime-only fields from persisted fields.

### 12.2 No dynamic contract rule

Consumers must not add undocumented attributes to shared result objects.

A new cross-component field requires:

- model update;
- producer update;
- consumer review;
- serialization review;
- tests;
- contract update when externally visible.

### 12.3 Internal versus persisted models

Internal Python models may use:

- `Path`;
- enums;
- dataclasses;
- richer process objects.

Persisted schemas use canonical serializable forms defined in `PERSISTED_SCHEMA_LOCK.md`.

Serialization occurs at designated boundaries, not opportunistically throughout the codebase.

---

## 13. Orchestration layer

Canonical owner:

```text
app/audit/audit_core.py
```

The orchestrator coordinates the run but does not absorb stage implementation.

Responsibilities:

1. validate the resolved run configuration;
2. create the run directory;
3. initialize logging and run metadata;
4. probe GF when required;
5. select files, checkpoints, entrypoints, and scenarios;
6. invoke validation stages in mode-defined order;
7. collect stage results;
8. classify causal relationships;
9. compare with the previous compatible run;
10. evaluate release gates;
11. finalize the run result;
12. invoke report writers;
13. invoke manifest creation;
14. return one final `RunResult`.

The orchestrator must not:

- implement GF command details;
- scan source text directly;
- parse GF diagnostics directly;
- render report prose;
- write gold files;
- hide stage failures;
- continue past an unsafe configuration failure.

---

## 14. Validation stage architecture

Validation is a pipeline of independent stages coordinated by the orchestrator.

```text
configuration validation
        ↓
tool/version probe
        ↓
file discovery
        ↓
static scanning
        ↓
module compilation
        ↓
entrypoint / PGF build
        ↓
scenario execution
        ↓
normalization and assertions
        ↓
gold comparison
        ↓
classification
        ↓
previous-run comparison
        ↓
release-gate evaluation
        ↓
reports and manifest
```

Not every mode executes every stage.

### 14.1 Stage contract

Each stage must define:

- inputs;
- outputs;
- owner;
- allowed side effects;
- status behavior;
- raw evidence;
- timeout policy when process-backed;
- deterministic ordering;
- failure-containment behavior;
- tests.

A stage must not modify another stage’s result after ownership has transferred, except through an explicit aggregation or classification step.

---

## 15. File discovery

Canonical owner:

```text
app/audit/file_selector.py
```

Responsibilities:

- resolve the configured source directory;
- enumerate candidate `.gf` files;
- apply inclusion and exclusion rules;
- enforce maximum-file constraints;
- select target files for `quick`;
- select checkpoints for `checkpoint`;
- select complete project scope for `diagnostic` or `release`;
- return deterministic project-relative paths.

File discovery must not:

- parse GF modules;
- infer import graphs from compiler prose;
- launch GF;
- classify failures;
- write reports.

---

## 16. Static scanning

Canonical owner:

```text
app/audit/scanner.py
```

Responsibilities:

- read GF source safely;
- distinguish code from comments and strings;
- detect documented suspicious source patterns;
- count and describe findings;
- preserve a scan log;
- return structured scan results.

Static scanning is advisory or policy-driven evidence.

It is not a substitute for GF compilation.

A scanner finding must not be described as a GF type error unless GF independently reports such an error.

Language-specific lint rules must be declared by project policy or implemented through an explicit extension boundary.

---

## 17. External process integration

Canonical owner:

```text
app/utils/process_runner.py
```

or the final designated process utility.

Supporting command owners:

```text
app/audit/compiler.py
app/audit/pgf_builder.py
app/audit/scenario_runner.py
```

### 17.1 Process runner responsibilities

The process runner owns:

- shell-free process launch;
- ordered argument execution;
- explicit working directory;
- controlled environment overlay;
- stdin handling;
- timeout enforcement;
- cancellation handling;
- child-process termination policy;
- separate stdout and stderr capture;
- duration and exit-code capture;
- launch-error capture;
- output-size policy;
- raw process result creation.

### 17.2 Command builder responsibilities

A command-owning stage owns:

- operation-specific GF arguments;
- expected inputs;
- expected artifacts;
- success criteria beyond the exit code;
- operation timeout class;
- interpretation handoff.

### 17.3 No duplicate process logic

CLI, GUI, reports, classifiers, and project loaders must not launch GF.

All GF execution passes through the process boundary.

---

## 18. GF compilation

Canonical owner:

```text
app/audit/compiler.py
```

Responsibilities:

- build the GF compilation request;
- resolve declared GF paths through the shared path resolver;
- invoke the process runner;
- verify required `.gfo` artifacts when applicable;
- preserve raw stdout and stderr;
- produce a `CompileSummary`;
- hand diagnostics to the normalization layer.

Compilation status must consider:

- launch success;
- timeout;
- exit code;
- GF diagnostics;
- required artifact existence;
- contract completeness.

A zero exit code alone is not sufficient when a required artifact is missing.

---

## 19. PGF construction

Canonical owner:

```text
app/audit/pgf_builder.py
```

Responsibilities:

- select configured release entrypoints;
- build the documented GF command;
- invoke the process runner;
- verify the expected `.pgf`;
- catalog the artifact;
- return a process-backed build result.

PGF construction is required only when the active project and validation mode require it.

The PGF builder must not:

- decide language architecture;
- choose undocumented entrypoints;
- accept an absent PGF as success;
- rewrite PGF contents.

---

## 20. Scenario execution

Canonical owner:

```text
app/audit/scenario_runner.py
```

Scenario sources:

```text
project/validation/scenarios/*.gfs
```

Related assets:

```text
project/validation/inputs/
project/validation/gold/
```

Responsibilities:

- load the configured scenario registry;
- validate scenario paths and identifiers;
- invoke GF with the `.gfs` script;
- enforce scenario timeout and output limits;
- capture stdout and stderr separately;
- verify required markers and sections;
- normalize stable output;
- compare with gold when configured;
- catalog scenario artifacts;
- return one `ScenarioResult` per scenario.

The scenario runner must not implement a second GF shell.

Native `.gfs` scripts remain the execution language.

---

## 21. Output normalization

Canonical owner:

```text
app/audit/normalization.py
```

or the final designated normalization component.

Responsibilities:

- normalize CRLF to LF;
- remove ANSI control sequences;
- replace explicitly unstable environment paths with stable tokens;
- remove explicitly declared unstable timing values;
- preserve linguistically meaningful Unicode and punctuation;
- preserve trees, strings, counts, missing-function lists, and morphology output;
- write a versioned normalized output;
- retain a reference to raw evidence.

Normalization must be:

- deterministic;
- versioned;
- tested;
- narrow;
- reversible only where the contract requires it.

A normalization change that affects gold comparison is a contract change.

---

## 22. Diagnostics and classification

Diagnostics are divided into two architectural responsibilities.

### 22.1 Diagnostic normalization

Canonical owner:

```text
app/audit/diagnostics.py
```

Responsibilities:

- inspect stdout and stderr together;
- normalize known GF diagnostic structures;
- identify error kinds;
- preserve source location and original evidence;
- distinguish launch, timeout, tool, contract, artifact, and configuration failures.

It must not decide upstream versus downstream causality.

### 22.2 Causal classification

Canonical owner:

```text
app/audit/classifier.py
```

Responsibilities:

- classify results as direct, downstream, ambiguous, noise, skipped, or okay;
- identify known blockers;
- preserve uncertainty;
- avoid turning heuristic relationships into unsupported certainty.

### 22.3 Orthogonal result dimensions

The architecture keeps four dimensions distinct.

```text
validation_status
execution_state
error_kind
diagnostic_class
```

Recommended final meanings:

```text
validation_status:
  OK | FAIL | ERROR | SKIPPED

execution_state:
  completed | timed_out | cancelled | launch_failed

error_kind:
  OK | OTHER | TYPE | SYNTAX | INTERNAL | TIMEOUT |
  SCRIPT | CONFIG | IO | TOOL | CONTRACT | ARTIFACT |
  NORMALIZATION | GOLD

diagnostic_class:
  ok | direct | downstream | ambiguous | noise | skipped
```

A process layer does not assign direct or downstream causality.

A classifier does not rewrite raw process evidence.

---

## 23. Fingerprints and regression comparison

### 23.1 Source fingerprints

Canonical owner:

```text
app/audit/fingerprint.py
```

Responsibilities:

- compute deterministic source fingerprints;
- use SHA-256 for canonical output;
- record size and modification metadata;
- support change detection without replacing version control.

### 23.2 Previous-run comparison

Canonical owner:

```text
app/audit/diff.py
```

Responsibilities:

- locate a previous compatible summary;
- load it through the schema reader;
- compare stable subject identities;
- classify changes as unchanged, improved, regressed, new, or removed;
- remain deterministic;
- tolerate absence of a previous run.

The diff component must not compare Markdown prose.

`summary.json` is the machine source of truth.

---

## 24. Validation modes

GF Wordbench defines four final modes.

### 24.1 Quick

Purpose:

- validate one selected file or a tightly bounded target;
- provide fast developer feedback.

Expected scope:

- configuration validation;
- relevant file discovery;
- static scan;
- targeted compile;
- limited diagnostics;
- concise reports.

### 24.2 Checkpoint

Purpose:

- validate a declared architectural layer.

Expected scope:

- configured checkpoint modules;
- their required supporting stages;
- selected required scenarios;
- regression comparison.

### 24.3 Diagnostic

Purpose:

- collect broad evidence for investigation.

Expected scope:

- all selected source files;
- static scans;
- compilation;
- extended diagnostics;
- optional diagnostic scenarios;
- detailed reports.

Diagnostic mode may continue after isolated language failures when evidence collection remains safe.

### 24.4 Release

Purpose:

- prove all project-defined release criteria.

Expected scope:

- clean configuration;
- required source validation;
- entrypoint validation;
- required PGF build;
- all required scenarios;
- gold comparison;
- required artifact verification;
- manifest integrity;
- no unresolved release blockers.

Release mode is strict.

Mandatory release requirements cannot be silently disabled by state or presentation defaults.

---

## 25. Run result aggregation

`RunResult` is the authoritative in-memory aggregate of a completed or terminal run.

It includes:

- resolved configuration;
- run paths;
- timing;
- GF version;
- file results;
- scenario results;
- PGF build results when applicable;
- totals;
- diagnostic groups;
- top errors;
- diff entries;
- release-gate outcomes;
- artifact records;
- framework errors;
- overall status.

### 25.1 Overall status

```text
ERROR
```

means GF Wordbench could not execute or interpret a required operation.

```text
FAIL
```

means required validation executed but did not meet its criterion.

```text
OK
```

means every required criterion passed.

`SKIPPED` applies to individual operations, not normally to a finalized required release run.

### 25.2 Partial evidence

A terminal framework error must not erase evidence already captured.

The run result should preserve completed-stage results and identify the stage that prevented completion.

---

## 26. Reporting architecture

Canonical report owners:

```text
app/reports/report_json.py
app/reports/report_md.py
app/reports/report_ai_ready.py
app/reports/report_logs.py
app/reports/report_details.py
app/reports/report_manifest.py
```

### 26.1 Report rules

Reports:

- consume completed results;
- do not rerun validation;
- do not launch GF;
- do not silently modify raw evidence;
- use owned paths from `RunPaths`;
- preserve deterministic ordering;
- fail independently where possible.

### 26.2 Machine summary

```text
summary.json
```

is the primary persisted run record.

It supports:

- automation;
- GUI reload;
- previous-run comparison;
- migration;
- report verification;
- historical analysis.

### 26.3 Human summary

```text
summary.md
```

provides a concise reviewable explanation.

It is not a machine schema.

### 26.4 AI handoff

```text
AI_READY.md
```

provides:

- bounded evidence;
- direct/downstream separation;
- failing files and scenarios;
- artifact references;
- no second execution.

### 26.5 Manifest

```text
manifest.json
```

catalogs final artifacts with:

- role;
- path;
- size;
- SHA-256;
- owner;
- required status.

---

## 27. Run artifact architecture

Canonical run layout:

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

### 27.1 Artifact classes

#### Raw evidence

Examples:

- stdout;
- stderr;
- scan logs;
- command records;
- process metadata.

Raw evidence is immutable after capture.

#### Tool-generated artifacts

Examples:

- `.gfo`;
- `.pgf`;
- GF-generated exports.

GF creates them. GF Wordbench catalogs or copies them without changing their meaning.

#### Derived artifacts

Examples:

- normalized scenario output;
- gold diff;
- summary;
- diagnostic aggregation.

Derived artifacts retain references to source evidence.

### 27.2 Ownership rule

Every artifact has one writer.

Readers do not rewrite artifacts owned by another component.

---

## 28. Persistence architecture

Canonical persisted schemas include:

```text
gf-wordbench.project/1.0
gf-wordbench.app-state/1.0
gf-wordbench.run-summary/1.0
gf-wordbench.artifact-manifest/1.0
gf-wordbench.scenario-output/1.0
gf-wordbench.scenario-gold/1.0
```

Persistence rules include:

- explicit schema identity;
- explicit schema version;
- UTF-8;
- deterministic ordering;
- portable project-relative and run-relative paths;
- explicit UTC timestamps;
- atomic writes;
- tested migration;
- no secret persistence.

No new unversioned machine-readable format may be introduced.

---

## 29. Path architecture

Paths belong to one of three classes.

### 29.1 Project-owned paths

Examples:

```text
lib/src/french/GrammarFre.gf
validation/scenarios/parse.gfs
```

Rules:

- relative to the project root;
- `/` separators in canonical persistence;
- no path escape;
- portable across clones.

### 29.2 Run-owned paths

Examples:

```text
raw/compile/GrammarFre.stdout.txt
artifacts/pgf/Grammar.pgf
```

Rules:

- relative to the run directory in summaries and manifests;
- owned by `RunPaths`;
- never reconstructed through duplicated filename logic.

### 29.3 Environment paths

Examples:

```text
C:/tools/gf/gf.exe
C:/work/gf-rgl/src
```

Rules:

- may be absolute;
- resolved before execution;
- recorded for traceability;
- not stored as portable project facts.

---

## 30. Dependency rules

### 30.1 Allowed high-level direction

```text
CLI ─┐
     ├→ bootstrap → orchestrator → stages → process runner
GUI ─┘                     │            │
                           │            └→ GF
                           ↓
                         models
                           ↓
                    reports/persistence
```

### 30.2 Prohibited directions

The following are prohibited:

- models importing CLI or GUI;
- process utilities importing reports;
- reports importing CLI or GUI;
- reports launching validation;
- GUI widgets importing compiler internals;
- scanner importing report writers;
- classifier launching external tools;
- project loader importing active-language Python code;
- framework defaults importing project-specific constants;
- active project source mutating framework files;
- template files depending on active project content.

### 30.3 Shared utility rule

A utility module is permitted only when:

- its responsibility is cohesive;
- it has more than one legitimate consumer;
- it does not become a hidden service locator;
- it does not own business policy that belongs to a domain component.

---

## 31. Failure containment

The architecture separates failures by layer.

### 31.1 Configuration failure

Examples:

- missing project file;
- invalid schema;
- unresolved required path;
- duplicate scenario ID.

Normally terminal before validation begins.

### 31.2 Launch failure

The executable could not be started.

This is not a GF language failure.

### 31.3 Timeout or cancellation

The process did not complete under the execution contract.

This is not equivalent to a normal non-zero GF exit.

### 31.4 Tool-reported failure

GF ran and reported a failure.

Raw diagnostics remain authoritative evidence.

### 31.5 Contract or artifact failure

The process returned but required markers or artifacts are absent.

A zero exit code does not override this failure.

### 31.6 Validation failure

The operation executed correctly but the language project failed the required criterion.

### 31.7 Reporting failure

A report writer failed after evidence existed.

The run records the reporting error without erasing raw evidence or relabeling GF results.

---

## 32. Security and trust boundaries

GF Wordbench is a local developer tool, but it executes external processes and executable scenario scripts.

### 32.1 Untrusted inputs

Treat as untrusted:

- project paths;
- `.gfs` scenarios;
- validation input files;
- project configuration;
- external executable paths;
- legacy persisted files.

### 32.2 Process safety

Required controls:

- `shell=False` or equivalent by default;
- ordered arguments;
- explicit working directory;
- bounded timeout;
- bounded output policy;
- controlled environment overlay;
- child-process termination policy;
- separate stdout and stderr capture.

### 32.3 Filesystem safety

Required controls:

- path containment;
- atomic writes;
- no silent overwrite of source files;
- no normal-run gold updates;
- no artifact paths escaping the configured root;
- no symlink-based escape in strict operations.

### 32.4 Secret handling

Reports and persisted files must not include:

- tokens;
- passwords;
- private keys;
- cookies;
- complete environment dumps;
- secret command arguments.

### 32.5 Scenario execution

A `.gfs` file is executable input.

Operating-system escape or pipeline behavior must be prohibited by default unless an explicit policy and contract enable it.

---

## 33. Extension architecture

GF Wordbench supports controlled extension, not unrestricted plugins.

### 33.1 Supported extension points

- a new validation stage;
- a new static diagnostic rule;
- a new GF command capability;
- a new scenario assertion;
- a new report field;
- a new report format;
- a new schema minor version;
- a new optional external tool contract;
- a new project documentation specialization.

### 33.2 Extension requirements

An extension must define:

- owner;
- inputs;
- outputs;
- side effects;
- status behavior;
- configuration;
- persistence impact;
- tests;
- compatibility impact;
- documentation;
- contract updates.

### 33.3 When not to extend

Do not add a new component when an existing owner can absorb the behavior without:

- mixing responsibilities;
- creating a second implementation;
- changing its public contract incoherently;
- increasing coupling.

---

## 34. Testing architecture

Testing is organized by architectural boundary.

### 34.1 Unit tests

Cover:

- configuration validation;
- file selection;
- static scanning;
- command construction;
- diagnostic normalization;
- classification;
- fingerprints;
- comparison;
- serialization;
- report rendering.

### 34.2 Contract tests

Recommended location:

```text
tests/contracts/
```

Cover:

- provider-consumer interfaces;
- artifact ownership;
- dependency direction;
- path ownership;
- status vocabulary;
- no duplicate execution;
- CLI/GUI equivalence at the application boundary.

### 34.3 Schema tests

Recommended location:

```text
tests/schemas/
```

Cover:

- canonical round trips;
- required fields;
- version rejection;
- legacy migration;
- deterministic ordering;
- atomic-write behavior;
- path normalization.

### 34.4 Process integration tests

Cover:

- shell-free launch;
- stdout/stderr separation;
- timeout;
- cancellation;
- launch failure;
- non-zero exit;
- required artifact verification;
- encoding behavior.

### 34.5 GF integration tests

Cover, when GF is available:

- version probe;
- simple module compilation;
- checkpoint compilation;
- PGF creation;
- `.gfs` execution;
- marker detection;
- gold match and mismatch.

Tests must not depend silently on a developer’s global GF environment.

### 34.6 End-to-end tests

Cover:

```text
project fixture
  → resolved config
  → validation run
  → reports
  → manifest
  → reload and diff
```

---

## 35. Backward compatibility

The final architecture supports migration from the GF Audit baseline.

Legacy elements include:

```text
.gf_audit_state.json
unversioned summary.json
mode=file
mode=all
ai_brief_path
absolute artifact paths
SHA-1 short fingerprints
language defaults in app/config.py
```

Canonical replacements include:

```text
.gf_wordbench_state.json
versioned run summary
mode=quick
mode=diagnostic
artifacts.ai_ready
run-relative artifact paths
SHA-256 fingerprints
project/project.toml
```

Migration principles:

- read legacy;
- validate what can be validated;
- preserve the source;
- write canonical output separately;
- report ambiguous or lossy conversions;
- emit only canonical formats from new writers.

Compatibility code must remain isolated in loaders or migrators.

It must not spread legacy aliases through current domain logic.

---

## 36. Operational model

GF Wordbench runs as a local foreground application.

It does not require:

- a daemon;
- a queue;
- a remote scheduler;
- a database;
- a network service.

A run may be initiated by:

- CLI;
- GUI;
- CI;
- a documented local automation wrapper.

The process completes by returning:

- an exit code to CLI or automation;
- a final result to the GUI;
- persisted run artifacts.

Cancellation is cooperative through the application and process boundaries.

---

## 37. Release architecture

A framework release and a language-project release are related but distinct.

### 37.1 Framework release

Proves:

- package correctness;
- contract compliance;
- schema compatibility;
- supported GF compatibility;
- framework tests;
- documentation consistency.

### 37.2 Language-project release

Proves:

- project configuration validity;
- required module compilation;
- required PGF build;
- required scenario success;
- required gold matches;
- project release criteria;
- no unresolved blocking issues;
- complete evidence manifest.

A framework version does not imply that an active language project is releasable.

A language project release must record the GF Wordbench and GF versions used.

---

## 38. Architectural decision summary

| Decision | Final choice |
|---|---|
| Active project model | One active language project per repository copy |
| GF semantics | Delegated to native GF |
| Framework role | Orchestration, evidence, classification, comparison, reporting |
| Interfaces | Shared application boundary for CLI and GUI |
| Scenario format | Native `.gfs` |
| Regression expectations | Versioned normalized output and reviewed `.gold` |
| Machine result | Versioned `summary.json` |
| Artifact integrity | Versioned `manifest.json` with SHA-256 |
| Persistent project config | `project/project.toml` |
| Local preferences | `.gf_wordbench_state.json` |
| Process execution | Centralized, shell-free by default |
| Storage | Filesystem; no mandatory database |
| Extensibility | Controlled explicit extension points |
| Compatibility | Versioned schemas and tested migrations |
| Anti-drift | Interfile, external-tool, persisted-schema, and project locks |

---

## 39. Architecture invariants

The following invariants define the final architecture.

1. Exactly one active project configuration exists per GF Wordbench copy.
2. The permanent framework contains no active-language defaults.
3. GF remains authoritative for GF semantics.
4. CLI and GUI use the same application and orchestration boundaries.
5. External execution is centralized.
6. Every external process has an explicit executable, ordered arguments, working directory, and finite timeout.
7. Stdout and stderr are preserved separately.
8. Raw evidence is captured before normalization.
9. Reports consume results and never rerun validation.
10. Every generated artifact has one owner.
11. Machine-consumed data uses explicit versioned schemas.
12. Project paths and run paths use explicit path models.
13. Required release artifacts must exist; exit code alone is insufficient.
14. Gold files change only through an explicit update workflow.
15. Validation status, execution state, error kind, and diagnostic class remain distinct.
16. Legacy compatibility remains isolated in loaders and migrators.
17. A component may change internally when its external contracts remain compatible.
18. A cross-file contract change is one coordinated change.
19. A failure in a later stage must not erase valid earlier evidence.
20. Complexity must correspond to a stable responsibility or contract.

---

## 40. Architecture compliance checklist

A final implementation is architecture-compliant when:

```text
[ ] Framework code contains no active-language paths or module names
[ ] project.toml is the active-project authority
[ ] CLI and GUI resolve the same RunConfig for equivalent inputs
[ ] audit_core is the only validation orchestrator
[ ] all GF launches use the shared process runner
[ ] compilation, PGF, and scenarios have distinct stage owners
[ ] raw stdout and stderr are preserved
[ ] every process-backed result records command and working directory
[ ] reports do not launch GF or rescan sources
[ ] summary.json is versioned and reloadable
[ ] manifest.json verifies required artifacts
[ ] project and run paths are canonical and contained
[ ] state is disposable and contains no project architecture
[ ] gold updates are explicit
[ ] required release gates cannot be silently bypassed
[ ] status vocabularies are centralized
[ ] compatibility aliases are not emitted by canonical writers
[ ] contract tests cover component boundaries
[ ] schema tests cover canonical and legacy forms
[ ] end-to-end tests produce a complete run directory
[ ] documentation ownership contains no conflicting normative duplicates
```

---

## 41. Related documents

### Architecture details

```text
docs/architecture/COMPONENT_MAP.md
docs/architecture/EXECUTION_FLOW.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/architecture/EXTENSION_BOUNDARIES.md
docs/architecture/DEPENDENCY_RULES.md
```

### Normative locks

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

### GF and validation

```text
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/GOLDEN_TESTS.md
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
```

### Configuration and reports

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
```

### Decisions

```text
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0002-GF-AS-EXECUTION-ENGINE.md
docs/decisions/ADR-0003-SEPARATE-SCAN-AND-COMPILE.md
docs/decisions/ADR-0004-NATIVE-GFS-SCENARIOS.md
docs/decisions/ADR-0005-FILE-AND-SCENARIO-RESULTS.md
docs/decisions/ADR-0006-AI-READY-REPORT.md
docs/decisions/ADR-0007-GOLDEN-OUTPUT-TESTING.md
```

---

## 42. Final rule

GF Wordbench is not a collection of independent utilities.

It is one coordinated validation system in which:

```text
the project defines what must be validated
GF executes GF semantics
the framework controls and records the execution
models carry explicit results
reports expose those results
schemas preserve them across time
contracts keep every boundary aligned
```

A local implementation change is acceptable only when the complete architectural path remains coherent.
