# ADR-0004 — Use Native GF Shell Scenarios

**Decision ID:** `ADR-0004`  
**Status:** Accepted  
**Decision date:** `2026-07-22`  
**Last reviewed:** `2026-07-22`  
**Owners:** GF Wordbench maintainers  
**Applies to:** Scenario authoring, scenario execution, project configuration, validation modes, gold comparison, reports, release gates, and GF integration  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\decisions\ADR-0004-NATIVE-GFS-SCENARIOS.md`

---

## 1. Decision

GF Wordbench will use native Grammatical Framework shell scripts (`.gfs`) as its executable scenario format.

GF Wordbench will:

- execute each registered `.gfs` scenario with the real GF executable;
- pass scenario content through standard input without an intermediate shell;
- start a fresh GF process for each scenario;
- preserve stdout and stderr separately before interpretation;
- require finite timeouts;
- recognize a small GF Wordbench marker protocol emitted through valid GF commands;
- evaluate assertions outside GF;
- normalize captured output through a versioned normalization contract;
- compare normalized output with reviewed `.gold` files when configured;
- record the scenario script hash, execution evidence, assertions, artifacts, and result;
- keep required and optional scenarios distinct;
- treat missing required scenarios as configuration failures;
- prohibit normal validation from modifying `.gfs` or `.gold` files.

GF Wordbench will not:

- create a second language that replaces GF shell commands;
- parse or reinterpret GF command syntax;
- emulate GF parsing, linearization, generation, morphology, or introspection;
- use Python functions as the canonical project scenario format;
- treat process exit code zero as sufficient scenario success;
- silently accept unsupported, skipped, or incomplete commands;
- execute operating-system shell escapes in normal project scenarios;
- update gold files during ordinary validation.

---

## 2. Context

GF Wordbench must validate more than source compilation.

A complete GF language project also needs executable checks for behavior such as:

```text
load an entrypoint
inspect available concrete languages
detect missing linearizations
linearize reviewed abstract trees
parse reviewed strings
exercise parse-linearize round trips
inspect morphology
perform bounded generation
inspect retained operations or source interfaces
validate final PGF behavior
```

These operations are already provided by the GF shell.

The project therefore needs a scenario mechanism that:

- exercises the authoritative GF runtime;
- remains readable by GF developers;
- can be executed manually outside GF Wordbench;
- can be stored with the active project;
- supports stable regression evidence;
- works in CLI, GUI, automation, and release validation;
- remains language-specific without making the framework language-specific;
- avoids duplicating GF semantics in Python;
- preserves enough raw evidence for diagnosis.

The predecessor audit system focused primarily on scanning and compilation.

The final GF Wordbench architecture adds scenario-level validation as a peer validation stage.

---

## 3. Architectural problem

Several possible scenario formats were considered.

A custom format could make metadata and assertions convenient, but it would create a second command language between project authors and GF.

Direct Python tests could be expressive, but they would couple language-project validation to framework internals and permit tests to bypass the GF process boundary.

Raw shell scripts could invoke GF, but they would be platform-specific, harder to secure, and inconsistent across Windows and POSIX systems.

The decision must preserve this authority boundary:

```text
GF
    owns GF commands and grammar semantics

GF Wordbench
    owns execution, evidence capture, markers, assertions,
    normalization, gold comparison, classification, and reporting

active project
    owns scenario purpose, script, inputs, expected output,
    mode applicability, and release requirement
```

---

## 4. Decision drivers

The selected approach must satisfy the following requirements.

### 4.1 Semantic authority

GF must remain authoritative for:

- grammar loading;
- type-checked tree operations;
- parsing;
- linearization;
- generation;
- morphology;
- grammar introspection;
- GF diagnostics.

### 4.2 Manual reproducibility

A project maintainer should be able to inspect and execute the scenario directly with GF.

### 4.3 Project ownership

Scenario files must live with the active language project rather than inside reusable framework code.

### 4.4 Framework neutrality

The framework must not hardcode one language’s:

- module names;
- categories;
- examples;
- expected strings;
- expected trees;
- scenario inventory.

### 4.5 Evidence preservation

The runner must preserve:

- executable;
- arguments;
- working directory;
- GF path;
- standard input source;
- script hash;
- exit code;
- execution state;
- stdout;
- stderr;
- timeout;
- generated artifacts;
- normalized output;
- assertions;
- gold comparison.

### 4.6 Determinism

Release scenarios must use:

- explicit entrypoints;
- explicit languages;
- explicit categories when material;
- deterministic input order;
- bounded generation;
- finite timeout;
- stable marker order;
- versioned normalization.

### 4.7 Security

Normal scenarios must not become unrestricted operating-system scripts.

### 4.8 Migration simplicity

Existing GF scripts and familiar shell commands should be reusable with limited adaptation.

---

## 5. Selected scenario model

The active project stores scenarios under:

```text
project/validation/scenarios/
```

Canonical script path:

```text
project/validation/scenarios/<scenario-id>.gfs
```

Optional project inputs:

```text
project/validation/inputs/
```

Reviewed gold files:

```text
project/validation/gold/<scenario-id>.gold
```

Scenario metadata belongs to the project registry and project validation documentation.

It does not belong in invalid or pseudo-syntax lines inside the `.gfs` file.

The project registry resolves at least:

```text
scenario ID
script path
required or optional state
applicable modes
checkpoint association
entrypoint
input assets
gold path
timeout class
assertion profile
```

---

## 6. Canonical execution boundary

The preferred execution model is:

```text
<gf-executable>
stdin = UTF-8 contents of <scenario>.gfs
working directory = resolved project root or documented scenario directory
timeout = finite scenario timeout
shell = false
```

The scenario runner owns this request.

Conceptual provider:

```text
app/audit/scenario_runner.py
```

The runner must use the same resolved:

- GF executable;
- GF version;
- project root;
- GF search path;
- environment policy;

as other validation stages.

The runner must not independently rediscover or reconstruct these values.

---

## 7. Fresh-process rule

Each scenario runs in a fresh GF process.

A scenario must not depend on:

- a grammar imported by another scenario;
- shell history from another scenario;
- command macros defined elsewhere;
- current terminal state;
- another scenario’s working directory;
- execution order;
- unregistered generated files.

This provides:

- reproducibility;
- isolation;
- deterministic failure attribution;
- safe independent retry;
- future parallel execution;
- clear timeout ownership.

A scenario must explicitly load every grammar or resource it requires.

---

## 8. Marker protocol

A native GF script may continue processing after a command problem, and process exit alone does not prove that all intended checks completed.

GF Wordbench therefore defines a narrow marker protocol.

Markers must be emitted through a valid GF command such as:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=parse-basic"
```

Required scenario markers:

```text
__GF_WORDBENCH_SCENARIO_BEGIN__
__GF_WORDBENCH_SCENARIO_END__
```

Optional section markers:

```text
__GF_WORDBENCH_SECTION_BEGIN__
__GF_WORDBENCH_SECTION_END__
```

A canonical scenario structure is:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=<scenario-id>"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i <ENTRYPOINT>.gf
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=check"
<GF COMMANDS>
ps "__GF_WORDBENCH_SECTION_END__ id=check"

ps "__GF_WORDBENCH_SCENARIO_END__ id=<scenario-id>"
q
```

The runner interprets only the GF Wordbench marker protocol.

It does not interpret the GF commands between markers.

---

## 9. Marker guarantees

Markers provide evidence that:

- scenario processing started;
- declared sections were reached;
- declared sections completed;
- the final scenario marker was reached;
- marker order was structurally valid.

Markers do not independently prove that:

- every GF command succeeded;
- expected linguistic output was produced;
- no fatal diagnostic occurred;
- required artifacts exist;
- gold output matches.

Scenario success therefore combines markers with process, diagnostic, assertion, artifact, and gold evidence.

---

## 10. Success model

A required scenario succeeds only when all applicable conditions hold:

```text
configuration is valid
and the script exists
and the script hash is recorded
and GF launches
and execution does not time out
and execution is not cancelled
and raw stdout is captured
and raw stderr is captured
and required markers are valid
and required sections complete
and no fatal diagnostic invalidates the scenario
and required assertions pass
and required artifacts exist
and required gold comparison matches
```

A zero exit code is evidence, not complete success.

A nonzero exit normally fails the scenario, while raw diagnostics remain authoritative evidence.

---

## 11. Scenario result

Scenario execution returns a structured `ScenarioResult` or final equivalent.

The result must represent at least:

```text
scenario identifier
script path
script hash
required or optional state
applicable mode
validation status
execution state
diagnostic class
error kind
command
working directory
GF executable
GF version
effective GF path
exit code
timeout state
duration
stdout path
stderr path
normalized output path
gold path when applicable
assertion results
primary message
detailed message
produced artifacts
```

Scenario results are peers of file results in the final run model.

Reports consume scenario results.

Reports do not rerun scenarios.

---

## 12. Raw-evidence rule

Raw evidence must be written before normalization or comparison.

Canonical paths are determined by the run artifact model.

Conceptual paths:

```text
raw/scenarios/<scenario-id>.out.txt
raw/scenarios/<scenario-id>.err.txt
scenarios/<scenario-id>.normalized.txt
```

Raw stdout and stderr remain separate.

Normalization must not overwrite them.

A diagnostic parser or report may reference raw evidence but must not replace it.

---

## 13. Normalization rule

Scenario output may contain unstable nonsemantic material such as:

- GF prompts;
- approved version banners;
- absolute run paths;
- platform newline differences;
- temporary run identifiers;
- approved timing noise.

A versioned normalization profile may remove or canonicalize such material.

Normalization must not remove or rewrite linguistically meaningful content such as:

- linearized strings;
- abstract trees;
- function names;
- missing-linearization names;
- ambiguity;
- word order;
- inflection;
- category identity;
- assertion-relevant diagnostics.

A normalization change that alters existing gold meaning is a breaking scenario-output contract change.

---

## 14. Gold comparison

Gold files are reviewed project source assets.

Comparison occurs after normalization.

A missing required gold file is a failure.

A gold mismatch is a validation failure.

Normal execution must not update gold.

The explicit gold-update workflow must:

1. preserve current gold;
2. show the normalized difference;
3. require deliberate authorization;
4. write atomically;
5. record the normalization version;
6. require the proving validation mode to run again.

Gold represents accepted expected behavior.

It is not created automatically from current output.

---

## 15. Assertions

Assertions are evaluated by GF Wordbench against captured evidence.

They are not implemented as a replacement command language inside `.gfs`.

Supported assertion concepts may include:

```text
required marker
forbidden marker
required text
forbidden text
required regular expression
forbidden regular expression
exact normalized section
empty normalized section
nonempty normalized section
bounded result count
required artifact
forbidden fatal diagnostic
gold match
```

Scenario metadata or the project validation specification owns assertion configuration.

The `.gfs` file owns executable GF commands and marker emission.

---

## 16. Required and optional scenarios

The active project registry distinguishes:

```text
required scenarios
optional scenarios
```

A required applicable scenario that is:

- missing;
- unreadable;
- invalid;
- timed out;
- incomplete;
- assertion-failing;
- artifact-failing;
- gold-mismatching;

fails the applicable validation mode.

An optional scenario remains visible when run.

Its failure blocks release only when project release policy explicitly says so.

The framework must not infer requirement from filename.

---

## 17. Validation-mode integration

### 17.1 Quick

May run one small registered smoke scenario or an explicitly selected scenario.

### 17.2 Checkpoint

Runs scenarios assigned to the selected checkpoint and its required closure.

### 17.3 Release

Runs every required release scenario and enforces all required assertions, golds, and artifacts.

### 17.4 Diagnostic

May run one focused scenario, all scenarios, or additional bounded introspection scenarios with expanded evidence.

A successful diagnostic scenario run does not make the project release-eligible.

---

## 18. Scenario authoring constraints

Release-relevant scenarios must be:

```text
native GF scripts
project-owned
registered
single-purpose
fresh-process safe
explicit
bounded
deterministic
machine-marked
asserted
evidence-preserving
non-destructive
version-compatible
reviewable
```

Potentially expansive commands must have explicit limits.

Examples:

```text
generation depth
generation count
parse input count
process timeout
output-size limit
```

Random generation may be used diagnostically.

It must not produce exact gold unless determinism is explicitly guaranteed.

---

## 19. Security boundary

`.gfs` files are trusted executable project inputs to GF.

Normal scenarios must not use GF shell mechanisms that invoke operating-system commands.

Prohibited by default:

```text
shell escape
system pipe
operating-system command
network command
unrestricted external process
```

Scenario file reads must be restricted to:

- registered project inputs;
- approved grammar roots;
- current run-owned paths where explicitly allowed.

Scenario file writes should be avoided.

When a scenario intentionally creates an artifact:

- the path must be run-owned;
- the artifact must be registered;
- overwrite behavior must be explicit;
- project sources, scenarios, inputs, and golds must remain unchanged.

Untrusted projects require an external operating-system or container sandbox.

GF Wordbench is not itself a complete hostile-code sandbox.

---

## 20. Alternatives considered

### 20.1 Custom YAML or TOML scenario language

Example concept:

```yaml
steps:
  - import: GrammarX.gf
  - parse:
      language: LangX
      category: Utt
      input: example
```

Rejected as the canonical executable format.

Reasons:

- duplicates GF shell semantics;
- requires a translator for every supported GF command and option;
- creates version drift between GF and GF Wordbench;
- limits advanced GF workflows;
- makes manual reproduction less direct;
- creates new quoting, piping, and type-conversion problems;
- expands maintenance and testing cost;
- risks false confidence when the translation differs from real GF use.

TOML remains appropriate for scenario registration and metadata, not command execution.

---

### 20.2 Python scenario functions

Example concept:

```python
def scenario(context):
    context.import_grammar(...)
    context.parse(...)
```

Rejected as the project scenario contract.

Reasons:

- couples language projects to Python framework internals;
- permits bypassing process and evidence contracts;
- makes scenarios harder to execute outside GF Wordbench;
- creates arbitrary code-execution risk;
- encourages direct use of private helpers;
- weakens language-neutral project portability;
- requires Python API compatibility for project tests.

Python remains appropriate for the scenario runner and framework tests.

---

### 20.3 Operating-system shell scripts

Examples:

```text
.bat
.ps1
.sh
```

Rejected as the canonical cross-platform scenario format.

Reasons:

- platform-specific;
- quoting and redirection differ;
- harder path handling;
- unrestricted operating-system capabilities;
- inconsistent timeout and child-process control;
- greater injection risk;
- duplicates launcher behavior.

OS scripts may launch GF Wordbench, but they do not define linguistic scenarios.

---

### 20.4 Direct GF command arguments without scripts

Example concept:

```text
gf-wordbench scenario --command "p ..."
```

Rejected for multi-step project validation.

Reasons:

- poor reviewability;
- difficult marker structure;
- difficult version control;
- command quoting problems;
- weak association with inputs and gold;
- unsuitable for checkpoint and release scenario inventories.

A single diagnostic command may be supported separately without replacing project scenarios.

---

### 20.5 PGF runtime API tests only

Rejected as the only scenario mechanism.

Reasons:

- not every project validation concern is exposed identically through one PGF API;
- source-level operations and `pg -missing` may be needed;
- final PGF does not replace checkpoint or source-entrypoint evidence;
- introduces runtime-language binding dependencies;
- loses direct GF shell reproducibility.

PGF runtime tests may be added as complementary external-tool contracts.

---

### 20.6 Parse Markdown examples as tests

Rejected.

Reasons:

- documentation prose is not an executable contract;
- quoting and expected output are ambiguous;
- machine readers would depend on human formatting;
- report and documentation changes could break tests;
- no clear process, timeout, or artifact ownership.

Documentation may reference registered scenarios.

---

### 20.7 No scenario layer

Rejected.

Compilation alone cannot prove:

- reviewed linearization;
- parsing behavior;
- round-trip behavior;
- morphology;
- bounded generation;
- missing-linearization expectations;
- runtime entrypoint loading;
- project-defined linguistic release examples.

---

## 21. Positive consequences

The decision provides:

- direct use of GF’s authoritative shell;
- manual reproducibility;
- low conceptual overhead for GF developers;
- broad access to existing GF commands;
- language-specific scenarios outside reusable framework code;
- deterministic scenario inventories;
- clean separation between commands and assertions;
- reusable raw evidence;
- versioned gold comparison;
- checkpoint and release integration;
- no competing GF interpreter;
- simpler migration of existing `.gfs` scripts;
- clear project-to-entrypoint and project-to-gold contracts.

---

## 22. Negative consequences

The decision also introduces costs.

### 22.1 GF shell output is not a stable machine protocol

Mitigation:

- preserve raw output;
- use markers;
- version normalization;
- use assertions;
- test supported GF versions.

### 22.2 Exit status may not describe every command outcome

Mitigation:

- require marker completion;
- detect fatal diagnostics;
- require expected output or artifacts;
- compare gold where appropriate.

### 22.3 Scenario metadata is stored separately

Mitigation:

- use one project scenario registry;
- validate script-to-registry consistency;
- lint filenames, IDs, inputs, and gold mappings.

### 22.4 `.gfs` files can invoke powerful commands

Mitigation:

- trust only project-owned scenarios;
- lint prohibited commands;
- restrict paths;
- use finite timeouts;
- require external sandboxing for untrusted projects.

### 22.5 GF version changes may affect output

Mitigation:

- record GF version;
- maintain compatibility policy;
- test normalization;
- review gold changes;
- preserve raw output.

### 22.6 Each scenario starts a new process

Mitigation:

- keep scenarios focused;
- permit future controlled parallelism;
- prioritize reproducibility and isolation over startup optimization.

---

## 23. Neutral consequences

The following remain separate decisions:

- exact persisted `ScenarioResult` field layout;
- exact project registry TOML syntax;
- exact marker parser implementation;
- exact normalization rules;
- exact gold update command;
- whether PGF runtime bindings are added later;
- whether optional scenario parallelism is implemented;
- exact report layout.

These decisions must remain compatible with this ADR.

---

## 24. Implementation requirements

The final implementation must provide or resolve the following components.

### 24.1 Project loader

Must resolve:

```text
scenario ID
script path
required or optional
mode applicability
checkpoint mapping
entrypoint
inputs
gold
timeout
assertions
```

### 24.2 Scenario linter

Must detect at least:

```text
missing script
duplicate ID
filename and ID mismatch
missing begin marker
missing end marker
missing final q
invalid marker order
unresolved placeholders
absolute unsafe path
parent traversal
prohibited system command
unbounded generation
unregistered input
missing required gold
unsupported command where detectable
```

### 24.3 Scenario runner

Must:

- start a fresh GF process;
- use structured process invocation;
- pass UTF-8 script content through stdin;
- define working directory explicitly;
- enforce timeout;
- capture stdout and stderr separately;
- save raw evidence first;
- parse markers;
- detect fatal diagnostics;
- invoke normalization;
- invoke assertions;
- invoke gold comparison;
- register artifacts;
- return structured results.

### 24.4 Normalizer

Must:

- be deterministic;
- be versioned;
- preserve semantic GF output;
- normalize LF/CRLF differences;
- document every removed noise class;
- never overwrite raw evidence.

### 24.5 Gold comparator

Must:

- compare normalized output;
- preserve diff evidence;
- fail on missing required gold;
- never update gold during normal validation.

### 24.6 Orchestrator

Must:

- select scenarios by mode and target;
- preserve deterministic order;
- distinguish required and optional scenarios;
- include scenario results in the final run;
- evaluate release gates from structured results.

### 24.7 Reports

Must show:

- scenario ID;
- required or optional state;
- execution state;
- validation status;
- primary diagnostic;
- raw evidence paths;
- normalized output path;
- gold result;
- artifact paths.

Reports must not rerun GF.

---

## 25. Required tests

Framework tests must cover:

```text
fresh process per scenario
UTF-8 stdin
explicit working directory
finite timeout
launch failure
nonzero exit
stdout-only output
stderr-only diagnostic
stdout and stderr together
scenario begin marker
scenario end marker
section markers
missing end marker
duplicate marker
mismatched section ID
invalid marker order
zero exit with incomplete scenario
fatal diagnostic with zero exit
assertion pass
assertion failure
normalization
gold match
gold mismatch
missing required gold
optional scenario failure
required scenario failure
output truncation
prohibited system command
script hash
deterministic scenario order
path containing spaces
CRLF input
cancellation
```

Real GF integration tests should cover a small neutral fixture:

```text
load
parse
linearize
pg -missing
bounded generation
PGF load when applicable
```

Tests requiring real GF must be marked separately.

---

## 26. Migration strategy

The predecessor audit tool did not provide the final scenario layer.

Migration proceeds as follows:

1. create `project/validation/scenarios/`;
2. create `project/validation/inputs/`;
3. create `project/validation/gold/`;
4. identify existing manual GF shell checks;
5. convert them into focused project-owned `.gfs` scripts;
6. add canonical markers;
7. add explicit `q`;
8. register scenarios in project configuration;
9. identify required and optional scenarios;
10. assign modes and checkpoints;
11. define assertions;
12. capture baseline normalized output;
13. review and approve gold files;
14. add scenario-runner tests;
15. add release gates;
16. run checkpoint and release validation.

Existing manual `.gfs` scripts may be reused when they satisfy the final contract.

They must not be accepted solely because they run manually.

---

## 27. Compatibility policy

Required scenarios must use commands and options supported by the declared GF compatibility range.

When GF behavior changes:

1. preserve old raw evidence;
2. record the new GF version;
3. run compatibility scenarios;
4. inspect marker behavior;
5. inspect diagnostic behavior;
6. inspect normalization differences;
7. review gold changes;
8. update compatibility documentation;
9. update this ADR only when the architectural decision changes.

A new GF command does not require a new ADR when it fits the native scenario model.

A replacement of `.gfs` as the canonical scenario format requires a superseding ADR.

---

## 28. Operational rules

Scenario execution must not:

- run without a finite timeout;
- depend on the terminal working directory;
- use a hidden GF executable;
- use a hidden GF path;
- modify project source;
- modify scenario scripts;
- modify gold;
- discard stderr;
- normalize before raw capture;
- mark missing required evidence as success.

Partial scenario evidence should be preserved after:

```text
timeout
cancellation
GF failure
assertion failure
gold mismatch
report failure
```

---

## 29. Documentation requirements

This ADR is implemented through:

```text
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/validation/VALIDATION_MODES.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
```

Detailed documents may refine syntax and procedures.

They must not contradict this decision.

---

## 30. Decision enforcement

Recommended checks:

```text
gf-wordbench scenarios lint
gf-wordbench contracts check
gf-wordbench project contracts check
```

Enforcement should reject or report:

- unregistered `.gfs`;
- registered missing scenario;
- duplicate scenario ID;
- missing required gold;
- unsafe shell command;
- invalid marker protocol;
- scenario without finite timeout;
- scenario result without raw evidence;
- report-time scenario execution;
- normal gold mutation;
- language-specific scenario embedded in reusable framework code;
- scenario runner implementing GF commands itself.

---

## 31. Reconsideration triggers

This decision should be reconsidered only when one or more of the following becomes true:

- GF removes or fundamentally changes scriptable shell execution;
- required project validation cannot be expressed reliably through supported GF commands;
- a stable official GF machine protocol supersedes shell output;
- security requirements prohibit executing project-owned `.gfs` even in controlled environments;
- scenario portability becomes impossible across supported GF versions;
- an official PGF or GF testing protocol provides materially stronger evidence with lower duplication.

Convenience alone is not sufficient to replace the native `.gfs` decision.

---

## 32. Supersession policy

A future ADR superseding this decision must explain:

- why GF shell authority is no longer sufficient;
- how manual reproducibility is preserved;
- how existing `.gfs` scenarios migrate;
- how raw evidence remains available;
- how gold compatibility is handled;
- how GF semantics avoid duplication;
- how security improves;
- how required and optional scenario behavior remains stable;
- how release evidence remains comparable.

Until such an ADR is accepted, native `.gfs` remains the canonical executable scenario format.

---

## 33. Final rationale

GF already provides the commands required to exercise a grammar.

Reimplementing those commands in a GF Wordbench-specific language would create duplicate semantics, additional compatibility work, and a weaker connection to the authoritative tool.

Native `.gfs` scenarios preserve the correct division of responsibility:

```text
active project
    declares what behavior must be exercised

GF shell
    executes the grammar behavior

GF Wordbench
    controls execution and determines whether the declared contract passed
```

The accepted architecture is therefore:

```text
registered project .gfs
→ fresh GF process
→ raw stdout/stderr
→ marker validation
→ diagnostic interpretation
→ normalization
→ assertions
→ gold comparison
→ ScenarioResult
→ checkpoint and release gates
```

This approach provides the strongest balance of authenticity, portability, evidence quality, maintainability, and anti-drift protection.
