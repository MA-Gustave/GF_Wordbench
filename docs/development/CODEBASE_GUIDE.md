# GF Wordbench — Codebase Guide

**Document ID:** `GF-WB-DEVELOPMENT-CODEBASE-GUIDE`  
**Status:** Normative developer guide  
**Document version:** `2.0.0`  
**Applies to:** GF Wordbench source, tests, active-project boundary, reusable validation-profile template, generated artifacts, public exports, and coordinated code changes  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** 2026-08-05  
**Target path:** `docs/development/CODEBASE_GUIDE.md`

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

This document explains how the GF Wordbench codebase is organized, where responsibilities belong, and how components cooperate.

It is intended for developers who need to:

- understand the system before editing it;
- locate the owner of a responsibility;
- trace a run from CLI, GUI, or automation to generated evidence;
- add or modify validation behavior;
- extend typed contracts without causing drift;
- change external-tool integration safely;
- add or modify diagnostics;
- change reports and persisted schemas;
- integrate native `.gfs` scenarios and reviewed gold comparisons;
- distinguish framework code from active-project code;
- preserve GF Audit capabilities during migration;
- identify the tests, locks, schemas, and documents affected by a change.

This is a navigation and ownership guide.

It does not replace:

- accepted ADRs;
- architecture owner documents;
- public interfile contracts;
- external-tool contracts;
- persisted-schema definitions;
- active-project GF contracts;
- command references;
- testing procedures;
- coding standards.

The central rule is:

> Every responsibility has one owner, and every cross-boundary change updates its provider, consumers, tests, schemas, artifacts, and owner documentation together.

---

## 2. Product model

GF Wordbench is a local development, validation, diagnostic, and release-readiness workbench for one resolved GF language context per run.

One workspace contains:

```text
one GF Wordbench framework
one resolved GF language context per run
one reusable generic validation-profile template
zero or more generated runs
local non-authoritative application state
```

The selected language context is represented by:

```text
project/
```

The reusable validation-profile template is represented by:

```text
templates/validation-profile/
```

Generated evidence is represented by:

```text
run_<run-id>/
```

GF Wordbench does not manage several unrelated selected language contexts inside one workspace.

Multi-workspace inventory, aggregation, comparison, and portfolio views belong to the independent `gf-portfolio` product.

Allowed product dependency:

```text
gf-portfolio
    → public versioned GF Wordbench artifacts

GF Wordbench
    -X→ gf-portfolio runtime, private APIs, database, state, or configuration
```

---

## 3. Authority boundaries

GF remains authoritative for:

```text
GF syntax
GF type checking
module resolution
.gf → .gfo compilation
PGF construction
grammar loading
parsing
linearization
generation
morphology
grammar introspection
GF runtime behavior
GF diagnostics
```

GF Wordbench remains authoritative for:

```text
active-project loading
target selection
validation orchestration
external-process control
timeouts and cancellation
raw evidence capture
static heuristic scanning
scenario assertion evaluation
normalization
gold comparison
diagnostic interpretation
causal classification
run history
report generation
artifact manifests
release-gate evaluation
```

GF Wordbench must not reimplement GF semantics.

Static scanning is heuristic evidence. It remains separate from authoritative GF execution.

---

## 4. Architectural model

GF Wordbench is one deployable modular monolith with hexagonal boundaries.

The architecture has two complementary dimensions:

1. five functional modules;
2. six dependency rings.

### 4.1 Functional modules

```text
projects
runs
validation
diagnostics
reporting
```

| Module | Primary responsibility |
|---|---|
| `projects` | Active-resolved language identity, configuration, loading, paths, lifecycle, and template operations |
| `runs` | Run identity, orchestration, budgets, continuation, cancellation, completion, and history |
| `validation` | Selection, scanning, compilation, PGF construction, scenarios, gold comparison, regression comparison, and release gates |
| `diagnostics` | Diagnostic normalization, findings, causal classification, pattern interpretation, and approved diagnostic tools |
| `reporting` | Persisted schemas, report rendering, manifests, artifact publication, and public exports |

There is no Wordbench `languages` or portfolio module.

### 4.2 Hexagonal rings

```text
domain
application
ports
adapters
entrypoints
bootstrap
```

| Ring | Responsibility |
|---|---|
| `domain` | Stable models, invariants, statuses, result semantics, and decision rules |
| `application` | Use cases and coordination |
| `ports` | Narrow contracts for external or unstable boundaries |
| `adapters` | Concrete filesystem, process, GF, TOML, JSON, clock, persistence, and UI-support mechanisms |
| `entrypoints` | CLI, GUI, and automation surfaces |
| `bootstrap` | Composition root and concrete dependency wiring |

Functional modules and rings are orthogonal.

A module may contain domain, application, port, and adapter elements. The repository does not require one package for every possible module-by-ring combination.

---

## 5. Canonical repository zones

```text
GF_Wordbench/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE.md
│
├── app/
│   ├── projects/
│   ├── runs/
│   ├── validation/
│   ├── diagnostics/
│   ├── reporting/
│   ├── entrypoints/
│   └── bootstrap.py
│
├── tests/
│   ├── unit/
│   ├── component/
│   ├── contracts/
│   ├── integration/
│   ├── end_to_end/
│   ├── migrations/
│   └── fixtures/
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
├── templates/
│   └── project/
│       ├── project.toml
│       ├── docs/
│       └── validation/
│
└── run_<run-id>/
    └── generated evidence
```

This layout expresses ownership, not a requirement to create empty directories.

A file is introduced only when it owns a coherent responsibility.

The repository must not gain technical layers merely to mirror documentation headings.

---

## 6. Package organization

A functional module normally exposes a structure equivalent to:

```text
<module>/
├── domain/
├── application/
├── ports/
├── adapters/
└── public API
```

Small cohesive areas may use fewer files when boundaries remain explicit.

### 6.1 Public API

Each module exposes a narrow public API.

Consumers must not import private implementation files merely to reuse a helper.

A public API may include:

- application request and result types;
- domain value objects;
- use-case functions or services;
- ports;
- stable events;
- versioned persisted artifacts.

### 6.2 Private implementation

Private implementation includes:

- adapter internals;
- parser internals;
- formatting helpers;
- local orchestration helpers;
- temporary migration readers;
- internal caches;
- package-private constants.

Private symbols must not become cross-module contracts accidentally.

### 6.3 Shared code

Shared code requires a clear owner.

Do not create a generic `common`, `shared`, or `utils` package as an ownerless dumping ground.

A helper belongs:

- in the module that owns its meaning;
- in an adapter that owns its mechanism;
- in a stable shared value-object package only when several modules legitimately consume the same contract.

---

## 7. Dependency direction

Canonical control flow:

```text
entrypoint
    → application use case
    → domain rules and ports
    → adapters
    → external systems
```

Bootstrap constructs the graph:

```text
bootstrap
    → adapters
    → ports
    → application services
    → entrypoints
```

Result flow returns as data:

```text
external evidence
    → adapter result
    → application result
    → domain result
    → run result
    → reporting and presentation
```

Prohibited reverse control includes:

```text
reporting → validation execution
diagnostics → GF compilation execution
projects → run results as resolved language identity
domain → adapters
adapters → entrypoints
project files → private Python modules
GF Wordbench → gf-portfolio internals
```

Detailed rules belong to:

```text
docs/architecture/DEPENDENCY_RULES.md
```

---

## 8. `projects` module

The `projects` module owns the active-project boundary.

### 8.1 Responsibilities

```text
resolved language identity
project.toml loading and validation
project-relative path resolution
source-root relationship
entrypoints and checkpoints
scenario registry
release configuration
project initialization
project reset
project migration
template validation
project checks
```

### 8.2 Domain

The `projects` domain owns concepts such as:

```text
ProjectId
ProjectConfig
ProjectPath
SourceRoot
ModuleTarget
Checkpoint
ScenarioRegistration
ReleaseTarget
ProjectValidationIssue
```

Domain objects remain free of TOML, filesystem, GUI, and process details.

### 8.3 Application

Application use cases include:

```text
load selected language context
show project
check project
initialize project
reset project
migrate project
resolve project paths
```

### 8.4 Ports

Typical ports include:

```text
ProjectConfigReader
ProjectConfigWriter
ProjectFilesystem
ProjectTemplateSource
ProjectArchiveWriter
ProjectLifecycleLock
```

### 8.5 Adapters

Typical adapters include:

```text
TOML project reader/writer
local filesystem project adapter
template directory adapter
ZIP or directory archive adapter
Git metadata reader
```

### 8.6 Prohibitions

The `projects` module must not:

- infer resolved language identity from application state;
- infer resolved language identity from previous runs;
- read Portfolio registries;
- own validation results;
- write reports;
- launch GF;
- update golds during ordinary loading or reset;
- hardcode an active language in framework source.

---

## 9. `runs` module

The `runs` module owns one execution lifecycle.

### 9.1 Responsibilities

```text
run ID
run request
run paths
execution budget
stage planning
continuation policy
progress
cancellation
partial-result preservation
run completion
run history
previous-run eligibility
cleanup coordination
```

### 9.2 Domain

The `runs` domain owns concepts such as:

```text
RunId
RunMode
RunRequest
RunPlan
RunBudget
RunState
RunResult
RunPaths
ProgressEvent
CancellationState
ContinuationDecision
```

### 9.3 Application

Application use cases include:

```text
validate selected language context
validate one target
validate checkpoints
run diagnostic validation
run release validation
show run
verify run
archive run
restore run
clean run
```

### 9.4 Ports

Typical ports include:

```text
Clock
RunDirectoryStore
RunHistoryReader
CancellationSource
ProcessExecutor
ArtifactVerifier
```

### 9.5 Orchestration rule

`runs` coordinates public application contracts from:

```text
projects
validation
diagnostics
reporting
```

It does not implement their algorithms.

### 9.6 Completion rule

A run is completed through one controlled completion path that:

- preserves available evidence;
- evaluates terminal state;
- requests required reports;
- writes or verifies the manifest;
- records missing evidence;
- releases temporary resources;
- returns one structured `RunResult`.

---

## 10. `validation` module

The `validation` module owns bounded validation operations.

### 10.1 Responsibilities

```text
file selection
static scanning
source fingerprinting
GF compilation
PGF construction
native .gfs scenarios
marker checks
normalization
gold comparison
regression comparison
release gates
```

### 10.2 Domain

The `validation` domain owns concepts such as:

```text
ValidationStatus
FileSelection
SelectionReason
ScanRuleId
ScanCounts
StaticFinding
SourceFingerprint
CompileRequest
CompileResult
ScenarioId
ScenarioResult
GoldComparison
RegressionChange
ReleaseGate
ReleaseDecision
```

### 10.3 Application

Application use cases include:

```text
select project files
scan one selected source
compile one selected target
build PGF
run one scenario
run required scenarios
compare normalized output with gold
compare current results with a previous run
evaluate release gates
```

### 10.4 Ports

Typical ports include:

```text
GfToolPort
SourceReader
ValidationEvidenceWriter
GoldReader
GoldWriter
FingerprintService
NormalizationProfileReader
```

### 10.5 Adapters

Typical adapters include:

```text
native GF adapter
local source reader
run-evidence writer
project gold adapter
normalization adapter
legacy summary reader
```

### 10.6 Prohibitions

Validation components must not:

- render user reports;
- import GUI or CLI code;
- update golds during normal validation;
- define resolved language identity;
- invoke Portfolio;
- infer release readiness from one compile result;
- treat static findings as GF compiler verdicts;
- parse human Markdown as machine truth.

---

## 11. Static scanning

Static scanning remains language-neutral and heuristic.

Canonical built-in counts preserve the inherited GF Audit nucleus:

```text
single_slash_eq
double_slash_dash
runtime_str_match
untyped_case_str_pat
untyped_table_str_pat
trailing_spaces
```

Static scanning:

- operates on one already selected source;
- preserves deterministic counts;
- records structured findings;
- writes one run-owned evidence artifact;
- does not invoke GF;
- does not modify source;
- does not classify dependency cascades;
- does not determine release status directly.

Detailed behavior belongs to:

```text
docs/validation/STATIC_SCANNING.md
```

---

## 12. GF anti-corruption boundary

All GF interaction passes through `GfToolPort` and approved adapters.

The GF boundary owns translation between:

```text
Wordbench requests and results
↕
GF executable arguments, streams, artifacts, and diagnostics
```

The boundary preserves:

- executable;
- ordered arguments;
- working directory;
- effective GF path;
- stdin source;
- environment changes;
- timeout;
- cancellation;
- stdout;
- stderr;
- exit state;
- produced artifacts;
- version identity.

The adapter must not leak raw GF-specific representations into unrelated domain rules.

Detailed behavior belongs to:

```text
docs/decisions/ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md
docs/gf/GF_COMMAND_CONSTRUCTION.md
docs/gf/GF_COMPILATION.md
docs/gf/GF_SCRIPT_EXECUTION.md
```

---

## 13. Compilation

Compilation is one bounded validation operation.

Inputs include:

```text
selected source identity
resolved project context
resolved GF path
GF compatibility profile
compile timeout
run-owned evidence target
```

Outputs include:

```text
process result
normalized compile result
diagnostic references
produced artifact records
compile evidence references
```

Compilation does not:

- select files;
- run the static scanner;
- classify downstream failures;
- decide full release readiness;
- render reports;
- mutate project source.

A pre-existing `.gfo` does not prove current compilation success.

---

## 14. PGF construction

PGF construction is a separate validation operation.

It receives:

```text
configured release entrypoint or ordered entrypoints
resolved GF path
optimization policy
timeout
expected PGF identity
run-owned output target
```

It verifies:

```text
process completion
GF diagnostics
expected PGF existence
non-empty artifact
current-run attribution
manifest inclusion
```

The release entrypoint and expected PGF identity come from project contracts.

They must not be guessed from whichever module compiled last.

---

## 15. Native `.gfs` scenarios

Scenario logic belongs in project-owned `.gfs` files.

Python orchestration owns:

```text
scenario registration
path validation
GF process request
stdin delivery
stdout/stderr capture
marker checks
normalization
assertion evaluation
gold comparison
ScenarioResult construction
```

A zero exit code alone is insufficient.

A successful scenario requires every configured completion and assertion criterion.

Normal validation is read-only with respect to:

```text
<validation-profile-root>/validation/scenarios/
<validation-profile-root>/validation/inputs/
<validation-profile-root>/validation/gold/
```

Gold updates occur only through an explicit reviewed workflow.

---

## 16. Regression comparison

Regression comparison consumes structured current and previous results.

Canonical change kinds:

```text
unchanged
improved
regressed
new
removed
```

Comparison requires compatible:

```text
resolved language identity
schema
subject identity
rule semantics
normalization profile
selection context where relevant
```

The comparison engine does not parse `summary.md`.

Legacy summaries are accepted only through isolated migration readers.

---

## 17. Release gates

Release gates evaluate the completed structured validation evidence.

They may depend on:

- project release policy;
- required file and checkpoint results;
- required scenarios;
- required gold comparisons;
- expected PGF evidence;
- unresolved blockers;
- manifest integrity;
- required schema and contract checks.

Release gates must not:

- alter failing results;
- rerun missing stages silently;
- update gold;
- ignore missing required evidence;
- infer readiness from report prose.

---

## 18. `diagnostics` module

The `diagnostics` module owns interpretation of preserved evidence.

### 18.1 Responsibilities

```text
GF diagnostic parsing
tool diagnostic parsing
normalization
error-kind assignment
finding construction
causal classification
blocker resolution
known pattern catalog
approved diagnostic-tool execution
```

### 18.2 Domain

Typical concepts include:

```text
Diagnostic
DiagnosticKind
DiagnosticClass
EvidenceRef
Finding
BlockerRef
ToolFinding
ClassificationResult
```

### 18.3 Application

Application use cases include:

```text
interpret GF compile evidence
interpret scenario evidence
classify file failures
resolve blocker graph
run approved diagnostic tool
build diagnostic audit
```

### 18.4 Ports

Typical ports include:

```text
DiagnosticToolPort
EvidenceReader
DiagnosticPatternRegistry
```

### 18.5 Prohibitions

Diagnostics must not:

- replace raw evidence;
- launch GF through validation-private helpers;
- rewrite validation results;
- render reports directly;
- use AI output as normative evidence;
- execute arbitrary commands;
- contain language-specific source policy in framework rules.

---

## 19. Diagnostic normalization and causal classification

Diagnostic normalization and causal classification remain separate.

```text
raw evidence
    → diagnostic normalization
    → structured diagnostics
    → causal classification
```

Normalization owns:

- source references;
- line and column extraction;
- technical error kinds;
- message normalization;
- fatal-diagnostic recognition.

Classification owns:

- direct;
- downstream;
- ambiguous;
- noise;
- skipped;
- blocker relationships.

Classification must preserve the raw stage result.

It does not replace compile or scenario status.

---

## 20. Diagnostic tools

Optional diagnostic executables are registered through an explicit allowlist.

Each tool registration defines:

```text
tool ID
purpose
executable resolution
allowed operations
allowed arguments
working-directory policy
input policy
timeout
output limits
mutability
network policy
evidence role
parser
```

Project configuration must not inject arbitrary command templates.

Diagnostic tools do not determine GF truth, run status, release status, or Portfolio readiness directly.

---

## 21. `reporting` module

The `reporting` module owns persisted and rendered outputs.

### 21.1 Responsibilities

```text
summary.json
summary.md
AI_READY.md
raw-log aggregation
detail reports
top-error output
manifest.json
artifact verification views
public versioned exports
```

### 21.2 Domain and contracts

Reporting consumes public result contracts.

It does not own validation semantics.

Persisted formats have:

```text
schema_id
schema_version
canonical field meanings
path semantics
migration policy
```

### 21.3 Application

Application use cases include:

```text
write machine summary
write human summary
write AI-ready report
write aggregate logs
write detail artifacts
write manifest
verify artifact set
export public run package
```

### 21.4 Ports and adapters

Typical ports include:

```text
ArtifactWriter
ArtifactReader
SchemaSerializer
ManifestHasher
```

Typical adapters include:

```text
JSON writer
Markdown renderer
filesystem artifact writer
SHA-256 manifest adapter
legacy summary reader
```

### 21.5 Passive-reporting rule

Reports:

- consume completed or explicitly partial results;
- use existing evidence references;
- preserve deterministic ordering;
- do not invoke GF;
- do not rerun scanning;
- do not modify project files;
- do not update gold;
- do not create new status vocabularies;
- do not parse another human report as authority.

---

## 22. Canonical run artifacts

Conceptual run layout:

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
│   ├── scenarios/
│   └── tools/
├── details/
└── artifacts/
    ├── gfo/
    ├── pgf/
    └── out/
```

`RunPaths` owns actual locations.

Individual writers must not independently reconstruct canonical filenames.

A run never rewrites project source or golds.

Previous runs are immutable evidence until an explicit cleanup operation removes them.

---

## 23. Artifact ownership

Every artifact has one writer and zero or more observers.

| Artifact | Owner |
|---|---|
| `<validation-profile-root>/project.toml` | `projects` |
| application state | local state adapter |
| raw process evidence | process or tool adapter for the operation |
| static-scan evidence | `validation` |
| compile evidence | `validation` |
| scenario evidence | `validation` |
| diagnostic findings | `diagnostics` |
| structured run result | `runs` |
| `summary.json` | `reporting` |
| `summary.md` | `reporting` |
| `AI_READY.md` | `reporting` |
| aggregate logs | `reporting` |
| `manifest.json` | `reporting` |
| `.gold` files | explicit reviewed gold-update workflow |

Observers must not rewrite owned artifacts.

Derived artifacts reference their source evidence.

---

## 24. Entrypoints

### 24.1 CLI

The CLI owns:

```text
command parsing
surface-level validation
application request construction
terminal rendering
exit-code mapping
```

The CLI does not own:

```text
project schema
GF arguments
process execution
validation algorithms
report serialization
release policy
```

Exact command spelling belongs to:

```text
docs/usage/CLI_REFERENCE.md
```

### 24.2 GUI

The GUI owns:

```text
visual input
early presentation validation
progress display
result display
artifact navigation
local convenience state
```

The GUI calls the same application use cases as the CLI.

Widgets must not invoke GF, process adapters, or validation stages directly.

### 24.3 Automation

Automation uses the same public application requests and structured results.

It must not depend on terminal text when a machine-readable artifact exists.

---

## 25. Bootstrap

Bootstrap is the composition root.

It owns:

- adapter construction;
- port binding;
- environment-specific dependency selection;
- application-service construction;
- entrypoint wiring;
- optional capability wiring.

Bootstrap must not:

- execute a run during import;
- parse raw CLI arguments;
- display GUI dialogs;
- contain validation algorithms;
- write reports;
- define project policy;
- hide required configuration through implicit fallback;
- connect Wordbench to Portfolio.

Importing bootstrap produces no filesystem, process, or UI side effects.

---

## 26. Project boundary

The selected language context contains language-specific facts and assets.

```text
<validation-profile-root>/project.toml
<validation-profile-root>/docs/
<validation-profile-root>/validation/scenarios/
<validation-profile-root>/validation/gold/
<validation-profile-root>/validation/inputs/
configured GF source tree
```

The selected language context owns:

- resolved language identity;
- language identity;
- source roots;
- module conventions;
- entrypoints;
- checkpoints;
- scenarios;
- gold expectations;
- morphology and syntax contracts;
- release criteria;
- project decisions;
- known issues.

Framework production code must not hardcode these facts.

---

## 27. Active-project documentation

Canonical project documentation includes, as applicable:

```text
00_PROJECT_START_HERE.md
INTERFILE_CONTRACT_LOCK.md
LANGUAGE_OVERVIEW.md
LANGUAGE_ARCHITECTURE.md
MODULE_DEPENDENCY_MAP.md
CATEGORY_AND_LINCAT_CONTRACT.md
MORPHOLOGY_SPEC.md
SYNTAX_AND_CONSTRUCTOR_RULES.md
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
DECISION_LOG.md
KNOWN_ISSUES.md
RELEASE_CRITERIA.md
RESEARCH_EVIDENCE.md
```

Framework documentation must not duplicate these language-specific contracts.

Project documents describe the project directly. They do not maintain a separate implementation-status tracker.

---

## 28. Template boundary

`templates/validation-profile/` is generic and identity-free.

It contains:

- reusable structure;
- placeholders;
- language-neutral guidance;
- empty or example-only registries;
- project initialization instructions.

It must not contain:

- active-language identity;
- old source paths;
- local machine paths;
- run history;
- selected language context decisions;
- populated release evidence;
- copied golds presented as current;
- Portfolio identifiers.

Initialization copies or renders the template into `project/`.

Template updates do not overwrite an selected language context silently.

---

## 29. Persisted schemas

Persisted schemas are public contracts.

Schema changes require coordinated updates to:

```text
domain models
serializers
readers
migration readers
reports
diff and comparison
fixtures
tests
schema references
PERSISTED_SCHEMA_LOCK.md
```

Rules:

- one canonical writer per persisted format;
- readers validate `schema_id` and `schema_version`;
- legacy support remains isolated in migration boundaries;
- current writers emit only current canonical shapes;
- human Markdown is not parsed when structured JSON exists;
- paths are serialized using documented project-relative or run-relative semantics.

---

## 30. Runtime and persisted paths

Runtime path type:

```python
Path
```

Portable persisted representation:

```text
project-relative POSIX string
run-relative POSIX string
or explicitly local environment path where the schema permits it
```

Path conversion belongs to a single path or serialization owner.

Report writers and consumers must not invent competing conversion rules.

Windows paths require:

- drive-awareness;
- UNC handling;
- case-insensitive equivalence;
- junction policy;
- long-path handling;
- safe filename generation.

---

## 31. Application state

Application state is disposable local convenience data.

It may contain:

```text
recent paths
last selected mode
window preferences
last run pointer
local executable selection
```

It must not contain:

```text
selected language context identity
required entrypoints
required scenarios
release policy
current run truth
gold expectations
Portfolio registry
credentials
```

A corrupt state file must not make the framework unusable.

State writes are atomic.

---

## 32. Process execution

All external process execution passes through one process port and approved adapters.

A process request includes:

```text
executable
ordered arguments
working directory
environment changes
stdin
timeout
cancellation
output limits
approved roots
```

A process result includes:

```text
launch state
exit code
timeout state
cancellation state
duration
stdout reference
stderr reference
termination outcome
produced artifacts
```

Normal execution uses no intermediate shell.

Detailed behavior belongs to:

```text
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/reference/COMMAND_REFERENCE.md
```

---

## 33. Evidence model

Every normative result is traceable to preserved evidence.

A reference may contain:

```text
evidence ID
artifact path
artifact role
producer
producer version
observed time
content hash
freshness context
```

Evidence is captured before normalization and interpretation.

Raw evidence is not replaced by:

- normalized output;
- diagnostic summaries;
- Markdown reports;
- AI-ready excerpts;
- Portfolio projections.

---

## 34. Status and error dimensions

Keep separate:

```text
validation status
execution state
error kind
diagnostic class
regression change
release decision
```

Example timeout:

```text
validation status = ERROR
execution state = timed_out
error kind = TIMEOUT
diagnostic class = ambiguous
```

Example local GF syntax failure:

```text
validation status = FAIL
execution state = completed
error kind = SYNTAX
diagnostic class = direct
```

No module introduces private competing values.

Canonical vocabularies belong to:

```text
docs/reference/STATUS_VALUES.md
docs/reference/DIAGNOSTIC_KINDS.md
docs/GLOSSARY.md
```

---

## 35. Determinism

The following are deterministic:

```text
file selection
checkpoint order
entrypoint order
scenario order
finding order
blocker order
artifact path order
manifest order
top-error order
report sections
previous-run matching
```

Determinism must not depend on:

```text
filesystem enumeration order
unordered set iteration
GUI widget order
localized strings
current working directory
random values without a controlled seed
legacy dictionary ordering
```

Parallel execution must restore canonical result order.

---

## 36. Exception boundaries

Errors become structured outcomes at the nearest boundary with enough context.

```text
projects adapter
    → configuration or path error

process adapter
    → launch, timeout, cancellation, or termination result

validation adapter
    → compile, scenario, or artifact result

diagnostics
    → structured interpretation

runs
    → continuation and terminal run result

entrypoint
    → exit code or visible presentation
```

Broad exception swallowing is prohibited.

When containment is required:

- preserve safe exception evidence;
- produce a structured error;
- continue only when independent evidence remains safe;
- never fabricate success.

---

## 37. Preserving GF Audit capabilities

The inherited GF Audit capability set remains part of the Wordbench behavior where applicable.

Preserve:

- the six static scan rules;
- deterministic file selection and exclusion reasons;
- GF version probing;
- compile requests and options;
- stdout, stderr, exit codes, timeouts, and artifacts;
- direct, downstream, and ambiguous classifications;
- regression states `unchanged`, `improved`, `regressed`, `new`, and `removed`;
- source fingerprints;
- CLI and GUI workflows;
- `summary.json`;
- `summary.md`;
- `AI_READY.md`;
- top-error and aggregate logs;
- best-effort evidence production without false success;
- scanner, classifier, diff, report, and smoke tests.

Legacy names and shapes remain confined to compatibility readers and migration tests.

Current code and artifacts use GF Wordbench terminology.

---

## 38. Adding a functional module

A new functional module requires:

- a stable product responsibility;
- a clear owner;
- a public API;
- independent domain meaning;
- multiple cohesive use cases;
- explicit dependency rules;
- tests;
- an accepted ADR updating the architecture.

Do not create a module for:

- one helper;
- one report section;
- one command option;
- one adapter implementation;
- Portfolio behavior inside Wordbench.

---

## 39. Adding a validation operation

Use this sequence:

```text
1. define the criterion
2. identify the validation owner
3. define typed request and result
4. define raw evidence
5. define execution and error semantics
6. define ports and adapters
7. define run-owned artifact locations
8. implement without report logic
9. add run orchestration
10. add diagnostic interpretation where needed
11. add persisted projections
12. add human reporting
13. add tests
14. update locks and owner documents
```

A separate operation is justified when it has:

- a distinct criterion;
- distinct inputs;
- distinct evidence;
- distinct failure behavior;
- an independently testable contract.

---

## 40. Adding or changing a model

Checklist:

```text
[ ] owner identified
[ ] domain meaning documented
[ ] required or optional decided
[ ] invariant defined
[ ] constructors updated
[ ] producers updated
[ ] consumers searched
[ ] serialization reviewed
[ ] readers and migrations reviewed
[ ] reports reviewed
[ ] comparison behavior reviewed
[ ] fixtures updated
[ ] schema impact reviewed
[ ] contract tests updated
[ ] lock files updated
```

Do not add a field solely because one report wants prose that can be derived safely.

Do not make reports parse another report to obtain a field.

---

## 41. Adding a port or adapter

A port is justified when:

- the boundary is external;
- the mechanism is unstable;
- tests need a controlled substitute;
- platform behavior varies;
- security containment is required.

Checklist:

```text
[ ] boundary owner identified
[ ] port types are mechanism-neutral
[ ] adapter-specific types do not leak
[ ] failure contract defined
[ ] timeout and cancellation defined where applicable
[ ] read and write roots defined
[ ] fake adapter tests added
[ ] real adapter integration tests added
[ ] bootstrap wiring added
[ ] architecture tests updated
```

Do not introduce a port merely to wrap a private helper.

---

## 42. Adding a CLI capability

`docs/usage/CLI_REFERENCE.md` owns the command contract.

Checklist:

```text
[ ] application use case exists
[ ] safety class identified
[ ] parser updated
[ ] typed application request produced
[ ] project and environment precedence documented
[ ] GUI or automation equivalence reviewed
[ ] non-interactive behavior defined
[ ] exit mapping reviewed
[ ] help and examples updated
[ ] CLI tests added
[ ] no domain logic added to the parser
```

The CLI does not mutate an already resolved run request.

---

## 43. Adding a GUI capability

Checklist:

```text
[ ] application use case already exists or is added independently
[ ] GUI collects plain values
[ ] early validation is presentation-only
[ ] authoritative validation remains in application services
[ ] local state is non-authoritative
[ ] CLI or automation equivalence reviewed
[ ] worker and cancellation behavior reviewed
[ ] GUI tests added
[ ] GUI reference updated
```

A GUI-only value must not be required for headless execution.

---

## 44. Adding a report field or artifact

Checklist:

```text
[ ] source exists in a public result or evidence contract
[ ] artifact owner identified
[ ] path owned by RunPaths or artifact model
[ ] report does not execute validation
[ ] schema impact reviewed
[ ] deterministic ordering defined
[ ] path semantics defined
[ ] manifest role defined
[ ] legacy readers reviewed
[ ] report tests updated
[ ] schema and report references updated
```

A JSON field is a persisted-schema change.

A Markdown wording change is not a machine contract unless explicitly declared otherwise.

---

## 45. Adding a diagnostic rule

Checklist:

```text
[ ] evidence pattern documented
[ ] technical error kind selected
[ ] causal classification remains separate
[ ] false-positive risk reviewed
[ ] false-negative risk reviewed
[ ] stdout and stderr fixtures added
[ ] Unicode and path behavior tested
[ ] unknown fallback preserved
[ ] raw evidence unchanged
[ ] diagnostic reference updated
```

Diagnostic rules live under `diagnostics`.

They are not copied into reporting or validation adapters.

---

## 46. Adding an external tool

Before adding another executable:

```text
[ ] capability belongs to Wordbench scope
[ ] GF or Python cannot provide it sufficiently
[ ] tool ID assigned
[ ] purpose documented
[ ] executable resolution defined
[ ] allowed operations and arguments defined
[ ] working directory defined
[ ] environment policy defined
[ ] stdin/stdout/stderr behavior defined
[ ] timeout and output limits defined
[ ] mutability and network policy defined
[ ] artifacts defined
[ ] failure semantics defined
[ ] security reviewed
[ ] fake-process tests added
[ ] integration tests added
[ ] tool catalog and external lock updated
```

Do not add an executable merely for convenience.

Do not expose arbitrary command templates through project configuration.

---

## 47. Adding or changing scenarios

Checklist:

```text
[ ] scenario ID unique
[ ] registry entry defined
[ ] required or optional role defined
[ ] entrypoint relationship documented
[ ] input references registered
[ ] markers unique and complete
[ ] execution bounded
[ ] normalization profile selected
[ ] gold requirement defined
[ ] ScenarioResult populated
[ ] normal run cannot update gold
[ ] tests added
[ ] project validation specification updated
[ ] project lock updated
```

Scenario logic belongs in `.gfs`.

Python orchestrates and verifies the observable contract.

---

## 48. Changing gold normalization

This change requires coordinated review of:

```text
normalizer
scenario runner
affected gold files
comparison logic
scenario fixtures
schema version
project validation specification
gold-update workflow
release notes
migration guidance
```

A normal run never updates gold automatically.

Normalization must not erase meaningful GF output.

---

## 49. Changing run layout

Review:

```text
RunPaths
stage writers
evidence references
report writers
manifest writer
run verifier
previous-run reader
cleanup and retention
GUI artifact navigation
tests
PERSISTED_SCHEMA_LOCK.md
migration guidance
public Portfolio-facing artifacts
```

No component chooses a new filename independently.

---

## 50. Testing architecture

Canonical test categories:

```text
tests/unit/
tests/component/
tests/contracts/
tests/integration/
tests/end_to_end/
tests/migrations/
tests/fixtures/
```

### 50.1 Unit tests

Unit tests use:

- pure domain objects;
- fake ports;
- temporary paths;
- deterministic input;
- no developer-global GF installation.

### 50.2 Component tests

Component tests exercise one module through its public application contract with controlled adapters.

### 50.3 Contract tests

Contract tests verify:

- public APIs;
- dependency direction;
- schema shape;
- artifact ownership;
- path ownership;
- report passivity;
- process containment;
- project/template separation;
- Wordbench independence from `gf-portfolio`.

### 50.4 Integration tests

Integration tests may use:

- real GF;
- a controlled RGL installation;
- neutral fixture grammars;
- platform-specific process behavior;
- temporary workspaces.

### 50.5 End-to-end tests

End-to-end tests prove:

```text
entrypoint
→ bootstrap
→ project loading
→ run orchestration
→ validation
→ diagnostics
→ reporting
→ manifest verification
```

---

## 51. Architecture enforcement tests

Required checks include:

```text
domain does not import adapters
application does not import concrete adapters
entrypoints do not import validation internals
reports do not import execution behavior
only process adapters use process libraries
projects does not depend on runs for identity
validation does not depend on reporting
diagnostics does not rewrite evidence
production code does not import tests
framework code remains language-neutral
template remains identity-free
normal runs cannot update gold
Wordbench does not import gf-portfolio
```

Cycles between modules and rings are prohibited.

---

## 52. Development commands

Install development dependencies:

```text
python -m pip install -e ".[dev]"
```

Run tests:

```text
python -m pytest
```

Run a test module:

```text
python -m pytest <test-path>
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

CLI help and GUI startup use the canonical entrypoints documented in:

```text
docs/usage/CLI_REFERENCE.md
docs/usage/GUI_REFERENCE.md
```

Detailed setup belongs to:

```text
docs/development/DEVELOPMENT_SETUP.md
```

---

## 53. Navigation by responsibility

### Active-project loading

```text
projects application service
ProjectConfigReader port
TOML project adapter
```

### Project initialization and reset

```text
projects lifecycle use cases
project filesystem and archive ports
template adapter
```

### Run creation and completion

```text
runs application service
RunPaths owner
run directory adapter
```

### File selection

```text
validation selection use case
```

### Static scanning

```text
validation static-scanning use case
```

### GF command construction and execution

```text
GfToolPort
GF adapter
ProcessExecutor port
local process adapter
```

### Scenario execution

```text
validation scenario use case
GF adapter
normalization and gold contracts
```

### Diagnostic normalization

```text
diagnostics interpretation use cases
```

### Direct/downstream classification

```text
diagnostics causal-classification use case
```

### Regression comparison

```text
validation regression-comparison use case
```

### Structured run result

```text
runs domain and completion service
```

### `summary.json`

```text
reporting machine-summary writer
```

### `AI_READY.md`

```text
reporting AI-ready renderer
```

### Application state

```text
local state port and adapter
```

### Active language identity

```text
<validation-profile-root>/project.toml
```

### GF module contracts

```text
<validation-profile-root>/docs/INTERFILE_CONTRACT_LOCK.md
```

---

## 54. Debugging routes

### CLI and GUI resolve different behavior

Inspect:

```text
entrypoint request construction
bootstrap wiring
projects resolution
runs request equality
local state fallback
```

### Wrong files selected

Inspect:

```text
project source configuration
projects path resolution
validation selection contract
selection evidence
```

### GF request is wrong

Inspect:

```text
resolved executable
resolved GF path
GF adapter request construction
process request evidence
external-tool lock
```

### Failure classification is wrong

Inspect:

```text
raw stdout and stderr
normalized diagnostics
evidence references
causal classifier
blocker graph
```

### Report disagrees with machine summary

Inspect:

```text
RunResult
persisted schema
machine-summary writer
affected renderer
```

Do not fix this by parsing one report from another.

### Scenario reports success incorrectly

Inspect:

```text
process result
required markers
normalization
assertions
gold comparison
ScenarioResult
```

### Old language identity appears in framework code

Inspect:

```text
project configuration
project docs
project validation assets
framework fixtures
templates
migration readers
application state
```

### Portfolio concepts appear inside Wordbench

Inspect:

```text
project schema
application state
reporting exports
bootstrap wiring
module imports
```

Portfolio aggregation belongs outside Wordbench.

---

## 55. Anti-patterns

Do not introduce:

```text
a second active-project loader
a second RunPaths owner
a second path normalizer
report-time GF execution
GUI-only validation semantics
language-specific framework defaults
shell command strings built from project text
dynamic undocumented result fields
Markdown parsing as structured data exchange
silent gold updates
global mutable run state
shared cross-run caches without a contract
one generic status for every dimension
one giant orchestrator containing every algorithm
one interface per trivial helper
a generic workflow engine for a controlled pipeline
a runtime plugin system without stable use cases
Portfolio aggregation inside Wordbench
```

Complexity is justified only when it owns a stable, independently testable responsibility.

---

## 56. Refactoring rules

A compatible internal refactor preserves:

- public module contracts;
- domain meaning;
- artifact paths;
- schema identities;
- status semantics;
- deterministic output;
- tests;
- project behavior;
- external-tool contracts.

A contract refactor requires coordinated migration.

Before moving code:

```text
search imports
identify owner
identify public and private symbols
review dependency direction
move tests
update bootstrap wiring
update locks
update owner documents
remove duplicate implementation
```

Do not leave forwarding wrappers indefinitely unless they are explicit compatibility adapters.

---

## 57. Change-impact matrix

| Change | Primary owner | Required secondary review |
|---|---|---|
| Project field | `projects` | template, bootstrap, schemas, tests, migration |
| Run request field | `runs` | entrypoints, validation, reporting |
| Run path | `runs` | writers, readers, manifest, cleanup, schemas |
| Static scan rule | `validation` | diagnostics, reporting, fixtures, schemas |
| GF flag | GF adapter | external lock, compatibility, integration tests |
| Scenario marker | `validation` | `.gfs`, gold, normalization, tests |
| Diagnostic kind | `diagnostics` | schemas, reporting, tests |
| Causal class | `diagnostics` | run result, reporting, tests |
| JSON field | `reporting` | schema, readers, comparison, migration |
| Markdown section | `reporting` | tests and declared consumers |
| Gold normalization | `validation` | project golds, release review |
| Artifact filename | `runs` / artifact owner | writers, readers, manifest, schemas |
| GUI field | entrypoint | state, application request, CLI equivalence |
| CLI option | entrypoint | application request, GUI equivalence, CLI reference |
| Project template | `projects` | initializer, project docs, tests |
| Public export | `reporting` | schema, manifest, Portfolio compatibility |

---

## 58. Documentation ownership

Framework behavior is documented under:

```text
docs/
```

Active-project behavior is documented under:

```text
<validation-profile-root>/docs/
```

Template guidance is documented under:

```text
templates/validation-profile/docs/
```

Rules:

- one normative owner per rule;
- use cross-references instead of duplicated definitions;
- update documentation with the coordinated code change;
- mark examples as examples;
- do not add implementation-status trackers to normative documents;
- do not maintain Portfolio policy inside Wordbench documentation.

---

## 59. Required review checklist

For every non-trivial code change:

```text
[ ] functional module identified
[ ] architectural ring identified
[ ] responsibility owner identified
[ ] public contract identified
[ ] provider reviewed
[ ] direct consumers reviewed
[ ] downstream consumers reviewed
[ ] domain models reviewed
[ ] port and adapter boundaries reviewed
[ ] path ownership reviewed
[ ] status and error semantics reviewed
[ ] raw evidence preservation reviewed
[ ] persisted schema impact reviewed
[ ] project and template boundaries reviewed
[ ] Wordbench/Portfolio boundary reviewed
[ ] CLI, GUI, and automation equivalence reviewed
[ ] unit tests updated
[ ] component tests updated
[ ] contract tests updated
[ ] integration tests updated when required
[ ] fixtures and golds reviewed intentionally
[ ] lock files updated
[ ] owner documentation updated
[ ] migration or compatibility handling updated
```

---

## 60. Codebase acceptance criteria

The codebase architecture is healthy when:

```text
[ ] five functional modules own all product responsibilities
[ ] hexagonal dependency direction is enforced
[ ] one owner exists for every major contract and artifact
[ ] CLI, GUI, and automation call shared application use cases
[ ] one selected language context is loaded from <validation-profile-root>/project.toml
[ ] RunPaths owns generated locations
[ ] runs coordinates without absorbing validation algorithms
[ ] validation operations return typed evidence
[ ] GF execution is behind GfToolPort and process ports
[ ] raw stdout and stderr are preserved
[ ] diagnostics interpretation is centralized
[ ] causal classification remains separate
[ ] reports consume structured results and existing evidence
[ ] reports never execute GF
[ ] framework production code remains language-neutral
[ ] scenarios use native .gfs
[ ] normal runs never modify gold
[ ] persisted schemas are versioned
[ ] templates remain identity-free
[ ] tests do not require hidden developer state
[ ] dependency directions remain acyclic
[ ] GF Audit capabilities remain covered
[ ] GF Wordbench remains independent of gf-portfolio
[ ] contract changes update every consumer
```

---

## 61. Cross-references

| Topic | Document |
|---|---|
| Architectural decision | `docs/decisions/ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md` |
| Architecture overview | `docs/architecture/ARCHITECTURE_OVERVIEW.md` |
| Component ownership | `docs/architecture/COMPONENT_MAP.md` |
| Dependency rules | `docs/architecture/DEPENDENCY_RULES.md` |
| Product boundaries | `docs/architecture/PRODUCT_BOUNDARIES.md` |
| Execution flow | `docs/architecture/EXECUTION_FLOW.md` |
| Framework contracts | `docs/INTERFILE_CONTRACT_LOCK.md` |
| External tools | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Persisted schemas | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Command reference | `docs/reference/COMMAND_REFERENCE.md` |
| CLI | `docs/usage/CLI_REFERENCE.md` |
| Development setup | `docs/development/DEVELOPMENT_SETUP.md` |
| Testing | `docs/development/TESTING_GF_WORDBENCH.md` |
| Extension process | `docs/development/EXTENDING_GF_WORDBENCH.md` |
| Backward compatibility | `docs/development/BACKWARD_COMPATIBILITY.md` |
| Debugging | `docs/development/DEBUGGING_THE_FRAMEWORK.md` |
| Static scanning | `docs/validation/STATIC_SCANNING.md` |
| File selection | `docs/validation/FILE_SELECTION.md` |
| GF compilation | `docs/gf/GF_COMPILATION.md` |
| GF command construction | `docs/gf/GF_COMMAND_CONSTRUCTION.md` |
| Error classification | `docs/diagnostics/ERROR_CLASSIFICATION.md` |
| Diagnostic tools | `docs/diagnostics/TOOL_CATALOG.md` |
| Project schema | `docs/configuration/PROJECT_TOML_REFERENCE.md` |
| Active-project contracts | `<validation-profile-root>/docs/INTERFILE_CONTRACT_LOCK.md` |

---

## 62. Enforcement rule

> Follow ownership before implementation.

When a change appears to require edits in many unrelated places, identify the missing or duplicated owner before adding another dependency or helper.

When a change crosses a boundary, treat its provider, consumers, models, ports, adapters, schemas, tests, artifacts, and owner documents as one coordinated change unit.
