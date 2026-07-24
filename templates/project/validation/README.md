# GF Wordbench Project Template — Validation

**Document ID:** `GF-WB-TEMPLATE-PROJECT-VALIDATION-README`  
**Document role:** Normative project template  
**Decision status:** Accepted template contract  
**Implementation status:** Template available; active-project implementation depends on initialization  
**Verification status:** Requires placeholder, source, contract and validation checks after initialization  
**Applies to:** `templates/project/validation/` and every active project created from it  
**Template owner:** GF Wordbench maintainers  
**Project owner:** `<PROJECT_OWNER>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**GF suffix:** `<GF_SUFFIX>`  
**Target path:** `templates/project/validation/README.md`  
**Document version:** `1.0.0`  
**Last reviewed:** `<YYYY-MM-DD>`

---

## 1. Purpose

This directory is the validation-asset root for one GF project.

It contains the project-owned inputs and expectations used by GF Wordbench to prove that the language implementation behaves as intended.

Canonical subdirectories:

```text
templates/project/validation/
├── README.md
├── scenarios/
│   └── README.md
├── inputs/
│   └── README.md
└── gold/
    └── README.md
```

After project initialization, the active copy is:

```text
project/validation/
├── README.md
├── scenarios/
├── inputs/
└── gold/
```

This root README defines:

- the responsibilities of each validation subdirectory;
- the relationship between configuration, scenarios, inputs, golds, checkpoints, entrypoints, and releases;
- the validation evidence model;
- authoring and review workflows;
- required project initialization steps;
- anti-drift rules;
- release-readiness requirements.

It does not define the complete validation matrix.

The authoritative project validation design belongs in:

```text
project/docs/VALIDATION_SPEC.md
```

Feature-to-evidence coverage belongs in:

```text
project/docs/TEST_COVERAGE_MATRIX.md
```

---

## 2. Template-use rule

This file is a reusable template.

When creating an active GF project:

1. copy `templates/project/` to the active project location;
2. replace every required placeholder;
3. configure entrypoints and checkpoints in `project/project.toml`;
4. register required and optional scenarios;
5. create or remove scenario examples;
6. create required input files;
7. create reviewed gold files where exact regression comparison is appropriate;
8. align `VALIDATION_SPEC.md`;
9. align `TEST_COVERAGE_MATRIX.md`;
10. align `INTERFILE_CONTRACT_LOCK.md`;
11. run a baseline diagnostic validation;
12. record unresolved gaps in `STATUS_LEDGER.md`.

The initialized active-project copy must not retain unresolved required placeholders such as:

```text
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<ENTRYPOINT>
<SCENARIO_ID>
<INPUT_FILE>
<GOLD_FILE>
```

---

## 3. Core validation rule

> Project validation assets must prove declared project behavior through GF execution, preserved evidence, stable assertions, and reviewed expectations.

A project is not validated merely because:

- individual source files exist;
- the top entrypoint compiles once;
- a scenario process exits zero;
- a gold file exists;
- no static warning appears;
- a previous run passed.

Validation must prove the current source state against the current project contract.

---

## 4. Authority model

### 4.1 GF authority

GF is authoritative for:

```text
source syntax
type checking
module resolution
compilation
grammar loading
parsing
linearization
generation
morphology
GF-native introspection
PGF construction
GF-native diagnostics
```

### 4.2 Active project authority

The active project is authoritative for:

```text
project identity
source root
entrypoints
checkpoints
required scenarios
optional scenarios
input data
gold expectations
release criteria
known accepted gaps
expected PGF
```

### 4.3 GF Wordbench authority

GF Wordbench is authoritative for:

```text
resolved run configuration
validation mode
file selection
GF process requests
timeouts and cancellation
stdout/stderr capture
marker verification
normalization
gold comparison
result aggregation
reports
manifest
overall validation status
```

### 4.4 Validation assets do not execute themselves

Files under `project/validation/` are inputs to the shared validation pipeline.

They must not contain framework-specific code that bypasses:

```text
bootstrap
RunConfig
run_audit
scenario runner
gold comparator
manifest writer
```

---

## 5. Related project files

```text
project/project.toml
project/docs/00_PROJECT_START_HERE.md
project/docs/LANGUAGE_OVERVIEW.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA.md
project/docs/RESEARCH_EVIDENCE.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Framework references:

```text
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/VALIDATION_MODES.md
docs/validation/FILE_SELECTION.md
docs/validation/STATIC_SCANNING.md
docs/validation/COMPILATION_VALIDATION.md
docs/validation/SCENARIO_VALIDATION.md
docs/validation/REGRESSION_COMPARISON.md
docs/validation/RELEASE_GATES.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/gf/GF_TOOLCHAIN_BOUNDARY.md
docs/reports/REPORTING_OVERVIEW.md
```

---

# 6. Validation directory responsibilities

## 6.1 `validation/scenarios/`

Owns native `.gfs` scripts.

A scenario:

- loads a declared GF entrypoint;
- executes bounded GF operations;
- emits stable markers;
- uses registered inputs;
- produces raw stdout and stderr;
- may produce normalized output;
- may be compared with one reviewed gold file.

Detailed guide:

```text
validation/scenarios/README.md
```

---

## 6.2 `validation/inputs/`

Owns project-controlled external data consumed by scenarios.

Examples:

```text
sentences
abstract trees
lemmas
feature matrices
lexical lists
expected identifiers
small corpora
bounded test inventories
```

Detailed guide:

```text
validation/inputs/README.md
```

---

## 6.3 `validation/gold/`

Owns reviewed normalized expected output.

A gold file:

- belongs to one scenario or an explicitly selected scenario variant;
- records the scenario identity;
- records the normalization version;
- is version-controlled;
- is read-only during normal validation;
- changes only through explicit review.

Detailed guide:

```text
validation/gold/README.md
```

---

## 6.4 Generated artifacts do not belong here

Do not store generated run output in `project/validation/`.

Generated evidence belongs under a run directory:

```text
run_<run-id>/
```

Examples:

```text
summary.json
summary.md
AI_READY.md
manifest.json
raw/scenarios/*.out.txt
raw/scenarios/*.err.txt
raw/scenarios/*.out
details/*
artifacts/*
```

The validation directory contains source-controlled project assets, not transient run results.

---

# 7. Canonical project validation flow

```text
project.toml
→ resolve validation mode
→ validate project configuration
→ select files/checkpoints
→ static scan
→ compile GF providers and entrypoints
→ execute registered .gfs scenarios
→ preserve stdout/stderr
→ verify required markers
→ normalize scenario output
→ compare with gold when configured
→ verify generated artifacts
→ classify direct/downstream/ambiguous results
→ evaluate release gates
→ write reports and manifest
```

Each step uses current-run evidence.

Stale output must not satisfy a new run.

---

# 8. Project configuration relationship

`project/project.toml` is the authoritative registry for validation execution.

It must define or resolve:

```text
project identity
source directory
source selection
GF path additions
entrypoints
checkpoints
required scenarios
optional scenarios
release entrypoints
expected artifacts
```

Scenario, input, and gold files must agree with configuration.

This README must not become a second executable registry.

---

# 9. Validation-mode model

The canonical modes are:

```text
quick
checkpoint
release
diagnostic
```

Legacy values:

```text
file
all
```

may be accepted by compatibility readers but must not appear in canonical project configuration.

---

## 9.1 Quick mode

Purpose:

```text
fast feedback for one target or a small change
```

Typical project evidence:

- target file scan;
- target compile;
- minimal dependent entrypoint compile;
- one configured smoke scenario;
- optional previous compatible quick-run comparison.

Quick mode may omit broad optional scenarios.

It must not claim release readiness.

---

## 9.2 Checkpoint mode

Purpose:

```text
prove one declared development layer and its required consumers
```

Examples:

```text
morphology
paradigms
noun syntax
verb syntax
sentence syntax
structural vocabulary
lexicon
grammar entrypoint
```

A checkpoint should include:

```text
provider modules
direct consumers
downstream entrypoint proof
required scenarios
gold comparisons when applicable
```

Checkpoint order should follow dependency order.

---

## 9.3 Release mode

Purpose:

```text
evaluate every declared release criterion
```

Release mode requires, as configured:

```text
all required checkpoints
all required entrypoints
all required scenarios
all required gold comparisons
missing-function inspection
PGF build
expected artifact checks
manifest verification
known-issue review
```

Release mode must not allow required stages to be silently disabled.

Normal release validation never updates gold.

---

## 9.4 Diagnostic mode

Purpose:

```text
collect broad evidence for investigation
```

Diagnostic mode may include:

```text
broad file selection
optional scenarios
extended details
introspection
generation
additional logs
previous-run comparison
scan-only investigation
```

Diagnostic mode remains bounded and must use finite timeouts.

It does not bypass project contracts.

---

# 10. Project validation contracts

The following project-level contracts should be present in:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

## 10.1 Scenario registry

```text
PIFC-SCENARIO-001
```

Relationship:

```text
project.toml + scenarios directory
→ GF Wordbench scenario discovery
```

## 10.2 Scenario to entrypoint

```text
PIFC-SCENARIO-002
```

Relationship:

```text
.gfs scenario
→ declared GF entrypoint
```

## 10.3 Scenario to inputs

```text
PIFC-SCENARIO-003
```

Relationship:

```text
input file
→ scenario consumers
```

## 10.4 Scenario to output markers

```text
PIFC-SCENARIO-004
```

Relationship:

```text
scenario script
→ marker verifier
```

## 10.5 Scenario to gold

```text
PIFC-GOLD-001
```

Relationship:

```text
normalized scenario output
→ reviewed gold
```

## 10.6 Implementation change to gold update

```text
PIFC-GOLD-002
```

Relationship:

```text
intentional behavior change
→ explicit reviewed gold update
```

## 10.7 Validation to evidence

```text
PIFC-ARTIFACT-003
```

Relationship:

```text
validation run
→ reports, logs, artifacts, manifest
```

## 10.8 Checkpoints to release

```text
PIFC-RELEASE-001
```

## 10.9 Required scenarios to release status

```text
PIFC-RELEASE-002
```

## 10.10 Known issues to release decision

```text
PIFC-RELEASE-003
```

---

# 11. Evidence model

GF Wordbench distinguishes:

```text
raw evidence
derived evidence
structured results
human reports
integrity metadata
```

## 11.1 Raw evidence

Examples:

```text
GF stdout
GF stderr
scanner log
process metadata
generated GF artifact
```

Raw evidence must be preserved before interpretation.

## 11.2 Derived evidence

Examples:

```text
normalized scenario output
gold diff
diagnostic grouping
direct/downstream classification
previous-run diff
```

Derived evidence must point back to its source evidence.

## 11.3 Structured results

Canonical machine source:

```text
summary.json
```

## 11.4 Human reports

Examples:

```text
summary.md
AI_READY.md
top_errors.txt
details/*
```

Reports are views.

They must not execute validation.

## 11.5 Integrity metadata

Canonical source:

```text
manifest.json
```

The manifest verifies final artifact existence, size, role, and hash.

---

# 12. Validation status model

Validation status:

```text
OK
FAIL
ERROR
SKIPPED
```

Execution state:

```text
completed
timed_out
cancelled
launch_failed
```

Error kind:

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

Diagnostic class:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

These are separate axes.

Examples:

```text
GF syntax defect:
  validation_status = FAIL
  execution_state = completed
  error_kind = SYNTAX
  diagnostic_class = direct

Scenario blocked by failed entrypoint:
  validation_status = SKIPPED
  diagnostic_class = downstream
  blocked_by = [entrypoint]

Process timeout:
  validation_status = ERROR
  execution_state = timed_out
  error_kind = TIMEOUT
```

---

# 13. Required versus optional validation

## 13.1 Required evidence

A required item:

- must exist;
- must be discoverable;
- must run when its mode requires it;
- must not be silently skipped;
- blocks release on failure;
- must have explicit prerequisites;
- must produce traceable evidence.

## 13.2 Optional evidence

An optional item:

- remains visible;
- may be excluded by mode;
- must not be counted as successful when not run;
- must not become release-critical without configuration change.

## 13.3 Missing required asset

Examples:

```text
missing required scenario
missing required input
missing required gold
missing release entrypoint
missing expected PGF
```

A missing required asset is a configuration, validation, or artifact failure as defined by its contract.

It is never an automatic pass.

---

# 14. Scenario inventory

Maintain the authoritative scenario inventory in:

```text
project/docs/VALIDATION_SPEC.md
```

or one designated source referenced by it.

Recommended fields:

| Scenario ID | Script | Required | Modes | Entrypoint | Inputs | Gold/assertion | Owner | Status |
|---|---|---:|---|---|---|---|---|---|
| `<SCENARIO_ID>` | `<FILE>.gfs` | yes/no | quick/checkpoint/release/diagnostic | `<ENTRYPOINT>` | `<FILES_OR_NONE>` | `<GOLD_OR_ASSERTION>` | `<OWNER>` | `<STATUS>` |

Do not maintain conflicting scenario tables in multiple documents.

---

# 15. Checkpoint inventory

Maintain a checkpoint table.

| Checkpoint ID | Purpose | Modules | Prerequisites | Required scenarios | Release required | Owner | Status |
|---|---|---|---|---|---:|---|---|
| `<CHECKPOINT_ID>` | `<PURPOSE>` | `<MODULES>` | `<IDS>` | `<SCENARIOS>` | yes/no | `<OWNER>` | `<STATUS>` |

Required checkpoints must be present in `project.toml`.

---

# 16. Entry-point inventory

| Role | Module | Required modes | Scenarios | Expected artifact | Status |
|---|---|---|---|---|---|
| Concrete grammar | `<CONCRETE_ENTRYPOINT>` | checkpoint/release/diagnostic | `<IDS>` | `.gfo` | `<STATUS>` |
| Syntax/API | `<SYNTAX_OR_API_ENTRYPOINT>` | `<MODES>` | `<IDS>` | `.gfo`/optional PGF | `<STATUS>` |
| Language | `<LANGUAGE_ENTRYPOINT>` | release/diagnostic | `<IDS>` | `.gfo` | `<STATUS>` |
| Release | `<RELEASE_ENTRYPOINT>` | release | `<IDS>` | `<EXPECTED_PGF>` | `<STATUS>` |

Remove non-applicable rows.

---

# 17. Validation root initialization

When initializing an active project, complete:

```text
project/validation/README.md
project/validation/scenarios/README.md
project/validation/inputs/README.md
project/validation/gold/README.md
```

Then create actual assets.

Do not leave the active directories containing only generic documentation when release criteria require executable validation.

---

# 18. Scenario authoring overview

Every registered scenario must have:

```text
stable scenario ID
native .gfs script
declared purpose
declared entrypoint
required/optional status
finite timeout
stable markers
bounded operations
registered inputs
normalization policy
gold/assertion policy
owner
coverage mapping
```

Detailed requirements belong in:

```text
validation/scenarios/README.md
```

---

# 19. Input authoring overview

Every registered input must have:

```text
stable project-relative path
purpose
format
encoding
consumer scenarios
ordering semantics
blank-line semantics
comment syntax
owner
release significance
```

Detailed requirements belong in:

```text
validation/inputs/README.md
```

---

# 20. Gold authoring overview

Every gold-backed scenario must have:

```text
one authoritative gold file
matching scenario ID
matching normalization version
reviewed expected output
source-control history
explicit update workflow
```

Detailed requirements belong in:

```text
validation/gold/README.md
```

---

# 21. Scenario marker requirements

A required scenario should emit stable begin/end markers.

Conceptual syntax:

```text
GF_WORDBENCH::<scenario-id>::BEGIN
GF_WORDBENCH::<scenario-id>::SECTION::<section-id>::BEGIN
GF_WORDBENCH::<scenario-id>::SECTION::<section-id>::END
GF_WORDBENCH::<scenario-id>::END
```

The exact active marker syntax is governed by:

```text
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
project/docs/VALIDATION_SPEC.md
```

A missing required end marker is a scenario failure.

---

# 22. Scenario execution requirements

GF Wordbench executes scenarios using GF.

A scenario request includes:

```text
scenario ID
script path
GF executable
ordered GF arguments
working directory
GF path
stdin bytes
timeout
expected markers
expected artifacts
normalization version
gold path
```

The scenario runner must preserve:

```text
stdout
stderr
exit code
execution state
duration
generated artifacts
```

---

# 23. Raw scenario paths

For a launched scenario:

```text
raw/scenarios/<scenario-id>.out.txt
raw/scenarios/<scenario-id>.err.txt
```

Normalized output:

```text
raw/scenarios/<scenario-id>.out
```

Gold:

```text
project/validation/gold/<scenario-id>.gold
```

Diff path is run-owned and defined by the artifact/report model.

Project assets must not be written into `raw/`.

---

# 24. Normalization

Normalization occurs after raw evidence is preserved.

Allowed examples:

```text
CRLF → LF
ANSI escape removal
approved absolute-path replacement
trailing-space removal
approved unstable-duration replacement
```

Forbidden examples:

```text
removing GF errors
removing abstract trees
changing linearized strings
sorting meaningful output
removing ambiguity
changing punctuation
changing Unicode distinctions
inventing missing markers
```

Normalization rules are versioned.

---

# 25. Gold comparison

Comparison order:

```text
raw output
→ normalized output
→ gold comparison
→ structured result
```

A mismatch is a validation failure.

A comparator crash, unreadable file, or incompatible normalization version is an error.

A missing required gold is not a pass.

---

# 26. Gold-update rule

Normal validation is read-only.

It must never modify:

```text
project/validation/gold/
```

Gold updates require an explicit operation and review.

Planned command:

```text
gf-wordbench gold update <scenario-id>
```

An update must:

1. run the current scenario;
2. verify complete markers;
3. normalize output;
4. show or store the diff;
5. require explicit approval;
6. write atomically;
7. update relevant documentation;
8. receive source-control review.

---

# 27. Input-data rule

Inputs used for release validation must be version-controlled.

They must not include:

```text
secrets
personal data without approval
developer-local paths
unlicensed corpora
unstable generated IDs
machine-specific encodings
```

Large corpora require a separate data-management and licensing policy.

The validation template is intended for small, reviewable, deterministic assets.

---

# 28. Compilation validation

Scenario validation does not replace compilation.

Required compile evidence may include:

```text
provider module compile
direct consumer compile
checkpoint compile
entrypoint compile
clean release compile
PGF build
```

A scenario blocked by a failed entrypoint must remain downstream.

Do not patch a scenario to load a lower temporary module merely to avoid an entrypoint failure.

---

# 29. Static scanning

GF Wordbench may run heuristic source scans before compilation.

Static findings may identify:

```text
unsafe string matching
suspicious slash syntax
untyped patterns
trailing whitespace
project-specific anti-patterns
```

Static findings are not GF compiler truth.

A clean scan does not prove successful compilation.

---

# 30. Causal classification

Likely root failures should be classified separately from cascades.

Examples:

```text
Morphology provider fails:
  provider = direct
  paradigms = downstream
  lexicon = downstream
  entrypoint = downstream
  scenario = blocked/downstream
```

When evidence is insufficient:

```text
diagnostic_class = ambiguous
```

Do not mark every failing file as an independent root.

---

# 31. Previous-run comparison

A compatible previous run may be used to identify:

```text
unchanged
improved
regressed
new
removed
```

Compatibility should require:

```text
same project identity
supported summary schema
different run ID
compatible comparison policy
available complete summary
```

Previous-run comparison must not alter current validation results.

---

# 32. Artifact verification

Required generated artifacts may include:

```text
.gfo
.pgf
scenario output
gold diff
summary.json
summary.md
AI_READY.md
raw logs
manifest.json
```

Artifact existence alone may be insufficient.

Verification may also require:

```text
non-empty file
expected path
current-run source fingerprint
correct role
manifest entry
SHA-256 match
```

Stale artifacts must not satisfy a new release.

---

# 33. Release gates

A project release should require:

```text
[ ] Project configuration is valid
[ ] No required placeholder remains
[ ] Required source files exist
[ ] Required checkpoints compile
[ ] Required entrypoints compile
[ ] Required scenarios exist
[ ] Required inputs exist
[ ] Required scenarios pass
[ ] Required markers complete
[ ] Required gold files exist
[ ] Required gold comparisons match
[ ] Missing-function checks satisfy policy
[ ] Known issues are reviewed
[ ] Required PGF builds
[ ] Required artifacts exist
[ ] Manifest verifies
[ ] Normal validation did not alter source or gold
[ ] Release evidence identifies GF and source versions
```

The authoritative release checklist belongs in:

```text
project/docs/RELEASE_CRITERIA.md
```

---

# 34. Known issues and accepted gaps

A validation gap must be recorded when:

```text
scenario missing
gold missing
input incomplete
checkpoint disabled
GF-version output unstable
feature only manually tested
temporary fallback remains
generation is not bounded
entrypoint is blocked
PGF build is unavailable
```

Record in:

```text
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
```

Every accepted issue must state:

```text
owner
scope
evidence
release impact
replacement/fix plan
review date
```

Undocumented warnings must not be silently accepted.

---

# 35. Coverage matrix

`TEST_COVERAGE_MATRIX.md` should map features to evidence.

Recommended columns:

| Feature/contract | Provider | Compile checkpoint | Scenario | Input | Gold/assertion | Required mode | Status |
|---|---|---|---|---|---|---|---|
| `<FEATURE>` | `<MODULE>` | `<ID>` | `<ID>` | `<FILE_OR_NONE>` | `<FILE_OR_RULE>` | `<MODE>` | `<STATUS>` |

A feature is not release-proven merely because one neighboring feature is covered.

---

# 36. Manual validation

Manual validation is permitted only when automation is currently impossible or inappropriate.

A manual criterion must identify:

```text
owner
procedure
environment
evidence location
expected result
review date
release impact
automation plan or reason none is planned
```

Manual evidence must not be represented as an automated pass.

---

# 37. Validation ownership

Complete the project ownership table.

| Area | Owner | Reviewers | Required evidence |
|---|---|---|---|
| Project configuration | `<OWNER>` | `<REVIEWERS>` | config check |
| Compile checkpoints | `<OWNER>` | `<REVIEWERS>` | compile results |
| Scenarios | `<OWNER>` | `<REVIEWERS>` | scenario results |
| Inputs | `<OWNER>` | `<REVIEWERS>` | format/consumer review |
| Gold | `<OWNER>` | `<REVIEWERS>` | diff approval |
| Release entrypoint | `<OWNER>` | `<REVIEWERS>` | compile/PGF |
| Known issues | `<OWNER>` | `<REVIEWERS>` | release review |
| Validation docs | `<OWNER>` | `<REVIEWERS>` | contract check |

---

# 38. Validation asset naming

## 38.1 Scenario IDs

Recommended:

```text
lowercase-kebab-case
```

## 38.2 Scenario files

Recommended:

```text
<scenario-id>.gfs
```

## 38.3 Gold files

Recommended:

```text
<scenario-id>.gold
```

## 38.4 Input files

Use descriptive stable names:

```text
parse-basic.sentences.txt
noun-paradigms.tsv
trees.gfexpr
lexicon-smoke.txt
```

Actual suffixes must match the documented input format.

Avoid temporary names:

```text
test1
new
final-final
copy
tmp
```

---

# 39. Encoding and newline policy

Canonical project text assets use:

```text
UTF-8 without BOM
LF
```

Readers may tolerate CRLF.

Writers and reviewed project assets should use LF.

Line-oriented files should end with a final newline.

Language-specific Unicode must remain exact.

Do not replace diacritics or non-ASCII letters for tool convenience.

---

# 40. Determinism

Validation assets should produce deterministic evidence given the same:

```text
source bytes
project configuration
GF version
RGL revision
scenario inputs
normalization version
platform policy
```

Potential instability must be controlled:

```text
timestamps
durations
absolute paths
random generation
filesystem ordering
diagnostic ordering
free variant ordering
```

Do not normalize away linguistic differences to achieve determinism.

---

# 41. Portability

Project validation assets must not hard-code:

```text
C:\...
/home/...
developer usernames
GF executable path
RGL installation path
run directory
IDE working directory
```

Use project-relative paths and configured GF path resolution.

Raw external diagnostics may contain native paths.

Normalized output may replace approved non-semantic paths.

---

# 42. Security

`.gfs` scripts are executable inputs.

Validation assets must not:

```text
invoke operating-system shells
delete arbitrary files
write outside owned run directories
read secrets
dump the complete environment
perform network requests
spawn unrelated processes
modify source files
modify gold during normal validation
```

Input data must not contain secrets.

Untrusted external datasets require review before inclusion.

---

# 43. Performance and bounds

Required validation must be bounded.

Bound:

```text
process timeout
generation count
generation depth
parse alternatives
input size
log size
artifact size when applicable
```

A scenario that grows without a known limit cannot be required for release.

Diagnostic scenarios may use larger bounds but still require finite limits.

---

# 44. Validation result interpretation

## 44.1 `OK`

Every required criterion for the item passed.

## 44.2 `FAIL`

GF executed reliably, but a project expectation failed.

Examples:

```text
GF compile diagnostic
missing required parse
unexpected linearization
gold mismatch
missing required function
```

## 44.3 `ERROR`

The framework could not evaluate the criterion reliably.

Examples:

```text
GF launch failure
timeout
unreadable input
invalid configuration
capture failure
normalization failure
manifest failure
```

## 44.4 `SKIPPED`

The item was not executed.

Reasons must be explicit:

```text
not selected
optional for mode
blocked by prerequisite
unsupported capability
cancelled before scheduling
```

Required skipped items prevent release success.

---

# 45. Run artifact navigation

After validation, inspect in this order:

1. `summary.md`;
2. `AI_READY.md`;
3. `top_errors.txt`;
4. direct-failure detail files;
5. individual raw stdout/stderr;
6. normalized scenario output;
7. gold diff;
8. `summary.json`;
9. `manifest.json`.

Automation should use:

```text
summary.json
manifest.json
```

Automation must not parse human prose for run success.

---

# 46. Baseline validation

After initializing the project, run a diagnostic baseline.

Record:

```text
baseline run ID
date
GF Wordbench version
GF version
RGL revision
project source revision
project identity
overall status
direct failures
blocked areas
required scenario status
PGF status
known accepted gaps
```

Store the baseline reference in the project’s designated status or release documentation.

---

# 47. Validation asset change classes

## 47.1 Internal compatible change

Examples:

```text
clarify README text
reformat comments
add non-semantic input comments
improve an optional diagnostic excerpt
```

Still validate that no executable behavior changed.

## 47.2 Compatible extension

Examples:

```text
add optional scenario
add optional input
add additional bounded section
add optional gold-backed coverage
```

Required:

```text
configuration review
coverage update
contract update when cross-file
tests
documentation
```

## 47.3 Breaking validation change

Examples:

```text
rename scenario ID
change required entrypoint
change input format
remove required scenario
change required marker
change normalization semantics
rename required gold
change release gate
change expected artifact
```

Required:

1. identify contract IDs;
2. list providers and consumers;
3. update configuration;
4. update scenarios;
5. update inputs;
6. update gold intentionally;
7. update validation spec;
8. update coverage matrix;
9. update interfile lock;
10. record the decision;
11. run checkpoint and release validation.

---

# 48. Adding a scenario

```text
[ ] Assign a unique ID
[ ] Create the .gfs file
[ ] Register it in project.toml
[ ] Declare required/optional status
[ ] Declare validation modes
[ ] Declare entrypoint
[ ] Declare timeout
[ ] Declare inputs
[ ] Declare required markers
[ ] Declare expected artifacts
[ ] Declare normalization version
[ ] Declare gold/assertion policy
[ ] Add coverage row
[ ] Add contract entries
[ ] Run direct scenario test
[ ] Run downstream release test when required
```

---

# 49. Removing a scenario

```text
[ ] Confirm no required contract loses evidence
[ ] Replace coverage when needed
[ ] Remove project.toml registration
[ ] Remove scenario-to-entrypoint contract
[ ] Remove input consumers
[ ] Retire or remove gold deliberately
[ ] Update validation spec
[ ] Update coverage matrix
[ ] Update release criteria
[ ] Update status ledger
[ ] Record breaking decision when required
[ ] Run release validation
```

Do not leave orphan gold or input files.

---

# 50. Adding an input

```text
[ ] Define format
[ ] Define encoding
[ ] Define purpose
[ ] Define consumer scenarios
[ ] Define ordering semantics
[ ] Define blank-line/comment semantics
[ ] Add README documentation
[ ] Add contract entry
[ ] Add format validation
[ ] Add source/provenance review
[ ] Add release significance
```

---

# 51. Changing an input format

An input-format change is breaking for every consuming scenario unless backward compatibility is explicit.

Update:

```text
parser/consumer assumptions
all scenario consumers
input README
interfile lock
validation spec
fixtures
gold when output changes
decision log
```

---

# 52. Adding a gold file

```text
[ ] Scenario completes successfully
[ ] Required markers are present
[ ] Normalized output is stable
[ ] Scenario ID matches
[ ] Normalization version matches
[ ] No machine-specific noise remains
[ ] Linguistic output is reviewed
[ ] Gold filename is registered
[ ] Gold is source-controlled
[ ] Comparison test passes
[ ] Mismatch test fails as expected
```

---

# 53. Updating gold

```text
[ ] Source/specification change is intentional
[ ] Scenario still tests the intended contract
[ ] Raw stdout/stderr inspected
[ ] New normalized output inspected
[ ] Diff reviewed
[ ] Linguistic correctness approved
[ ] Normalization change reviewed
[ ] Project-version impact reviewed
[ ] Validation docs updated
[ ] Release impact reviewed
[ ] Atomic update used
```

Do not update gold merely to remove a red test.

---

# 54. Adding a checkpoint

```text
[ ] Stable checkpoint ID assigned
[ ] Purpose documented
[ ] Modules listed
[ ] Prerequisite checkpoints listed
[ ] Required scenarios listed
[ ] project.toml updated
[ ] Dependency order reviewed
[ ] Coverage matrix updated
[ ] Release significance declared
[ ] Direct and downstream compile proof exists
```

---

# 55. Adding a release gate

A new release gate must identify:

```text
criterion
owner
required evidence
failure status
exception policy
documentation
automation
```

A gate must not depend only on human report prose.

---

# 56. Documentation ownership

| Document | Owns |
|---|---|
| `validation/README.md` | validation asset root and workflows |
| `validation/scenarios/README.md` | `.gfs` authoring and execution |
| `validation/inputs/README.md` | input formats and provenance |
| `validation/gold/README.md` | expected-output management |
| `docs/VALIDATION_SPEC.md` | project validation design and inventory |
| `docs/TEST_COVERAGE_MATRIX.md` | feature-to-evidence mapping |
| `docs/architecture/DEPENDENCY_RULES.md` | framework dependency contracts |
| `docs/RELEASE_CRITERIA.md` | release acceptance |
| `docs/STATUS_LEDGER.md` | incomplete/temporary validation |
| `docs/KNOWN_ISSUES.md` | unresolved user-visible validation issues |
| `project.toml` | executable registry and mode membership |

Do not duplicate the authoritative full scenario registry in every README.

---

# 57. Template validation examples

A new GF project should normally begin with a small set of representative validation families.

Possible examples:

```text
entrypoint-load
missing-functions
linearize-smoke
parse-smoke
morphology-smoke
bounded-generation
release-smoke
```

These are examples.

Remove or rename them according to the active project.

Do not claim an example scenario exists until the file and registry entry exist.

---

# 58. Minimal project validation set

A minimal initialized project should have:

```text
one configured compile checkpoint
one configured grammar entrypoint
one load/smoke scenario
one complete marker contract
one documented validation owner
one coverage matrix
one baseline run
```

A project intended for release should additionally have:

```text
all required checkpoint evidence
missing-function evidence
representative parse/linearization evidence
morphology evidence where applicable
reviewed gold where stability permits
PGF build evidence
manifest verification
release criteria
```

---

# 59. Optional validation families

A project may add:

```text
dialect variants
register variants
orthography variants
API scenarios
application-specific scenarios
performance smoke checks
large-lexicon checks
documentation examples
manual linguistic review
cross-version GF checks
```

Optional families must not obscure the required core suite.

---

# 60. Unsupported validation

When a validation family is not applicable or not implemented, document:

```text
family
status
reason
coverage impact
release impact
replacement plan
```

Accepted states:

```text
not-applicable
planned
blocked
experimental
disabled
```

Do not leave a required empty directory and assume it means “not applicable.”

---

# 61. Failure triage

Recommended triage order:

1. framework/environment `ERROR`;
2. direct compile failures;
3. direct scenario failures;
4. gold mismatches;
5. artifact failures;
6. downstream blocked results;
7. ambiguous failures;
8. static warnings;
9. optional scenario warnings.

Fix root providers before downstream entrypoints.

---

# 62. Troubleshooting: scenario missing

Check:

```text
project.toml registration
project-relative path
filename case
scenario ID
template placeholder residue
source-control inclusion
mode membership
```

A missing required scenario blocks release.

---

# 63. Troubleshooting: input missing

Check:

```text
registered path
project root
consumer list
filename case
encoding
source-control inclusion
```

A missing input is not a GF parse failure.

It is configuration or I/O evidence.

---

# 64. Troubleshooting: gold missing

Check:

```text
scenario is gold-backed
gold filename
scenario ID
normalization version
project registry
source-control inclusion
```

A missing required gold is a failure.

Do not generate it automatically during normal validation.

---

# 65. Troubleshooting: gold unstable

Inspect:

```text
raw stdout
raw stderr
normalized output
GF version
RGL revision
normalization version
absolute paths
timestamps
durations
random generation
unordered output
```

Do not solve instability by deleting meaningful output.

---

# 66. Troubleshooting: scenario blocked

Inspect:

```text
blocked_by
provider compile
entrypoint compile
PGF build
input availability
GF capability
```

A blocked scenario is downstream.

Fix the first direct failure.

---

# 67. Troubleshooting: release passes unexpectedly

Verify:

```text
required checkpoint list
required scenario list
release mode constraints
missing required asset handling
SKIPPED aggregation
manifest verification
known-issue exceptions
```

A required skipped item must prevent `OK`.

---

# 68. Troubleshooting: validation changes source or gold

Stop the workflow and preserve evidence.

Normal validation must not modify:

```text
project source
project.toml
validation inputs
validation scenarios
validation gold
project documentation
```

Only explicit maintenance commands may write project assets.

Treat unexpected modification as an integrity defect.

---

# 69. Anti-drift indicators

Validation drift likely exists when:

- project configuration names a scenario that does not exist;
- a `.gfs` file is not registered;
- two scenarios share one ID;
- a scenario loads an undocumented entrypoint;
- a scenario uses an unregistered input;
- an input has no consumers and no retained purpose;
- a gold file has no scenario;
- a required scenario has no gold or assertion strategy;
- scenario ID differs across config, markers, output, gold, and reports;
- a required marker is renamed in one file only;
- a normal run modifies gold;
- gold changes without a source/specification reason;
- a required checkpoint is omitted from release;
- a required scenario is silently skipped;
- scenario ordering depends on filesystem enumeration;
- generation is unbounded;
- raw output is overwritten by normalized output;
- stdout and stderr are merged;
- timeout is reported as syntax failure;
- an old language suffix remains;
- expected PGF differs across configuration and docs;
- `VALIDATION_SPEC.md` and project configuration disagree;
- coverage matrix claims evidence that no longer exists;
- a fallback validation path has no status-ledger entry;
- a report reruns validation;
- generated run files are committed under `project/validation/`.

Resolve drift by:

1. restoring the documented contract; or
2. changing the contract deliberately and updating every affected asset.

---

# 70. Validation change checklist

```text
[ ] Contract ID identified
[ ] Project configuration reviewed
[ ] Source providers reviewed
[ ] Entry points reviewed
[ ] Checkpoints reviewed
[ ] Scenario registry reviewed
[ ] Scenario files reviewed
[ ] Input files reviewed
[ ] Gold files reviewed
[ ] Marker contract reviewed
[ ] Normalization version reviewed
[ ] Coverage matrix updated
[ ] Validation specification updated
[ ] Interfile lock updated
[ ] Status ledger updated
[ ] Known issues updated
[ ] Decision log updated when breaking
[ ] Release criteria updated
[ ] Direct validation passed
[ ] Downstream validation passed
[ ] Release validation passed when applicable
```

---

# 71. Initial directory checklist

## Root

```text
[ ] README placeholders replaced
[ ] Project owner assigned
[ ] Language identity correct
[ ] Related document links valid
[ ] No generated run files present
```

## Scenarios

```text
[ ] scenarios/README.md initialized
[ ] Required .gfs files created
[ ] Scenario IDs registered
[ ] Entrypoints registered
[ ] Timeouts finite
[ ] Markers complete
```

## Inputs

```text
[ ] inputs/README.md initialized
[ ] Required inputs created
[ ] Formats documented
[ ] Consumers registered
[ ] Encoding verified
[ ] Provenance reviewed
```

## Gold

```text
[ ] gold/README.md initialized
[ ] Required golds created explicitly
[ ] Scenario IDs match
[ ] Normalization versions match
[ ] Diffs reviewed
[ ] Files source-controlled
```

---

# 72. Baseline run checklist

```text
[ ] Project configuration check passes
[ ] Placeholder scan completed
[ ] Source selection is correct
[ ] GF version recorded
[ ] Direct providers compile
[ ] Checkpoint consumers compile
[ ] Entrypoints compile
[ ] Required scenarios discovered
[ ] Required inputs discovered
[ ] Required markers verified
[ ] Normalized output generated
[ ] Gold comparisons executed
[ ] PGF build attempted when configured
[ ] Reports written
[ ] Manifest written and verified
[ ] Baseline run ID recorded
[ ] Direct failures entered in status ledger
```

---

# 73. Release validation checklist

```text
[ ] Current source revision recorded
[ ] Current project version recorded
[ ] Supported GF version used
[ ] Required RGL revision recorded
[ ] Clean artifact directories used
[ ] All required checkpoints pass
[ ] All required entrypoints pass
[ ] All required scenarios pass
[ ] All required golds match
[ ] All required artifacts exist
[ ] Expected PGF is non-empty
[ ] Manifest hashes verify
[ ] No source changed during run
[ ] No gold changed during run
[ ] Known issues reviewed
[ ] No undocumented fallback remains
[ ] Overall status is OK
```

---

# 74. Template maintenance

Changes to this reusable README must remain language-neutral.

Do not add:

```text
project-specific module names
project-specific scenario IDs
project-specific gold output
project-specific paths
specific linguistic assumptions
developer-local environment paths
```

Template examples must be clearly marked as examples.

A template change should be tested by initializing a small synthetic project.

---

# 75. Related template files

```text
templates/project/README.md
templates/project/project.toml
templates/project/docs/00_PROJECT_START_HERE.md
templates/project/docs/LANGUAGE_OVERVIEW.md
templates/project/docs/LANGUAGE_ARCHITECTURE.md
templates/project/docs/MODULE_DEPENDENCY_MAP.md
templates/project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
templates/project/docs/MORPHOLOGY_SPEC.md
templates/project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
templates/project/docs/VALIDATION_SPEC.md
templates/project/docs/TEST_COVERAGE_MATRIX.md
templates/project/docs/STATUS_LEDGER.md
templates/project/docs/DECISION_LOG.md
templates/project/docs/KNOWN_ISSUES.md
templates/project/docs/RELEASE_CRITERIA.md
templates/project/docs/RESEARCH_EVIDENCE.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/validation/scenarios/README.md
templates/project/validation/inputs/README.md
templates/project/validation/gold/README.md
```

---

# 76. Final initialization checklist

```text
[ ] Replace every required placeholder
[ ] Confirm one active project identity
[ ] Configure source directory
[ ] Configure GF path additions
[ ] Configure entrypoints
[ ] Configure checkpoints
[ ] Configure required scenarios
[ ] Configure optional scenarios
[ ] Configure release artifacts
[ ] Initialize scenarios README
[ ] Initialize inputs README
[ ] Initialize gold README
[ ] Create required scenarios
[ ] Create required inputs
[ ] Create required golds explicitly
[ ] Define marker contract
[ ] Define normalization version
[ ] Define coverage matrix
[ ] Define release gates
[ ] Define validation owners
[ ] Register incomplete work
[ ] Update interfile contracts
[ ] Run placeholder scan
[ ] Run configuration check
[ ] Run diagnostic baseline
[ ] Record baseline run ID
[ ] Confirm normal validation is read-only
```

---

# 77. Final enforcement rule

The project validation directory is a source-controlled contract between the language implementation, GF, and GF Wordbench.

> Scenarios must execute declared GF behavior, inputs must be portable and documented, golds must represent reviewed normalized expectations, and release status must be derived from complete current-run evidence.

The directory is initialized only when:

```text
configuration
checkpoints
entrypoints
scenarios
inputs
golds
coverage
contracts
release criteria
```

all describe the same active project.
