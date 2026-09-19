# GF Wordbench — Validation Pipeline

**Document ID:** `GF-WB-VALIDATION-PIPELINE`  
**Status:** Normative validation architecture  
**Applies to:** GF Wordbench framework and one selected GF language context  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** GF Wordbench maintainers  
**Target path:** `docs/validation/VALIDATION_PIPELINE.md`  
**Document version:** `1.1.0`  
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

This document defines the complete GF Wordbench validation pipeline.

It specifies:

- how a validation run begins;
- which configuration sources are authoritative;
- which stages execute and in which logical order;
- which stages are required by each validation mode;
- how files, modules, scenarios, and artifacts are selected;
- how static scans and GF execution remain distinct;
- how failures block dependent work without hiding unrelated evidence;
- how stage, item, and run statuses are calculated;
- how previous-run comparison is performed;
- how reports and manifests are finalized;
- which components own each stage;
- which invariants tests must enforce.

This document defines pipeline behavior.

Detailed contracts remain owned by:

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
<validation-profile-root>/docs/INTERFILE_CONTRACT_LOCK.md
```

Detailed GF integration remains owned by:

```text
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
```

Detailed mode policy remains owned by:

```text
docs/validation/VALIDATION_MODES.md
```

When a lower-level document conflicts with a lock, the lock governs.

---

## 2. Pipeline objective

A GF Wordbench run must answer five questions.

1. **Was the requested validation configured correctly?**
2. **What source, scenario, and artifact set was actually validated?**
3. **What did GF and the framework report?**
4. **Which failures are local, downstream, ambiguous, or infrastructural?**
5. **Is the resulting evidence sufficient for the requested validation mode?**

The pipeline is not successful merely because a process exits.

The pipeline is successful only when every required criterion for the selected mode has trustworthy evidence.

---

## 3. Core pipeline rule

> Validation must preserve evidence before interpretation and must not declare success when required work is missing, skipped, incomplete, timed out, or unverified.

The pipeline must:

- build one resolved run configuration for one selected language context and one normative language target;
- create one owned run directory;
- use one GF executable and one compatibility decision per run;
- preserve raw stdout and stderr before parsing;
- represent every attempted stage with structured results;
- distinguish validation failure from framework error;
- continue independent work when useful;
- block dependent work when prerequisites are invalid;
- write deterministic machine-readable results;
- never rerun GF from report generation;
- never update gold files during ordinary validation;
- finalize reports and manifests atomically where supported.

---

## 4. Pipeline authority boundaries

### 4.1 GF authority

GF determines:

- GF syntax validity;
- type correctness;
- module loading;
- dependency resolution;
- `.gfo` generation;
- `.pgf` generation;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- native GF diagnostics.

### 4.2 GF Wordbench authority

GF Wordbench determines:

- requested validation mode;
- resolved project configuration;
- selected files and scenarios;
- GF request construction;
- process timeouts;
- evidence capture;
- static findings;
- normalized diagnostics;
- direct/downstream classification;
- gold comparison;
- previous-run comparison;
- required artifact checks;
- release gates;
- reports;
- overall validation status.

### 4.3 Validation profile authority

The selected language context determines:

- language identity;
- source roots;
- entrypoints;
- checkpoints;
- required scenarios;
- optional scenarios;
- expected gold files;
- expected PGF artifacts;
- project-specific release criteria.

The authoritative source is:

```text
<validation-profile-root>/project.toml
```

with supporting project specifications under:

```text
<validation-profile-root>/docs/
```

### 4.4 Portfolio boundary

`gf-portfolio` is an independent optional consumer of finalized public Wordbench artifacts.

The permitted direction is:

```text
gf-portfolio -> public versioned GF Wordbench artifacts
```

GF Wordbench must not:

- discover Portfolio workspaces during a validation run;
- aggregate several selected language contexts in one pipeline;
- import or call `gf-portfolio`;
- require Portfolio storage, configuration or runtime services;
- write Portfolio registry or aggregation state into Wordbench schemas.

A Portfolio ingestion failure cannot change the status or artifacts of a completed Wordbench run.

---

## 5. Pipeline inputs

A validation run receives four input classes.

### 5.1 Framework defaults

Owned by:

```text
app/config.py
```

Examples:

- default timeout values;
- default output root;
- encoding policy;
- report filenames;
- supported modes;
- safe process defaults.

Framework defaults must not contain active-language identifiers.

### 5.2 Validation profile configuration

Owned by:

```text
<validation-profile-root>/project.toml
```

Examples:

- project ID;
- language code;
- source directory;
- source glob;
- entrypoints;
- checkpoints;
- GF path additions;
- required scenarios;
- optional scenarios;
- release artifact expectations.

### 5.3 Local environment configuration

Examples:

- GF executable;
- RGL root;
- output root;
- temporary directory;
- optional local path overrides.

Local environment configuration is not portable resolved language identity.

### 5.4 Explicit invocation overrides

Supplied by CLI, GUI, or automation.

Examples:

- mode;
- target file;
- selected checkpoint;
- timeout override;
- maximum file count;
- diagnostic verbosity;
- previous-run comparison;
- explicit GF path;
- optional scenario filter.

An explicit override must be validated and recorded.

---

## 6. Configuration precedence

Canonical precedence:

```text
framework safe defaults
→ selected language context configuration
→ local environment configuration
→ persisted UI convenience state
→ explicit CLI/GUI invocation values
→ mode-enforced constraints
```

Mode-enforced constraints are applied last.

Examples:

- release mode may prohibit `no_compile`;
- release mode requires required scenarios;
- quick mode may require a target;
- checkpoint mode requires a declared checkpoint;
- diagnostic mode may enable expanded evidence.

### 6.1 Forbidden precedence

The following are prohibited:

- GUI state overriding resolved language identity;
- framework defaults overriding explicit project entrypoints;
- a scenario silently selecting another project;
- launcher scripts changing validation semantics;
- stale previous-run data filling missing current configuration;
- reports reconstructing configuration from prose;
- Portfolio state selecting, replacing or aggregating the selected language context.

---

## 7. Resolved run configuration

The configuration builder must produce one immutable logical `RunConfig`.

The resolved configuration must contain enough information to execute non-interactively.

At minimum:

```text
mode
project_id
project_root
source_root
entrypoints
checkpoints
required_scenarios
optional_scenarios
gf_executable
gf_version_policy
rgl_root
gf_path
output_root
target_file
selected_checkpoint
timeouts
selection_rules
diff_previous
no_compile
skip_version_probe
emit_cpu_stats
strict
```

Concrete field names may differ internally, but this information must remain available through the canonical run configuration.

### 7.1 Configuration immutability

After the run begins:

- stage code must not mutate the resolved configuration;
- GUI state changes must not alter the active run;
- environment rediscovery must not silently replace resolved values;
- project configuration changes on disk must not be partially adopted.

A run uses one configuration snapshot.

---

## 8. Canonical pipeline overview

The canonical logical pipeline is:

```text
VAL-000  accept invocation
VAL-010  load framework defaults
VAL-020  load and validate selected language context
VAL-030  resolve environment and GF toolchain
VAL-040  build resolved run configuration
VAL-050  create run directory and initial metadata
VAL-060  validate contracts and preconditions
VAL-070  probe GF version and capabilities
VAL-080  select files, modules, scenarios, and release targets
VAL-090  inventory and fingerprint selected source assets
VAL-100  run static source scans
VAL-110  compile selected GF modules
VAL-120  normalize compile diagnostics
VAL-130  classify direct, downstream, and ambiguous failures
VAL-140  execute selected GF scenarios
VAL-150  normalize scenario output and verify markers
VAL-160  compare scenario output with gold
VAL-170  build required PGF and other release artifacts
VAL-180  run artifact and release checks
VAL-190  compare with the previous compatible run
VAL-200  assemble the canonical RunResult
VAL-210  write machine and human reports
VAL-220  build and verify the artifact manifest
VAL-230  finalize the run atomically
VAL-240  return result and process exit status
```

The IDs define logical stages.

Implementations may group internal functions while preserving:

- stage ownership;
- dependency order;
- evidence;
- status semantics;
- required mode behavior.

---

## 9. Stage classes

Stages belong to one of six classes.

| Class | Purpose |
|---|---|
| `bootstrap` | establish trustworthy configuration and paths |
| `inventory` | identify and fingerprint validation subjects |
| `analysis` | scan and compile source assets |
| `scenario` | execute runtime GF behavior and compare expectations |
| `release` | build and verify release artifacts |
| `finalization` | aggregate, compare, serialize, manifest, and return |

Stage class is not a validation status.

---

## 10. Stage result contract

Every pipeline stage should produce a structured stage result.

Recommended fields:

```text
stage_id
stage_name
stage_class
required
started_at
finished_at
duration_ms
validation_status
execution_state
error_kind
message
warnings[]
blocked_by[]
input_count
output_count
artifact_paths[]
subject_results[]
```

### 10.1 Validation status

Canonical values:

```text
OK
FAIL
ERROR
SKIPPED
```

### 10.2 Execution state

Canonical values:

```text
completed
timed_out
cancelled
launch_failed
not_started
```

`not_started` may exist internally.

Persisted public schemas must use only values allowed by the schema lock.

### 10.3 Stage meaning

- `OK`: the stage executed and all required criteria passed;
- `FAIL`: the stage executed correctly but at least one validation criterion failed;
- `ERROR`: the framework could not execute or interpret the stage reliably;
- `SKIPPED`: the stage was intentionally not executed.

A required stage that is skipped prevents overall `OK`.

---

## 11. Subject-level results

Stages may produce results for:

```text
file
module
checkpoint
scenario
gold comparison
artifact
release gate
```

Every subject result must have a stable identity.

Examples:

```text
file:lib/src/french/NounFre.gf
module:NounFre
scenario:linearize
artifact:artifacts/pgf/French.pgf
gate:required-entrypoints
```

Stable identities support:

- deterministic ordering;
- previous-run comparison;
- downstream classification;
- report links;
- test assertions.

---

# 12. Bootstrap stages

## 12.1 VAL-000 — Accept invocation

**Owner**

```text
app/main_cli.py
app/main_gui.py
automation entrypoint
```

**Purpose**

Capture the user or automation request without implementing validation logic.

**Responsibilities**

- parse invocation;
- collect explicit values;
- reject malformed syntax;
- call the shared configuration builder;
- avoid direct calls to scanner, compiler, scenario runner, or reports.

**Output**

```text
InvocationRequest
```

**Failure policy**

Malformed invocation produces an invocation/configuration error before a run begins unless policy requires a minimal failed-run record.

---

## 12.2 VAL-010 — Load framework defaults

**Owner**

```text
app/config.py
app/bootstrap.py
```

**Purpose**

Load stable framework-level defaults.

**Required checks**

- allowed modes are defined;
- timeouts are positive;
- encoding is supported;
- artifact names are internally consistent;
- active-language paths are absent from framework defaults.

**Failure policy**

Invalid framework defaults are `ERROR`.

No language validation may continue.

---

## 12.3 VAL-020 — Load and validate selected language context

**Owner**

```text
project configuration loader
app/bootstrap.py
```

**Purpose**

Load `<validation-profile-root>/project.toml` and validate its schema and internal references.

**Required checks**

- schema ID and version;
- one selected language context identity;
- project root;
- source directory;
- source glob;
- entrypoints;
- checkpoints;
- scenario IDs;
- required scenario files;
- optional scenario files;
- scenario-to-gold declarations;
- expected release artifacts;
- project-relative path containment;
- duplicate IDs;
- unresolved placeholders in the selected language context.

**Failure policy**

A malformed or unsupported required project configuration is `ERROR`.

No source execution may continue.

**Non-mutation rule**

Normal validation must not rewrite `project.toml`.

---

## 12.4 VAL-030 — Resolve environment and GF toolchain

**Owner**

```text
app/bootstrap.py
GF toolchain adapter
GF path resolver
```

**Purpose**

Resolve local infrastructure required by the project.

**Required checks**

- GF executable;
- RGL root;
- output root;
- GF path components;
- working directories;
- write permissions;
- host platform behavior.

**Failure policy**

Missing required environment infrastructure is `ERROR`.

A missing optional tool produces a warning or `SKIPPED` optional stage.

---

## 12.5 VAL-040 — Build resolved run configuration

**Owner**

```text
app/bootstrap.py
```

**Purpose**

Combine all accepted inputs into one validated configuration snapshot.

**Required checks**

- mode-specific requirements;
- timeout bounds;
- target existence;
- checkpoint existence;
- scenario filter validity;
- incompatible flag combinations;
- strict-mode constraints;
- release requirements.

**Examples**

```text
quick + no target + no default target → ERROR
checkpoint + unknown checkpoint → ERROR
release + no_compile=true → ERROR
release + missing required scenario → ERROR
```

**Output**

```text
RunConfig
```

---

## 12.6 VAL-050 — Create run directory and initial metadata

**Owner**

```text
app/bootstrap.py
filesystem utilities
```

**Purpose**

Create an owned, collision-safe run directory before stage evidence is written.

**Canonical layout**

```text
run_<run-id>/
├── details/
├── raw/
│   ├── compile/
│   ├── scan/
│   └── scenarios/
└── artifacts/
    ├── gfo/
    ├── out/
    └── pgf/
```

Final report files are added during finalization.

**Required behavior**

- UTC-based run ID;
- deterministic collision suffix;
- no overwrite of an existing run;
- writable directories;
- initial master log metadata;
- configuration snapshot or equivalent evidence;
- cleanup only of temporary files owned by this run.

**Failure policy**

Failure to establish the run directory is `ERROR`.

No external tool execution may begin.

---

## 12.7 VAL-060 — Validate contracts and preconditions

**Owner**

```text
contract checker
project validator
audit orchestration
```

**Purpose**

Detect known structural drift before expensive GF work.

**Checks may include**

- documented provider files exist;
- configured entrypoints exist;
- checkpoints exist;
- required scenarios exist;
- gold mappings are valid;
- output paths remain inside owned roots;
- framework/project boundary is respected;
- no stale active-language identifiers remain after cloning;
- mode requirements are satisfiable;
- persisted schema versions are supported;
- GF command contracts can be built.

**Failure policy**

A structural problem that makes execution untrustworthy is `ERROR`.

A project validation defect that GF can still meaningfully diagnose may be `FAIL`, with dependent stages blocked.

---

# 13. Toolchain readiness

## 13.1 VAL-070 — Probe GF version and capabilities

**Owner**

```text
GF toolchain adapter
app/audit/compiler.py during migration
```

**Purpose**

Verify that the resolved GF executable can run and determine compatibility.

**Evidence**

```text
raw/gf_version.out.txt
raw/gf_version.err.txt
```

**Checks**

- process launch;
- finite timeout;
- raw stream capture;
- version extraction;
- minimum supported version;
- known incompatibilities;
- required command capabilities.

**Status rules**

| Condition | Stage status |
|---|---|
| supported recognized version | `OK` |
| accepted untested version | `OK` with warning |
| unsupported version | `ERROR` |
| launch failure | `ERROR` |
| timeout | `ERROR` |
| explicitly skipped where allowed | `SKIPPED` |

**Mode policy**

Release mode requires trustworthy version evidence.

A skipped release probe is allowed only when equivalent externally verified evidence is explicitly supplied by policy.

---

# 14. Selection and inventory

## 14.1 VAL-080 — Select validation subjects

**Owner**

```text
app/audit/file_selector.py
scenario registry selector
release target selector
```

**Purpose**

Resolve the exact set of files, modules, checkpoints, scenarios, and artifacts required by the selected mode.

**Inputs**

- mode;
- target file;
- selected checkpoint;
- project source rules;
- entrypoint registry;
- scenario registry;
- optional filters;
- maximum file count.

**Outputs**

```text
selected_files[]
excluded_files[]
selected_modules[]
selected_scenarios[]
selected_entrypoints[]
expected_artifacts[]
```

### 14.1.1 Deterministic ordering

- files: normalized project-relative path;
- checkpoints: configured order;
- scenarios: configured order;
- entrypoints: configured order;
- artifacts: normalized expected path.

### 14.1.2 Exclusion evidence

Every excluded candidate should record:

```text
path
reason
rule
```

### 14.1.3 Empty selection

An empty required selection is not success.

Examples:

- quick target missing: `ERROR`;
- checkpoint with no modules: `ERROR`;
- release with no entrypoints: `ERROR`;
- optional diagnostic filter matching nothing: `SKIPPED` or warning.

---

## 14.2 VAL-090 — Inventory and fingerprint source assets

**Owner**

```text
app/audit/fingerprint.py
inventory component
```

**Purpose**

Record the exact source assets used by the run.

**Fingerprint fields**

```text
size_bytes
hash_algorithm
hash
last_modified_utc
```

Canonical hash:

```text
SHA-256
```

**Assets to fingerprint**

- selected `.gf` files;
- selected `.gfs` scenarios;
- relevant input files;
- gold files used for comparison;
- `project.toml`;
- optionally project contract documents used as release evidence.

**Failure policy**

- missing required file: `ERROR` or `FAIL` according to whether configuration or project completeness is at fault;
- unreadable required file: `ERROR`;
- file changed during the run: `ERROR` in strict/release mode.

### 14.2.1 Snapshot consistency

The pipeline should detect source mutation during validation by comparing initial and final fingerprints when strict consistency is required.

A run must not combine pre-change and post-change source states silently.

---

# 15. Static analysis

## 15.1 VAL-100 — Run static source scans

**Owner**

```text
app/audit/scanner.py
```

**Purpose**

Detect suspicious GF source patterns before or alongside compilation.

**Current/foundation checks include**

- suspicious single-slash patterns;
- suspicious doubled-slash patterns;
- runtime string matching;
- untyped case blocks with string patterns;
- untyped table blocks with string patterns;
- trailing whitespace.

**Evidence**

```text
raw/scan/<safe-file-key>.scan.txt
```

**Result**

```text
ScanCounts
scan findings
scan log path
```

### 15.1.1 Scanner truth boundary

Static scans are heuristic.

They must not:

- claim GF syntax failure;
- claim type failure;
- replace compilation;
- alter source;
- generate release status alone unless the project explicitly defines a blocking static rule.

### 15.1.2 Per-file error isolation

If one file cannot be scanned:

- create an item-level `ERROR`;
- preserve available evidence;
- continue scanning independent files;
- do not discard the entire run unless selection integrity is lost.

### 15.1.3 Scan-only behavior

A `no_compile` diagnostic run may still scan.

Such a run cannot satisfy compile-dependent checkpoint or release criteria.

---

# 16. GF compilation

## 16.1 VAL-110 — Compile selected GF modules

**Owner**

```text
app/audit/compiler.py
app/utils/process_utils.py
```

**Purpose**

Obtain authoritative GF compile evidence for selected source modules.

**Per-file operation**

```text
prepare output directories
→ build structured GF request
→ execute with finite timeout
→ capture stdout and stderr
→ verify expected artifacts where applicable
→ return CompileSummary
```

**Evidence**

```text
raw/compile/<safe-file-key>.out.txt
raw/compile/<safe-file-key>.err.txt
artifacts/gfo/
artifacts/out/
```

### 16.1.1 Compile success

A file compile is `OK` only when all applicable conditions pass:

- process launched;
- no timeout;
- no cancellation;
- successful exit code;
- no recognized fatal diagnostic;
- required artifact exists.

### 16.1.2 Compile failure

A compile result is `FAIL` when GF executed correctly but rejected the source or failed a project validation criterion.

### 16.1.3 Compile error

A compile result is `ERROR` when:

- GF could not launch;
- the operation timed out under framework policy;
- output could not be captured;
- the result could not be interpreted;
- required process evidence is missing;
- source changed mid-operation.

### 16.1.4 No-compile policy

When explicitly allowed:

```text
validation_status = SKIPPED
diagnostic_class = skipped
```

A skipped compile is never represented as successful.

### 16.1.5 Per-file continuation

Compilation should continue across independent files after ordinary GF failures.

Infrastructure errors may trigger a circuit breaker when repeated execution is no longer meaningful.

---

## 16.2 Compile scheduling

Compilation may run:

- sequentially; or
- with bounded parallelism.

Pipeline semantics must remain equivalent.

### 16.2.1 Parallelism invariants

If parallel compilation is enabled:

- each file has unique evidence paths;
- GF artifact collisions are prevented;
- result serialization order remains deterministic;
- cancellation is coordinated;
- shared logs are not written unsafely;
- dependency classification waits for all required compile results;
- resource limits are configurable;
- release output is not produced concurrently into colliding paths.

Sequential execution is the safe baseline.

---

# 17. Diagnostic interpretation

## 17.1 VAL-120 — Normalize compile diagnostics

**Owner**

```text
app/audit/diagnostics.py
GF diagnostic utilities
```

**Purpose**

Convert raw GF process evidence into structured diagnostic information without destroying original output.

**Inputs**

- exit code;
- stdout path;
- stderr path;
- timeout state;
- launch error;
- expected artifacts;
- selected GF version.

**Outputs**

```text
error_kind
first_error
error_detail
fatal_diagnostics[]
diagnostic_locations[]
artifact_failure
interpretation_warnings[]
```

### 17.1.1 Canonical error kinds

```text
OK
OTHER
TYPE
SYNTAX
INTERNAL
TIMEOUT
SCRIPT
CONFIG
IO
TOOL
```

### 17.1.2 Interpretation failure

If raw evidence exists but parsing fails:

- preserve the raw evidence;
- use `ERROR` when reliable validation status cannot be determined;
- use a conservative fallback message;
- record `diagnostic_parse_failure`.

A parser failure must not transform a known non-zero GF exit into success.

---

# 18. Failure relationship classification

## 18.1 VAL-130 — Classify failures

**Owner**

```text
app/audit/classifier.py
```

**Purpose**

Distinguish the likely causal relationship between failing project items.

**Canonical diagnostic classes**

```text
ok
direct
downstream
ambiguous
noise
skipped
```

### 18.1.1 Inputs

The classifier may use:

- file/module identity;
- compile result;
- first error;
- diagnostic locations;
- failed provider set;
- configured dependency map;
- GF dependency evidence;
- selected order;
- blocked-by relationships.

### 18.1.2 Outputs

Each file result receives:

```text
diagnostic_class
is_direct
blocked_by[]
```

### 18.1.3 Separation rules

The classifier must not:

- execute GF;
- rewrite compile evidence;
- invent a blocker without evidence;
- turn infrastructure errors into language failures;
- classify optional excluded files as direct failures.

### 18.1.4 Conservative behavior

When evidence is insufficient:

```text
diagnostic_class = ambiguous
```

Ambiguity is preferable to unsupported certainty.

---

# 19. Scenario execution

## 19.1 VAL-140 — Execute selected GF scenarios

**Owner**

```text
app/audit/scenario_runner.py
app/utils/process_utils.py
```

**Purpose**

Validate runtime grammar behavior through native `.gfs` scripts.

**Inputs**

```text
scenario_id
script_path
required flag
resolved GF executable
GF path
working directory
timeout
required markers
forbidden markers
gold path
normalization version
expected artifacts
```

**Evidence**

```text
raw/scenarios/<scenario-id>.out.txt
raw/scenarios/<scenario-id>.err.txt
```

### 19.1.1 Scenario order

Scenarios execute in project configuration order.

Order must be preserved in:

- `scenario_results`;
- reports;
- regression comparison.

### 19.1.2 Scenario independence

A scenario may execute when its declared prerequisites pass.

A scenario must be blocked when its required entrypoint or PGF input is unavailable.

### 19.1.3 Required versus optional

- required failure affects overall status;
- optional failure is recorded and may warn;
- project release policy may promote an optional scenario to blocking;
- missing required scenario is not `SKIPPED` success.

### 19.1.4 Scenario process success

A zero exit code alone is insufficient.

Success also requires:

- required markers;
- no recognized fatal diagnostic;
- expected artifacts;
- valid normalized output;
- applicable assertions.

---

# 20. Scenario interpretation

## 20.1 VAL-150 — Normalize output and verify markers

**Owner**

```text
app/audit/normalization.py
app/audit/scenario_runner.py
```

**Purpose**

Create deterministic comparison output and prove required script sections executed.

**Derived output**

```text
raw/scenarios/<scenario-id>.out
```

**Checks**

- begin/end markers;
- final completion marker;
- marker order;
- duplicate section IDs;
- forbidden markers;
- normalization version;
- valid UTF-8 representation;
- bounded output.

### 20.1.1 Missing markers

A missing required marker causes:

- `FAIL` when a valid scenario assertion was not reached because the project failed;
- `ERROR` when the runner cannot determine whether execution was valid.

### 20.1.2 Normalization boundary

Normalization may remove approved unstable environment noise.

It must preserve:

- trees;
- strings;
- ambiguity;
- missing functions;
- morphology;
- meaningful Unicode;
- relevant diagnostics;
- evidence of incomplete execution.

---

## 20.2 VAL-160 — Compare with gold

**Owner**

```text
app/audit/gold.py
gold comparator
```

**Purpose**

Compare normalized actual output with reviewed expected output.

**Inputs**

```text
scenario_id
normalized_output_path
gold_path
normalization_version
comparison_policy
```

**Outputs**

```text
gold_match
diff_path
comparison_message
```

### 20.2.1 Exact comparison

Default exact comparison occurs after canonical newline normalization.

### 20.2.2 Missing gold

A missing required gold file is `FAIL`.

It is not created during validation.

### 20.2.3 Mismatch

A mismatch:

- preserves actual output;
- preserves expected output;
- writes a bounded diff;
- produces scenario `FAIL`;
- does not rewrite gold.

### 20.2.4 No-gold scenario

A scenario may use assertion markers without an exact gold.

In that case:

```text
gold_match = null
```

The scenario still requires its declared assertions.

---

# 21. Release artifact construction

## 21.1 VAL-170 — Build required PGF and release artifacts

**Owner**

```text
app/audit/pgf_builder.py
GF toolchain adapter
```

**Purpose**

Produce project-declared runtime artifacts.

**Primary artifact**

```text
artifacts/pgf/<grammar-name>.pgf
```

**Prerequisites**

- supported GF environment;
- required entrypoints available;
- required compilation prerequisites pass;
- release path is owned and collision-safe.

### 21.1.1 Success criteria

- process launched;
- no timeout;
- successful exit;
- no fatal diagnostic;
- expected PGF exists;
- PGF is non-empty;
- artifact identity is deterministic;
- manifest registration is possible.

### 21.1.2 Distinct stage rule

PGF build is distinct from per-file compilation.

Successful `.gfo` results do not prove release PGF success.

### 21.1.3 Mode behavior

- quick: normally skipped;
- checkpoint: optional unless checkpoint requires runtime artifact;
- diagnostic: optional;
- release: required when declared by project policy.

---

# 22. Release and artifact checks

## 22.1 VAL-180 — Run artifact and release checks

**Owner**

```text
release gate evaluator
artifact verifier
project validation policy
```

**Purpose**

Evaluate cross-stage completion criteria.

### 22.1.1 Framework-level checks

- every required stage has a result;
- no required stage is skipped;
- no required external process timed out;
- expected raw evidence exists;
- result counts are internally consistent;
- output paths remain inside the run root;
- canonical schemas can be serialized.

### 22.1.2 Project-level checks

Examples:

- required entrypoints compile;
- required checkpoints compile;
- required scenarios pass;
- required gold comparisons pass;
- missing-linearization policy passes;
- required PGF exists;
- required PGF contains intended language;
- accepted known issues are documented;
- project release criteria are satisfied.

### 22.1.3 Gate result

Each gate produces:

```text
gate_id
required
status
message
evidence[]
blocked_by[]
```

### 22.1.4 Release result

Release mode is `OK` only when every required gate is `OK`.

Warnings may exist without failing release only when policy explicitly permits them.

---

# 23. Previous-run comparison

## 23.1 VAL-190 — Compare with previous compatible run

**Owner**

```text
app/audit/diff.py
```

**Purpose**

Identify improvements, regressions, additions, and removals.

### 23.1.1 Previous-run selection

A previous run must be compatible by:

- resolved language identity;
- schema support;
- validation mode or comparison policy;
- normalization version where relevant;
- subject identity.

### 23.1.2 Diff inputs

```text
current RunResult
previous summary.json
```

Human reports are not parsed as the comparison source.

### 23.1.3 Change kinds

```text
unchanged
improved
regressed
new
removed
```

### 23.1.4 Missing previous run

No previous run is not an error.

The diff is empty and the report records that no compatible baseline was found.

### 23.1.5 Diff failure

A diff-loader or migration error:

- preserves current validation results;
- records a warning or finalization `ERROR` according to strict policy;
- must not discard the run.

Release policy may require a valid previous baseline for specific regression gates.

---

# 24. Canonical result assembly

## 24.1 VAL-200 — Assemble `RunResult`

**Owner**

```text
app/audit/result_model.py
```

**Purpose**

Construct the single canonical in-memory run representation.

**Inputs**

- resolved configuration;
- run paths;
- timestamps;
- GF version;
- stage results;
- file results;
- scenario results;
- release gate results;
- artifact inventory;
- diff entries;
- warnings;
- fatal framework errors.

**Responsibilities**

- calculate counts;
- calculate top errors;
- calculate overall status;
- validate internal invariants;
- sort deterministic collections;
- preserve references to evidence.

### 24.1.1 No report ownership

`result_model.py` must not:

- write reports;
- execute GF;
- scan source;
- load GUI state;
- update gold.

---

## 24.2 Count invariants

At minimum:

```text
files_included =
  files_ok + files_fail + files_error + files_skipped
```

```text
scenarios_seen =
  scenarios_ok + scenarios_fail + scenarios_error + scenarios_skipped
```

Counts must be non-negative integers.

A mismatch is a finalization `ERROR`.

---

# 25. Overall status aggregation

## 25.1 Canonical run statuses

```text
OK
FAIL
ERROR
```

`SKIPPED` is not a valid completed overall run status.

## 25.2 Aggregation priority

Recommended priority:

```text
ERROR > FAIL > OK
```

### 25.2.1 Overall `ERROR`

Use `ERROR` when:

- configuration is invalid;
- required infrastructure cannot execute;
- a required stage times out or cannot be interpreted;
- required evidence is missing;
- serialization or manifest integrity fails;
- source consistency is lost;
- framework invariants fail.

### 25.2.2 Overall `FAIL`

Use `FAIL` when:

- the pipeline executed reliably;
- required validation criteria did not pass;
- one or more required file/scenario/gold/release-gate results are `FAIL`;
- no higher-priority framework `ERROR` governs.

### 25.2.3 Overall `OK`

Use `OK` only when:

- all required stages executed;
- all required criteria passed;
- no required stage is skipped;
- final artifacts and schema checks pass;
- optional warnings are permitted by mode policy.

### 25.2.4 Optional failures

Optional-stage failure handling is declared by mode/project policy.

It must never be silently discarded.

---

# 26. Report generation

## 26.1 VAL-210 — Write machine and human reports

**Owners**

```text
app/reports/report_json.py
app/reports/report_md.py
app/reports/report_ai_ready.py
app/reports/report_logs.py
app/reports/report_details.py
```

**Canonical outputs**

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
details/
raw/master.log
raw/ALL_SCAN_LOGS.TXT
raw/ALL_LOGS.TXT
```

### 26.1.1 Source-of-truth rule

Reports derive from:

```text
RunResult
```

They must not rerun validation.

### 26.1.2 Report order

Recommended logical order:

1. finalize structured `RunResult`;
2. prepare `summary.json`;
3. prepare human reports;
4. prepare aggregate logs;
5. validate report content;
6. atomically publish staged report files;
7. build manifest from final bytes.

### 26.1.3 Best-effort versus release behavior

During development, secondary human-report failure may be recorded while preserving `summary.json`.

In strict/release mode:

- required report failures are finalization `ERROR`;
- machine summary and manifest are mandatory;
- missing required report artifacts cannot be ignored.

### 26.1.4 Report isolation

Report writers must not import:

```text
compiler
scanner
scenario_runner
process execution
```

---

# 27. Manifest construction

## 27.1 VAL-220 — Build and verify artifact manifest

**Owner**

```text
manifest writer
artifact verifier
```

**Purpose**

Prove which final files belong to the run and verify their integrity.

**Canonical output**

```text
manifest.json
```

### 27.1.1 Manifest entries

Each entry includes:

```text
path
role
media_type
required
size_bytes
sha256
created_by
```

### 27.1.2 Manifest scope

The manifest includes required final artifacts such as:

- `summary.json`;
- `summary.md`;
- `AI_READY.md`;
- `top_errors.txt`;
- raw logs;
- scenario normalized outputs;
- required `.gfo`;
- required `.pgf`;
- relevant diff artifacts.

The manifest does not hash itself.

### 27.1.3 Verification

Before publication:

- every required path exists;
- every path stays inside the run directory;
- paths are unique;
- file sizes match;
- hashes match;
- required summary artifact references agree;
- no forbidden symlink escape exists.

### 27.1.4 Failure and regeneration

If manifest verification changes overall status:

1. update the staged `RunResult`;
2. regenerate staged `summary.json` and dependent reports;
3. regenerate the manifest against the new final bytes;
4. verify again;
5. publish only when internally consistent.

This avoids a stale summary hash.

---

# 28. Atomic finalization

## 28.1 VAL-230 — Finalize the run

**Owner**

```text
audit orchestration
atomic filesystem utilities
```

**Purpose**

Publish a self-consistent completed run.

### 28.1.1 Two-phase finalization

Recommended model:

```text
phase 1: stage final files
phase 2: validate and atomically publish
```

### 28.1.2 Staging rules

- temporary files remain inside the run directory;
- temporary names cannot be mistaken for canonical artifacts;
- final files are validated before replacement;
- failed staging does not destroy earlier valid files;
- manifest reflects final canonical bytes.

### 28.1.3 Completion marker

The persisted schema may define a completion marker such as:

```text
.run_complete
```

when formally added to the persisted schema.

Until then, `manifest.json` plus valid `summary.json` defines a completed run.

No undocumented completion file may become required.

### 28.1.4 Interrupted finalization

An interrupted run must remain distinguishable from a completed run.

Automation must not treat a directory containing partial logs as a successful run.

---

# 29. Return and exit semantics

## 29.1 VAL-240 — Return result and process exit status

**Owner**

```text
app/audit/audit_core.py
app/main_cli.py
GUI controller
```

### 29.1.1 API return

The orchestration API returns:

```text
RunResult
```

It does not terminate the process.

### 29.1.2 CLI exit code

The CLI maps overall status to documented exit codes.

Recommended baseline:

```text
0 = overall OK
1 = validation FAIL
2 = invalid invocation or configuration
3 = framework/runtime ERROR
```

The canonical mapping is defined in:

```text
docs/reference/EXIT_CODES.md
```

### 29.1.3 GUI behavior

The GUI:

- receives `RunResult`;
- displays status and artifact links;
- does not reinterpret validation rules;
- does not call stage modules directly;
- restores idle state after completion or error.

---

# 30. Mode-to-stage matrix

Legend:

```text
R = required
O = optional/configurable
S = normally skipped
C = conditional prerequisite
```

| Stage | Quick | Checkpoint | Release | Diagnostic |
|---|:---:|:---:|:---:|:---:|
| config/project validation | R | R | R | R |
| environment resolution | R | R | R | R |
| GF version probe | O | R | R | O |
| file selection | R | R | R | R |
| fingerprinting | R | R | R | R |
| static scans | R | R | R | R |
| module compilation | R | R | R | O/R |
| diagnostic normalization | R | R | R | R when compile runs |
| failure classification | O/R | R | R | R |
| scenarios | O | R | R | O/R |
| marker verification | C | R | R | C |
| gold comparison | O | R when declared | R when declared | O |
| PGF build | S | O | R when declared | O |
| release gates | S | checkpoint gates | R | O |
| previous-run diff | O | R recommended | R | O |
| reports | R | R | R | R |
| manifest | O/R | R | R | R recommended |
| atomic finalization | R | R | R | R |

The detailed mode document may refine optional behavior without contradicting required pipeline invariants.

---

# 31. Blocking and continuation policy

GF Wordbench uses dependency-aware continuation.

## 31.1 Continue when useful

Continue after:

- one file fails GF compilation;
- one optional scenario fails;
- one static scan errors but other files remain readable;
- previous-run diff cannot load in non-strict mode;
- a human detail report fails in non-release mode.

The goal is to preserve broad diagnostic evidence.

## 31.2 Block dependent work

Block when:

- project configuration is invalid;
- GF cannot launch;
- source root is missing;
- a required entrypoint failed and a scenario requires it;
- normalized output cannot be produced for gold comparison;
- PGF build prerequisites failed;
- an expected artifact cannot be trusted;
- source changed during strict validation.

## 31.3 Abort the run

Abort scheduling new work when:

- run directory is unavailable;
- configuration identity is inconsistent;
- output containment is violated;
- repeated infrastructure failure makes remaining GF execution meaningless;
- user cancellation is received;
- a security boundary is violated.

Even after aborting execution, the pipeline should write a failed run summary when the run directory is trustworthy.

---

# 32. Dependency-aware blocked results

A blocked subject should receive:

```text
validation_status = SKIPPED
diagnostic_class = downstream or skipped
blocked_by = [stable subject IDs]
```

Use:

- `downstream` when a known failed provider caused the block;
- `skipped` when policy intentionally omitted the work.

A blocked required stage prevents overall `OK`.

Blocked work must not be counted as successful.

---

# 33. Error containment

## 33.1 Per-file containment

One file exception creates one structured file `ERROR` when possible.

## 33.2 Per-scenario containment

One scenario exception creates one structured scenario `ERROR` when possible.

## 33.3 Stage containment

A stage-level exception:

- records stage `ERROR`;
- preserves prior stage results;
- blocks declared dependents;
- permits independent finalization.

## 33.4 Fatal containment

A fatal orchestration exception should still attempt:

- finished timestamp;
- duration;
- master log;
- partial `RunResult`;
- machine summary;
- raw evidence references.

Finalization must not hide the original fatal error.

---

# 34. Cancellation model

Cancellation may originate from:

- GUI;
- CLI signal;
- automation controller;
- timeout policy.

On cancellation:

1. stop scheduling new subjects;
2. request termination of active owned processes;
3. capture partial output;
4. mark execution states;
5. block dependent stages;
6. assemble a non-successful result;
7. finalize available evidence.

A cancelled release can never be `OK`.

---

# 35. Source consistency and mutation

Normal validation is read-only with respect to project source assets.

The pipeline must not modify:

```text
<validation-profile-root>/project.toml
project/**/*.gf
project/**/*.gfs
<validation-profile-root>/validation/inputs/
<validation-profile-root>/validation/gold/
<validation-profile-root>/docs/
```

Explicit migration or gold-update commands are separate workflows.

### 35.1 Mid-run mutation

In strict/checkpoint/release validation, if a selected source changes after fingerprinting:

```text
overall_status = ERROR
```

unless the run is explicitly restarted from a new snapshot.

---

# 36. Determinism

Given identical:

- source bytes;
- project configuration;
- GF version;
- RGL revision;
- environment policy;
- validation mode;
- scenario inputs;
- normalization version;

the pipeline should produce equivalent structured validation results.

### 36.1 Deterministic collections

Sort or preserve declared order for:

- file results;
- scenarios;
- entrypoints;
- checkpoints;
- artifacts;
- top errors;
- diff entries.

### 36.2 Non-deterministic fields

Expected variability:

- run ID;
- timestamps;
- durations;
- absolute environment paths;
- random generation output.

These values may be normalized only under documented rules.

---

# 37. Logging model

## 37.1 Master log

`raw/master.log` records stage progression and major decisions.

Recommended events:

```text
run_started
configuration_resolved
stage_started
subject_started
subject_completed
stage_completed
warning
fatal_error
run_finalizing
run_completed
```

## 37.2 Structured logging

Human log text does not replace structured results.

Where practical, stage events should also carry structured fields.

## 37.3 Sensitive information

Logs must not include:

- credentials;
- private tokens;
- full environment dumps;
- secret command arguments.

---

# 38. Artifact lifecycle

Artifacts pass through four states.

```text
planned
created
verified
published
```

### 38.1 Planned

Declared by configuration or stage policy.

### 38.2 Created

File exists but integrity is not yet verified.

### 38.3 Verified

Existence, size, containment, and applicable semantics pass.

### 38.4 Published

The final manifest references the artifact.

A required artifact is not complete at `created`.

---

# 39. Pipeline invariants

The following are always required.

1. One resolved configuration per run.
2. One resolved language identity per run.
3. One run directory per run.
4. Raw external evidence precedes interpretation.
5. Static scan truth is separate from GF truth.
6. Compilation is separate from dependency classification.
7. Scenario execution is separate from gold comparison.
8. PGF build is separate from file compilation.
9. Reports do not execute validation.
10. Gold files are read-only during normal validation.
11. Required skipped work prevents success.
12. Required missing artifacts prevent success.
13. Timeouts are not reported as syntax errors.
14. Cancellation is not reported as success.
15. Deterministic identities and ordering are preserved.
16. Summary and manifest schemas remain versioned.
17. Final reports derive from one canonical `RunResult`.
18. A failed report cannot rewrite raw evidence.
19. The active language is not inferred from old runs.
20. Finalization does not silently overwrite another run.
21. A run never aggregates several selected language contexts.
22. GF Wordbench validation does not depend on `gf-portfolio`.

---

# 40. GF Audit compatibility baseline

GF Wordbench preserves the following established GF Audit responsibilities:

```text
build run paths
→ probe GF version
→ select files
→ scan each file
→ fingerprint each file
→ compile each file
→ build file results
→ classify failures
→ build run result
→ calculate counts and top errors
→ compare previous run
→ write reports
```

The Wordbench pipeline also defines:

```text
selected language context schema loading
four canonical modes
contract preflight
scenario selection and execution
marker verification
output normalization
gold comparison
PGF release build
release gates
manifest creation
two-phase finalization
canonical overall status
```

### 40.1 Compatibility rules

- legacy modes `file` and `all` are accepted only as documented input aliases;
- legacy summaries are read only through documented compatibility or migration rules;
- canonical writers emit the schemas and names defined by the persisted-schema lock;
- reports are never the sole source of run facts;
- scenario, manifest and release stages remain pipeline stages rather than report-generation side effects;
- orchestration remains centralized in `audit_core.py` or its designated application service;
- compatibility adapters must not change validation semantics or introduce a second pipeline.

---

# 41. Recommended orchestration pseudocode

```python
def run_validation(request: InvocationRequest) -> RunResult:
    context = bootstrap_run(request)

    try:
        preflight = validate_preconditions(context)
        if preflight.is_fatal:
            return finalize_failed_run(context, preflight)

        toolchain = probe_toolchain_if_required(context)
        selection = select_validation_subjects(context, toolchain)
        inventory = fingerprint_subjects(context, selection)

        scan_results = run_static_scans(context, selection.files)

        compile_results = run_compilation_stage(
            context,
            selection.files,
            prerequisites=[toolchain],
        )

        normalized_compile_results = normalize_compile_diagnostics(
            context,
            compile_results,
        )

        file_results = classify_file_failures(
            context,
            normalized_compile_results,
        )

        scenario_results = run_eligible_scenarios(
            context,
            selection.scenarios,
            file_results,
        )

        comparison_results = normalize_and_compare_scenarios(
            context,
            scenario_results,
        )

        release_artifacts = build_release_artifacts_if_required(
            context,
            selection.entrypoints,
            file_results,
            comparison_results,
        )

        gate_results = evaluate_mode_gates(
            context,
            file_results,
            comparison_results,
            release_artifacts,
        )

        run_result = build_run_result(
            context=context,
            inventory=inventory,
            file_results=file_results,
            scenario_results=comparison_results,
            release_gate_results=gate_results,
        )

        run_result.diff_entries = compare_previous_run(context, run_result)

        return finalize_run(context, run_result)

    except CancellationError as exc:
        return finalize_cancelled_run(context, exc)
    except Exception as exc:
        return finalize_fatal_run(context, exc)
```

This pseudocode defines responsibility flow, not exact Python signatures.

---

# 42. Required tests

Recommended test groups:

```text
tests/pipeline/
tests/contracts/
tests/schemas/
tests/integration/
```

## 42.1 Bootstrap tests

- missing project;
- unsupported project schema;
- invalid mode;
- missing target;
- unknown checkpoint;
- incompatible flags;
- unwritable output root;
- run ID collision.

## 42.2 Selection tests

- include/exclude behavior;
- deterministic file order;
- missing entrypoint;
- duplicate scenario ID;
- required scenario missing;
- max-file limit;
- active-language containment.

## 42.3 Stage tests

- scanner success and error;
- compiler success, failure, timeout, launch error;
- classifier direct/downstream/ambiguous;
- scenario marker success and failure;
- normalization failure;
- gold match and mismatch;
- PGF success and missing artifact;
- release-gate aggregation.

## 42.4 Continuation tests

- one file failure does not stop independent files;
- failed entrypoint blocks dependent scenario;
- optional scenario failure does not disappear;
- infrastructure circuit breaker;
- cancellation preserves partial evidence;
- fatal error still produces summary when possible.

## 42.5 Finalization tests

- deterministic result ordering;
- count invariants;
- atomic summary write;
- human report failure;
- manifest hash verification;
- manifest excludes itself;
- summary regeneration after manifest failure;
- interrupted run is not complete;
- no report launches GF;
- no normal run modifies gold.

## 42.6 Mode tests

Each mode must have a matrix test proving:

- required stages;
- optional stages;
- forbidden skips;
- overall status aggregation;
- CLI/GUI equivalence.

---

# 43. Pipeline drift indicators

Pipeline drift likely exists when:

- CLI and GUI execute different stages for equivalent inputs;
- one stage writes an artifact owned by another;
- a report launches GF;
- compilation and scenario execution resolve different GF paths;
- one required stage is absent from `RunResult`;
- `SKIPPED` required work still yields overall `OK`;
- a timeout becomes `FAIL` in one stage and `ERROR` in another without policy;
- scenario failure is mixed into file counts;
- gold comparison occurs before raw output capture;
- previous-run comparison parses `summary.md`;
- stage ordering depends on filesystem enumeration;
- an optional stage silently becomes required;
- release succeeds without manifest verification;
- a file changes after fingerprinting without detection;
- manifest hashes stale report bytes;
- a finalization error overwrites the original validation evidence;
- legacy mode names appear in canonical output;
- active-language paths appear in framework defaults.

Any drift indicator requires contract and test review.

---

# 44. Pipeline change workflow

A pipeline change is complete only when:

```text
[ ] Stage owner identified
[ ] Stage ID reviewed
[ ] Inputs and outputs documented
[ ] Dependencies documented
[ ] Mode matrix reviewed
[ ] Blocking behavior reviewed
[ ] Status aggregation reviewed
[ ] Result models updated
[ ] Persisted schema reviewed
[ ] Artifact ownership reviewed
[ ] Raw evidence behavior reviewed
[ ] Unit tests updated
[ ] Integration tests updated
[ ] Contract locks updated if needed
[ ] Migration behavior documented
[ ] Documentation links updated
```

Examples of pipeline contract changes:

- moving classification before all compile results exist;
- making an optional scenario required;
- changing which stage builds PGF;
- adding a new overall status;
- changing finalization order;
- changing the baseline selection policy;
- changing required release evidence;
- adding concurrency;
- changing cancellation behavior.

Such changes must not be made through an isolated code edit.

---

# 45. Related documentation

Read with:

```text
docs/00_START_HERE.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/EXECUTION_FLOW.md
docs/architecture/DATA_MODEL.md
docs/architecture/ARTIFACT_MODEL.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/VALIDATION_MODES.md
docs/validation/FILE_SELECTION.md
docs/validation/STATIC_SCANNING.md
docs/validation/COMPILATION_VALIDATION.md
docs/validation/SCENARIO_VALIDATION.md
docs/validation/REGRESSION_COMPARISON.md
docs/validation/RELEASE_GATES.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/reports/REPORTING_OVERVIEW.md
docs/reports/ARTIFACT_MANIFEST.md
<validation-profile-root>/project.toml
<validation-profile-root>/docs/VALIDATION_SPEC__PROJECT_DOCS.md
<validation-profile-root>/docs/RELEASE_CRITERIA__PROJECT_DOCS.md
```

---

# 46. Pipeline rule

The validation pipeline is a chain of evidence, not a chain of assumptions.

> Each stage must consume documented inputs, produce structured results, preserve its evidence, respect dependency boundaries, and contribute to one deterministic overall decision.

A run is complete only when the requested validation has been executed or explicitly blocked, every required result is represented, final artifacts are internally consistent, and the reason for the overall status can be traced back to preserved evidence.
