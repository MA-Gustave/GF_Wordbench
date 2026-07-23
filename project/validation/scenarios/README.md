# GF Wordbench Project — Validation Scenarios

**Document ID:** `GF-WB-PROJECT-SCENARIOS-README`  
**Status:** Normative project authoring guide  
**Applies to:** `project/validation/scenarios/` for the active Albanian (`sqi`, GF suffix `Sqi`) project  
**Owner:** Active language project maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\project\validation\scenarios\README.md`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This directory contains native GF shell scenarios used to validate the active language project.

Each scenario is a `.gfs` script executed by GF through GF Wordbench.

Scenarios provide runtime evidence for:

- grammar loading;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- missing-function checks;
- entrypoint smoke tests;
- regression checks;
- release gates.

Scenarios do not replace direct `.gf` compilation.

The validation model is:

```text
compile providers and entrypoints
→ execute native .gfs scenarios
→ verify required markers
→ normalize stable output
→ compare with reviewed gold when configured
→ record structured results and raw evidence
```

---

## 2. Directory role

Canonical location:

```text
project/validation/scenarios/
```

This directory owns project-specific runtime validation scripts.

Related directories:

```text
project/validation/inputs/
project/validation/gold/
```

Related project documents:

```text
project/project.toml
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/RELEASE_CRITERIA.md
project/docs/STATUS_LEDGER.md
```

Framework-level references:

```text
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/validation/SCENARIO_VALIDATION.md
```

---

## 3. Authority model

### 3.1 GF authority

GF is authoritative for:

- loading GF modules;
- executing GF shell commands;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- GF-native diagnostics.

### 3.2 Project authority

The active project is authoritative for:

- which scenarios exist;
- which scenarios are required;
- which entrypoint each scenario loads;
- which inputs each scenario consumes;
- which markers are required;
- which output is expected;
- which gold file belongs to each scenario;
- which scenarios block release.

### 3.3 GF Wordbench authority

GF Wordbench is authoritative for:

- scenario discovery;
- request construction;
- working directory;
- GF executable;
- GF path;
- timeout;
- stdout/stderr capture;
- marker verification;
- output normalization;
- gold comparison;
- result classification;
- artifact paths;
- reporting.

---

## 4. Core rule

> A scenario passes only when GF execution and every required scenario contract both pass.

A zero GF exit code is not sufficient when:

- a required marker is missing;
- a forbidden marker appears;
- a required section did not execute;
- expected output is absent;
- a required artifact is missing;
- normalized output differs from gold;
- the process timed out;
- the process was cancelled;
- the wrong grammar entrypoint was loaded.

---

## 5. Native `.gfs` rule

Scenario files are native GF shell scripts.

Extension:

```text
.gfs
```

GF Wordbench must not invent a parallel language that replaces GF shell semantics.

Project-specific metadata may be declared in `project.toml` or stable comment headers, but the executed content remains valid GF shell input.

A maintainer should be able to reproduce the essential script manually with the configured GF executable.

---

## 6. Scenario registry

Every scenario used by GF Wordbench must be registered in:

```text
project/project.toml
```

The registry should identify, directly or through the project schema:

```text
scenario_id
scenario file
required or optional status
entrypoint
timeout
input dependencies
gold file
normalization version
required markers
forbidden markers
expected artifacts
validation modes
```

The exact TOML field names are governed by:

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/PERSISTED_SCHEMA_LOCK.md
```

Do not invent new project fields only inside a scenario file.

---

## 7. Scenario identity

Each scenario has one stable identifier.

Recommended format:

```text
lowercase-kebab-case
```

Examples:

```text
entrypoint-smoke
noun-paradigms
verb-paradigms
parse-basic
linearize-basic
morphology-analysis
missing-functions
release-smoke
```

Requirements:

- unique within the active project;
- stable across file moves;
- independent from run IDs;
- used consistently in project configuration, markers, gold paths, reports, and documentation.

Renaming a scenario ID is a coordinated migration.

---

## 8. File naming

Recommended filename:

```text
<scenario-id>.gfs
```

Examples:

```text
entrypoint-smoke.gfs
noun-paradigms.gfs
parse-basic.gfs
```

A filename may differ from the scenario ID only when the mapping is explicit and justified.

Avoid:

```text
test1.gfs
new.gfs
final-final.gfs
tmp.gfs
copy-of-parse.gfs
```

Temporary scripts that are not registered should not remain in the canonical scenario directory.

---

## 9. Scenario categories

Recommended scenario families:

```text
smoke
compile-adjacent
parse
linearize
generate
morphology
introspection
missing-functions
regression
release
```

A scenario may cover more than one family, but smaller focused scenarios are usually easier to diagnose.

---

## 10. Canonical directory layout

Recommended project layout:

```text
project/validation/
├── README.md
├── scenarios/
│   ├── README.md
│   ├── entrypoint-smoke.gfs
│   ├── parse-basic.gfs
│   ├── linearize-basic.gfs
│   ├── noun-paradigms.gfs
│   ├── verb-paradigms.gfs
│   └── release-smoke.gfs
├── inputs/
│   ├── README.md
│   └── ...
└── gold/
    ├── README.md
    ├── entrypoint-smoke.gold
    ├── parse-basic.gold
    └── ...
```

The actual scenario set is declared by the active project.

This example is not a claim that every listed file already exists.

---

## 11. Scenario header

A scenario should begin with a stable comment header.

Recommended form:

```gf
-- GF_WORDBENCH_SCENARIO 1.0
-- scenario_id: parse-basic
-- purpose: Basic parsing smoke coverage
-- entrypoint: <CONFIGURED_ENTRYPOINT>
-- required: true
-- normalization_version: 1.0
```

The header is documentation unless the scenario schema explicitly makes a field machine-readable.

`project.toml` remains authoritative for registered execution settings.

Header values must not contradict configuration.

---

## 12. Scenario markers

Markers prove that required sections executed.

Recommended marker form:

```text
GF_WORDBENCH::<scenario-id>::BEGIN
GF_WORDBENCH::<scenario-id>::SECTION::<section-id>::BEGIN
GF_WORDBENCH::<scenario-id>::SECTION::<section-id>::END
GF_WORDBENCH::<scenario-id>::END
```

Markers must be:

- deterministic;
- unique;
- plain text;
- independent from localized prose;
- preserved by normalization;
- easy to identify exactly.

The exact marker syntax is governed by:

```text
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
```

---

## 13. Required marker sequence

A complete required scenario should emit:

```text
scenario begin
→ one or more section begin/end pairs
→ scenario end
```

The order must match execution order.

Invalid examples:

```text
END before BEGIN
duplicate section ID
missing section END
missing final scenario END
marker from another scenario ID
```

A missing required end marker invalidates the scenario even if GF exits zero.

---

## 14. Section identifiers

Section IDs should use:

```text
lowercase-kebab-case
```

Examples:

```text
load-entrypoint
parse-sentence-01
linearize-tree-01
noun-class-a
verb-present
missing-functions
```

Section IDs must be unique within the scenario.

Stable section IDs make gold diffs easier to review.

---

## 15. Marker output

Use a GF shell command that emits literal text supported by the configured GF version.

The project must use one documented marker-emission pattern.

Do not mix multiple marker encodings across scenarios.

Do not depend on:

- timestamps;
- random numbers;
- absolute paths;
- environment values;
- terminal colors.

---

## 16. Entry point selection

Each scenario must load the entrypoint declared by the project registry.

Typical roles may include:

```text
GrammarSqi
LangSqi
AllSqi
syntax entrypoint
API entrypoint
release entrypoint
```

Exact active module names are defined by:

```text
project/project.toml
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

A scenario must not silently switch to another language or private temporary module.

---

## 17. Working directory

GF Wordbench supplies an explicit working directory.

Scenario paths must not rely on:

- the terminal launch directory;
- the GUI process directory;
- a developer’s IDE;
- a user-specific absolute path;
- a launcher shortcut directory.

Project-owned paths should be relative to the project root or declared input root.

---

## 18. GF path

Compilation, PGF build, and scenario execution must use equivalent GF path semantics.

The resolved GF path should include:

- active project source directories;
- required project additions;
- required RGL paths.

A scenario must not redefine a hidden conflicting GF path unless the external-tool contract explicitly permits it.

---

## 19. Scenario inputs

Reusable input data belongs in:

```text
project/validation/inputs/
```

Examples:

```text
sentences
trees
lemmas
feature matrices
lexical forms
expected identifiers
```

Scenario files should remain readable and focused.

Large datasets should not be pasted directly into `.gfs` when a registered input file is more maintainable.

---

## 20. Input identity

Each input file used by a scenario must have:

```text
stable project-relative path
documented format
documented encoding
owning scenario or shared consumer list
validation rules
```

If one input is shared by multiple scenarios, its compatibility becomes a project contract.

---

## 21. Input encoding

Canonical project input text uses:

```text
UTF-8 without BOM
LF
final newline where line-oriented
```

Albanian letters must be preserved exactly.

Do not replace them with ASCII approximations.

---

## 22. Required and optional scenarios

### Required

A required scenario:

- runs in its configured validation modes;
- cannot be silently skipped;
- blocks release when it fails;
- requires all declared prerequisites;
- requires marker completion;
- requires gold when configured.

### Optional

An optional scenario:

- may be excluded by mode or environment policy;
- must still report a clear state;
- must not be counted as successful when not executed;
- must not become release-critical implicitly.

Required/optional status belongs to project configuration.

---

## 23. Scenario prerequisites

A scenario may depend on:

```text
successful entrypoint compilation
successful PGF construction
required input files
required GF version capability
required RGL content
successful provider checkpoints
```

If a prerequisite fails, the scenario result should record:

```text
validation_status = SKIPPED
diagnostic_class = downstream or skipped
blocked_by = [prerequisite identities]
```

A blocked scenario is not a successful scenario.

---

## 24. Validation modes

The canonical framework modes are:

```text
quick
checkpoint
release
diagnostic
```

### Quick

Runs a small focused scenario subset.

Typical use:

```text
entrypoint smoke
one targeted scenario
fast regression check
```

### Checkpoint

Runs scenarios associated with selected development layers.

Typical use:

```text
morphology checkpoint
syntax checkpoint
lexicon checkpoint
```

### Release

Runs every required release scenario and release gate.

### Diagnostic

Runs the broadest configured set, including optional diagnostic scenarios where safe.

Scenario-mode membership must be declared in project configuration or validation policy.

---

## 25. Timeout policy

Every scenario has a finite timeout.

Timeout may be:

- project default;
- scenario-specific override;
- mode-constrained value.

A timeout produces:

```text
execution_state = timed_out
validation_status = ERROR
error_kind = TIMEOUT
```

It must not be classified as a GF syntax or type error.

---

## 26. Cancellation

Cancellation is distinct from timeout.

A cancelled scenario should record:

```text
execution_state = cancelled
validation_status = ERROR or non-success according to framework policy
```

Partial stdout and stderr should remain available.

A cancellation must not update gold.

---

## 27. stdout and stderr

GF Wordbench captures streams separately.

Canonical raw paths:

```text
raw/scenarios/<scenario-id>.out.txt
raw/scenarios/<scenario-id>.err.txt
```

Both files should exist for a launched scenario, even when one stream is empty.

Framework messages must not be inserted into raw GF streams as if GF emitted them.

---

## 28. Normalized scenario output

Canonical normalized path:

```text
raw/scenarios/<scenario-id>.out
```

Canonical header:

```text
# GF_WORDBENCH_OUTPUT 1.0
# scenario_id: <scenario-id>
# normalization_version: <version>
```

Normalization may remove approved non-semantic instability.

It must preserve linguistic evidence.

---

## 29. Allowed normalization

Allowed examples:

```text
CRLF → LF
ANSI escape removal
approved absolute path replacement
trailing-space removal
approved duration token replacement
```

Approved tokens may include:

```text
<PROJECT_ROOT>
<RGL_ROOT>
<RUN_DIR>
<GF_EXECUTABLE>
<DURATION_MS>
```

---

## 30. Forbidden normalization

Do not normalize away:

```text
abstract trees
linearized strings
parse alternatives
ambiguity counts
morphological analyses
missing-function lists
GF errors
meaningful punctuation
Albanian Unicode distinctions
required markers
section order
```

Do not sort output whose order is semantically meaningful.

---

## 31. Gold files

A scenario with stable expected output may use:

```text
project/validation/gold/<scenario-id>.gold
```

Canonical gold header:

```text
# GF_WORDBENCH_GOLD 1.0
# scenario_id: <scenario-id>
# normalization_version: <version>
```

The scenario ID and normalization version must match the normalized actual output.

---

## 32. Gold comparison

Comparison occurs after normalization.

A gold mismatch produces a validation failure, not a framework error, unless the comparator itself fails.

Expected artifacts include:

```text
normalized actual output
gold path
diff path
comparison status
```

Normal validation never modifies gold.

---

## 33. Gold updates

Gold updates are explicit maintenance actions.

Planned command:

```text
gf-wordbench gold update <scenario-id>
```

A gold update requires:

1. successful current scenario execution;
2. complete required markers;
3. reviewed normalized output;
4. displayed or stored diff;
5. correct normalization version;
6. atomic write;
7. source-control review.

Do not update gold only to make a failing test pass.

---

## 34. Scenario result model

A scenario result should contain:

```text
scenario_id
required
validation_status
execution_state
error_kind
diagnostic_class
blocked_by
duration
stdout_path
stderr_path
normalized_output_path
gold_path
gold_match
diff_path
marker results
expected artifact results
```

The canonical machine representation belongs to:

```text
summary.json
```

---

## 35. Canonical statuses

Validation:

```text
OK
FAIL
ERROR
SKIPPED
```

Execution:

```text
completed
timed_out
cancelled
launch_failed
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

Do not collapse these axes into one scenario status.

---

## 36. Scenario success criteria

A scenario is `OK` only when all required conditions pass:

```text
[ ] prerequisite stages passed
[ ] GF process launched
[ ] process completed
[ ] no timeout
[ ] no cancellation
[ ] exit semantics accepted
[ ] no fatal GF diagnostic
[ ] required markers found
[ ] forbidden markers absent
[ ] expected artifacts exist
[ ] normalized output created
[ ] gold matches when configured
```

---

## 37. Scenario failure categories

### Direct validation failure

Examples:

- parse does not include required tree;
- linearization differs from expected behavior;
- required marker assertion fails;
- gold mismatch;
- missing-function check reports required implementation missing.

### Downstream failure

Examples:

- scenario blocked by failed grammar entrypoint;
- scenario blocked by missing PGF;
- scenario blocked by failed morphology provider.

### Framework or environment error

Examples:

- GF cannot launch;
- scenario times out;
- input file cannot be read;
- output cannot be written;
- marker parser crashes;
- configuration is invalid.

---

## 38. Scenario design principles

Good scenarios are:

```text
focused
deterministic
bounded
labeled
reproducible
diagnosable
portable
reviewable
```

Bad scenarios are:

```text
unbounded
random without seed/control
dependent on local absolute paths
silent
monolithic
duplicated
dependent on hidden state
self-modifying
gold-updating
```

---

## 39. One concern per section

A scenario may include multiple sections, but each section should test one coherent behavior.

Good:

```text
noun-regular-class-a
noun-irregular-plural
noun-definite-accusative
```

Weak:

```text
everything
misc
test-2
```

Clear sections make regressions easier to localize.

---

## 40. Bounded generation

Generation commands must be bounded.

Use one or more:

```text
specific category
specific function
maximum count
maximum depth
fixed input tree
fixed lemma set
```

Do not use unbounded random generation in required scenarios.

Random exploratory scenarios must be optional and must not use stable gold comparison unless deterministic controls are available.

---

## 41. Parse scenarios

A parse scenario should identify:

```text
input sentence
loaded grammar
start category
parse limits
expected tree or tree family
expected ambiguity policy
```

A parse test may assert:

- exact tree;
- inclusion of a tree;
- parse count;
- absence of parse;
- bounded ambiguity.

Do not claim uniqueness when the grammar intentionally permits ambiguity.

---

## 42. Linearization scenarios

A linearization scenario should identify:

```text
abstract tree
concrete language
expected string
variant policy
punctuation policy
```

Output should preserve meaningful spaces and punctuation.

If multiple valid variants are allowed, the assertion policy must be explicit.

---

## 43. Morphology scenarios

Morphology scenarios should label feature combinations.

Conceptual output:

```text
NOUN|lemma=<...>|number=sg|def=indef|case=nom|form=<...>
VERB|lemma=<...>|person=1|number=sg|tense=pres|form=<...>
```

Exact identifiers should remain stable.

Required morphology coverage is defined by:

```text
project/docs/MORPHOLOGY_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
```

---

## 44. Grammar introspection scenarios

Introspection may verify:

```text
loaded languages
categories
functions
missing linearizations
available operations
entrypoint identity
```

Introspection output may vary across GF versions.

Only stable, reviewed portions should be included in gold.

---

## 45. Missing-function scenarios

A missing-function scenario should distinguish:

```text
expected zero missing functions
known accepted missing functions
unexpected missing functions
unsupported introspection capability
```

Known accepted gaps must be recorded in:

```text
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
```

Do not hide unexpected missing functions through normalization.

---

## 46. Release smoke scenarios

A release smoke scenario should use the release entrypoint or built PGF.

It should verify a small set of critical behaviors such as:

```text
grammar loads
one representative parse
one representative linearization
one representative morphology operation
one introspection operation
completion marker
```

Release smoke is not a substitute for the complete required suite.

---

## 47. Input data design

Input files should be:

```text
small enough to review
large enough to represent the target
stable
documented
version-controlled
UTF-8
```

Avoid datasets containing:

- personal data;
- secrets;
- machine-specific paths;
- unstable generated identifiers;
- unlicensed text.

---

## 48. Scenario portability

A portable scenario must not hard-code:

```text
C:\...
/home/...
developer usernames
temporary run directories
installed GF location
installed RGL location
```

Use project configuration and GF path resolution.

When a raw GF diagnostic contains an absolute path, normalization may replace it with an approved token.

---

## 49. Scenario security

`.gfs` files are executable inputs.

Scenario authors must not add:

- operating-system shell escapes;
- arbitrary file deletion;
- writes outside owned run directories;
- secret reads;
- network calls;
- process spawning;
- environment dumps.

A prohibited command must be rejected before execution where possible.

---

## 50. Deterministic ordering

Scenario execution order follows project configuration.

Do not depend on filesystem enumeration order.

Within a scenario, output section order follows script execution.

Gold comparison must preserve that order unless the scenario contract explicitly marks a section as unordered.

---

## 51. Scenario dependencies

A scenario should not depend on side effects from a previous scenario.

Each scenario should be independently executable given its declared prerequisites.

Prohibited hidden dependency:

```text
scenario B assumes scenario A wrote a file
```

Allowed dependency:

```text
both scenarios consume a declared project input
```

or:

```text
scenario depends on a declared PGF artifact
```

---

## 52. Generated files

A scenario may generate files only when:

- the output is declared;
- the path is inside the owned run directory;
- the artifact role is documented;
- the file is included in the manifest when required;
- cleanup behavior is defined.

A scenario must not modify project source, input files, or gold files during normal validation.

---

## 53. Scenario-to-gold contract

For each gold-backed scenario:

```text
scenario ID
→ normalized output
→ exactly one authoritative gold file
```

Multiple gold variants require an explicit selection rule.

Examples:

```text
GF-version-specific gold
platform-specific gold
dialect-specific gold
```

Such variants should be avoided unless the difference is meaningful and documented.

---

## 54. Scenario-to-entrypoint contract

Every scenario must identify the entrypoint it loads.

The mapping belongs in:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/VALIDATION_SPEC.md
```

A broken mapping is a project contract failure.

---

## 55. Scenario-to-input contract

Every external input path must be registered or documented.

A missing required input is:

```text
validation_status = ERROR
error_kind = CONFIG or IO
```

It is not a language parse failure.

---

## 56. Scenario-to-marker contract

Required marker IDs are stable public scenario outputs.

Renaming a required marker requires updating:

```text
scenario
project configuration
marker verifier tests
gold
validation specification
interfile contract
```

---

## 57. Scenario-to-report contract

Reports consume structured scenario results.

Reports must not:

- rerun scenarios;
- infer marker success from prose;
- reconstruct raw paths;
- compare gold independently;
- modify scenario artifacts.

---

## 58. Authoring template

Use this conceptual template:

```gf
-- GF_WORDBENCH_SCENARIO 1.0
-- scenario_id: <scenario-id>
-- purpose: <one sentence>
-- entrypoint: <configured entrypoint>
-- required: <true|false>
-- normalization_version: 1.0

-- Emit:
-- GF_WORDBENCH::<scenario-id>::BEGIN

-- Load the configured entrypoint.

-- Emit:
-- GF_WORDBENCH::<scenario-id>::SECTION::<section-id>::BEGIN

-- Execute one bounded GF operation.

-- Emit:
-- GF_WORDBENCH::<scenario-id>::SECTION::<section-id>::END

-- Emit:
-- GF_WORDBENCH::<scenario-id>::END
```

Replace comments with the documented GF shell commands supported by the configured GF version.

---

## 59. Parse scenario template

Conceptual structure:

```text
BEGIN scenario
load configured grammar
BEGIN parse-basic
parse one reviewed sentence
emit parse result
END parse-basic
END scenario
```

Document:

```text
start category
expected tree policy
ambiguity policy
normalization policy
gold policy
```

---

## 60. Linearization scenario template

Conceptual structure:

```text
BEGIN scenario
load configured grammar
BEGIN linearize-basic
linearize one reviewed abstract tree
emit result
END linearize-basic
END scenario
```

Document whether exact or variant-aware comparison is required.

---

## 61. Morphology scenario template

Conceptual structure:

```text
BEGIN scenario
load configured grammar/resource
BEGIN noun-class-a
emit labeled forms
END noun-class-a
BEGIN verb-class-a
emit labeled forms
END verb-class-a
END scenario
```

Each table cell should be labeled or ordered through a documented matrix.

---

## 62. Introspection scenario template

Conceptual structure:

```text
BEGIN scenario
load configured grammar
BEGIN missing-functions
run bounded introspection
emit result
END missing-functions
END scenario
```

Avoid including unstable verbose dumps in gold.

---

## 63. Scenario author checklist

```text
[ ] Scenario ID is unique
[ ] Filename is stable
[ ] Scenario is registered
[ ] Required/optional status is declared
[ ] Entry point is declared
[ ] GF path assumptions are portable
[ ] Working directory assumptions are portable
[ ] Inputs are registered
[ ] Timeout is finite
[ ] Begin marker exists
[ ] Section markers exist
[ ] Final marker exists
[ ] Operations are bounded
[ ] Output is deterministic
[ ] Meaningful Unicode is preserved
[ ] Forbidden commands are absent
[ ] Expected artifacts are declared
[ ] Gold policy is declared
[ ] Normalization version is declared
[ ] Validation documentation is updated
[ ] Coverage matrix is updated
```

---

## 64. Scenario review checklist

```text
[ ] Script runs manually with recorded GF request
[ ] Script runs through GF Wordbench
[ ] stdout and stderr are separate
[ ] Required markers are detected
[ ] Missing marker test fails
[ ] Timeout test behaves correctly
[ ] Wrong entrypoint test fails clearly
[ ] Missing input test fails clearly
[ ] Normalized output is reviewable
[ ] Gold mismatch produces a diff
[ ] Normal run does not modify gold
[ ] Result appears correctly in summary.json
[ ] Result appears correctly in summary.md
[ ] Artifact paths are in manifest
```

---

## 65. Gold review checklist

```text
[ ] Scenario completed fully
[ ] Required markers are present
[ ] Scenario ID matches
[ ] Normalization version matches
[ ] Output contains only intended stable evidence
[ ] No absolute machine path remains
[ ] No timestamp or duration remains unless tokenized
[ ] No semantic line was removed
[ ] Albanian characters are correct
[ ] Diff is understood
[ ] Language change is intentional
[ ] Project version impact is reviewed
[ ] Source-control review is complete
```

---

## 66. Change workflow

When changing a scenario:

1. identify the scenario contract;
2. identify entrypoint, inputs, markers, gold, and consumers;
3. preserve current output;
4. update the `.gfs`;
5. run the scenario without updating gold;
6. inspect raw stdout and stderr;
7. inspect normalized output;
8. inspect marker results;
9. compare with gold;
10. update gold explicitly only when intended;
11. update project configuration if metadata changed;
12. update validation documentation;
13. update coverage matrix;
14. update interfile contract for public marker/input/entrypoint changes;
15. run the complete required suite.

---

## 67. Breaking changes

The following are breaking scenario-contract changes:

```text
scenario ID rename
required scenario removal
entrypoint change
required marker rename/removal
section semantic change
input format change
normalization major change
gold identity change
required artifact path change
success-criterion change
```

A breaking change requires coordinated migration.

---

## 68. Compatible changes

Usually compatible:

```text
add optional diagnostic section
add optional scenario
add additional bounded example
improve comments
add raw evidence not used by gold
add optional marker metadata
```

A change is not compatible when older readers or gold comparators misinterpret it.

---

## 69. Deprecation

A deprecated scenario should record:

```text
replacement scenario
deprecation date/version
reason
remaining consumers
planned removal
migration notes
```

Required release coverage must move to the replacement before removal.

Do not silently stop running a required scenario.

---

## 70. Troubleshooting: scenario does not load

Check:

```text
configured entrypoint
GF path
working directory
source compilation
module name/suffix
GF version
RGL paths
stderr
```

Do not patch the scenario to load a private lower-level module unless that is the intended contract.

---

## 71. Troubleshooting: exits zero but fails

Likely causes:

```text
missing required marker
forbidden marker
gold mismatch
missing expected artifact
empty required section
ignored GF command
```

Inspect:

```text
raw stdout
raw stderr
marker results
normalized output
gold diff
```

---

## 72. Troubleshooting: works manually only

Compare the exact recorded:

```text
GF executable
ordered arguments
working directory
GF path
stdin bytes
timeout
environment overrides
```

A manual reproduction using a simplified command is not equivalent.

---

## 73. Troubleshooting: unstable gold

Compare:

```text
raw stdout
normalized output
gold
GF version
RGL revision
normalization version
```

Look for:

```text
absolute paths
timestamps
durations
random generation
unordered output
GF-version-specific diagnostics
platform newlines
```

Do not solve instability by deleting semantic output.

---

## 74. Troubleshooting: Unicode mismatch

Inspect bytes and code points.

Check:

```text
UTF-8 encoding
BOM
NFC/NFD differences
editor normalization
Albanian ë/Ë
Albanian ç/Ç
apostrophe variants
hyphen variants
```

Do not globally normalize Unicode without project policy.

---

## 75. Troubleshooting: downstream skip

Inspect:

```text
blocked_by
entrypoint compile result
provider compile result
PGF build result
required input existence
GF capability probe
```

Fix the first direct failure.

Do not count blocked scenarios as independent root defects.

---

## 76. Troubleshooting: timeout

Check:

```text
unbounded generation
large parse search
missing limit
recursive grammar behavior
GF process deadlock
huge input
wrong entrypoint
too-small timeout
```

Increase timeout only after confirming the scenario is intentionally bounded.

---

## 77. Troubleshooting: marker collision

Markers must include the scenario ID and section ID.

Do not use generic markers such as:

```text
BEGIN
END
DONE
```

These may appear in normal GF output.

---

## 78. Troubleshooting: wrong gold selected

Verify:

```text
scenario ID
scenario filename
project registry
gold filename
gold header
normalization version
variant-selection policy
```

Do not select gold by “newest file” or filename prefix guessing.

---

## 79. Test coverage matrix integration

Every required scenario should map to one or more coverage rows.

Recommended columns:

```text
scenario ID
feature family
module providers
entrypoint
required mode
input files
gold file
status
known gap
release gate
```

A required feature without scenario or compile evidence is incomplete.

---

## 80. Status ledger integration

Record scenario gaps such as:

```text
temporary scenario
partial assertion
missing gold
unstable GF-version output
disabled scenario
blocked scenario
known timeout
missing input corpus
accepted ambiguity
```

A disabled required scenario blocks release unless release criteria explicitly permit it.

---

## 81. Decision log integration

Use `DECISION_LOG.md` when changing:

```text
scenario format
marker syntax
normalization semantics
entrypoint strategy
gold variant policy
random-generation policy
input format
release scenario set
```

Routine example additions do not require an ADR-like project decision.

---

## 82. Release criteria integration

Release validation should confirm:

```text
all required scenarios discovered
all required inputs present
all required prerequisites passed
all required scenarios completed
all required markers present
all required golds matched
no normal run modified gold
release smoke passed
scenario artifacts are manifested
```

---

## 83. Scenario inventory

Maintain an inventory in `VALIDATION_SPEC.md` or `TEST_COVERAGE_MATRIX.md`.

Recommended table:

| Scenario ID | File | Required | Entry point | Gold | Modes | Owner | Status |
|---|---|---:|---|---|---|---|---|
| `<id>` | `<file>.gfs` | yes/no | `<module>` | `<file>.gold` or none | quick/checkpoint/release/diagnostic | `<owner>` | active/partial/blocked |

Do not duplicate inconsistent inventories across many files.

One document should own the full table.

---

## 84. Scenario ownership

Every scenario must have a maintainer or project area owner.

Possible ownership areas:

```text
morphology
noun phrase
verb phrase
sentence
questions
relatives
coordination
lexicon
structural
extensions
release
```

Ownership does not permit changing shared markers or entrypoint contracts unilaterally.

---

## 85. Anti-drift indicators

Probable scenario drift exists when:

- a `.gfs` file is not registered;
- a registered scenario file is missing;
- a required scenario is silently skipped;
- scenario ID differs across config, header, markers, gold, and reports;
- a scenario loads an undocumented entrypoint;
- a scenario uses an unregistered input;
- a gold file has no scenario;
- a scenario has multiple authoritative golds without a rule;
- required markers are absent;
- marker order differs from script order;
- a normal run modifies gold;
- normalization removes linguistic output;
- a scenario depends on a previous scenario side effect;
- an absolute developer path appears in the script;
- generation is unbounded;
- randomness affects required gold;
- GUI and CLI execute different scenario requests;
- raw stdout and stderr are merged;
- timeout is mapped to a syntax failure;
- a report reruns the scenario;
- an optional scenario becomes release-critical without configuration change;
- scenario output shape changes without normalization/scenario contract review.

Any drift indicator requires project contract review.

---

## 86. Minimum required evidence per scenario

Every active scenario must have at least:

```text
registered configuration
successful discovery test
manual or automated execution proof
raw stdout
raw stderr
marker verification
structured result
documented owner
```

Gold-backed scenarios also require:

```text
normalized output
gold file
diff behavior
read-only normal validation proof
```

---

## 87. Scenario completion criteria

A scenario is complete when:

```text
[ ] ID is stable
[ ] File is registered
[ ] Owner is known
[ ] Entrypoint is correct
[ ] Inputs are registered
[ ] Required status is correct
[ ] Timeout is finite
[ ] Markers are complete
[ ] Output is bounded
[ ] Output is deterministic
[ ] Normalization is versioned
[ ] Gold exists when required
[ ] Direct execution passes
[ ] Expected failure test exists where relevant
[ ] Coverage matrix is updated
[ ] Interfile contracts are updated
[ ] Release policy is updated when applicable
```

---

## 88. Example scenario plan

Before writing a scenario, define:

```text
Scenario ID: noun-paradigms
Purpose: Validate representative noun inflection classes
Entrypoint: configured morphology or grammar entrypoint
Required: yes
Modes: checkpoint, release, diagnostic
Inputs: representative noun lemmas
Sections:
  - regular-class-a
  - regular-class-b
  - irregular-plural
  - definite-cases
Markers: required for every section
Gold: noun-paradigms.gold
Normalization: 1.0
Owner: morphology
```

This is a planning example.

It does not assert current source constructors or scenario registry entries.

---

## 89. Example review record

```text
Scenario ID: <id>
Source revision: <commit>
GF version: <version>
RGL revision: <revision>
Project version: <version>
Normalization version: <version>
Raw stdout: <run-relative-path>
Raw stderr: <run-relative-path>
Normalized output: <run-relative-path>
Gold: <project-relative-path>
Result: OK/FAIL/ERROR/SKIPPED
Reviewer: <name>
Date: <date>
```

---

## 90. Final rule

Scenarios are executable project contracts.

> Every required `.gfs` file must load the declared grammar, execute bounded GF operations, emit stable completion markers, preserve raw evidence, and produce reviewable normalized output whose expectations are controlled through explicit gold and project configuration.

A scenario is not complete merely because it runs once.

It is complete when it is:

```text
registered
portable
deterministic
bounded
diagnosable
versioned
covered
reviewed
release-aware
```
