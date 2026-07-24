# GF Wordbench Project Template — Morphology Specification

**Document ID:** `GF-WB-TEMPLATE-MORPHOLOGY-SPEC`  
**Document role:** Normative template  
**Decision status:** Accepted template contract  
**Implementation status:** Template available; active-project implementation depends on initialization  
**Verification status:** Requires placeholder, source, contract and validation checks after initialization  
**Template path:** `templates/project/docs/MORPHOLOGY_SPEC.md`  
**Active-project destination:** `project/docs/MORPHOLOGY_SPEC.md`  
**Template owner:** GF Wordbench maintainers  
**Project owner after initialization:** `<PROJECT_OWNER>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**GF module suffix:** `<GF_SUFFIX>`  
**Primary morphology provider:** `<MORPHOLOGY_PROVIDER>.gf`  
**Document version:** `1.0.0`  
**Last reviewed:** `<YYYY-MM-DD>`

---

## 1. Purpose

This document defines the morphological contract for one initialized GF project.

It records:

- the grammatical dimensions represented by the project;
- the authoritative modules that own morphological behavior;
- the GF `param`, table, record, constructor, and helper shapes used across files;
- nominal, adjectival, verbal, pronominal, and other inflection systems that apply;
- stem and affix operations;
- agreement behavior;
- irregular and defective paradigms;
- orthographic and morphophonological transformations;
- fallback and incomplete behavior;
- consumers of morphology;
- validation scenarios, gold output, and release gates.

The template is language-neutral.

It MUST be replaced with the real morphology of the initialized project.

The central rule is:

> A morphological behavior is complete only when its linguistic dimensions, GF representation, provider ownership, consumer contract, irregular cases, and validation evidence are all explicit.

---

## 2. Scope

This specification governs project-owned morphology that crosses file boundaries.

It includes, where applicable:

```text
number
gender
case
person
tense
aspect
mood
voice
polarity
definiteness
degree
animacy
honorific or politeness distinctions
possessive agreement
subject agreement
object agreement
clitic agreement
state or construct distinctions
noun classes
declension classes
conjugation classes
stem alternations
affixation
compounding
reduplication
suppletion
defective paradigms
orthographic realization
morphophonological realization
```

This specification does not govern:

- general word order;
- syntactic constructor composition except where it consumes morphology;
- parser algorithms implemented by GF;
- framework process execution;
- scenario-runner mechanics;
- local helper implementations not consumed outside their file;
- purely lexical content without a morphological contract.

Cross-reference syntax behavior in:

```text
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
```

Cross-reference shared category and lincat shapes in:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

---

## 3. Template instructions

When initializing this document:

1. replace every required placeholder;
2. remove every non-applicable grammatical dimension;
3. add language-specific dimensions that are missing;
4. name the authoritative provider for each public behavior;
5. identify every direct consumer;
6. copy exact GF types from source;
7. distinguish stable, experimental, fallback, and blocked behavior;
8. register irregular and defective paradigms;
9. define representative validation cases;
10. align the project interfile contract lock;
11. align the dependency map;
12. align the validation specification;
13. align the test coverage matrix;
14. execute baseline compile and morphology scenarios;
15. retain the baseline run evidence.

Do not copy the completed morphology specification of another language and rename its suffix.

---

# 4. Normative vocabulary

The keywords below are normative.

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **PROVIDER**: module that defines a morphological type, form table, constructor, or helper.
- **CONSUMER**: module that imports or depends on the provided behavior.
- **PARADIGM**: mapping from a lexical base and grammatical feature set to surface form or structured value.
- **LEMMA**: canonical lexical citation form used by project policy.
- **STEM**: project-defined base used to derive one or more forms.
- **FORM**: surface realization selected by grammatical features.
- **FEATURE**: grammatical distinction represented in GF.
- **TOTAL PARADIGM**: every declared feature combination has a valid representation.
- **DEFECTIVE PARADIGM**: one or more declared combinations are intentionally unavailable.
- **IRREGULAR PARADIGM**: forms cannot be derived fully by the regular class rule.
- **FALLBACK**: temporary or reduced behavior used when the intended implementation is incomplete.
- **MORPHOPHONOLOGY**: conditioned changes at morpheme boundaries.
- **ORTHOGRAPHIC NORMALIZATION**: project-owned transformation required to produce canonical written output.

---

# 5. Status vocabulary

Every morphology component listed in this document must use one status.

```text
stable
experimental
temporary
fallback
warning
blocked
disabled
deprecated
retired
```

Meanings:

| Status | Meaning |
|---|---|
| `stable` | Implemented, validated, and allowed for release |
| `experimental` | Implemented for evaluation; compatibility may change |
| `temporary` | Transitional implementation with a planned replacement |
| `fallback` | Reduced implementation used when complete behavior is unavailable |
| `warning` | Usable with a documented correctness or coverage limitation |
| `blocked` | Intended behavior cannot currently be completed |
| `disabled` | Deliberately unavailable in normal project use |
| `deprecated` | Supported temporarily pending removal |
| `retired` | No longer active; retained only for history |

Every non-stable entry MUST be registered in:

```text
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
```

with:

- owner;
- impact;
- next action;
- exit condition;
- release decision.

---

# 6. Project morphology summary

Complete this table.

| Field | Project value |
|---|---|
| Language | `<LANGUAGE_NAME>` |
| Language code | `<LANGUAGE_CODE>` |
| Module suffix | `<GF_SUFFIX>` |
| Primary morphology provider | `<MORPHOLOGY_PROVIDER>.gf` |
| Paradigm provider or providers | `<PARADIGM_PROVIDER_PATHS>` |
| Category provider | `<CATEGORY_PROVIDER>.gf` |
| Lexicon consumers | `<LEXICON_CONSUMER_PATHS>` |
| Structural consumers | `<STRUCTURAL_CONSUMER_PATHS>` |
| Entry point consumers | `<ENTRYPOINT_PATHS>` |
| Morphology scenario | `<MORPHOLOGY_SCENARIO_ID_OR_NONE>` |
| Morphology gold | `<MORPHOLOGY_GOLD_PATH_OR_NONE>` |
| Current maturity | `<stable|experimental|temporary|fallback|warning|blocked>` |
| Main known limitation | `<LIMITATION_OR_NONE>` |

---

# 7. Morphology ownership map

Every public morphological responsibility must have one authoritative provider.

| Responsibility | Provider | Direct consumers | Status | Evidence |
|---|---|---|---|---|
| Shared feature parameters | `<PATH>` | `<PATHS>` | `<STATUS>` | `<COMPILE_OR_SCENARIO>` |
| Nominal morphology | `<PATH>` | `<PATHS>` | `<STATUS>` | `<COMPILE_OR_SCENARIO>` |
| Adjectival morphology | `<PATH_OR_NA>` | `<PATHS_OR_NA>` | `<STATUS>` | `<EVIDENCE>` |
| Verbal morphology | `<PATH>` | `<PATHS>` | `<STATUS>` | `<COMPILE_OR_SCENARIO>` |
| Pronominal morphology | `<PATH_OR_NA>` | `<PATHS_OR_NA>` | `<STATUS>` | `<EVIDENCE>` |
| Determiner morphology | `<PATH_OR_NA>` | `<PATHS_OR_NA>` | `<STATUS>` | `<EVIDENCE>` |
| Numeral morphology | `<PATH_OR_NA>` | `<PATHS_OR_NA>` | `<STATUS>` | `<EVIDENCE>` |
| Adverbial morphology | `<PATH_OR_NA>` | `<PATHS_OR_NA>` | `<STATUS>` | `<EVIDENCE>` |
| Clitic morphology | `<PATH_OR_NA>` | `<PATHS_OR_NA>` | `<STATUS>` | `<EVIDENCE>` |
| Derivational morphology | `<PATH_OR_NA>` | `<PATHS_OR_NA>` | `<STATUS>` | `<EVIDENCE>` |
| Orthographic normalization | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| Morphophonological rules | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| Irregular paradigm registry | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| Defective paradigm policy | `<PATH_OR_DOC>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |

Rules:

- duplicate authoritative providers are prohibited unless a selection rule is documented;
- a consumer MUST NOT reimplement provider logic silently;
- moving ownership is a breaking project contract change;
- every provider must appear in the dependency map;
- every non-private public helper must appear in the project contract lock or helper registry.

---

# 8. Dependency direction

Expected direction:

```text
low-level character and string operations
    → morphophonological helpers
    → inflection tables and feature parameters
    → paradigm constructors
    → category resources
    → lexicon and structural modules
    → syntax modules
    → grammar and API entrypoints
```

Prohibited directions:

```text
morphology provider → grammar entrypoint
morphology provider → validation scenario
paradigm provider → top-level language module
low-level resource → high-level syntax module for convenience
```

Circular GF imports are prohibited.

A low-level provider may depend on standard GF or RGL resources explicitly listed in the dependency map.

---

# 9. Feature inventory

Complete the feature inventory before documenting individual paradigms.

Use `N/A` only with a linguistic or architectural justification.

| Feature family | Project distinction | GF type or parameter | Applies to | Status |
|---|---|---|---|---|
| Number | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Gender or noun class | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Case | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Person | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Tense | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Aspect | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Mood | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Voice | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Polarity | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Definiteness | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Degree | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Animacy | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Possessor features | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Object agreement | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Honorific/politeness | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| State/construct | `<VALUES_OR_NA>` | `<GF_PARAM_OR_NA>` | `<CATEGORIES>` | `<STATUS>` |
| Additional dimension | `<NAME_AND_VALUES>` | `<GF_PARAM>` | `<CATEGORIES>` | `<STATUS>` |

---

## 9.1 Feature-value stability

A public GF `param` value is contractual when consumers pattern-match on it.

Changing any of the following is breaking unless all consumers migrate together:

```text
parameter name
parameter constructor name
constructor arity
feature meaning
feature ordering when serialized or table-indexed
default or fallback interpretation
```

Adding a value requires:

- provider update;
- exhaustive pattern review;
- table completeness review;
- consumer compilation;
- scenario expansion;
- gold review;
- contract-lock update.

---

## 9.2 Feature compression

A project MAY combine several linguistic dimensions into one GF parameter when:

- the combination reflects a stable project architecture;
- consumers do not need the dimensions independently;
- every combined value is documented;
- table coverage remains reviewable;
- no meaningful distinction is lost silently.

Document combined parameters here:

| Combined parameter | Encoded dimensions | Values | Consumers | Reason |
|---|---|---|---|---|
| `<PARAM>` | `<DIMENSIONS>` | `<VALUES>` | `<PATHS>` | `<RATIONALE>` |

A combined parameter must not be created solely to silence type errors.

---

# 10. Shared GF type contracts

Copy exact public GF declarations from source.

## 10.1 Feature parameters

```gf
param
  <PARAMETER_1> = <VALUE_1> | <VALUE_2> ;
  <PARAMETER_2> = <VALUE_1> | <VALUE_2> ;
```

## 10.2 Shared form index

```gf
param
  <FORM_INDEX> =
      <FORM_VALUE_1>
    | <FORM_VALUE_2>
    ;
```

## 10.3 Shared morphology record

```gf
oper
  <MORPH_RECORD> : Type = {
    <FIELD_1> : <TYPE_1> ;
    <FIELD_2> : <TYPE_2> ;
  } ;
```

## 10.4 Shared table type

```gf
oper
  <INFLECTION_TABLE> : Type = <FORM_INDEX> => Str ;
```

These declarations are illustrative placeholders.

The initialized specification must contain actual project declarations or exact cross-references.

---

# 11. Surface-form policy

Define what counts as a valid form.

| Topic | Project policy |
|---|---|
| Canonical script | `<SCRIPT_OR_ORTHOGRAPHY>` |
| Unicode normalization | `<NFC_NFD_OR_OTHER>` |
| Case sensitivity | `<POLICY>` |
| Hyphenation | `<POLICY>` |
| Apostrophes | `<POLICY>` |
| Diacritics | `<POLICY>` |
| Alternative spellings | `<POLICY>` |
| Multiword forms | `<POLICY>` |
| Zero realization | `<POLICY>` |
| Missing form representation | `<POLICY>` |
| Capitalization | `<POLICY>` |
| Token-boundary policy | `<POLICY>` |

Rules:

- linguistically meaningful distinctions MUST NOT be normalized away;
- output normalization used for gold comparison is not a substitute for correct surface forms;
- multiple accepted variants require an explicit representation strategy;
- empty string MUST NOT mean both “valid zero form” and “unimplemented form”;
- missing forms need an explicit defective-paradigm policy.

---

# 12. Lemma and stem policy

Define the lexical input expected by paradigm constructors.

| Category | Lemma convention | Stem derivation | Required additional inputs |
|---|---|---|---|
| Noun | `<CONVENTION>` | `<RULE>` | `<INPUTS>` |
| Adjective | `<CONVENTION>` | `<RULE>` | `<INPUTS>` |
| Verb | `<CONVENTION>` | `<RULE>` | `<INPUTS>` |
| Pronoun | `<CONVENTION>` | `<RULE_OR_EXPLICIT_FORMS>` | `<INPUTS>` |
| Determiner | `<CONVENTION>` | `<RULE_OR_EXPLICIT_FORMS>` | `<INPUTS>` |
| Numeral | `<CONVENTION>` | `<RULE_OR_EXPLICIT_FORMS>` | `<INPUTS>` |
| Other | `<CONVENTION>` | `<RULE>` | `<INPUTS>` |

A paradigm constructor must document whether its string input is:

```text
citation form
bare stem
inflected form used to infer a class
principal part
compound base
orthographic base
phonological approximation
```

A constructor name must not imply one convention while implementing another.

---

## 12.1 Stem operations

Register every public stem operation.

| Helper | Provider | Input | Output | Failure behavior | Consumers |
|---|---|---|---|---|---|
| `<STEM_HELPER_1>` | `<PATH>` | `<INPUT_CONTRACT>` | `<OUTPUT_CONTRACT>` | `<FAILURE>` | `<PATHS>` |
| `<STEM_HELPER_2>` | `<PATH>` | `<INPUT_CONTRACT>` | `<OUTPUT_CONTRACT>` | `<FAILURE>` | `<PATHS>` |

Public stem operations must define behavior for:

- shortest accepted input;
- unexpected final character;
- Unicode character handling;
- multiword input;
- already-inflected input;
- empty input;
- irregular exception.

Do not rely on undocumented string slicing assumptions.

---

# 13. Morphophonological rules

Register productive transformations.

| Rule ID | Trigger | Input environment | Output | Provider | Status | Validation |
|---|---|---|---|---|---|---|
| `MORPH-PHON-001` | `<TRIGGER>` | `<ENVIRONMENT>` | `<TRANSFORMATION>` | `<PATH>` | `<STATUS>` | `<CASE_IDS>` |
| `MORPH-PHON-002` | `<TRIGGER>` | `<ENVIRONMENT>` | `<TRANSFORMATION>` | `<PATH>` | `<STATUS>` | `<CASE_IDS>` |

For each rule document:

- whether it is productive;
- exceptions;
- ordering relative to other rules;
- whether it operates on orthographic or abstract stems;
- whether consumers may invoke it directly;
- whether it is reversible;
- whether it changes token boundaries;
- whether it applies across compounds.

---

## 13.1 Rule ordering

When several transformations apply, define order explicitly.

```text
1. <RULE>
2. <RULE>
3. <RULE>
4. final orthographic normalization
```

Different ordering that changes output is a contract change.

A helper implementation may be refactored only when observable forms remain compatible.

---

# 14. Affix inventory

Document productive affixes only when they are represented as project rules.

| Affix ID | Type | Form or pattern | Grammatical function | Attachment rule | Provider |
|---|---|---|---|---|---|
| `<AFFIX_ID>` | prefix/suffix/infix/circumfix/other | `<FORM>` | `<FUNCTION>` | `<RULE>` | `<PATH>` |

Do not create an affix table for lexicalized material that is not treated productively by the project.

Allomorph selection must be documented under morphophonology or the relevant paradigm.

---

# 15. Nominal morphology

Remove this section only when the GF project has no nominal category.

## 15.1 Nominal dimensions

| Dimension | Values | Required for noun | Required for NP agreement | GF representation |
|---|---|---:|---:|---|
| Number | `<VALUES>` | Yes/No | Yes/No | `<PARAM>` |
| Gender/class | `<VALUES_OR_NA>` | Yes/No | Yes/No | `<PARAM_OR_FIELD>` |
| Case | `<VALUES_OR_NA>` | Yes/No | Yes/No | `<PARAM>` |
| Definiteness | `<VALUES_OR_NA>` | Yes/No | Yes/No | `<PARAM>` |
| Animacy | `<VALUES_OR_NA>` | Yes/No | Yes/No | `<PARAM_OR_FIELD>` |
| State | `<VALUES_OR_NA>` | Yes/No | Yes/No | `<PARAM>` |
| Additional | `<VALUES>` | Yes/No | Yes/No | `<REPRESENTATION>` |

---

## 15.2 Nominal form table

Copy the actual type.

```gf
oper
  <NOUN_FORM> : Type = {
    s : <NOUN_INDEX> => Str ;
    <OTHER_FIELDS>
  } ;
```

Document field meaning:

| Field | Meaning | Consumers | Stable |
|---|---|---|---:|
| `s` | `<MEANING>` | `<PATHS>` | Yes |
| `<FIELD>` | `<MEANING>` | `<PATHS>` | Yes/No |

No consumer may access an undocumented field.

---

## 15.3 Declension classes

| Class ID | Diagnostic input | Productive rule | Exceptions | Constructor | Status |
|---|---|---|---|---|---|
| `<NOUN_CLASS_1>` | `<INPUT_PATTERN>` | `<RULE>` | `<EXCEPTIONS>` | `<CONSTRUCTOR>` | `<STATUS>` |
| `<NOUN_CLASS_2>` | `<INPUT_PATTERN>` | `<RULE>` | `<EXCEPTIONS>` | `<CONSTRUCTOR>` | `<STATUS>` |

Class detection must be:

```text
explicit
deterministic
documented
validated
```

A broad catch-all class must be identified as a fallback when it is not linguistically complete.

---

## 15.4 Noun constructors

Register every public constructor.

| Constructor | Type | Input convention | Output guarantee | Failure/fallback |
|---|---|---|---|---|
| `<MK_NOUN>` | `<GF_TYPE>` | `<INPUT>` | `<GUARANTEE>` | `<BEHAVIOR>` |
| `<MK_IRREG_NOUN>` | `<GF_TYPE>` | `<INPUTS>` | `<GUARANTEE>` | `<BEHAVIOR>` |

Example type placeholder:

```gf
oper
  <MK_NOUN> : Str -> <NOUN_TYPE> ;
```

The initialized specification must include exact types.

---

## 15.5 Nominal irregulars

| Lemma ID | Reason irregular | Explicit forms | Provider | Status | Test case |
|---|---|---|---|---|---|
| `<LEMMA>` | `<REASON>` | `<FORMS_OR_PATH>` | `<PATH>` | `<STATUS>` | `<CASE_ID>` |

An irregular form may be:

- encoded in a specialized constructor;
- encoded as explicit principal parts;
- stored as a fully explicit table;
- delegated to an upstream RGL provider.

The choice must be documented.

---

## 15.6 Nominal validation cases

Minimum recommended coverage:

```text
one regular lemma per productive class
one vowel- or consonant-boundary case where applicable
one irregular lemma
one defective lemma if supported
every number value
every case value
every definiteness value
every gender/class value that changes forms
one multiword or compound case if supported
one invalid constructor input
```

Register concrete cases:

| Case ID | Constructor/lemma | Feature selection | Expected form | Proof |
|---|---|---|---|---|
| `MORPH-N-001` | `<INPUT>` | `<FEATURES>` | `<EXPECTED>` | `<SCENARIO_OR_GOLD>` |

---

# 16. Adjectival morphology

Use `N/A` only with justification.

## 16.1 Adjectival dimensions

| Dimension | Values | Agreement source | GF representation |
|---|---|---|---|
| Number | `<VALUES_OR_NA>` | `<SOURCE>` | `<PARAM_OR_FIELD>` |
| Gender/class | `<VALUES_OR_NA>` | `<SOURCE>` | `<PARAM_OR_FIELD>` |
| Case | `<VALUES_OR_NA>` | `<SOURCE>` | `<PARAM_OR_FIELD>` |
| Definiteness | `<VALUES_OR_NA>` | `<SOURCE>` | `<PARAM_OR_FIELD>` |
| Degree | `<VALUES_OR_NA>` | `<SOURCE>` | `<PARAM_OR_FIELD>` |
| Position/class | `<VALUES_OR_NA>` | `<SOURCE>` | `<PARAM_OR_FIELD>` |
| Additional | `<VALUES_OR_NA>` | `<SOURCE>` | `<REPRESENTATION>` |

---

## 16.2 Adjective table

```gf
oper
  <ADJ_TYPE> : Type = {
    s : <ADJ_INDEX> => Str ;
    <OTHER_FIELDS>
  } ;
```

Document whether degree is:

- inflectional;
- periphrastic;
- lexical;
- unsupported;
- delegated to syntax.

---

## 16.3 Adjective classes and constructors

| Class | Input pattern | Agreement behavior | Degree behavior | Constructor | Status |
|---|---|---|---|---|---|
| `<ADJ_CLASS>` | `<PATTERN>` | `<RULE>` | `<RULE>` | `<CONSTRUCTOR>` | `<STATUS>` |

---

## 16.4 Adjectival validation cases

Minimum recommended coverage:

```text
one regular class
one irregular class
each agreement dimension
positive/comparative/superlative when represented
attributive and predicative use when morphologically distinct
one negative input case
```

---

# 17. Verbal morphology

## 17.1 Verbal dimensions

| Dimension | Values | GF representation | Surface impact |
|---|---|---|---|
| Person | `<VALUES_OR_NA>` | `<PARAM>` | `<DESCRIPTION>` |
| Number | `<VALUES_OR_NA>` | `<PARAM>` | `<DESCRIPTION>` |
| Gender/class | `<VALUES_OR_NA>` | `<PARAM>` | `<DESCRIPTION>` |
| Tense | `<VALUES_OR_NA>` | `<PARAM>` | `<DESCRIPTION>` |
| Aspect | `<VALUES_OR_NA>` | `<PARAM>` | `<DESCRIPTION>` |
| Mood | `<VALUES_OR_NA>` | `<PARAM>` | `<DESCRIPTION>` |
| Voice | `<VALUES_OR_NA>` | `<PARAM>` | `<DESCRIPTION>` |
| Polarity | `<VALUES_OR_NA>` | `<PARAM_OR_SYNTAX>` | `<DESCRIPTION>` |
| Finiteness | `<VALUES_OR_NA>` | `<PARAM>` | `<DESCRIPTION>` |
| Object agreement | `<VALUES_OR_NA>` | `<PARAM_OR_FIELD>` | `<DESCRIPTION>` |
| Additional | `<VALUES>` | `<REPRESENTATION>` | `<DESCRIPTION>` |

---

## 17.2 Verb form index

Copy the actual public representation.

```gf
param
  <VERB_FORM> =
      <FINITE_FORM>
    | <NONFINITE_FORM>
    | <OTHER_FORM>
    ;
```

or:

```gf
oper
  <VERB_INDEX> : Type = <TENSE> * <MOOD> * <PERSON> * <NUMBER> ;
```

Document the actual structure.

---

## 17.3 Verb record

```gf
oper
  <VERB_TYPE> : Type = {
    s : <VERB_INDEX> => Str ;
    <OTHER_FIELDS>
  } ;
```

Document fields:

| Field | Meaning | Consumers | Stability |
|---|---|---|---|
| `s` | `<MEANING>` | `<PATHS>` | Stable |
| `<FIELD>` | `<MEANING>` | `<PATHS>` | `<STATUS>` |

Fields such as auxiliaries, particles, complement type, reflexivity, or valency belong here only when they are genuinely part of the project morphology record.

Syntactic valency must not be mixed into morphology accidentally.

---

## 17.4 Conjugation classes

| Class ID | Principal parts/input | Productive rule | Constructor | Exceptions | Status |
|---|---|---|---|---|---|
| `<VERB_CLASS_1>` | `<INPUTS>` | `<RULE>` | `<CONSTRUCTOR>` | `<EXCEPTIONS>` | `<STATUS>` |
| `<VERB_CLASS_2>` | `<INPUTS>` | `<RULE>` | `<CONSTRUCTOR>` | `<EXCEPTIONS>` | `<STATUS>` |

Class inference must not guess silently when two classes are plausible.

Provide explicit constructors or class arguments where needed.

---

## 17.5 Auxiliary and periphrastic forms

Document every form composed from several tokens or auxiliary elements.

| Construction | Morphological owner | Syntactic owner | Inputs | Ordering | Validation |
|---|---|---|---|---|---|
| `<CONSTRUCTION>` | `<PATH>` | `<PATH>` | `<FEATURES>` | `<ORDER>` | `<CASE_IDS>` |

Ownership rule:

- morphology owns form selection and inflection;
- syntax owns phrase or clause composition;
- exceptions must be explicit.

---

## 17.6 Non-finite forms

| Form | Feature distinctions | Constructor/provider | Consumers | Status |
|---|---|---|---|---|
| Infinitive or equivalent | `<DISTINCTIONS_OR_NA>` | `<PATH>` | `<PATHS>` | `<STATUS>` |
| Participle | `<DISTINCTIONS_OR_NA>` | `<PATH>` | `<PATHS>` | `<STATUS>` |
| Gerund/converb | `<DISTINCTIONS_OR_NA>` | `<PATH>` | `<PATHS>` | `<STATUS>` |
| Verbal noun | `<DISTINCTIONS_OR_NA>` | `<PATH>` | `<PATHS>` | `<STATUS>` |
| Other | `<DISTINCTIONS>` | `<PATH>` | `<PATHS>` | `<STATUS>` |

---

## 17.7 Verbal irregulars

| Lemma ID | Irregular dimensions | Representation | Provider | Status | Test case |
|---|---|---|---|---|---|
| `<LEMMA>` | `<FEATURES>` | `<EXPLICIT_OR_SPECIAL_RULE>` | `<PATH>` | `<STATUS>` | `<CASE_ID>` |

Suppletive verbs should use explicit forms or a dedicated constructor.

Do not force suppletion through unreadable stem heuristics.

---

## 17.8 Defective verbs

| Lemma/class | Missing forms | Intended interpretation | Runtime representation | Consumer behavior |
|---|---|---|---|---|
| `<LEMMA_OR_CLASS>` | `<FORMS>` | `<REASON>` | `<REPRESENTATION>` | `<BEHAVIOR>` |

The project MUST distinguish:

```text
linguistically unavailable
not yet implemented
invalid constructor input
empty realization
```

These states must not all map silently to `""`.

---

## 17.9 Verbal validation cases

Minimum recommended coverage:

```text
one regular verb per productive class
one irregular verb
one defective verb if supported
every person and number value affecting the form
every tense/aspect/mood represented
every non-finite form represented
one auxiliary/periphrastic form
one polarity contrast when morphology participates
one boundary morphophonological case
one invalid input
```

Register concrete cases:

| Case ID | Lemma/constructor | Features | Expected form | Proof |
|---|---|---|---|---|
| `MORPH-V-001` | `<INPUT>` | `<FEATURES>` | `<EXPECTED>` | `<SCENARIO_OR_GOLD>` |

---

# 18. Pronominal morphology

Document pronouns separately when their paradigm is not a regular nominal subclass.

| Dimension | Values | Representation |
|---|---|---|
| Person | `<VALUES>` | `<PARAM_OR_FIELD>` |
| Number | `<VALUES>` | `<PARAM_OR_FIELD>` |
| Gender/class | `<VALUES_OR_NA>` | `<PARAM_OR_FIELD>` |
| Case | `<VALUES_OR_NA>` | `<PARAM_OR_FIELD>` |
| Politeness | `<VALUES_OR_NA>` | `<PARAM_OR_FIELD>` |
| Clitic/full form | `<VALUES_OR_NA>` | `<PARAM_OR_FIELD>` |
| Reflexivity | `<VALUES_OR_NA>` | `<PARAM_OR_FIELD>` |
| Possession | `<VALUES_OR_NA>` | `<PARAM_OR_FIELD>` |

Register explicit pronoun paradigms:

| Pronoun ID | Feature bundle | Forms/provider | Status | Validation |
|---|---|---|---|---|
| `<PRONOUN_ID>` | `<FEATURES>` | `<PATH_OR_FORMS>` | `<STATUS>` | `<CASE_ID>` |

---

# 19. Determiners and quantifiers

Document inflection that cannot be treated as ordinary adjective or pronoun behavior.

| Class | Dimensions | Agreement target | Provider | Consumers | Status |
|---|---|---|---|---|---|
| `<DETERMINER_CLASS>` | `<FEATURES>` | `<TARGET>` | `<PATH>` | `<PATHS>` | `<STATUS>` |

Specify whether definiteness is:

- lexical;
- inflectional;
- clitic;
- syntactically selected;
- jointly realized.

---

# 20. Numeral morphology

Document:

```text
cardinal forms
ordinal forms
agreement
case inflection
classifier behavior
compound formation
digit/word alternation
special forms
```

| Numeral class | Input | Output dimensions | Provider | Status |
|---|---|---|---|---|
| `<CLASS>` | `<INPUT>` | `<DIMENSIONS>` | `<PATH>` | `<STATUS>` |

Unbounded numeric generation must not be used as exact gold without a deterministic bounded projection.

---

# 21. Other inflectional categories

Add sections for categories that have productive morphology in the language.

Possible examples:

```text
adverbs
prepositions
postpositions
articles
particles
complementizers
conjunctions
interjections
classifiers
copulas
evidentials
auxiliaries
```

Use this table:

| Category | Dimensions | Provider | Consumers | Status | Validation |
|---|---|---|---|---|---|
| `<CATEGORY>` | `<FEATURES>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |

Do not add a category section merely because the category exists syntactically.

---

# 22. Derivational morphology

Derivation may be documented here when it is productive and project-owned.

| Derivation | Input category | Output category | Rule | Productivity | Provider |
|---|---|---|---|---|---|
| `<DERIVATION>` | `<CATEGORY>` | `<CATEGORY>` | `<RULE>` | `<STATUS>` | `<PATH>` |

Clarify whether derivation is:

```text
productive grammar behavior
lexicon-construction convenience
lexicalized list
unsupported
```

Do not represent derivational uncertainty as inflectional certainty.

---

# 23. Compounds and multiword lexemes

Document whether morphology applies to:

- the first token;
- the last token;
- an internal head;
- every component;
- no component;
- a project-specific structured representation.

| Compound class | Head policy | Inflection site | Token policy | Constructor | Status |
|---|---|---|---|---|---|
| `<CLASS>` | `<POLICY>` | `<SITE>` | `<POLICY>` | `<CONSTRUCTOR>` | `<STATUS>` |

String concatenation alone is insufficient when consumers need internal structure.

---

# 24. Clitics

When clitics are morphologically represented, document:

```text
feature inventory
host selection
ordering
fusion
allomorphy
doubling
separation in orthography
interaction with negation
interaction with auxiliaries
```

| Clitic class | Features | Position owner | Form owner | Provider | Validation |
|---|---|---|---|---|---|
| `<CLASS>` | `<FEATURES>` | `<SYNTAX_PATH>` | `<MORPH_PATH>` | `<PATH>` | `<CASE_IDS>` |

Clearly divide morphology and syntax ownership.

---

# 25. Agreement contracts

List every agreement dependency crossing module boundaries.

| Agreement ID | Controller | Target | Features | Morphology provider | Syntax consumer | Failure if violated |
|---|---|---|---|---|---|---|
| `AGR-001` | `<CONTROLLER>` | `<TARGET>` | `<FEATURES>` | `<PATH>` | `<PATH>` | `<FAILURE>` |

Agreement features must use the same meanings across providers and consumers.

A consumer must not reconstruct agreement from surface strings when structured features are available.

---

# 26. Paradigm-constructor registry

Register every public morphology constructor.

| Constructor | Provider | GF type | Category | Regular/irregular | Status | Direct consumers |
|---|---|---|---|---|---|---|
| `<CONSTRUCTOR>` | `<PATH>` | `<GF_TYPE>` | `<CATEGORY>` | `<CLASS>` | `<STATUS>` | `<PATHS>` |

For every constructor document:

- accepted input;
- rejected input;
- output completeness;
- class inference;
- fallback behavior;
- side effects, normally none;
- public stability;
- representative tests.

Constructor names are public contracts when imported elsewhere.

---

# 27. Helper registry

Register shared helpers only.

| Helper | Provider | GF type | Purpose | Consumers | Status |
|---|---|---|---|---|---|
| `<HELPER>` | `<PATH>` | `<GF_TYPE>` | `<PURPOSE>` | `<PATHS>` | `<STATUS>` |

A helper remains private when no other module consumes it.

Do not register every local `oper`.

Duplicate public helpers require consolidation or an explicit difference in purpose.

---

# 28. Irregular registry

The project should maintain one authoritative irregular registry or clearly documented distributed ownership.

| Irregular ID | Category | Lemma | Reason | Representation | Provider | Coverage |
|---|---|---|---|---|---|---|
| `IRR-001` | `<CATEGORY>` | `<LEMMA>` | `<REASON>` | `<METHOD>` | `<PATH>` | `<CASE_ID>` |

Each irregular entry should state whether it is:

```text
fully explicit
partially rule-derived
suppletive
orthographically irregular only
morphophonologically irregular
defective
borrowed
historical exception
```

A large untracked exception list is a maintenance defect.

---

# 29. Defective-paradigm policy

Choose one canonical representation.

Possible approaches:

```text
explicit Maybe-like project type
separate existence predicate
structured variant
documented sentinel
absence handled by constructor choice
```

Using an empty string as a sentinel is permitted only when:

- a valid zero form is impossible;
- every consumer understands the sentinel;
- the contract documents it;
- scenarios test it;
- release reports expose defects.

Complete:

| Topic | Policy |
|---|---|
| Missing-form representation | `<POLICY>` |
| Consumer obligation | `<POLICY>` |
| Linearization behavior | `<POLICY>` |
| Parse behavior | `<POLICY>` |
| Report behavior | `<POLICY>` |
| Gold representation | `<POLICY>` |

---

# 30. Fallback policy

A fallback is not a stable paradigm.

Every fallback must state:

```text
affected category
provider
trigger
produced behavior
known incorrect behavior
consumer impact
status-ledger ID
release impact
replacement plan
exit condition
```

Fallback registry:

| Ledger ID | Provider | Trigger | Behavior | Limitation | Release blocking |
|---|---|---|---|---|---:|
| `<LEDGER_ID>` | `<PATH>` | `<TRIGGER>` | `<BEHAVIOR>` | `<LIMITATION>` | Yes/No |

Forbidden behavior:

- silently routing every unknown class to one guessed class;
- returning the lemma for every unsupported form while claiming completeness;
- flattening a structured paradigm to `Str`;
- using empty output for unimplemented forms without a defect contract;
- hiding fallback use from validation evidence.

---

# 31. Error and invalid-input policy

GF morphology constructors may receive invalid input.

Define policy:

| Invalid condition | Required behavior |
|---|---|
| Empty string | `<BEHAVIOR>` |
| Too-short input | `<BEHAVIOR>` |
| Unsupported script | `<BEHAVIOR>` |
| Unexpected ending | `<BEHAVIOR>` |
| Ambiguous class | `<BEHAVIOR>` |
| Invalid principal parts | `<BEHAVIOR>` |
| Multiword input where unsupported | `<BEHAVIOR>` |
| Missing required explicit form | `<BEHAVIOR>` |

Possible behaviors:

```text
compile-time constructor discipline
explicit fallback with warning status
Predef.error for impossible internal state
specialized constructor required
documented defective result
```

Do not introduce runtime failure casually into common linearization paths.

---

# 32. Consumer contracts

Every direct consumer must state exactly what it uses.

| Consumer | Provider | Used types/fields/helpers | Assumption | Validation |
|---|---|---|---|---|
| `<PATH>` | `<PATH>` | `<PUBLIC_SURFACE>` | `<ASSUMPTION>` | `<COMPILE_OR_SCENARIO>` |

A consumer MUST NOT depend on:

- private helpers;
- undocumented record fields;
- implicit table ordering;
- undocumented fallback behavior;
- a lexical example as if it were a productive rule;
- output string parsing when structured fields exist.

---

# 33. Category and lincat alignment

Cross-check this document with:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

Required alignment:

```text
feature parameters
record field names
field types
agreement dimensions
table indices
constructor result types
missing-form representation
structured category preservation
```

When this document and the lincat contract disagree, release validation must stop until one authoritative design is selected.

---

# 34. Syntax boundary

Morphology provides forms and morphological features.

Syntax provides composition and order.

Complete the boundary table:

| Behavior | Morphology owner | Syntax owner | Boundary object |
|---|---|---|---|
| Noun form selection | `<PATH>` | `<PATH>` | `<TYPE_OR_FIELD>` |
| Adjective agreement | `<PATH>` | `<PATH>` | `<TYPE_OR_FIELD>` |
| Verb agreement | `<PATH>` | `<PATH>` | `<TYPE_OR_FIELD>` |
| Tense/aspect construction | `<PATH>` | `<PATH>` | `<TYPE_OR_FIELD>` |
| Negation | `<PATH_OR_NA>` | `<PATH>` | `<TYPE_OR_FIELD>` |
| Clitic form | `<PATH>` | `<PATH>` | `<TYPE_OR_FIELD>` |
| Auxiliary inflection | `<PATH>` | `<PATH>` | `<TYPE_OR_FIELD>` |
| Definiteness | `<PATH_OR_NA>` | `<PATH_OR_NA>` | `<TYPE_OR_FIELD>` |

A feature may have joint ownership only when the boundary is explicit.

---

# 35. RGL and upstream morphology

Document what is inherited from the RGL or another upstream project.

| Upstream module | Imported behavior | Local override | Reason | Compatibility evidence |
|---|---|---|---|---|
| `<UPSTREAM_PATH>` | `<BEHAVIOR>` | `<PATH_OR_NONE>` | `<RATIONALE>` | `<EVIDENCE>` |

Rules:

- do not duplicate an upstream productive rule without justification;
- local overrides must preserve required public types;
- upstream version changes require revalidation;
- inherited placeholders or shallow implementations must be recorded;
- the exact RGL release or commit belongs in run and release evidence.

---

# 36. Lexicon boundary

Define how lexical entries obtain paradigms.

| Lexical category | Preferred constructor | Explicit-form constructor | Class-selection policy |
|---|---|---|---|
| Noun | `<CONSTRUCTOR>` | `<CONSTRUCTOR_OR_NA>` | `<POLICY>` |
| Adjective | `<CONSTRUCTOR>` | `<CONSTRUCTOR_OR_NA>` | `<POLICY>` |
| Verb | `<CONSTRUCTOR>` | `<CONSTRUCTOR_OR_NA>` | `<POLICY>` |
| Pronoun | `<CONSTRUCTOR>` | `<CONSTRUCTOR_OR_NA>` | `<POLICY>` |
| Other | `<CONSTRUCTOR>` | `<CONSTRUCTOR_OR_NA>` | `<POLICY>` |

Lexicon modules should select or supply paradigms.

They should not reproduce low-level morphology rules.

---

# 37. Structural lexicon boundary

Structural words often contain irregular or closed-class morphology.

Document:

| Structural family | Provider | Morphological source | Explicit forms required | Validation |
|---|---|---|---|---|
| Pronouns | `<PATH>` | `<PATH>` | Yes/No | `<CASE_IDS>` |
| Determiners | `<PATH>` | `<PATH>` | Yes/No | `<CASE_IDS>` |
| Prepositions/adpositions | `<PATH>` | `<PATH_OR_NA>` | Yes/No | `<CASE_IDS>` |
| Conjunctions | `<PATH>` | `<PATH_OR_NA>` | Yes/No | `<CASE_IDS>` |
| Auxiliaries | `<PATH>` | `<PATH>` | Yes/No | `<CASE_IDS>` |
| Copula | `<PATH>` | `<PATH>` | Yes/No | `<CASE_IDS>` |

Closed-class explicit tables still require ownership and tests.

---

# 38. Scenario contract

Preferred morphology scenario:

```text
project/validation/scenarios/<MORPHOLOGY_SCENARIO_ID>.gfs
```

Optional gold:

```text
project/validation/gold/<MORPHOLOGY_SCENARIO_ID>.gold
```

The scenario should use stable sections.

Conceptual sections:

```text
nominal_regular
nominal_irregular
adjectival_agreement
verbal_regular
verbal_irregular
nonfinite
pronouns
defective_forms
morphophonology
```

Only include applicable sections.

Each required section must have:

- begin marker;
- end marker;
- bounded output;
- deterministic input;
- explicit assertion or gold expectation.

---

## 38.1 Scenario data

Large test inventories should live in:

```text
project/validation/inputs/
```

Possible files:

```text
morphology_nouns.txt
morphology_verbs.txt
morphology_irregulars.txt
morphology_negative.txt
```

Do not place unbounded lexicon dumps into exact gold output.

---

## 38.2 Gold policy

Morphology gold should preserve:

```text
lemma or case ID
feature selection
surface form
meaningful alternative variants
defective-form marker
section order
```

Normalization MAY remove:

```text
machine paths
timestamps
process noise
platform line endings
```

Normalization MUST NOT remove:

```text
diacritics
grammatical feature labels
meaningful whitespace or token boundaries
surface-form differences
accepted variant distinctions
```

---

# 39. Required morphology test families

An initialized project should classify each row as required, optional, conditional, or not applicable.

| Family | Policy | Minimum cases | Evidence |
|---|---|---:|---|
| Feature parameter exhaustiveness | `<POLICY>` | all values | compile/contract |
| Regular noun classes | `<POLICY>` | one per class | scenario/gold |
| Irregular nouns | `<POLICY>` | representative set | scenario/gold |
| Regular adjective classes | `<POLICY>` | one per class | scenario/gold |
| Adjective agreement | `<POLICY>` | all changing dimensions | scenario/gold |
| Regular verb classes | `<POLICY>` | one per class | scenario/gold |
| Irregular verbs | `<POLICY>` | representative set | scenario/gold |
| Non-finite forms | `<POLICY>` | one per form | scenario/gold |
| Pronouns | `<POLICY>` | all core feature bundles | scenario/gold |
| Determiners | `<POLICY>` | representative set | scenario/gold |
| Numerals | `<POLICY>` | boundaries and compounds | scenario/gold |
| Morphophonology | `<POLICY>` | one per productive rule | scenario/gold |
| Defective paradigms | `<POLICY>` | one per policy branch | scenario/gold |
| Invalid constructor input | `<POLICY>` | representative failures | scenario/test |
| Consumer integration | `<POLICY>` | entrypoint examples | linearize/parse |
| PGF availability | `<POLICY>` | release artifact | PGF build |

---

# 40. Test case registry

Use stable IDs.

| Case ID | Family | Input | Features | Expected | Scenario/gold | Status |
|---|---|---|---|---|---|---|
| `MORPH-N-001` | noun | `<INPUT>` | `<FEATURES>` | `<EXPECTED>` | `<PATH>` | `<STATUS>` |
| `MORPH-A-001` | adjective | `<INPUT>` | `<FEATURES>` | `<EXPECTED>` | `<PATH>` | `<STATUS>` |
| `MORPH-V-001` | verb | `<INPUT>` | `<FEATURES>` | `<EXPECTED>` | `<PATH>` | `<STATUS>` |
| `MORPH-P-001` | pronoun | `<INPUT>` | `<FEATURES>` | `<EXPECTED>` | `<PATH>` | `<STATUS>` |
| `MORPH-X-001` | negative/boundary | `<INPUT>` | `<FEATURES>` | `<EXPECTED>` | `<PATH>` | `<STATUS>` |

IDs must not be reused after retirement.

---

# 41. Compile coverage

Required compile sequence should follow dependency order.

Conceptual sequence:

```text
morphology provider
    → paradigm provider
    → category consumers
    → noun/adjective/verb consumers
    → structural module
    → extension module
    → grammar entrypoint
    → API entrypoint
```

Complete the actual sequence:

```text
1. <MODULE>.gf
2. <MODULE>.gf
3. <MODULE>.gf
4. <ENTRYPOINT>.gf
```

Every provider change requires:

- direct provider compile;
- all direct consumer compiles;
- downstream entrypoint compiles;
- relevant scenarios;
- gold review when output changes.

---

# 42. Static checks

Static validation may detect:

```text
duplicate helper names
unregistered public constructors
unregistered fallback markers
empty or suspicious form tables
string slicing without guarded input
temporary comments tied to public behavior
source paths inconsistent with project configuration
old language identifiers
trailing whitespace
```

Static scans are heuristic.

They do not prove morphological correctness.

GF compilation and scenarios remain authoritative behavioral evidence.

---

# 43. Release gates

Morphology is release-ready only when all applicable criteria pass.

```text
[ ] Feature inventory is complete
[ ] Public GF types match source
[ ] One authoritative provider exists per responsibility
[ ] Direct consumers are registered
[ ] No undocumented public helper remains
[ ] No undocumented lincat dependency remains
[ ] Regular classes have representative coverage
[ ] Irregular forms have representative coverage
[ ] Defective-form policy is explicit
[ ] Fallbacks are ledgered
[ ] Required provider and consumer modules compile
[ ] Required morphology scenarios pass
[ ] Required gold comparisons pass
[ ] Meaningful output is preserved by normalization
[ ] Entry points compile
[ ] PGF build passes when required
[ ] No release-blocking morphology issue remains
[ ] Manual linguistic review is recorded
```

A compile-only morphology implementation is not automatically release-ready.

---

# 44. Manual linguistic review

Automation can prove consistency and regression behavior.

It cannot independently establish that every form is linguistically correct.

Required review record:

| Field | Value |
|---|---|
| Reviewer | `<REVIEWER>` |
| Scope | `<CATEGORIES_OR_CASE_IDS>` |
| Reference sources | `<SOURCES>` |
| Date | `<YYYY-MM-DD>` |
| Outcome | `<APPROVED_OR_CHANGES_REQUIRED>` |
| Known limitations | `<LIMITATIONS_OR_NONE>` |
| Decision or issue IDs | `<IDS_OR_NONE>` |

Do not cite a linguistic source that was not actually consulted.

---

# 45. Evidence record

After a complete morphology validation, retain:

```text
run ID
GF Wordbench version
GF version
RGL release or commit
project source commit
provider compile result
consumer compile results
entrypoint compile results
morphology ScenarioResult
normalized output
gold comparison
artifact manifest
manual review record
status-ledger review
known-issues review
```

This specification defines required evidence.

It does not store transient pass/fail values.

---

# 46. Change classification

## 46.1 Compatible internal change

Examples:

- refactor a private helper;
- improve performance;
- simplify table construction;
- rename a local variable;
- reorganize private operations.

Requirements:

```text
observable forms unchanged
public types unchanged
consumer behavior unchanged
tests pass
```

---

## 46.2 Compatible contract extension

Examples:

- add an optional constructor;
- add a new productive class without changing old forms;
- add a derivable field with safe initialization;
- add an optional scenario case;
- add explicit support for a previously rejected lexical class.

Requirements:

```text
provider updated
consumers reviewed
tests added
documentation updated
contract lock updated
project version impact reviewed
```

---

## 46.3 Breaking change

Examples:

- rename a public morphology module;
- rename a public constructor;
- change constructor arity;
- change accepted lemma convention;
- change a `param` value;
- remove a feature distinction;
- change a consumed record field;
- change missing-form representation;
- move provider ownership;
- change existing generated forms intentionally;
- change normalization in a way that alters gold.

Requirements:

1. identify affected contract IDs;
2. document reason;
3. enumerate providers and consumers;
4. update source atomically;
5. update project configuration if paths change;
6. update dependency map;
7. update lincat contract;
8. update scenarios and gold intentionally;
9. update status ledger;
10. record a decision;
11. run checkpoints and entrypoints;
12. classify project-version impact;
13. update this specification.

---

# 47. Morphology issue registry

This specification should summarize open morphology issues by reference, not duplicate full issue text.

| Issue ID | Summary | Affected provider | Status | Release blocking | Source |
|---|---|---|---|---:|---|
| `<ISSUE_ID>` | `<SUMMARY>` | `<PATH>` | `<STATUS>` | Yes/No | `STATUS_LEDGER__TEMPLATES_PROJECT_DOCS.md` or `KNOWN_ISSUES.md` |

No issue should exist only in this table.

---

# 48. Initialization checklist

```text
[ ] Replace project identity placeholders
[ ] Name the primary morphology provider
[ ] Complete the ownership map
[ ] Complete the feature inventory
[ ] Copy exact public GF parameter declarations
[ ] Copy exact public record and table types
[ ] Define surface-form policy
[ ] Define lemma and stem conventions
[ ] Register public stem helpers
[ ] Register morphophonological rules
[ ] Complete applicable category sections
[ ] Register regular classes
[ ] Register irregular paradigms
[ ] Define defective-form policy
[ ] Register all fallbacks
[ ] Register public constructors
[ ] Register public shared helpers
[ ] Document agreement boundaries
[ ] Document syntax/morphology ownership
[ ] Document RGL inheritance and overrides
[ ] Define lexicon constructor policy
[ ] Define morphology scenario
[ ] Define morphology input files
[ ] Define gold policy
[ ] Register test cases
[ ] Define compile sequence
[ ] Align CATEGORY_AND_LINCAT_CONTRACT.md
[ ] Align MODULE_DEPENDENCY_MAP.md
[ ] Align INTERFILE_CONTRACT_LOCK.md
[ ] Align VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md
[ ] Align TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md
[ ] Add incomplete behavior to STATUS_LEDGER__TEMPLATES_PROJECT_DOCS.md
[ ] Add release-significant gaps to KNOWN_ISSUES.md
[ ] Record breaking decisions
[ ] Execute baseline compile coverage
[ ] Execute baseline morphology scenario
[ ] Review baseline gold
[ ] Record manual linguistic review
[ ] Retain baseline evidence
```

---

# 49. Template validation

The GF Wordbench template test suite should verify:

```text
this file exists
approved placeholders are present
no active-project identity appears
no active project path appears
no local tool path appears
all fenced blocks are balanced
required sections exist
status vocabulary is canonical
cross-references use canonical paths
the active project initializer replaces required placeholders
```

The generic template itself is not compiled as GF source.

---

# 50. Anti-drift indicators

Morphology drift exists when:

- source exposes a public parameter absent from this document;
- this document lists a parameter no longer present in source;
- a consumer reads an undocumented field;
- two modules own the same productive rule without a selection contract;
- a paradigm constructor changes input convention silently;
- a new class falls through a generic fallback without a ledger entry;
- an irregular form is fixed only in gold but not in source;
- morphology and syntax both implement the same agreement choice;
- a provider moves without updating imports and dependency maps;
- missing form and valid empty realization share an undocumented sentinel;
- morphology gold changes during a normal run;
- normalization removes meaningful form differences;
- an RGL update changes forms without review;
- optional morphology tests are the only proof of a required release behavior;
- a compile success is presented as proof of linguistic correctness;
- template placeholders are presented as active project facts.

Any drift indicator requires coordinated review.

---

# 51. Required cross-references

| Topic | Document |
|---|---|
| Project start | `project/docs/00_PROJECT_START_HERE__PROJECT_DOCS.md` |
| Project contracts | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Language architecture | `project/docs/LANGUAGE_ARCHITECTURE.md` |
| Module dependencies | `project/docs/MODULE_DEPENDENCY_MAP.md` |
| Category and lincat shapes | `project/docs/CATEGORY_AND_LINCAT_CONTRACT.md` |
| Syntax boundary | `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| Validation semantics | `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md` |
| Coverage obligations | `project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md` |
| Temporary states | `project/docs/STATUS_LEDGER__PROJECT_DOCS.md` |
| Known issues | `project/docs/KNOWN_ISSUES.md` |
| Decisions | `project/docs/DECISION_LOG.md` |
| Release criteria | `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md` |
| Scenario format | `docs/scenarios/SCENARIO_FORMAT.md` |
| Gold updates | `docs/scenarios/UPDATING_GOLD_FILES.md` |
| GF compilation | `docs/gf/GF_COMPILATION.md` |
| Project template guide | `templates/project/README.md` |
| Template project lock | `templates/project/docs/INTERFILE_CONTRACT_LOCK.md` |

---

# 52. Final rule

> Morphology is a public data contract, not a collection of convenient string operations.

A provider owns the forms, features, and structured values it exposes.

A consumer may rely only on documented morphology.

An irregular or fallback form must remain visible.

A release claim requires GF compilation, behavioral evidence, reviewed expectations, and linguistic review appropriate to the project.
