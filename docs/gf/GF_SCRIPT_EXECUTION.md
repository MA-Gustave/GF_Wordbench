# GF Wordbench — GF Script Execution

**Document ID:** `GF-WB-GF-SCRIPT-EXECUTION`  
**Status:** Normative integration specification  
**Applies to:** Native GF shell scenarios executed by GF Wordbench  
**Primary asset type:** `.gfs`  
**Primary runner:** `app/audit/scenario_runner.py`  
**Owner:** GF Wordbench maintainers  
**Contract family:** `EXT-GF-005` through `EXT-GF-010`  
**Last structural review:** 2026-07-22  

---

## 1. Purpose

This document defines how GF Wordbench executes native Grammatical Framework shell scripts.

GF Wordbench uses `.gfs` scenarios to validate behavior that cannot be proved by compiling individual `.gf` files alone, including:

- loading a complete grammar;
- checking missing linearizations;
- parsing representative text;
- linearizing representative trees;
- bounded tree generation;
- morphology checks;
- grammar introspection;
- project-specific regression expectations.

The design principle is:

> GF executes GF commands. GF Wordbench orchestrates the process, preserves evidence, verifies completion, normalizes output, applies project assertions, and reports the result.

GF Wordbench must not implement a competing GF shell, parser, type checker, generator, linearizer, or PGF runtime.

---

## 2. Scope

This specification governs:

- discovery and registration of `.gfs` scenarios;
- scenario identifiers;
- scenario file locations;
- process invocation;
- standard input;
- working directory;
- GF search path;
- encoding;
- raw stdout and stderr;
- finite timeouts;
- process termination;
- stable markers;
- output normalization;
- gold comparison;
- scenario assertions;
- scenario artifacts;
- required and optional scenarios;
- failure semantics;
- strict-mode restrictions;
- security rules;
- deterministic execution;
- scenario-result construction;
- tests.

It also defines approved usage patterns for these GF shell operations:

```text
import / i
parse / p
linearize / l
generate_random / gr
generate_trees / gt
print_grammar / pg
morpho_analyse / ma
abstract_info / ai
show_dependencies / sd
dependency_graph / dg
show_operations / so
show_source / ss
compute_concrete / cc
put_string / ps
put_tree / pt
read_file / rf
write_file / wf
quit / q
```

---

## 3. Non-goals

This document does not define:

- GF source-language syntax;
- the implementation of the GF shell;
- Python PGF bindings;
- the PGF release-build command;
- static source scanning;
- per-file batch compilation;
- language-specific expected trees or strings;
- field-level `ScenarioResult` serialization;
- report prose;
- project-specific coverage targets.

Those responsibilities belong to other documents.

---

## 4. Verified GF execution facts

GF Wordbench relies on these upstream GF behaviors:

1. The GF shell accepts a sequence of GF commands.
2. Commands can be connected with pipes.
3. Multiple command pipes may be separated with semicolons.
4. A `.gfs` script can be supplied through standard input.
5. The standard shell invocation documented by GF is logically equivalent to:

   ```text
   gf < script.gfs
   ```

6. A script contains GF commands, conventionally one per line.
7. GF may skip an unrecognized command line without terminating the interpreter.
8. `q` / `quit` exits the interpreter.
9. `eh` / `execute_history` reads commands from another file.
10. `ps` / `put_string` emits a string.
11. `wf` / `write_file` writes a previous command value to a file.
12. `!`, `?`, and `sp` can invoke or pipe to operating-system commands.
13. `import` loads `.gf`, `.gfo`, or `.pgf` grammar material according to the file suffix.
14. `parse`, `linearize`, generation, and introspection are GF shell operations.
15. GF's own test-suite model uses `.gfs` scripts, `.out` output, and optional `.gold` expectations.

GF Wordbench adds stricter completion, security, evidence, and determinism rules on top of these upstream behaviors.

---

## 5. Core contract

A scenario execution is one external-process request with:

```text
explicit GF executable
ordered process arguments
explicit working directory
explicit environment overrides
UTF-8 scenario content on stdin
finite timeout
separate stdout capture
separate stderr capture
output-size limits
structured process result
```

Canonical logical invocation:

```text
executable = <resolved-gf>
args = <verified-shell-options>
cwd = <resolved-project-root-or-declared-scenario-root>
stdin = UTF-8 contents of scenario.gfs
shell = false
```

The operating-system redirection syntax:

```text
gf < scenario.gfs
```

describes GF behavior but is not the preferred Python implementation.

GF Wordbench should pass the scenario content directly to the child process through `stdin`.

---

## 6. Architecture

```text
project.toml / project validation contract
                    |
                    v
          scenario registry
                    |
                    v
         scenario selection by mode
                    |
                    v
      app/audit/scenario_runner.py
                    |
                    +--> validate paths and policy
                    |
                    +--> read .gfs as UTF-8
                    |
                    +--> hash exact scenario bytes
                    |
                    +--> build process request
                    |
                    v
       app/utils/process_utils.py
                    |
                    v
             gf / gf.exe
                    |
          +---------+----------+
          |                    |
          v                    v
       stdout               stderr
          |                    |
          +---------+----------+
                    |
                    v
             raw evidence
                    |
                    v
          marker verification
                    |
                    v
          output normalization
                    |
                    v
            gold comparison
                    |
                    v
            ScenarioResult
                    |
                    v
               RunResult
```

---

# 7. Scenario asset model

## 7.1 Canonical directories

```text
project/
└── validation/
    ├── README.md
    ├── scenarios/
    │   ├── README.md
    │   └── <scenario-id>.gfs
    ├── gold/
    │   ├── README.md
    │   └── <scenario-id>.gold
    └── inputs/
        ├── README.md
        └── ...
```

## 7.2 Canonical script path

```text
project/validation/scenarios/<scenario-id>.gfs
```

## 7.3 Canonical gold path

```text
project/validation/gold/<scenario-id>.gold
```

A scenario without exact golden output may omit the gold file.

## 7.4 Input paths

Scenario-owned input fixtures belong under:

```text
project/validation/inputs/
```

They must be declared by the active project validation contract.

A scenario must not read arbitrary files from the developer machine.

## 7.5 Project ownership

The active language project owns:

- `.gfs` content;
- scenario IDs;
- required/optional classification;
- linguistic expectations;
- input fixtures;
- gold files;
- expected entrypoints;
- scenario-specific release relevance.

The framework owns:

- execution;
- process limits;
- raw capture;
- marker checking;
- normalization;
- gold comparison;
- result construction;
- reporting.

---

# 8. Scenario identifiers

## 8.1 Format

Canonical scenario IDs use:

```text
lowercase-kebab-case
```

Recommended regular expression:

```text
^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$
```

Examples:

```text
load
missing
linearize-basic
parse-negation
generation-smoke
morphology-nouns
```

## 8.2 Identity

The scenario ID is the stable identity across:

- project configuration;
- `.gfs` filename;
- `.gold` filename;
- `ScenarioResult`;
- raw logs;
- normalized output;
- regression comparison;
- report sections.

Renaming a scenario creates a new identity unless a documented migration maps the old ID.

## 8.3 Uniqueness

Scenario IDs must be unique within the active project.

Required and optional scenario lists must not contain the same ID.

## 8.4 Path derivation

Canonical path derivation:

```text
script = project/validation/scenarios/<scenario-id>.gfs
gold   = project/validation/gold/<scenario-id>.gold
```

A richer explicit path mapping may be supported only through a documented project-schema field.

---

# 9. Scenario registration

## 9.1 Authoritative registration

The active project configuration is authoritative for machine-readable scenario registration.

The project validation specification documents:

- purpose;
- mode membership;
- required or optional status;
- expected entrypoint;
- expected sections;
- gold policy;
- coverage rationale.

## 9.2 Required scenario

A required scenario:

- must exist;
- must be readable;
- must satisfy security policy;
- must complete;
- must satisfy marker requirements;
- must satisfy artifact requirements;
- must pass gold comparison when gold is required;
- affects overall run status.

## 9.3 Optional scenario

An optional scenario:

- runs only when selected by mode or explicit option;
- produces full evidence;
- must not be silently treated as required;
- may fail without failing the run only when project policy explicitly permits it;
- remains visible in reports.

## 9.4 Missing registration

An unregistered `.gfs` file is not executed automatically.

This prevents accidental execution of:

- scratch scripts;
- developer experiments;
- copied scripts;
- archived scenarios;
- unreviewed external content.

## 9.5 Missing required script

A registered required scenario with no script produces:

```text
validation_status = ERROR
execution_state = not_started
error_kind = CONFIG
```

It is not silently skipped.

---

# 10. Scenario selection by validation mode

## 10.1 Quick mode

Quick mode normally runs:

- no scenario; or
- a minimal explicitly configured smoke scenario.

Quick mode must not run release-only scenarios implicitly.

## 10.2 Checkpoint mode

Checkpoint mode runs:

- required checkpoint scenarios;
- explicitly selected optional checkpoint scenarios.

Typical checkpoint scenarios:

```text
load
linearize-basic
morphology-smoke
```

## 10.3 Release mode

Release mode runs every required release scenario.

It may also run optional release diagnostics, but optional diagnostics must not conceal required failures.

Typical release scenarios:

```text
load
missing
linearize
parse
generation-bounded
morphology
```

## 10.4 Diagnostic mode

Diagnostic mode may run:

- all required diagnostic scenarios;
- selected optional scenarios;
- introspection scenarios;
- bounded generation;
- focused reproduction scenarios.

Diagnostic mode should maximize useful evidence without weakening safety limits.

## 10.5 Deterministic order

Scenario order comes from project configuration.

Filesystem enumeration order must not determine execution order.

---

# 11. Script encoding and text rules

## 11.1 Encoding

Canonical `.gfs` encoding:

```text
UTF-8 without BOM
```

Readers may accept a UTF-8 BOM for compatibility, but the executed content hash must reflect the exact source bytes or the documented canonicalization policy.

## 11.2 Newlines

Canonical repository form:

```text
LF
```

The runner may accept CRLF.

The framework must not alter linguistically meaningful string content while normalizing script line endings.

## 11.3 Final newline

A `.gfs` file should end with one newline.

## 11.4 Empty file

An empty registered scenario is invalid.

## 11.5 Binary or undecodable content

Undecodable scenario content produces:

```text
validation_status = ERROR
error_kind = CONFIG
execution_state = not_started
```

GF must not be launched.

---

# 12. GF command-line invocation

## 12.1 Canonical request

```text
executable:
  resolved absolute path to gf or gf.exe

arguments:
  verified shell-mode options only

working directory:
  resolved active project root by default

stdin:
  exact UTF-8 scenario text

stdout:
  raw/scenarios/<scenario-id>.stdout.txt

stderr:
  raw/scenarios/<scenario-id>.stderr.txt

timeout:
  configured scenario timeout

shell:
  false
```

## 12.2 Script path is not a shell-redirection argument

The implementation must not create an argument containing:

```text
< scenario.gfs
```

Redirection characters belong to a command shell, not to GF.

The process runner receives scenario content through direct stdin.

## 12.3 `--run` compatibility

Some GF documentation describes a `--run` option that suppresses prompts and other interactive noise.

GF Wordbench may use `--run` only when:

- the selected GF version is known to support it;
- capability or version policy confirms the behavior;
- the resolved arguments are recorded;
- output normalization remains versioned;
- tests cover the selected GF versions.

The portable baseline remains:

```text
gf with scenario content on stdin
```

The framework must not assume `--run` support without verification.

## 12.4 Initial grammar arguments

GF Wordbench should prefer explicit `import` commands inside the scenario.

Supplying grammar files as process arguments may be supported only when the scenario contract explicitly chooses that mode.

One scenario must not accidentally load both through arguments and through conflicting imports.

## 12.5 Working directory

Default:

```text
active project root
```

A different working directory is permitted only when:

- declared by project configuration;
- resolved inside an approved root;
- recorded in `ScenarioResult`;
- covered by path tests.

## 12.6 GF path

The scenario process uses the same resolved GF search-path policy as compilation and PGF build.

Compilation and scenario execution must not construct incompatible GF paths from equivalent configuration.

---

# 13. Process environment

## 13.1 Explicit overrides

Environment overrides may include:

- GF library-path variables when required;
- locale controls;
- temporary-directory controls;
- compatibility variables documented for a GF version.

## 13.2 Precedence

Explicit resolved configuration takes precedence over inherited environment values for correctness-critical behavior.

## 13.3 Isolation

Overrides apply only to the child process.

The runner must not mutate the parent environment globally.

## 13.4 Recording

Record relevant non-secret overrides.

Do not record:

- full environment dumps;
- passwords;
- tokens;
- private keys;
- unrelated personal variables.

## 13.5 Locale

Locale must not make stdout/stderr decoding nondeterministic.

UTF-8 is the framework default.

---

# 14. Scenario process lifecycle

## 14.1 Lifecycle

```text
validate registration
    |
validate script and paths
    |
read exact bytes
    |
decode UTF-8
    |
security scan
    |
compute scenario hash
    |
build process request
    |
launch GF
    |
stream or collect bounded output
    |
timeout / cancellation monitoring
    |
terminate if required
    |
close streams
    |
persist raw stdout and stderr
    |
interpret process state
    |
verify markers
    |
normalize
    |
compare gold
    |
verify artifacts
    |
construct ScenarioResult
```

## 14.2 Start evidence

Before launch, record:

- scenario ID;
- script path;
- scenario hash;
- required flag;
- executable;
- ordered arguments;
- working directory;
- effective GF path;
- timeout;
- expected gold;
- expected artifact policy.

## 14.3 End evidence

After execution, record:

- exit code;
- timeout state;
- cancellation state;
- launch error;
- duration;
- stdout path;
- stderr path;
- byte counts;
- truncation state;
- marker result;
- normalization result;
- gold result;
- produced artifacts;
- validation status.

---

# 15. Timeout and termination

## 15.1 Finite timeout

Every scenario must have a finite timeout.

A missing or non-positive timeout is invalid configuration.

## 15.2 Timeout classes

Scenario timeouts may differ by scenario class:

```text
load
parse
linearize
generation
introspection
release
```

The configured effective timeout must be recorded.

## 15.3 Timeout behavior

On timeout:

1. mark `timed_out = true`;
2. attempt controlled process termination;
3. terminate owned child processes according to platform policy;
4. retain partial stdout;
5. retain partial stderr;
6. record duration;
7. prevent further writes into a finalized run;
8. construct a structured timeout result.

## 15.4 Timeout status

Canonical mapping:

```text
validation_status = ERROR
execution_state = timed_out
error_kind = TIMEOUT
diagnostic_class = ambiguous
```

A project may classify a reproducible resource-limit failure differently at a higher diagnostic layer, but raw timeout identity remains preserved.

## 15.5 Cancellation

On user cancellation:

```text
validation_status = ERROR
execution_state = cancelled
error_kind = TOOL or dedicated cancellation kind when standardized
```

Cancellation must not be reported as a GF parse, type, or syntax failure.

---

# 16. Output capture

## 16.1 Raw stdout

Canonical path:

```text
raw/scenarios/<scenario-id>.stdout.txt
```

## 16.2 Raw stderr

Canonical path:

```text
raw/scenarios/<scenario-id>.stderr.txt
```

## 16.3 Separate streams

Stdout and stderr must be captured separately.

A merged human view may be generated later, but it does not replace raw streams.

## 16.4 Output on failure

Non-zero exit, timeout, marker failure, or gold mismatch must not cause captured output to be discarded.

## 16.5 Output-size limit

Every scenario execution should have a configurable output-size limit.

When a limit is reached:

- stop or truncate according to policy;
- record truncation;
- retain bounded evidence;
- do not allow a truncated exact-gold comparison to pass;
- classify required evidence loss as an error.

## 16.6 Decoding

Use explicit UTF-8 decoding.

A documented replacement strategy may preserve undecodable bytes for diagnostics, but decoding loss must be recorded.

Raw byte preservation may be added when required by compatibility testing.

---

# 17. Script structure

## 17.1 Recommended order

A scenario should follow this order:

```text
1. begin scenario marker
2. import grammar
3. verify load section
4. execute one or more focused validation sections
5. emit end markers
6. quit
```

## 17.2 One logical operation per line

GF supports pipes and semicolon-separated command sequences.

GF Wordbench project scenarios should prefer one logical command or pipe per line.

This improves:

- review;
- marker localization;
- diffs;
- failure diagnosis;
- compatibility analysis.

## 17.3 Pipes

GF pipes are allowed.

Example:

```text
p -lang=LangEng "this cheese is Italian" | l -lang=LangIta
```

Pipes must remain purely within GF unless a separately authorized external command is involved.

## 17.4 Semicolons

Semicolon-separated command lines are permitted by GF but should be avoided in normative scenarios.

They can make partial completion ambiguous.

Use separate lines unless atomic grouping is necessary and documented.

## 17.5 Explicit termination

A scenario should end with:

```text
q
```

This ensures that the interpreter exits after the declared scenario.

If the selected verified execution mode exits automatically at end-of-input, `q` remains recommended for clarity and compatibility.

---

# 18. Stable markers

## 18.1 Why markers are required

GF may skip an unrecognized command line without terminating.

Therefore, a bare line such as:

```text
GF_WORDBENCH_BEGIN load
```

must not be used as a marker command.

It may be ignored by GF.

Markers must be emitted through a recognized GF command.

## 18.2 Canonical marker emission

Use `ps` / `put_string`:

```text
ps "GF_WORDBENCH_BEGIN <section-id>"
ps "GF_WORDBENCH_END <section-id>"
```

Example:

```text
ps "GF_WORDBENCH_BEGIN load"
i GrammarExample.gf
ps "GF_WORDBENCH_END load"
q
```

## 18.3 Marker text

Canonical marker grammar:

```text
GF_WORDBENCH_BEGIN <section-id>
GF_WORDBENCH_END <section-id>
```

Recommended section-ID pattern:

```text
^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$
```

## 18.4 Marker uniqueness

Within one scenario:

- each required section ID appears once as begin;
- each required section ID appears once as end;
- begin precedes end;
- nesting is either prohibited or explicitly defined by the scenario-format specification;
- duplicate marker pairs are invalid.

Default policy:

```text
markers do not nest
```

## 18.5 Scenario-level markers

Every normative scenario should contain:

```text
GF_WORDBENCH_BEGIN scenario
GF_WORDBENCH_END scenario
```

or a scenario-ID-specific outer section.

Recommended:

```text
ps "GF_WORDBENCH_BEGIN scenario-<scenario-id>"
...
ps "GF_WORDBENCH_END scenario-<scenario-id>"
```

## 18.6 Completion rule

A scenario does not complete merely because the process exits.

All required end markers must be present in normalized marker extraction.

## 18.7 Marker collision

Linguistic output that happens to contain marker text could create a false marker.

To reduce collision risk:

- marker lines must match the complete normalized line;
- section IDs must be declared;
- only expected markers count;
- unexpected marker lines produce a warning or strict failure;
- project test data should not intentionally reproduce reserved marker lines.

---

# 19. Assertions

## 19.1 Assertion ownership

GF executes commands.

GF Wordbench evaluates scenario assertions from captured evidence.

GF Wordbench does not inject a new assertion language into GF command syntax.

## 19.2 Assertion sources

Assertions may come from:

- marker completion;
- process success;
- fatal diagnostic absence;
- expected artifact existence;
- exact gold comparison;
- structured scenario policy;
- bounded count checks supported by the runner;
- project validation specification.

## 19.3 Required base assertions

Every required scenario checks:

```text
process launched
process did not time out
process was not cancelled
required markers completed
raw evidence exists
no prohibited command policy was violated
required artifacts exist
gold comparison passed when required
```

## 19.4 Linguistic assertions

Linguistic expectations belong to the active project.

Examples:

- expected parse tree appears;
- exactly one parse exists;
- no parse exists for a negative test;
- expected linearization appears;
- output is non-empty;
- all generated trees linearize;
- missing-linearization list is empty;
- required morphological form appears.

## 19.5 Exact versus semantic assertions

Exact gold is appropriate when output is expected to be stable.

Semantic or bounded assertions are preferable when:

- output order can vary;
- random generation is used;
- multiple variants are valid;
- GF version changes formatting without changing meaning;
- exhaustive output is intentionally limited.

A semantic assertion must still be deterministic and testable.

---

# 20. Grammar import

## 20.1 Canonical command

```text
import <module-or-grammar>
```

Short form:

```text
i <module-or-grammar>
```

Project scenarios should prefer one spelling consistently.

Recommended normative spelling:

```text
i
```

or long form if readability policy prefers it.

## 20.2 Supported targets

GF determines target behavior from suffix, including:

```text
.gf
.gfo
.pgf
```

The project validation specification defines the intended target.

## 20.3 Source versus PGF scenarios

A source-load scenario validates source compilation and shell loading.

A PGF-load scenario validates the produced runtime grammar.

They are distinct proofs and should use distinct scenario IDs when both matter.

## 20.4 `-retain`

Use:

```text
i -retain <target>
```

only when later commands require retained source operations.

Examples of operations that may require retained source include source-level introspection.

`-retain` must not be enabled globally without need.

## 20.5 Load success

Import success requires more than a zero process exit.

The scenario must complete a marker after the import command:

```text
ps "GF_WORDBENCH_BEGIN load"
i GrammarExample.gf
ps "GF_WORDBENCH_END load"
```

Fatal diagnostics between markers cause failure even if the interpreter later exits normally.

## 20.6 Multiple imports

Multiple compatible concrete grammars may be loaded in one scenario.

Order must be deterministic.

A later import that replaces part of shell state must be intentional and documented.

---

# 21. Parse validation

## 21.1 Commands

Long form:

```text
parse
```

Short form:

```text
p
```

## 21.2 Typical options

```text
-lang=<language>
-cat=<category>
```

Additional options may be used only when supported by the selected GF version and documented by the project scenario.

## 21.3 Example

```text
ps "GF_WORDBENCH_BEGIN parse-basic"
p -lang=LangEng -cat=S "this cheese is Italian"
ps "GF_WORDBENCH_END parse-basic"
```

## 21.4 Parse expectations

A parse section must declare one of:

```text
at least one parse
exactly one parse
expected tree present
approved tree set
no parse expected
parse count within bound
```

Absence of a fatal error is not enough to prove parse success.

## 21.5 Input quoting

Project text is scenario data.

It must be quoted according to GF shell syntax.

The runner must not interpolate arbitrary unescaped user input into `.gfs` command text during normal execution.

Generated dynamic scenarios require a dedicated safe builder and tests.

## 21.6 Ambiguity

Expected ambiguity must be declared.

An ambiguous parse is not automatically a failure.

Unexpected ambiguity may fail according to project policy.

## 21.7 Negative parse tests

A negative parse test must distinguish:

- no parse;
- import failure;
- parse command failure;
- timeout;
- marker failure.

Only the first is a successful negative linguistic result.

---

# 22. Linearization validation

## 22.1 Commands

Long form:

```text
linearize
```

Short form:

```text
l
```

## 22.2 Typical options

```text
-lang=<language>
-all
-list
-table
-treebank
-tabtreebank
```

Use only the options required by the scenario.

## 22.3 Example

```text
ps "GF_WORDBENCH_BEGIN linearize-basic"
l -lang=LangEng (PredVP (UsePN john_PN) (UseV sleep_V))
ps "GF_WORDBENCH_END linearize-basic"
```

The tree is illustrative only.

Active-project scenarios define valid project trees.

## 22.4 Variants

When a tree has multiple valid surface variants, the scenario must define how variants are handled:

- exact ordered list;
- unordered approved set;
- one-of expectation;
- non-empty expectation;
- gold output with stable order.

The framework must not silently sort meaningful variants unless the normalization contract explicitly permits it.

## 22.5 Empty output

An empty string is different from missing output.

The assertion layer must preserve that distinction.

## 22.6 Orthography

Normalization must not erase:

- accents;
- apostrophes;
- punctuation;
- capitalization;
- token-binding effects;
- language-specific whitespace with semantic relevance.

---

# 23. Parse-linearize pipelines

## 23.1 GF-native pipeline

Example:

```text
p -lang=LangEng "this cheese is Italian" | l -lang=LangIta
```

This is a GF shell pipe.

GF Wordbench captures the resulting output.

## 23.2 Validation use

A parse-linearize pipeline may validate:

- translation behavior;
- parse coverage;
- target-language realization;
- tree compatibility.

## 23.3 Limitations

A successful final linearization does not expose every intermediate parse unless tracing or separate commands are used.

When intermediate evidence matters, use separate marked sections or documented trace options.

## 23.4 Cross-language expectations

Source and target language names must match the loaded grammar.

They belong to the active project contract, not framework constants.

---

# 24. Missing-linearization checks

## 24.1 GF command

A common shell operation is:

```text
pg -missing
```

Optionally restricted by language according to supported GF behavior:

```text
pg -missing -lang=<language>
```

## 24.2 Purpose

The command exposes abstract functions without linearizations in the selected concrete grammar.

## 24.3 Example

```text
ps "GF_WORDBENCH_BEGIN missing"
i GrammarExample.gf
pg -missing
ps "GF_WORDBENCH_END missing"
q
```

## 24.4 Success policy

Typical release expectation:

```text
no missing required functions
```

The active project may permit explicitly documented placeholders.

## 24.5 Output interpretation

The framework must not treat any non-empty output as failure without accounting for:

- prompts;
- markers;
- version banners;
- selected languages;
- documented approved omissions.

Prefer normalized gold or a structured project assertion.

---

# 25. Bounded generation

## 25.1 Commands

Random generation:

```text
generate_random
gr
```

Exhaustive or bounded tree generation:

```text
generate_trees
gt
```

## 25.2 Required bounds

Automated generation scenarios must define finite bounds.

Supported GF options include:

```text
-cat=<category>
-number=<integer>
-depth=<integer>
-lang=<language-list>
```

At least one effective count or depth bound is required.

## 25.3 Example

```text
ps "GF_WORDBENCH_BEGIN generation-smoke"
gr -cat=S -number=20 -depth=5 | l -lang=LangEng
ps "GF_WORDBENCH_END generation-smoke"
q
```

## 25.4 Resource controls

In addition to GF options, Wordbench enforces:

- process timeout;
- stdout limit;
- stderr limit;
- total artifact limit;
- optional line or result-count limits.

## 25.5 Random output

Random generation must not be used as exact gold unless reproducibility is proven for the supported GF version and configuration.

When no stable seed contract exists, use random generation for assertions such as:

- command completes;
- no runtime failure;
- output count is bounded;
- no output is empty;
- all trees linearize;
- forbidden diagnostics do not occur.

## 25.6 Exhaustive generation

`gt` can expand rapidly.

Use conservative values for:

```text
-depth
-number
```

Unbounded exhaustive generation is prohibited in automated validation.

---

# 26. Morphology validation

## 26.1 Morphological analysis

GF shell command:

```text
morpho_analyse
ma
```

Typical use:

```text
ma -lang=<language> "word"
```

## 26.2 Known and missing word checks

Supported options may include:

```text
-known
-missing
```

## 26.3 Scenario purpose

Morphology scenarios may validate:

- expected analyses;
- unknown-word behavior;
- form coverage;
- lexicon integration;
- orthographic normalization;
- language-specific paradigm behavior.

## 26.4 Project ownership

Expected morphological analyses are language-specific.

They belong in:

```text
project/docs/MORPHOLOGY_SPEC.md
project/docs/VALIDATION_SPEC.md
project/validation/gold/
```

## 26.5 Stability

Morphological output may be sensitive to:

- grammar version;
- lexicon changes;
- ordering;
- retained source state;
- language selection.

Exact gold changes require review.

---

# 27. Introspection

## 27.1 Supported diagnostic commands

Possible introspection commands:

```text
ai
pg
sd
dg
so
ss
cc
```

## 27.2 Retained source

Commands requiring source operations must use:

```text
i -retain <source-target>
```

The scenario must not assume retained source when only a `.pgf` is loaded.

## 27.3 Diagnostic status

Introspection is diagnostic unless a project explicitly makes it a release gate.

An introspection failure must not be mislabeled as a normal file compilation failure.

## 27.4 External artifacts

Commands such as dependency-graph generation may create files.

Every produced file must:

- be expected;
- remain inside an approved output root;
- be registered as an artifact;
- be covered by an external-tool contract when another program renders it.

## 27.5 Graph rendering

Invoking Graphviz or another renderer is not part of the GF shell contract by default.

It requires a separate optional external-tool contract.

---

# 28. File-reading commands

## 28.1 `rf` / `read_file`

`rf` may read scenario input from a file.

Example logical use:

```text
rf -file="project/validation/inputs/example.txt" | p -lang=LangEng
```

Exact path syntax must remain compatible with GF and the selected working directory.

## 28.2 Policy

`rf` is allowed only for:

- declared project input fixtures;
- declared run-owned intermediate files;
- paths contained in approved roots.

## 28.3 Prohibited reads

Scenarios must not read:

- user-profile secrets;
- arbitrary absolute paths;
- environment files;
- credentials;
- unrelated repositories;
- files reached through traversal.

## 28.4 `-lines`

When line-list behavior is used, expected ordering and blank-line semantics must be documented.

---

# 29. File-writing commands

## 29.1 `wf` / `write_file`

GF can write command output to a file.

This creates a filesystem side effect.

## 29.2 Default policy

`wf` is prohibited in ordinary scenarios unless explicitly authorized.

GF Wordbench already captures stdout and should prefer captured output over script-directed writes.

## 29.3 Authorized use

An authorized `wf` command must:

- write inside a run-owned artifact directory;
- use a declared deterministic filename;
- avoid project source and gold directories;
- follow overwrite policy;
- be registered in expected artifacts;
- be verified after execution;
- be included in the manifest.

## 29.4 Append mode

`wf -append` is prohibited in deterministic validation unless the artifact contract explicitly requires and tests append behavior.

## 29.5 Pre-existing file

A scenario must not overwrite a pre-existing file without an explicit safe policy.

---

# 30. Nested script execution

## 30.1 `eh` / `execute_history`

GF supports:

```text
eh FILE
```

which reads and executes commands from another file.

## 30.2 Default policy

Nested script execution is prohibited in normative project scenarios by default.

Reasons:

- hidden dependencies;
- incomplete scenario hashing;
- unclear review boundaries;
- path traversal risk;
- difficult marker ownership;
- nondeterministic working-directory behavior.

## 30.3 Authorized nested script

When explicitly supported, every nested script must:

- be declared;
- live under the scenario directory;
- be UTF-8 readable;
- pass the same security checks;
- be included in the scenario content hash set;
- have deterministic order;
- be visible in `ScenarioResult`;
- remain inside the project root.

Recursive cycles are prohibited.

---

# 31. System-command prohibition

## 31.1 GF system escape

GF shell commands capable of operating-system execution include:

```text
!
?
sp
```

## 31.2 Normal policy

These commands are prohibited in normal GF Wordbench scenarios.

Examples of prohibited behavior:

```text
! del ...
! rm ...
? grep ...
sp -command="..."
```

Even read-only operating-system commands create:

- platform dependency;
- shell-injection risk;
- hidden executable dependencies;
- nondeterministic output;
- environment leakage.

## 31.3 Detection

The scenario policy checker should detect system-command syntax before launching GF.

Detection must be aware of:

- leading whitespace;
- command abbreviations;
- command pipes;
- semicolon-separated commands;
- quoted strings;
- expected GF syntax.

Static detection is a safety gate, not a full GF parser.

## 31.4 Explicit exception

An exception requires:

- project-level authorization;
- separate external-tool contract;
- exact command allowlist;
- no untrusted interpolation;
- explicit shell;
- platform policy;
- timeout;
- output limits;
- security tests;
- visible report disclosure.

Strict mode rejects all such exceptions.

---

# 32. Interactive commands

## 32.1 Prohibition

Scenarios must not require interactive user input.

Interactive quizzes and similar commands are prohibited in automated validation unless a non-interactive bounded behavior is explicitly proven.

## 32.2 Examples

Commands such as morphology or translation quizzes are not normal validation primitives.

## 32.3 Prompt handling

Known GF prompts may be normalized when documented.

An unexpected prompt indicating that GF is waiting for input causes timeout or contract failure.

---

# 33. Dynamic scenario generation

## 33.1 Default policy

Canonical project scenarios are version-controlled `.gfs` files.

The runner should not rewrite them.

## 33.2 Generated scenarios

A future dynamic scenario builder may be used only for controlled framework-generated commands.

It must:

- use a typed command model;
- escape GF strings correctly;
- prohibit system commands;
- produce reviewable script text;
- record generated content;
- hash executed content;
- preserve it as a run artifact;
- have extensive injection tests.

## 33.3 User text

Arbitrary user text must not be concatenated into a GF command.

For project fixtures, prefer reviewed `.gfs` or declared input files.

---

# 34. Raw evidence and normalization

## 34.1 Raw-first rule

The runner writes raw stdout and stderr before normalization.

## 34.2 Normalized output path

Canonical path:

```text
raw/scenarios/<scenario-id>.out
```

or the exact path owned by `RunPaths` and the persisted schema.

## 34.3 Allowed normalization

Versioned normalization may handle:

- CRLF to LF;
- ANSI control sequences;
- known GF prompts;
- known startup banners;
- run-root prefixes;
- project-root prefixes through stable tokens;
- temporary-directory prefixes;
- measured durations;
- documented timestamps;
- platform path separators;
- trailing spaces;
- final newline.

## 34.4 Forbidden normalization

Normalization must not remove:

- GF errors;
- parse trees;
- linearizations;
- morphology analyses;
- missing-linearization names;
- marker lines;
- meaningful blank lines when asserted;
- meaningful Unicode;
- expected variants;
- command output needed for project assertions.

## 34.5 Normalization version

The normalization version must be recorded.

A change that can alter gold comparison requires:

- version update;
- review of affected gold;
- migration notes;
- tests.

## 34.6 Marker extraction

Marker extraction uses normalized line boundaries but must be traceable to raw output.

## 34.7 Prompt suppression

Using a verified GF option to reduce prompts may simplify output.

It does not remove the need for normalization and raw capture.

---

# 35. Gold comparison

## 35.1 Comparison input

Compare:

```text
normalized scenario output
```

against:

```text
reviewed .gold content
```

Never compare a merged or human-formatted log.

## 35.2 Exact comparison

Canonical exact comparison occurs after:

- UTF-8 decoding;
- CRLF normalization;
- documented output normalization;
- final-newline normalization.

## 35.3 Missing gold

When gold is required:

```text
missing gold = failure
```

The runner must not create it automatically.

## 35.4 Mismatch

A mismatch produces:

- `gold_match = false`;
- a scenario failure;
- a reviewable diff artifact or report section;
- retained actual output;
- retained expected path.

## 35.5 Read-only normal run

Normal validation must not modify `.gold`.

## 35.6 Explicit update

Gold update is a separate command and workflow.

It must:

1. execute the scenario;
2. preserve raw output;
3. normalize;
4. show or store the diff;
5. require explicit authorization;
6. write atomically;
7. leave a reviewable source-control change.

---

# 36. Artifact validation

## 36.1 Declared artifacts

A scenario may declare expected artifacts such as:

- generated graph source;
- exported grammar view;
- controlled data file;
- scenario-specific output.

## 36.2 Required artifact

A required artifact must:

- exist;
- be inside an approved root;
- have expected type or suffix;
- satisfy minimum size where applicable;
- be registered;
- be included in the manifest.

## 36.3 Missing artifact

A missing required artifact causes:

```text
error_kind = TOOL or contract-specific artifact failure
validation_status = FAIL or ERROR according to whether execution was valid
```

## 36.4 Unexpected artifacts

Unexpected writes produce a warning or strict failure.

Source-tree mutation is always an error.

## 36.5 Hashing

Important artifacts should receive SHA-256 hashes in the run manifest.

---

# 37. Success semantics

A scenario is `OK` only when every applicable condition passes:

```text
registration valid
script valid
security policy valid
process launched
no timeout
not cancelled
acceptable exit code
no fatal diagnostic
required markers complete
normalization successful
assertions successful
required gold matched
required artifacts valid
```

A zero exit code alone is insufficient.

---

# 38. Failure taxonomy

## 38.1 Validation status

```text
OK
FAIL
ERROR
SKIPPED
```

## 38.2 Execution state

```text
completed
timed_out
cancelled
launch_failed
not_started
```

## 38.3 Diagnostic class

```text
ok
direct
downstream
ambiguous
noise
skipped
```

Scenario failures are normally direct to the scenario unless a documented upstream grammar failure explains them.

## 38.4 Error kinds

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

## 38.5 Typical mapping

| Condition | Status | Execution state | Error kind |
|---|---|---|---|
| All checks pass | `OK` | `completed` | `OK` |
| Gold mismatch | `FAIL` | `completed` | `OTHER` |
| Expected parse absent | `FAIL` | `completed` | `OTHER` |
| Required marker absent | `FAIL` or `ERROR` | `completed` | `SCRIPT` |
| GF reports scenario command failure | `FAIL` | `completed` | GF-derived kind |
| GF executable missing | `ERROR` | `launch_failed` | `TOOL` |
| Timeout | `ERROR` | `timed_out` | `TIMEOUT` |
| Invalid UTF-8 scenario | `ERROR` | `not_started` | `CONFIG` |
| Prohibited system command | `ERROR` | `not_started` | `CONFIG` |
| Optional scenario not selected | `SKIPPED` | `not_started` | `OK` |
| Required artifact absent | `FAIL` or `ERROR` | `completed` | `TOOL` |

The detailed status reference is authoritative.

---

# 39. ScenarioResult contract

A completed runner returns one structured `ScenarioResult`.

Required logical fields:

```text
scenario_id
script_path
script_hash
required
validation_status
execution_state
command
working_directory
effective_gf_path
exit_code
timed_out
duration_ms
stdout_path
stderr_path
stdout_truncated
stderr_truncated
normalized_output_path
normalization_version
gold_path
gold_match
diagnostic_class
error_kind
primary_message
sections
artifacts
warnings
```

## 39.1 Paths

Project assets are project-relative in persisted output.

Run artifacts are run-relative.

Environment tool paths may be absolute according to schema policy.

## 39.2 Command

The command is stored as:

```text
executable
ordered argument list
```

Do not store only a rendered shell string.

## 39.3 Sections

Each required marker section records:

```text
id
begin_seen
end_seen
completed
order_index
```

## 39.4 Partial result

A launch failure or pre-execution policy failure still produces a `ScenarioResult` when a run directory exists.

---

# 40. Strict mode

Strict scenario execution requires:

- explicit resolved GF executable;
- supported GF version;
- no inherited GF-path fallback;
- scenario path containment;
- UTF-8 without undecodable bytes;
- no system-command features;
- no nested `eh`;
- no unauthorized `rf`;
- no unauthorized `wf`;
- finite positive timeout;
- output-size limits;
- complete required markers;
- exact expected artifact verification;
- required gold presence;
- gold read-only behavior;
- no unexpected source-tree writes;
- deterministic scenario order;
- manifest registration.

Strict mode does not turn untrusted scripts into safe sandboxed code.

---

# 41. Security model

## 41.1 Executable input

A `.gfs` scenario is executable input to GF.

Treat scenarios from untrusted projects as untrusted code.

## 41.2 No sandbox guarantee

GF Wordbench does not provide operating-system isolation.

Use a low-privilege account, container, or virtual machine for untrusted projects.

## 41.3 Path validation

Validate:

- script path;
- gold path;
- input paths;
- working directory;
- expected artifact paths;
- nested script paths.

## 41.4 Source protection

Before and after scenario execution, release or strict workflows may verify that protected project files were not modified.

Protected assets include:

```text
.gf source
.gfs scenarios
.gold files
project.toml
project documentation
```

## 41.5 Secrets

Scenario execution reports must not expose:

- credentials;
- secret environment values;
- complete environment dumps;
- unrelated user files.

## 41.6 Resource exhaustion

Bound:

- runtime;
- output;
- generation;
- artifact size;
- process tree;
- number of scenarios.

---

# 42. Windows behavior

## 42.1 Native executable

Windows execution uses the resolved `gf.exe`.

## 42.2 No manual quoting in argument values

When arguments are supplied as a list, the framework must not add manual quote characters merely because a path contains spaces.

## 42.3 Stdin

Scenario text is passed directly to the process.

Do not use `cmd.exe` redirection for normal execution.

## 42.4 Process tree

Timeout and cancellation handling must account for child processes.

## 42.5 Paths

Support:

- drive letters;
- spaces;
- Unicode;
- CRLF input;
- normalized persisted separators.

## 42.6 Launchers

Batch launchers do not own scenario semantics.

Equivalent CLI and GUI configuration must produce equivalent process requests.

---

# 43. Version compatibility

## 43.1 Capability policy

GF shell command availability and output can vary by GF version.

GF Wordbench maintains:

```text
minimum_supported_gf_version
tested_gf_versions
known_incompatible_gf_versions
```

## 43.2 Unknown newer GF

An unknown newer version:

- warns in permissive modes;
- may proceed when base capabilities pass;
- may fail in strict mode;
- must record the version.

## 43.3 Unsupported older GF

A version below the minimum fails before scenario execution.

## 43.4 Command capability

Version-sensitive options require:

- a version gate;
- a capability probe;
- or a documented adapter.

Silent fallback to different semantics is prohibited.

## 43.5 Script compatibility

The project validation specification should identify the GF versions against which scenarios and gold files were reviewed.

## 43.6 Output changes

When a new GF version changes output:

1. preserve raw evidence;
2. determine whether meaning changed;
3. update normalization only for genuine instability;
4. do not normalize away new errors;
5. review gold changes;
6. update compatibility tests.

---

# 44. Canonical scenario examples

The examples below show framework conventions.

They are not language-project specifications.

## 44.1 Load scenario

```text
ps "GF_WORDBENCH_BEGIN scenario-load"
ps "GF_WORDBENCH_BEGIN load"
i GrammarExample.gf
ps "GF_WORDBENCH_END load"
ps "GF_WORDBENCH_END scenario-load"
q
```

## 44.2 Missing-linearization scenario

```text
ps "GF_WORDBENCH_BEGIN scenario-missing"
i GrammarExample.gf
ps "GF_WORDBENCH_BEGIN missing"
pg -missing
ps "GF_WORDBENCH_END missing"
ps "GF_WORDBENCH_END scenario-missing"
q
```

## 44.3 Linearization scenario

```text
ps "GF_WORDBENCH_BEGIN scenario-linearize"
i GrammarExample.gf
ps "GF_WORDBENCH_BEGIN linearize-basic"
l -lang=LangExample ExampleTree
ps "GF_WORDBENCH_END linearize-basic"
ps "GF_WORDBENCH_END scenario-linearize"
q
```

## 44.4 Parse scenario

```text
ps "GF_WORDBENCH_BEGIN scenario-parse"
i GrammarExample.gf
ps "GF_WORDBENCH_BEGIN parse-basic"
p -lang=LangExample -cat=S "example sentence"
ps "GF_WORDBENCH_END parse-basic"
ps "GF_WORDBENCH_END scenario-parse"
q
```

## 44.5 Translation pipeline scenario

```text
ps "GF_WORDBENCH_BEGIN scenario-translation"
i GrammarSource.gf GrammarTarget.gf
ps "GF_WORDBENCH_BEGIN translate-basic"
p -lang=LangSource -cat=S "example source" | l -lang=LangTarget
ps "GF_WORDBENCH_END translate-basic"
ps "GF_WORDBENCH_END scenario-translation"
q
```

## 44.6 Bounded-generation scenario

```text
ps "GF_WORDBENCH_BEGIN scenario-generation-smoke"
i GrammarExample.gf
ps "GF_WORDBENCH_BEGIN generation-smoke"
gt -cat=S -depth=3 -number=25 | l -lang=LangExample
ps "GF_WORDBENCH_END generation-smoke"
ps "GF_WORDBENCH_END scenario-generation-smoke"
q
```

## 44.7 Morphology scenario

```text
ps "GF_WORDBENCH_BEGIN scenario-morphology"
i GrammarExample.gf
ps "GF_WORDBENCH_BEGIN morphology-basic"
ma -lang=LangExample "example"
ps "GF_WORDBENCH_END morphology-basic"
ps "GF_WORDBENCH_END scenario-morphology"
q
```

## 44.8 Retained-source introspection

```text
ps "GF_WORDBENCH_BEGIN scenario-introspection"
i -retain GrammarExample.gf
ps "GF_WORDBENCH_BEGIN operations"
so
ps "GF_WORDBENCH_END operations"
ps "GF_WORDBENCH_END scenario-introspection"
q
```

---

# 45. Scenario authoring rules

A normative project scenario should:

```text
[ ] have a registered unique ID
[ ] use UTF-8
[ ] stay inside project/validation/scenarios
[ ] load an explicit project entrypoint
[ ] emit an outer begin marker
[ ] emit begin/end markers for asserted sections
[ ] use finite generation bounds
[ ] avoid operating-system commands
[ ] avoid undeclared file reads
[ ] avoid file writes by default
[ ] avoid nested scripts by default
[ ] avoid interactive commands
[ ] end with q
[ ] have reviewed expected output or assertions
[ ] have a documented purpose
```

---

# 46. Runner algorithm

Canonical logical algorithm:

```python
def run_scenario(spec, run_config, run_paths):
    validate_scenario_id(spec.id)
    validate_registered_scenario(spec)
    validate_project_containment(spec.script_path)
    validate_gold_policy(spec)
    validate_expected_artifact_paths(spec)

    scenario_bytes = read_bytes(spec.script_path)
    scenario_text = decode_utf8(scenario_bytes)

    policy_findings = inspect_scenario_policy(scenario_text)
    if policy_findings.blocking:
        return build_not_started_policy_error(spec, policy_findings)

    script_hash = sha256(scenario_bytes)

    request = build_process_request(
        executable=run_config.gf_executable,
        args=build_verified_shell_args(run_config),
        cwd=resolve_scenario_cwd(spec, run_config),
        stdin_text=scenario_text,
        stdout_path=run_paths.scenario_stdout(spec.id),
        stderr_path=run_paths.scenario_stderr(spec.id),
        timeout_sec=resolve_scenario_timeout(spec, run_config),
        environment_overrides=resolve_gf_environment(run_config),
        output_size_limit=resolve_output_limit(spec, run_config),
    )

    process_result = run_process(request)

    preserve_raw_streams(process_result)

    marker_result = verify_required_markers(
        stdout_path=request.stdout_path,
        expected_sections=spec.sections,
    )

    normalized_path = normalize_scenario_output(
        stdout_path=request.stdout_path,
        stderr_path=request.stderr_path,
        normalization_version=run_config.normalization_version,
    )

    gold_result = compare_gold_if_required(
        actual_path=normalized_path,
        gold_path=spec.gold_path,
    )

    artifacts = verify_scenario_artifacts(spec, run_paths)

    return build_scenario_result(
        spec=spec,
        script_hash=script_hash,
        request=request,
        process_result=process_result,
        marker_result=marker_result,
        normalized_path=normalized_path,
        gold_result=gold_result,
        artifacts=artifacts,
    )
```

Private helper names may differ.

The ordering and responsibility boundaries are normative.

---

# 47. Failure-flow algorithm

```text
invalid registration
    -> do not launch
    -> CONFIG error result

invalid UTF-8
    -> do not launch
    -> CONFIG error result

prohibited command
    -> do not launch
    -> CONFIG/security error result

launch failure
    -> preserve launch message
    -> TOOL error result

timeout
    -> terminate process tree
    -> preserve partial streams
    -> TIMEOUT error result

non-zero exit
    -> preserve streams
    -> inspect diagnostics
    -> FAIL or ERROR

zero exit + missing marker
    -> SCRIPT failure

markers complete + gold mismatch
    -> validation FAIL

all checks pass
    -> OK
```

---

# 48. Report behavior

Reports consume `ScenarioResult`.

They must not:

- execute the scenario again;
- read `.gfs` to reconstruct execution facts;
- normalize output independently;
- compare gold independently;
- infer timeout from prose;
- rewrite project assets.

Reports should show:

- scenario ID;
- required flag;
- status;
- execution state;
- duration;
- primary message;
- failed sections;
- gold result;
- raw evidence paths;
- normalized output path;
- artifacts.

---

# 49. Regression comparison

Scenario regression identity is:

```text
scenario_id
```

Possible changes:

```text
unchanged
improved
regressed
new
removed
```

Comparison uses structured `ScenarioResult` data from `summary.json`.

Gold files are not used directly as prior-run records.

---

# 50. Required tests

Recommended test structure:

```text
tests/scenarios/
├── test_scenario_registry.py
├── test_scenario_id.py
├── test_scenario_paths.py
├── test_scenario_encoding.py
├── test_scenario_policy.py
├── test_scenario_request.py
├── test_scenario_stdin.py
├── test_scenario_timeout.py
├── test_scenario_cancellation.py
├── test_scenario_output_limits.py
├── test_scenario_markers.py
├── test_scenario_normalization.py
├── test_scenario_gold.py
├── test_scenario_artifacts.py
├── test_scenario_result.py
├── test_scenario_security.py
└── test_scenario_integration_gf.py
```

## 50.1 Registry tests

Verify:

- required scenario exists;
- optional scenario selection;
- duplicate ID rejection;
- unregistered file not executed;
- deterministic order;
- filename derivation.

## 50.2 Encoding tests

Verify:

- UTF-8;
- Unicode linguistic strings;
- CRLF;
- BOM compatibility;
- invalid byte sequence;
- final newline.

## 50.3 Process-request tests

Verify:

- explicit executable;
- argument list;
- `shell=False`;
- explicit cwd;
- direct stdin;
- effective GF path;
- timeout;
- output paths;
- environment isolation.

## 50.4 Marker tests

Verify:

- complete pair;
- missing begin;
- missing end;
- duplicate begin;
- duplicate end;
- reversed order;
- unexpected marker;
- marker text inside a larger output line;
- bare pseudo-marker not accepted;
- `ps`-emitted marker accepted.

## 50.5 Policy tests

Verify rejection of:

```text
!
?
sp
unauthorized eh
unauthorized rf
unauthorized wf
interactive commands
unbounded generation
path traversal
```

## 50.6 Output tests

Verify:

- stdout-only diagnostics;
- stderr-only diagnostics;
- non-zero exit;
- zero exit with fatal diagnostic;
- output truncation;
- ANSI removal;
- CRLF normalization;
- Unicode preservation;
- raw output unchanged.

## 50.7 Gold tests

Verify:

- match;
- mismatch;
- missing required gold;
- optional no-gold scenario;
- normal run does not write gold;
- explicit update writes atomically;
- normalization-version mismatch.

## 50.8 Artifact tests

Verify:

- required artifact exists;
- missing artifact;
- artifact outside approved root;
- unexpected source mutation;
- manifest registration;
- SHA-256.

## 50.9 Real-GF tests

A small trusted fixture should test:

- load;
- marker emission with `ps`;
- parse;
- linearize;
- parse-to-linearize pipe;
- `pg -missing`;
- bounded `gr`;
- bounded `gt`;
- morphology;
- `q`;
- timeout where safely reproducible.

Real-GF tests must be marked separately from unit tests using fake process responses.

---

# 51. Contract checker

Suggested command:

```text
gf-wordbench scenarios check
```

Checks:

```text
scenario IDs unique
registered scripts exist
required gold files exist
UTF-8 decoding succeeds
paths remain contained
no prohibited system commands
no unauthorized nested scripts
no unauthorized reads or writes
generation is bounded
required markers are declared
q termination present
scenario hashes computable
GF version policy declared
normalization version declared
```

Strict form:

```text
gf-wordbench scenarios check --strict
```

Strict checking may reject every non-approved GF shell command.

---

# 52. Change control

A scenario-execution contract change must identify:

```text
Contract ID:
Current invocation:
New invocation:
GF versions affected:
Platforms affected:
Script syntax affected:
Marker syntax affected:
Normalization affected:
Gold affected:
Security affected:
Result fields affected:
Compatibility:
Migration:
Tests:
```

Required checklist:

```text
[ ] scenario runner updated
[ ] process runner reviewed
[ ] project configuration reviewed
[ ] external-tool lock updated
[ ] interfile lock updated
[ ] persisted schema reviewed
[ ] scenario format updated
[ ] normalization docs updated
[ ] gold files reviewed
[ ] security policy reviewed
[ ] unit tests updated
[ ] real-GF tests updated
[ ] compatibility notes updated
```

---

# 53. Drift indicators

Probable drift exists when:

- `.gfs` is executed through a shell-redirection command string;
- CLI and GUI build different scenario requests;
- scenario arguments are not recorded;
- working directory depends on the launcher;
- compilation and scenarios use different GF paths;
- raw output is overwritten by normalized output;
- a bare unrecognized line is used as a completion marker;
- one component verifies markers differently from another;
- gold is compared before normalization;
- normal validation modifies `.gold`;
- random output is used as unstable exact gold;
- generation has no effective bound;
- a required scenario is silently skipped;
- a zero exit code overrides missing markers;
- stdout is inspected but stderr is discarded;
- system commands appear without authorization;
- nested scripts are not included in the hash;
- unexpected artifacts are ignored;
- a report reruns the scenario;
- scenario status values differ from shared status values;
- normalization changes without gold review.

Any drift indicator requires contract review.

---

# 54. Implementation completion checklist

The scenario system is complete when:

```text
[ ] native .gfs execution is implemented
[ ] direct stdin is implemented
[ ] shell=False is enforced
[ ] scenario IDs are stable
[ ] project registration is authoritative
[ ] required and optional scenarios are distinct
[ ] scenario order is deterministic
[ ] exact executed script hash is recorded
[ ] UTF-8 is explicit
[ ] working directory is explicit
[ ] effective GF path is recorded
[ ] finite timeouts are enforced
[ ] process-tree termination is implemented
[ ] stdout and stderr are separate
[ ] output limits are enforced
[ ] ps-based markers are implemented
[ ] missing markers fail
[ ] raw evidence precedes normalization
[ ] normalization is versioned
[ ] gold comparison is read-only
[ ] explicit gold update exists
[ ] system commands are blocked
[ ] nested scripts are blocked by default
[ ] file reads are controlled
[ ] file writes are controlled
[ ] interactive commands are blocked
[ ] generation bounds are checked
[ ] expected artifacts are verified
[ ] ScenarioResult is complete
[ ] summary.json serializes scenario results
[ ] reports consume existing results only
[ ] manifest includes scenario artifacts
[ ] unit tests pass
[ ] real-GF integration tests pass
[ ] Windows paths with spaces pass
[ ] strict mode passes
```

---

# 55. Related documents

```text
docs/architecture/EXECUTION_FLOW.md
docs/architecture/PROCESS_EXECUTION_MODEL.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/gf/GF_PATH_RESOLUTION.md
docs/gf/GF_OUTPUT_NORMALIZATION.md
docs/gf/GF_VERSION_COMPATIBILITY.md
docs/validation/SCENARIO_VALIDATION.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/WRITING_GFS_SCENARIOS.md
docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/VALIDATION_SPEC.md
SECURITY.md
```

---

# 56. Upstream GF references

This specification was checked against these primary GF documents:

- **GF Shell Reference** — GF shell command model, standard-input scripting, import, parse, linearize, generation, introspection, system commands, file commands, and quit.
- **GF Developers Guide** — `.gfs`, `.out`, and `.gold` test-suite architecture.
- **GF Quick Start / Tutorial** — shell-script execution and parse-to-linearize usage.
- **GF Language Reference Manual** — `.gf`, `.gfo`, and `.pgf` roles.

Upstream documentation defines GF behavior.

This file defines the stricter GF Wordbench orchestration contract.

---

# 57. Final rule

A `.gfs` scenario is a reviewed executable validation asset.

GF executes its commands.

GF Wordbench proves that the intended scenario actually completed.

Therefore:

> A scenario passes only when the process boundary is valid, required GF commands complete, stable markers are observed, raw evidence is preserved, declared assertions pass, required artifacts exist, and golden output matches where required.
