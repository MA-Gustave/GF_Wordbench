# Albanian Language Project Overview

**Document ID:** `GF-WB-PROJECT-LANGUAGE-OVERVIEW`  
**Status:** Active project overview with explicitly identified completion gaps  
**Applies to:** The active Albanian GF project represented by this GF Wordbench repository copy  
**Project ID:** `sqi`  
**Language name:** Albanian  
**Language code:** `sqi`  
**GF module suffix:** `Sqi`  
**Source root:** `lib/src/albanian`  
**Project identity authority:** `project/project.toml`  
**Architecture authority:** `project/docs/LANGUAGE_ARCHITECTURE.md`  
**Validation authority:** `project/docs/VALIDATION_SPEC.md`  
**Contract authority:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Status authority:** `project/docs/STATUS_LEDGER.md`  
**Last reviewed:** 2026-07-22

---

## 1. Purpose

This document provides the project-level overview of the Albanian implementation maintained in the active GF Wordbench project.

It defines:

- the project identity;
- the confirmed implementation scope;
- the source and module naming conventions;
- the intended relationship with the Grammatical Framework Resource Grammar Library;
- the current architectural layers visible in the source family;
- the linguistic domains the project is expected to cover;
- the boundaries between overview, detailed specifications and status tracking;
- the decisions that are already confirmed;
- the decisions that remain unverified and must not be invented;
- the conditions under which this overview may claim release completeness.

This document is intentionally conservative.

It describes only facts supported by the active project configuration, source naming, maintained contracts or preserved project evidence.

The core rule is:

> This overview may summarize the active Albanian project, but it must not convert an undocumented linguistic assumption into project policy.

---

## 2. Active project identity

The active language project is Albanian.

Canonical identity:

```text
Project ID:       sqi
Language name:    Albanian
Language code:    sqi
GF module suffix: Sqi
Source root:      lib/src/albanian
```

The project configuration is the authoritative owner of these values.

This document must be updated when the configuration changes.

A change to:

- project ID;
- language code;
- module suffix;
- source root;
- release entrypoint;

is a coordinated project migration, not a documentation-only edit.

---

## 3. Single-active-language rule

This repository copy represents one active language project.

For this copy, that language is Albanian.

Albanian-specific facts belong in:

```text
project/project.toml
project/docs/
project/validation/
lib/src/albanian/
```

They must not become hidden defaults in reusable framework code under:

```text
app/
tests/
docs/
templates/
```

Framework tests may retain explicitly labeled Albanian migration fixtures or historical compatibility examples, but they must not use Albanian as an implicit universal default.

---

## 4. Source-tree identity

The confirmed active-language source root is:

```text
lib/src/albanian
```

The source family uses the GF suffix:

```text
Sqi
```

Confirmed or historically exercised module names include:

```text
CatSqi
MorphoSqi
NounSqi
StructuralSqi
SymbolSqi
ExtendSqi
ExtendSqiScaffolding
GrammarSqi
LangSqi
AllSqi
```

These names establish a real source-family pattern.

They do not, by themselves, prove that every module is complete, current or release-ready.

The authoritative module inventory belongs in:

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/STATUS_LEDGER.md
```

---

## 5. Project objective

The project objective is to maintain an Albanian concrete language implementation and associated GF entrypoints that can be:

- compiled by GF;
- loaded through native GF scenarios;
- inspected for missing linearizations;
- exercised through parse and linearization scenarios;
- validated through deterministic project-owned evidence;
- built into the configured final `.pgf` artifact when release criteria require it.

The project is not complete merely because individual source files parse or compile in isolation.

Completion requires agreement between:

```text
source modules
module contracts
entrypoints
checkpoints
scenarios
gold files
release artifacts
project documentation
```

---

## 6. Relationship to GF and the RGL

GF remains the authoritative execution engine.

The Albanian project is expected to integrate with the GF Resource Grammar Library architecture through the project’s configured source paths and entrypoints.

GF Wordbench does not replace:

- GF source parsing;
- type checking;
- module loading;
- linearization;
- parsing;
- morphology execution;
- generation;
- PGF construction.

GF Wordbench provides:

- deterministic file selection;
- static supplementary scanning;
- native GF process execution;
- raw evidence capture;
- diagnostic parsing;
- direct/downstream classification;
- scenario execution;
- normalized comparison;
- project gold validation;
- report generation;
- artifact integrity checks.

---

## 7. Confirmed architectural layers

The source names and project contracts support the following high-level layer model.

```text
morphology and low-level resources
    → category and lincat providers
    → noun, verb and phrase-level syntax
    → structural vocabulary and symbols
    → extension layer
    → grammar entrypoint
    → language/API entrypoints
    → final PGF target
```

The confirmed module family suggests at least these responsibilities:

| Responsibility | Confirmed module family or evidence | Current interpretation |
|---|---|---|
| Category/lincat layer | `CatSqi` | Shared concrete category structures |
| Morphology layer | `MorphoSqi` | Low-level Albanian morphology and inflection support |
| Noun layer | `NounSqi` | Noun phrase and noun-related behavior |
| Structural vocabulary | `StructuralSqi` | Structural lexical and grammatical items |
| Symbol handling | `SymbolSqi` | Symbol/category support |
| Extension layer | `ExtendSqi`, `ExtendSqiScaffolding` | Extended constructors and incomplete/scaffolded extension work |
| Grammar assembly | `GrammarSqi` | Main grammar-level assembly |
| Language entrypoint | `LangSqi` | Top-level language module |
| Broad/final entrypoint | `AllSqi` | Broad aggregate or release-facing assembly |

This table is an overview, not a substitute for the dependency map.

Exact imports, public symbols and statuses must be recorded in the project architecture and interfile contract lock.

---

## 8. Entrypoint policy

The available project evidence identifies these top-level candidates:

```text
GrammarSqi
LangSqi
AllSqi
```

Their exact roles must be declared in `project/project.toml`.

The project must distinguish:

- grammar entrypoint;
- language entrypoint;
- API or syntax entrypoint;
- release/PGF entrypoint;
- checkpoint-only module.

A module must not be treated as the release entrypoint merely because its filename appears top-level.

The release entrypoint must be:

- explicitly configured;
- present in the source tree;
- loadable by required scenarios;
- validated after required checkpoints;
- linked to the expected current `.pgf` artifact.

---

## 9. Checkpoint policy

Checkpoints should represent meaningful dependency layers.

For the Albanian module family, candidate checkpoint responsibilities include:

```text
morphology
categories/lincats
noun and phrase syntax
structural vocabulary
extensions
grammar assembly
language entrypoint
final aggregate entrypoint
```

The authoritative checkpoint list and order belong in:

```text
project/project.toml
```

Checkpoint order must follow dependency order.

Alphabetical order is not sufficient.

A downstream entrypoint failure must not be presented as an independent root failure when a lower checkpoint already failed.

---

## 10. Linguistic coverage domains

The project is expected to document and validate, as applicable, the following Albanian domains:

### 10.1 Orthography and text representation

- supported writing system;
- canonical Unicode policy;
- capitalization;
- punctuation;
- apostrophes or other orthographic separators;
- token-boundary behavior;
- accepted spelling variants;
- input normalization policy.

### 10.2 Nominal morphology

- noun inflection;
- number;
- gender where represented;
- case distinctions;
- definiteness;
- irregular nouns;
- noun phrase agreement;
- form-table completeness.

### 10.3 Adjectival morphology

- adjective forms;
- agreement;
- attributive and predicative use;
- degree;
- irregularity;
- interaction with noun phrases.

### 10.4 Verbal morphology

- person;
- number;
- tense;
- mood;
- voice where represented;
- participles and non-finite forms;
- auxiliary behavior;
- irregular paradigms;
- negation interaction.

### 10.5 Pronouns and determiners

- personal pronouns;
- possessive forms;
- demonstratives;
- interrogatives;
- relative forms;
- determiners;
- agreement and case behavior.

### 10.6 Clause syntax

- declarative clauses;
- negation;
- questions;
- imperatives where supported;
- subordination;
- complement clauses;
- relative clauses;
- coordination;
- word order and clitic placement where represented.

### 10.7 Structural vocabulary

- prepositions;
- conjunctions;
- particles;
- auxiliaries;
- structural adverbs;
- grammaticalized lexical items;
- symbols.

### 10.8 Lexical coverage

- core closed classes;
- representative open-class paradigms;
- irregular high-frequency items;
- project-specific lexical extensions;
- release-required vocabulary.

Detailed linguistic rules belong in:

```text
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

---

## 11. Dialect policy

The available authoritative project records do not yet establish a reviewed dialect policy.

This document therefore does not assert that the implementation targets:

- one specific Albanian dialect;
- a particular regional variety;
- all dialects;
- one historical stage;
- one standardization profile.

Before release, the project must state explicitly:

```text
primary target variety
accepted variants
excluded variants
fallback policy
gold-output policy for variants
```

The decision belongs in:

```text
project/docs/LANGUAGE_OVERVIEW.md
project/docs/DECISION_LOG.md
project/docs/VALIDATION_SPEC.md
```

and, where it affects implementation contracts, in:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

---

## 12. Orthographic policy

The available authoritative records do not yet define a complete orthographic policy.

Before release, the project must document:

- canonical spelling source;
- character inventory;
- Unicode normalization policy;
- capitalization;
- punctuation;
- apostrophe/hyphen policy where applicable;
- accepted input variants;
- canonical output form;
- handling of nonstandard or historical spelling.

GF Wordbench normalization must not silently repair Albanian orthography.

Linguistic output must remain project-owned and exact.

---

## 13. Language code and suffix distinction

The project uses:

```text
language code: sqi
module suffix: Sqi
```

These are related but not interchangeable.

Use:

- `sqi` for the project/language identifier;
- `Sqi` for the GF module family suffix.

Do not:

- lowercase GF module names;
- use `Sqi` as a schema ID;
- use `sqi` as a replacement for configured module names;
- infer filenames solely from the language code when configuration is explicit.

---

## 14. Module naming policy

Active Albanian modules should follow the configured suffix consistently.

Examples:

```text
CatSqi.gf
MorphoSqi.gf
NounSqi.gf
GrammarSqi.gf
LangSqi.gf
AllSqi.gf
```

Contractual names include:

- module names;
- public categories;
- public functions;
- public operations;
- parameter values;
- scenario IDs;
- gold filenames;
- release artifact names.

Renaming one requires review of all consumers.

---

## 15. Incomplete and scaffolded implementation

The presence of a module named:

```text
ExtendSqiScaffolding.gf
```

is evidence that at least part of the extension layer has been represented as scaffolding or staged work.

Scaffolding must not be presented as stable implementation without review.

Every incomplete, temporary, fallback, warning, blocked or disabled state must be recorded in:

```text
project/docs/STATUS_LEDGER.md
```

The overview must not claim full language coverage while release-significant scaffolding remains unresolved.

---

## 16. Known historical diagnostic evidence

Preserved audit evidence has exercised or referenced failures involving modules such as:

```text
CatSqi
GrammarSqi
LangSqi
AllSqi
NounSqi
StructuralSqi
```

Examples of observed historical diagnostic themes include:

- missing or defaulted linearization types;
- internal GF generation failures;
- inflection-rule failures;
- downstream blocking from grammar-level failures.

These observations are historical evidence, not the current status authority.

Current status must come from:

```text
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
current GF Wordbench runs
```

Resolved historical failures must not remain described as current.

Unresolved failures must not disappear from the ledger.

---

## 17. Abstract-to-concrete relationship

The Albanian project implements concrete behavior against configured abstract GF interfaces.

The project must preserve:

- abstract category names;
- function names;
- function types;
- concrete `lincat` definitions;
- constructor arity;
- inherited interface obligations;
- missing-function visibility.

A concrete module that omits abstract functions must make those omissions visible through GF validation.

A default `{s : Str}` insertion or equivalent fallback must not be accepted silently when the real project contract requires richer structure.

---

## 18. Lincat policy

Shared `lincat` structures are project contracts.

Consumers must not depend on undocumented fields.

Relevant dimensions may include:

- string fields;
- agreement information;
- number;
- person;
- gender;
- case;
- definiteness;
- polarity;
- tense or anteriority;
- clitic or complement information;
- structural flags.

The exact shapes must be documented in:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

This overview does not lock field-level structures.

---

## 19. Morphology policy

`MorphoSqi` is the confirmed morphology-oriented module family.

The project should maintain one authoritative owner for:

- noun inflection;
- verb inflection;
- adjective inflection;
- stem operations;
- irregular forms;
- form-table construction;
- shared agreement parameters.

Paradigm and lexicon modules must consume documented morphology providers rather than duplicating logic without justification.

Failed or partial paradigms must remain distinguishable from complete paradigms.

---

## 20. Structural vocabulary policy

`StructuralSqi` is a confirmed structural module family.

The structural layer should own shared items such as:

- prepositions;
- pronouns;
- determiners;
- conjunctions;
- particles;
- auxiliaries;
- structural adverbs;
- other closed-class items.

Consumer modules must not reconstruct structural entries independently when a canonical provider exists.

Changes affecting linearization output require scenario and gold review.

---

## 21. Extension policy

`ExtendSqi` and `ExtendSqiScaffolding` indicate an extension layer.

The project must distinguish:

```text
stable extension
experimental extension
scaffolding
temporary fallback
disabled extension
retired extension
```

Extensions must not bypass lower-level category, morphology or syntax contracts.

An extension coordinator may depend on extension providers.

Lower-level providers must not import the final extension entrypoint merely for convenience.

---

## 22. Language/API assembly

`GrammarSqi`, `LangSqi` and `AllSqi` represent higher-level assembly candidates.

The project architecture must state:

- which module assembles the core grammar;
- which module exposes the language;
- which module exposes the broad API;
- which module is used for scenarios;
- which module is used for PGF;
- which modules are compatibility wrappers.

These roles must not be inferred independently by the compiler, scenario runner and release builder.

---

## 23. Validation objectives

The Albanian project must validate more than source-file syntax.

Required validation domains should include:

```text
project configuration
source inventory
module existence
checkpoint compilation
entrypoint loading
missing-function inspection
representative linearization
representative parsing
morphology
bounded generation where deterministic
gold comparison
final PGF build where required
artifact freshness and integrity
```

The exact required set belongs in:

```text
project/docs/VALIDATION_SPEC.md
```

---

## 24. Scenario baseline

A typical Albanian scenario registry may include:

```text
load
missing
linearize
parse
morphology
generation
```

The exact required/optional status must come from `project/project.toml`.

This overview does not activate a scenario by naming it.

Each active scenario must have:

- a registered ID;
- a `.gfs` file;
- a documented entrypoint;
- bounded execution;
- stable markers;
- an assertion strategy;
- a gold file where exact comparison is required.

---

## 25. Gold-output policy

Project gold files represent reviewed accepted Albanian output.

Canonical location:

```text
project/validation/gold/
```

Normal validation is read-only.

A gold update requires:

- current scenario execution;
- raw stdout/stderr review;
- normalization review;
- deterministic diff;
- linguistic or architectural approval;
- atomic write;
- version-control review.

Current output must never be accepted automatically merely because the implementation produced it.

---

## 26. Unicode and normalization

Albanian linguistic text must be preserved exactly unless the project explicitly defines a Unicode normalization policy.

GF Wordbench output normalization may remove only approved execution instability.

It must not:

- remove accents or diacritics;
- transliterate;
- case-fold;
- replace project punctuation;
- repair spelling;
- reorder linguistic variants without policy;
- collapse meaningful spaces.

The project’s Unicode and orthographic policy must be defined before release.

---

## 27. Determinism

Given the same:

```text
source files
project configuration
GF version
scenario inputs
normalization profile
```

the project should produce deterministic normalized validation evidence.

Sources of nondeterminism must be:

- eliminated;
- seeded and recorded;
- bounded;
- or validated through non-exact assertions.

Random generation must not be used for exact gold comparison without a proven deterministic contract.

---

## 28. Release target

The project must define one unambiguous final release target.

The target includes:

```text
release entrypoint
expected PGF name
required concrete language
source fingerprint
required checkpoints
required scenarios
required golds
known-issue policy
```

The available evidence identifies `GrammarSqi`, `LangSqi` and `AllSqi` as likely high-level modules, but the final release target must be selected explicitly in `project/project.toml`.

This document does not guess which candidate is final.

---

## 29. Release readiness

The Albanian project is release-ready only when:

```text
[ ] Project identity is complete
[ ] Dialect policy is explicit
[ ] Orthographic policy is explicit
[ ] Source inventory is current
[ ] Module ownership is documented
[ ] Shared lincats are documented
[ ] Morphology behavior is specified
[ ] Syntax behavior is specified
[ ] Checkpoints pass
[ ] Required scenarios pass
[ ] Required golds match
[ ] Missing functions satisfy policy
[ ] Release entrypoint is explicit
[ ] Current PGF is built and verified when required
[ ] Scaffolding and fallback states are resolved or explicitly accepted
[ ] No release-blocking ledger item remains
[ ] Manifest and release evidence verify
```

---

## 30. Current maturity statement

Based on the available project evidence, the Albanian project should be treated as an active integration and completion project rather than assumed release-complete.

Reasons include:

- project-specific lock material still requiring concrete population in available records;
- dialect policy not yet confirmed;
- orthographic policy not yet confirmed;
- final release entrypoint not proven by the available records;
- historical evidence of compilation and generation failures;
- presence of explicitly named scaffolding.

This statement must be revised when current authoritative project documents and release evidence establish a newer status.

---

## 31. Non-goals of this overview

This overview does not:

- define every Albanian grammatical rule;
- list every GF module;
- define exact lincat records;
- define exact paradigms;
- select the final entrypoint without configuration;
- declare unresolved scaffolding stable;
- approve gold output;
- claim dialect coverage;
- claim complete RGL parity;
- replace current GF execution evidence;
- replace the status ledger or known-issues file.

---

## 32. Project-specific decisions required before release

The project must resolve these decisions explicitly:

```text
1. Primary Albanian variety or standard target
2. Accepted dialectal variants
3. Canonical orthography
4. Unicode normalization policy
5. Canonical release entrypoint
6. Canonical PGF artifact name
7. Required checkpoint list and order
8. Required scenario list
9. Missing-function acceptance policy
10. Scaffolding retirement policy
11. Fallback acceptance policy
12. Gold variant policy
13. Supported GF versions
14. Release-blocking known issues
```

Each decision must have one owner and validation impact.

---

## 33. Evidence hierarchy

When sources disagree, use this order:

1. current `project/project.toml`;
2. current project interfile contract lock;
3. current source modules;
4. current language architecture and dependency map;
5. current validation specification;
6. current status ledger and known issues;
7. current successful GF Wordbench release evidence;
8. historical audit output;
9. examples and migration fixtures.

Historical GUI/application state is not project identity.

---

## 34. Change policy

Update this overview when any of these change:

- project identity;
- language code;
- module suffix;
- source root;
- target variety;
- orthographic policy;
- major coverage scope;
- top-level entrypoints;
- release target;
- supported GF versions;
- project maturity;
- accepted non-goals.

A module-internal refactor that preserves all public behavior may not require an overview update.

---

## 35. Anti-drift checks

The project should detect:

- non-`Sqi` active module suffixes;
- old-language identifiers;
- entrypoints absent from the source tree;
- modules named in documentation but missing;
- source modules absent from the dependency map;
- scenario scripts loading undocumented entrypoints;
- gold files without registered scenarios;
- unresolved placeholders;
- scaffolding not recorded in the status ledger;
- release claims contradicted by current evidence;
- dialect/orthographic assumptions embedded only in code comments.

---

## 36. Overview completion checklist

```text
[ ] Project ID matches project.toml
[ ] Language code matches project.toml
[ ] Module suffix matches source modules
[ ] Source root matches source tree
[ ] Module-family summary matches architecture
[ ] Dialect policy is explicit
[ ] Orthographic policy is explicit
[ ] Linguistic scope is explicit
[ ] Non-goals are explicit
[ ] Entrypoints are explicit
[ ] Release target is explicit
[ ] Scaffolding status is explicit
[ ] Validation scope is explicit
[ ] Supported GF versions are documented
[ ] Research evidence is linked
[ ] No unresolved placeholders remain
```

---

## 37. Related project documents

- `project/README.md`
- `project/project.toml`
- `project/docs/00_PROJECT_START_HERE.md`
- `project/docs/LANGUAGE_ARCHITECTURE.md`
- `project/docs/MODULE_DEPENDENCY_MAP.md`
- `project/docs/CATEGORY_AND_LINCAT_CONTRACT.md`
- `project/docs/MORPHOLOGY_SPEC.md`
- `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md`
- `project/docs/VALIDATION_SPEC.md`
- `project/docs/TEST_COVERAGE_MATRIX.md`
- `project/docs/STATUS_LEDGER.md`
- `project/docs/DECISION_LOG.md`
- `project/docs/KNOWN_ISSUES.md`
- `project/docs/RELEASE_CRITERIA.md`
- `project/docs/RESEARCH_EVIDENCE.md`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`

---

## 38. Related framework documents

- `docs/projects/PROJECT_MODEL.md`
- `docs/projects/CREATING_A_PROJECT.md`
- `docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md`
- `docs/gf/GF_COMPILATION.md`
- `docs/gf/GF_PGF_BUILD.md`
- `docs/gf/GF_VERSION_COMPATIBILITY.md`
- `docs/scenarios/SCENARIO_FORMAT.md`
- `docs/scenarios/GOLDEN_TESTS.md`
- `docs/validation/RELEASE_GATES.md`
- `docs/reference/TERMINOLOGY_REFERENCE.md`

---

## 39. Final enforcement rule

The active project is the Albanian `sqi` module family using the `Sqi` GF suffix under `lib/src/albanian`.

That identity is confirmed.

Detailed dialect, orthographic and release-target policies are not considered confirmed until they are represented by current authoritative project configuration and reviewed project documents.

Therefore:

> This overview must distinguish verified project facts from pending project decisions, and release documentation must never present an unresolved decision as implemented language policy.
