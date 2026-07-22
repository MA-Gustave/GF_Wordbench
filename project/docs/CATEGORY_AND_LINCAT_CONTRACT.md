# GF Wordbench — Albanian Category and Lincat Contract

**Document ID:** `GF-WB-PROJECT-CATEGORY-LINCAT-CONTRACT`  
**Status:** Normative  
**Applies to:** Active Albanian GF project (`sqi`, module suffix `Sqi`)  
**Project owner:** Gustave (pseudonym), owner of the Mécanismes Abstraits GitHub account  
**Primary interfile contracts:** `PIFC-LINCAT-001`, `PIFC-LINCAT-002`, `PIFC-DOC-002`  
**Contract version:** `1.0.0`  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\project\docs\CATEGORY_AND_LINCAT_CONTRACT.md`  
**Last structural review:** 2026-07-22

---

## 1. Purpose

This document locks the concrete category and lincat contracts of the active Albanian GF project.

It defines:

- the authoritative providers of Albanian lincats;
- resource-level parameters and implementation records;
- the current concrete shape of each important category;
- the fields that consumers may rely on;
- the fields consumers must preserve;
- the boundary between rich and shallow categories;
- the difference between lincat shape and constructor availability;
- approved producer modules;
- exact helper-compatibility rules;
- complement, agreement, case, clitic, and numeral invariants;
- current warning and blocked construction zones;
- validation evidence required for contract changes;
- anti-drift rules.

The central rule is:

> A category is not correctly implemented merely because it linearizes to a plausible string; every producer and consumer must preserve the complete current Albanian lincat contract until an explicit, coordinated contract change replaces it.

A second rule is equally important:

> Knowing that a category currently has shape `{s : Str}` does not prove that an arbitrary local `lin Category {s = ...}` constructor is valid in every module context.

---

## 2. Project identity

| Field | Value |
|---|---|
| Language | Albanian |
| Project/language code | `sqi` |
| GF module suffix | `Sqi` |
| Category provider | `SRC/CatSqi.gf` |
| Resource-type provider | `SRC/ResSqi.gf` |
| Current source-root evidence | `lib/src/albanian` |
| Canonical source-root authority | `project/project.toml` |
| Project contract lock | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Architecture owner | `project/docs/LANGUAGE_ARCHITECTURE.md` |
| Morphology owner | `project/docs/MORPHOLOGY_SPEC.md` |
| Constructor-policy owner | `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| Temporary-status owner | `project/docs/STATUS_LEDGER.md` |
| Validation owner | `project/docs/VALIDATION_SPEC.md` |

In this document:

```text
SRC
```

means the project source directory resolved from `project/project.toml`.

For the current imported Albanian source snapshot:

```text
SRC = lib/src/albanian
```

The project configuration remains authoritative if the source tree is relocated without changing module identity.

---

## 3. Scope

This contract governs:

- resource parameters used by cross-module category records;
- resource record types imported by `CatSqi.gf`;
- lincats declared in `CatSqi.gf`;
- category-specific record fields;
- producer-owned list categories;
- producer-owned local auxiliary categories when consumed across files;
- category-preserving constructors;
- deliberate reduction boundaries;
- helper signatures that cross module boundaries;
- construction of shallow categories where module context matters;
- consumer assumptions;
- compile, scenario, gold, and review evidence.

It applies to modules including:

```text
CatSqi.gf
ResSqi.gf
MorphoSqi.gf
ParadigmsSqi.gf
NounSqi.gf
AdjectiveSqi.gf
VerbSqi.gf
SentenceSqi.gf
QuestionSqi.gf
RelativeSqi.gf
AdverbSqi.gf
ConjunctionSqi.gf
NumeralSqi.gf
StructuralSqi*.gf
ExtendSqi*.gf
GrammarSqi.gf
LangSqi.gf
```

The actual module inventory is owned by `MODULE_DEPENDENCY_MAP.md` and the source tree.

---

## 4. Non-scope

This document does not:

- redefine abstract RGL signatures;
- define complete Albanian morphology;
- define every constructor implementation;
- define every lexical entry;
- define scenario IDs or gold content;
- guarantee that a record literal is constructible in every GF module;
- treat historical comments as authoritative;
- redesign the current Albanian grammar toward an idealized future model;
- authorize flattening solely for implementation convenience;
- replace the GF compiler.

Exact abstract signatures remain authoritative in the abstract grammar and imported RGL modules.

GF remains authoritative for type checking and constructor acceptance.

---

## 5. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **CATEGORY PROVIDER**: module declaring or supplying the concrete category shape.
- **PRODUCER**: module constructing values of a category.
- **CONSUMER**: module reading fields or accepting values of a category.
- **RICH CATEGORY**: category whose current lincat preserves grammatical dimensions beyond one surface string.
- **SHALLOW CATEGORY**: category whose current lincat is surface-oriented, usually `{s : Str}`.
- **CATEGORY-PRESERVING**: retains every field and table dimension required by the target lincat.
- **LOSSY PROJECTION**: extracts one or more surface forms while discarding part of a rich value.
- **REDUCTION BOUNDARY**: category transition where loss of rich structure is intentional and documented.
- **CONSTRUCTOR AVAILABILITY**: proof that a construction pattern is accepted in the current GF module context.
- **PRODUCER-FIRST**: use an established category owner or paradigm constructor before manufacturing a local record.
- **COMPATIBILITY BUILDER**: explicitly limited fallback that does not establish a canonical category-preserving pattern.
- **LOCK FIELD**: hidden or explicit field required by GF’s concrete-category representation or inherited contract.
- **CURRENT SOURCE TRUTH**: current source plus current GF compile behavior.
- **STALE COMMENT**: comment contradicted by current source or compiler evidence.

---

## 6. Authority and precedence

When evidence disagrees, use this order:

1. exact abstract signature;
2. current GF compiler behavior in the actual module context;
3. current `SRC/CatSqi.gf` lincat definition;
4. current `SRC/ResSqi.gf` parameter and record definitions;
5. current Albanian producer-module patterns;
6. current project interfile contract lock;
7. current validation artifacts and `.gfo` evidence;
8. this document;
9. status ledger and decision log;
10. historical comments and notes.

This ordering has two consequences.

First:

```text
documented shape ≠ guaranteed local constructor availability
```

Second:

```text
historical comment ≠ current category contract
```

A current compile failure overrides a construction assumption.

It does not silently rewrite the lincat contract; instead, the construction path must be corrected or the contract must be changed deliberately.

---

## 7. Contract ownership

### 7.1 `PIFC-LINCAT-001` — Category lincat ownership

**Provider**

```text
SRC/CatSqi.gf
```

**Supporting provider**

```text
SRC/ResSqi.gf
```

**Consumers**

All concrete modules importing or inheriting Albanian categories.

**Locked promise**

Every consumer may rely only on lincats and fields documented here and present in the current providers.

No consumer may rely on an undocumented field, parameter constructor, table axis, or local category projection.

---

### 7.2 `PIFC-LINCAT-002` — Parameter and record ownership

**Provider**

```text
SRC/ResSqi.gf
```

**Consumers**

```text
SRC/CatSqi.gf
morphology modules
paradigm modules
noun/adjective/verb modules
sentence and adverb modules
structural and extension modules that use the exported resource API
```

**Locked promise**

The parameter domains and record fields documented in Section 10 remain stable across consumers.

A change requires complete consumer review.

---

### 7.3 `PIFC-DOC-002` — Documentation synchronization

**Provider**

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

**Consumers**

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/STATUS_LEDGER.md
project/docs/VALIDATION_SPEC.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

**Locked promise**

This file reflects the current category and lincat implementation.

A lincat change is incomplete until this document and all affected consumers are updated.

---

## 8. Two independent status systems

This document uses two distinct status systems.

### 8.1 Lincat-contract status

```text
Active
Experimental
Deprecated
Retired
```

This answers:

```text
Is the category shape part of the active contract?
```

### 8.2 Construction status

```text
stable
conditional
warning
fallback-only
blocked
```

This answers:

```text
How safely may this category be manufactured in local modules?
```

A category can therefore be:

```text
lincat status = Active
construction status = warning
```

`DConj` and `Prep` are important examples.

---

## 9. Global invariants

```text
INV-CAT-001 `CatSqi.gf` owns base Albanian lincats.
INV-CAT-002 `ResSqi.gf` owns shared resource parameters and record types.
INV-CAT-003 Consumers depend only on documented fields and table dimensions.
INV-CAT-004 Rich categories are not flattened to `Str` for convenience.
INV-CAT-005 Shallow shape does not grant universal local-constructor permission.
INV-CAT-006 Exact category identity is stronger than family resemblance.
INV-CAT-007 A helper typed for `A` is not automatically valid for `AP`.
INV-CAT-008 A helper typed for `N` or `CN` is not automatically valid for `NP`.
INV-CAT-009 `Pron` is not interchangeable with generic `NP`.
INV-CAT-010 Complement slots `c2` and `c3` are preserved.
INV-CAT-011 `NP` agreement is preserved.
INV-CAT-012 Pronoun clitic fields are preserved.
INV-CAT-013 Rich list categories preserve their own list records.
INV-CAT-014 Preposition government follows the current Albanian producer path.
INV-CAT-015 Reduction occurs only at documented target categories.
INV-CAT-016 Static comments do not override source and compile truth.
INV-CAT-017 Lock-field warnings are contract evidence, not cosmetic noise.
INV-CAT-018 Every breaking lincat change updates all direct and downstream consumers.
INV-CAT-019 Every category-contract change has compile and scenario evidence.
INV-CAT-020 Temporary compatibility builders are registered and bounded.
```

---

# 10. Resource-level parameter contract

The following parameter constructors are current active contracts of `ResSqi.gf`.

## 10.1 `Species`

```gf
param Species = Indef | Def ;
```

Meaning:

- `Indef`: indefinite nominal realization;
- `Def`: definite nominal realization.

Consumers include:

- `Noun`;
- `Quant`;
- `Det`;
- `AP`;
- `CN`;
- `ListCN`;
- `ListAP`;
- `ListDAP`.

Changing constructor names, count, or meaning is breaking.

---

## 10.2 `Case`

```gf
param Case = Nom | Acc | Dat | Ablat ;
```

Meaning:

- `Nom`: nominative;
- `Acc`: accusative;
- `Dat`: dative;
- `Ablat`: ablative.

Consumers include:

- noun morphology;
- adjectives;
- noun phrases;
- pronouns;
- determiners;
- quantifiers;
- prepositional NP realization;
- rich list categories.

A case change requires review of every table indexed by `Case`.

---

## 10.3 `Gender`

```gf
param Gender = Masc | Fem ;
```

Consumers include:

- `Noun.g`;
- adjective tables;
- determiner tables;
- quantifier tables;
- agreement;
- rich noun/adjective list categories.

---

## 10.4 `GenNum`

```gf
param GenNum = GSg Gender | GPl ;
```

`GenNum` combines singular gender with a plural state.

It is not equivalent to storing independent `Gender` and `Number` fields.

Consumers must not deconstruct or reconstruct it inconsistently.

---

## 10.5 `Tense`

```gf
param Tense = Pres | Past | Imperfect | Aorist ;
```

This is the current resource-level verb tense contract.

The complete interpretation is owned by `MORPHOLOGY_SPEC.md`.

Changing the tense inventory or meaning is breaking for `Verb` and its consumers.

---

## 10.6 Imported parameters

The current records also use imported RGL parameters including:

```text
Number
Person
Bool
```

The project does not redefine those values here.

Consumers use the exact imported parameter contracts available in the current module graph.

---

# 11. Shared resource records

## 11.1 `Agr`

```gf
Agr = {
  gn : GenNum ;
  p  : Person
}
```

**Provider**

```text
SRC/ResSqi.gf
```

**Consumers**

```text
NP
Pron
ListNP
noun and pronoun constructors
sentence agreement logic
```

**Invariants**

- `gn` is always present;
- `p` is always present;
- agreement must not be replaced by a surface string;
- third-person nominal agreement should use the established helper where appropriate.

Current helper:

```gf
agrgP3 : Gender -> Number -> Agr
```

---

## 11.2 `Compl`

```gf
Compl = {
  s : Str
}
```

`Compl` is the current complement record.

It is also the current underlying type of `Prep`.

The shallow shape does not erase producer ownership.

---

## 11.3 `Prep`

```gf
Prep = Compl
```

This resource alias is current implementation truth.

It does not authorize arbitrary preposition construction outside verified module contexts.

Approved producer/composition paths include:

```text
ResSqi.mkPrep
AdverbSqi.PrepNP
```

---

## 11.4 `Noun`

```gf
Noun = {
  s : Species => Case => Number => Str ;
  g : Gender
}
```

**Fields**

| Field | Meaning | Required consumers |
|---|---|---|
| `s` | complete nominal inflection table | `N`, `N2`, `N3`, `CN`, noun constructors |
| `g` | lexical gender | determiners, agreement, adjectives, lists |

**Invariants**

- every `Species`, `Case`, and `Number` cell is contractually meaningful;
- `g` is not derivable from one surface form;
- a single surface string is not a valid replacement for `Noun`;
- `CN` and `N` currently share this shape.

---

## 11.5 `Adj`

```gf
Adj = {
  s    : Case => Gender => Number => Str ;
  clit : Bool
}
```

**Fields**

| Field | Meaning |
|---|---|
| `s` | adjective inflection table |
| `clit` | current adjective clitic/placement behavior flag |

`Adj` is the lincat of lexical adjective category `A`.

It is not the lincat of `AP`.

---

## 11.6 `Verb`

```gf
Verb = {
  Indicative       : Tense => Number => Person => Str ;
  Imperative       : Number => Str ;
  participle       : Str ;
  pres_optative    : Number => Person => Str ;
  perf_optative    : Number => Person => Str ;
  pres_admirative  : Number => Person => Str ;
  imperf_admirative: Number => Person => Str
}
```

**Invariants**

- every documented field remains present;
- indicative tense/person/number structure is preserved;
- imperative structure is preserved;
- participle and non-indicative paradigms are not silently dropped;
- lexical verb categories use this record or an explicit extension containing it.

---

## 11.7 `Pron`

```gf
Pron = {
  s        : Case => Str ;
  acc_clit : Str ;
  dat_clit : Str ;
  a        : Agr
}
```

**Invariants**

- all case forms are preserved;
- accusative clitic is preserved;
- dative clitic is preserved;
- agreement is preserved;
- a generic `NP` value is not automatically a valid `Pron`.

---

## 11.8 `Quant`

```gf
Quant = {
  s    : Case => Gender => Number => Str ;
  spec : Species
}
```

`spec` determines nominal species behavior and must not be discarded.

---

## 11.9 `Det`

```gf
Det = {
  s    : Case => Gender => Str ;
  n    : Number ;
  spec : Species
}
```

`Det` fixes number through `n` and species through `spec`.

Consumers must not reconstruct those values from one realized string.

---

# 12. Base lincat registry

All categories in this section have lincat-contract status:

```text
Active
```

unless stated otherwise.

The construction status describes local manufacturing, not category existence.

---

## 12.1 Noun-family and lexical categories

| Category | Current lincat | Required fields/dimensions | Primary provider | Construction status |
|---|---|---|---|---|
| `N` | `Noun` | `s[Species,Case,Number]`, `g` | `CatSqi` + `ResSqi` | producer-first |
| `N2` | `Noun ** {c2 : Compl}` | all `Noun` fields, `c2` | `CatSqi` + noun producers | producer-first |
| `N3` | `Noun ** {c2,c3 : Compl}` | all `Noun` fields, `c2`, `c3` | `CatSqi` + noun producers | producer-first |
| `CN` | `Noun` | `s[Species,Case,Number]`, `g` | `CatSqi`, `NounSqi` | producer-first |
| `NP` | `{s : Case => Str ; a : Agr}` | case table, agreement | `CatSqi`, `NounSqi` | rich; local flattening forbidden |
| `Pron` | `Pron` resource record | case table, clitics, agreement | `CatSqi`, pronoun producers | rich; generic NP substitution forbidden |
| `Det` | `Det` resource record | case/gender table, number, species | `CatSqi`, noun/structural producers | producer-first |
| `Quant` | `Quant` resource record | case/gender/number table, species | `CatSqi`, noun/structural producers | producer-first |
| `Num` | `{s : Str ; n : Number}` | surface, number | `CatSqi`, numeral producers | conditional |
| `Card` | `{s : Str}` | surface | `CatSqi`, numeral producers | conditional |
| `ACard` | `{s : Str}` | surface | `CatSqi`, numeral producers | conditional |
| `Ord` | `{s : Str}` | surface | `CatSqi`, numeral producers | conditional |
| `Predet` | `{s : Str}` | surface | `CatSqi`, structural producers | conditional |
| `DAP` | `{s : Str}` | surface | `CatSqi` | warning |
| `GN` | `{s : Str}` | surface | `CatSqi` | conditional |
| `LN` | `{s : Str}` | surface | `CatSqi` | conditional |
| `PN` | `{s : Str}` | surface | `CatSqi`, paradigms/lexicon | producer-first |
| `SN` | `{s : Str}` | surface | `CatSqi` | conditional |

### Noun-family invariants

- `N` and `CN` currently share `Noun`.
- `N2` and `N3` extend rather than replace `Noun`.
- `NP` preserves case and agreement.
- `Pron` preserves additional clitic fields.
- `Det` and `Quant` are not interchangeable.
- `Num`, `Card`, `ACard`, `Ord`, and `DAP` must not be treated as one generic surface category.
- shallow noun-related categories still require category-correct producers.

---

## 12.2 Adjective-family categories

| Category | Current lincat | Required fields/dimensions | Primary provider | Construction status |
|---|---|---|---|---|
| `A` | `Adj` | `s[Case,Gender,Number]`, `clit` | `CatSqi`, `ResSqi`, `AdjectiveSqi` | producer-first |
| `A2` | `Adj ** {c2 : Compl}` | all `Adj` fields, `c2` | `CatSqi`, `AdjectiveSqi` | producer-first |
| `AP` | `{s : Species => Case => Gender => Number => Str}` | all four table axes | `CatSqi`, `AdjectiveSqi` | rich; local flattening forbidden |

### Adjective-family invariants

```text
A ≠ AP
A2 ≠ A
```

An `A -> Str` helper is not compatible with an `AP` input.

An `AP` surface extractor must accept `AP` and choose cells intentionally.

A constructor returning `AP` must preserve:

```text
Species
Case
Gender
Number
```

unless the lincat contract itself is changed.

---

## 12.3 Verb-family categories

| Category | Current lincat | Required fields/dimensions | Primary provider | Construction status |
|---|---|---|---|---|
| `V` | `Verb` | full verb record | `CatSqi`, paradigms, `VerbSqi` | producer-first |
| `VA` | `Verb` | full verb record | same | producer-first |
| `VV` | `Verb` | full verb record | same | producer-first |
| `VS` | `Verb` | full verb record | same | producer-first |
| `VQ` | `Verb` | full verb record | same | producer-first |
| `V2` | `Verb ** {c2 : Compl}` | full verb record, `c2` | `CatSqi`, `VerbSqi` | producer-first |
| `V2S` | `Verb ** {c2 : Compl}` | full verb record, `c2` | same | producer-first |
| `V2Q` | `Verb ** {c2 : Compl}` | full verb record, `c2` | same | producer-first |
| `V3` | `Verb ** {c2,c3 : Compl}` | full verb record, `c2`, `c3` | same | producer-first |
| `V2A` | `Verb ** {c2,c3 : Compl}` | full verb record, `c2`, `c3` | same | producer-first |
| `V2V` | `Verb ** {c2,c3 : Compl}` | full verb record, `c2`, `c3` | same | producer-first |
| `VP` | `{s : Str}` | surface | `CatSqi`, `VerbSqi` | conditional |
| `VPSlash` | `{s : Str}` | surface | `CatSqi`, `VerbSqi` | conditional |
| `Comp` | `{s : Str}` | surface | `CatSqi`, `VerbSqi` | conditional; approved reduction target |

### Verb-family invariants

- lexical verb categories remain rich;
- complement-bearing lexical verbs preserve complement records;
- `VP`, `VPSlash`, and `Comp` are current reduction-level categories;
- reduction to `Comp` is intentional;
- rich inputs must not be flattened earlier merely because the final `Comp` is shallow.

Current producer evidence includes:

```gf
CompNP  np  = {s = npNom np} ;
CompAP  ap  = {s = apPred ap} ;
CompCN  cn  = {s = cnPred cn} ;
CompAdv adv = {s = adv.s} ;
UseComp c   = {s = join copula c.s} ;
```

These patterns establish `Comp` as a documented reduction boundary.

---

## 12.4 Clause, sentence, question, and relative categories

| Category | Current lincat | Primary owner | Construction status |
|---|---|---|---|
| `S` | `{s : Str}` | `CatSqi`, `SentenceSqi` | conditional |
| `QS` | `{s : Str}` | `CatSqi`, `QuestionSqi` | conditional |
| `RS` | `{s : Str}` | `CatSqi`, `RelativeSqi` | conditional |
| `SSlash` | `{s : Str}` | sentence/slash producers | conditional |
| `Cl` | `{s : Str}` | `CatSqi`, `SentenceSqi` | conditional |
| `QCl` | `{s : Str}` | `CatSqi`, `QuestionSqi` | conditional |
| `RCl` | `{s : Str}` | `CatSqi`, `RelativeSqi` | conditional |
| `RP` | `{s : Str}` | relative producers | conditional |
| `ClSlash` | `{s : Str}` | slash producers | conditional |
| `IComp` | `{s : Str}` | question producers | conditional |
| `IP` | `{s : Str}` | question producers | conditional |
| `IDet` | `{s : Str}` | question producers | conditional |
| `IQuant` | `{s : Str}` | question producers | conditional |
| `Subj` | `{s : Str}` | paradigms/structural producers | conditional |
| `Conj` | `{s : Str}` | paradigms/conjunction producers | conditional |
| `PConj` | surface record equivalent | paradigms/structural producers | conditional |
| `DConj` | `{s : Str}` | structural clause producer | warning; known local constructor blocked |
| `Imp` | `{s : Str}` | verbal/sentence producers | conditional |
| `Utt` | `{s : Str}` in current use | utterance producers | stable shallow target |
| `Voc` | surface-oriented category | structural producers | conditional |

### Upper-layer invariants

- current flattening is implementation truth, not a universal RGL claim;
- sentence and clause construction remains producer-owned;
- an arbitrary local record is not preferred over a current sentence/question/relative constructor;
- `DConj` is not treated as universally constructible from its visible shape;
- a shallow output does not permit incorrect rich-input handling.

Current sentence evidence includes:

```gf
PredVP np vp = {
  s = np.s ! Nom ++ sep ++ vp.s
}
```

This confirms nominative subject realization at this sentence-layer boundary.

---

## 12.5 Adverbial and prepositional categories

| Category | Current lincat/use | Primary owner | Construction status |
|---|---|---|---|
| `Prep` | `Compl = {s : Str}` | `ResSqi`, `AdverbSqi`, paradigms | warning / producer-first |
| `Adv` | surface-used as `{s : Str}` | `AdverbSqi` | conditional |
| `AdV` | surface-used as `{s : Str}` | adverb producers | conditional |
| `AdA` | surface-used as `{s : Str}` | adverb/adjective producers | conditional |
| `AdN` | surface-used as `{s : Str}` | adverb/noun producers | conditional |
| `IAdv` | surface-used as `{s : Str}` | question/adverb producers | conditional |
| `CAdv` | local surface record behavior | comparative-adverb producers | stable only in verified context |

### Preposition invariants

Current canonical composition evidence:

```gf
PrepNP p np = {
  s = p.s ++ npAfterPrep p np
}
```

Current default NP realization after preposition:

```gf
npAfterPrep : Prep -> NP -> Str = \_,np -> np.s ! Acc
```

Therefore:

```text
current default case after Prep = Acc
```

A new preposition-bearing constructor must not invent a different case policy without:

- source evidence;
- explicit architecture decision;
- affected scenario review;
- gold review.

The current shallow runtime type does not erase preposition producer ownership.

---

## 12.6 Numeral and digit categories

| Category | Current lincat | Required fields | Primary owner | Construction status |
|---|---|---|---|---|
| `Numeral` | `{s : Str}` | `s` | numeral grammar | conditional |
| `Digits` | `{s : Str ; n : Number ; tail : DTail}` | `s`, `n`, `tail` | numeral/digit grammar | conditional |
| `Decimal` | `{s : Str ; n : Number ; hasDot : Bool}` | `s`, `n`, `hasDot` | numeral/digit grammar | conditional |

### Numeral invariants

- `Digits` is not a plain string;
- `Decimal` is not a plain string;
- `Numeral`, `Digits`, `DAP`, and `Num` remain distinct categories;
- digit-tail and decimal-dot state must be preserved;
- numeral producers own canonical construction.

---

# 13. Producer-owned auxiliary categories

These categories are not base `CatSqi.gf` facts unless explicitly declared there.

They are nevertheless contractual when consumed across modules.

---

## 13.1 Conjunction-owned list categories

**Provider**

```text
SRC/ConjunctionSqi.gf
```

| Category | Concrete shape | Preservation rule | Construction status |
|---|---|---|---|
| `ListS` | `{init : Str ; last : Str}` | preserve two-part list | stable producer-owned |
| `ListNP` | `{init : Case => Str ; last : Case => Str ; a : Agr}` | preserve case tables and agreement | rich |
| `ListCN` | `{init : Species => Case => Number => Str ; last : Species => Case => Number => Str ; g : Gender}` | preserve nominal tables and gender | rich |
| `ListAP` | `{init : Species => Case => Gender => Number => Str ; last : Species => Case => Gender => Number => Str}` | preserve AP tables | rich |
| `ListAdv` | `{init : Str ; last : Str}` | preserve list structure | stable producer-owned |
| `ListAdV` | `{init : Str ; last : Str}` | preserve list structure | stable producer-owned |
| `ListIAdv` | `{init : Str ; last : Str}` | preserve list structure | stable producer-owned |
| `ListRS` | `{init : Str ; last : Str}` | preserve list structure | stable producer-owned |
| `ListDAP` | `{init : Str ; last : Str ; spec : Species ; n : Number}` | preserve species and number | custom producer-owned |

### List invariants

```text
ListNP ≠ NP
ListCN ≠ CN
ListAP ≠ AP
ListDAP ≠ generic shallow list
```

A list constructor must preserve `init` and `last`.

Rich list categories must not be collapsed before the conjunction layer has completed its contract.

---

## 13.2 Question-owned `QVP`

**Provider**

```text
SRC/QuestionSqi.gf
```

Current local shape:

```gf
QVP = {s : Str}
```

`QVP` is a question-layer auxiliary category.

It must not be documented or consumed as a base `CatSqi.gf` lincat unless it is deliberately promoted through a contract change.

---

## 13.3 Extension-owned categories

Extension modules may contain local categories including:

```text
VPS
VPI
VPS2
VPI2
X
extension-specific list wrappers
```

Rules:

- local extension shapes remain extension-owned;
- they do not redefine base Albanian categories;
- inheritance policy remains authoritative;
- inherited families must not be reopened casually;
- cross-module consumption requires documentation in the project lock;
- temporary compatibility wrappers belong in the status ledger.

---

# 14. Provider and consumer map

| Contract surface | Authoritative provider | Major consumers |
|---|---|---|
| Parameter inventory | `ResSqi.gf` | `CatSqi`, morphology, syntax modules |
| `Agr` | `ResSqi.gf` | `NP`, `Pron`, `ListNP`, sentence logic |
| `Noun` | `ResSqi.gf` | `CatSqi`, `NounSqi`, paradigms, lexicon |
| `Adj` | `ResSqi.gf` | `CatSqi`, `AdjectiveSqi`, paradigms |
| `Verb` | `ResSqi.gf` | `CatSqi`, `VerbSqi`, paradigms |
| `Pron` record | `ResSqi.gf` | `CatSqi`, pronoun/structural modules |
| `Quant` record | `ResSqi.gf` | `CatSqi`, noun/structural modules |
| `Det` record | `ResSqi.gf` | `CatSqi`, `NounSqi`, structural modules |
| Base lincats | `CatSqi.gf` | all concrete syntax modules |
| Nominal construction | `NounSqi.gf` | grammar, structural, extension layers |
| AP construction | `AdjectiveSqi.gf` | noun, verb, extension layers |
| Verb and `Comp` construction | `VerbSqi.gf` | sentence, question, extension layers |
| Clause/sentence construction | `SentenceSqi.gf` | question, relative, grammar entrypoint |
| Interrogative construction | `QuestionSqi.gf` | grammar/extension entrypoints |
| Relative construction | `RelativeSqi.gf` | grammar/extension entrypoints |
| Preposition composition | `AdverbSqi.gf` | structural and extension modules |
| Rich list construction | `ConjunctionSqi.gf` | coordination consumers |
| Numeral/digit construction | numeral modules | noun, structural, lexicon consumers |
| Structural inventory | `StructuralSqi*.gf` | language/grammar entrypoints |
| Extension behavior | `ExtendSqi*.gf` | extension coordinator/entrypoint |

A consumer must not create a second canonical provider for one of these surfaces without an ownership migration.

---

# 15. Canonical producer evidence

This section records important current patterns that define category behavior.

## 15.1 `DetCN`

```gf
DetCN det cn = {
  s = \c =>
    det.s ! c ! cn.g
    ++ cn.s ! det.spec ! c ! det.n ;
  a = agrgP3 cn.g det.n
}
```

Contract implications:

- determiner gender selection uses `cn.g`;
- noun selection uses determiner species and number;
- result is case-sensitive;
- result agreement is constructed from noun gender and determiner number.

---

## 15.2 `AdjCN`

```gf
AdjCN ap cn = {
  s = \spec,c,n =>
    cn.s ! spec ! c ! n
    ++ ap.s ! spec ! c ! cn.g ! n ;
  g = cn.g
}
```

Contract implications:

- `CN` structure is preserved;
- adjective agreement uses CN gender;
- AP species, case, gender, and number axes are consumed;
- result gender remains CN gender.

---

## 15.3 Identity-style category constructors

Current evidence includes:

```gf
UseN n = n
UsePron p = p
```

An identity constructor preserves the complete record.

It must not be replaced by a partial reconstruction unless required by a deliberate contract change.

---

## 15.4 `AP` producers

`PositA`, `ComplA2`, and `SentAP` establish that `AP` remains a complete four-axis table.

A new AP-returning constructor must follow category-preserving patterns rather than one-cell extraction.

---

## 15.5 `Comp` reduction

The `CompNP`, `CompAP`, `CompCN`, and `CompAdv` family establishes an intentional lossy transition into a shallow target.

This is an approved reduction because:

```text
target category = Comp
Comp lincat = {s : Str}
```

It does not authorize returning a string record where the target is `NP`, `CN`, or `AP`.

---

## 15.6 Sentence reduction

`PredVP` establishes nominative subject extraction at a sentence construction boundary.

The input `NP` remains rich before that boundary.

---

## 15.7 Prepositional NP realization

`PrepNP` and `npAfterPrep` establish:

- preposition surface concatenation;
- accusative NP selection in the current default implementation.

This is the canonical current path unless explicitly superseded.

---

# 16. Rich-category preservation rules

## 16.1 `CN`

Must preserve:

```text
Species
Case
Number
Gender
```

Forbidden:

```gf
lin CN {s = someString}
```

when the actual target requires `Noun`.

Also forbidden:

- rebuilding a CN from one nominal cell;
- discarding `g`;
- using one fixed species/case/number form as the whole category.

---

## 16.2 `AP`

Must preserve:

```text
Species
Case
Gender
Number
```

Forbidden:

- treating nominative masculine singular as the entire AP;
- applying an `A` extractor to `AP`;
- building AP through an untyped constant string helper;
- ignoring one table axis without explicit target reduction.

---

## 16.3 `NP`

Must preserve:

```text
Case => Str
Agr
```

Forbidden:

- nominative-only NP as complete NP;
- dropping `a`;
- reconstructing agreement from surface text;
- replacing a pronoun or rich list with generic NP assumptions.

---

## 16.4 `Pron`

Must preserve:

```text
Case => Str
acc_clit
dat_clit
Agr
```

Forbidden:

- generic NP-to-Pron coercion;
- empty clitics without lexical/architectural justification;
- loss of person or gen/num agreement.

---

## 16.5 Lexical verbs

Must preserve every `Verb` field and complement slot declared by the category.

Forbidden:

- keeping only present indicative;
- dropping optative/admirative fields;
- discarding `c2` or `c3`;
- replacing a rich lexical verb with a VP string.

---

## 16.6 Rich lists

Must preserve:

- `init`;
- `last`;
- family-specific tables;
- agreement or gender where present.

Forbidden:

- representing `ListNP`, `ListCN`, or `ListAP` as one joined string before the owner’s coordination boundary.

---

# 17. Approved reduction boundaries

Lossy surface extraction is permitted only when the target category contract is already shallow or a documented helper explicitly extracts a surface form.

Approved target classes include current:

```text
Comp
VP
VPSlash
Cl
QCl
RCl
S
QS
RS
SSlash
ClSlash
Utt
Imp
IComp
IP
IDet
IQuant
RP
Adv-family shallow targets
```

Approval is conditional on:

1. exact target category;
2. correct input category;
3. exact helper signature;
4. valid construction context;
5. current producer ownership;
6. no contradictory compile warning;
7. no loss required by a richer target.

A shallow target does not excuse an incorrectly typed input helper.

---

# 18. Exact helper compatibility

Before reusing a helper, verify:

```text
exact input category
exact output category
required record fields
table axes consumed
whether the helper is preserving or lossy
module/export availability
status in helper registry or status ledger
```

Family resemblance is insufficient.

## 18.1 Prohibited substitutions

```text
A helper → AP input
N helper → CN or NP input without exact type
CN helper → NP input
Pron helper → generic NP input
NP helper → ListNP input
CN helper → ListCN input
AP helper → ListAP input
DAP helper → Det or NP input
Digits helper → Numeral or DAP input
```

## 18.2 Compatibility builders

A compatibility builder may be used only when:

- target category is explicitly shallow or lexicalized;
- scope is narrow;
- helper is registered;
- loss is documented;
- canonical rich constructor is unavailable or intentionally not required;
- exit condition exists when temporary.

A compatibility builder does not establish a general category-construction pattern.

---

# 19. Shallow-category construction policy

A shallow category is categorized as follows.

## 19.1 `stable`

Direct construction is accepted in a verified, well-owned context.

Current examples:

```text
CAdv in verified producer context
Utt as a shallow result target
```

## 19.2 `conditional`

The lincat is shallow, but producer ownership or module context must be checked.

Examples:

```text
Subj
Conj
PConj
Voc
Imp
Adv
AdV
AdA
AdN
IAdv
Comp
S
QS
RS
Cl
QCl
RCl
SSlash
ClSlash
IComp
IP
IDet
IQuant
RP
Numeral
Digits
```

## 19.3 `warning`

The category is shallow in shape but has demonstrated drift or compiler-context risk.

Current warning categories/zones:

```text
DConj
Prep
DAP
structural preposition constructor zone
```

## 19.4 `fallback-only`

A construction is accepted only as a documented compatibility bridge.

It must not be copied as canonical architecture.

## 19.5 `blocked`

Current compile evidence rejects the construction pattern in its actual module context.

---

# 20. Current high-risk and blocked zones

## 20.1 `DConj`

Current lincat:

```gf
{s : Str}
```

Current construction conclusion:

```text
shape is shallow
direct local constructor is not universally licensed
```

Known blocked pattern in `StructuralSqiClause.gf`:

```gf
mkDConj : Str -> DConj =
  \s -> lin DConj {s = s}
```

Current status of that pattern:

```text
blocked by compile reality
```

Affected exports include at least:

```text
both7and_DConj
either7or_DConj
```

Exit criteria:

- accepted constructor path identified in the exact module context;
- `StructuralSqiClause.gf` compiles;
- dependent structural exports compile;
- targeted constructor-availability scenario/test passes;
- status ledger updated.

---

## 20.2 `DAP`

Current lincat:

```gf
{s : Str}
```

Status:

```text
Active lincat
warning construction zone
```

Risks:

- confusing it with `NP`, `Det`, `Num`, or `Digits`;
- relying on stale comments about default lincat insertion;
- assuming local constructor availability from shape alone.

A fresh GF warning about a missing or defaulted DAP lincat must be treated as a contract failure until reconciled with current source.

---

## 20.3 `Prep`

Current resource shape:

```gf
Compl = {s : Str}
Prep = Compl
```

Status:

```text
Active lincat
warning / producer-first construction
```

Risks:

- naked string construction;
- ignoring producer-owned behavior;
- ignoring case government;
- treating lock-field warnings as harmless.

Preferred paths:

```text
ResSqi.mkPrep
AdverbSqi.PrepNP
```

---

## 20.4 `A` versus `AP`

Current contracts:

```text
A  = Adj
AP = Species => Case => Gender => Number => Str
```

Known risk:

```text
using an A-typed helper where AP is required
```

The `fp_FocusAP` family remains warning-state until the live implementation uses an exact `AP` helper/extractor and compile evidence passes.

---

## 20.5 Structural verbal incompleteness

`must_VV` is currently tracked as incomplete in the project status evidence.

This is not a lincat ambiguity.

It is an implementation-completion issue involving a rich verbal category and structural export path.

It must remain in `STATUS_LEDGER.md` until its explicit exit criteria pass.

---

# 21. Field-level consumer contract

| Field | Owning record/category | Consumer assumption | Forbidden assumption |
|---|---|---|---|
| `s` | many records | exact table/string type declared by provider | every `s` is plain `Str` |
| `g` | `Noun`, rich CN lists | lexical/category gender | infer from one string |
| `a` | `NP`, `Pron`, `ListNP` | complete agreement | optional decoration |
| `gn` | `Agr` | singular gender/plural state | independent gender and number fields |
| `p` | `Agr` | person | always third person unless constructor proves it |
| `acc_clit` | `Pron` | accusative clitic | generic NP field |
| `dat_clit` | `Pron` | dative clitic | generic NP field |
| `spec` | `Quant`, `Det`, `ListDAP` | species/definiteness behavior | derive from surface form |
| `n` | `Det`, `Num`, `Digits`, `Decimal`, `ListDAP` | grammatical number | ignore because output is shallow |
| `c2` | complement-bearing lexical categories | first complement contract | discard during coercion |
| `c3` | two-complement categories | second complement contract | discard during coercion |
| `clit` | `Adj` | adjective-specific behavior | AP field or irrelevant flag |
| `tail` | `Digits` | digit-tail state | replace with surface string |
| `hasDot` | `Decimal` | decimal-point state | infer from normalized text only |
| `init` | list categories | non-final coordinated material | merge prematurely |
| `last` | list categories | final coordinated material | merge prematurely |

---

# 22. Complement-slot contract

Categories with `c2`:

```text
N2
A2
V2
V2S
V2Q
```

Categories with `c2` and `c3`:

```text
N3
V3
V2A
V2V
```

Rules:

- complement fields are part of the category;
- projection to the base lexical category is lossy;
- consumers must not assume all complements are empty strings;
- constructors must initialize complement fields through approved records;
- moving complement ownership is breaking;
- scenarios must cover complement realization where release-significant.

---

# 23. Agreement contract

Agreement is represented by:

```gf
Agr = {
  gn : GenNum ;
  p  : Person
}
```

Agreement-bearing categories include at least:

```text
NP
Pron
ListNP
```

Rules:

- agreement is not optional metadata;
- noun-derived NP agreement uses noun gender and determiner number in current evidence;
- pronoun agreement preserves lexical person;
- list agreement follows conjunction-module contract;
- sentence and verb agreement consumers must not recover agreement from strings;
- any Agr shape change requires noun, pronoun, sentence, question, and list review.

---

# 24. Case contract

Case-sensitive categories include at least:

```text
N
N2
N3
CN
NP
Pron
Det
Quant
A
A2
AP
ListNP
ListCN
ListAP
```

Rules:

- case tables must remain total over the current `Case` domain;
- selecting a case is permitted only at a documented syntactic boundary;
- nominative selection in subject position is current sentence evidence;
- accusative selection after preposition is current adverb evidence;
- generic NP constructors must not hard-code nominative;
- a case-policy change requires scenario and gold review.

---

# 25. Species contract

Species-sensitive categories include:

```text
N
N2
N3
CN
AP
Quant
Det
ListCN
ListAP
ListDAP
```

Rules:

- `Indef` and `Def` remain distinct;
- determiners and quantifiers may select species;
- AP realization must receive species where its lincat requires it;
- CN construction must not collapse species;
- list coordination preserves species-indexed realization.

---

# 26. Gender contract

Gender-sensitive categories and fields include:

```text
Noun.g
A.s
AP.s
Det.s
Quant.s
Agr/GenNum
ListCN.g
ListAP.s
```

Rules:

- noun gender feeds determiner and adjective realization;
- result CN gender normally remains lexical noun gender;
- gender must not be guessed from orthography inside consumers;
- changing gender inventory requires morphology and syntax migration.

---

# 27. Number contract

Number occurs in:

```text
Noun.s
Adj.s
Verb forms
Quant.s
Det.n
Num.n
Digits.n
Decimal.n
Agr/GenNum
ListDAP.n
```

Rules:

- fixed-number categories must retain their `n` field;
- number selection must use the correct category source;
- number cannot be inferred solely from one surface token;
- digit and decimal number fields remain distinct from nominal agreement.

---

# 28. Clitic contract

## 28.1 Pronoun clitics

```text
acc_clit
dat_clit
```

are public fields of the current pronoun record.

They must be preserved through pronoun producers and any explicit pronoun transformation.

## 28.2 Adjective clitic flag

```text
Adj.clit
```

belongs to lexical adjective shape.

It is not an AP field.

## 28.3 Change rules

Changing clitic representation requires:

- resource type change;
- all producer review;
- all consumer review;
- morphology and syntax docs;
- targeted scenarios;
- project contract version review.

---

# 29. Constructor review algorithm

Before implementing or modifying a constructor:

1. read the exact abstract signature;
2. identify the exact target category;
3. identify the current lincat provider;
4. list every required field and table axis;
5. determine whether the target is rich or shallow;
6. identify the canonical producer module;
7. inspect current Albanian patterns for the same target;
8. verify exact helper signatures;
9. classify helpers as preserving, lossy, compatibility, or unknown;
10. verify constructor availability in the actual module;
11. inspect warning/blocked status;
12. implement the smallest category-correct change;
13. compile the provider;
14. compile direct consumers;
15. compile checkpoint and entrypoint modules;
16. run required scenarios;
17. review gold impact;
18. update contracts and status records.

Skipping steps 8–11 because a category “looks simple” is prohibited.

---

# 30. Change classification

## 30.1 Internal compatible implementation change

Examples:

- refactor a private helper;
- simplify code while preserving every field;
- use a different equivalent producer constructor;
- improve comments.

Requirements:

- provider compile;
- direct consumer compile;
- relevant scenarios;
- no contract version bump unless normative wording changes.

---

## 30.2 Compatible lincat extension

Example:

```text
add an optional/derivable field with a safe initialization policy
```

This is compatible only when:

- existing consumers remain valid;
- all producers can supply the field safely;
- default semantics are documented;
- GF inheritance and lock behavior are verified;
- schema/contract policy accepts the change.

Required actions:

- provider update;
- producer review;
- consumer review;
- contract minor version;
- tests;
- scenarios;
- gold review where output changes.

---

## 30.3 Breaking lincat change

Examples:

- rename or remove field;
- change field type;
- change table axes;
- change parameter constructors;
- flatten rich category;
- enrich shallow category with required fields;
- move category ownership;
- change complement structure;
- merge `A` and `AP`;
- merge `NP` and `Pron`;
- change `Prep` case policy;
- change list category shape.

Required actions:

1. identify `PIFC-LINCAT-001` or `PIFC-LINCAT-002`;
2. record decision;
3. update provider;
4. migrate every producer;
5. migrate every direct consumer;
6. review downstream entrypoints;
7. update architecture and morphology/syntax documents;
8. update status ledger;
9. update scenarios;
10. deliberately update affected gold;
11. compile clean checkpoints;
12. compile final entrypoints;
13. rebuild PGF;
14. increment project contract major;
15. review project release major.

---

# 31. Validation evidence

Every active lincat contract requires at least one proof.

Accepted evidence:

```text
provider module compilation
direct consumer compilation
checkpoint compilation
entrypoint compilation
GF load scenario
missing-linearization inspection
linearization scenario
parse scenario
morphology scenario
bounded generation scenario
gold comparison
reviewed `.gfo`/`.pgf` artifact
manual type/field review when automation cannot inspect a contract
```

A successful provider compile alone is insufficient when downstream modules consume the changed shape.

---

## 31.1 Minimum evidence by change type

| Change | Minimum evidence |
|---|---|
| Private helper only | provider compile + unit/target test |
| Producer implementation, same shape | provider + direct consumers + relevant scenario |
| New constructor for rich category | provider + checkpoint + entrypoint + field-preservation scenarios |
| Shallow local constructor | exact module compile + constructor-availability test |
| Lincat field addition | provider + all producers + consumers + scenarios |
| Lincat field removal/type change | full release validation + migration |
| Parameter change | full morphology/syntax release validation |
| Prep government change | prep scenarios + parse/linearization + gold review |
| AP/CN/NP boundary change | targeted rich-category preservation tests + release |
| List category change | conjunction scenarios + consumers + gold review |
| DConj repair | structural module compile + dependent exports + targeted test |

---

# 32. Required contract tests

The project should provide checks equivalent to:

```text
category provider exists
resource provider exists
documented lincat names exist
documented resource fields exist
producer modules exist
no undocumented cross-module field access
no rich-category flattening patterns
exact helper type checks for high-risk families
DConj constructor-availability regression
Prep producer-path regression
A/AP mismatch regression
NP agreement-preservation regression
Pron clitic-preservation regression
ListNP/ListCN/ListAP shape regression
Digits/Decimal field-preservation regression
old-language identifier scan
contract/document synchronization
```

GF compile behavior remains the decisive type proof.

---

# 33. Scenario coverage requirements

`VALIDATION_SPEC.md` owns exact scenario IDs.

Coverage must include at least these semantic families:

```text
noun inflection across species/case/number
determiner + CN agreement
AP + CN agreement
NP case realization
pronoun case and clitics
preposition + NP case
verb paradigm smoke coverage
complement-bearing lexical categories
Comp reduction from NP/AP/CN/Adv
subject + VP realization
question and relative shallow boundaries
rich list coordination
DAP constructor/use coverage
DConj structural coverage
digits and decimal state
missing-linearization inspection
```

A release-blocking category family must not rely exclusively on manual inspection.

---

# 34. Gold impact

A category or lincat change may change:

- linearized strings;
- ordering;
- inflection;
- agreement;
- clitic placement;
- preposition case;
- list coordination;
- parse ambiguity;
- missing-linearization output;
- generated PGF behavior.

Gold update rules:

- normal validation is read-only;
- old and new raw outputs are reviewed;
- semantic reason is documented;
- normalization is not used to conceal a contract change;
- all affected scenario sections are reviewed;
- status ledger and decision log are updated when significant.

---

# 35. Documentation synchronization

The following files must agree with this contract:

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
project/docs/KNOWN_ISSUES.md
```

Conflict resolution:

- current source and compile truth determine current implementation;
- this document is corrected when stale;
- source is corrected when it violates an accepted stable contract;
- breaking differences require an explicit decision.

---

# 36. Forbidden patterns

The following are prohibited.

```text
Returning `{s : Str}` for `NP`, `CN`, `AP`, `Pron`, `ListNP`, `ListCN`, or `ListAP`
Using an `A` helper for `AP`
Using one AP cell as the complete AP
Dropping NP agreement
Dropping pronoun clitic fields
Dropping `c2` or `c3`
Using processing success as proof of field preservation
Treating every `s` field as plain `Str`
Creating Prep values as unreviewed naked strings
Changing preposition case policy locally
Treating DConj shape as universal local-constructor permission
Treating DAP as NP/Det/Num by family resemblance
Replacing Digits or Decimal with one string
Flattening rich lists before coordination ownership
Reconstructing rich values from normalized gold text
Using comments instead of current provider definitions
Ignoring GF lock-field warnings
Copying a constructor from another module without checking exports and context
Using a fallback helper as a canonical producer
Changing a lincat in one file only
```

---

# 37. Anti-drift indicators

Probable category drift exists when:

- a consumer accesses an undocumented field;
- `CatSqi.gf` and this document disagree;
- `ResSqi.gf` and this document disagree;
- a rich target is built from one string;
- a helper’s declared input differs from the actual category;
- a producer loses a table axis;
- `NP.a` disappears;
- pronoun clitics disappear;
- complement slots disappear;
- a list category is replaced with a singular category;
- `PrepNP` behavior changes without case-policy review;
- a local `lin DConj` is introduced without compile proof;
- a DAP warning is dismissed because the shape looks shallow;
- a lock-field warning appears;
- a compile succeeds only in an aggregator but the owner fails;
- a current comment describes an older default lincat;
- two modules become competing owners for one category helper;
- a gold update hides missing structure;
- a new category shape has no scenario coverage;
- the status ledger calls a warning pattern stable without new evidence.

Every indicator requires restoration of the current contract or a deliberate coordinated change.

---

# 38. Current status summary

## 38.1 Stable active foundations

```text
ResSqi parameter inventory
Agr
Noun
Adj
Verb
Pron
Quant
Det
CatSqi base lincat ownership
rich NP/CN/AP preservation principle
Comp reduction boundary
PrepNP current accusative path
ConjunctionSqi rich list ownership
```

## 38.2 Conditional areas

```text
most shallow clause/sentence/question categories
local construction of structural shallow categories
surface-oriented numeral categories
producer-owned adverbial categories
module-local auxiliary categories
```

## 38.3 Warning areas

```text
DConj construction
DAP constructor/comment drift
Prep and structural preposition construction
A/AP helper compatibility
compatibility builders in extension modules
```

## 38.4 Blocked/incomplete evidence

```text
mkDConj local constructor pattern in StructuralSqiClause
both7and_DConj while the underlying constructor remains unresolved
either7or_DConj while the underlying constructor remains unresolved
must_VV implementation/export path
```

The authoritative live status of individual symbols belongs to `STATUS_LEDGER.md`.

---

# 39. Review checklist

```text
[ ] Exact abstract signature reviewed
[ ] Exact target category identified
[ ] Current CatSqi lincat reviewed
[ ] Current ResSqi type reviewed
[ ] Every required field identified
[ ] Every table axis identified
[ ] Rich/shallow classification recorded
[ ] Canonical producer identified
[ ] Current Albanian producer pattern inspected
[ ] Exact helper signature verified
[ ] Helper status verified
[ ] Constructor availability verified in actual module
[ ] Warning/blocked status reviewed
[ ] No rich input was flattened prematurely
[ ] NP agreement preserved
[ ] Pronoun clitics preserved
[ ] Complement slots preserved
[ ] Prep case policy preserved
[ ] List structure preserved
[ ] Provider compiles
[ ] Direct consumers compile
[ ] Checkpoint compiles
[ ] Entrypoint compiles
[ ] Required scenarios pass
[ ] Gold impact reviewed
[ ] Status ledger updated
[ ] Decision log updated when breaking
[ ] Interfile lock updated
[ ] This document updated
```

---

# 40. Completion criteria

This contract is implementation-complete when:

```text
[ ] project.toml resolves the Albanian source root
[ ] CatSqi is the single base lincat provider
[ ] ResSqi is the single shared resource-type provider
[ ] every active category in CatSqi is represented here
[ ] every public resource record is represented here
[ ] every cross-module field use is documented
[ ] producer ownership is documented
[ ] high-risk shallow categories have construction status
[ ] helper compatibility is documented
[ ] DConj blocked behavior is tracked
[ ] Prep warning behavior is tracked
[ ] DAP warning behavior is tracked
[ ] A/AP distinction has regression coverage
[ ] rich list categories have regression coverage
[ ] required checkpoints compile
[ ] final entrypoints compile
[ ] required scenarios pass
[ ] no release-blocking category-contract issue remains
```

---

# 41. Compact lookup

## 41.1 Preserve fully

```text
N / CN      → Species × Case × Number + Gender
NP          → Case + Agreement
Pron        → Case + acc_clit + dat_clit + Agreement
A           → Case × Gender × Number + clit
AP          → Species × Case × Gender × Number
Verb        → complete paradigm record
N2/A2/V2*   → base record + c2
N3/V3/V2A/V2V → base record + c2 + c3
ListNP      → init/last Case tables + Agreement
ListCN      → init/last nominal tables + Gender
ListAP      → init/last AP tables
Digits      → s + Number + tail
Decimal     → s + Number + hasDot
```

## 41.2 Approved surface boundaries

```text
Comp
VP
VPSlash
Cl/QCl/RCl
S/QS/RS
SSlash/ClSlash
Utt
Imp
question/relative shallow result categories
```

## 41.3 Stop and verify before local construction

```text
DConj
DAP
Prep
Subj
Conj
PConj
Voc
Adv-family categories
Numeral/Digits
any producer-owned shallow category
```

## 41.4 Never confuse

```text
A and AP
N/CN and NP
NP and Pron
NP and ListNP
CN and ListCN
AP and ListAP
DAP and Det/NP/Num
Digits and Numeral/Decimal
shallow shape and constructor availability
```

---

# 42. Final enforcement rule

The current Albanian grammar deliberately combines rich morphology-sensitive categories with several shallow upper-layer categories.

Correct maintenance therefore requires both structural preservation and disciplined reduction.

Therefore:

> Every Albanian constructor must preserve the full lincat of its declared target, use only exact category-compatible helpers, and reduce rich values to strings only at a documented shallow boundary whose constructor is valid in the current module context.
