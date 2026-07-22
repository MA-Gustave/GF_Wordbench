# GF Wordbench — Writing `.gfs` Scenarios

**Document ID:** `GF-WB-WRITING-GFS-SCENARIOS`  
**Status:** Normative  
**Applies to:** Active-project scenario authors, scenario reviewers, scenario runner, gold comparator, project migration, and release validation  
**Owner:** GF Wordbench maintainers and active-project maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\scenarios\WRITING_GFS_SCENARIOS.md`  
**Scenario authoring contract:** `1.0.0`  
**Marker protocol:** `1`  
**Last reviewed:** `2026-07-21`

---

## 1. Purpose

This document defines how to write reliable native GF shell scenarios for GF Wordbench.

A scenario is a project-owned `.gfs` file executed by the real GF shell.

It is used to validate observable grammar behavior such as:

- loading an entrypoint;
- inspecting missing linearizations;
- linearizing representative trees;
- parsing representative strings;
- exercising parse-linearize round trips;
- performing bounded generation;
- checking morphology;
- inspecting operations or source interfaces;
- proving a checkpoint;
- supplying release evidence.

The scenario author is responsible for defining a small, deterministic and reviewable validation purpose.

GF Wordbench is responsible for:

- invoking GF reproducibly;
- supplying the scenario through standard input;
- enforcing a timeout;
- capturing stdout and stderr separately;
- parsing GF Wordbench markers;
- normalizing output;
- evaluating assertions;
- comparing reviewed gold output;
- preserving evidence;
- reporting the result.

GF remains authoritative for GF shell semantics and grammar execution.

GF Wordbench must not implement a second interpreter for `.gfs` commands.

---

## 2. Core authoring rule

> One scenario must prove one declared behavior through explicit GF commands, bounded output, machine-detectable completion, and reviewable evidence.

A scenario is not correct merely because GF exits with code zero.

A scenario succeeds only when all applicable conditions hold:

```text
GF starts
and the scenario does not time out
and required markers are observed
and required sections complete
and no fatal diagnostic invalidates the scenario
and required assertions pass
and required artifacts exist
and required gold comparison matches
```

---

## 3. Relationship to other documents

| Topic | Authoritative document |
|---|---|
| Scenario data model and persisted result | `docs/PERSISTED_SCHEMA_LOCK.md` |
| GF process invocation | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Scenario runner dependency direction | `docs/architecture/DEPENDENCY_RULES.md` |
| Mode applicability | `docs/validation/VALIDATION_MODES.md` |
| General scenario file contract | `docs/scenarios/SCENARIO_FORMAT.md` |
| Marker grammar | `docs/scenarios/SCENARIO_MARKERS_AND_ASSERTIONS.md` |
| Output normalization | `docs/scenarios/OUTPUT_NORMALIZATION.md` |
| Gold comparison | `docs/scenarios/GOLDEN_TESTS.md` |
| Gold update procedure | `docs/scenarios/UPDATING_GOLD_FILES.md` |
| Active-project scenario registry | `project/project.toml` |
| Active-project validation intent | `project/docs/VALIDATION_SPEC.md` |
| Scenario-to-entrypoint and scenario-to-gold relationships | `project/docs/INTERFILE_CONTRACT_LOCK.md` |

This document owns authoring practice.

It must not redefine persisted schema or process execution details owned elsewhere.

---

## 4. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **SCENARIO**: one registered `.gfs` validation script.
- **SCENARIO ID**: stable project-unique identifier for a scenario.
- **SECTION**: named contiguous region of scenario output.
- **MARKER**: reserved string emitted through a valid GF command and interpreted by GF Wordbench.
- **ASSERTION**: machine-evaluated condition applied to scenario evidence.
- **RAW OUTPUT**: exact captured stdout or stderr bytes decoded under the execution policy.
- **NORMALIZED OUTPUT**: stable derived output used for assertions or gold comparison.
- **GOLD**: reviewed expected normalized output.
- **ENTRYPOINT**: documented GF module loaded by a scenario.
- **INPUT ASSET**: project-owned file consumed by a scenario.
- **REQUIRED SCENARIO**: applicable scenario that must pass.
- **OPTIONAL SCENARIO**: applicable scenario whose result remains visible but is not blocking unless project policy promotes it.
- **BOUNDED**: constrained by an explicit count, depth, timeout, file size, or output limit.
- **FRESH PROCESS**: a new GF process with no state inherited from another scenario.
- **SCENARIO CONTRACT FAILURE**: GF ran, but the scenario did not satisfy its marker, assertion, artifact, or output contract.

---

# 5. What a `.gfs` scenario is

A `.gfs` scenario is a sequence of GF shell commands.

The scenario runner starts GF and sends the file contents to standard input.

Conceptually:

```text
gf
stdin = contents of project/validation/scenarios/<scenario-id>.gfs
```

The runner should use direct process standard input rather than shell redirection.

The file itself remains a project source asset.

It is not generated per run.

---

# 6. What a `.gfs` scenario is not

A `.gfs` scenario is not:

- a Python test;
- a shell script;
- a batch file;
- a YAML document;
- a TOML document;
- a custom GF Wordbench language;
- a report template;
- a gold file;
- a place for hidden project configuration;
- an unrestricted command runner;
- a replacement for direct `.gf` compilation.

Do not embed front matter such as:

```text
---
id: parse-basic
required: true
---
```

GF Wordbench does not treat such text as scenario metadata.

Scenario metadata belongs to the project registry and validation documentation.

---

# 7. Canonical directory layout

```text
project/
└── validation/
    ├── scenarios/
    │   ├── load-main.gfs
    │   ├── missing-linearizations.gfs
    │   ├── linearize-basic.gfs
    │   ├── parse-basic.gfs
    │   ├── roundtrip-basic.gfs
    │   ├── generation-bounded.gfs
    │   └── morphology-basic.gfs
    ├── inputs/
    │   ├── parse-basic/
    │   │   └── sentences.txt
    │   └── morphology-basic/
    │       └── words.txt
    └── gold/
        ├── missing-linearizations.gold
        ├── linearize-basic.gold
        ├── parse-basic.gold
        └── morphology-basic.gold
```

Not every project requires every example.

The active project defines its own scenario inventory.

---

# 8. Naming rules

## 8.1 Scenario ID

Recommended format:

```text
[a-z][a-z0-9-]{1,63}
```

Examples:

```text
load-main
linearize-basic
parse-relative-clause
morphology-nouns
generation-small
```

Avoid:

```text
Parse Test
scenario_01_final_final
MyLanguageScenario
test
```

A scenario ID should communicate purpose, not implementation history.

## 8.2 Script filename

The canonical script filename is:

```text
<scenario-id>.gfs
```

Example:

```text
linearize-basic.gfs
```

## 8.3 Gold filename

When the scenario has one canonical gold:

```text
<scenario-id>.gold
```

## 8.4 Input directory

When several inputs belong only to one scenario:

```text
project/validation/inputs/<scenario-id>/
```

## 8.5 Section ID

Recommended format:

```text
[a-z][a-z0-9-]{0,63}
```

Examples:

```text
load
missing
positive
negative
nouns
verbs
summary
```

Section IDs must be unique within one scenario.

---

# 9. One scenario, one primary purpose

Each scenario must have one primary validation purpose.

Good examples:

```text
load the release entrypoint
list missing linearizations
linearize ten representative trees
parse twenty reviewed strings
validate noun morphology examples
perform bounded generation for Cl
```

Poor examples:

```text
test everything
run miscellaneous commands
inspect grammar
try new features
```

A scenario may contain several sections when they support one purpose.

Example:

```text
scenario: parse-basic

sections:
  load
  positive
  ambiguous
  rejected
```

Do not combine unrelated morphology, parsing, generation and release-artifact checks in one large script merely to reduce file count.

Small scenarios improve:

- failure localization;
- gold review;
- mode selection;
- timeout tuning;
- reuse across checkpoints;
- regression comparison.

---

# 10. Fresh-process isolation

Every scenario should run in a fresh GF process.

A scenario must not depend on:

- grammar state left by another scenario;
- command macros defined by another scenario;
- shell history from another scenario;
- current terminal state;
- the order in which other scenarios ran;
- files generated by another scenario unless registered as explicit prerequisites.

Because each scenario starts independently, the script must load every grammar or resource it requires.

This isolation makes scenarios reproducible and parallelizable.

---

# 11. Canonical scenario skeleton

Use this pattern:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=<scenario-id>"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i <ENTRYPOINT>.gf
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=<validation-section>"
<GF COMMANDS>
ps "__GF_WORDBENCH_SECTION_END__ id=<validation-section>"

ps "__GF_WORDBENCH_SCENARIO_END__ id=<scenario-id>"
q
```

Replace every placeholder before registering the scenario.

A file containing unresolved `<PLACEHOLDER>` text is invalid.

---

# 12. Marker protocol

## 12.1 Reserved prefix

GF Wordbench reserves:

```text
__GF_WORDBENCH_
```

Project linguistic output must not intentionally begin with this prefix.

## 12.2 Required scenario markers

Every registered scenario must emit exactly one begin marker:

```text
__GF_WORDBENCH_SCENARIO_BEGIN__
```

and exactly one end marker:

```text
__GF_WORDBENCH_SCENARIO_END__
```

## 12.3 Required attributes

Scenario begin:

```text
version=1
id=<scenario-id>
```

Scenario end:

```text
id=<scenario-id>
```

## 12.4 Section markers

A section uses:

```text
__GF_WORDBENCH_SECTION_BEGIN__ id=<section-id>
__GF_WORDBENCH_SECTION_END__ id=<section-id>
```

## 12.5 Emission command

Markers must be emitted with a valid GF command:

```gf
ps "<marker>"
```

Do not place marker text alone on a line.

Incorrect:

```text
__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=parse-basic
```

Correct:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=parse-basic"
```

## 12.6 Why executable markers are required

An arbitrary line may be unrecognized by GF and skipped.

A marker must therefore be produced by a real GF command.

The runner must still check diagnostics and assertions, because reaching an end marker proves only that command processing continued to that point.

## 12.7 Marker matching

The runner should recognize a marker only when:

- the reserved marker token appears on its own normalized output line;
- the scenario or section ID is exact;
- the marker order is valid;
- no duplicate marker violates the protocol.

The runner may strip GF prompts before matching.

It must not search arbitrary substrings inside linguistic output.

## 12.8 Marker order

Valid order:

```text
SCENARIO_BEGIN
SECTION_BEGIN
SECTION_END
SECTION_BEGIN
SECTION_END
SCENARIO_END
```

Invalid:

```text
SECTION_BEGIN before SCENARIO_BEGIN
nested SECTION_BEGIN
SECTION_END with different ID
SCENARIO_END while a section is open
duplicate SCENARIO_END
output section after SCENARIO_END
```

Nested sections are prohibited in protocol version 1.

---

# 13. Completion is not success

The end marker confirms that the script reached its final marker command.

It does not prove that every previous command succeeded.

GF Wordbench must combine:

- process outcome;
- timeout state;
- stdout;
- stderr;
- fatal-diagnostic detection;
- marker validity;
- assertions;
- gold comparison;
- required artifact checks.

Scenario authors must provide assertions or gold evidence where command failure might otherwise be invisible.

---

# 14. End the scenario explicitly

The final command must be:

```gf
q
```

Place it after the scenario end marker.

Canonical ending:

```gf
ps "__GF_WORDBENCH_SCENARIO_END__ id=parse-basic"
q
```

Do not place required output after `q`.

Do not depend on end-of-file alone to terminate the session.

---

# 15. Loading grammars

## 15.1 Source entrypoint

Typical source import:

```gf
i <ENTRYPOINT>.gf
```

The entrypoint must be registered in project configuration or the project interfile contract.

## 15.2 PGF entrypoint

A PGF validation scenario may import:

```gf
i <GRAMMAR>.pgf
```

The PGF path must refer to the current run’s registered artifact or another explicitly approved source.

Do not load an old arbitrary PGF from a developer directory.

## 15.3 Retained source operations

Resource or operation introspection may require:

```gf
i -retain <RESOURCE>.gf
```

Use `-retain` only when the scenario needs source operations such as operation or source inspection.

A normal runtime grammar scenario should not add it without purpose.

## 15.4 Explicit entrypoint

Do not rely on a filename convention when the project has explicit entrypoints.

The loaded module must match:

- scenario registry;
- project configuration;
- project interfile contract;
- validation specification.

## 15.5 Import evidence

Every scenario should have a `load` section.

Example:

```gf
ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i GrammarX.gf
pg -langs
ps "__GF_WORDBENCH_SECTION_END__ id=load"
```

The `pg -langs` line provides visible grammar-state evidence.

---

# 16. Working directory and paths

## 16.1 Canonical working directory

The default scenario working directory is the resolved project root.

A scenario-specific working directory may be configured only when documented.

## 16.2 Relative paths

Project-owned paths in scenarios should be relative to the project root.

Preferred:

```text
project/validation/inputs/parse-basic/sentences.txt
```

Avoid:

```text
C:\Users\name\Desktop\sentences.txt
/home/name/project/sentences.txt
```

## 16.3 Path separators

Use `/` in project-owned scenario paths.

The runner and GF compatibility layer are responsible for host-platform resolution where needed.

## 16.4 Quoting

Quote filenames supplied to file-oriented commands.

Example:

```gf
rf -lines -file="project/validation/inputs/parse-basic/sentences.txt"
```

## 16.5 Path containment

A scenario must not read or write outside:

- project-owned input roots;
- the current run directory;
- explicitly approved external grammar roots.

Parent traversal such as `../..` should be rejected by project validation.

---

# 17. Encoding

Scenario files must use:

```text
UTF-8 without BOM
```

Canonical newlines:

```text
LF
```

The runner may accept CRLF and normalize it before execution.

Input and gold files must follow their own schema contracts.

Unicode linguistic content may appear directly in quoted GF strings.

Do not depend on terminal-specific encodings.

---

# 18. Command-line discipline inside `.gfs`

## 18.1 One command line per line

Write one logical GF command line per physical line.

GF supports pipes and semicolon-separated commands, but long compound lines are harder to diagnose.

Preferred:

```gf
p -lang=LangX -cat=Utt "example"
l -lang=LangX ExampleTree
```

Use a pipe when the pipe itself is the behavior under test:

```gf
p -lang=LangX -cat=Utt "example" | l -lang=LangX
```

## 18.2 Explicit flags

Prefer explicit:

```gf
p -lang=LangX -cat=Utt "example"
gt -lang=LangX -cat=Cl -depth=2 -number=20
l -lang=LangX ExampleTree
```

Avoid relying on:

- current default language;
- current start category;
- previous macro state;
- implicit grammar state not established in the script.

## 18.3 Stable command names

Short GF command names such as `i`, `p`, `l`, `pg`, `ma`, `gt`, `gr`, `ps`, `rf`, `so`, `ss`, and `q` are valid shell commands.

A project may prefer long command names for readability only when tested across supported GF versions.

Within one project, use one consistent style.

## 18.4 No terminal prompts

Do not include:

```text
>
gf>
$
C:\>
```

in the `.gfs` file.

Only GF commands belong in the script.

---

# 19. Input-string rules

## 19.1 Quote strings

Use double quotes:

```gf
p -lang=LangX -cat=Utt "the reviewed example"
ma -lang=LangX "word one word two"
```

## 19.2 Escape review

Any embedded quote or special character must be validated against actual GF shell string syntax.

Do not generate quoting rules independently in several tools.

## 19.3 One concern per input

Each input should have an intentional role:

- positive parse;
- expected ambiguity;
- expected rejection;
- morphology coverage;
- orthographic variant;
- regression reproduction.

Do not add large unexplained lists.

## 19.4 External input files

Use input files when:

- the list is long;
- one input per line improves review;
- the same list is reused;
- linguistic data should be reviewed separately from commands.

Example:

```gf
rf -lines -file="project/validation/inputs/parse-basic/sentences.txt" | p -lang=LangX -cat=Utt
```

The exact pipeline must be integration-tested with the supported GF versions.

---

# 20. Writing a load scenario

Purpose:

```text
prove that the configured entrypoint loads in a fresh GF process
```

Template:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=load-main"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i <ENTRYPOINT>.gf
pg -langs
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SCENARIO_END__ id=load-main"
q
```

Recommended assertions:

```text
required marker: section load
required output: configured concrete language name
forbidden diagnostic: fatal import or compile error
```

Do not use this scenario as a substitute for direct compilation evidence.

---

# 21. Writing a missing-linearization scenario

Purpose:

```text
list abstract functions lacking a linearization in the selected concrete grammar
```

Template:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=missing-linearizations"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i <ENTRYPOINT>.gf
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=missing"
pg -missing -lang=<CONCRETE_MODULE>
ps "__GF_WORDBENCH_SECTION_END__ id=missing"

ps "__GF_WORDBENCH_SCENARIO_END__ id=missing-linearizations"
q
```

Recommended comparison:

```text
exact normalized gold
```

Release policy may require the normalized `missing` section to be empty.

Do not normalize away missing function names.

---

# 22. Writing a linearization scenario

Purpose:

```text
verify representative abstract trees and their concrete output
```

Template:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=linearize-basic"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i <ENTRYPOINT>.gf
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=representative"
l -lang=<CONCRETE_MODULE> <TREE_1>
l -lang=<CONCRETE_MODULE> <TREE_2>
l -lang=<CONCRETE_MODULE> <TREE_3>
ps "__GF_WORDBENCH_SECTION_END__ id=representative"

ps "__GF_WORDBENCH_SCENARIO_END__ id=linearize-basic"
q
```

Authoring rules:

- use reviewed typed trees;
- cover the declared linguistic contract;
- keep order stable;
- separate categories into sections when useful;
- prefer exact gold comparison;
- do not include unstable random trees.

Good coverage dimensions may include:

- number;
- gender;
- definiteness;
- case;
- agreement;
- tense;
- polarity;
- person;
- word order;
- clitic placement;
- coordination;
- subordination.

Only dimensions relevant to the active project belong in its scenario.

---

# 23. Writing a parse scenario

Purpose:

```text
verify that reviewed strings parse to expected abstract syntax
```

Template:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=parse-basic"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i <ENTRYPOINT>.gf
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=positive"
p -lang=<CONCRETE_MODULE> -cat=<CATEGORY> "<STRING_1>"
p -lang=<CONCRETE_MODULE> -cat=<CATEGORY> "<STRING_2>"
ps "__GF_WORDBENCH_SECTION_END__ id=positive"

ps "__GF_WORDBENCH_SCENARIO_END__ id=parse-basic"
q
```

Authoring rules:

- always state `-lang`;
- normally state `-cat`;
- document expected ambiguity;
- bound parser depth when metavariable proof search requires it;
- keep robust parsing options out of strict parse scenarios;
- separate positive and intentionally rejected examples;
- do not accept “some parse exists” when a specific tree is required.

Possible assertion profiles:

```text
at least one parse
exact tree set
contains expected tree
exact normalized output
no parse expected
bounded parse count
```

---

# 24. Writing a parse-linearize round-trip scenario

Purpose:

```text
verify that parsing and linearization remain mutually coherent for reviewed examples
```

Template:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=roundtrip-basic"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i <ENTRYPOINT>.gf
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=roundtrip"
p -lang=<CONCRETE_MODULE> -cat=<CATEGORY> "<STRING_1>" | l -lang=<CONCRETE_MODULE>
p -lang=<CONCRETE_MODULE> -cat=<CATEGORY> "<STRING_2>" | l -lang=<CONCRETE_MODULE>
ps "__GF_WORDBENCH_SECTION_END__ id=roundtrip"

ps "__GF_WORDBENCH_SCENARIO_END__ id=roundtrip-basic"
q
```

A round trip need not reproduce the original string exactly when the grammar intentionally canonicalizes variants.

The gold must represent the accepted canonicalization policy.

Do not interpret orthographic normalization as semantic equivalence without project documentation.

---

# 25. Writing a bounded-generation scenario

Purpose:

```text
exercise a controlled finite part of the abstract syntax
```

Prefer exhaustive bounded generation:

```gf
gt -lang=<CONCRETE_MODULE> -cat=<CATEGORY> -depth=<SMALL_DEPTH> -number=<SMALL_LIMIT>
```

Example structure:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=generation-bounded"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i <ENTRYPOINT>.gf
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=generate"
gt -lang=<CONCRETE_MODULE> -cat=<CATEGORY> -depth=2 -number=20 | l -lang=<CONCRETE_MODULE>
ps "__GF_WORDBENCH_SECTION_END__ id=generate"

ps "__GF_WORDBENCH_SCENARIO_END__ id=generation-bounded"
q
```

Required bounds:

- explicit category;
- explicit depth;
- explicit number;
- finite scenario timeout;
- output-size limit.

Random generation command `gr` may be useful diagnostically.

It should not feed an exact gold unless deterministic behavior is proven and version-controlled.

---

# 26. Writing a morphology scenario

Purpose:

```text
verify reviewed morphological analyses or identify missing words
```

Template:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=morphology-basic"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i <ENTRYPOINT>.gf
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=analysis"
ma -lang=<CONCRETE_MODULE> "<WORD_1> <WORD_2> <WORD_3>"
ps "__GF_WORDBENCH_SECTION_END__ id=analysis"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=missing"
ma -missing -lang=<CONCRETE_MODULE> "<WORD_1> <WORD_2> <WORD_3>"
ps "__GF_WORDBENCH_SECTION_END__ id=missing"

ps "__GF_WORDBENCH_SCENARIO_END__ id=morphology-basic"
q
```

Use exact gold only when morphological output is stable across supported GF versions.

For large word lists, use a project input file.

Do not treat an empty missing-word list as proof of correct analysis.

---

# 27. Writing an operations-introspection scenario

Purpose:

```text
verify resource operations exposed by a retained source grammar
```

Template:

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=operations-interface"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i -retain <RESOURCE_MODULE>.gf
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=operations"
so -grep=<STABLE_FILTER>
ps "__GF_WORDBENCH_SECTION_END__ id=operations"

ps "__GF_WORDBENCH_SCENARIO_END__ id=operations-interface"
q
```

This scenario validates a source-level interface.

It should not become a duplicate of the project’s category and lincat documentation.

Use stable filters.

Avoid golding the complete operation inventory when unrelated RGL changes would create noise.

---

# 28. Writing a source-interface scenario

Purpose:

```text
inspect stable compiled source headers or module interfaces
```

Possible command:

```gf
ss -strip <MODULE>
```

Requirements:

- import source with `-retain`;
- restrict output to documented modules;
- normalize only known unstable formatting;
- avoid complete source dumps in normal reports;
- use this scenario only when the interface itself is a contract.

Source inspection must not replace direct compiler tests.

---

# 29. Input-file scenarios

## 29.1 Why use inputs

Separate input files are appropriate when linguistic data deserves independent review.

Examples:

```text
sentences
words
abstract trees
expected rejected strings
ambiguity cases
```

## 29.2 Input format

Prefer one logical item per line.

Use UTF-8 and LF.

Document whether blank lines are significant.

## 29.3 Registration

Every input file must be:

- project-relative;
- version-controlled;
- assigned to a scenario;
- listed in project validation documentation;
- validated before execution.

## 29.4 Stable ordering

The file order is validation order unless the scenario explicitly defines another deterministic order.

## 29.5 No implicit globbing

A scenario should not load every file matching a broad pattern.

The registry must identify the intended inputs.

---

# 30. Macros

GF shell tree or command macros may be used when they improve clarity.

Examples of relevant GF shell features include tree macros and command macros.

Rules:

- define every macro within the same scenario;
- use stable names;
- keep definitions near their use;
- do not depend on shell history;
- do not hide the primary behavior;
- avoid macros for only one short command;
- gold the expanded observable result, not the macro definition alone.

Macros must not become a second project configuration system.

---

# 31. Pipes

Pipes are appropriate when the composition itself is under test.

Examples:

```gf
p -lang=LangX -cat=Utt "example" | l -lang=LangX
gt -lang=LangX -cat=Cl -depth=2 -number=10 | l -lang=LangX
rf -lines -file="project/validation/inputs/parse-basic/sentences.txt" | p -lang=LangX -cat=Utt
```

Rules:

- keep the pipe short;
- document the expected data type between commands;
- bound commands that can produce multiple values;
- avoid operating-system pipes;
- preserve the full raw line in evidence.

---

# 32. Semicolon-separated commands

GF shell command lines may contain semicolon-separated command pipes.

GF Wordbench scenarios should normally avoid them.

Preferred:

```gf
p -lang=LangX -cat=Utt "example"
l -lang=LangX ExampleTree
```

Instead of:

```gf
p -lang=LangX -cat=Utt "example" ; l -lang=LangX ExampleTree
```

Separate lines improve:

- diagnostic localization;
- marker placement;
- review;
- compatibility testing.

Use semicolons only when sequential execution on one command line is the behavior being validated.

---

# 33. Determinism rules

A scenario used for regression or release must be deterministic under its declared environment.

It must define:

- exact entrypoint;
- exact language;
- exact category where relevant;
- exact input order;
- bounded generation;
- stable section order;
- normalization version;
- gold version where applicable.

Avoid:

- random generation in exact golds;
- current time;
- temporary absolute paths in expected output;
- directory enumeration without sorting;
- unspecified default language;
- unspecified start category when material;
- operating-system command output;
- external network data;
- mutable files outside the project;
- previous scenario state.

---

# 34. Bounded-output rules

Every scenario must have a finite process timeout.

Potentially expansive commands must also have command-level bounds.

## 34.1 Generation

Specify:

```text
category
depth
number
```

## 34.2 Parsing

Use reviewed inputs and optional depth bounds where required.

Do not parse an uncontrolled corpus in one release scenario.

## 34.3 Source and operation inspection

Filter to required modules or stable substrings.

## 34.4 Output files

Scenario-created files must have explicit size and path policies.

## 34.5 Truncation

The runner may enforce output limits.

Truncation must be recorded.

A gold comparison cannot pass against truncated required output.

---

# 35. Assertions

A scenario may use one or more assertion types.

Canonical concepts:

```text
required marker
forbidden marker
required text
forbidden text
required regex
forbidden regex
exact normalized section
empty normalized section
nonempty normalized section
bounded result count
required artifact
forbidden fatal diagnostic
gold match
```

Assertions belong to scenario metadata or the validation specification.

Do not invent assertion syntax as unrecognized lines inside `.gfs`.

The `.gfs` file emits evidence.

GF Wordbench evaluates assertions outside the GF shell.

---

# 36. Recommended assertion strategy

## 36.1 Load scenario

```text
required section: load
required language: configured concrete
forbidden fatal diagnostic
```

## 36.2 Missing scenario

```text
required section: missing
exact gold or empty section
```

## 36.3 Linearization scenario

```text
required section
exact normalized gold
forbidden missing-linearization diagnostic
```

## 36.4 Parse scenario

```text
required parse count
contains expected tree
or exact normalized gold
```

## 36.5 Generation scenario

```text
result count <= configured limit
section nonempty
no fatal diagnostic
```

## 36.6 Morphology scenario

```text
expected analyses present
unexpected missing words absent
gold when stable
```

---

# 37. Gold comparison

A gold file contains expected normalized output.

It does not contain raw GF prompts, terminal noise or machine-specific paths.

The runner should transform raw scenario sections into the canonical normalized form defined by the persisted schema.

Conceptually:

```text
raw marker:
__GF_WORDBENCH_SECTION_BEGIN__ id=representative

normalized section:
--- BEGIN representative ---
...
--- END representative ---
```

A scenario may gold:

- the complete normalized scenario;
- selected sections;
- a stable extracted representation.

The strategy must be declared.

---

# 38. Choosing what belongs in gold

Include:

- linguistically meaningful output;
- expected abstract trees;
- expected linearizations;
- expected missing function names;
- stable morphology results;
- stable section structure.

Exclude through documented normalization:

- prompts;
- elapsed time;
- absolute project path;
- run directory;
- executable path;
- nonsemantic platform line endings;
- approved version banner noise.

Do not normalize away:

- word order;
- inflection;
- function names;
- tree structure;
- ambiguity;
- missing linearizations;
- error messages required by the assertion;
- language identifiers relevant to the test.

---

# 39. Gold update discipline

Normal scenario execution must not modify gold.

A gold update is a separate explicit workflow.

Before accepting new gold, review:

```text
[ ] source change is intentional
[ ] validation purpose remains the same
[ ] changed linguistic output is correct
[ ] changed tree output is expected
[ ] no unstable noise entered the gold
[ ] no marker was lost
[ ] normalization version is correct
[ ] related project documentation is updated
[ ] release impact is understood
```

After updating gold, rerun the proving validation mode.

---

# 40. Raw and normalized evidence

For each scenario, preserve at least:

```text
script path
script hash
scenario ID
working directory
GF executable
GF version
GF path
ordered invocation
timeout
start and finish timestamps
exit code
execution state
stdout path
stderr path
normalized output path
marker result
assertion result
gold result
artifact list
```

Raw stdout and stderr must be saved before normalization.

A report must not rerun the scenario to fill missing evidence.

---

# 41. Scenario result semantics

A scenario result should distinguish:

```text
validation_status
execution_state
diagnostic_class
error_kind
```

Examples:

## 41.1 Validation failure

```text
execution_state = completed
validation_status = FAIL
error_kind = SCRIPT
primary_message = required marker missing
```

## 41.2 GF-reported failure

```text
execution_state = completed
validation_status = FAIL
error_kind = TYPE
primary_message = GF diagnostic
```

## 41.3 Timeout

```text
execution_state = timed_out
validation_status = ERROR
error_kind = TIMEOUT
```

## 41.4 Gold mismatch

```text
execution_state = completed
validation_status = FAIL
error_kind = OTHER
primary_message = gold mismatch
```

Do not classify a missing marker as a successful scenario merely because process exit was zero.

---

# 42. Required versus optional scenarios

The scenario registry defines requirement and mode applicability.

A required applicable scenario must exist and pass.

An optional scenario:

- may run;
- may fail under project policy;
- must remain visible;
- must not be silently omitted after selection.

A scenario author must not encode required/optional status only in the filename.

Bad:

```text
optional_parse_test.gfs
```

The registry is authoritative.

---

# 43. Mode applicability

Typical patterns:

## 43.1 Quick

Small smoke scenario:

- one entrypoint;
- very few commands;
- short timeout;
- bounded output.

## 43.2 Checkpoint

Scenario proving one subsystem:

- declared checkpoint;
- relevant entrypoint;
- representative examples;
- applicable gold.

## 43.3 Release

Scenario with stable complete evidence:

- required;
- deterministic;
- fully asserted;
- reviewed gold when appropriate;
- no unsafe command;
- all required markers.

## 43.4 Diagnostic

Expanded or focused scenario:

- introspection;
- optional verbose output;
- broader evidence;
- still bounded;
- not automatically release evidence.

A scenario can apply to several modes.

Its required status may depend on mode through project policy.

---

# 44. Security rules

A `.gfs` file is executable input to GF.

Only trusted project scenarios should run by default.

## 44.1 Prohibited operating-system commands

Normal scenarios must not use GF shell mechanisms that invoke operating-system commands.

Prohibited unless a dedicated security policy explicitly authorizes them:

```text
!
?
sp
system_pipe
```

This prohibition includes:

- shell escape;
- system pipes;
- external command execution;
- network clients;
- filesystem utilities outside GF Wordbench ownership.

## 44.2 No hidden shell redirection

Do not put platform shell syntax into `.gfs`:

```text
>
>>
<
2>
|
```

GF command pipes are allowed.

Operating-system pipes and redirection are not.

The runner itself supplies the scenario through stdin.

## 44.3 File reads

`rf` may read registered project inputs.

It must not read:

- user profile files;
- environment secrets;
- arbitrary absolute paths;
- files outside allowed roots.

## 44.4 File writes

`wf` should be avoided in ordinary validation because stdout is already captured.

When a scenario intentionally creates an artifact:

- path must be run-owned;
- artifact must be registered;
- overwrite policy must be explicit;
- project sources and gold files must remain untouched.

## 44.5 Untrusted strings

Do not construct GF command text from untrusted input.

Use reviewed input files and bounded values.

---

# 45. Commands to avoid by default

Avoid unless the scenario purpose explicitly requires them:

```text
!              operating-system escape
?              operating-system pipe
sp             operating-system command
wf             writes files
eh             executes command history from file
r              depends on previous import command
gr             random output
visualization  may invoke external viewers or tools
interactive quizzes
```

A command is not forbidden merely because it is uncommon.

It requires a documented purpose, compatibility evidence and security review when it crosses external boundaries.

---

# 46. Commands commonly suitable for scenarios

Commonly useful shell commands include:

```text
i / import             load a source, object or PGF grammar
l / linearize          linearize an abstract tree
p / parse              parse a string
pg / print_grammar     inspect grammar information
pg -missing            list functions without linearization
ma / morpho_analyse    inspect word analyses
gt / generate_trees    bounded exhaustive generation
gr / generate_random   diagnostic random generation only
rf / read_file         consume registered input assets
ps / put_string        emit markers or process strings
pt / put_tree          process trees
so / show_operations   inspect retained operations
ss / show_source       inspect retained compiled source
q / quit               terminate the scenario
```

Command and option availability must be checked against the supported GF versions.

---

# 47. Compatibility rules

## 47.1 Supported shell

Canonical scenarios target the standard GF shell.

An alternate shell or runtime profile requires explicit compatibility documentation.

## 47.2 Command availability

Every command and flag used by a required scenario must be available in all GF versions supported for that project release.

## 47.3 Version changes

When GF version changes:

1. run compatibility scenarios;
2. inspect raw output differences;
3. review normalization;
4. review all affected gold files;
5. update compatibility documentation;
6. do not hide semantic changes as noise.

## 47.4 Unknown commands

Because unrecognized lines may be skipped, required behavior must be detected through:

- markers;
- diagnostics;
- assertions;
- required output;
- required artifacts.

## 47.5 Help inspection

`help -full` may be used manually or in a compatibility probe.

A normal linguistic gold should not include the full help output.

---

# 48. Scenario review standards

A reviewer must be able to answer:

- What single behavior does this scenario prove?
- Which entrypoint does it load?
- Which project contract requires it?
- Which modes use it?
- Is it required or optional?
- Are all commands valid for supported GF versions?
- Is output bounded?
- Is ordering deterministic?
- Are markers complete?
- Are assertions sufficient?
- Is gold appropriate?
- Are input files reviewed?
- Can it modify any project file?
- Can it invoke the operating system?
- What failure would this scenario detect?
- What defect could still pass?

A scenario without a clear answer should not become a release requirement.

---

# 49. Scenario authoring workflow

## Step 1 — State the purpose

Write one sentence in `project/docs/VALIDATION_SPEC.md`.

Example:

```text
Verify that representative declarative clauses linearize with reviewed agreement and word order.
```

## Step 2 — Select the entrypoint

Choose one configured entrypoint.

Do not load a temporary undocumented module.

## Step 3 — Select the mode and requirement

Declare:

```text
applicable modes
required or optional
checkpoint association
```

## Step 4 — Choose evidence

Choose one or more:

```text
assertion
exact gold
required artifact
empty result
bounded count
```

## Step 5 — Write the smallest script

Add:

- scenario begin;
- load section;
- validation sections;
- scenario end;
- `q`.

## Step 6 — Run manually with the supported GF executable

Verify commands and output.

Manual execution is development evidence, not final registration proof.

## Step 7 — Run through GF Wordbench

Verify:

- process invocation;
- raw logs;
- marker extraction;
- normalization;
- assertions;
- timeout;
- result model.

## Step 8 — Create or review gold

Use the explicit gold-update process.

## Step 9 — Register the scenario

Update the active project registry and project interfile contract.

## Step 10 — Add automated tests

Add framework integration coverage or project release coverage as applicable.

---

# 50. Minimal complete template

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=<scenario-id>"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i <ENTRYPOINT>.gf
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=check"
<ONE_OR_MORE_BOUNDED_GF_COMMANDS>
ps "__GF_WORDBENCH_SECTION_END__ id=check"

ps "__GF_WORDBENCH_SCENARIO_END__ id=<scenario-id>"
q
```

Required replacement:

```text
<scenario-id>
<ENTRYPOINT>
<ONE_OR_MORE_BOUNDED_GF_COMMANDS>
```

---

# 51. Full representative template

```gf
ps "__GF_WORDBENCH_SCENARIO_BEGIN__ version=1 id=<scenario-id>"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=load"
i <ENTRYPOINT>.gf
pg -langs
ps "__GF_WORDBENCH_SECTION_END__ id=load"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=positive"
<POSITIVE_COMMAND_1>
<POSITIVE_COMMAND_2>
ps "__GF_WORDBENCH_SECTION_END__ id=positive"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=edge-cases"
<EDGE_COMMAND_1>
<EDGE_COMMAND_2>
ps "__GF_WORDBENCH_SECTION_END__ id=edge-cases"

ps "__GF_WORDBENCH_SECTION_BEGIN__ id=summary"
<SUMMARY_OR_INTROSPECTION_COMMAND>
ps "__GF_WORDBENCH_SECTION_END__ id=summary"

ps "__GF_WORDBENCH_SCENARIO_END__ id=<scenario-id>"
q
```

Do not retain unused sections.

---

# 52. Bad scenario examples

## 52.1 Missing markers

```gf
i GrammarX.gf
p "example"
q
```

Problem:

- completion cannot be proven;
- purpose is not segmented;
- language and category are implicit.

## 52.2 Metadata as invalid commands

```text
id: parse-basic
required: true
i GrammarX.gf
```

Problem:

- metadata is not GF syntax;
- unrecognized lines may be skipped;
- registration is hidden in the wrong file.

## 52.3 Unbounded generation

```gf
gt | l
```

Problem:

- default category and limits are implicit;
- output can become excessive;
- exact gold is unstable across grammar growth.

## 52.4 Operating-system escape

```gf
! dir
```

Problem:

- platform-specific;
- unsafe;
- outside validation scope.

## 52.5 Random exact gold

```gf
gr -cat=Cl -number=100 | l
```

Problem:

- random result;
- large output;
- unsuitable for exact regression gold.

## 52.6 Hidden state dependency

```gf
r
p "example"
```

Problem:

- reload depends on previous import history;
- fresh-process behavior is undefined.

## 52.7 Writing project gold

```gf
l ExampleTree | wf -file="project/validation/gold/example.gold"
```

Problem:

- ordinary validation mutates accepted baseline;
- artifact ownership is violated.

---

# 53. Refactoring scenarios

A compatible scenario refactor may:

- improve marker placement;
- split one section into clearer sections;
- move long inputs into a registered input file;
- replace repeated commands with a local macro;
- improve explicit flags;
- remove irrelevant output;
- reduce runtime while preserving validation coverage.

A potentially breaking scenario change includes:

- changing entrypoint;
- changing category;
- changing language;
- changing input set;
- changing accepted ambiguity;
- changing output order;
- changing normalization dependence;
- adding or removing golded commands;
- changing required markers;
- changing required/optional status;
- changing applicable modes.

Breaking changes require coordinated review of:

```text
scenario
registry
validation specification
gold
project interfile contract
coverage matrix
release criteria
```

---

# 54. Splitting a scenario

Split a scenario when:

- sections validate unrelated contracts;
- one section is optional and another is required;
- one section needs a much longer timeout;
- one section is deterministic and another random;
- one section needs gold and another does not;
- failures are difficult to localize;
- different checkpoints need different subsets.

Do not split only to make files artificially small.

---

# 55. Combining scenarios

Combine scenarios only when:

- they share one validation purpose;
- they require the same entrypoint;
- they use the same mode applicability;
- they have compatible timeout and evidence needs;
- one reviewed gold remains understandable;
- combined failure localization remains clear.

Do not combine solely to reduce process startup time.

Correctness and diagnosis take priority.

---

# 56. Scenario coverage

The active project should map each required contract to at least one proof.

Possible proofs:

```text
direct compile
checkpoint compile
entrypoint compile
scenario assertion
gold comparison
PGF artifact
manual review when automation is impossible
```

A scenario should not duplicate a direct compile test without adding runtime or linguistic evidence.

Coverage belongs in:

```text
project/docs/TEST_COVERAGE_MATRIX.md
```

---

# 57. Framework tests for scenarios

Framework tests should cover:

```text
valid marker protocol
missing scenario begin
missing scenario end
duplicate markers
mismatched section IDs
nested section rejection
GF zero exit with missing marker
nonzero exit with raw evidence
stdout marker
stderr diagnostic
timeout
cancellation
UTF-8 scenario
CRLF input
path containing spaces
normalization
exact gold match
gold mismatch
missing required gold
optional scenario failure
required scenario failure
output truncation
prohibited command detection
fresh process per scenario
scenario order determinism
```

Integration tests with real GF should use a small neutral fixture grammar.

---

# 58. Project-level tests

Each required active-project scenario should be proven by at least one project validation test or release run.

Project checks should verify:

- script exists;
- ID matches registry;
- entrypoint exists;
- inputs exist;
- gold exists when required;
- markers use correct ID;
- final command is `q`;
- no forbidden system command exists;
- scenario is applicable to at least one mode;
- required scenario is covered by release validation.

---

# 59. Automated linting

Recommended command:

```text
gf-wordbench scenarios lint
```

The linter should detect:

1. filename and ID mismatch;
2. invalid scenario ID;
3. missing begin marker;
4. missing end marker;
5. missing final `q`;
6. duplicate section ID;
7. nested sections;
8. unresolved placeholders;
9. absolute paths;
10. parent traversal;
11. forbidden system commands;
12. unbounded generation;
13. missing explicit `-lang` where required by policy;
14. missing explicit `-cat` for strict parse/generation scenarios;
15. unregistered input;
16. missing required gold;
17. scenario absent from project registry;
18. registry entry without script;
19. non-UTF-8 content;
20. inconsistent newline policy.

Strict mode:

```text
gf-wordbench scenarios lint --strict
```

Strict mode may also flag:

- broad scenarios with too many purposes;
- excessive command count;
- reliance on defaults;
- random commands in golded scenarios;
- `wf`, `eh`, or `r`;
- unsupported commands for the configured GF version;
- duplicate linguistic examples across scenarios.

---

# 60. Release checklist for one scenario

```text
[ ] Stable scenario ID
[ ] Filename matches ID
[ ] One primary purpose
[ ] Registered entrypoint
[ ] Applicable modes declared
[ ] Required/optional status declared
[ ] Fresh-process compatible
[ ] Scenario begin marker
[ ] Unique ordered sections
[ ] Scenario end marker
[ ] Final q command
[ ] Explicit language flags
[ ] Explicit category flags where relevant
[ ] Bounded generation and output
[ ] Finite timeout
[ ] No operating-system commands
[ ] No unauthorized file writes
[ ] Inputs registered
[ ] Assertions sufficient
[ ] Gold reviewed when required
[ ] Raw output preserved
[ ] Normalization reviewed
[ ] Integration test passes
[ ] Coverage matrix updated
[ ] Project interfile contract updated
```

---

# 61. Authoring decision guide

Use direct compilation instead of a scenario when the question is:

```text
Does this module compile?
```

Use a load scenario when the question is:

```text
Can the entrypoint be loaded in a fresh GF shell?
```

Use linearization when the question is:

```text
Does this reviewed tree produce the accepted string?
```

Use parsing when the question is:

```text
Does this reviewed string produce the accepted tree set?
```

Use round trip when the question is:

```text
Does the grammar preserve or canonicalize this reviewed example coherently?
```

Use morphology when the question is:

```text
What analyses does the grammar assign to these reviewed words?
```

Use bounded generation when the question is:

```text
Can a small controlled region of the abstract syntax linearize without failure?
```

Use `pg -missing` when the question is:

```text
Which abstract functions still lack linearization?
```

Use source or operation introspection only when the project contract concerns retained source interfaces.

---

# 62. Final authoring contract

A final GF Wordbench scenario must be:

```text
native to GF
project-owned
registered
single-purpose
fresh-process safe
explicit
bounded
deterministic where regression-tested
machine-marked
asserted
evidence-preserving
non-destructive
version-compatible
reviewable
```

The final invariant is:

> The `.gfs` file tells GF what to execute; the project registry tells GF Wordbench why it executes; markers prove how far execution progressed; assertions and gold determine whether the declared behavior passed.

No scenario may rely only on a process exit code, an implicit shell default, another scenario’s state, or a silently accepted output change.
