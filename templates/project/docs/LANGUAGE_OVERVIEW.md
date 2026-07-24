# GF Wordbench Project — Language Overview

**Document ID:** `GF-WB-PROJECT-LANGUAGE-OVERVIEW`  
**Document role:** Normative template  
**Decision status:** Accepted template contract  
**Implementation status:** Template available; active-project implementation depends on initialization  
**Verification status:** Requires placeholder, source, contract and validation checks after initialization  
**Applies to:** One active GF project  
**Template owner:** GF Wordbench  
**Project owner:** `<PROJECT_OWNER>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**GF module suffix:** `<GF_SUFFIX>`  
**Document version:** `1.0.0`  
**Last reviewed:** `<YYYY-MM-DD>`  
**Target path:** `templates/project/docs/LANGUAGE_OVERVIEW.md`

---

## 1. Purpose

This document gives the authoritative high-level description of the active GF project.

It tells a maintainer, reviewer, contributor, or validation operator:

- which language or language variety the project implements;
- which linguistic scope is included;
- which scope is deliberately excluded;
- which orthographic and dialect conventions are used;
- which GF entrypoints expose the project;
- which major grammatical dimensions are represented;
- which parts are stable, partial, experimental, or blocked;
- which external linguistic evidence informs the implementation;
- which project documents own the detailed technical contracts;
- which validation evidence supports the project’s maturity claims.

This file is an overview.

It must not duplicate the complete contents of:

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA.md
project/docs/RESEARCH_EVIDENCE.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

The central rule is:

> This overview states what the GF project is and what it currently claims to support; specialized project documents define how those claims are implemented and validated.

---

## 2. Template-use rules

This file is a template.

When creating an active project:

1. copy this file to:

   ```text
   project/docs/LANGUAGE_OVERVIEW.md
   ```

2. replace every required placeholder;
3. delete instructional text that does not belong in the final project document;
4. remove non-applicable example rows;
5. add project-specific rows where needed;
6. align all identity fields with `project/project.toml`;
7. align scope claims with implementation and validation evidence;
8. record incomplete or uncertain areas honestly;
9. update the project interfile contract lock;
10. run the project documentation and completion checks.

The active-project copy must not remain a generic template.

---

## 3. Required placeholders

The following placeholders are mandatory unless a row is explicitly removed as non-applicable.

```text
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<PROJECT_ID>
<PROJECT_DISPLAY_NAME>
<SOURCE_DIR>
<ABSTRACT_ENTRYPOINT>
<CONCRETE_ENTRYPOINT>
<GRAMMAR_ENTRYPOINT>
<SYNTAX_ENTRYPOINT>
<LANGUAGE_ENTRYPOINT>
<API_ENTRYPOINT_OR_NONE>
<EXPECTED_PGF_OR_NONE>
<LANGUAGE_FAMILY>
<PRIMARY_VARIETY>
<ORTHOGRAPHY_STANDARD>
<SCRIPT>
<PROJECT_STATUS>
<YYYY-MM-DD>
```

Additional placeholders use the same format:

```text
<UPPER_SNAKE_CASE_DESCRIPTION>
```

Every unresolved required placeholder in the active project is a completion failure.

---

## 4. Authority and precedence

When this overview conflicts with another project source, use the following precedence.

1. `project/project.toml` for project identity, paths, entrypoints, checkpoints, scenarios, and release targets;
2. current GF source and GF compiler behavior for implemented language behavior;
3. `project/docs/INTERFILE_CONTRACT_LOCK.md` for cross-file ownership;
4. specialized project documents for morphology, syntax, lincats, validation, status, and release;
5. this overview;
6. historical notes and examples.

This overview must be corrected when it becomes stale.

It must not be used to override current configuration or source behavior silently.

---

## 5. Project identity

Fill every applicable field.

| Field | Project value |
|---|---|
| Project ID | `<PROJECT_ID>` |
| Project display name | `<PROJECT_DISPLAY_NAME>` |
| Language name | `<LANGUAGE_NAME>` |
| Language code | `<LANGUAGE_CODE>` |
| GF module suffix | `<GF_SUFFIX>` |
| Project owner | `<PROJECT_OWNER>` |
| Source directory | `<SOURCE_DIR>` |
| Abstract entrypoint | `<ABSTRACT_ENTRYPOINT>` |
| Concrete entrypoint | `<CONCRETE_ENTRYPOINT>` |
| Grammar entrypoint | `<GRAMMAR_ENTRYPOINT>` |
| Syntax entrypoint | `<SYNTAX_ENTRYPOINT>` |
| Language entrypoint | `<LANGUAGE_ENTRYPOINT>` |
| API entrypoint | `<API_ENTRYPOINT_OR_NONE>` |
| Expected PGF | `<EXPECTED_PGF_OR_NONE>` |
| Project status | `<PROJECT_STATUS>` |
| Last accepted release | `<PROJECT_VERSION_OR_NONE>` |
| Last accepted release run | `<RUN_ID_OR_NONE>` |

Identity values must agree with:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/STATUS_LEDGER.md
project/docs/RELEASE_CRITERIA.md
```

---

## 6. One-project-specific invariant

This document describes exactly one active GF project.

The active identity must not depend on:

- GUI state;
- the last run directory;
- a branch name;
- a hidden profile;
- an environment-only language selector;
- a scenario filename;
- an old project copy.

Language-specific values belong in:

```text
project/project.toml
project/docs/
project/validation/
the active GF source tree
```

They must not be hard-coded into language-neutral framework modules.

Multiple languages require isolated GF Wordbench workspaces or external orchestration.

---

## 7. One-paragraph project summary

Replace this section with one concise paragraph.

```text
<LANGUAGE_NAME> is implemented in this project as <PRIMARY_VARIETY_OR_SCOPE>.
The project targets <MAIN_USE_CASES_OR_RGL_SCOPE>, uses <ORTHOGRAPHY_STANDARD>,
and exposes <MAIN_ENTRYPOINTS>. Its current maturity is <PROJECT_STATUS>,
with <SHORT_DESCRIPTION_OF_STABLE_AREAS> stable and
<SHORT_DESCRIPTION_OF_LIMITATIONS> still incomplete or experimental.
```

The final paragraph should answer:

- what language is implemented;
- which variety is selected;
- what the project is intended to support;
- how mature it is;
- where the main limitations remain.

Do not include implementation detail better owned by the architecture or lincat documents.

---

## 8. Language classification

| Field | Project value |
|---|---|
| Language family | `<LANGUAGE_FAMILY>` |
| Branch or subgroup | `<LANGUAGE_BRANCH_OR_NONE>` |
| Primary country or region | `<PRIMARY_REGION>` |
| Additional regions | `<ADDITIONAL_REGIONS_OR_NONE>` |
| Primary variety | `<PRIMARY_VARIETY>` |
| Other represented varieties | `<OTHER_VARIETIES_OR_NONE>` |
| Script | `<SCRIPT>` |
| Writing direction | `<LTR_OR_RTL>` |
| Standardization authority or convention | `<STANDARDIZATION_AUTHORITY_OR_CONVENTION>` |

This classification is descriptive.

Detailed research evidence belongs in:

```text
project/docs/RESEARCH_EVIDENCE.md
```

Do not make unsupported genealogical, sociolinguistic, or historical claims in this overview.

---

## 9. Variety and dialect policy

### 9.1 Selected variety

```text
<DESCRIBE_THE_PRIMARY_STANDARD_DIALECT_OR_PROJECT_VARIETY>
```

### 9.2 Selection rationale

```text
<WHY_THIS_VARIETY_WAS_SELECTED>
```

Possible reasons include:

- official standard;
- source availability;
- intended users;
- compatibility with an existing RGL resource;
- project research scope;
- educational or experimental purpose.

### 9.3 Included variation

| Variation dimension | Included forms | Selection or precedence rule | Validation evidence |
|---|---|---|---|
| Regional | `<FORMS_OR_NONE>` | `<RULE>` | `<SCENARIO_OR_REVIEW>` |
| Orthographic | `<FORMS_OR_NONE>` | `<RULE>` | `<SCENARIO_OR_REVIEW>` |
| Morphological | `<FORMS_OR_NONE>` | `<RULE>` | `<SCENARIO_OR_REVIEW>` |
| Lexical | `<FORMS_OR_NONE>` | `<RULE>` | `<SCENARIO_OR_REVIEW>` |
| Register | `<FORMS_OR_NONE>` | `<RULE>` | `<SCENARIO_OR_REVIEW>` |

### 9.4 Excluded variation

```text
<LIST_VARIETIES_OR_VARIANTS_INTENTIONALLY_NOT_SUPPORTED>
```

Exclusion must not be confused with an accidental implementation gap.

Use:

```text
project/docs/KNOWN_ISSUES.md
```

for intended support that is currently missing.

---

## 10. Orthography policy

| Field | Project value |
|---|---|
| Orthographic standard | `<ORTHOGRAPHY_STANDARD>` |
| Script | `<SCRIPT>` |
| Encoding | `UTF-8` |
| Case policy | `<CASE_POLICY>` |
| Diacritic policy | `<DIACRITIC_POLICY>` |
| Apostrophe policy | `<APOSTROPHE_POLICY>` |
| Hyphen policy | `<HYPHEN_POLICY>` |
| Spacing policy | `<SPACING_POLICY>` |
| Punctuation policy | `<PUNCTUATION_POLICY>` |
| Number formatting | `<NUMBER_FORMATTING_POLICY>` |
| Decimal formatting | `<DECIMAL_FORMATTING_POLICY>` |
| Quotation style | `<QUOTATION_STYLE>` |

### 10.1 Canonical output spelling

```text
<DESCRIBE_THE_CANONICAL_SPELLING_USED_BY_LINEARIZATION>
```

### 10.2 Accepted parse variants

```text
<DESCRIBE_ACCEPTED_NON_CANONICAL_INPUT_VARIANTS_OR_STATE_NONE>
```

### 10.3 Normalization boundary

Validation normalization must not erase meaningful orthographic distinctions.

Project-specific orthographic normalization must be documented in:

```text
project/docs/VALIDATION_SPEC.md
project/docs/RESEARCH_EVIDENCE.md
```

---

## 11. Character inventory

List only characters materially relevant to implementation or validation.

| Class | Characters or description | Notes |
|---|---|---|
| Core letters | `<CORE_CHARACTER_SET>` | `<NOTES>` |
| Diacritics | `<DIACRITIC_CHARACTERS_OR_NONE>` | `<NOTES>` |
| Apostrophes | `<ALLOWED_APOSTROPHE_CHARACTERS>` | `<NOTES>` |
| Hyphens/dashes | `<ALLOWED_HYPHEN_CHARACTERS>` | `<NOTES>` |
| Digits | `<DIGIT_POLICY>` | `<NOTES>` |
| Other symbols | `<OTHER_RELEVANT_SYMBOLS_OR_NONE>` | `<NOTES>` |

The project should avoid visually similar but semantically different Unicode characters unless explicitly supported.

Encoding and normalization tests should cover all language-relevant characters.

---

## 12. Intended use

Select and describe the project’s intended uses.

| Use case | Status | Notes |
|---|---|---|
| RGL development | `<IN_SCOPE_OR_OUT_OF_SCOPE>` | `<NOTES>` |
| Parsing | `<IN_SCOPE_OR_OUT_OF_SCOPE>` | `<NOTES>` |
| Linearization | `<IN_SCOPE_OR_OUT_OF_SCOPE>` | `<NOTES>` |
| Generation | `<IN_SCOPE_OR_OUT_OF_SCOPE>` | `<NOTES>` |
| Morphological exploration | `<IN_SCOPE_OR_OUT_OF_SCOPE>` | `<NOTES>` |
| Grammar teaching | `<IN_SCOPE_OR_OUT_OF_SCOPE>` | `<NOTES>` |
| Controlled-language applications | `<IN_SCOPE_OR_OUT_OF_SCOPE>` | `<NOTES>` |
| Translation experiments | `<IN_SCOPE_OR_OUT_OF_SCOPE>` | `<NOTES>` |
| Production deployment | `<IN_SCOPE_OR_OUT_OF_SCOPE>` | `<NOTES>` |
| Research prototyping | `<IN_SCOPE_OR_OUT_OF_SCOPE>` | `<NOTES>` |

Do not describe an experimental project as production-ready without release evidence.

---

## 13. Explicit non-goals

List non-goals that prevent scope ambiguity.

```text
- <NON_GOAL_1>
- <NON_GOAL_2>
- <NON_GOAL_3>
```

Common examples, to retain only when true:

- exhaustive dialect coverage;
- unrestricted natural-language understanding;
- corpus-scale lexical completeness;
- automatic linguistic correctness proof;
- speech processing;
- statistical disambiguation;
- machine translation quality guarantees;
- replacement of upstream GF or RGL;
- support for every historical orthography;
- simultaneous implementation of multiple languages in one workspace.

A non-goal must not be used to hide a requirement already declared in project scope.

---

## 14. Linguistic scope summary

Use the following status vocabulary:

```text
stable
partial
experimental
planned
out_of_scope
blocked
```

| Domain | Status | Implemented scope | Main limitations | Evidence owner |
|---|---|---|---|---|
| Orthography | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | `RESEARCH_EVIDENCE.md` / scenarios |
| Nominal morphology | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | `MORPHOLOGY_SPEC.md` |
| Adjectival morphology | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | `MORPHOLOGY_SPEC.md` |
| Verbal morphology | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | `MORPHOLOGY_SPEC.md` |
| Pronouns | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | morphology/syntax docs |
| Determiners | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | lincat/syntax docs |
| Numerals | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | morphology/syntax docs |
| Noun phrases | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Adjective phrases | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Verb phrases | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Clauses | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Questions | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Relative clauses | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Coordination | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Prepositions/adpositions | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Subordination | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Negation | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Polarity | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Tense/aspect/mood | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | morphology/syntax docs |
| Information structure | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | syntax docs |
| Clitics | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | morphology/syntax docs |
| Lexicon | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | lexicon/status docs |
| Parsing | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | validation spec |
| Generation | `<STATUS>` | `<SCOPE>` | `<LIMITATIONS>` | validation spec |

Delete rows that are genuinely irrelevant.

Do not delete a row merely because implementation is incomplete; use `partial`, `planned`, or `blocked`.

---

## 15. Morphological profile

Provide only a high-level summary here.

Detailed paradigms and forms belong in:

```text
project/docs/MORPHOLOGY_SPEC.md
```

### 15.1 Nominal dimensions

| Dimension | Values or behavior | Status |
|---|---|---|
| Number | `<VALUES>` | `<STATUS>` |
| Gender/class | `<VALUES_OR_NONE>` | `<STATUS>` |
| Case | `<VALUES_OR_NONE>` | `<STATUS>` |
| Definiteness/species | `<VALUES_OR_NONE>` | `<STATUS>` |
| Animacy | `<VALUES_OR_NONE>` | `<STATUS>` |
| Possession | `<BEHAVIOR_OR_NONE>` | `<STATUS>` |
| Other | `<DIMENSION_OR_NONE>` | `<STATUS>` |

### 15.2 Adjectival dimensions

| Dimension | Values or behavior | Status |
|---|---|---|
| Agreement | `<VALUES_OR_BEHAVIOR>` | `<STATUS>` |
| Degree | `<VALUES_OR_BEHAVIOR>` | `<STATUS>` |
| Definiteness | `<VALUES_OR_BEHAVIOR>` | `<STATUS>` |
| Position/attribution | `<VALUES_OR_BEHAVIOR>` | `<STATUS>` |
| Other | `<DIMENSION_OR_NONE>` | `<STATUS>` |

### 15.3 Verbal dimensions

| Dimension | Values or behavior | Status |
|---|---|---|
| Person | `<VALUES>` | `<STATUS>` |
| Number | `<VALUES>` | `<STATUS>` |
| Tense | `<VALUES>` | `<STATUS>` |
| Aspect | `<VALUES_OR_NONE>` | `<STATUS>` |
| Mood | `<VALUES_OR_NONE>` | `<STATUS>` |
| Voice | `<VALUES_OR_NONE>` | `<STATUS>` |
| Polarity | `<VALUES_OR_NONE>` | `<STATUS>` |
| Participles/non-finite forms | `<VALUES_OR_NONE>` | `<STATUS>` |
| Other | `<DIMENSION_OR_NONE>` | `<STATUS>` |

### 15.4 Pronouns and clitics

```text
<SUMMARIZE_PERSON_NUMBER_GENDER_CASE_CLITIC_AND_REFLEXIVE_BEHAVIOR>
```

### 15.5 Irregularity policy

```text
<EXPLAIN_WHICH_IRREGULARITIES_ARE_LEXICALIZED_AND_WHICH_ARE_DERIVED>
```

---

## 16. Syntactic profile

Detailed constructor and word-order rules belong in:

```text
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
```

### 16.1 Basic constituent order

```text
<DESCRIBE_BASIC_CLAUSE_ORDER_AND_MAJOR_ALTERNATIVES>
```

### 16.2 Noun phrase order

```text
<DESCRIBE_DETERMINER_NUMERAL_ADJECTIVE_GENITIVE_RELATIVE_ORDER>
```

### 16.3 Adposition strategy

```text
<PREPOSITION_POSTPOSITION_OR_MIXED_BEHAVIOR>
```

### 16.4 Agreement strategy

```text
<DESCRIBE_MAJOR_SUBJECT_VERB_NOUN_ADJECTIVE_DETERMINER_AGREEMENT>
```

### 16.5 Case and government

```text
<DESCRIBE_MAJOR_CASE_ASSIGNMENT_AND_ADPOSITIONAL_GOVERNMENT>
```

### 16.6 Negation

```text
<DESCRIBE_NEGATION_POSITION_AND_INTERACTION_WITH_VERBS_OR_CLAUSES>
```

### 16.7 Questions

```text
<DESCRIBE_POLAR_AND_CONTENT_QUESTION_STRATEGY>
```

### 16.8 Relative clauses

```text
<DESCRIBE_RELATIVE_CLAUSE_STRATEGY>
```

### 16.9 Coordination

```text
<DESCRIBE_COORDINATION_STRATEGY_AND_AGREEMENT>
```

### 16.10 Subordination

```text
<DESCRIBE_COMPLEMENTIZERS_SUBJUNCTIONS_AND_MAJOR_SUBORDINATE_PATTERNS>
```

### 16.11 Information structure and word-order variation

```text
<DESCRIBE_SUPPORTED_FOCUS_TOPIC_OR_SCRAMBLING_BEHAVIOR_OR_STATE_NONE>
```

---

## 17. GF category coverage

This is a summary, not the full lincat contract.

| Category family | Main categories | Status | Owner |
|---|---|---|---|
| Nouns | `<N_N2_N3_CN_OR_PROJECT_SET>` | `<STATUS>` | `<MODULE>` |
| Noun phrases | `<NP_PRON_DET_QUANT_OR_PROJECT_SET>` | `<STATUS>` | `<MODULE>` |
| Adjectives | `<A_A2_AP_OR_PROJECT_SET>` | `<STATUS>` | `<MODULE>` |
| Verbs | `<V_V2_V3_VS_VQ_VV_ETC>` | `<STATUS>` | `<MODULE>` |
| Verb phrases | `<VP_VPSLASH_COMP_OR_PROJECT_SET>` | `<STATUS>` | `<MODULE>` |
| Clauses/sentences | `<CL_S_QCL_QS_RCL_RS_ETC>` | `<STATUS>` | `<MODULE>` |
| Adverbs/adpositions | `<ADV_PREP_ETC>` | `<STATUS>` | `<MODULE>` |
| Numerals | `<NUM_CARD_ORD_DIGITS_ETC>` | `<STATUS>` | `<MODULE>` |
| Coordination/lists | `<CONJ_AND_LIST_CATEGORIES>` | `<STATUS>` | `<MODULE>` |
| Extensions | `<EXTENSION_CATEGORIES>` | `<STATUS>` | `<MODULE>` |

The exact lincat shapes and field contracts belong in:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

---

## 18. Lexicon scope

### 18.1 Current lexical coverage

```text
<DESCRIBE_APPROXIMATE_OR_DECLARED_LEXICON_SCOPE>
```

### 18.2 Lexical sources

```text
<LIST_DICTIONARIES_CORPORA_WORDLISTS_OR_INTERNAL_SOURCES>
```

Detailed citations and rights belong in:

```text
project/docs/RESEARCH_EVIDENCE.md
```

### 18.3 Inclusion policy

```text
<DESCRIBE_WHICH_LEXEMES_ARE_INCLUDED_AND_WHY>
```

### 18.4 Exclusion policy

```text
<DESCRIBE_WHICH_LEXEMES_ARE_EXCLUDED_OR_DEFERRED>
```

### 18.5 Multiword expressions

```text
<DESCRIBE_MULTIWORD_EXPRESSION_POLICY_OR_STATE_NONE>
```

### 18.6 Proper names

```text
<DESCRIBE_PROPER_NAME_POLICY_OR_STATE_NONE>
```

### 18.7 Loanwords and foreign spellings

```text
<DESCRIBE_LOANWORD_AND_FOREIGN_NAME_POLICY>
```

### 18.8 Lexicon maturity

| Area | Status | Evidence |
|---|---|---|
| Core closed class | `<STATUS>` | `<MODULE_OR_SCENARIO>` |
| Core open-class examples | `<STATUS>` | `<MODULE_OR_SCENARIO>` |
| Paradigm coverage | `<STATUS>` | `<MODULE_OR_SCENARIO>` |
| Irregular entries | `<STATUS>` | `<MODULE_OR_SCENARIO>` |
| Domain vocabulary | `<STATUS>` | `<MODULE_OR_SCENARIO>` |
| Proper names | `<STATUS>` | `<MODULE_OR_SCENARIO>` |

---

## 19. Semantic and pragmatic conventions

Only include conventions implemented or required by the project.

| Area | Project convention | Status |
|---|---|---|
| Definiteness | `<CONVENTION>` | `<STATUS>` |
| Generic reference | `<CONVENTION>` | `<STATUS>` |
| Politeness | `<CONVENTION>` | `<STATUS>` |
| Evidentiality | `<CONVENTION_OR_NONE>` | `<STATUS>` |
| Animacy | `<CONVENTION_OR_NONE>` | `<STATUS>` |
| Reflexivity | `<CONVENTION_OR_NONE>` | `<STATUS>` |
| Possession | `<CONVENTION_OR_NONE>` | `<STATUS>` |
| Focus | `<CONVENTION_OR_NONE>` | `<STATUS>` |
| Topic | `<CONVENTION_OR_NONE>` | `<STATUS>` |
| Impersonal constructions | `<CONVENTION_OR_NONE>` | `<STATUS>` |
| Existential constructions | `<CONVENTION_OR_NONE>` | `<STATUS>` |

Do not claim semantic distinctions that are not represented or validated.

---

## 20. Abstract/concrete alignment

### 20.1 Abstract grammar relationship

```text
<DESCRIBE_WHETHER_THE_PROJECT_IMPLEMENTS_STANDARD_RGL_ABSTRACTS_CUSTOM_ABSTRACTS_OR_BOTH>
```

### 20.2 Concrete grammar relationship

```text
<DESCRIBE_THE_MAIN_CONCRETE_MODULE_AND_INHERITANCE_STRATEGY>
```

### 20.3 Incomplete or project-specific abstracts

```text
<LIST_CUSTOM_OR_INCOMPLETE_ABSTRACT_MODULES_OR_STATE_NONE>
```

### 20.4 API and extension surfaces

```text
<DESCRIBE_SYNTAX_API_LANGUAGE_API_AND_EXTENSION_ENTRYPOINTS>
```

Exact module ownership belongs in:

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

---

## 21. Entrypoint summary

| Entrypoint role | Module | Purpose | Release-required |
|---|---|---|---:|
| Abstract | `<ABSTRACT_ENTRYPOINT>` | `<PURPOSE>` | `<YES_OR_NO>` |
| Concrete | `<CONCRETE_ENTRYPOINT>` | `<PURPOSE>` | `<YES_OR_NO>` |
| Grammar | `<GRAMMAR_ENTRYPOINT>` | `<PURPOSE>` | `<YES_OR_NO>` |
| Syntax | `<SYNTAX_ENTRYPOINT>` | `<PURPOSE>` | `<YES_OR_NO>` |
| Language | `<LANGUAGE_ENTRYPOINT>` | `<PURPOSE>` | `<YES_OR_NO>` |
| API | `<API_ENTRYPOINT_OR_NONE>` | `<PURPOSE_OR_NONE>` | `<YES_OR_NO>` |
| PGF build | `<PGF_ENTRYPOINT>` | `<PURPOSE>` | `<YES_OR_NO>` |

The final list must match `project/project.toml`.

Do not list a lower-level checkpoint as a final release entrypoint unless the release contract explicitly says so.

---

## 22. Checkpoint summary

| Checkpoint ID | Module | Layer proved | Required scenarios | Status |
|---|---|---|---|---|
| `<CHECKPOINT_ID_1>` | `<MODULE>` | `<LAYER>` | `<SCENARIOS>` | `<STATUS>` |
| `<CHECKPOINT_ID_2>` | `<MODULE>` | `<LAYER>` | `<SCENARIOS>` | `<STATUS>` |
| `<CHECKPOINT_ID_3>` | `<MODULE>` | `<LAYER>` | `<SCENARIOS>` | `<STATUS>` |

Checkpoint definitions belong to:

```text
project/project.toml
project/docs/VALIDATION_SPEC.md
```

This table is a readable summary.

---

## 23. Validation summary

### 23.1 Required scenario families

```text
<LIST_REQUIRED_SCENARIO_IDS>
```

### 23.2 Optional scenario families

```text
<LIST_OPTIONAL_SCENARIO_IDS_OR_NONE>
```

### 23.3 Main validated behaviors

```text
- <VALIDATED_BEHAVIOR_1>
- <VALIDATED_BEHAVIOR_2>
- <VALIDATED_BEHAVIOR_3>
```

### 23.4 Manual review requirements

```text
- <MANUAL_REVIEW_CRITERION_1>
- <MANUAL_REVIEW_CRITERION_2>
```

### 23.5 Baseline

| Field | Value |
|---|---|
| Baseline run ID | `<BASELINE_RUN_ID_OR_NONE>` |
| GF Wordbench version | `<WORDBENCH_VERSION_OR_NONE>` |
| GF version | `<GF_VERSION_OR_NONE>` |
| RGL identity | `<RGL_VERSION_OR_REVISION_OR_NONE>` |
| Overall status | `<STATUS_OR_NONE>` |
| Date | `<YYYY-MM-DD_OR_NONE>` |

Validation details belong to:

```text
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/validation/
```

---

## 24. Project maturity

Use only the project completion states defined by GF Wordbench.

```text
not_initialized
in_development
checkpoint_complete
structurally_complete
validation_complete
complete_not_release_ready
release_ready
released
```

Current state:

```text
<PROJECT_STATUS>
```

### 24.1 Stable areas

```text
- <STABLE_AREA_1>
- <STABLE_AREA_2>
```

### 24.2 Partial areas

```text
- <PARTIAL_AREA_1>
- <PARTIAL_AREA_2>
```

### 24.3 Experimental areas

```text
- <EXPERIMENTAL_AREA_1>
- <EXPERIMENTAL_AREA_2>
```

### 24.4 Blocked areas

```text
- <BLOCKED_AREA_1_OR_NONE>
```

### 24.5 Release blockers

```text
- <RELEASE_BLOCKER_1_OR_NONE>
```

The authoritative live status belongs to:

```text
project/docs/STATUS_LEDGER.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA.md
```

---

## 25. Known limitations

Summarize only significant user-visible or architectural limitations.

| ID | Limitation | Impact | Workaround | Release-blocking | Owner |
|---|---|---|---|---:|---|
| `<LIMITATION_ID>` | `<DESCRIPTION>` | `<IMPACT>` | `<WORKAROUND_OR_NONE>` | `<YES_OR_NO>` | `<OWNER>` |

Each live limitation must have a corresponding status-ledger or known-issue record.

This overview must not become the sole issue tracker.

---

## 26. Temporary implementations

Summarize project areas that are intentionally temporary.

| Ledger ID | Area | Temporary behavior | Exit condition | Status |
|---|---|---|---|---|
| `<LEDGER_ID>` | `<AREA>` | `<BEHAVIOR>` | `<EXIT_CONDITION>` | `<STATUS>` |

Temporary behavior must not be described as stable.

The full record belongs in:

```text
project/docs/STATUS_LEDGER.md
```

---

## 27. Research and evidence policy

### 27.1 Evidence categories

The project may use:

- normative orthography references;
- descriptive grammars;
- dictionaries;
- corpus evidence;
- peer-reviewed research;
- official language resources;
- native-speaker review;
- existing RGL implementations;
- internally reviewed project conventions.

### 27.2 Evidence distinction

Every significant linguistic claim should be classified as one of:

```text
external fact
project convention
implementation constraint
working hypothesis
unverified assumption
```

### 27.3 Source ownership

Detailed citations, quotations, license restrictions, and source evaluation belong in:

```text
project/docs/RESEARCH_EVIDENCE.md
```

### 27.4 Unsupported claims

When evidence is insufficient, write:

```text
Evidence is currently insufficient to establish this behavior.
```

Do not silently fill gaps with assumed linguistic rules.

---

## 28. Data and licensing summary

| Asset class | Source | License/permission | Project use | Restrictions |
|---|---|---|---|---|
| Grammar references | `<SOURCE>` | `<TERMS>` | `<USE>` | `<RESTRICTIONS>` |
| Dictionaries | `<SOURCE_OR_NONE>` | `<TERMS>` | `<USE>` | `<RESTRICTIONS>` |
| Corpora | `<SOURCE_OR_NONE>` | `<TERMS>` | `<USE>` | `<RESTRICTIONS>` |
| Word lists | `<SOURCE_OR_NONE>` | `<TERMS>` | `<USE>` | `<RESTRICTIONS>` |
| Native-speaker review | `<SOURCE_OR_NONE>` | `<TERMS>` | `<USE>` | `<RESTRICTIONS>` |
| Upstream GF/RGL code | `<SOURCE>` | `<TERMS>` | `<USE>` | `<RESTRICTIONS>` |

This table is a summary.

The legal and evidentiary details belong in:

```text
project/docs/RESEARCH_EVIDENCE.md
project/docs/RELEASE_CRITERIA.md
```

Ambiguous rights block public distribution until reviewed.

---

## 29. Compatibility summary

| Dependency | Supported/tested identity | Status | Notes |
|---|---|---|---|
| GF Wordbench | `<VERSION_OR_RANGE>` | `<SUPPORTED_TESTED_UNKNOWN>` | `<NOTES>` |
| GF | `<VERSION_OR_RANGE>` | `<SUPPORTED_TESTED_UNKNOWN>` | `<NOTES>` |
| RGL | `<VERSION_OR_REVISION>` | `<SUPPORTED_TESTED_UNKNOWN>` | `<NOTES>` |
| Python | `<VERSION_OR_RANGE>` | `<SUPPORTED_TESTED_UNKNOWN>` | `<NOTES>` |
| Operating system | `<PLATFORMS>` | `<SUPPORTED_TESTED_UNKNOWN>` | `<NOTES>` |

Use the terms consistently:

```text
tested
supported
deprecated
unknown
incompatible
```

A version range in this overview does not replace actual release-run evidence.

---

## 30. Release artifact summary

| Artifact | Expected identity | Required | Purpose |
|---|---|---:|---|
| `.gfo` checkpoints | `<EXPECTED_GFO_SET>` | `<YES_OR_NO>` | layer validation |
| Final `.gfo` | `<EXPECTED_ENTRYPOINT_GFO>` | `<YES_OR_NO>` | entrypoint proof |
| PGF | `<EXPECTED_PGF_OR_NONE>` | `<YES_OR_NO>` | release/runtime artifact |
| Scenario outputs | run-owned | `<YES_OR_NO>` | validation evidence |
| Gold diffs | run-owned on mismatch | `<YES_OR_NO>` | regression evidence |
| Summary JSON | `summary.json` | Yes for release | canonical run result |
| Manifest | `manifest.json` | Yes for release | artifact integrity |

Exact artifact ownership belongs to project configuration and release criteria.

---

## 31. Documentation map

| Question | Authoritative document |
|---|---|
| What language and scope is this? | `LANGUAGE_OVERVIEW.md` |
| How is the source organized? | `LANGUAGE_ARCHITECTURE.md` |
| Which module imports which? | `MODULE_DEPENDENCY_MAP.md` |
| What are the lincats and fields? | `CATEGORY_AND_LINCAT_CONTRACT.md` |
| How does morphology work? | `MORPHOLOGY_SPEC.md` |
| How do constructors and syntax work? | `SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| What must validation execute? | `VALIDATION_SPEC.md` |
| Which requirement has which test? | `TEST_COVERAGE_MATRIX.md` |
| What is temporary or blocked? | `STATUS_LEDGER.md` |
| Why were major choices made? | `DECISION_LOG.md` |
| Which known issues remain? | `KNOWN_ISSUES.md` |
| What blocks or permits release? | `RELEASE_CRITERIA.md` |
| Which sources support linguistic claims? | `RESEARCH_EVIDENCE.md` |
| Which files promise what to each other? | `INTERFILE_CONTRACT_LOCK.md` |

This file must link to specialized documents instead of copying their full rules.

---

## 32. Contributor orientation

A contributor should read the project in this order:

```text
1. project/docs/00_PROJECT_START_HERE.md
2. project/docs/LANGUAGE_OVERVIEW.md
3. project/project.toml
4. project/docs/LANGUAGE_ARCHITECTURE.md
5. project/docs/MODULE_DEPENDENCY_MAP.md
6. project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
7. project/docs/MORPHOLOGY_SPEC.md
8. project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
9. project/docs/VALIDATION_SPEC.md
10. project/docs/STATUS_LEDGER.md
11. project/docs/INTERFILE_CONTRACT_LOCK.md
```

Before changing language behavior, the contributor must identify:

- the authoritative provider;
- all direct consumers;
- affected entrypoints;
- relevant scenarios;
- affected gold files;
- documentation and ledger impact.

---

## 33. Change-impact rules

### 33.1 Identity change

Changing any of:

```text
project ID
language code
GF suffix
source root
entrypoint identity
expected PGF identity
```

requires coordinated project migration.

### 33.2 Scope change

Adding or removing a claimed linguistic domain requires:

- this overview;
- specialized specification;
- coverage matrix;
- validation scenarios;
- release criteria;
- decision log when significant.

### 33.3 Orthography change

Requires:

- research evidence;
- morphology/lexicon review;
- scenario input review;
- gold review;
- release-note classification.

### 33.4 Dialect change

Changing the primary variety is a major project decision.

It may require a project major release.

### 33.5 Maturity change

A status may be promoted only when its exit criteria and validation evidence pass.

Documentation alone cannot promote an area from experimental to stable.

---

## 34. Required consistency checks

The active project should verify that:

```text
language name matches project.toml
language code matches project.toml
GF suffix matches source modules
source directory exists
entrypoint names exist
checkpoint names exist
required scenarios exist
expected PGF name matches release configuration
project status matches STATUS_LEDGER.md
release claims match RELEASE_CRITERIA.md
scope claims map to TEST_COVERAGE_MATRIX.md
known limitations map to KNOWN_ISSUES.md
linguistic claims map to RESEARCH_EVIDENCE.md
```

A documentation checker should report unresolved placeholders and stale identifiers.

---

## 35. Initialization checklist

Complete this checklist when instantiating the template.

```text
[ ] Replace project owner
[ ] Replace project ID
[ ] Replace project display name
[ ] Replace language name
[ ] Replace language code
[ ] Replace GF suffix
[ ] Replace source directory
[ ] Fill every applicable entrypoint
[ ] Fill expected PGF or mark not applicable
[ ] Write one-paragraph project summary
[ ] Fill language classification
[ ] Select primary variety
[ ] Document dialect policy
[ ] Document orthography
[ ] Document script and character inventory
[ ] State intended uses
[ ] State explicit non-goals
[ ] Fill linguistic scope table
[ ] Summarize morphology
[ ] Summarize syntax
[ ] Summarize category coverage
[ ] Summarize lexicon scope
[ ] Summarize semantic conventions
[ ] Fill entrypoint table
[ ] Fill checkpoint table
[ ] Fill validation summary
[ ] Record project maturity
[ ] Link limitations to known issues
[ ] Link temporary behavior to status ledger
[ ] Fill research-evidence summary
[ ] Fill licensing summary
[ ] Fill compatibility summary
[ ] Fill release-artifact summary
[ ] Remove non-applicable examples
[ ] Remove instructional text not needed in active document
[ ] Verify no required placeholder remains
[ ] Verify identity against project.toml
[ ] Verify scope against implementation
[ ] Verify scope against validation coverage
[ ] Verify release claims against release criteria
[ ] Update project interfile contract lock
[ ] Run documentation checks
```

---

## 36. Review checklist

Use this checklist for every review.

```text
[ ] Project identity is current
[ ] One active GF project is described
[ ] Primary variety is explicit
[ ] Orthography policy is explicit
[ ] Scope and non-goals are distinct
[ ] Stable, partial, experimental, and blocked areas are honest
[ ] Morphological summary matches MORPHOLOGY_SPEC.md
[ ] Syntactic summary matches SYNTAX_AND_CONSTRUCTOR_RULES.md
[ ] Category summary matches CATEGORY_AND_LINCAT_CONTRACT.md
[ ] Entrypoints match project.toml
[ ] Checkpoints match project.toml
[ ] Validation summary matches VALIDATION_SPEC.md
[ ] Coverage claims match TEST_COVERAGE_MATRIX.md
[ ] Temporary items match STATUS_LEDGER.md
[ ] Known limitations match KNOWN_ISSUES.md
[ ] Release claims match RELEASE_CRITERIA.md
[ ] Research claims have evidence
[ ] Licensing summary is current
[ ] Compatibility values are current
[ ] No stale language name remains
[ ] No template placeholder remains
[ ] No specialized contract is duplicated unnecessarily
[ ] Last reviewed date is current
```

---

## 37. Anti-drift indicators

Probable overview drift exists when:

- the language name differs from `project.toml`;
- the code or GF suffix differs from source modules;
- a removed entrypoint remains listed;
- a checkpoint exists in configuration but not here;
- a non-existent PGF is described as released;
- a partial feature is described as stable;
- a non-goal conflicts with release criteria;
- a limitation exists only in prose and not in the issue/ledger system;
- a dialect claim has no research evidence;
- an orthographic policy differs from scenario inputs or gold;
- a category family is claimed supported with no coverage;
- validation scenarios are listed by filename guessing;
- a previous run from another project is cited;
- framework-specific implementation details dominate the language overview;
- complete lincat tables are duplicated here;
- complete syntax rules are duplicated here;
- a template example is presented as project fact;
- unresolved placeholders remain;
- old-language identifiers survive cloning;
- status is promoted without evidence;
- licensing claims are assumed rather than reviewed.

Every indicator requires correction before project completion or release.

---

## 38. Active-project cleanup instructions

Delete this section from the active project after initialization if the project documentation policy prefers a concise final overview.

Before deletion, confirm:

```text
[ ] All required placeholders were replaced
[ ] All example-only rows were removed or filled
[ ] All instructional wording was removed or clearly retained as guidance
[ ] Every claim has an owner
[ ] Every status has evidence
[ ] Every limitation has a ledger or issue record
[ ] Every external claim has research evidence
```

The template copy under `templates/project/docs/` retains the full instructions.

---

## 39. Minimal active-project form

An active project may shorten this document, but it must retain at least:

```text
project identity
one-paragraph summary
language classification
variety policy
orthography policy
intended use
non-goals
linguistic scope summary
morphology summary
syntax summary
entrypoints
checkpoints
validation summary
maturity
known limitations
research-evidence links
release-artifact summary
documentation map
last reviewed
```

Removing one of these sections requires an explicit reason in project documentation policy.

---

## 40. Completion criteria

The active `LANGUAGE_OVERVIEW.md` is complete when:

```text
[ ] It describes exactly one active GF project
[ ] Identity agrees with project.toml
[ ] No required placeholder remains
[ ] Variety and orthography are explicit
[ ] Scope and non-goals are explicit
[ ] Linguistic coverage is honestly classified
[ ] Morphology and syntax summaries link to authoritative details
[ ] Entrypoints and checkpoints are current
[ ] Validation claims are supported
[ ] Maturity matches project status
[ ] Limitations and temporary behavior are traceable
[ ] Research claims are supported
[ ] Licensing constraints are summarized
[ ] Compatibility is current
[ ] Release artifacts are accurately described
[ ] Project contract lock references the document
```

---

## 41. Final enforcement rule

The language overview is the project’s high-level statement of identity, scope, and maturity.

It must be readable without becoming a duplicate technical specification.

Therefore:

> No active GF project may claim a language feature, maturity level, compatibility range, or release capability in `LANGUAGE_OVERVIEW.md` unless that claim agrees with project configuration, current GF source, the specialized project contracts, and current validation evidence.
