# Albanian (`Sqi`) — Language Architecture

**Document ID:** `GF-WB-PROJECT-LANGUAGE-ARCHITECTURE`  
**Status:** Normative active-project architecture  
**Project language:** Albanian  
**GF module suffix:** `Sqi`  
**Canonical source root:** `lib/src/albanian`  
**Primary configuration owner:** `project/project.toml`  
**Primary contract owner:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Architecture version:** `1.0`  
**Last reviewed:** 2026-07-22  

---

## 1. Purpose

This document defines the linguistic and GF-module architecture of the active Albanian project.

It establishes:

- the architectural layers;
- the direction of imports;
- the ownership of categories, parameters, lincats, morphology, syntax, structural vocabulary, lexicon, extensions, and entrypoints;
- the boundary between the abstract grammar and the Albanian concrete syntax;
- the role of the Resource Grammar Library;
- the rules for public helpers and record fields;
- the relationship between module checkpoints, scenarios, gold files, and release artifacts;
- the change process for architectural decisions;
- the minimum evidence required to claim that one layer is stable.

This document is project-specific.

Framework-wide Python architecture belongs under:

```text
docs/
```

Albanian GF implementation decisions belong under:

```text
project/
```

---

## 2. Architectural source of truth

The architecture is distributed across explicit owners.

| Concern | Authoritative source |
|---|---|
| Project identity | `project/project.toml` |
| Exact source inventory | `lib/src/albanian/*.gf` |
| Module dependency graph | `project/docs/MODULE_DEPENDENCY_MAP.md` |
| Category and lincat shapes | `project/docs/CATEGORY_AND_LINCAT_CONTRACT.md` |
| Morphology requirements | `project/docs/MORPHOLOGY_SPEC.md` |
| Syntax and constructor rules | `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| Cross-file contracts | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Validation coverage | `project/docs/VALIDATION_SPEC.md` |
| Temporary or incomplete work | `project/docs/STATUS_LEDGER.md` |
| Architectural decisions | `project/docs/DECISION_LOG.md` |
| Release requirements | `project/docs/RELEASE_CRITERIA.md` |
| Known limitations | `project/docs/KNOWN_ISSUES.md` |

This document provides the architectural model connecting those sources.

It must not duplicate every GF type or every import edge.

---

## 3. Active project identity

Canonical active-language identity:

```text
Language: Albanian
Language code / GF suffix: Sqi
Source root: lib/src/albanian
```

Known top-level or representative project modules include:

```text
GrammarSqi.gf
LangSqi.gf
AllSqi.gf
NounSqi.gf
AdverbSqi.gf
ExtendSqi.gf
```

The complete module inventory must be obtained from the source tree and `project.toml`.

A module name mentioned in this document is contractual only when it exists in the source tree or is registered as planned/blocked in `STATUS_LEDGER.md`.

---

## 4. Architectural principles

### 4.1 One active language

This GF Wordbench copy represents one active language project: Albanian.

The framework must remain language-neutral.

The Albanian project may use:

```text
Albanian
Sqi
GrammarSqi
NounSqi
LangSqi
```

inside project-owned files.

Those identifiers must not leak into reusable framework defaults or templates.

### 4.2 GF is authoritative

GF owns:

- module parsing;
- type checking;
- import resolution;
- concrete syntax compilation;
- PGF generation;
- parsing;
- linearization;
- generation;
- missing-linearization inspection.

Project documentation describes intended architecture.

It does not replace GF validation.

### 4.3 Explicit ownership

Every public category, function, parameter, `oper`, lincat field, paradigm, structural entry, and entrypoint must have one clear provider.

A consumer may depend only on documented provider guarantees.

### 4.4 Structured representations

Core syntactic categories must not be flattened to `Str` merely to make one module compile.

Structured values such as:

```text
NP
CN
AP
VP
Cl
S
QS
RS
Pron
Det
Prep
Conj
```

must retain the fields required by their consumers.

Any deliberate flattening is an architectural decision and a breaking project-contract change.

### 4.5 Stable import direction

Imports flow upward from low-level resources to public entrypoints.

```text
parameters and low-level resources
        ↓
morphology
        ↓
paradigms and category implementations
        ↓
syntax modules
        ↓
structural and extension layers
        ↓
grammar, language, syntax, and API entrypoints
        ↓
PGF and scenarios
```

Reverse imports are prohibited.

### 4.6 Evidence before stability

A module or layer is stable only when its required evidence exists.

Evidence may include:

- direct compilation;
- consumer compilation;
- entrypoint compilation;
- missing-linearization inspection;
- scenario execution;
- normalized gold comparison;
- final PGF construction.

---

## 5. Layer model

The Albanian grammar is organized conceptually into the following layers.

```text
Layer 0 — abstract API and RGL interfaces
Layer 1 — parameters and low-level resources
Layer 2 — morphology
Layer 3 — category implementations and paradigms
Layer 4 — core syntax
Layer 5 — structural vocabulary and closed classes
Layer 6 — extensions and language-specific constructions
Layer 7 — lexicon
Layer 8 — public entrypoints
Layer 9 — validation and release artifacts
```

A physical module may participate in more than one nearby layer.

Its authoritative ownership must still remain clear.

---

# 6. Layer 0 — abstract API and RGL interfaces

## 6.1 Purpose

This layer defines the abstract functions and categories that the Albanian concrete syntax implements.

Typical upstream abstract modules may include RGL grammar interfaces and project-specific abstract extensions.

The Albanian project must not redefine an upstream abstract function under a conflicting identity.

## 6.2 Responsibilities

This layer owns:

- abstract categories;
- abstract constructors;
- function signatures;
- constructor argument order;
- API-level compatibility.

## 6.3 Concrete obligation

Every required abstract function exposed by the selected entrypoint must have an Albanian linearization.

Missing functions must be visible through:

- GF compilation;
- `pg -missing` or equivalent;
- required release scenarios.

## 6.4 Change impact

Changing an abstract signature requires coordinated review of:

```text
concrete linearizations
syntax constructors
extensions
lexicon
scenarios
gold files
PGF clients
project version
```

---

# 7. Layer 1 — parameters and low-level resources

## 7.1 Purpose

This layer defines the finite grammatical domains and reusable low-level operations used throughout the Albanian concrete syntax.

Typical ownership belongs in a resource module such as:

```text
ResSqi.gf
```

when present.

## 7.2 Parameter domains

The architecture must explicitly model every parameter used across module boundaries.

Relevant domains may include:

- number;
- gender;
- person;
- case;
- definiteness;
- agreement;
- tense;
- anteriority;
- polarity;
- verb form;
- adjective form;
- pronoun form;
- clitic placement or form;
- noun inflection class;
- verb conjugation class.

The exact constructors and names belong in `CATEGORY_AND_LINCAT_CONTRACT.md` and the provider module.

## 7.3 Public-resource rules

A low-level public resource may expose:

```gf
param ...
oper ...
```

only when the exported item has a stable cross-module purpose.

Private implementation helpers should remain private.

## 7.4 No reverse dependency

Resource and parameter modules must not import:

```text
GrammarSqi
LangSqi
AllSqi
SyntaxSqi
```

or another top-level entrypoint merely to obtain a helper.

The helper must move to the correct lower layer.

## 7.5 Parameter change

Changing a public parameter domain is breaking when it affects:

- table completeness;
- pattern matching;
- lincat fields;
- constructor output;
- scenario output;
- gold output.

All consumers must be recompiled and reviewed.

---

# 8. Layer 2 — morphology

## 8.1 Purpose

The morphology layer converts lexical stems and grammatical features into Albanian word forms.

It must represent the language’s inflectional distinctions explicitly enough for syntax consumers.

## 8.2 Noun morphology

The noun system must provide the forms required for:

- number;
- case;
- definiteness;
- gender-sensitive agreement where applicable;
- noun-phrase construction.

Canonical category ownership is expected around:

```text
NounSqi.gf
```

with lower-level resource support as needed.

The concrete representation must not collapse all noun forms into one string when consumers require distinctions.

## 8.3 Adjective morphology

The adjective system must provide the agreement and surface variants required by:

- attributive modification;
- predicative use;
- comparison;
- coordination;
- article or linking behavior where represented by the project.

Expected provider when present:

```text
AdjectiveSqi.gf
```

## 8.4 Verb morphology

The verb system must provide the finite and nonfinite forms needed by Albanian clause construction.

Expected provider when present:

```text
VerbSqi.gf
```

The architecture must distinguish at least those features consumed by:

- tense and anteriority;
- polarity;
- person and number agreement;
- participial or infinitival constructions;
- auxiliary constructions;
- clitic ordering;
- complements.

## 8.5 Pronoun morphology

Pronouns must retain enough structure for:

- person;
- number;
- gender where relevant;
- case or syntactic role;
- strong versus clitic realization where modeled;
- possessive or reflexive behavior where modeled.

Pronoun form selection must have one owner.

## 8.6 Numeral morphology

Numeral architecture must define:

- cardinal and ordinal behavior;
- agreement or noun-selection requirements;
- compositional numeral construction;
- interaction with determiners and noun phrases.

Expected provider when present:

```text
NumeralSqi.gf
```

## 8.7 Morphological evidence

Required evidence includes:

```text
direct provider compilation
paradigm constructor compilation
representative morphology scenario
representative linearization gold
consumer entrypoint compilation
```

---

# 9. Layer 3 — category implementations and paradigms

## 9.1 Purpose

This layer defines the concrete `lincat` structures and public constructors used by syntax and lexicon modules.

## 9.2 Category ownership

Each concrete category has one authoritative representation.

Examples:

```gf
lincat N  = ... ;
lincat CN = ... ;
lincat NP = ... ;
lincat A  = ... ;
lincat AP = ... ;
lincat V  = ... ;
lincat V2 = ... ;
lincat VP = ... ;
lincat Cl = ... ;
```

The exact shapes belong in:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

## 9.3 Paradigm API

A paradigms module, when present, provides stable lexical constructor functions.

Expected provider:

```text
ParadigmsSqi.gf
```

Typical consumers:

```text
LexiconSqi.gf
StructuralSqi.gf
project-specific lexical modules
```

Paradigm constructors must:

- return fully valid category values;
- initialize every required field;
- preserve irregular forms;
- avoid hidden default strings;
- document argument order;
- distinguish stable and temporary constructors.

## 9.4 Constructor naming

Public paradigm names are contractual.

Renaming requires:

- consumer search;
- lexicon update;
- scenario update;
- dependency-map update;
- contract-lock update;
- decision entry when breaking.

## 9.5 Category helper location

A helper belongs:

- in the category module when category-specific;
- in a low-level resource when shared by unrelated categories;
- in paradigms when intended for lexical construction;
- in syntax when it combines complete category values.

A helper must not be duplicated across modules only for convenience.

---

# 10. Layer 4 — core syntax

## 10.1 Purpose

Core syntax combines structured morphological categories into phrases, clauses, questions, relatives, and sentences.

## 10.2 Noun phrase syntax

The noun-phrase architecture must coordinate:

- noun inflection;
- definiteness;
- number;
- gender;
- determiners;
- adjectives;
- numerals;
- pronouns;
- prepositional complements;
- possessive structures.

Expected ownership is divided between category providers and syntax modules such as `NounSqi.gf`.

The exact provider-consumer split must be listed in the dependency map.

## 10.3 Verb phrase syntax

Verb phrase construction must coordinate:

- verb valency;
- object and complement insertion;
- agreement;
- tense and polarity;
- auxiliaries;
- clitics;
- adverbials;
- nonfinite complements.

Expected ownership is centered around `VerbSqi.gf` and clause/sentence modules.

## 10.4 Clause and sentence syntax

Expected modules when present:

```text
SentenceSqi.gf
TenseSqi.gf
PhraseSqi.gf
```

They own progressively higher combinations:

```text
VP + subject/agreement → clause
clause + tense/polarity → sentence
sentence/utterance → phrase-level output
```

Exact field ownership must be explicit.

## 10.5 Question syntax

Expected provider when present:

```text
QuestionSqi.gf
```

It owns:

- polar-question formation;
- constituent questions;
- interrogative phrases;
- interrogative word order;
- question-specific clitic or auxiliary behavior.

It may consume clause resources but must not duplicate ordinary clause construction.

## 10.6 Relative syntax

Expected provider when present:

```text
RelativeSqi.gf
```

It owns:

- relative pronouns or markers;
- gap or resumptive strategy as implemented;
- relative-clause agreement;
- attachment to nominal phrases.

## 10.7 Coordination

Expected provider when present:

```text
ConjunctionSqi.gf
```

It owns list and coordination behavior.

Coordination must preserve category structure rather than concatenating arbitrary strings where agreement or punctuation is needed.

## 10.8 Adverbial syntax

Known representative module:

```text
AdverbSqi.gf
```

It owns or contributes:

- adverb construction;
- adjective-to-adverb operations where appropriate;
- phrase attachment;
- degree modification;
- adverbial ordering constraints.

## 10.9 Symbol syntax

Expected provider when present:

```text
SymbolSqi.gf
```

It owns structured use of:

- symbols;
- numerals as symbols;
- names or literal tokens;
- punctuation-sensitive combinations.

---

# 11. Layer 5 — structural vocabulary and closed classes

## 11.1 Purpose

Structural vocabulary provides closed-class and grammar-supporting lexical items.

Expected provider when present:

```text
StructuralSqi.gf
```

## 11.2 Owned areas

The structural layer may own:

- prepositions;
- conjunctions;
- determiners;
- pronouns;
- interrogatives;
- quantifiers;
- particles;
- auxiliaries;
- subjunctions;
- fixed structural adverbs.

## 11.3 Structural-entry rules

Every structural entry must:

- use approved category constructors;
- encode required case or complement behavior;
- preserve agreement features;
- avoid duplicated independent reconstruction by consumers;
- be marked when temporary or approximate;
- have scenario evidence when it affects major syntax.

## 11.4 Preposition contract

A preposition must retain any required:

- case selection;
- complement type;
- contraction behavior;
- linearization ordering;
- interaction with pronouns.

It must not be represented as raw `Str` when consumers require more structure.

## 11.5 Determiner contract

Determiners must retain the features used for:

- definiteness;
- number;
- gender;
- quantification;
- noun-phrase agreement;
- standalone pronominal use where supported.

---

# 12. Layer 6 — extensions and Albanian-specific constructions

## 12.1 Purpose

The extension layer implements constructions outside the minimal core grammar or coordinates families of extended functions.

Known representative module:

```text
ExtendSqi.gf
```

Other expected modules may include:

```text
ExtraSqi.gf
ConstructionSqi.gf
IdiomSqi.gf
```

when present.

## 12.2 Extension boundary

An extension module may:

- consume stable lower-layer categories;
- add language-specific constructions;
- coordinate related extension providers;
- expose selected constructions through top-level entrypoints.

It must not:

- become the hidden owner of basic noun or verb morphology;
- redefine stable category lincats;
- import top-level entrypoints;
- conceal incomplete implementation.

## 12.3 Albanian-specific phenomena

Project-specific constructions that may require explicit ownership include:

- clitic combinations;
- analytic tense constructions;
- article-sensitive adjective behavior;
- definite and indefinite nominal realization;
- case-governed prepositional phrases;
- reflexive and impersonal patterns;
- complementizer and subordination behavior;
- idiomatic constructions.

Only implemented and validated phenomena may be marked stable.

## 12.4 Extension status

Each extension family must be classified in `STATUS_LEDGER.md` as one of:

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

A blocked or fallback construction must not be represented as complete in release documentation.

---

# 13. Layer 7 — lexicon

## 13.1 Purpose

The lexicon instantiates abstract lexical functions with Albanian paradigms.

Expected provider when present:

```text
LexiconSqi.gf
```

Additional project-specific lexicon modules may be used when ownership is explicit.

## 13.2 Lexicon rules

Lexical entries must:

- use approved paradigms;
- preserve Albanian orthography;
- include irregular forms explicitly;
- avoid duplicate abstract identifiers;
- use the correct GF category;
- avoid private ad hoc record construction when a public paradigm exists;
- mark temporary approximations;
- trigger gold review when output changes.

## 13.3 Lexicon versus morphology

The lexicon owns lexical data.

Morphology and paradigms own reusable inflectional behavior.

A lexicon module must not become the only place where a general inflection rule exists.

## 13.4 Coverage

Lexical completeness is project-release specific.

It must be tracked through:

```text
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/STATUS_LEDGER.md
project/docs/RELEASE_CRITERIA.md
```

---

# 14. Layer 8 — public entrypoints

## 14.1 Purpose

Entrypoints expose stable compilable surfaces to GF Wordbench, scenarios, and PGF consumers.

Known representative entrypoints include:

```text
GrammarSqi.gf
LangSqi.gf
AllSqi.gf
```

The exact role of each must match `project.toml`.

## 14.2 Grammar entrypoint

Expected role of:

```text
GrammarSqi.gf
```

is to expose the main concrete grammar surface required by compilation and higher-level composition.

It must:

- import every required concrete component;
- use the documented abstract grammar;
- compile from a clean artifact directory;
- surface missing required linearizations;
- avoid local machine paths;
- remain a registered checkpoint or entrypoint.

## 14.3 Language entrypoint

Expected role of:

```text
LangSqi.gf
```

is to expose the language-level composition expected by scenarios or clients.

It may combine:

- grammar;
- structural vocabulary;
- lexicon;
- extensions;
- language API modules.

Its exact public surface must be documented.

## 14.4 Aggregate entrypoint

Expected role of:

```text
AllSqi.gf
```

is an aggregate or broad validation surface when registered.

It may be useful for:

- integration compilation;
- detecting downstream failures;
- broad module coverage;
- development diagnostics.

It must not be treated as the release PGF target unless `project.toml` explicitly selects it.

## 14.5 Syntax entrypoint

Expected module when present:

```text
SyntaxSqi.gf
```

It exposes constructors intended for application or grammar-development use.

Its public functions must be stable enough for consumers and tests.

## 14.6 API entrypoint

An optional application-facing API module may expose a controlled subset.

If present, it must be explicitly registered.

No API entrypoint may be inferred only from filename convention.

## 14.7 Release entrypoint

The release entrypoint is selected by:

```text
project/project.toml
```

It owns the expected PGF target.

Successful release build requires:

- GF process success;
- expected PGF existence;
- non-empty artifact;
- required languages/functions;
- manifest entry;
- release-mode gate success.

---

# 15. Layer 9 — validation and release evidence

## 15.1 Checkpoints

Checkpoints prove architectural layers incrementally.

Recommended progression:

```text
resource/morphology checkpoint
        ↓
category checkpoint
        ↓
core syntax checkpoint
        ↓
structural/extension checkpoint
        ↓
GrammarSqi
        ↓
LangSqi or configured language entrypoint
        ↓
configured release entrypoint
```

The exact ordered checkpoint list belongs in `project.toml`.

## 15.2 Required scenarios

Project validation should include, as applicable:

```text
load
missing
linearize
parse
generation
morphology
```

Actual IDs are configuration-owned.

Required scenarios cannot be skipped in a successful release.

## 15.3 Gold files

Gold files contain reviewed normalized output.

They must not be modified during normal validation.

A change to morphology, syntax, structural vocabulary, lexicon, entrypoints, or normalization requires deliberate gold review.

## 15.4 Release artifact

The final PGF is a generated release artifact.

Its identity includes:

```text
project version
source revision
GF Wordbench version
GF version
entrypoint
SHA-256
manifest record
```

---

# 16. Import-direction rules

## 16.1 Allowed direction

```text
ResSqi / low-level interfaces
    → morphology modules
    → ParadigmsSqi and category modules
    → sentence/question/relative modules
    → StructuralSqi
    → ExtendSqi / ConstructionSqi / ExtraSqi
    → LexiconSqi
    → GrammarSqi
    → LangSqi / SyntaxSqi / API
    → AllSqi or configured release entrypoint
```

This is a conceptual direction.

The exact graph belongs in `MODULE_DEPENDENCY_MAP.md`.

## 16.2 Prohibited direction

Examples:

```text
ResSqi → GrammarSqi
NounSqi → LangSqi
VerbSqi → AllSqi
ParadigmsSqi → LexiconSqi
SentenceSqi → final API entrypoint
StructuralSqi → AllSqi merely for a helper
```

## 16.3 Circularity

Circular GF imports are prohibited.

When two modules need the same helper:

1. identify the helper’s true abstraction level;
2. move it to a lower shared provider;
3. document the provider;
4. update all consumers;
5. validate downstream entrypoints.

---

# 17. Category and lincat architecture

## 17.1 Contract ownership

The complete lincat contract belongs in:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

This document fixes the architectural rules.

## 17.2 Required properties

Every public lincat must define:

- provider module;
- record or table shape;
- public fields;
- parameter domains;
- construction invariants;
- consumers;
- validation evidence;
- compatibility status.

## 17.3 Field visibility

A field becomes contractual when another module accesses it.

Private fields may change locally only when no consumer depends on them.

## 17.4 Lincat change impact

Changing any of the following is potentially breaking:

```text
field name
field type
table index
parameter constructor
agreement behavior
word-order flag
case requirement
polarity behavior
clitic field
variant representation
```

Required review:

```text
all direct consumers
all downstream entrypoints
scenarios
golds
project contract lock
decision log
project version
```

## 17.5 No accidental compatibility

A consumer compiling by accident after a lincat change does not prove semantic compatibility.

Representative linearization and parse scenarios are also required.

---

# 18. Morphosyntactic invariants

The following are architectural invariants unless superseded by a recorded decision.

## 18.1 Nominal invariants

- noun forms retain required number, case, and definiteness distinctions;
- noun gender remains available to agreement consumers;
- noun phrase construction does not guess unavailable forms;
- adjective and determiner agreement use documented features;
- case selection has one owner;
- definiteness realization has one owner per construction family.

## 18.2 Verbal invariants

- verb valency remains explicit;
- finite agreement remains structured;
- tense and polarity are not embedded inconsistently across unrelated modules;
- object and clitic handling follow one documented ordering model;
- auxiliary selection has one owner;
- participial/nonfinite forms remain available where consumers require them.

## 18.3 Pronominal invariants

- person and number remain explicit;
- case or syntactic role remains distinguishable where required;
- clitic and strong forms are not confused silently;
- reflexive behavior has documented ownership;
- pronoun ordering is not reconstructed independently by multiple modules.

## 18.4 Clause invariants

- subject and predicate combination uses the declared agreement contract;
- complement order is documented;
- question formation reuses clause structure where appropriate;
- relative construction preserves required gap or marker information;
- sentence-level tense/polarity composition remains centralized.

---

# 19. Word-order ownership

Word order must be decided at the lowest layer with enough information to make the decision correctly.

Examples:

| Decision | Preferred owner |
|---|---|
| Stem and affix composition | morphology |
| Article/inflection composition | morphology or category provider |
| Determiner–noun ordering | noun phrase syntax |
| Adjective placement | noun/adjective syntax |
| Object placement | verb phrase syntax |
| Clitic sequence | dedicated verb/clitic resource |
| Subject–predicate order | clause syntax |
| Question order | question syntax |
| Relative marker order | relative syntax |
| Coordination punctuation/order | conjunction module |
| Utterance punctuation | phrase/sentence layer |

A high-level entrypoint must not patch lower-level word order through raw string manipulation.

---

# 20. Variation and variants

GF variants may represent genuine acceptable alternatives.

Rules:

- variants must be linguistically motivated;
- variant order must be deterministic where gold comparison depends on it;
- unbounded variant explosion is prohibited;
- optionality must not conceal missing required forms;
- normalization must preserve meaningful variation;
- gold expectations must state whether order and multiplicity matter.

---

# 21. Fallbacks and incomplete implementation

## 21.1 Registration

Every temporary or approximate implementation must be registered in:

```text
project/docs/STATUS_LEDGER.md
```

## 21.2 Prohibited hidden fallback

Examples of prohibited hidden fallback:

```gf
s = ""
s = input.s
s = table { _ => input.s }
```

when the structure requires real inflection or syntax and no decision authorizes the fallback.

## 21.3 Allowed temporary fallback

A temporary fallback may be used only when:

- status is explicit;
- consumers are known;
- release impact is known;
- validation demonstrates the limitation;
- replacement work is tracked.

## 21.4 Release behavior

A fallback marked blocking prevents release.

A nonblocking fallback must be explicitly accepted in `RELEASE_CRITERIA.md`.

---

# 22. Extension boundaries

## 22.1 Core versus extension

A construction belongs in core syntax when it is required for the normal RGL contract.

It belongs in extension when it is:

- language-specific;
- outside the core abstract API;
- optional;
- experimental;
- coordinated across a separate family.

## 22.2 Extension consumers

Entrypoints must choose explicitly whether to include an extension provider.

An extension must not become active merely because it is in the GF search path.

## 22.3 Promotion

Promoting an extension to stable core requires:

- contract decision;
- provider ownership;
- consumer update;
- checkpoint update;
- scenario coverage;
- gold review;
- status-ledger update;
- release-criteria update.

---

# 23. Entrypoint registry

The authoritative entrypoint registry is `project.toml`.

This document expects the registry to distinguish:

```text
development checkpoints
grammar entrypoint
language entrypoint
syntax/API entrypoint
release entrypoint
PGF target
```

No tool or scenario may infer a different registry from filenames.

A documentation mismatch is architecture drift.

---

# 24. Architecture ownership map

The following map must be kept synchronized with the source tree.

| Responsibility | Expected provider family | Main consumers |
|---|---|---|
| Low-level parameters/resources | `ResSqi` or registered equivalent | all concrete modules |
| Noun morphology and NP categories | `NounSqi` | syntax, structural, lexicon |
| Verb morphology and VP categories | `VerbSqi` | sentence, question, extensions |
| Adjective morphology and AP categories | `AdjectiveSqi` | noun syntax, comparisons |
| Adverbs | `AdverbSqi` | VP, clause, phrase |
| Numerals | `NumeralSqi` | NP syntax, structural |
| Sentence/clause syntax | `SentenceSqi` | question, relative, grammar |
| Tense/polarity | `TenseSqi` | sentence and entrypoints |
| Questions | `QuestionSqi` | grammar |
| Relatives | `RelativeSqi` | grammar |
| Coordination | `ConjunctionSqi` | grammar and category consumers |
| Phrase/utterance | `PhraseSqi` | language entrypoints |
| Structural vocabulary | `StructuralSqi` | grammar/language entrypoints |
| Paradigm API | `ParadigmsSqi` | lexicon and structural |
| Lexicon | `LexiconSqi` | language entrypoint |
| Extensions | `ExtendSqi` and registered providers | language/API entrypoints |
| Main concrete grammar | `GrammarSqi` | `LangSqi`, scenarios, PGF |
| Language composition | `LangSqi` | scenarios, API, release |
| Aggregate validation surface | `AllSqi` when registered | diagnostic validation |
| Syntax API | `SyntaxSqi` when registered | application clients/scenarios |
| Final PGF target | configured release entrypoint | release workflow |

“Expected provider family” does not prove that a file currently exists or is stable.

Exact status belongs in `STATUS_LEDGER.md`.

---

# 25. Module-status model

Canonical project implementation statuses:

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

## 25.1 Stable

- provider exists;
- direct compilation passes;
- required consumers pass;
- required scenarios pass;
- no known blocking contract issue.

## 25.2 Experimental

- provider exists;
- behavior may change;
- not relied upon by required stable release paths unless explicitly accepted.

## 25.3 Temporary

- implementation is intentionally short-lived;
- replacement is planned;
- consumers and limitations are documented.

## 25.4 Fallback

- behavior is intentionally approximate;
- the limitation is visible;
- release impact is documented.

## 25.5 Warning

- implementation works but carries a known concern requiring review.

## 25.6 Blocked

- required implementation or dependency is unavailable;
- release impact is explicit.

## 25.7 Disabled

- code or scenario is intentionally excluded.

## 25.8 Retired

- no current consumer may depend on it;
- identity remains documented for history.

---

# 26. Validation architecture

## 26.1 Quick validation

Used for a selected file or bounded local change.

It proves only the requested scope.

It does not establish architecture-wide stability.

## 26.2 Checkpoint validation

Used after completing a layer.

A checkpoint should compile:

- the changed provider;
- key direct consumers;
- the next architectural entrypoint.

## 26.3 Diagnostic validation

Used for broad evidence and root-cause analysis.

It may include:

- all configured files;
- optional scenarios;
- bounded generation;
- deeper introspection.

## 26.4 Release validation

Required for project release.

It must include:

- required source modules;
- configured entrypoints;
- missing-linearization check;
- PGF build;
- required scenarios;
- gold comparison;
- artifact manifest;
- known-issue gate.

---

# 27. Change workflow

Every architectural change follows this sequence.

```text
1. identify provider
2. identify public surface
3. identify direct consumers
4. identify downstream entrypoints
5. identify contract ID
6. classify compatible or breaking
7. update implementation
8. update category/lincat contract
9. update dependency map
10. update scenarios
11. review gold
12. update status ledger
13. record decision when required
14. validate checkpoints
15. validate release entrypoints when applicable
16. update interfile lock
```

An isolated source-file edit is not complete when a cross-file contract changes.

---

# 28. Compatible changes

Usually compatible:

- private helper refactor;
- performance improvement with identical output;
- new optional paradigm;
- new optional lexical item;
- new optional extension not included in stable entrypoints;
- additional internal table field not consumed externally;
- improved diagnostic comments.

Compatibility must still be proven.

---

# 29. Breaking changes

Breaking project changes include:

- module rename;
- public symbol rename;
- category or lincat field change;
- parameter-constructor change;
- constructor arity change;
- constructor argument-order change;
- entrypoint change;
- module suffix change;
- word-order contract change;
- clitic-order contract change;
- scenario ID change;
- gold normalization change;
- expected PGF name change;
- public abstract API change;
- ownership transfer between modules.

A breaking change requires a decision-log entry and project-version review.

---

# 30. Review matrix

| Changed area | Minimum review |
|---|---|
| Resource parameter | all pattern matches and tables |
| Noun lincat | noun syntax, adjectives, determiners, lexicon |
| Verb lincat | VP, sentence, questions, extensions |
| Pronoun structure | NP, VP/clitic logic, structural vocabulary |
| Tense structure | sentence, questions, relatives, entrypoints |
| Paradigm constructor | all lexical consumers |
| Structural entry | scenarios and gold using the entry |
| Entry point | project config, scenarios, PGF build |
| Normalization-sensitive output | gold review |
| Module name | imports, config, docs, scenarios |
| Scenario ID | config, gold, coverage matrix, reports |

---

# 31. Architecture anti-drift rules

Drift exists when:

- source modules and `project.toml` disagree;
- module suffix differs from `Sqi`;
- a lower-level module imports a top-level entrypoint;
- a consumer accesses an undocumented lincat field;
- two modules own the same public helper;
- a parameter value appears in consumers but not in the category contract;
- `GrammarSqi`, `LangSqi`, or `AllSqi` roles are ambiguous;
- a scenario loads an unregistered entrypoint;
- an expected PGF name differs across config and docs;
- a fallback is not in the status ledger;
- a gold changes without a reviewed implementation or normalization change;
- a module is marked stable without downstream validation;
- an entrypoint compiles only because of undeclared local paths;
- a source file belongs to the active language but is excluded accidentally;
- a retired module still has consumers;
- documentation describes a module that no longer exists without marking it historical.

Any drift must be corrected or deliberately adopted through the change workflow.

---

# 32. Documentation synchronization

When architecture changes, review:

```text
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
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Only affected documents require content changes.

Every document must still be reviewed for consistency.

---

# 33. Architecture review checklist

```text
[ ] project identity remains Albanian / Sqi
[ ] source root matches project.toml
[ ] exact module inventory is current
[ ] entrypoints are registered
[ ] checkpoints are ordered
[ ] release entrypoint is explicit
[ ] expected PGF is explicit
[ ] import graph is acyclic
[ ] lower layers do not import higher entrypoints
[ ] every public helper has one owner
[ ] every cross-module lincat field is documented
[ ] parameter domains are complete
[ ] noun morphology preserves required distinctions
[ ] verb morphology preserves required distinctions
[ ] pronoun/clitic behavior has one owner
[ ] word-order decisions have explicit owners
[ ] structural vocabulary uses approved constructors
[ ] lexicon uses approved paradigms
[ ] extensions have explicit status
[ ] no hidden fallback exists
[ ] scenarios map to documented entrypoints
[ ] gold files use the current normalization version
[ ] changed providers have validated consumers
[ ] status ledger is current
[ ] decision log records breaking changes
[ ] dependency map is synchronized
[ ] interfile contract lock is synchronized
```

---

# 34. Release architecture checklist

```text
[ ] required checkpoints compile
[ ] GrammarSqi or configured grammar entrypoint compiles
[ ] LangSqi or configured language entrypoint compiles
[ ] configured release entrypoint compiles
[ ] missing-linearization check passes
[ ] required morphology scenario passes
[ ] required linearization scenario passes
[ ] required parse scenario passes
[ ] required load scenario passes
[ ] required gold files match
[ ] no blocking fallback remains
[ ] no blocking known issue remains
[ ] final PGF exists and is non-empty
[ ] PGF uses the configured entrypoint
[ ] manifest contains the PGF and required reports
[ ] project version and source revision are recorded
[ ] GF Wordbench and GF versions are recorded
```

---

# 35. Prohibited architecture behavior

The following are prohibited:

- language-specific assumptions in framework Python code;
- module identity inferred from old output directories;
- top-level entrypoints used as low-level helper libraries;
- circular imports;
- undocumented public lincat fields;
- duplicated public helper ownership;
- silent flattening to `Str`;
- raw-string patches at entrypoint level for lower-layer errors;
- hidden default morphology;
- lexicon-local implementation of general morphology;
- scenarios loading unregistered entrypoints;
- optional scenarios silently becoming release requirements;
- required scenarios silently becoming optional;
- normal validation modifying gold;
- a zero GF exit code treated as sufficient release evidence;
- missing required PGF treated as success;
- undocumented fallback presented as stable;
- architecture documentation using stale language identifiers;
- source change declared complete before consumers are validated.

---

# 36. Final invariants

1. The active project is Albanian and uses the `Sqi` module suffix.
2. `project.toml` owns project identity and entrypoint selection.
3. The source tree owns the exact current module inventory.
4. The dependency map owns explicit import relationships.
5. The category contract owns public lincat shapes.
6. The morphology specification owns inflectional requirements.
7. The syntax specification owns constructor and word-order rules.
8. The interfile lock owns cross-module promises.
9. Every public item has one provider.
10. Lower layers do not import higher entrypoints.
11. Circular imports are prohibited.
12. Structured categories are not flattened without a decision.
13. Shared parameter domains are documented.
14. Albanian noun forms preserve required case, number, gender, and definiteness information.
15. Verb forms preserve the features required by clause consumers.
16. Pronoun and clitic behavior has explicit ownership.
17. Word-order decisions occur at the correct information-bearing layer.
18. Paradigms own reusable lexical construction.
19. Lexicon owns lexical data, not general morphology.
20. Structural entries use approved category constructors.
21. Extensions are explicit and status-controlled.
22. `GrammarSqi`, `LangSqi`, `AllSqi`, and other entrypoints have distinct registered roles.
23. Required scenarios load only documented entrypoints.
24. Gold comparison follows versioned normalization.
25. Normal validation never modifies gold.
26. Stable status requires direct and downstream evidence.
27. Fallback and blocked work remains visible.
28. Breaking architecture changes are coordinated and recorded.
29. Release requires a verified PGF and manifest.
30. Documentation, configuration, source, scenarios, and artifacts must agree.

---

# 37. Final rule

The Albanian grammar is not a collection of independent `.gf` files.

It is one layered network of typed contracts:

```text
abstract functions
    → Albanian parameters and morphology
    → structured categories
    → syntax
    → structural vocabulary and extensions
    → lexicon
    → registered entrypoints
    → scenarios and gold
    → verified PGF
```

A change is architecturally complete only when the provider, every affected consumer, the project configuration, the validation evidence, and the project documentation all agree.
