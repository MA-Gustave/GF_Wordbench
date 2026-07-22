# GF Wordbench Project — Interfile Contract Lock

**Document ID:** `GF-WB-PROJECT-INTERFILE-LOCK`  
**Status:** Normative template  
**Applies to:** One active GF language project  
**Template owner:** GF Wordbench  
**Project owner:** `<PROJECT_OWNER>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**Project root:** `<PROJECT_ROOT>`  
**Last reviewed:** `<YYYY-MM-DD>`  
**Contract version:** `1.0.0`

---

## 1. Purpose

This document prevents drift between files belonging to one active GF language project.

It locks the behavior expected at file boundaries:

- one GF module importing another;
- one module calling a public `oper`, `lin`, `lincat`, constructor or helper;
- concrete modules implementing abstract categories and functions;
- project configuration selecting source directories, entrypoints and checkpoints;
- validation scenarios loading modules and issuing GF commands;
- scenario outputs being compared with gold files;
- final entrypoints producing `.gfo` or `.pgf` artifacts;
- project documentation describing contracts implemented by source files.

This document does not lock internal implementation details that do not affect another file.

A module may be refactored internally when every externally visible promise remains compatible.

---

## 2. Core anti-drift rule

> A file that provides a symbol, structure, artifact or assumption and every file that consumes it form one coordinated change unit.

A contract-changing edit is complete only when all affected elements are updated together:

1. provider file;
2. all direct consumers;
3. downstream entrypoints;
4. project configuration;
5. validation scenarios;
6. gold expectations;
7. dependency map;
8. status ledger;
9. this contract lock;
10. release evidence, when applicable.

An isolated provider change is prohibited when another file depends on the changed contract.

An isolated consumer change is prohibited when the provider does not guarantee the requested behavior.

---

## 3. Normative language

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless an explicit reason is documented.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **PROVIDER**: file exposing a symbol, structure, artifact or behavior.
- **CONSUMER**: file importing, calling, loading, reading or validating the provider.
- **ENTRYPOINT**: top-level GF module used for final compilation, loading or PGF construction.
- **CHECKPOINT**: module whose successful validation is required at a defined development stage.
- **SCENARIO**: `.gfs` script executed by GF Wordbench.
- **GOLD**: reviewed expected output used for regression comparison.
- **LOCKED**: externally visible behavior that cannot change silently.
- **INTERNAL**: implementation detail not consumed by another file.

---

## 4. Scope

This lock covers relationships between:

- abstract GF modules;
- concrete GF modules;
- resource modules;
- interface and instance modules;
- morphology modules;
- syntax modules;
- lexicon modules;
- helper modules;
- extension modules;
- structural modules;
- language-level entrypoints;
- API-level entrypoints;
- `project.toml`;
- validation scenarios;
- validation inputs;
- gold outputs;
- expected `.gfo` and `.pgf` artifacts;
- language documentation that defines source-level contracts.

This lock does not govern:

- formatting;
- private local helpers that are not consumed elsewhere;
- comments that do not define a contract;
- local variable names;
- algorithmic changes preserving all external behavior;
- temporary debugging files excluded from the project.

An internal detail becomes locked when another file depends on it.

---

## 5. Project identity

Fill this section when initializing the language project.

| Field | Value |
|---|---|
| Language name | `<LANGUAGE_NAME>` |
| ISO or project code | `<LANGUAGE_CODE>` |
| GF suffix | `<GF_SUFFIX>` |
| Source directory | `<SOURCE_DIR>` |
| Abstract entrypoint | `<ABSTRACT_ENTRYPOINT>` |
| Concrete entrypoint | `<CONCRETE_ENTRYPOINT>` |
| Syntax entrypoint | `<SYNTAX_ENTRYPOINT>` |
| Language entrypoint | `<LANGUAGE_ENTRYPOINT>` |
| API entrypoint | `<API_ENTRYPOINT_OR_NONE>` |
| Expected PGF | `<EXPECTED_PGF>` |
| Validation specification | `project/docs/VALIDATION_SPEC.md` |
| Dependency map | `project/docs/MODULE_DEPENDENCY_MAP.md` |
| Status ledger | `project/docs/STATUS_LEDGER.md` |

---

## 6. Contract identifiers

Every contract MUST have a stable identifier.

Format:

```text
IFC-PROJ-<DOMAIN>-<NUMBER>
```

Recommended domains:

```text
CONFIG
MODULE
ABSTRACT
CONCRETE
LINC
MORPH
SYNTAX
LEXICON
HELPER
EXTEND
STRUCTURAL
SCENARIO
GOLD
ENTRY
PGF
DOC
```

Examples:

```text
IFC-PROJ-MODULE-001
IFC-PROJ-SCENARIO-003
IFC-PROJ-PGF-001
```

Identifiers MUST NOT be reused after retirement.

---

## 7. Required fields for every contract

Each contract entry MUST specify:

| Field | Requirement |
|---|---|
| Contract ID | Stable unique identifier |
| Status | `active`, `experimental`, `deprecated`, `blocked`, `retired` |
| Provider | File or artifact supplying the contract |
| Consumers | All known direct consumers |
| Public surface | Imported module, category, function, `oper`, field, artifact or schema |
| Request | What the consumer supplies or assumes |
| Response | What the provider guarantees |
| Type contract | GF type, lincat shape, file format or artifact type |
| Ordering contract | Required word, field or execution ordering |
| Side effects | Generated artifacts or state changes |
| Failure behavior | Expected compile, load or runtime failure modes |
| Locked invariants | Behavior that must remain stable |
| Forbidden behavior | Changes or dependencies that are prohibited |
| Validation evidence | Scenario, compile target, gold file or test |
| Documentation links | Related architecture, spec or decision |
| Last reviewed | Date or release |

---

## 8. Global project invariants

### 8.1 Single active language

The project represents one active language.

Framework source files MUST NOT contain project-specific language assumptions.

Language-specific assumptions belong in:

```text
project/project.toml
project/docs/
project/validation/
language source files
```

### 8.2 Explicit module ownership

Every public symbol SHOULD have one clear owner.

Duplicate public helpers with the same purpose SHOULD NOT exist across multiple modules unless the difference is documented.

### 8.3 No hidden lincat dependency

A consumer MUST NOT depend on an undocumented record field, table shape or parameter value.

Any cross-module use of a lincat field MUST be documented in:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

and referenced by a contract entry in this file.

### 8.4 No silent flattening

Structured values such as `NP`, `AP`, `CN`, `VP`, `Cl`, `Prep`, `Pron` or language-specific records MUST NOT be flattened to `Str` solely to satisfy a local implementation unless the architecture explicitly permits it.

A flattening decision affecting consumers is a breaking contract change.

### 8.5 Import direction discipline

Imports MUST follow the project architecture.

Lower-level modules MUST NOT import higher-level entrypoints.

Expected direction:

```text
morphology/resources
    → category implementations
    → syntax/structural/extend
    → grammar/syntax/language entrypoints
    → API/PGF entrypoint
```

Circular imports are prohibited.

### 8.6 Deterministic validation

Given the same sources, GF version, configuration and scenario inputs, validation results SHOULD be deterministic.

Generated output used for gold comparison MUST be bounded and normalized.

### 8.7 No undocumented fallback

Fallback implementations MUST be registered in:

```text
project/docs/STATUS_LEDGER.md
```

with status such as:

```text
temporary
fallback
warning
blocked
```

A fallback MUST NOT be presented as a final implementation without an explicit decision.

### 8.8 Evidence preservation

Every locked contract MUST have at least one validation proof:

- direct module compilation;
- entrypoint compilation;
- `.gfs` scenario;
- gold comparison;
- generated artifact;
- documented manual inspection, only when automation is impossible.

### 8.9 Consumer completeness

When a provider changes, all consumers listed in this document and in the dependency map MUST be reviewed.

A contract is not updated until downstream entrypoints have also been validated.

---

## 9. Project configuration contracts

## IFC-PROJ-CONFIG-001 — `project.toml` to GF Wordbench

**Status:** Active

**Provider**

```text
project/project.toml
```

**Consumer**

```text
GF Wordbench project configuration loader
```

**Required project fields**

```text
project.id
project.name
project.language_code
project.source_dir
project.source_glob
project.entrypoints
project.checkpoints
toolchain.gf_path_parts
validation.required_scenarios
validation.optional_scenarios
release.required_entrypoints
release.expected_artifacts
```

**Locked invariants**

- Relative paths resolve from the project root.
- The source directory identifies the active language sources.
- Entrypoints and checkpoints are ordered deterministically.
- Scenario identifiers are unique.
- Required scenarios cannot be silently skipped.
- Expected artifacts use project-relative or run-relative paths.
- Language-specific values are not duplicated in framework defaults.
- Unknown required keys produce a configuration error.
- Optional keys have documented defaults.

**Forbidden behavior**

- UI state MUST NOT override mandatory release gates.
- A scenario file MUST NOT select a different language project implicitly.
- The project loader MUST NOT infer entrypoints from filename conventions when entrypoints are explicitly configured.

**Validation evidence**

```text
project configuration validation
quick-mode startup
checkpoint-mode startup
release-mode startup
```

---

## IFC-PROJ-CONFIG-002 — Project configuration to GF path

**Status:** Active

**Provider**

```text
project/project.toml
```

**Consumers**

```text
module compiler
scenario runner
PGF builder
```

**Response**

A GF `--path` value containing all required source and RGL directories.

**Locked invariants**

- Path ordering is deterministic.
- The active language source directory is included exactly once.
- Required RGL paths are included.
- Nonexistent required paths fail before compilation.
- Path separators are normalized for the host platform.
- Compiler and scenario runner use equivalent GF path semantics.

---

## 10. Abstract-to-concrete contracts

## IFC-PROJ-ABSTRACT-001 — Abstract categories to concrete lincats

**Status:** `<active|experimental>`

**Provider**

```text
<ABSTRACT_CATEGORY_MODULE>.gf
```

**Consumers**

```text
<CONCRETE_CATEGORY_MODULE>.gf
<OTHER_CONSUMERS>
```

**Public surface**

```text
cat <CATEGORY_1> ;
cat <CATEGORY_2> ;
```

**Response**

Each abstract category is implemented by a concrete `lincat`.

**Type contract**

```gf
lincat <CATEGORY_1> = <LOCKED_TYPE_OR_RECORD_SHAPE> ;
lincat <CATEGORY_2> = <LOCKED_TYPE_OR_RECORD_SHAPE> ;
```

**Locked invariants**

- Every required abstract category has exactly one concrete implementation per concrete syntax.
- Record fields used by another module are documented.
- Parameter domains used across modules are documented.
- A lincat shape change is treated as a breaking change.
- Concrete consumers compile after any lincat change.
- Category structure is not flattened without an architecture decision.

**Validation evidence**

```text
<CONCRETE_CATEGORY_MODULE>.gf compiles
<SYNTAX_ENTRYPOINT> compiles
<LANGUAGE_ENTRYPOINT> compiles
<SCENARIO_ID>
```

---

## IFC-PROJ-ABSTRACT-002 — Abstract functions to concrete linearizations

**Status:** `<active|experimental>`

**Provider**

```text
<ABSTRACT_FUNCTION_MODULE>.gf
```

**Consumer**

```text
<CONCRETE_FUNCTION_MODULE>.gf
```

**Public surface**

```gf
fun <FUNCTION_NAME> : <GF_TYPE> ;
```

**Response**

```gf
lin <FUNCTION_NAME> = <IMPLEMENTATION> ;
```

**Locked invariants**

- Every required abstract function has a concrete linearization.
- The linearization preserves the declared category structure.
- Missing functions are detected by compilation or `pg -missing`.
- Placeholder linearizations are registered in the status ledger.
- Constructor argument order matches the abstract signature.

---

## 11. Module-to-module contracts

Duplicate this section for every important provider/consumer relationship.

## IFC-PROJ-MODULE-001 — `<CONSUMER_MODULE>` to `<PROVIDER_MODULE>`

**Status:** `<active|experimental|blocked>`

**Provider**

```text
<SOURCE_DIR>/<PROVIDER_MODULE>.gf
```

**Consumers**

```text
<SOURCE_DIR>/<CONSUMER_MODULE>.gf
<SOURCE_DIR>/<SECOND_CONSUMER_OR_REMOVE>.gf
```

**Import contract**

```gf
<CONSUMER_MODULE> imports/opens <PROVIDER_MODULE>
```

**Public surface**

```gf
oper <PUBLIC_HELPER> : <GF_TYPE> ;
lin  <PUBLIC_LINEARIZATION> = ... ;
```

**Request**

The consumer supplies:

```text
<ARGUMENTS_OR_ASSUMPTIONS>
```

**Response**

The provider guarantees:

```text
<RETURN_VALUE_OR_STRUCTURE>
```

**Type contract**

```gf
<PUBLIC_HELPER> : <FULL_GF_TYPE>
```

**Ordering contract**

```text
<WORD_ORDER_OR_FIELD_ORDER_REQUIREMENT>
```

**Locked invariants**

- The public symbol remains available under the documented name.
- The GF type remains compatible.
- Required record fields remain present.
- Number, gender, case, person, tense or agreement behavior remains compatible.
- The consumer does not access undocumented private helpers.
- The provider does not import the consumer.
- Error or fallback behavior is documented.

**Forbidden behavior**

- Renaming without updating all consumers.
- Type widening or narrowing without coordinated validation.
- Replacing a structured value with raw `Str` without approval.
- Moving the symbol to another provider without updating the dependency map and this lock.
- Introducing a reverse import.

**Failure behavior**

```text
<EXPECTED_COMPILE_OR_RUNTIME_FAILURES>
```

**Validation evidence**

```text
direct compile: <PROVIDER_MODULE>.gf
consumer compile: <CONSUMER_MODULE>.gf
entrypoint compile: <ENTRYPOINT>.gf
scenario: <SCENARIO_ID>
gold: project/validation/gold/<SCENARIO_ID>.gold
```

**Documentation**

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/DECISION_LOG.md
```

**Last reviewed**

```text
<YYYY-MM-DD>
```

---

## 12. Morphology contracts

## IFC-PROJ-MORPH-001 — Morphology provider to grammatical consumers

**Status:** `<active|experimental>`

**Provider**

```text
<SOURCE_DIR>/<MORPHOLOGY_MODULE>.gf
```

**Consumers**

```text
<SOURCE_DIR>/<NOUN_MODULE>.gf
<SOURCE_DIR>/<VERB_MODULE>.gf
<SOURCE_DIR>/<ADJECTIVE_MODULE>.gf
<SOURCE_DIR>/<PARADIGMS_MODULE>.gf
```

**Public surface**

List every public paradigm, table, parameter and constructor used outside the morphology module.

```gf
param <PARAMETER_NAME> = ... ;
oper <PARADIGM_NAME> : <GF_TYPE> ;
```

**Locked invariants**

- Inflection tables cover every documented parameter combination.
- Table domains consumed elsewhere do not change silently.
- Orthographic normalization is applied consistently.
- Stem-selection behavior is documented.
- Defective or invariant forms are explicit.
- Runtime string matching is used only where approved.
- Morphological constructors return structures compatible with downstream lincats.

**Validation evidence**

```text
morphology compile
paradigm scenario
generation scenario
gold output
```

---

## 13. Syntax and constructor contracts

## IFC-PROJ-SYNTAX-001 — Syntax constructors to category implementations

**Status:** `<active|experimental>`

**Provider**

```text
<SOURCE_DIR>/<SYNTAX_OR_STRUCTURAL_MODULE>.gf
```

**Consumers**

```text
<SOURCE_DIR>/<GRAMMAR_MODULE>.gf
<SOURCE_DIR>/<EXTEND_MODULE>.gf
<SOURCE_DIR>/<LANGUAGE_ENTRYPOINT>.gf
```

**Locked invariants**

- Constructor argument order matches the abstract API.
- Agreement features are propagated explicitly.
- Word-order decisions are stable and documented.
- Complement selection remains compatible.
- Slash and extraction behavior is not approximated silently.
- Polarity, tense, anteriority and mood handling follow the language specification.
- A constructor marked temporary remains visible in the status ledger.

**Validation evidence**

```text
constructor-specific linearization scenarios
parse scenarios
round-trip scenarios where applicable
entrypoint compilation
```

---

## 14. Helper contracts

## IFC-PROJ-HELPER-001 — Public helper registry

**Status:** `<active|experimental>`

**Provider**

```text
<SOURCE_DIR>/<HELPER_MODULE>.gf
```

**Consumers**

```text
<LIST_ALL_CONSUMERS>
```

**Registry**

| Helper | GF type | Consumers | Stability | Purpose |
|---|---|---|---|---|
| `<HELPER>` | `<TYPE>` | `<MODULES>` | `<stable|temporary>` | `<PURPOSE>` |

**Locked invariants**

- Every cross-module helper is listed.
- Private helpers remain private.
- Duplicate helpers are consolidated or explicitly distinguished.
- A helper type change triggers review of all consumers.
- Temporary helpers include an exit condition.

---

## 15. Extension and inheritance contracts

## IFC-PROJ-EXTEND-001 — Extension module to inherited framework

**Status:** `<active|experimental|blocked>`

**Provider**

```text
<SOURCE_DIR>/<EXTEND_MODULE>.gf
```

**External provider**

```text
<GF_OR_RGL_PARENT_MODULE>
```

**Consumers**

```text
<SOURCE_DIR>/<GRAMMAR_OR_LANGUAGE_ENTRYPOINT>.gf
```

**Locked invariants**

- Inherited functions remain inherited unless an override is justified.
- Overrides are listed explicitly.
- Subtractions are listed explicitly.
- Local overrides preserve abstract signatures.
- An override does not duplicate behavior already supplied correctly upstream.
- Temporary overrides are recorded in the status ledger.
- Changes to inheritance policy update the override matrix when one exists.

**Override registry**

| Symbol | Action | Provider | Local reason | Status | Validation |
|---|---|---|---|---|---|
| `<SYMBOL>` | `inherit/override/subtract` | `<MODULE>` | `<REASON>` | `<STATUS>` | `<SCENARIO>` |

---

## 16. Structural module contracts

## IFC-PROJ-STRUCTURAL-001 — Structural lexicon to grammar consumers

**Status:** `<active|experimental>`

**Provider**

```text
<SOURCE_DIR>/<STRUCTURAL_MODULE>.gf
```

**Consumers**

```text
<LIST_CONSUMERS>
```

**Locked invariants**

- Structural words expose the expected grammatical category.
- Prepositions retain required case or complement behavior.
- Pronouns retain person, number, gender and agreement fields.
- Determiners retain definiteness and agreement behavior.
- Conjunctions retain coordination structure.
- Placeholder structural entries are marked clearly.
- Consumer modules do not reconstruct structural entries independently.

---

## 17. Lexicon contracts

## IFC-PROJ-LEXICON-001 — Lexicon provider to language entrypoint

**Status:** `<active|experimental>`

**Provider**

```text
<SOURCE_DIR>/<LEXICON_MODULE>.gf
```

**Consumers**

```text
<SOURCE_DIR>/<LANGUAGE_ENTRYPOINT>.gf
<SCENARIOS>
```

**Locked invariants**

- Lexical entries use approved paradigms.
- Duplicate abstract identifiers are prohibited.
- Orthography follows the project policy.
- Required lexical categories are complete for release.
- Temporary lexical entries are distinguishable.
- Lexicon changes affecting gold output require reviewed gold updates.

---

## 18. Entrypoint contracts

## IFC-PROJ-ENTRY-001 — Concrete entrypoint to final grammar

**Status:** Active

**Provider**

```text
<SOURCE_DIR>/<CONCRETE_ENTRYPOINT>.gf
```

**Consumers**

```text
GF compiler
GF scenario runner
PGF builder
release workflow
```

**Locked invariants**

- The module imports every required concrete component.
- The module name matches project configuration.
- It compiles from a clean artifact directory.
- It does not depend on undeclared local paths.
- It is loadable by required scenarios.
- Missing linearizations are surfaced before release.
- It produces expected `.gfo` output.

---

## IFC-PROJ-ENTRY-002 — Language/API entrypoint to PGF builder

**Status:** `<active|not-applicable>`

**Provider**

```text
<SOURCE_DIR>/<LANGUAGE_OR_API_ENTRYPOINT>.gf
```

**Consumer**

```text
GF PGF build stage
```

**Response**

```text
<EXPECTED_PGF>
```

**Locked invariants**

- The configured build command targets the documented entrypoint.
- The PGF is created in the configured artifact directory.
- The PGF contains the required concrete language.
- Required functions are available.
- Build success requires both process success and artifact existence.
- Artifact naming is stable unless the persisted schema and release docs are updated.

---

## 19. Scenario contracts

## IFC-PROJ-SCENARIO-001 — Scenario registry

**Status:** Active

**Provider**

```text
project/project.toml
project/validation/scenarios/
```

**Consumer**

```text
GF Wordbench scenario runner
```

**Scenario registry**

| Scenario ID | Script | Required | Mode | Gold | Purpose |
|---|---|---:|---|---|---|
| `load` | `load.gfs` | Yes | checkpoint/release | optional | Load the main grammar |
| `missing` | `missing.gfs` | Yes | release | `missing.gold` | Detect missing linearizations |
| `linearize` | `linearize.gfs` | Yes | checkpoint/release | `linearize.gold` | Validate representative trees |
| `parse` | `parse.gfs` | `<Yes/No>` | release | `parse.gold` | Validate representative phrases |
| `generation` | `generation.gfs` | No | diagnostic/release | optional | Bounded generation checks |

Replace or extend this registry for the active language.

**Locked invariants**

- Scenario IDs are unique.
- Required scenarios exist.
- Each scenario loads only documented entrypoints.
- Scenario commands remain compatible with the supported GF version.
- Scenarios terminate explicitly when required.
- Scenario output includes stable section markers.
- Normal execution does not modify gold files.
- Scenario failures remain distinguishable from compilation failures.

---

## IFC-PROJ-SCENARIO-002 — Scenario to entrypoint

**Status:** Active

**Provider**

```text
project/validation/scenarios/<SCENARIO>.gfs
```

**Consumer**

```text
<SOURCE_DIR>/<ENTRYPOINT>.gf
```

**Request**

The scenario imports or loads:

```text
<ENTRYPOINT>
```

and executes:

```text
<GF_COMMANDS>
```

**Response**

```text
<EXPECTED_SECTIONS_AND_OUTPUT>
```

**Locked invariants**

- The scenario references the configured entrypoint.
- Required commands produce all expected markers.
- A missing marker is a failure.
- Unsupported commands are not accepted as success.
- Scenario input files are versioned with the project.
- Output normalization does not remove linguistic content.

---

## 20. Gold-file contracts

## IFC-PROJ-GOLD-001 — Scenario output to reviewed gold

**Status:** Active

**Provider**

```text
project/validation/gold/<SCENARIO>.gold
```

**Consumers**

```text
scenario comparison stage
release gate
```

**Locked invariants**

- Gold files contain normalized expected output.
- Gold files are reviewed source artifacts.
- Gold files are never rewritten during ordinary validation.
- Gold updates require an explicit command or manual review.
- Platform-specific noise may be normalized.
- Linguistically meaningful output must remain.
- A missing required gold file is a failure.
- Every gold update is associated with a source or specification change.

**Gold update checklist**

```text
[ ] Source change is intentional
[ ] New output is linguistically correct
[ ] Scenario still tests the intended contract
[ ] Unstable noise has not leaked into the gold
[ ] Related documentation is updated
[ ] Release impact is reviewed
```

---

## 21. Validation-input contracts

## IFC-PROJ-INPUT-001 — Input data to scenarios

**Status:** `<active|not-applicable>`

**Provider**

```text
project/validation/inputs/<INPUT_FILE>
```

**Consumers**

```text
<SCENARIO_FILES>
```

**Locked invariants**

- Input encoding is UTF-8 unless documented otherwise.
- Line ordering is stable when it affects output.
- Blank-line semantics are documented.
- Comments use a documented syntax.
- Each input has a declared purpose.
- Removed inputs are removed from all consumers.
- Inputs used for release are version-controlled.

---

## 22. Artifact contracts

## IFC-PROJ-PGF-001 — Release entrypoint to PGF artifact

**Status:** `<active|not-applicable>`

**Provider**

```text
<LANGUAGE_OR_API_ENTRYPOINT>.gf
```

**Consumer**

```text
release workflow
```

**Expected artifact**

```text
<EXPECTED_PGF>
```

**Locked invariants**

- Artifact existence is verified.
- Artifact path is declared in `project.toml`.
- Build command and GF path are recorded.
- The artifact is built from the current source fingerprint.
- Required scenarios pass against the same source state.
- Stale artifacts are not accepted.
- Release reports reference the artifact hash.

---

## IFC-PROJ-ARTIFACT-002 — Module compilation to `.gfo`

**Status:** Active

**Provider**

```text
GF compiler
```

**Consumers**

```text
downstream module compilation
entrypoint compilation
diagnostic tooling
```

**Locked invariants**

- `.gfo` artifacts are generated outside canonical source files where configured.
- Stale `.gfo` files do not mask source failures.
- Clean release validation can rebuild from scratch.
- Source files are never overwritten by artifact cleanup.
- Artifact retention policy is documented.

---

## 23. Documentation contracts

## IFC-PROJ-DOC-001 — Architecture documentation to source layout

**Status:** Active

**Provider**

```text
project/docs/LANGUAGE_ARCHITECTURE.md
```

**Consumers**

```text
source modules
dependency map
validation specification
maintainers
AI-assisted development
```

**Locked invariants**

- Every major source layer is documented.
- Entry modules match the current source tree.
- Module responsibility descriptions remain accurate.
- Architectural changes update both source and documentation.
- Historical designs are not presented as current targets.

---

## IFC-PROJ-DOC-002 — Dependency map to actual imports

**Status:** Active

**Provider**

```text
project/docs/MODULE_DEPENDENCY_MAP.md
```

**Consumers**

```text
classifier review
maintenance workflow
contract review
AI handoff
```

**Locked invariants**

- Direct imports match source reality.
- Entry-point dependency chains are current.
- Removed modules are removed from the map.
- Newly introduced provider/consumer relationships are added.
- The dependency map and this lock do not contradict one another.

---

## IFC-PROJ-DOC-003 — Validation specification to scenarios

**Status:** Active

**Provider**

```text
project/docs/VALIDATION_SPEC.md
```

**Consumers**

```text
project/project.toml
project/validation/scenarios/
project/validation/gold/
release workflow
```

**Locked invariants**

- Every required scenario has a documented purpose.
- Every release criterion has executable evidence where possible.
- Scenario removals require specification updates.
- A project cannot be declared complete when required criteria remain unproven.
- Manual criteria identify owner, method and evidence location.

---

## IFC-PROJ-DOC-004 — Status ledger to temporary implementations

**Status:** Active

**Provider**

```text
project/docs/STATUS_LEDGER.md
```

**Consumers**

```text
source maintainers
release workflow
known issues
AI handoff
```

**Locked invariants**

- Temporary, fallback, blocked and warning states are registered.
- Resolved entries retain a resolution record.
- A release-blocking entry cannot be ignored silently.
- Source comments and ledger entries do not contradict one another.
- Every temporary implementation has a next action or exit condition.

---

## 24. Forbidden dependency directions

The project MUST define its allowed dependency direction in `LANGUAGE_ARCHITECTURE.md`.

Default prohibited directions:

```text
morphology → language entrypoint
resource module → grammar entrypoint
category implementation → API entrypoint
helper module → direct consumer that already imports the helper
lower layer → higher orchestration layer
scenario → undocumented local source path
gold file → source generation logic
```

Default expected directions:

```text
resource/morphology
    → category implementations
    → syntax/structural/extend
    → grammar/syntax entrypoints
    → language/API entrypoint
    → PGF
```

Any exception MUST be documented as a contract.

---

## 25. Drift indicators

The following observations indicate probable interfile drift:

- a consumer calls a symbol absent from the provider;
- a provider changes a GF type without updating consumers;
- a lincat field is used but not documented;
- a module imports a higher-level entrypoint;
- the dependency map differs from actual imports;
- a scenario loads a renamed or obsolete module;
- `project.toml` lists an entrypoint that no longer exists;
- a required scenario has no script;
- a required gold file is missing;
- a gold file changes without an intentional source change;
- an expected `.pgf` name differs between configuration and release scripts;
- a temporary fallback is absent from the status ledger;
- two modules provide competing helpers with the same role;
- a structured category is flattened locally to bypass a type contract;
- an override duplicates inherited behavior;
- a scenario passes only because an unsupported GF command was ignored;
- direct module compilation passes but the documented consumer fails;
- a source module moved without updating documentation and validation paths;
- a release artifact was produced from stale `.gfo` files.

Detected drift MUST be resolved by restoring the documented contract or changing the contract deliberately.

---

## 26. Change classification

### 26.1 Internal compatible change

Examples:

- local helper refactor;
- performance improvement;
- comment correction;
- internal table reorganization preserving public behavior.

Required action:

```text
run direct provider validation
run affected consumer validation
no contract-version change required
```

### 26.2 Compatible contract extension

Examples:

- new optional helper;
- new optional record field unused by existing consumers;
- new optional scenario;
- new lexical entry.

Required action:

```text
update provider
update relevant documentation
add validation evidence
review consumers
```

### 26.3 Breaking contract change

Examples:

- rename or remove a public symbol;
- change a public GF type;
- change a lincat record shape;
- alter required word order;
- move ownership to another module;
- rename an entrypoint;
- change a scenario output contract;
- rename a gold file;
- change expected PGF name.

Required action:

1. identify all consumers;
2. update provider and consumers together;
3. update dependency map;
4. update scenarios;
5. update gold files deliberately;
6. update status and decision logs;
7. update this lock;
8. execute checkpoint and release validation;
9. record migration notes.

---

## 27. Contract-change workflow

Every contract-changing change set MUST include:

```text
[ ] Contract ID identified
[ ] Provider updated
[ ] All direct consumers reviewed
[ ] Downstream entrypoints validated
[ ] project.toml reviewed
[ ] Dependency map updated
[ ] Category/lincat contract updated
[ ] Scenarios updated
[ ] Gold files reviewed
[ ] Status ledger updated
[ ] Decision log updated when architectural
[ ] This lock updated
[ ] Quick validation passed
[ ] Checkpoint validation passed
[ ] Release validation passed when release-facing
```

Recommended change note:

```text
Contract:
Provider:
Consumers:
Previous behavior:
New behavior:
Reason:
Compatibility:
Scenarios:
Gold impact:
Release impact:
Evidence:
```

---

## 28. Project contract registry

Maintain this table as contracts are added.

| Contract ID | Provider | Consumers | Status | Primary validation |
|---|---|---|---|---|
| IFC-PROJ-CONFIG-001 | `project.toml` | project loader | Active | config validation |
| IFC-PROJ-CONFIG-002 | `project.toml` | compiler/scenario runner | Active | environment probe |
| IFC-PROJ-ABSTRACT-001 | `<ABSTRACT_CATEGORY_MODULE>` | `<CONCRETE_CATEGORY_MODULE>` | `<status>` | concrete compile |
| IFC-PROJ-ABSTRACT-002 | `<ABSTRACT_FUNCTION_MODULE>` | `<CONCRETE_FUNCTION_MODULE>` | `<status>` | `pg -missing` |
| IFC-PROJ-MODULE-001 | `<PROVIDER_MODULE>` | `<CONSUMER_MODULE>` | `<status>` | consumer compile |
| IFC-PROJ-MORPH-001 | `<MORPHOLOGY_MODULE>` | morphology consumers | `<status>` | morphology scenario |
| IFC-PROJ-SYNTAX-001 | `<SYNTAX_MODULE>` | grammar entrypoint | `<status>` | syntax scenario |
| IFC-PROJ-HELPER-001 | `<HELPER_MODULE>` | registered consumers | `<status>` | consumer compile |
| IFC-PROJ-EXTEND-001 | `<EXTEND_MODULE>` | language entrypoint | `<status>` | extend scenarios |
| IFC-PROJ-STRUCTURAL-001 | `<STRUCTURAL_MODULE>` | grammar consumers | `<status>` | structural scenario |
| IFC-PROJ-LEXICON-001 | `<LEXICON_MODULE>` | language entrypoint | `<status>` | lexical scenario |
| IFC-PROJ-ENTRY-001 | `<CONCRETE_ENTRYPOINT>` | compiler/scenarios | Active | entrypoint compile |
| IFC-PROJ-ENTRY-002 | `<LANGUAGE_ENTRYPOINT>` | PGF builder | `<status>` | PGF build |
| IFC-PROJ-SCENARIO-001 | scenario registry | scenario runner | Active | scenario discovery |
| IFC-PROJ-SCENARIO-002 | `<SCENARIO>.gfs` | `<ENTRYPOINT>` | `<status>` | scenario run |
| IFC-PROJ-GOLD-001 | `<SCENARIO>.gold` | comparator | Active | gold comparison |
| IFC-PROJ-INPUT-001 | `<INPUT_FILE>` | scenarios | `<status>` | scenario run |
| IFC-PROJ-PGF-001 | `<ENTRYPOINT>` | release workflow | `<status>` | PGF build |
| IFC-PROJ-DOC-001 | architecture doc | source layout | Active | documentation review |
| IFC-PROJ-DOC-002 | dependency map | maintainers | Active | import review |
| IFC-PROJ-DOC-003 | validation spec | scenarios/release | Active | release review |
| IFC-PROJ-DOC-004 | status ledger | maintainers/release | Active | ledger review |

---

## 29. Compact contract template

Copy this section for each additional contract.

```markdown
## IFC-PROJ-<DOMAIN>-<NUMBER> — <Contract name>

**Status:** Active | Experimental | Deprecated | Blocked | Retired

**Provider**

`<path>`

**Consumers**

- `<path>`
- `<path>`

**Public surface**

`<symbol, GF type, record shape, artifact or configuration field>`

**Request**

- `<input or assumption>`

**Response**

- `<guaranteed output or behavior>`

**Type contract**

```gf
<GF TYPE OR Lincat SHAPE>
```

**Ordering contract**

`<word order, argument order, field order or execution order>`

**Side effects**

- `<artifact or none>`

**Failure behavior**

- `<compile, load, runtime or comparison failure>`

**Locked invariants**

- `<invariant>`
- `<invariant>`

**Forbidden behavior**

- `<prohibition>`
- `<prohibition>`

**Validation evidence**

- Direct compile: `<module>`
- Consumer compile: `<module>`
- Entrypoint compile: `<entrypoint>`
- Scenario: `<scenario>`
- Gold: `<gold>`
- Artifact: `<artifact>`

**Documentation**

- `<related document>`

**Last reviewed**

`<YYYY-MM-DD>`
```

---

## 30. Initialization checklist

When creating a new language project from this template:

```text
[ ] Replace every required placeholder
[ ] Delete non-applicable example contracts
[ ] Fill the project identity table
[ ] Register project configuration fields
[ ] Register entrypoints and checkpoints
[ ] Document abstract-to-concrete relationships
[ ] Document shared lincat fields
[ ] Document cross-module helpers
[ ] Register scenarios and gold files
[ ] Document the expected PGF
[ ] Align the dependency map
[ ] Align the validation specification
[ ] Align the status ledger
[ ] Execute initial baseline validation
[ ] Record the baseline run ID
```

The file MUST NOT remain filled with unresolved required placeholders after project initialization.

---

## 31. Final enforcement rule

A GF module owns the promises it makes to its consumers.

A consumer may depend only on documented promises.

A scenario owns the validation behavior it declares.

A gold file owns the reviewed expected output.

Project configuration owns the active project identity, entrypoints and gates.

Therefore:

> No cross-file contract may be modified through an isolated file edit.

Every contract change must be coordinated, validated, documented and reviewable as one complete project change.
