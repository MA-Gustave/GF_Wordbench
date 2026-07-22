# GF Wordbench Project — Morphology Specification

**Document ID:** `GF-WB-PROJECT-MORPHOLOGY-SPEC`  
**Status:** Normative project specification  
**Applies to:** The active Albanian (`sqi`, GF suffix `Sqi`) language project  
**Primary source area:** `lib/src/albanian/`  
**Owner:** Active language project maintainers  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\project\docs\MORPHOLOGY_SPEC.md`  
**Document version:** `1.0.0`  
**Last reviewed:** `2026-07-22`

---

## 1. Purpose

This document defines the morphology contract for the active Albanian GF project.

It specifies:

- which modules own morphological knowledge;
- how low-level morphology, paradigms, category implementations, lexicon modules, structural modules, and entrypoints depend on one another;
- which grammatical distinctions must be represented;
- how inflection tables and stems are modeled;
- how regular, irregular, defective, and invariant forms are handled;
- how morphology interacts with lincats;
- how orthographic transformations are centralized;
- which public constructors are allowed to cross module boundaries;
- how morphology is validated;
- which changes are breaking;
- which evidence is required before a morphology change is accepted.

This document does not replace GF source.

The source remains authoritative for exact public symbol names and GF types.

This document defines the behavior those source symbols must collectively provide.

---

## 2. Authority and source-verification rule

The morphology specification has three authority layers.

### 2.1 GF authority

GF is authoritative for:

- source syntax;
- type correctness;
- table completeness;
- pattern validity;
- module resolution;
- compilation;
- morphological analysis;
- linearization;
- generation;
- PGF behavior.

GF Wordbench must not replace GF’s morphological semantics with a Python reimplementation.

### 2.2 Project source authority

The active source tree is authoritative for:

- exact `param` names;
- exact parameter values;
- exact record fields;
- exact table types;
- exact public `oper` names;
- exact constructor signatures;
- exact imported module names;
- exact irregular lexical entries.

### 2.3 Documentation authority

This document is authoritative for:

- module ownership;
- dependency direction;
- required grammatical distinctions;
- invariants;
- accepted simplifications;
- validation obligations;
- change coordination;
- fallback policy.

### 2.4 No invented-symbol rule

A maintainer must not add an exact GF symbol to this document unless the symbol exists in the source or is introduced in the same coordinated change.

When source and documentation disagree:

1. preserve the failing evidence;
2. identify whether source or documentation is intended to change;
3. update provider, consumers, tests, contracts, and this document together;
4. do not silently reinterpret an undocumented field or constructor.

---

## 3. Related project documents

Read this specification with:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_OVERVIEW.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA.md
project/docs/RESEARCH_EVIDENCE.md
```

Framework-level behavior is governed by:

```text
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/gf/GF_TOOLCHAIN_INTEGRATION.md
docs/validation/VALIDATION_PIPELINE.md
docs/diagnostics/DIAGNOSTIC_OVERVIEW.md
```

When a project document conflicts with the project interfile lock, the lock governs.

---

## 4. Confirmed project modules

Current project evidence confirms the following Albanian modules or module roles:

```text
lib/src/albanian/MorphoSqi.gf
lib/src/albanian/ParadigmsSqi.gf
lib/src/albanian/NounSqi.gf
lib/src/albanian/CatSqi.gf
lib/src/albanian/GrammarSqi.gf
lib/src/albanian/StructuralSqi.gf
lib/src/albanian/AdverbSqi.gf
lib/src/albanian/ExtendSqi.gf
lib/src/albanian/LangSqi.gf
lib/src/albanian/AllSqi.gf
```

Additional category modules such as verb, adjective, pronoun, determiner, numeral, sentence, question, relative, and conjunction modules are governed by the same rules when present.

The dependency map must list the complete current source set.

---

## 5. Morphology ownership model

The expected dependency direction is:

```text
MorphoSqi
→ ParadigmsSqi
→ lexical/category modules
→ StructuralSqi and syntax modules
→ GrammarSqi
→ LangSqi / AllSqi / API entrypoints
→ PGF
```

Lower layers must not import higher-level entrypoints.

### 5.1 `MorphoSqi.gf`

`MorphoSqi.gf` is the authoritative low-level morphology provider.

It owns or coordinates:

- inflection parameters;
- inflection-table types;
- stem types;
- stem-selection operations;
- shared orthographic operations;
- regular inflection builders;
- irregular-form builders;
- defective-form representation;
- agreement-support structures;
- morphology-specific helper records;
- canonical form retrieval operations.

It must not depend on:

```text
GrammarSqi
LangSqi
AllSqi
API entrypoints
release-only modules
scenario files
gold files
```

### 5.2 `ParadigmsSqi.gf`

`ParadigmsSqi.gf` is the public lexical-construction API.

It owns or re-exports:

- user-facing `mkN`-like constructors;
- user-facing verb constructors;
- adjective constructors;
- adverb constructors when morphologically relevant;
- pronoun/determiner constructors when part of the public paradigm API;
- invariant-word constructors;
- irregular constructors;
- documented overloads;
- stable constructor defaults.

It must call `MorphoSqi` or another declared morphology provider.

It must not duplicate low-level inflection logic merely to avoid importing the provider.

### 5.3 Category modules

Category implementations such as `NounSqi.gf` consume morphology through documented structures.

They own:

- category lincats;
- syntax-facing composition;
- agreement propagation;
- article/determiner interaction;
- case selection;
- complement realization;
- category-specific ordering.

They do not own general stem or inflection algorithms already provided by `MorphoSqi`.

### 5.4 Lexicon modules

Lexicon modules consume public paradigms.

They own:

- lexical lemmas;
- constructor selection;
- lexical irregularity arguments;
- lexical semantic classification;
- documented lexical exceptions.

They must not reconstruct inflection tables manually when a public paradigm exists.

### 5.5 Structural modules

`StructuralSqi.gf` and related modules may contain closed-class items whose forms are morphologically irregular.

They may use low-level morphology only through public documented constructors or a declared structural interface.

They must not become a second hidden morphology provider.

### 5.6 Entrypoints

`GrammarSqi.gf`, `LangSqi.gf`, `AllSqi.gf`, and release/API entrypoints consume completed category and syntax layers.

They must not define local morphology to repair lower-level defects.

---

## 6. Locked project contracts

This specification implements and expands the following project contracts.

### 6.1 `PIFC-MODULE-003` — Morphology to paradigms

**Status:** Active

Provider:

```text
lib/src/albanian/MorphoSqi.gf
```

Primary consumer:

```text
lib/src/albanian/ParadigmsSqi.gf
```

Additional consumers may include category, lexicon, and structural modules when documented.

Provided elements include:

- inflection tables;
- stem operations;
- agreement parameters;
- constructor helpers;
- irregular-form support.

### 6.2 `PIFC-MODULE-004` — Paradigms to lexicon

**Status:** Active

Provider:

```text
lib/src/albanian/ParadigmsSqi.gf
```

Consumers:

```text
project lexicon modules
project structural lexicon
project examples and lexical tests
```

### 6.3 `PIFC-LINCAT-001` — Categories to lincat consumers

Morphological structures exposed through lincats must be documented in:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

### 6.4 `PIFC-LINCAT-002` — Parameters to pattern consumers

Every `param` value inspected by another module is a public contract.

Adding, removing, renaming, merging, or reordering parameter values requires consumer review.

### 6.5 `PIFC-HELPER-001` — Helper providers to consumers

Shared orthographic and stem helpers must have one provider and a registered consumer set.

---

# 7. Design principles

## 7.1 Structure before strings

Morphological values must remain structured until the point where a concrete string is required.

Do not flatten:

```text
noun
adjective
verb
pronoun
determiner
participle
agreement value
case-bearing phrase
```

to `Str` solely to satisfy one consumer.

A flattening that crosses a module boundary is a breaking contract change unless explicitly approved.

---

## 7.2 Total tables

An inflection table must define every value in its declared domain.

Partial table behavior is allowed only when the missingness is represented explicitly.

A runtime crash or hidden `Predef.error` must not be used as the normal representation of a defective paradigm.

---

## 7.3 Centralized orthography

An orthographic transformation used by more than one paradigm must have one owner.

Examples of transformation classes:

- final-letter replacement;
- suffix attachment;
- vowel alternation;
- consonant alternation;
- stress-sensitive choice when represented;
- elision;
- clitic joining;
- article joining;
- capitalization preservation;
- punctuation-neutral token joining.

The same transformation must not be copied with slightly different behavior across noun, adjective, and verb modules.

---

## 7.4 Explicit irregularity

Irregularity is data or a named constructor choice.

It must not be hidden in a broad fallback that silently treats unknown inputs as a different regular class.

---

## 7.5 Conservative inference

A one-string constructor may infer a regular class only when:

- the inference rule is documented;
- the rule is deterministic;
- failures are explicit;
- representative counterexamples are tested;
- an explicit-form constructor exists for exceptions.

---

## 7.6 No unsafe shallow matching

Runtime matching directly on realized strings should be minimized.

Patterns such as:

```gf
case x.s of { ... }
```

or untyped suffix matching require explicit justification because:

- `x.s` may already be inflected;
- a string may not preserve lexical class;
- table-domain context may be lost;
- pattern behavior may change after refactoring.

Preferred design:

```text
typed lexical-class parameter
typed stem record
typed inflection class
named orthographic helper
```

Static scanner findings do not prove semantic failure, but unresolved findings must be reviewed.

---

## 7.7 Deterministic generation

Given identical:

```text
source
GF version
RGL version
lexical input
constructor
grammatical features
```

the same morphological form must be produced.

Random or environment-dependent morphology is prohibited.

---

# 8. Morphological representation layers

The project should distinguish four layers.

## 8.1 Linguistic features

Language-level distinctions such as:

```text
gender
number
case
definiteness
person
tense
mood
voice
degree
agreement
```

## 8.2 GF parameters

Typed `param` definitions representing distinctions required by tables and patterns.

## 8.3 Inflection records and tables

Typed records containing:

```text
stems
forms
agreement values
inherent lexical properties
defectiveness information
```

## 8.4 Category lincats

Structures consumed by syntax.

Category lincats may expose only the morphology that syntax needs.

They must not expose private implementation details accidentally.

---

# 9. Parameter governance

## 9.1 Public parameter rule

A parameter becomes public when:

- another module patterns on it;
- another module constructs it;
- it appears in a public lincat field;
- a public constructor accepts it;
- scenario output depends on its labels or ordering.

## 9.2 Required documentation

Every public parameter must be documented with:

```text
owner module
GF name
values
meaning
consumers
default, if any
ordering significance
validation scenario
```

The exact inventory belongs in `CATEGORY_AND_LINCAT_CONTRACT.md`.

## 9.3 Value changes

The following are breaking unless all consumers are migrated:

- renaming a value;
- removing a value;
- merging values;
- changing meaning;
- changing which table dimension the value indexes;
- changing a public constructor default.

Adding a value is also potentially breaking because existing tables may become incomplete.

## 9.4 Internal parameters

A private parameter used only inside one provider may change without external migration when:

- no public type exposes it;
- no serialized output depends on it;
- all provider tests remain valid;
- no consumer patterns on it indirectly.

---

# 10. Orthographic policy

## 10.1 Encoding

All Albanian source and validation text uses:

```text
UTF-8
```

Albanian letters and diacritics must be preserved exactly.

Do not transliterate source forms to ASCII for internal convenience.

## 10.2 Canonical forms

Lexical constructors should accept canonical orthography.

Normalization must not change lexical identity silently.

## 10.3 Case preservation

Constructors should document whether they:

- preserve input capitalization;
- require lowercase lemmas;
- normalize initial capitalization;
- provide proper-name-specific constructors.

A general noun constructor must not accidentally apply common-noun lowercasing to proper names.

## 10.4 Token joining

Use GF token-composition behavior deliberately.

Do not embed arbitrary leading/trailing spaces in morphological forms.

Whitespace-sensitive forms require tests.

## 10.5 Apostrophes and clitic punctuation

If apostrophes, hyphens, or fused clitic forms are produced:

- ownership must be explicit;
- joining rules must be centralized;
- normalized scenario output must preserve meaningful punctuation;
- gold tests must include representative forms.

---

# 11. Stem model

## 11.1 Stem identity

A stem is not automatically the citation form.

The provider must document for each paradigm:

```text
citation form
primary stem
secondary stems
plural stem
participle stem
present stem
past stem
irregular overrides
```

as applicable.

## 11.2 Stem records

When more than one consumer needs a stem distinction, represent it in a typed record.

Do not recompute the same stem separately in multiple modules.

## 11.3 Stem derivation

A derivation operation must document:

```text
accepted input shape
class precondition
transformation
fallback behavior
failure behavior
examples
```

## 11.4 Stem validation

Each stem builder needs tests for:

- shortest valid input;
- typical input;
- final vowel;
- final consonant;
- Albanian-specific letters;
- irregular override;
- unsupported input;
- capitalization.

---

# 12. Noun morphology

## 12.1 Ownership

Low-level noun inflection belongs to `MorphoSqi.gf` or one declared noun-morphology provider.

Public lexical noun constructors belong to `ParadigmsSqi.gf`.

Noun phrase composition belongs to `NounSqi.gf`.

## 12.2 Required linguistic dimensions

The noun system must represent every distinction required by the active grammar.

The Albanian linguistic target includes at least:

```text
number
definiteness
case
inherent gender
```

The source may represent some dimensions through:

- table indices;
- inherent fields;
- separate constructors;
- determiner/article structures;
- syntax-level selection.

Any collapsed distinction must be documented.

## 12.3 Number

The minimum number distinction is:

```text
singular
plural
```

If additional values exist for technical or agreement purposes, they must be documented.

Plural formation must support:

- regular suffixal classes;
- stem alternations;
- invariant nouns;
- irregular plural stems;
- plural-only or singular-only nouns when present.

## 12.4 Definiteness

The morphology must distinguish definite and indefinite nominal forms wherever the grammar requires them.

Definiteness may be represented:

- directly in noun forms;
- through determiner/article composition;
- through a combined noun table;
- through a category-specific record.

The implementation must not produce a definite form by blindly appending a single suffix to every noun class.

## 12.5 Case

The Albanian linguistic inventory includes case distinctions conventionally described as:

```text
nominative
accusative
genitive
dative
ablative
vocative
```

The GF implementation may merge or derive some of these if:

- the exact representation is documented;
- syntax consumers do not require a lost distinction;
- scenarios cover every syntax-visible case;
- the decision is recorded in `DECISION_LOG.md`.

A case represented through prepositions or article structures must not be misreported as a fully inflected noun form.

## 12.6 Gender

Nouns carry inherent gender where required for:

- adjective agreement;
- pronoun agreement;
- determiner selection;
- participial agreement;
- anaphoric reference.

The minimum target distinction is:

```text
masculine
feminine
```

Any neutral, common, unknown, or technical value must be documented and tested.

## 12.7 Noun table completeness

For every noun class, all required combinations of:

```text
number × definiteness × case
```

must be defined or explicitly marked unavailable.

## 12.8 Noun constructor classes

The public paradigm API should distinguish:

```text
regular one-form constructor
class-specific regular constructors
explicit singular/plural constructor
explicit full-paradigm constructor
invariant constructor
proper-name constructor when behavior differs
defective constructor when required
```

Exact function names are source-owned.

## 12.9 Noun irregularity

Irregular noun entries should provide explicit forms or explicit stems.

Do not encode lexical exceptions through a growing global list hidden inside a generic constructor unless that list is the documented authoritative irregular lexicon.

## 12.10 Noun validation

Required evidence includes:

```text
MorphoSqi compile
ParadigmsSqi compile
NounSqi compile
representative noun analysis scenario
representative noun linearization scenario
regular-class gold
irregular-class gold
entrypoint compile
```

---

# 13. Adjective morphology

## 13.1 Ownership

Adjective inflection belongs to `MorphoSqi.gf` or a declared adjective-morphology provider.

Public adjective constructors belong to `ParadigmsSqi.gf`.

Adjective phrase composition belongs to the adjective/category implementation module.

## 13.2 Required agreement dimensions

The adjective system must represent every distinction consumed by Albanian syntax.

The minimum target includes:

```text
gender agreement
number agreement
```

Case, definiteness, article class, position, and degree must be represented when required by the implemented syntax.

## 13.3 Albanian adjectival article behavior

Albanian adjective realization may involve a pre-adjectival linking/article element.

The project must document whether this behavior is owned by:

```text
adjective morphology
adjective phrase syntax
determiner/article module
noun phrase composition
```

Only one layer may be authoritative for selecting and ordering the element.

Do not duplicate article choice in both morphology and syntax.

## 13.4 Degree

If positive, comparative, and superlative behavior is implemented, distinguish:

```text
inflectional morphology
analytic particles
syntax-level comparison
lexical irregularity
```

Do not store analytic comparative words inside every adjective inflection table unless the architecture explicitly chooses that representation.

## 13.5 Invariant adjectives

Invariant adjectives must use an explicit invariant constructor or class.

They must not be represented by accidentally repeating one form across a table without documentation.

## 13.6 Adjective validation

Required evidence includes representative combinations of:

```text
masculine singular
feminine singular
plural
attributive use
predicative use
article/linking-element behavior
degree behavior when supported
irregular/invariant adjective
```

---

# 14. Verb morphology

## 14.1 Ownership

Verb stem formation and inflection belong to `MorphoSqi.gf` or one declared verb-morphology provider.

Public verb constructors belong to `ParadigmsSqi.gf`.

Verb phrase syntax belongs to the verb/sentence modules.

## 14.2 Required agreement dimensions

Finite forms must represent:

```text
person
number
```

at minimum.

Canonical person target:

```text
first
second
third
```

Canonical number target:

```text
singular
plural
```

## 14.3 Tense, aspect, and mood

The implementation must document which distinctions are:

- morphologically inflected;
- analytically constructed;
- delegated to tense/sentence modules;
- unsupported;
- approximated.

The Albanian target may include forms or constructions associated with:

```text
present
imperfect
aorist/simple past
perfect
pluperfect
future
conditional
subjunctive
imperative
indicative
non-finite forms
```

This list is a linguistic coverage target, not permission to claim support.

`STATUS_LEDGER.md` and the validation matrix must state actual implementation status.

## 14.4 Voice

If active, passive, middle, or reflexive distinctions are represented, ownership must be explicit.

Possible ownership:

```text
verb morphology
auxiliary construction
reflexive/clitic syntax
lexical verb class
```

A voice distinction must not be independently constructed in multiple layers.

## 14.5 Non-finite forms

Document support for:

```text
participle
infinitival construction
gerundial/converb-like construction
verbal noun
```

as applicable.

A non-finite form used by compound tense construction becomes a public contract.

## 14.6 Auxiliaries

Compound forms should use declared auxiliary providers.

Do not hard-code auxiliary strings inside arbitrary lexical verbs.

Auxiliary selection, agreement, and participle interaction must have one owner.

## 14.7 Negation

Negation normally belongs to syntax unless a form is morphologically fused.

Morphology may expose special negative forms only when linguistically required and documented.

## 14.8 Clitics

Object, reflexive, or auxiliary clitics must be modeled separately from the lexical verb paradigm unless the form is genuinely fused and inseparable.

Clitic ordering belongs to one documented provider.

## 14.9 Verb constructor classes

The public paradigm API should provide, as required:

```text
regular citation-form constructor
class-specific constructors
principal-parts constructor
explicit finite-table constructor
irregular constructor
defective constructor
auxiliary constructor
invariant/non-finite-only constructor
```

Exact names and arities are source-owned.

## 14.10 Principal parts

A verb constructor that cannot infer all forms safely must accept sufficient principal parts.

The required principal parts must be documented by class.

A constructor must not infer an irregular past or participle from unrelated spelling coincidence.

## 14.11 Defective verbs

Defective verbs must identify unavailable forms explicitly.

Unavailable forms must not:

- crash normal generation unexpectedly;
- silently copy an unrelated form;
- appear as fully supported in release coverage.

## 14.12 Verb validation

Required evidence includes representative:

```text
person × number combinations
regular classes
irregular classes
finite tense/mood forms
imperative
participle/non-finite form
compound form
negation interaction
clitic interaction when supported
analysis/generation round trip where possible
```

---

# 15. Pronoun morphology

## 15.1 Ownership

Pronoun forms may be owned by:

```text
MorphoSqi
a dedicated pronoun resource
NounSqi
StructuralSqi
```

The authoritative provider must be listed in the dependency map.

## 15.2 Required distinctions

As implemented, pronouns may require:

```text
person
number
gender
case
stressed/unstressed form
clitic/full form
possessive agreement
reflexive distinction
demonstrative distance
```

Every distinction consumed by syntax must be typed.

## 15.3 Clitic and full forms

Do not represent clitic and independent forms as interchangeable strings.

If both exist, the lincat or resource type must make the distinction explicit.

## 15.4 Pronoun validation

Cover:

```text
subject use
direct object
indirect object
prepositional use
clitic use
reflexive use
possessive use
gender-sensitive third person
```

according to implemented scope.

---

# 16. Determiners and articles

## 16.1 Ownership

Determiner/article morphology must have one declared provider.

Possible consumers include:

```text
NounSqi
adjective phrase implementation
StructuralSqi
pronoun/determiner module
```

## 16.2 Required distinctions

As implemented:

```text
definiteness
number
gender
case
deixis
quantification
possessive agreement
```

## 16.3 Definite morphology boundary

If definiteness is realized partly on the noun and partly by a determiner/article:

- the split must be documented;
- category constructors must not apply definiteness twice;
- scenarios must cover bare, indefinite, and definite noun phrases;
- adjective linking/article behavior must be coordinated.

---

# 17. Numerals and quantifiers

Numeral morphology may interact with:

```text
number agreement
case
noun form selection
definiteness
classifier-like syntax
ordinal formation
```

The project must distinguish:

```text
cardinal
ordinal
quantifier
determiner-like numeral
adverbial numeral
```

when the syntax does.

A numeral constructor must not force all governed nouns into one form without documented linguistic justification.

---

# 18. Adverbs and invariant words

`AdverbSqi.gf` and structural modules may contain invariant words.

Invariant lexical items must use explicit structures that make invariance intentional.

Do not infer that a word is invariant merely because one scenario uses only one form.

Morphologically derived adverbs should use a documented derivation rule or explicit lexical constructor.

---

# 19. Proper names

Proper-name handling must document:

```text
capitalization
gender
number behavior
case behavior
definiteness
article behavior
multiword names
foreign orthography
indeclinability
```

A common-noun constructor may be reused only when its behavior matches the name contract.

---

# 20. Multiword morphological units

A lexical item containing multiple tokens requires an explicit design.

Possible models:

```text
fixed invariant phrase
head-inflected phrase
separately inflected components
particle verb
cliticized unit
compound with internal agreement
```

Do not apply single-token suffix operations to a multiword string without identifying the head.

---

# 21. Public paradigm API

## 21.1 Purpose

`ParadigmsSqi.gf` provides stable constructors for lexicon authors.

The API should prioritize:

- safe defaults;
- explicit irregularity;
- typed class selection;
- readable lexical declarations;
- compatibility with category lincats.

## 21.2 Constructor documentation

Every public constructor must define:

```text
name
GF type
category returned
accepted input
inferred properties
default gender/class/etc.
failure behavior
regularity assumptions
examples
irregular alternative
consumers
```

## 21.3 Overloads

Overloads are permitted when each signature has unambiguous meaning.

Avoid overload sets where a one-string constructor and a class-string constructor are indistinguishable.

## 21.4 Defaults

A default is allowed only when:

- it is linguistically reasonable for the documented class;
- it does not conceal frequent irregularity;
- callers can override it;
- the default is stable;
- tests cover it.

Changing a public default is a breaking project API change.

## 21.5 Constructor completeness

A public constructor must return a structure accepted by all documented category consumers.

A constructor that fills missing fields with empty strings is not complete unless empty is the documented semantic value.

---

# 22. Full-form constructors

Every major lexical category should have an escape hatch for explicit forms when regular inference is unsafe.

A full-form constructor should:

- accept typed forms;
- require every necessary table cell;
- preserve inherent features;
- validate internal consistency where GF types permit;
- avoid applying additional regular transformations.

Full-form constructors are the preferred representation for exceptional paradigms.

---

# 23. Irregular morphology registry

Irregular morphology must be discoverable.

The project may use:

```text
explicit lexical entries
named irregular constructors
an irregular resource module
data tables
```

Whichever model is chosen must have:

- one owner;
- deterministic lookup;
- source review;
- validation examples;
- no duplicate conflicting entry.

A hidden exception embedded in a generic suffix helper is prohibited when it applies to one lexical item only.

---

# 24. Defectiveness and missing forms

## 24.1 Explicit representation

A defective paradigm must state:

```text
which cells are unavailable
why they are unavailable
how generation behaves
how analysis behaves
which syntax paths avoid them
```

## 24.2 No fake completeness

Do not fill an unavailable cell with:

- the lemma;
- an arbitrary neighboring form;
- an empty string;
- a generic placeholder;

unless the representation explicitly marks that value as unavailable and consumers handle it safely.

## 24.3 Release visibility

Known defective families must appear in:

```text
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
project/docs/TEST_COVERAGE_MATRIX.md
```

when release-relevant.

---

# 25. Fallback policy

Fallback implementations are allowed only during controlled development.

A fallback must be recorded with:

```text
identifier
owner
affected category
behavior
limitations
reason
validation coverage
replacement plan
release impact
```

Status values may include:

```text
temporary
fallback
warning
blocked
```

A fallback must not be described as complete final morphology.

Release criteria must decide whether it blocks release.

---

# 26. Error behavior

## 26.1 Compile-time failures

Preferred failure mode for an invalid morphology implementation:

```text
GF type or syntax failure
```

Compile errors should expose the provider rather than being patched in downstream modules.

## 26.2 Runtime `Predef.error`

`Predef.error` may be used only for a genuinely impossible or explicitly unsupported branch.

It must not be the normal behavior of a public regular constructor.

Every reachable `Predef.error` in public morphology requires:

- documented precondition;
- scenario or test;
- clear diagnostic text;
- status-ledger review.

## 26.3 Empty forms

An empty string must have documented semantics.

Possible meanings:

```text
zero morph
no overt article
elided element
unsupported form
```

These meanings must not be conflated.

## 26.4 Unsupported input

A constructor receiving unsupported input should:

- fail deterministically; or
- require an explicit class; or
- route to an explicit full-form constructor.

It must not silently choose a random or unrelated class.

---

# 27. Interaction with category lincats

Morphology and lincats form a coordinated contract.

## 27.1 Required documentation

For each category using morphology, document:

```text
lincat type
morphological fields
inherent fields
agreement fields
syntax-only fields
private fields
provider
consumers
```

## 27.2 Field ownership

A field used by more than one module is public.

It must not be renamed or repurposed locally.

## 27.3 Derived fields

A field derivable from another value should not be duplicated unless:

- derivation is expensive or impossible in GF;
- both values have different consumers;
- consistency is validated.

## 27.4 Agreement propagation

Syntax must preserve agreement information until every consumer has used it.

Do not discard gender, number, person, or case early and later infer it from strings.

---

# 28. Interaction with syntax

Morphology provides forms.

Syntax decides composition and ordering unless the morphology is genuinely fused.

Examples normally owned by syntax:

```text
word order
complement order
negation placement
auxiliary sequencing
clitic sequencing
preposition selection
article/adjective ordering
coordination
subordination
```

Examples normally owned by morphology:

```text
inflected word form
stem alternation
suffix selection
agreement-indexed form table
fused form
lexical irregularity
```

Borderline cases require a decision-log entry.

---

# 29. Interaction with the lexicon

Lexicon entries should be declarative.

Preferred pattern:

```text
lemma/principal parts
→ public paradigm constructor
→ complete category value
```

Avoid:

```text
lexical item
→ copied private stem logic
→ manually assembled undocumented record
```

The lexicon may use a low-level constructor only when the dependency is documented.

---

# 30. Module import rules

Allowed direction:

```text
MorphoSqi
→ ParadigmsSqi
→ lexicon/category modules
→ StructuralSqi
→ GrammarSqi
→ LangSqi / AllSqi
```

Normally prohibited:

```text
MorphoSqi → GrammarSqi
MorphoSqi → LangSqi
MorphoSqi → AllSqi
ParadigmsSqi → project lexicon implementation
category module → final API entrypoint
gold file → source logic
scenario → private morphology helper
```

Circular imports are prohibited.

Exceptions require:

```text
DECISION_LOG entry
INTERFILE_CONTRACT_LOCK update
MODULE_DEPENDENCY_MAP update
compile proof
scenario proof
```

---

# 31. Public symbol inventory

The complete public morphology inventory must be generated or reviewed from source.

It must list:

```text
module
symbol
kind: param/oper/resource/interface/instance
GF type
visibility
consumers
contract ID
validation evidence
status
```

The inventory belongs in either:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

This specification does not invent the current symbol list.

A release review must confirm that every cross-module morphology symbol appears in the inventory.

---

# 32. Source annotation policy

Public morphology declarations should have concise comments describing:

```text
linguistic class
input assumptions
forms produced
irregular behavior
consumer expectations
```

Private helpers need comments when the algorithm is non-obvious or linguistically motivated.

Comments must not contradict tests or this specification.

---

# 33. Validation strategy

Morphology validation has five layers.

```text
static review
→ provider compilation
→ consumer compilation
→ GF morphology/runtime scenarios
→ entrypoint/release validation
```

No single layer replaces the others.

---

## 33.1 Static review

GF Wordbench scans for risks including:

```text
runtime string matching
untyped case string patterns
untyped table string patterns
suspicious slash syntax
trailing whitespace
```

A static finding is heuristic.

It must be reviewed but is not itself a GF compile failure.

---

## 33.2 Provider compilation

Required direct compile targets include:

```text
lib/src/albanian/MorphoSqi.gf
lib/src/albanian/ParadigmsSqi.gf
```

and any dedicated morphology providers.

---

## 33.3 Consumer compilation

After a provider change, compile every direct consumer.

At minimum, review applicable:

```text
NounSqi.gf
adjective implementation
verb implementation
pronoun/determiner implementation
lexicon modules
StructuralSqi.gf
GrammarSqi.gf
LangSqi.gf
AllSqi.gf
```

The exact set comes from the dependency map.

---

## 33.4 Runtime scenarios

Required scenario families:

```text
morphology inventory
noun paradigms
adjective agreement
verb paradigms
pronoun/case forms
determiner/article forms
irregular paradigms
defective forms
analysis
generation
entrypoint smoke
```

Scenario IDs and files are declared by `project.toml`.

---

## 33.5 Gold comparison

Stable representative forms should be compared against reviewed gold.

Gold must include:

- scenario contract version;
- normalization version;
- unique scenario ID;
- bounded output;
- no environment-specific paths;
- meaningful Albanian Unicode.

Normal validation is read-only.

---

# 34. Morphology scenario design

## 34.1 Scenario markers

Every morphology scenario must include:

```text
begin marker
section markers
end marker
final completion marker
```

A zero GF exit code without required markers is insufficient.

## 34.2 Form labels

Output should label each requested feature combination explicitly.

Example conceptual format:

```text
NOUN|lemma=<...>|number=sg|def=indef|case=nom|form=<...>
```

The exact text format belongs to the scenario/gold contract.

Labels should use stable technical identifiers.

## 34.3 Bounded generation

Generation must be bounded by:

```text
depth
count
specific function
specific category
```

Unbounded `generate_random` output must not be used for deterministic gold.

## 34.4 Analysis and synthesis

Where GF supports the operation, test both:

```text
features/lemma → form
form → possible analysis
```

Ambiguity is valid evidence and must not be normalized away.

---

# 35. Required noun test matrix

At minimum, representative tests should cover:

| Dimension | Required coverage |
|---|---|
| Gender | every implemented noun gender |
| Number | singular and plural |
| Definiteness | indefinite and definite |
| Case | every syntax-visible case |
| Class | every regular inflection class |
| Irregularity | representative irregular nouns |
| Invariance | invariant noun when supported |
| Defectiveness | singular-only/plural-only when supported |
| Orthography | Albanian-specific letters and alternations |
| Syntax | use in NP/CN contexts |
| Entrypoint | load and linearize through release grammar |

A class without a representative test is not release-complete.

---

# 36. Required adjective test matrix

| Dimension | Required coverage |
|---|---|
| Gender | every implemented agreement gender |
| Number | singular and plural |
| Position | attributive and predicative when supported |
| Linking/article behavior | every implemented class |
| Degree | every supported degree |
| Class | regular classes |
| Irregularity | representative irregular adjective |
| Invariance | invariant class when supported |
| Syntax | AP and NP integration |
| Entrypoint | release grammar behavior |

---

# 37. Required verb test matrix

| Dimension | Required coverage |
|---|---|
| Person | first, second, third |
| Number | singular, plural |
| Tense/aspect | every implemented finite series |
| Mood | every implemented mood |
| Imperative | supported person/number cells |
| Non-finite | every form used by syntax |
| Voice | every implemented voice |
| Class | every regular conjugation class |
| Irregularity | representative irregular verbs |
| Defectiveness | unavailable cells |
| Auxiliaries | every compound construction |
| Negation | representative negative forms |
| Clitics | representative ordering/forms |
| Entrypoint | parse/linearize through final grammar |

---

# 38. Required pronoun/determiner test matrix

Cover every implemented combination of:

```text
person
number
gender
case
clitic/full form
reflexive
possessive
demonstrative
definiteness
```

Only dimensions actually supported may be marked not applicable.

Unsupported dimensions must not be reported as passing.

---

# 39. Round-trip expectations

Round-trip tests are useful but not universally bijective.

Possible checks:

```text
linearize(tree) produces expected form
parse(expected form) includes expected tree
morphological analysis includes expected lemma/features
generation includes expected form
```

A round trip may be ambiguous.

Tests should assert inclusion rather than false uniqueness when the grammar legitimately permits multiple analyses.

---

# 40. Regression selection

Gold coverage should prioritize:

- common regular classes;
- high-frequency irregular forms;
- orthographic alternations;
- table boundaries;
- historical defects;
- constructor defaults;
- forms used by release scenarios;
- categories with downstream cascade risk.

Do not create massive unreviewable gold merely to maximize cell count.

Use smaller labeled sections with complete critical coverage.

---

# 41. Compile checkpoints

Recommended morphology checkpoints:

```text
morphology-core
paradigms-api
noun-morphology
adjective-morphology
verb-morphology
pronoun-determiner
structural-morphology
grammar-entrypoint
release-pgf
```

Actual checkpoint IDs are declared in `project.toml`.

A checkpoint is complete only when its direct provider and declared consumers compile.

---

# 42. Release gates

Morphology-related release gates should include:

```text
all active morphology providers compile
all public paradigm modules compile
all required category consumers compile
all required morphology scenarios pass
all required morphology golds match
no undocumented fallback remains
no release-blocking defective paradigm remains
no required table cell is missing
entrypoints compile
PGF builds
manifest records evidence
```

Warnings may be accepted only when `RELEASE_CRITERIA.md` explicitly permits them.

---

# 43. Diagnostics and root-cause handling

When a morphology provider fails:

- classify the provider failure as direct when evidence supports it;
- classify downstream category or entrypoint failures as downstream;
- record `blocked_by`;
- do not count every cascade as an independent morphology defect.

An error such as:

```text
Cannot find an inflection rule
```

requires inspection of:

```text
provider table completeness
constructor class selection
lexical principal parts
pattern coverage
expected artifact
GF version behavior
```

Do not patch only the final entrypoint.

---

# 44. Known-risk patterns

Review morphology changes carefully when they add:

```text
case on realized strings
table on suffix strings without typed class
duplicate suffix logic
broad wildcard fallback
empty-string default
Predef.error in public path
manual record construction in lexicon
flattened Str lincat
higher-level import
unbounded generation
gold rewrite
```

Each occurrence needs justification or removal.

---

# 45. Performance

Morphology should favor compile-time typed tables over repeated runtime string inspection.

Performance requirements:

- avoid repeated full-string transformations;
- share computed stems when safe;
- avoid exponential constructor composition;
- bound generation scenarios;
- keep public constructors deterministic;
- measure before introducing caches.

A cache must not change semantic output or hide source changes.

---

# 46. Compatibility and versioning

## 46.1 Project patch change

Examples:

- correct one irregular form;
- correct one orthographic helper;
- fix an incorrect table cell;
- improve diagnostics without changing public type.

## 46.2 Project minor change

Examples:

- add a compatible public paradigm;
- add a regular class;
- add optional morphology coverage;
- add a new lexical constructor without changing existing behavior.

## 46.3 Project major change

Examples:

- change a public lincat shape;
- remove or rename a public constructor;
- change parameter meaning;
- change constructor defaults incompatibly;
- remove a supported morphological distinction;
- change release-visible forms incompatibly.

The framework version need not change for a language-project-only morphology change.

---

# 47. Breaking morphology changes

The following require coordinated migration:

```text
public param value change
public table-domain change
record field rename/removal
constructor signature change
constructor default change
new required lincat field
stem semantics change
definiteness ownership move
article ownership move
clitic-order ownership move
case inventory collapse
agreement information removal
normalization change affecting gold
```

Required coordinated files:

```text
provider
all consumers
ParadigmsSqi
lexicon
category lincats
entrypoints
project.toml when checkpoints/scenarios change
scenario files
gold files
dependency map
category/lincat contract
interfile lock
status ledger
decision log
release criteria
```

---

# 48. Morphology change workflow

```text
[ ] Identify linguistic requirement
[ ] Identify authoritative provider
[ ] Identify public/private boundary
[ ] List all consumers
[ ] Update typed parameters/records
[ ] Update low-level helpers
[ ] Update public paradigms
[ ] Update lexical entries
[ ] Update category consumers
[ ] Compile provider
[ ] Compile direct consumers
[ ] Compile entrypoints
[ ] Run morphology scenarios
[ ] Review normalized output
[ ] Update gold explicitly when intended
[ ] Update dependency map
[ ] Update category/lincat contract
[ ] Update interfile contract
[ ] Update status ledger
[ ] Add decision record for breaking changes
[ ] Run release gates
```

---

# 49. Review checklist for a public constructor

```text
[ ] Exact GF type documented
[ ] Category returned is correct
[ ] Inputs are unambiguous
[ ] Regularity assumptions documented
[ ] Default features documented
[ ] Irregular alternative exists
[ ] Unsupported inputs fail deterministically
[ ] No hidden environment dependency
[ ] No duplicated low-level logic
[ ] Result satisfies lincat contract
[ ] Direct compile test exists
[ ] Lexical use example exists
[ ] Scenario coverage exists
[ ] Gold coverage exists when stable
[ ] Consumers are registered
```

---

# 50. Review checklist for an inflection table

```text
[ ] Domain is typed
[ ] Every domain cell is defined
[ ] Table dimensions match linguistic contract
[ ] Inherent features are not duplicated inconsistently
[ ] Defective cells are explicit
[ ] Empty strings have documented semantics
[ ] Orthographic helpers have one owner
[ ] Irregular cells are explicit
[ ] No unsafe broad fallback
[ ] Representative forms are tested
[ ] Downstream lincat fields remain compatible
```

---

# 51. Review checklist for an orthographic helper

```text
[ ] Helper has one provider
[ ] Accepted inputs are documented
[ ] Transformation is deterministic
[ ] Unicode is preserved
[ ] Short input is safe
[ ] Multiword input policy is explicit
[ ] Capitalization policy is explicit
[ ] Failure behavior is explicit
[ ] Consumers are listed
[ ] Duplicate implementations removed
[ ] Unit/scenario examples cover boundaries
```

---

# 52. Status ledger integration

`STATUS_LEDGER.md` must track:

```text
unimplemented inflection class
partial case coverage
partial tense/mood coverage
fallback constructor
known incorrect form
temporary invariant treatment
missing irregular entries
missing scenario coverage
blocked release family
GF-version-specific issue
```

Every entry should include:

```text
ID
status
owner
affected module
affected constructors
user-visible impact
validation evidence
replacement plan
release impact
```

---

# 53. Known-issues integration

A morphology issue belongs in `KNOWN_ISSUES.md` when it:

- affects users;
- affects release output;
- has no immediate fix;
- is GF-version-specific;
- causes ambiguity or missing forms;
- requires linguistic research;
- cannot be safely represented by the current lincat.

Internal refactoring tasks without observable impact may remain in the normal issue tracker.

---

# 54. Research evidence

Linguistic claims used to design a paradigm should be recorded in:

```text
project/docs/RESEARCH_EVIDENCE.md
```

Record:

```text
claim
source
dialect/register
examples
implementation decision
known exceptions
date reviewed
```

Do not encode a broad linguistic rule from one isolated example.

External research must be distinguished from behavior observed in the current GF implementation.

---

# 55. Dialect and register policy

The project must declare its target standard, dialect, and register.

Morphology constructors must not silently mix:

```text
standard and dialectal forms
formal and colloquial forms
archaic and modern forms
regional alternatives
orthographic variants
```

Variants may be supported when:

- represented explicitly;
- documented;
- tested;
- selected deterministically.

---

# 56. Lexical provenance

For irregular or disputed forms, lexical entries should identify provenance through documentation or adjacent structured data.

The source code need not contain long bibliographic notes.

`RESEARCH_EVIDENCE.md` should provide traceability.

---

# 57. Generated inventories

The project should eventually generate read-only inventories from GF or source analysis:

```text
public morphology parameters
public constructors
constructor signatures
lexicon constructor usage
inflection classes
irregular entries
defective paradigms
scenario coverage
gold coverage
```

Generated inventories are evidence.

They do not replace the source or this specification.

---

# 58. Contract-check automation

A future contract checker should verify:

```text
MorphoSqi exists
ParadigmsSqi exists
documented public symbols exist
documented consumers import valid providers
no undocumented public lincat field is consumed
no lower-level module imports entrypoints
all project morphology checkpoints exist
all required morphology scenarios exist
all required gold files exist
normal validation does not modify gold
status-ledger references resolve
```

Recommended command:

```text
gf-wordbench contracts check --strict
```

---

# 59. Required documentation maintenance

A morphology change may require updates to:

| Document | Update trigger |
|---|---|
| `MORPHOLOGY_SPEC.md` | behavior or ownership changes |
| `CATEGORY_AND_LINCAT_CONTRACT.md` | fields, params, lincats change |
| `MODULE_DEPENDENCY_MAP.md` | imports/consumers change |
| `INTERFILE_CONTRACT_LOCK.md` | public boundary changes |
| `SYNTAX_AND_CONSTRUCTOR_RULES.md` | composition/constructor contract changes |
| `VALIDATION_SPEC.md` | scenarios/gates change |
| `TEST_COVERAGE_MATRIX.md` | coverage changes |
| `STATUS_LEDGER.md` | temporary/partial status changes |
| `DECISION_LOG.md` | breaking or disputed design decision |
| `KNOWN_ISSUES.md` | unresolved user-visible defect |
| `RELEASE_CRITERIA.md` | release gate changes |
| `RESEARCH_EVIDENCE.md` | linguistic claim changes |

---

# 60. Anti-drift indicators

Probable morphology drift exists when:

- `ParadigmsSqi` duplicates logic from `MorphoSqi`;
- a lexicon module manually constructs a private morphology record;
- a consumer patterns on an undocumented parameter;
- a lincat field changes in one file only;
- an entrypoint contains local inflection logic;
- two helpers implement the same suffix transformation differently;
- a one-form constructor silently changes class inference;
- a new parameter value leaves tables incomplete;
- a runtime string match replaces a typed class;
- an empty string represents both zero morphology and unsupported form;
- an irregular form is fixed only in gold;
- a gold file changes during normal validation;
- a downstream compile failure is counted as a separate root morphology failure;
- the dependency map omits a morphology consumer;
- the status ledger claims complete behavior while a fallback remains;
- a source form uses non-canonical Unicode;
- a scenario covers only one table cell but release claims full class coverage;
- `MorphoSqi` imports `GrammarSqi`, `LangSqi`, or `AllSqi`;
- a public constructor lacks an explicit irregular alternative;
- the source and category/lincat documentation list different table domains.

Any drift indicator requires provider/consumer review.

---

# 61. Completion criteria

The morphology subsystem is complete for a release only when:

```text
[ ] Authoritative providers are identified
[ ] Public symbol inventory is current
[ ] Parameter inventory is current
[ ] Lincat contract is current
[ ] Dependency map is current
[ ] All active regular classes have representative tests
[ ] Required irregular classes have representative tests
[ ] Defective behavior is explicit
[ ] Provider modules compile
[ ] Direct consumers compile
[ ] Entry points compile
[ ] Required scenarios pass
[ ] Required golds match
[ ] No undocumented fallback remains
[ ] No release-blocking known issue remains
[ ] PGF builds
[ ] Manifest contains required evidence
[ ] Release criteria approve morphology coverage
```

---

# 62. Current evidence limitations

The available project evidence confirms:

- Albanian source location under `lib/src/albanian/`;
- the existence or use of `MorphoSqi.gf`;
- the existence or use of `ParadigmsSqi.gf`;
- the existence or use of `NounSqi.gf`;
- the use of `CatSqi.gf`, `GrammarSqi.gf`, `StructuralSqi.gf`, `AdverbSqi.gf`, `ExtendSqi.gf`, `LangSqi.gf`, and `AllSqi.gf`;
- an active morphology-to-paradigms contract;
- an active paradigms-to-lexicon contract;
- risks involving runtime string matching and untyped string patterns;
- the requirement for compile, scenario, generation, and gold evidence.

The available evidence does not expose the complete current source declarations.

Therefore, this document intentionally does not assert exact existing:

```text
param names
param value names
record field names
constructor names
constructor arities
complete tense inventory
complete case table shape
complete irregular lexicon
```

Those details must be extracted from the active source and entered into the project contract inventory before a release claims the documentation is fully synchronized.

This limitation is a documentation synchronization task, not permission to invent source APIs.

---

# 63. Source synchronization procedure

To synchronize exact morphology symbols:

1. enumerate public declarations in `MorphoSqi.gf`;
2. enumerate public declarations in `ParadigmsSqi.gf`;
3. enumerate imports and qualified uses in direct consumers;
4. enumerate lincat fields consumed outside their provider;
5. enumerate constructor use in lexicon modules;
6. identify irregular and defective entries;
7. map each symbol to a contract ID;
8. update `CATEGORY_AND_LINCAT_CONTRACT.md`;
9. update `INTERFILE_CONTRACT_LOCK.md`;
10. update scenario coverage;
11. compile all direct consumers;
12. run required morphology scenarios;
13. review gold;
14. mark the inventory reviewed with source revision and date.

---

# 64. Final rule

Morphology is a shared project contract, not a collection of local string operations.

> `MorphoSqi` must provide typed, complete, and documented morphological structures; `ParadigmsSqi` must expose safe lexical constructors; category and syntax modules must preserve the distinctions they consume; and every public change must be proven through GF compilation, representative scenarios, and reviewed regression evidence.

A form is not correct because it compiles in one file.

It is correct only when:

```text
the provider contract is coherent
the consumer contract is preserved
GF accepts the implementation
representative morphology behaves as intended
entrypoints remain valid
release evidence remains traceable
```
