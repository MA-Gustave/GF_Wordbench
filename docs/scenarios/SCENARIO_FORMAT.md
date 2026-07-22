# GF Wordbench — Scenario Format

**Document ID:** `GF-WB-SCENARIO-FORMAT`  
**Status:** Normative specification  
**Applies to:** `project/validation/scenarios/*.gfs`, the scenario registry, scenario execution, normalized output and gold comparison  
**Owner:** GF Wordbench maintainers  
**Project authority:** active-language project maintainers  
**Primary implementation owner:** `app/audit/scenario_runner.py` or its final designated equivalent  
**Related external contract:** `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`  
**Related normalization contract:** `docs/gf/GF_OUTPUT_NORMALIZATION.md`  
**Related persisted schema:** `docs/PERSISTED_SCHEMA_LOCK.md`

---

## 1. Purpose

A GF Wordbench scenario is a native Grammatical Framework shell script used to prove behavior that cannot be established reliably by static scanning or isolated source-file compilation.

Scenarios validate such behavior as:

- loading a configured grammar entrypoint;
- checking missing functions;
- parsing configured text;
- linearizing configured trees;
- inspecting morphology;
- performing bounded generation;
- exercising retained source operations;
- verifying final grammar behavior;
- producing stable evidence for reviewed gold comparison.

This document defines the final scenario format.

It specifies:

- where scenarios live;
- how scenario identity is resolved;
- how required and optional scenarios are registered;
- which GF shell constructs are permitted;
- how output sections are marked;
- how execution terminates;
- how inputs are supplied;
- how output is normalized and compared;
- how success, failure and error are distinguished;
- how scenarios remain deterministic, bounded and secure;
- how scenario changes are reviewed and tested.

The core rule is:

> A scenario is a native GF script with a declared project identity, deterministic execution order, stable output markers and externally evaluated success criteria.

GF Wordbench runs GF. It does not reimplement GF shell semantics.

---

## 2. Scope

This specification governs:

- `.gfs` files under the active project;
- scenario identifiers;
- registry-to-file mapping;
- required and optional classification;
- scenario execution order;
- entrypoint loading;
- scenario inputs;
- stable output markers;
- section identifiers;
- allowed and prohibited command behavior;
- explicit termination;
- timeouts and output bounds;
- raw stdout and stderr;
- normalized `.out` files;
- project `.gold` files;
- scenario result fields;
- scenario-level compatibility and migration;
- scenario security checks;
- scenario contract tests.

This specification does not govern:

- GF language syntax inside `.gf` modules;
- the complete command-line contract used to launch `gf`;
- the implementation of output normalization;
- the detailed JSON schema of `ScenarioResult`;
- language-specific linguistic expectations;
- report presentation;
- automatic editing of `.gfs` files;
- automatic gold approval.

Those subjects remain owned by their dedicated documents.

---

## 3. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **SCENARIO**: one registered `.gfs` script executed as one GF process invocation.
- **SCENARIO ID**: stable project identifier for a scenario.
- **REGISTRY**: the required and optional scenario lists in `project/project.toml`.
- **SCRIPT**: the `.gfs` file corresponding to one scenario ID.
- **ENTRYPOINT**: configured GF module or grammar loaded by a scenario.
- **SECTION**: a marked region of scenario output with one stable purpose.
- **MARKER**: exact machine-recognized line delimiting a section.
- **INPUT ASSET**: reviewed project file read by a scenario.
- **RAW EVIDENCE**: unmodified captured stdout, stderr and execution facts.
- **NORMALIZED OUTPUT**: derived deterministic text used for comparison.
- **GOLD**: reviewed expected normalized output.
- **ASSERTION**: criterion evaluated by GF Wordbench after GF execution.
- **REQUIRED SCENARIO**: scenario whose absence or non-success affects required validation.
- **OPTIONAL SCENARIO**: scenario that remains visible but does not automatically block every release policy.
- **BOUNDED**: constrained by timeout, output limit, result count or another explicit finite limit.
- **DETERMINISTIC**: ordered and reproducible for equivalent inputs and supported tool versions.

---

## 4. Authority boundaries

## 4.1 GF is authoritative for

- GF shell command semantics;
- module loading;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- GF diagnostics;
- GF process output.

## 4.2 GF Wordbench is authoritative for

- scenario discovery;
- registry validation;
- execution order;
- executable and working-directory resolution;
- timeouts;
- stdout and stderr capture;
- marker validation;
- normalization;
- scenario assertions;
- gold comparison;
- structured scenario results;
- artifact paths;
- release-gate interpretation.

## 4.3 Active project is authoritative for

- which scenarios are required;
- which scenarios are optional;
- which entrypoints a scenario is intended to exercise;
- linguistic inputs;
- expected linguistic behavior;
- reviewed gold files;
- project-specific release criteria.

No layer may silently assume authority assigned to another layer.

---

## 5. Scenario location

Canonical directory:

```text
project/validation/scenarios/
```

Canonical script path:

```text
project/validation/scenarios/<scenario-id>.gfs
```

Examples:

```text
project/validation/scenarios/load.gfs
project/validation/scenarios/missing.gfs
project/validation/scenarios/parse.gfs
project/validation/scenarios/linearize.gfs
project/validation/scenarios/morphology.gfs
project/validation/scenarios/generation.gfs
```

Rules:

- scenario paths are project-relative;
- one scenario ID maps to one `.gfs` file;
- nested directories are not part of canonical v1;
- generated run output MUST NOT be written into the scenario directory;
- scenario filenames use lowercase `kebab-case`;
- the filename stem is the scenario ID;
- a scenario file MUST NOT be discovered solely because it exists;
- registration in `project.toml` is required.

---

## 6. Scenario identity

## 6.1 Canonical identifier

Recommended syntax:

```text
[a-z][a-z0-9-]*
```

Valid examples:

```text
load
missing
parse
linearize
morphology
generation
parse-basic
linearize-regression
```

Invalid examples:

```text
Parse
parse_basic
parse basic
../parse
parse.gfs
```

## 6.2 Identity source

The authoritative identity is the scenario ID declared in:

```text
project/project.toml
```

The corresponding filename MUST be:

```text
<scenario-id>.gfs
```

The runner MUST NOT infer active scenarios from directory enumeration alone.

## 6.3 Stable identity

A scenario ID is a stable project contract.

Renaming it affects:

- `project.toml`;
- the `.gfs` path;
- marker prefixes;
- the default gold path;
- historical result comparison;
- project documentation;
- test coverage;
- release evidence.

A rename requires coordinated migration.

---

## 7. Scenario registry

Canonical project configuration fields:

```toml
[validation]
required_scenarios = [
  "load",
  "missing",
  "linearize",
  "parse",
]

optional_scenarios = [
  "generation",
  "morphology",
]
```

## 7.1 Registry invariants

- IDs are unique across both arrays.
- Declared order is execution order unless a validation mode selects a documented subset.
- Every required ID maps to exactly one file.
- Every optional ID maps to exactly one file when selected.
- An undeclared `.gfs` file is not executed automatically.
- A missing required file is a configuration error.
- A missing selected optional file is an error for that requested operation.
- A scenario cannot be both required and optional.
- Normal execution MUST NOT reorder the arrays.
- Registry values remain language-project data, not framework defaults.

## 7.2 Required versus optional

Requiredness is project policy.

The `.gfs` file does not declare itself required.

This prevents disagreement between:

```text
project.toml
scenario comments
GUI state
historical reports
```

Optional scenarios remain visible in configuration and reports.

They MUST NOT silently disappear from diagnostic runs or project-completion checks.

---

## 8. Mode selection

The script itself MUST NOT branch on the GF Wordbench validation mode.

Mode-to-scenario selection belongs to the validation pipeline.

Conceptual behavior:

| Mode | Scenario behavior |
|---|---|
| `quick` | Runs only the configured quick/smoke subset, when applicable |
| `checkpoint` | Runs required scenarios associated with the selected checkpoint policy |
| `release` | Runs every required release scenario |
| `diagnostic` | Runs required scenarios and selected optional scenarios |

The precise mapping belongs to `VALIDATION_MODES.md` and project validation policy.

A scenario script must produce the same semantic operation whenever it is selected.

---

## 9. File encoding and text format

A canonical `.gfs` scenario MUST use:

```text
UTF-8 without BOM
```

Canonical newline:

```text
LF
```

Readers MAY accept CRLF for compatibility.

Rules:

- a final newline is required;
- tabs SHOULD NOT be used for visual indentation;
- trailing whitespace SHOULD be absent;
- Unicode linguistic input is preserved exactly;
- decoding errors are configuration or execution errors;
- a scenario MUST NOT depend on the user's terminal encoding;
- scenario hashing uses canonical file bytes as stored.

---

## 10. Script structure

A canonical scenario contains these logical phases:

```text
1. Optional human comments
2. Grammar import or load
3. One or more marked validation sections
4. Explicit termination
```

Minimal structure:

```gf
-- Optional human-readable description.

i <entrypoint>

ps "GF_WORDBENCH_BEGIN <scenario-id>:<section-id>"
<GF command or pipeline>
ps "GF_WORDBENCH_END <scenario-id>:<section-id>"

q
```

The exact import target, commands and inputs are project-specific.

GF comments are not machine-authoritative scenario metadata.

The runner derives identity and requiredness from project configuration.

---

## 11. Human comment header

A leading comment block MAY document:

```text
purpose
entrypoint
input source
expected sections
normalization profile
gold policy
known GF-version constraints
```

Example:

```gf
-- Scenario: parse
-- Purpose: Validate representative parsing behavior.
-- Entrypoint: GrammarX
-- Gold: validation/gold/parse.gold
```

Rules:

- comments are guidance only;
- the runner MUST NOT require free-form comment parsing;
- comments MUST agree with authoritative configuration and project validation documentation;
- a stale comment is documentation drift;
- secrets and local absolute paths MUST NOT be placed in comments.

---

## 12. Grammar loading

A scenario SHOULD load one configured entrypoint explicitly.

Canonical forms may use the supported GF shell command:

```gf
i GrammarX
```

or the documented long equivalent:

```gf
import GrammarX
```

The chosen form must be supported by the selected GF version.

## 12.1 Entrypoint rules

- The target comes from active-project configuration or project validation specification.
- The target MUST NOT be inferred from the previous scenario.
- Every scenario runs in a fresh GF process unless an explicit future contract states otherwise.
- Load success is evaluated from all evidence, not exit code alone.
- `-retain` is used only when later operations require source retention.
- Loading a final grammar is distinct from compiling one source file.
- A scenario that uses a different entrypoint must document why.

## 12.2 Load section

A project MAY mark the load command itself:

```gf
ps "GF_WORDBENCH_BEGIN load:load-grammar"
i GrammarX
ps "GF_WORDBENCH_END load:load-grammar"
q
```

A load marker proves command flow completion.

It does not override fatal diagnostics emitted by GF.

---

## 13. Canonical marker syntax

New scenarios MUST emit full markers:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
GF_WORDBENCH_END <scenario-id>:<section-id>
```

Recommended GF shell emission:

```gf
ps "GF_WORDBENCH_BEGIN parse:parse-basic"
...
ps "GF_WORDBENCH_END parse:parse-basic"
```

The emitted output line must match exactly after line-ending and documented prompt normalization.

Compact legacy markers:

```text
GF_WORDBENCH_BEGIN <section-id>
GF_WORDBENCH_END <section-id>
```

MAY be read during migration but MUST NOT be emitted by new canonical scenarios.

---

## 14. Marker rules

- Marker prefixes are uppercase ASCII.
- One ASCII space separates prefix and identity.
- Identity contains exactly one `:` between scenario and section ID.
- Marker IDs are case-sensitive.
- Begin and end identities must match.
- Section IDs are unique within the scenario.
- Sections are not nested.
- An end without a begin is invalid.
- A begin without an end is invalid.
- Duplicate completion of the same section is invalid unless a future repeatable-section contract is introduced.
- Marker-like text inside linguistic output is not a marker unless it occupies the exact recognized marker line.
- The runner validates expected marker completion.
- The normalizer converts valid raw markers into canonical `.out` section delimiters.

---

## 15. Section identifiers

Recommended syntax:

```text
[a-z][a-z0-9-]*
```

A section ID describes one stable validation purpose.

Good examples:

```text
load-grammar
missing-functions
parse-basic
parse-negative
linearize-basic
morphology-noun
generation-bounded
```

Poor examples:

```text
test1
stuff
temp
output
new
```

A section ID change affects gold structure and is a contract change.

---

## 16. Section granularity

One section should contain one reviewable semantic output unit.

Create separate sections when:

- different commands have different acceptance criteria;
- output uses different normalization policy;
- one part may fail independently;
- project documentation maps requirements separately;
- a gold diff should isolate the change.

Do not create a section for every trivial command.

Do not combine unrelated parse, morphology and generation output into one unstructured section.

---

## 17. Output outside sections

Some GF output may occur outside markers:

- startup banner;
- prompt;
- import diagnostics;
- termination text;
- fatal errors;
- unexpected output.

Rules:

- raw output always preserves it;
- known non-semantic prompt or banner text may be normalized according to the selected profile;
- diagnostics remain visible;
- unknown outside-marker output is preserved and warned about;
- strict release validation may reject unexpected unscoped output;
- output outside sections MUST NOT be silently dropped.

A scenario cannot hide a fatal load error by marking only later output.

---

## 18. Explicit termination

A scenario SHOULD terminate with:

```gf
q
```

when required by the selected GF shell execution mode.

Rules:

- termination appears after the final end marker;
- commands after `q` are prohibited;
- a missing `q` is allowed only when the process contract supplies an equivalent EOF termination and the selected GF version handles it reliably;
- interactive confirmation prompts are prohibited;
- the runner still enforces a finite timeout;
- process termination does not prove section success.

Canonical v1 scenarios SHOULD include `q`.

---

## 19. Command ordering

Scenario command order is semantically significant.

The runner MUST pass the script to GF without reordering commands.

The scenario author MUST ensure:

- grammar load occurs before commands requiring the grammar;
- retained-source commands use the required import mode;
- input-producing commands precede dependent pipeline commands;
- begin markers occur before the output they own;
- end markers occur only after the operation completes;
- termination occurs last.

GF Wordbench MUST NOT optimize or combine commands across scenarios.

---

## 20. Permitted scenario purposes

Canonical scenario families include:

```text
load
missing
parse
linearize
morphology
generation
introspection
release-smoke
```

A project MAY define additional scenario IDs when they represent a stable validation purpose.

The scenario registry remains project-specific.

A new scenario family must not duplicate an existing scenario without a documented distinction.

---

## 21. Load scenarios

Purpose:

- prove a configured module or grammar can be imported;
- capture load diagnostics;
- establish a higher-level proof than isolated compilation.

Typical structure:

```gf
ps "GF_WORDBENCH_BEGIN load:load-grammar"
i GrammarX
ps "GF_WORDBENCH_END load:load-grammar"
q
```

Success requires:

- GF launched;
- no timeout;
- expected markers completed;
- no fatal load diagnostic;
- any configured artifact criteria pass.

---

## 22. Missing-function scenarios

Purpose:

- inspect unimplemented abstract functions;
- support release-gate evidence;
- compare expected omissions where a project is incomplete by policy.

Conceptual structure:

```gf
i GrammarX

ps "GF_WORDBENCH_BEGIN missing:missing-functions"
pg -missing
ps "GF_WORDBENCH_END missing:missing-functions"

q
```

The exact supported command and options depend on GF compatibility.

Rules:

- every missing function remains visible;
- the result is not inferred from absence of fatal errors;
- expected omissions must be documented by the active project;
- release policy decides whether any missing function blocks release;
- ordering is preserved unless the selected normalization profile explicitly treats the output as a set.

---

## 23. Parse scenarios

Purpose:

- validate that configured text produces expected parse behavior.

Conceptual structure:

```gf
i GrammarX

ps "GF_WORDBENCH_BEGIN parse:parse-basic"
p -lang=X -cat=S "example input"
ps "GF_WORDBENCH_END parse:parse-basic"

q
```

Rules:

- input is UTF-8 data;
- input MUST NOT be constructed from untrusted shell fragments;
- language and category are explicit when required;
- expected ambiguity belongs to project validation policy;
- parse trees remain visible;
- no parse is distinct from process error;
- negative parsing tests must be explicit;
- absence of fatal diagnostics alone is not parse success.

---

## 24. Linearization scenarios

Purpose:

- validate expected surface realization of configured abstract trees.

Conceptual structure:

```gf
i GrammarX

ps "GF_WORDBENCH_BEGIN linearize:linearize-basic"
l -lang=X <abstract-tree>
ps "GF_WORDBENCH_END linearize:linearize-basic"

q
```

Rules:

- abstract trees are scenario data or deterministic previous GF output;
- expected target language is explicit when needed;
- output orthography remains exact;
- empty output is distinct from absent output;
- variants and their ordering are documented;
- normalization MUST NOT case-fold, transliterate or repair strings.

---

## 25. Morphology scenarios

Purpose:

- inspect paradigms, forms, tables or inflectional behavior.

Rules:

- paradigm and feature labels remain visible;
- expected missing forms are explicit;
- table layout may be normalized only through an approved profile;
- language-specific morphology expectations belong to project documentation;
- a scenario must remain bounded;
- output is not repaired or completed by the runner.

A morphology scenario SHOULD use separate sections for unrelated paradigms.

---

## 26. Generation scenarios

Purpose:

- validate bounded generation or representative abstract/surface outputs.

Generation is especially sensitive to nondeterminism.

A generation scenario MUST define:

- a finite command-level result bound where GF supports one;
- a finite process timeout;
- an output-size limit;
- expected ordering policy;
- duplicate policy;
- whether exact gold comparison is valid.

Random generation MUST NOT be used for exact deterministic gold unless a stable seed and stable GF behavior are proven.

When exact output is not stable, the project should use bounded structural assertions instead of arbitrary normalization.

---

## 27. Introspection scenarios

Introspection may include:

- grammar information;
- retained-source inspection;
- operation listing;
- category or language queries;
- supported GF diagnostic commands.

Rules:

- introspection output is version-sensitive;
- GF version compatibility must be documented;
- banners and prompts are normalized only through approved rules;
- broad deletion of changed output is prohibited;
- introspection scenarios SHOULD be optional unless release policy depends on them.

---

## 28. Input sources

Scenario inputs may be:

```text
inline literal input
project/validation/inputs/<file>
deterministic output from an earlier command in the same scenario
configured project identity or entrypoint
```

## 28.1 Inline input

Use inline input when it is:

- short;
- stable;
- readable;
- not duplicated excessively;
- safely represented in GF shell syntax.

## 28.2 Input assets

Use a project input file when data is:

- long;
- shared;
- versioned independently;
- generated from reviewed research evidence;
- difficult to represent safely inline.

Input assets belong under:

```text
project/validation/inputs/
```

## 28.3 Input invariants

- Inputs are project-relative.
- Inputs exist before execution.
- Input files are read-only during normal validation.
- Input encoding is explicit.
- Scenario-to-input relationships are documented in project validation documentation.
- Missing required input is a configuration error.
- Absolute developer-machine paths are prohibited.
- Scenario input MUST NOT contain unauthorized operating-system commands.

---

## 29. Variable substitution

Canonical v1 `.gfs` scenarios are static files.

GF Wordbench MUST NOT perform arbitrary text templating over the script.

Permitted runner behavior is limited to externally defined execution configuration such as:

- executable path;
- working directory;
- GF search path;
- timeout;
- environment overrides.

If future parameter substitution is introduced, it requires:

- a versioned syntax;
- escaping rules;
- type restrictions;
- security review;
- project schema update;
- contract tests;
- migration policy.

Naive string replacement in `.gfs` files is prohibited.

---

## 30. Scenario assertions

GF Wordbench v1 evaluates assertions outside the script.

The canonical baseline assertion set is:

```text
process launched
process did not time out
exit policy passed
required markers completed
no fatal diagnostic violated the scenario
required artifacts exist
gold comparison passed when configured
```

Project-specific linguistic meaning is expressed through:

- scenario commands;
- section boundaries;
- reviewed gold output;
- `project/docs/VALIDATION_SPEC.md`;
- release criteria.

The script does not define a second custom assertion language.

---

## 31. Gold policy

Normal validation is read-only for project gold files.

Default gold path:

```text
project/validation/gold/<scenario-id>.gold
```

A scenario may be valid without a gold file only when its assertion strategy is explicitly documented.

Examples:

- artifact-existence validation;
- marker-only smoke scenario;
- expected process failure with structured diagnostic checks;
- nondeterministic bounded generation with non-exact criteria.

Rules:

- a required gold file must exist before release validation;
- a missing gold is not automatically created;
- normal validation is read-only;
- actual normalized output is written to the run directory;
- comparison occurs after normalization;
- a mismatch is `FAIL`, not normalization `ERROR`;
- gold updates require an explicit operation and review.

---

## 32. Normalization profile

Canonical default:

```text
profile_id = scenario-default
normalization_version = 1.0
```

Scenario-to-profile selection is controlled by framework/project configuration defined by the normalization specification.

The `.gfs` script MUST NOT implement its own output cleanup.

Prohibited inside scenarios solely to stabilize gold:

- removing paths through shell commands;
- sorting output through operating-system utilities;
- deleting diagnostics;
- rewriting Unicode;
- filtering lines with external processes;
- hiding timestamps by avoiding required evidence.

All comparison normalization belongs to the central normalizer.

---

## 33. Raw and derived artifacts

For each executed scenario, GF Wordbench records as applicable:

```text
raw/scenarios/<scenario-id>.stdout.txt
raw/scenarios/<scenario-id>.stderr.txt
raw/scenarios/<scenario-id>.out
raw/scenarios/<scenario-id>.gold.diff
```

Roles:

- `.stdout.txt`: raw GF stdout;
- `.stderr.txt`: raw GF stderr;
- `.out`: canonical normalized output;
- `.gold.diff`: derived comparison evidence.

The script file remains a project asset.

The output files remain run artifacts.

---

## 34. Scenario result

A canonical structured scenario result contains:

```text
scenario_id
script_path
required
status
command
working_directory
exit_code
timed_out
duration_ms
stdout_path
stderr_path
normalized_output_path
gold_path
gold_match
diagnostic_class
error_kind
primary_message
sections
artifacts
```

Rules:

- `scenario_id` matches registry identity;
- `script_path` is project-relative;
- `required` comes from the registry;
- raw paths are run-relative in persisted summaries;
- `gold_match` is `null` when no gold applies;
- section order matches execution order;
- produced artifacts are explicit;
- scenario ordering in `summary.json` follows configuration order.

---

## 35. Status semantics

Canonical validation status:

```text
OK
FAIL
ERROR
SKIPPED
```

### `OK`

GF executed and every required scenario criterion passed.

### `FAIL`

GF executed, evidence was interpretable, but a validation criterion failed.

Examples:

- gold mismatch;
- expected parse absent;
- unexpected missing functions;
- required marker not completed because the GF operation failed semantically;
- required project artifact absent after otherwise valid scenario execution.

### `ERROR`

GF Wordbench could not correctly execute or interpret the scenario.

Examples:

- missing script;
- invalid registry;
- process launch failure;
- timeout;
- malformed marker structure;
- unsupported normalization profile;
- raw evidence write failure;
- invalid encoding;
- scenario security rejection.

### `SKIPPED`

The scenario was intentionally not selected or could not run because a documented prerequisite failed.

A skipped required scenario affects the overall gate according to validation policy.

---

## 36. Execution state

Execution facts remain separate from validation status.

Relevant facts include:

```text
completed
timed_out
cancelled
launch_failed
```

Rules:

- timeout is not a normal GF semantic failure;
- cancellation is not `OK`;
- zero exit code cannot override missing markers or gold mismatch;
- non-zero exit code does not replace diagnostic interpretation;
- process state does not assign direct/downstream classification by itself.

---

## 37. Diagnostic classification

Scenario results may use:

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Scenario failure is normally `direct` when the scenario's own entrypoint, input or expectation fails.

It may be `downstream` when a known prerequisite module or checkpoint failure blocks meaningful execution.

Classification occurs after evidence capture.

The scenario runner MUST NOT infer dependency cascades without the classifier's evidence.

---

## 38. Timeout and bounds

Every scenario has a finite timeout.

Timeout source precedence is defined by the configuration model.

A scenario must also be bounded where relevant by:

- parse count;
- generation count;
- result size;
- input size;
- output size;
- finite command sequence.

Rules:

- no interactive waiting;
- no infinite generation;
- no unbounded pipeline;
- timeout is recorded explicitly;
- partial raw output is preserved;
- timed-out scenarios cannot pass gold comparison;
- release scenarios should use conservative, reproducible bounds.

---

## 39. Output-size policy

GF Wordbench SHOULD enforce raw and normalized output limits.

When a limit is exceeded:

- truncation is explicit;
- raw evidence records truncation state;
- exact comparison cannot pass from a retained prefix;
- the scenario result becomes `ERROR` or another documented non-success;
- the scenario must be redesigned if normal expected output exceeds safe limits.

A scenario author MUST NOT rely on intentionally enormous output as proof.

---

## 40. Determinism requirements

A scenario MUST avoid dependence on:

- current terminal directory;
- GUI state;
- previous scenario process state;
- local shell aliases;
- unrecorded environment variables;
- current time;
- random generation without controlled policy;
- locale-dependent sorting;
- user-specific absolute paths;
- terminal width;
- color support;
- network state;
- unordered external filesystem enumeration.

Equivalent configuration and supported GF versions should produce equivalent normalized evidence.

---

## 41. Process isolation

Canonical v1 runs each scenario in its own GF process.

Benefits:

- no hidden grammar state;
- no command leakage;
- independent timeouts;
- independent stdout/stderr;
- clear provenance;
- deterministic ordering;
- simpler failure containment.

Sharing one interactive GF process across scenarios is prohibited unless a future explicit external-tool contract replaces this rule.

---

## 42. Working directory

Every scenario process uses an explicit working directory.

The working directory is resolved from project configuration.

It MUST NOT depend on:

- the shell that launched GF Wordbench;
- IDE configuration;
- GUI startup directory;
- launcher shortcut location;
- previous scenario execution.

Relative paths inside the scenario must resolve according to the documented GF process contract.

---

## 43. GF search path

The effective GF search path is resolved centrally.

Scenarios MUST NOT construct a competing search path.

The runner records:

- executable;
- path arguments;
- working directory;
- applicable environment overrides.

Compilation and scenario execution must use compatible path resolution for the same project.

---

## 44. Security model

A `.gfs` scenario is executable input.

Scenario files from an untrusted project must be treated as untrusted code.

## 44.1 Prohibited behavior

Normal scenarios MUST NOT:

- invoke operating-system shell commands;
- pipe output to external tools;
- write outside approved run locations;
- delete files;
- modify source files;
- modify gold files;
- read credentials;
- depend on secrets;
- download network content;
- launch additional executables;
- create unbounded output;
- escape through unvalidated paths.

## 44.2 Shell escape

GF shell features capable of invoking the operating system are prohibited unless an explicit security policy and external-tool contract enable a specific use.

Default:

```text
disabled
```

## 44.3 Static security check

Before execution, the runner SHOULD inspect the script for prohibited constructs.

Static checking supplements process isolation.

It does not prove safety by itself.

---

## 45. Source mutation prohibition

Normal scenario execution MUST NOT modify:

```text
*.gf
project/project.toml
project/docs/
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

All generated evidence belongs under the run directory.

A gold-update command is a separate explicit project mutation operation.

---

## 46. Scenario hash

The runner SHOULD record a cryptographic hash of the executed scenario bytes.

Recommended algorithm:

```text
SHA-256
```

Purpose:

- provenance;
- historical comparison;
- stale-evidence detection;
- proof that the reported script matches the executed file.

The scenario hash does not replace the project path or scenario ID.

---

## 47. Scenario ordering

Scenario execution order is the order declared in `project.toml`.

Required scenarios execute in their declared order.

Optional scenarios execute in their declared order when selected.

The runner MUST NOT:

- sort IDs alphabetically;
- order by filesystem enumeration;
- group by filename unless configuration says so;
- run scenarios concurrently when order-sensitive evidence would become ambiguous.

Parallel execution may be introduced only through an explicit deterministic scheduling contract.

---

## 48. Dependencies between scenarios

Canonical v1 scenarios are independent.

A scenario MUST NOT depend on:

- another scenario's GF process;
- another scenario's temporary files;
- another scenario's unregistered output;
- execution order for semantic state.

A project may require one validation result before selecting another, but each script remains independently executable from project inputs and configuration.

Cross-scenario artifact dependencies require a future explicit contract.

---

## 49. Negative scenarios

A negative scenario intentionally validates rejection or failure.

Examples:

- input should not parse;
- a forbidden form should be absent;
- an invalid tree should produce a known diagnostic.

Rules:

- expected failure is documented;
- process launch and marker completion remain required where possible;
- expected diagnostic or normalized output is explicit;
- broad acceptance of any error is prohibited;
- an infrastructure error cannot satisfy a negative linguistic test;
- a timeout cannot satisfy expected rejection.

---

## 50. Scenario completeness

A scenario is complete when:

```text
[ ] ID registered
[ ] Script exists at canonical path
[ ] Purpose documented
[ ] Entrypoint or target documented
[ ] Inputs reviewed
[ ] Commands bounded
[ ] Sections use canonical markers
[ ] Section IDs are unique
[ ] Termination is explicit
[ ] Normalization profile exists
[ ] Gold or alternative assertion strategy exists
[ ] Timeout policy exists
[ ] Security check passes
[ ] Unit/contract tests exist
[ ] Project validation specification references it
[ ] Coverage matrix references it
```

A placeholder scenario is not release evidence.

---

## 51. Canonical load example

```gf
-- Load the configured grammar entrypoint.

ps "GF_WORDBENCH_BEGIN load:load-grammar"
i GrammarX
ps "GF_WORDBENCH_END load:load-grammar"

q
```

This is a structural example.

The real project must replace `GrammarX` with its configured entrypoint.

---

## 52. Canonical parse example

```gf
-- Validate one representative parse.

i GrammarX

ps "GF_WORDBENCH_BEGIN parse:parse-basic"
p -lang=X -cat=S "Example sentence."
ps "GF_WORDBENCH_END parse:parse-basic"

q
```

Project-specific language codes, categories, input strings and expected trees belong to the active project.

---

## 53. Canonical linearization example

```gf
-- Validate one representative linearization.

i GrammarX

ps "GF_WORDBENCH_BEGIN linearize:linearize-basic"
l -lang=X ExampleTree
ps "GF_WORDBENCH_END linearize:linearize-basic"

q
```

`ExampleTree` is illustrative only.

The project validation specification owns the real tree and expected string.

---

## 54. Multi-section example

```gf
i GrammarX

ps "GF_WORDBENCH_BEGIN morphology:noun-singular"
<GF morphology command>
ps "GF_WORDBENCH_END morphology:noun-singular"

ps "GF_WORDBENCH_BEGIN morphology:noun-plural"
<GF morphology command>
ps "GF_WORDBENCH_END morphology:noun-plural"

q
```

Each section should map to a distinct reviewable requirement.

---

## 55. Invalid examples

### Missing registration

```text
project/validation/scenarios/parse-extra.gfs
```

exists but is absent from both registry arrays.

Result: not a valid active scenario.

### Filename mismatch

Registry:

```text
parse-basic
```

File:

```text
parse_basic.gfs
```

Result: configuration error.

### Missing end marker

```gf
ps "GF_WORDBENCH_BEGIN parse:parse-basic"
p "Example"
q
```

Result: scenario non-success.

### Nested sections

```gf
ps "GF_WORDBENCH_BEGIN parse:outer"
ps "GF_WORDBENCH_BEGIN parse:inner"
...
ps "GF_WORDBENCH_END parse:inner"
ps "GF_WORDBENCH_END parse:outer"
```

Result: invalid canonical v1 marker structure.

### Hidden gold mutation

```text
scenario command writes project/validation/gold/parse.gold
```

Result: prohibited.

---

## 56. Compatibility

## 56.1 Compatible changes

Usually compatible:

- adding comments;
- clarifying purpose;
- adding an optional section that is excluded from existing gold by explicit versioned policy;
- replacing a long GF command with an equivalent documented alias under the same supported versions;
- adding a new optional scenario ID.

Compatibility still requires tests.

## 56.2 Breaking changes

Breaking:

- renaming the scenario ID;
- moving the script;
- changing required/optional classification;
- changing the entrypoint;
- changing section IDs;
- changing marker syntax;
- changing command order;
- changing input meaning;
- changing assertion strategy;
- changing normalization profile or version in a gold-affecting way;
- changing gold ownership;
- making a bounded scenario unbounded;
- changing expected PGF or produced artifact meaning.

Breaking changes require coordinated project migration.

---

## 57. Deprecation

A deprecated scenario remains registered until its replacement and migration are complete.

Deprecation should record:

```text
old scenario ID
replacement ID
reason
first deprecated release
planned removal release
gold migration
coverage migration
```

Scenario IDs MUST NOT be reused after retirement for unrelated behavior.

Historical run results may retain retired IDs.

---

## 58. Scenario change workflow

A scenario change is complete only when all applicable elements are reviewed.

```text
[ ] Scenario ID identified
[ ] Registry reviewed
[ ] Required/optional status reviewed
[ ] Filename reviewed
[ ] Entrypoint reviewed
[ ] Inputs reviewed
[ ] Command compatibility reviewed
[ ] Marker identities reviewed
[ ] Section ordering reviewed
[ ] Timeout and bounds reviewed
[ ] Security reviewed
[ ] Normalization profile reviewed
[ ] Raw evidence reviewed
[ ] Gold diff reviewed
[ ] Project validation specification updated
[ ] Coverage matrix updated
[ ] Project interfile lock updated
[ ] Tests updated
[ ] Migration note added when breaking
```

Change record template:

```text
Scenario ID:
Purpose:
Current script:
New behavior:
Entrypoint:
Inputs:
Sections:
Required:
Normalization profile:
Gold:
GF versions:
Security:
Compatibility:
Migration:
Tests:
```

---

## 59. Required tests

Recommended framework tests:

```text
tests/scenarios/
├── test_scenario_registry.py
├── test_scenario_paths.py
├── test_scenario_markers.py
├── test_scenario_runner.py
├── test_scenario_security.py
├── test_scenario_results.py
├── test_scenario_ordering.py
├── test_scenario_timeout.py
└── test_scenario_gold_contract.py
```

## 59.1 Registry tests

- duplicate ID;
- ID in both arrays;
- invalid ID syntax;
- missing required file;
- missing selected optional file;
- undeclared file;
- deterministic order;
- filename mismatch.

## 59.2 Marker tests

- valid single section;
- valid multiple sections;
- wrong scenario prefix;
- duplicate section ID;
- end without begin;
- begin without end;
- nested section;
- marker-like linguistic output;
- compact legacy marker migration.

## 59.3 Runner tests

- successful execution;
- non-zero exit;
- timeout;
- cancellation;
- stdout only;
- stderr only;
- fatal diagnostic on stdout;
- fatal diagnostic on stderr;
- paths containing spaces;
- UTF-8 input;
- explicit working directory;
- explicit termination;
- missing `q` compatibility policy.

## 59.4 Security tests

- shell escape;
- external pipe;
- source write attempt;
- gold write attempt;
- path traversal;
- unbounded generation pattern;
- excessive output;
- arbitrary template placeholder;
- secret-like environment access.

## 59.5 Gold tests

- exact match;
- mismatch;
- missing required gold;
- scenario ID mismatch;
- normalization version mismatch;
- normal execution leaves gold unchanged;
- explicit gold update is separate.

---

## 60. Real-GF integration fixture

A small fixture grammar SHOULD provide scenarios for:

```text
load
missing
parse
linearize
morphology
bounded generation
```

The fixture should prove:

- GF process invocation;
- marker emission;
- Unicode handling;
- raw stdout and stderr capture;
- normalization;
- gold comparison;
- timeout containment where safe;
- supported GF-version behavior.

Real-GF tests SHOULD be marked separately from fast unit tests.

---

## 61. Automated checks

Recommended command:

```text
gf-wordbench scenarios check
```

Strict mode:

```text
gf-wordbench scenarios check --strict
```

The checker should verify:

1. every registered ID is valid;
2. IDs are unique;
3. every selected ID has one canonical file;
4. filenames match IDs;
5. scripts use UTF-8;
6. scripts have final newlines;
7. canonical markers are well formed;
8. section IDs are unique;
9. termination policy is satisfied;
10. prohibited commands are absent;
11. referenced inputs exist;
12. required gold files exist;
13. gold headers match scenario IDs;
14. normalization profiles exist;
15. required scenarios are covered by project validation documentation;
16. scenario order is deterministic;
17. no undeclared permanent scenario is present in strict mode.

---

## 62. Drift indicators

Scenario drift exists when:

- a required ID has no file;
- a file is renamed without registry update;
- an undeclared file is assumed active;
- the script loads a different entrypoint from project documentation;
- markers use old IDs;
- a required section no longer completes;
- a new section appears without validation review;
- a scenario depends on previous process state;
- scenario order comes from filesystem enumeration;
- a scenario writes into project gold;
- a script invokes the operating system;
- a scenario becomes unbounded;
- output normalization occurs inside the script;
- a gold file changes without scenario review;
- comments describe different behavior from the script;
- the runner and project disagree about requiredness;
- release validation omits a required scenario;
- a missing required gold passes automatically;
- a timeout is reported as expected negative behavior;
- the script path is serialized inconsistently;
- a scenario result lacks raw evidence paths.

Every drift indicator requires restoration or a coordinated contract change.

---

## 63. Responsibility boundaries

### Project maintainers

Own:

- scenario purpose;
- registry membership;
- script content;
- input assets;
- gold expectations;
- project validation documentation.

### Project loader

Owns:

- registry loading;
- ID validation;
- project-relative path resolution;
- required/optional distinction.

### Scenario runner

Owns:

- process request;
- raw capture;
- timeout handling;
- marker validation;
- scenario execution facts;
- produced artifact references.

### Normalizer

Owns:

- central output normalization;
- canonical `.out`;
- normalization warnings and errors.

### Gold comparator

Owns:

- actual/expected comparison;
- deterministic diff;
- `gold_match`.

### Classifier

Owns:

- direct/downstream/ambiguous relationship interpretation.

### Reports

Consume structured scenario results.

They do not run or reinterpret scenarios independently.

---

## 64. Related documents

### GF execution

- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/gf/GF_SCRIPT_EXECUTION.md`
- `docs/gf/GF_OUTPUT_NORMALIZATION.md`
- `docs/gf/GF_VERSION_COMPATIBILITY.md`

### Validation

- `docs/validation/SCENARIO_VALIDATION.md`
- `docs/validation/VALIDATION_MODES.md`
- `docs/validation/RELEASE_GATES.md`

### Scenario guidance

- `docs/scenarios/WRITING_GFS_SCENARIOS.md`
- `docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md`
- `docs/scenarios/OUTPUT_NORMALIZATION.md`
- `docs/scenarios/GOLDEN_TESTS.md`
- `docs/scenarios/UPDATING_GOLD_FILES.md`

### Architecture and schemas

- `docs/architecture/ARTIFACT_MODEL.md`
- `docs/architecture/PROCESS_EXECUTION_MODEL.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/reference/STATUS_VALUES.md`

### Active project

- `project/project.toml`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`
- `project/docs/VALIDATION_SPEC.md`
- `project/docs/TEST_COVERAGE_MATRIX.md`
- `project/validation/scenarios/README.md`

---

## 65. Final enforcement rule

A scenario is not an informal command transcript.

It is a project contract connecting:

```text
project configuration
    → scenario ID
    → .gfs script
    → GF entrypoint
    → marked raw output
    → normalized output
    → gold or explicit assertion
    → structured scenario result
    → release decision
```

Therefore:

> No scenario identity, command sequence, marker, input, entrypoint, assertion, normalization profile or gold relationship may change through an isolated file edit.

Every scenario change must remain registered, deterministic, bounded, secure, evidence-preserving, tested and reviewable as one complete project change.
