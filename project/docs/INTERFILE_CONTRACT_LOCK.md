# GF Wordbench — Project Interfile Contract Lock

**Document ID:** `GF-WB-PROJECT-INTERFILE-LOCK`  
**Status:** Normative  
**Scope:** Active GF language project only  
**Applies to:** GF modules, project configuration, scenarios, inputs, gold files, generated GF artifacts, and project documentation  
**Does not govern:** Internal Python framework contracts  
**Framework counterpart:** `docs/INTERFILE_CONTRACT_LOCK.md`  
**Project owner:** `<maintainer or team>`  
**Active language:** `<language name>`  
**Language identifier:** `<language id>`  
**GF module suffix:** `<module suffix, for example Sqi>`  
**Last reviewed:** `<YYYY-MM-DD or release>`  

---

## 1. Purpose

This document prevents drift between the files that make up the active GF language project.

The project is not considered correct only because each file is internally valid. The project is correct when the files agree about:

- which module provides each category, function, operation, parameter, lincat, helper, paradigm, constructor, and entrypoint;
- which module imports and consumes each provider;
- which structures are preserved across module boundaries;
- which scenario loads which grammar;
- which inputs belong to which scenario;
- which gold file represents the accepted result;
- which final modules must produce which `.gfo` and `.pgf` artifacts;
- which project documents define the authoritative design and validation rules.

This file locks those relationships.

A module may change internally when its public contract remains compatible.

A contract between files must never change implicitly.

---

## 2. Core anti-drift rule

> Any change to what one project file requests from another, or what another project file promises in response, must be treated as one coordinated change.

A contract change is complete only when all affected elements have been updated together:

1. the provider file;
2. every consumer file;
3. related GF interfaces or instances;
4. dependent scenarios;
5. related input files;
6. related gold files;
7. project configuration;
8. project documentation;
9. validation evidence;
10. this contract lock.

A single-file edit is not sufficient when the contract crosses a file boundary.

---

## 3. Normative terms

The following terms are normative:

- **MUST**: mandatory;
- **MUST NOT**: prohibited;
- **SHOULD**: expected unless a documented exception exists;
- **SHOULD NOT**: normally prohibited;
- **MAY**: optional;
- **LOCKED**: part of the interfile contract;
- **PROVIDER**: file that supplies a symbol, structure, artifact, or behavior;
- **CONSUMER**: file that imports, invokes, loads, interprets, or compares the provider;
- **ENTRYPOINT**: top-level GF module used for compilation, loading, packaging, or release validation;
- **CHECKPOINT**: module whose successful validation proves a development layer is coherent;
- **SCENARIO**: `.gfs` file executed by GF Wordbench;
- **GOLD**: reviewed expected output associated with a scenario;
- **PROJECT ROOT**: root directory declared in `project/project.toml`;
- **SOURCE ROOT**: directory containing the active language GF sources.

---

## 4. Scope

This lock governs relationships between:

- abstract GF modules;
- concrete GF modules;
- resource modules;
- interface and instance modules;
- incomplete concrete modules;
- structural and paradigm modules;
- helper and support modules;
- extension modules;
- top-level grammar modules;
- syntax or API modules;
- `project/project.toml`;
- `.gfs` scenarios;
- scenario inputs;
- `.gold` files;
- `.gfo` and `.pgf` artifacts;
- project validation documents;
- project ledgers and decision records.

This lock does not govern:

- private implementation details that no other file consumes;
- local variable names;
- local `oper` definitions not imported or assumed elsewhere;
- comments that do not define a contract;
- Python framework behavior;
- generated runtime logs;
- temporary development files excluded by project configuration.

An internal detail becomes contractual as soon as another file depends on it.

---

## 5. Separation from the framework lock

This document owns project-level relationships such as:

```text
GF module → GF module
scenario → grammar entrypoint
scenario → input data
scenario → gold output
project.toml → active project files
entrypoint → generated PGF
project document → project implementation
```

The following relationships belong to the framework lock instead:

```text
Python module → Python module
CLI/GUI → bootstrap
audit core → compiler
audit core → scanner
report writer → result model
GF Wordbench → external process
```

No project-specific contract should be duplicated in the framework lock.

---

## 6. Project identity lock

The active project MUST have one authoritative identity.

### 6.1 Authoritative source

```text
project/project.toml
```

### 6.2 Locked identity fields

The project configuration MUST define or resolve:

```text
project id
display name
language name
module suffix
source root
entrypoints
checkpoints
required scenarios
optional scenarios
release targets
```

### 6.3 Identity invariants

- One GF Wordbench copy MUST represent one active language project.
- The active language identity MUST NOT be inferred from old output directories.
- The active language identity MUST NOT be taken from GUI state.
- Framework defaults MUST NOT override explicit project identity.
- Module suffixes used in scenarios and documents MUST agree with the project configuration.
- Renaming the language identifier or module suffix is a breaking project migration.
- Old-language names MUST be removed from active project paths, scenarios, gold files, and project documentation.

---

## 7. Contract identifiers

Every locked relationship SHOULD have a stable identifier.

Format:

```text
PIFC-<DOMAIN>-<NUMBER>
```

Recommended domains:

```text
CONFIG
MODULE
LINCAT
HELPER
ENTRY
SCENARIO
GOLD
ARTIFACT
DOC
RELEASE
```

Examples:

```text
PIFC-CONFIG-001
PIFC-MODULE-004
PIFC-SCENARIO-002
PIFC-ARTIFACT-001
```

Identifiers MUST NOT be reused for unrelated contracts.

Retired contracts remain listed with status `retired`.

---

## 8. Required fields for every project contract

Each contract entry MUST define:

| Field | Meaning |
|---|---|
| Contract ID | Stable project contract identifier |
| Status | `active`, `experimental`, `deprecated`, `blocked`, or `retired` |
| Provider | File supplying the contract |
| Consumer | File or files relying on the contract |
| Provided element | Module, symbol, lincat, artifact, output, or rule |
| Request | What the consumer assumes or asks for |
| Response | What the provider guarantees |
| Invariants | Properties that must remain true |
| Allowed variation | Internal changes that do not break the contract |
| Breaking changes | Changes requiring coordinated migration |
| Validation | Compile, scenario, gold, or review evidence |
| Documentation owner | Document where design intent is explained |
| Last reviewed | Date or release |

---

## 9. Global project invariants

### 9.1 No hidden provider rule

A consumer MUST NOT rely on a symbol, field, constructor, or side effect that is not declared by the provider or documented in this lock.

### 9.2 No duplicate ownership rule

Each public project responsibility MUST have one authoritative provider.

Examples:

- one authoritative noun morphology provider;
- one authoritative verb morphology provider;
- one authoritative lincat definition per category layer;
- one authoritative helper implementation;
- one authoritative release entrypoint;
- one authoritative gold file per scenario variant.

Duplicated providers require an explicit selection rule.

### 9.3 Structural preservation rule

A category structure MUST NOT be flattened across a file boundary merely to simplify a consumer.

Examples of potentially structured values include:

```text
NP
CN
AP
VP
VPSlash
Prep
Pron
Cl
S
```

If a consumer requires fields of a structured lincat, the provider MUST preserve those fields or the contract must be deliberately redesigned.

### 9.4 No undocumented fallback rule

Temporary fallbacks, shallow constructors, string-based substitutes, disabled operations, or inherited placeholders MUST be recorded in:

```text
project/docs/STATUS_LEDGER.md
```

and referenced from the relevant contract.

### 9.5 Import direction rule

Import direction MUST reflect architecture.

Lower-level modules MUST NOT import top-level grammar modules merely to access a convenience symbol.

Expected direction:

```text
low-level morphology
→ category and syntax resources
→ structural modules
→ extensions
→ top-level grammar/API entrypoints
```

Circular import dependencies are prohibited.

### 9.6 Stable naming rule

The following names are contractual when referenced by another file:

- GF module names;
- public categories;
- public functions;
- public `oper` names;
- public `param` values;
- resource interfaces;
- instance names;
- scenario identifiers;
- gold filenames;
- release artifact names.

### 9.7 Explicit incomplete-state rule

An incomplete implementation MUST be distinguishable from a stable implementation.

Accepted states:

```text
stable
experimental
temporary
fallback
warning
blocked
disabled
retired
```

No consumer may treat `temporary`, `fallback`, `blocked`, or `disabled` as `stable` without an explicit contract exception.

---

## 10. Project architecture ownership map

Fill this table for the active language.

| Responsibility | Authoritative provider | Main consumers | Status |
|---|---|---|---|
| Abstract syntax | `<path>` | `<paths>` | `<status>` |
| Core categories | `<path>` | `<paths>` | `<status>` |
| Noun morphology | `<path>` | `<paths>` | `<status>` |
| Verb morphology | `<path>` | `<paths>` | `<status>` |
| Adjective morphology | `<path>` | `<paths>` | `<status>` |
| Pronouns | `<path>` | `<paths>` | `<status>` |
| Determiners | `<path>` | `<paths>` | `<status>` |
| Structural lexicon | `<path>` | `<paths>` | `<status>` |
| Sentence syntax | `<path>` | `<paths>` | `<status>` |
| Question syntax | `<path>` | `<paths>` | `<status>` |
| Relative syntax | `<path>` | `<paths>` | `<status>` |
| Coordination | `<path>` | `<paths>` | `<status>` |
| Extension layer | `<path>` | `<paths>` | `<status>` |
| Paradigm API | `<path>` | `<paths>` | `<status>` |
| Syntax API | `<path>` | `<paths>` | `<status>` |
| Grammar entrypoint | `<path>` | scenarios/release | `<status>` |
| Syntax entrypoint | `<path>` | scenarios/release | `<status>` |
| Final PGF target | `<path or module>` | release validation | `<status>` |

A responsibility without an authoritative provider is unresolved drift.

A responsibility with multiple providers must document the selection rule.

---

# 11. Configuration contracts

## PIFC-CONFIG-001 — `project.toml` to source tree

**Status:** Active

**Provider**

```text
project/project.toml
```

**Consumers**

```text
GF Wordbench project loader
validation pipeline
scenario runner
release builder
project documentation
```

**Request**

The consumers request:

- active source root;
- file glob;
- include and exclude rules;
- GF path components;
- entrypoint modules;
- checkpoints;
- scenario lists;
- release target.

**Response**

The configuration guarantees:

- every required path is project-relative or explicitly absolute;
- entrypoints identify existing or intentionally planned modules;
- scenario identifiers are unique;
- release targets are unambiguous;
- language-specific values are centralized.

**Locked invariants**

- The configured source root MUST match the real active-language source tree.
- Entry modules MUST not be duplicated with conflicting names.
- Required scenarios MUST exist before release validation.
- Optional scenarios MUST remain distinguishable from required scenarios.
- Relative paths MUST resolve from the documented project root.
- A renamed source directory requires updates to scenarios, documentation, and this lock.

**Breaking changes**

- renaming configuration keys;
- changing path resolution rules;
- changing entrypoint identity;
- changing scenario identifiers;
- changing required/optional status;
- changing release artifact names.

**Validation**

```text
configuration load test
project path validation
entrypoint existence check
scenario registry check
```

---

## PIFC-CONFIG-002 — `project.toml` to module suffix

**Status:** Active

**Provider**

```text
project/project.toml
```

**Consumers**

```text
GF module names
scenario scripts
gold filenames
project documentation
release artifact naming
```

**Locked invariants**

- The configured suffix MUST match the active language module family.
- Scenarios MUST load modules using the same suffix.
- Documentation examples for the active project MUST use the same suffix.
- A suffix migration MUST be atomic across the project.
- Historical names may remain only in migration records or archived evidence.

---

# 12. Module contracts

## PIFC-MODULE-001 — Abstract syntax to concrete syntax

**Status:** Active

**Provider**

```text
<abstract module path>
```

**Consumers**

```text
<concrete module paths>
```

**Provided elements**

- abstract categories;
- abstract functions;
- function types;
- inheritance relationships.

**Locked invariants**

- Every concrete implementation MUST match the abstract function type.
- Category names and function names are stable public identifiers.
- Removing or changing an abstract function is a breaking project change.
- Incomplete concrete modules MUST declare omissions explicitly.
- A scenario that expects a function MUST identify the abstract provider.

**Validation**

```text
GF compilation of concrete modules
pg -missing or equivalent missing-function inspection
release scenario
```

---

## PIFC-MODULE-002 — Category provider to syntax modules

**Status:** Active

**Provider**

```text
<Cat/Res or equivalent provider path>
```

**Consumers**

```text
<Noun, Verb, Sentence, Question, Relative, Structural, Extend modules>
```

**Provided elements**

- lincats;
- record fields;
- parameters;
- agreement dimensions;
- shared constructors;
- shared coercions.

**Locked invariants**

- Consumers MUST use declared fields only.
- Field meaning MUST remain stable across consumers.
- Agreement dimensions MUST not be silently removed.
- Parameter value changes require review of all pattern matches.
- A field rename is breaking.
- Adding a mandatory field requires coordinated constructor updates.
- Adding an optional or derivable field requires explicit initialization policy.

**Validation**

```text
compile all direct consumers
compile all entrypoints
run representative linearization scenarios
```

---

## PIFC-MODULE-003 — Morphology resource to paradigms

**Status:** Active

**Provider**

```text
<morphology resource path>
```

**Consumers**

```text
<paradigm modules>
<lexicon modules>
<structural modules>
```

**Provided elements**

- inflection tables;
- stem operations;
- agreement parameters;
- constructor helpers;
- irregular-form support.

**Locked invariants**

- Paradigm modules MUST not duplicate provider logic without justification.
- Public morphology helpers MUST document accepted inputs.
- Failed or partial paradigms MUST not masquerade as complete paradigms.
- String normalization rules MUST remain consistent.
- Runtime string matching or unsafe shallow patterns MUST be explicitly documented.
- Orthographic transformations shared by multiple modules MUST have one provider.

**Validation**

```text
morphology compile checkpoint
morphological analysis scenario
representative paradigm gold tests
```

---

## PIFC-MODULE-004 — Paradigms to lexicon

**Status:** Active

**Provider**

```text
<paradigm module path>
```

**Consumers**

```text
<lexicon and structural lexicon paths>
```

**Request**

Consumers request stable constructors such as:

```text
mkN
mkV
mkA
mkAdv
mkPrep
<language-specific constructors>
```

**Response**

The provider guarantees:

- documented arities;
- documented argument order;
- documented default behavior;
- documented irregular-form pathways;
- compatible result categories.

**Locked invariants**

- Constructor arity and argument order are locked.
- A constructor MUST return the documented category.
- A shallow constructor MUST be marked as temporary or fallback.
- Lexicon entries MUST not rely on undocumented default inflection.
- Constructor migration requires recompiling all lexical consumers.

---

## PIFC-MODULE-005 — Structural module to grammar entrypoints

**Status:** Active

**Provider**

```text
<Structural module path>
```

**Consumers**

```text
<Grammar entrypoint>
<Syntax entrypoint>
<API modules>
<scenarios>
```

**Provided elements**

- structural words;
- closed-class lexical items;
- conjunctions;
- prepositions;
- pronouns;
- auxiliaries;
- determiners;
- punctuation or language-specific structural forms.

**Locked invariants**

- Required structural symbols MUST be present before release.
- Disabled symbols MUST be listed in the status ledger.
- A symbol used by an entrypoint scenario is release-significant.
- Lock-bearing categories such as `Prep` MUST preserve required fields.
- Structural lexicon changes require targeted scenario updates.

---

## PIFC-MODULE-006 — Extension modules to extension coordinator

**Status:** Conditional

**Provider**

```text
<extension submodule paths>
```

**Consumer**

```text
<extension coordinator path>
```

**Locked invariants**

- The coordinator SHOULD remain thin.
- Family-specific logic SHOULD live in the designated provider module.
- The same family MUST NOT be implemented by multiple submodules.
- Inherited families MUST not be locally redefined without a recorded decision.
- Moving a family between files requires updating:
  - import lists;
  - inheritance/subtraction lists;
  - helper ownership;
  - override policy;
  - scenarios;
  - this lock.

**Validation**

```text
compile each extension submodule
compile coordinator
compile immediate importer
run family-level scenario
```

---

## PIFC-MODULE-007 — Interface to instance

**Status:** Conditional

**Provider**

```text
<interface module path>
```

**Consumer**

```text
<instance module path>
```

**Locked invariants**

- The instance MUST satisfy every required interface symbol.
- Interface symbol types are locked.
- A default or inherited implementation MUST be explicit.
- Removing an interface symbol requires migration of every instance.
- Adding an interface symbol requires all instances to be updated or a compatible default to exist.

---

# 13. Lincat and record contracts

## PIFC-LINCAT-001 — Category lincat ownership

**Status:** Active

For every important category, record one authoritative lincat provider.

| Category | Provider | Consumers | Required fields | Status |
|---|---|---|---|---|
| `N` | `<path>` | `<paths>` | `<fields>` | `<status>` |
| `CN` | `<path>` | `<paths>` | `<fields>` | `<status>` |
| `NP` | `<path>` | `<paths>` | `<fields>` | `<status>` |
| `Pron` | `<path>` | `<paths>` | `<fields>` | `<status>` |
| `A` | `<path>` | `<paths>` | `<fields>` | `<status>` |
| `AP` | `<path>` | `<paths>` | `<fields>` | `<status>` |
| `V` | `<path>` | `<paths>` | `<fields>` | `<status>` |
| `VP` | `<path>` | `<paths>` | `<fields>` | `<status>` |
| `VPSlash` | `<path>` | `<paths>` | `<fields>` | `<status>` |
| `Prep` | `<path>` | `<paths>` | `<fields>` | `<status>` |
| `Cl` | `<path>` | `<paths>` | `<fields>` | `<status>` |
| `S` | `<path>` | `<paths>` | `<fields>` | `<status>` |

**Locked invariants**

- A consumer MUST not assume undeclared fields.
- A provider MUST not remove a required field without updating all consumers.
- A structured lincat MUST not be replaced by `Str` without a breaking-contract decision.
- Lock fields and agreement fields are public when consumed elsewhere.
- Field semantics MUST be documented in:
  - `CATEGORY_AND_LINCAT_CONTRACT.md`, or
  - the relevant architecture/specification document.

---

## PIFC-LINCAT-002 — Agreement parameter contract

**Status:** Active

Record agreement parameters and their providers.

| Parameter | Provider | Consumers | Values | Stability |
|---|---|---|---|---|
| Number | `<path>` | `<paths>` | `<values>` | `<status>` |
| Gender | `<path>` | `<paths>` | `<values>` | `<status>` |
| Person | `<path>` | `<paths>` | `<values>` | `<status>` |
| Case | `<path>` | `<paths>` | `<values>` | `<status>` |
| Definiteness | `<path>` | `<paths>` | `<values>` | `<status>` |
| Tense | `<path>` | `<paths>` | `<values>` | `<status>` |
| Mood | `<path>` | `<paths>` | `<values>` | `<status>` |

**Locked invariants**

- Parameter values used in consumer pattern matches are contractual.
- Renaming or merging values requires updating all matches and tables.
- A new parameter dimension requires initialization in every constructor that produces the affected record.
- Default values MUST be documented.

---

# 14. Helper contracts

## PIFC-HELPER-001 — Shared helper ownership

**Status:** Active

Every helper used across files MUST have one owner.

| Helper | Provider | Consumers | Input contract | Output contract | Status |
|---|---|---|---|---|---|
| `<helper>` | `<path>` | `<paths>` | `<inputs>` | `<output>` | `<status>` |

**Locked invariants**

- A helper used by multiple files MUST not be copied into each consumer.
- Public helper names and signatures are locked.
- A helper MUST not silently change from structured output to `Str`.
- A helper marked temporary MUST have a removal or stabilization condition.
- Private helpers MUST not be imported by other modules.
- Helper ownership changes require coordinated import migration.

---

# 15. Entrypoint contracts

## PIFC-ENTRY-001 — Grammar entrypoint

**Status:** Active

**Provider**

```text
<Grammar<suffix>.gf or equivalent>
```

**Consumers**

```text
release builder
load scenarios
parse scenarios
linearization scenarios
external applications
```

**Response**

The entrypoint guarantees:

- it resolves the configured abstract/concrete grammar;
- it imports the required language modules;
- it is loadable by GF;
- it is eligible for final build;
- it represents the intended active-language grammar surface.

**Locked invariants**

- The configured grammar entrypoint name MUST match the GF module name.
- Required imports MUST be explicit or inherited through documented modules.
- Entry success MUST be validated independently from individual module success.
- Removing a module from the entrypoint requires architectural review.
- A release MUST not substitute another entrypoint silently.

---

## PIFC-ENTRY-002 — Syntax/API entrypoint

**Status:** Active when present

**Provider**

```text
<Syntax<suffix>.gf, Lang<suffix>.gf, API module, or equivalent>
```

**Consumers**

```text
application scenarios
smoke scenarios
external API consumers
release validation
```

**Locked invariants**

- The API surface MUST be documented.
- Public constructors expected by scenarios MUST remain available.
- The entrypoint MUST be validated after lower-level checkpoints.
- A successful grammar entrypoint does not automatically prove the API entrypoint succeeds.

---

## PIFC-ENTRY-003 — Release target

**Status:** Active

**Provider**

```text
configured release entrypoint(s)
```

**Consumer**

```text
GF release build
```

**Artifact**

```text
<expected PGF filename>
```

**Locked invariants**

- The expected PGF name MUST be explicit.
- Release build success MUST verify artifact existence.
- A stale PGF from an earlier run MUST not count as success.
- The artifact SHOULD be tied to the current source fingerprint.
- Release scenarios MUST run against the intended current artifact or source state.

---

# 16. Scenario contracts

## PIFC-SCENARIO-001 — Scenario registry to scenario files

**Status:** Active

**Provider**

```text
project/project.toml
```

**Consumers**

```text
project/validation/scenarios/*.gfs
GF Wordbench scenario runner
```

**Locked invariants**

- Every required scenario identifier MUST map to exactly one `.gfs` file.
- Optional scenarios MUST be marked explicitly.
- Scenario filenames SHOULD match scenario identifiers.
- Duplicate scenario identifiers are prohibited.
- Unregistered scenario files are not release evidence unless explicitly invoked.

---

## PIFC-SCENARIO-002 — Scenario to grammar entrypoint

**Status:** Active

For each scenario, record the loaded module.

| Scenario ID | Scenario file | Loaded entrypoint | Required | Purpose |
|---|---|---|---|---|
| `<id>` | `<path>.gfs` | `<module>` | `yes/no` | `<purpose>` |

**Locked invariants**

- The scenario MUST load the documented entrypoint.
- Loading a lower-level substitute is not equivalent to loading the final entrypoint.
- Scenario module names MUST track project suffix migrations.
- A required scenario that fails to load its entrypoint is a project failure.
- Entry module changes require scenario review.

---

## PIFC-SCENARIO-003 — Scenario to input data

**Status:** Active when external input files are used

| Scenario ID | Input file | Format | Ownership | Stability |
|---|---|---|---|---|
| `<id>` | `<path>` | `<format>` | `<owner>` | `<status>` |

**Locked invariants**

- Input files MUST use a documented encoding.
- Input line meaning MUST be documented.
- Scenario and input file versions MUST remain compatible.
- Removing or reordering inputs may invalidate gold output.
- Generated temporary inputs MUST not replace reviewed canonical inputs during release validation.

---

## PIFC-SCENARIO-004 — Scenario markers

**Status:** Active

Scenario output sections MUST use the marker format defined by GF Wordbench.

Recommended form:

```text
GF_WORDBENCH_BEGIN <scenario-id>:<section-id>
GF_WORDBENCH_END <scenario-id>:<section-id>
```

**Locked invariants**

- Section identifiers MUST be unique within the scenario.
- Every begin marker MUST have a matching end marker.
- Marker text MUST not depend on localized UI language.
- Gold normalization MUST preserve marker identity.
- Missing markers MUST produce a scenario error, not a pass.

---

# 17. Gold-file contracts

## PIFC-GOLD-001 — Scenario to gold file

**Status:** Active

| Scenario ID | Scenario file | Gold file | Normalization profile | Required |
|---|---|---|---|---|
| `<id>` | `<path>.gfs` | `<path>.gold` | `<profile>` | `yes/no` |

**Locked invariants**

- Every required gold-backed scenario MUST identify one gold file.
- A missing gold file MUST not be treated as an automatic pass.
- Normal validation MUST never rewrite a gold file.
- Gold updates require an explicit reviewed operation.
- Gold content MUST represent accepted semantic output.
- Unstable noise such as timestamps or absolute paths MAY be normalized.
- Linguistically meaningful output MUST not be normalized away.
- Scenario and gold filenames SHOULD share the same identifier.

---

## PIFC-GOLD-002 — Gold update procedure

**Status:** Active

A gold update is valid only when:

1. the implementation change is intentional;
2. raw old and new outputs have been reviewed;
3. the linguistic or architectural reason is documented;
4. the scenario still tests the intended behavior;
5. `VALIDATION_SPEC.md` is updated when acceptance criteria changed;
6. `DECISION_LOG.md` is updated for significant behavior changes;
7. this lock is updated if the contract changed.

A gold file MUST NOT be updated merely to make a failing test pass.

---

# 18. Artifact contracts

## PIFC-ARTIFACT-001 — GF source to `.gfo`

**Status:** Active

**Provider**

```text
GF compiler
```

**Source consumer relationship**

```text
<Module>.gf → <Module>.gfo
```

**Locked invariants**

- A `.gfo` is valid evidence only when produced from the current source state.
- Stale `.gfo` files MUST not mask source compilation failures.
- Output location MUST follow configured build paths.
- Release validation SHOULD isolate generated artifacts from source directories where practical.
- Artifact existence alone is insufficient; process success and current fingerprint are also required.

---

## PIFC-ARTIFACT-002 — Entrypoint to `.pgf`

**Status:** Active

**Provider**

```text
configured release entrypoint
```

**Artifact**

```text
<expected name>.pgf
```

**Locked invariants**

- The release PGF name is locked.
- The PGF MUST correspond to the configured entrypoint.
- The PGF MUST be produced during the current release run.
- Required release scenarios MUST reference the same intended grammar.
- Renaming the PGF requires updates to consumers, release scripts, documentation, and this lock.

---

## PIFC-ARTIFACT-003 — Project validation to evidence

**Status:** Active

Every release-significant validation MUST produce traceable evidence:

```text
command
working directory
GF version
source fingerprint
stdout
stderr
exit code
timeout state
artifact paths
scenario result
gold comparison result
```

No release claim may depend solely on console text that was not preserved.

---

# 19. Documentation contracts

## PIFC-DOC-001 — Architecture documentation to module ownership

**Status:** Active

**Provider**

```text
project/docs/LANGUAGE_ARCHITECTURE.md
```

**Consumers**

```text
module layout
dependency map
this lock
development decisions
```

**Locked invariants**

- The architecture document MUST identify the intended module layers.
- Module ownership in code MUST agree with documented ownership.
- A module extraction, merge, or responsibility transfer requires documentation updates.
- Temporary architecture MUST be labeled as temporary.

---

## PIFC-DOC-002 — Category contract to lincats

**Status:** Active

**Provider**

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

**Consumers**

```text
category provider modules
syntax modules
helpers
scenarios
this lock
```

**Locked invariants**

- Required fields and agreement dimensions MUST match implementation.
- A lincat migration requires coordinated code and documentation changes.
- The document MUST distinguish stable structure from experimental structure.

---

## PIFC-DOC-003 — Validation specification to scenarios

**Status:** Active

**Provider**

```text
project/docs/VALIDATION_SPEC.md
```

**Consumers**

```text
project.toml
scenario registry
scenario files
gold files
release checklist
```

**Locked invariants**

- Every required validation criterion MUST map to executable evidence.
- A required scenario MUST have a documented purpose.
- A gold file MUST correspond to a documented acceptance criterion.
- “Done” or “release-ready” MUST be defined by the validation specification, not by memory.

---

## PIFC-DOC-004 — Status ledger to temporary implementations

**Status:** Active

**Provider**

```text
project/docs/STATUS_LEDGER.md
```

**Consumers**

```text
temporary code
fallback code
blocked features
known warnings
release decisions
```

**Locked invariants**

- Every temporary or blocked contract MUST have a ledger entry.
- Every ledger entry MUST identify its provider and consumers.
- Resolved entries MUST record the evidence that closed them.
- A release exception MUST be explicit and reviewed.

---

## PIFC-DOC-005 — Decision log to breaking project changes

**Status:** Active

**Provider**

```text
project/docs/DECISION_LOG.md
```

**Consumers**

```text
architecture
module contracts
scenario acceptance
gold updates
release policy
```

**Locked invariants**

Significant decisions MUST be logged when they affect:

- module ownership;
- lincat structure;
- constructor behavior;
- inheritance or override policy;
- release entrypoints;
- scenario expectations;
- accepted known issues;
- gold output.

---

# 20. Release contracts

## PIFC-RELEASE-001 — Checkpoints to release entrypoints

**Status:** Active

**Providers**

```text
configured checkpoint modules
```

**Consumer**

```text
release validation
```

**Locked invariants**

- Every checkpoint MUST compile before final entrypoint validation.
- Checkpoint order SHOULD follow dependency order.
- A downstream checkpoint failure MUST not be misreported as an independent root failure.
- Skipping a required checkpoint requires an explicit release exception.

---

## PIFC-RELEASE-002 — Required scenarios to release status

**Status:** Active

**Providers**

```text
required scenario results
```

**Consumer**

```text
release decision
```

**Locked invariants**

- Every required scenario MUST pass.
- Optional scenarios may warn but MUST remain visible.
- A missing required scenario is a release failure.
- A scenario execution error is distinct from a semantic scenario failure.
- Gold mismatch is a release failure unless the gold is deliberately updated and reviewed.

---

## PIFC-RELEASE-003 — Known issues to release decision

**Status:** Active

**Provider**

```text
project/docs/KNOWN_ISSUES.md
project/docs/STATUS_LEDGER.md
```

**Consumer**

```text
release checklist
```

**Locked invariants**

- Accepted issues MUST be explicit.
- Each accepted issue MUST state whether it blocks release.
- Undocumented warnings MUST not be silently accepted.
- Blocked or disabled required functions prevent release unless the validation specification explicitly permits them.

---

# 21. Forbidden project dependency directions

The following dependency directions are normally prohibited:

```text
low-level morphology → final grammar entrypoint
resource module → syntax API
category provider → consumer-specific helper
scenario → undocumented temporary module
gold file → source code
project configuration → generated run output
release entrypoint → test-only module
```

The following directions are expected:

```text
abstract syntax → concrete syntax
resource/category provider → syntax modules
morphology → paradigms → lexicon
structural modules → grammar entrypoints
extension providers → extension coordinator
entrypoints → scenarios
scenario output → gold comparison
validation specification → scenario registry
```

Exceptions require a decision-log entry.

---

# 22. Drift indicators

The following observations indicate probable interfile drift:

- a module imports a symbol not documented as public;
- two modules claim ownership of the same helper or family;
- a consumer reads a record field not documented by the lincat provider;
- a provider changes a field without updating constructors;
- a scenario loads a module different from the configured entrypoint;
- a gold file has no registered scenario;
- a required scenario has no gold or explicit assertion strategy;
- a project document names a module that no longer exists;
- a scenario or document uses an old language suffix;
- an entrypoint compiles but a required lower checkpoint is omitted;
- a `.pgf` artifact name differs from project configuration;
- temporary fallback code has no ledger entry;
- a helper is copied into multiple modules;
- an inherited family is redefined locally without policy;
- a new warning is accepted without documentation;
- a gold file changes without a decision or validation-spec review;
- a module is moved without updating the dependency map;
- active-language files still reference the previous language.

Every detected drift must be resolved by either:

1. restoring the existing contract; or
2. changing the contract deliberately and updating all affected files.

---

# 23. Change classification

## 23.1 Internal compatible change

Examples:

- refactoring a private helper;
- improving an algorithm without changing output structure;
- optimizing a table;
- clarifying comments;
- adding a local test.

Requirements:

- existing contract remains true;
- affected validations still pass;
- no lock update required unless the contract description becomes clearer.

## 23.2 Compatible contract extension

Examples:

- adding an optional public helper;
- adding a new optional scenario;
- adding a derivable record field with a safe initialization policy;
- adding an optional entrypoint.

Requirements:

- provider updated;
- consumers reviewed;
- tests added;
- documentation updated;
- lock updated.

## 23.3 Breaking contract change

Examples:

- renaming a module;
- renaming a public symbol;
- changing constructor arity;
- changing a lincat field;
- changing parameter values;
- changing entrypoints;
- changing scenario IDs;
- changing gold normalization;
- moving ownership between modules;
- changing expected PGF name.

Requirements:

1. identify the contract ID;
2. document the reason;
3. list all providers and consumers;
4. update all affected files together;
5. update scenarios and gold files intentionally;
6. update project configuration;
7. update project documentation;
8. record the decision;
9. validate checkpoints and entrypoints;
10. update this lock.

---

# 24. Required change checklist

For every interfile change:

```text
[ ] Contract ID identified
[ ] Provider identified
[ ] All direct consumers identified
[ ] Downstream consumers reviewed
[ ] Imports updated
[ ] Public symbols/types reviewed
[ ] Lincat/record fields reviewed
[ ] Helper ownership reviewed
[ ] Project configuration reviewed
[ ] Scenarios reviewed
[ ] Input files reviewed
[ ] Gold files reviewed
[ ] Entry points reviewed
[ ] PGF artifact contract reviewed
[ ] Dependency map updated
[ ] Validation specification updated
[ ] Status ledger updated
[ ] Decision log updated when required
[ ] This lock updated
[ ] Checkpoint validation passed
[ ] Release-level validation passed when applicable
```

---

# 25. Contract tests and evidence

Project contract validation SHOULD include:

```text
project configuration validation
module existence validation
module-name/file-name consistency
entrypoint existence validation
checkpoint registry validation
scenario registry validation
scenario-to-gold mapping validation
duplicate helper ownership checks
old-language identifier scan
dependency-map consistency review
required documentation existence
GF compile checkpoints
GF load scenarios
pg -missing or equivalent
linearization scenarios
parse scenarios
bounded generation scenarios
gold comparisons
final PGF build
```

GF Wordbench SHOULD eventually provide:

```text
gf-wordbench project contracts check
```

The checker should detect at least:

- missing modules;
- duplicate scenario IDs;
- missing required scenarios;
- missing gold files;
- stale language identifiers;
- unregistered entrypoints;
- broken scenario-to-entrypoint mappings;
- missing project documents;
- undocumented temporary statuses;
- stale artifact names.

---

# 26. Project contract registry

Fill and maintain this registry.

| Contract ID | Relationship | Status | Validation |
|---|---|---|---|
| PIFC-CONFIG-001 | `project.toml` → source tree | Active | config validation |
| PIFC-CONFIG-002 | project identity → module suffix | Active | identifier scan |
| PIFC-MODULE-001 | abstract → concrete syntax | Active | compile / missing |
| PIFC-MODULE-002 | category provider → syntax modules | Active | checkpoint compile |
| PIFC-MODULE-003 | morphology → paradigms | Active | morphology scenarios |
| PIFC-MODULE-004 | paradigms → lexicon | Active | lexicon compile |
| PIFC-MODULE-005 | structural → entrypoints | Active | entrypoint compile |
| PIFC-MODULE-006 | extension providers → coordinator | Conditional | family scenarios |
| PIFC-MODULE-007 | interface → instance | Conditional | interface compile |
| PIFC-LINCAT-001 | categories → lincat consumers | Active | compile / contract review |
| PIFC-LINCAT-002 | parameters → pattern consumers | Active | compile / generation |
| PIFC-HELPER-001 | helper providers → consumers | Active | helper registry |
| PIFC-ENTRY-001 | grammar entrypoint → release/scenarios | Active | load / build |
| PIFC-ENTRY-002 | API entrypoint → application scenarios | Conditional | smoke scenarios |
| PIFC-ENTRY-003 | release entrypoint → PGF | Active | release build |
| PIFC-SCENARIO-001 | scenario registry → `.gfs` files | Active | registry check |
| PIFC-SCENARIO-002 | scenario → entrypoint | Active | scenario run |
| PIFC-SCENARIO-003 | scenario → input files | Conditional | input validation |
| PIFC-SCENARIO-004 | scenario → output markers | Active | marker check |
| PIFC-GOLD-001 | scenario → gold | Active | normalized comparison |
| PIFC-GOLD-002 | implementation change → gold update | Active | review checklist |
| PIFC-ARTIFACT-001 | `.gf` → `.gfo` | Active | current-run compile |
| PIFC-ARTIFACT-002 | entrypoint → `.pgf` | Active | release build |
| PIFC-ARTIFACT-003 | validation → evidence | Active | manifest/report |
| PIFC-DOC-001 | architecture doc → module ownership | Active | documentation review |
| PIFC-DOC-002 | category contract → lincats | Active | documentation review |
| PIFC-DOC-003 | validation spec → scenarios | Active | scenario coverage |
| PIFC-DOC-004 | status ledger → temporary code | Active | ledger review |
| PIFC-DOC-005 | decision log → breaking changes | Active | release review |
| PIFC-RELEASE-001 | checkpoints → release entrypoints | Active | checkpoint gate |
| PIFC-RELEASE-002 | required scenarios → release status | Active | release gate |
| PIFC-RELEASE-003 | known issues → release decision | Active | issue review |

---

# 27. Contract entry template

Use this template for every project-specific relationship.

```markdown
## PIFC-<DOMAIN>-<NUMBER> — <relationship>

**Status:** Active | Experimental | Deprecated | Blocked | Retired

**Provider**

`path/to/provider.gf`

**Consumers**

- `path/to/consumer.gf`
- `project/validation/scenarios/example.gfs`

**Provided element**

- module;
- symbol;
- lincat;
- helper;
- artifact;
- output.

**Request**

Describe what consumers require.

**Response**

Describe what the provider guarantees.

**Locked invariants**

- invariant;
- invariant.

**Allowed internal variation**

- compatible implementation changes.

**Breaking changes**

- changes requiring coordinated migration.

**Validation**

- compile checkpoint;
- scenario;
- gold;
- release build.

**Documentation**

- architecture document;
- lincat contract;
- status ledger;
- decision entry.

**Last reviewed**

`<YYYY-MM-DD or release>`
```

---

# 28. Final enforcement rule

A GF project is a network of contracts, not a collection of independent files.

A provider owns the promises it makes to consumers.

A consumer may depend only on documented promises.

A scenario owns a declared validation purpose.

A gold file owns reviewed expected output.

An entrypoint owns the project surface it exposes.

Therefore:

> No project-level contract may be changed through an isolated file edit.

Every interfile change must be coordinated, validated, documented, and reviewable as one complete project change.
