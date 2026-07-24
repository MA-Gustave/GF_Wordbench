# GF Wordbench Project — Research Evidence Register

**Document ID:** `GF-WB-PROJECT-RESEARCH-EVIDENCE`  
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
**Register version:** `1.0.0`  
**Last reviewed:** `<YYYY-MM-DD>`  
**Target path:** `templates/project/docs/RESEARCH_EVIDENCE.md`

---

## 1. Purpose

This document is the project’s authoritative register of linguistic research evidence.

It records:

- which external sources the project consulted;
- which linguistic claims the project makes;
- which source passages support or challenge each claim;
- which project conventions were selected when external evidence was incomplete or conflicting;
- which observations, elicitation sessions, corpora, dictionaries, grammars, and experiments were used;
- how evidence quality and applicability were assessed;
- which implementation decisions depend on each claim;
- which validation scenarios test the implemented interpretation;
- which rights, consent, privacy, attribution, and redistribution restrictions apply;
- which questions remain unresolved.

This document exists to prevent unsupported linguistic assumptions from becoming hidden implementation truth.

The central rule is:

> Every language-specific behavior that materially affects morphology, syntax, orthography, lexical choice, parsing, linearization, or release claims must be traceable either to reviewed evidence or to an explicitly labeled project convention, hypothesis, or unresolved assumption.

---

## 2. Template-use rules

When creating an active project:

1. copy this file to:

   ```text
   project/docs/RESEARCH_EVIDENCE.md
   ```

2. replace every required project-identity placeholder;
3. retain the source and claim schemas;
4. delete example-only records;
5. register every material source;
6. create stable claim IDs;
7. connect claims to exact source locations;
8. identify conflicting evidence;
9. connect implemented claims to GF modules and validation evidence;
10. document rights and privacy constraints;
11. preserve unresolved questions honestly;
12. run project documentation and completion checks.

The active-project file must not remain a generic bibliography.

It must become a traceable evidence register.

---

## 3. Required placeholders

The following placeholders are mandatory in the active-project copy unless an entire non-applicable section is removed deliberately:

```text
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<PROJECT_ID>
<PRIMARY_VARIETY>
<ORTHOGRAPHY_STANDARD>
<RESEARCH_REVIEWER>
<YYYY-MM-DD>
```

Record templates use additional placeholders such as:

```text
<SOURCE_ID>
<CLAIM_ID>
<AUTHOR>
<TITLE>
<LOCATOR>
<GF_MODULE>
<SCENARIO_ID>
```

Unresolved placeholders in actual records are completion failures.

---

## 4. Scope

This register covers evidence for:

- language identity and variety selection;
- orthography and character inventory;
- phonologically conditioned spelling when relevant to GF output;
- noun morphology;
- adjective morphology;
- verb morphology;
- pronouns and clitics;
- determiners and quantifiers;
- numerals;
- agreement;
- case and government;
- word order;
- constituent structure;
- clause types;
- questions;
- relative clauses;
- coordination;
- subordination;
- negation;
- tense, aspect, mood, and voice;
- information structure;
- lexical forms;
- multiword expressions;
- parsing expectations;
- accepted ambiguity;
- generation expectations;
- sociolinguistic or register constraints that affect implementation;
- manual linguistic review;
- data and source rights.

It also covers evidence used to justify project-specific deviations from upstream GF or RGL patterns.

---

## 5. Non-scope

This register does not:

- replace the project architecture;
- define GF module imports;
- define lincat field shapes;
- define exact constructor implementations;
- replace the decision log;
- replace the status ledger;
- replace validation scenarios;
- replace gold files;
- reproduce entire copyrighted sources;
- prove linguistic correctness automatically;
- treat source authority as infallible;
- treat frequency alone as grammaticality;
- treat one speaker as representative of every variety;
- provide legal advice.

Detailed ownership remains:

| Topic | Authoritative owner |
|---|---|
| High-level language scope | `LANGUAGE_OVERVIEW.md` |
| Source architecture | `LANGUAGE_ARCHITECTURE.md` |
| Module dependencies | `MODULE_DEPENDENCY_MAP.md` |
| Categories and lincats | `CATEGORY_AND_LINCAT_CONTRACT.md` |
| Morphological implementation | `MORPHOLOGY_SPEC.md` |
| Syntax and constructor rules | `SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| Executable validation | `VALIDATION_SPEC.md` |
| Test mapping | `TEST_COVERAGE_MATRIX.md` |
| Temporary implementation status | `STATUS_LEDGER.md` |
| Architectural decisions | `DECISION_LOG.md` |
| Known defects and limitations | `KNOWN_ISSUES.md` |
| Release acceptance | `RELEASE_CRITERIA.md` |
| Cross-file promises | `INTERFILE_CONTRACT_LOCK.md` |

---

## 6. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **SOURCE**: external or internal material consulted as evidence.
- **CLAIM**: explicit statement about the language or selected project behavior.
- **EVIDENCE LINK**: relationship between a claim and a precise source location, observation, dataset query, or validation result.
- **LOCATOR**: page, section, example number, table, line range, corpus query, timestamp, record ID, or other precise source position.
- **EXTERNAL FACT**: claim presented as a description of language behavior outside this project.
- **PROJECT CONVENTION**: deliberate project choice among acceptable alternatives or in the absence of decisive evidence.
- **IMPLEMENTATION CONSTRAINT**: behavior selected because of current GF/RGL architecture rather than a claim about the language itself.
- **WORKING HYPOTHESIS**: provisional interpretation supported incompletely and subject to further research.
- **UNVERIFIED ASSUMPTION**: behavior used temporarily without adequate evidence.
- **COUNTEREVIDENCE**: source or observation that conflicts with or limits a claim.
- **APPLICABILITY**: degree to which evidence concerns the selected language variety, register, period, and construction.
- **QUALITY REVIEW**: structured assessment of a source’s authority, transparency, directness, consistency, and limitations.
- **ELICITATION**: targeted collection of judgments or forms from a participant.
- **OBSERVATION**: attested example or measured behavior from a text, corpus, speaker, or experiment.
- **ATTESTATION**: occurrence in reviewed data.
- **NEGATIVE EVIDENCE**: explicit rejection, absence under a controlled search, or documented unavailability.
- **TRIANGULATION**: support from more than one independent evidence type or source.
- **REPRODUCIBLE QUERY**: corpus or dataset operation recorded precisely enough to repeat.
- **RIGHTS STATUS**: documented permission, license, restriction, or unresolved legal status.
- **REVIEWED**: examined by the designated project reviewer.
- **SUPPORTED**: evidence is sufficient for the project’s stated confidence and scope.
- **CONTESTED**: material evidence conflicts and no single interpretation has been accepted without qualification.

---

## 7. Authority and precedence

Evidence does not replace current implementation truth, and implementation does not rewrite linguistic evidence.

When sources, code, and project policy differ, apply this process:

1. identify the exact claim;
2. identify the selected variety, register, and period;
3. inspect current source and GF behavior;
4. inspect all registered supporting and conflicting evidence;
5. distinguish external fact from project convention or implementation constraint;
6. decide whether the implementation, documentation, or claim must change;
7. record a decision when the choice is architecturally significant;
8. update affected scenarios and gold files;
9. retain the previous claim or source relationship as superseded history.

Precedence by domain:

| Domain | Highest authority |
|---|---|
| Project identity and active variety | `project/project.toml` plus approved project documentation |
| Current implemented behavior | current GF source and GF compiler/runtime evidence |
| External linguistic description | reviewed source evidence in this register |
| Project-selected convention | explicit approved project convention record |
| Cross-file ownership | `INTERFILE_CONTRACT_LOCK.md` |
| Release acceptance | `RELEASE_CRITERIA.md` and current release evidence |

A source statement does not automatically become a project requirement.

A project implementation does not automatically become an external linguistic fact.

---

## 8. Evidence-classification model

Every material statement must use one claim type:

```text
external_fact
project_convention
implementation_constraint
working_hypothesis
unverified_assumption
```

### 8.1 `external_fact`

Use when the project presents a behavior as an evidence-supported property of the selected language or variety.

Requirements:

- one or more precise evidence links;
- applicability review;
- no unresolved decisive counterevidence;
- confidence stated;
- implementation and validation mapping when implemented.

### 8.2 `project_convention`

Use when the project deliberately chooses:

- one spelling among accepted variants;
- one dialect as canonical output;
- one ambiguity policy;
- one ordering for deterministic gold;
- one representation convention;
- one lexical preference;
- one fallback in an underdocumented area.

Requirements:

- rationale;
- alternatives considered;
- scope;
- decision owner;
- validation impact;
- explicit statement that the choice is project-specific.

### 8.3 `implementation_constraint`

Use when current behavior reflects:

- GF or RGL type structure;
- available abstract syntax;
- current lincat architecture;
- compatibility requirements;
- bounded generation;
- parser or artifact limitations.

It must not be described as a linguistic fact unless independently supported.

### 8.4 `working_hypothesis`

Use when evidence supports a plausible interpretation but remains incomplete.

Requirements:

- known evidence;
- missing evidence;
- uncertainty;
- test plan;
- owner;
- review date or exit condition.

### 8.5 `unverified_assumption`

Use only temporarily.

Requirements:

- explicit risk;
- implementation location;
- release impact;
- research action;
- status-ledger link;
- expiry or exit condition.

A release-blocking assumption must not be silently accepted.

---

## 9. Claim status vocabulary

Every claim uses one current status:

```text
draft
supported
provisional
contested
rejected
superseded
not_applicable
```

### `draft`

Claim is being formulated and has not completed review.

### `supported`

Evidence and scope are sufficient for current project use.

### `provisional`

Claim may be used under documented limits while further evidence is sought.

### `contested`

Significant evidence conflicts.

Implementation must expose the selected convention or limitation explicitly.

### `rejected`

Claim was reviewed and not accepted.

The record is retained to prevent reintroduction without new evidence.

### `superseded`

A newer claim replaces it.

The replacement claim ID must be recorded.

### `not_applicable`

Claim was considered but falls outside declared project scope.

A reason is mandatory.

---

## 10. Confidence vocabulary

Use one confidence value:

```text
high
medium
low
unknown
```

### `high`

- evidence is direct and applicable;
- independent sources or methods agree;
- limitations are understood;
- implementation interpretation is clear.

### `medium`

- evidence is credible but limited;
- variation or interpretation remains;
- project convention may resolve a manageable ambiguity.

### `low`

- evidence is sparse, indirect, old, variety-mismatched, or conflicting;
- implementation should remain provisional.

### `unknown`

- evidence has not yet been evaluated adequately.

Confidence is not a substitute for claim status.

A contested claim can have high confidence that variation exists while having low confidence in one universal rule.

---

## 11. Stable identifiers

### 11.1 Source IDs

Format:

```text
SRC-<NUMBER>
```

Examples:

```text
SRC-0001
SRC-0002
```

### 11.2 Claim IDs

Format:

```text
CLM-<DOMAIN>-<NUMBER>
```

Recommended domains:

```text
IDENT
ORTH
PHON
MORPH
NOUN
ADJ
VERB
PRON
DET
NUM
CASE
AGR
SYNTAX
ORDER
NEG
QUEST
REL
COORD
SUBORD
CLITIC
LEX
SEM
PRAG
REGISTER
PARSE
GEN
META
```

Examples:

```text
CLM-ORTH-001
CLM-NOUN-004
CLM-SYNTAX-012
```

### 11.3 Observation IDs

Format:

```text
OBS-<NUMBER>
```

### 11.4 Review IDs

Format:

```text
REV-<NUMBER>
```

### 11.5 Identifier rules

- IDs are stable;
- IDs are never reused;
- retired records remain;
- renaming a claim does not change its ID;
- splitting one claim creates new IDs and supersedes the old record;
- merging claims creates a new claim or records the retained canonical ID explicitly.

---

## 12. Source-type vocabulary

Use one primary source type:

```text
official_standard
reference_grammar
descriptive_grammar
academic_article
book_chapter
dictionary
terminology_resource
corpus
treebank
parallel_corpus
wordlist
teaching_material
style_guide
official_website
institutional_website
community_resource
existing_gf_grammar
source_code
speaker_elicitation
speaker_review
field_notes
experiment
project_observation
historical_source
other
```

A source may have secondary characteristics in notes.

Do not classify a search-engine snippet, AI response, or unsourced summary as an authoritative source.

---

## 13. Source status vocabulary

Every source uses one status:

```text
candidate
reviewed
approved
restricted
deprecated
rejected
unavailable
```

### `candidate`

Located but not yet assessed.

### `reviewed`

Bibliographic identity, relevance, quality, and rights have been examined.

### `approved`

May support project claims within documented applicability.

### `restricted`

May be consulted but has access, quotation, redistribution, privacy, or licensing restrictions.

### `deprecated`

Previously used but no longer preferred.

Existing claim links remain traceable.

### `rejected`

Not reliable or applicable enough for project claims.

### `unavailable`

Known source cannot currently be accessed or verified.

A citation to an unavailable source must not be represented as reviewed evidence unless a preserved authorized copy or reliable locator exists.

---

## 14. Source-quality assessment

Quality is multidimensional.

Do not reduce source quality to one prestige score.

Assess the following:

| Dimension | Values |
|---|---|
| Authority | `strong`, `moderate`, `weak`, `unknown` |
| Directness | `direct`, `indirect`, `unclear` |
| Variety match | `exact`, `close`, `mixed`, `mismatch`, `unknown` |
| Register match | `exact`, `close`, `mixed`, `mismatch`, `unknown` |
| Time-period match | `current`, `historical_relevant`, `mixed`, `mismatch`, `unknown` |
| Method transparency | `high`, `medium`, `low`, `unknown` |
| Reproducibility | `high`, `medium`, `low`, `not_applicable`, `unknown` |
| Rights clarity | `clear`, `restricted`, `unclear` |
| Independence | `independent`, `derivative`, `unknown` |

### 14.1 Authority

Consider:

- author expertise;
- institutional responsibility;
- editorial or peer review;
- explicit scope;
- language-community authority;
- documented methodology.

### 14.2 Directness

Direct evidence describes or contains the exact construction, form, or variety.

Indirect evidence requires interpretation or transfer.

### 14.3 Variety and register match

Evidence for another variety may be useful, but transfer must be explicit.

### 14.4 Method transparency

A corpus with documented composition and query method is more interpretable than an unexplained count.

### 14.5 Reproducibility

A claim derived from data should record the query, filters, version, and result set.

### 14.6 Independence

Several websites copying one grammar are not independent triangulation.

---

## 15. Evidence-strength guidance

The following are guidelines, not automatic rankings.

### Strong combinations

- official standard plus current descriptive grammar;
- reference grammar plus representative corpus attestations;
- two independent grammars agreeing on the same variety;
- grammar description plus reviewed speaker judgments;
- reproducible corpus query plus explicit negative/positive controls;
- current source behavior plus targeted GF scenario when evaluating implementation rather than language truth.

### Limited combinations

- one dictionary entry with no syntax context;
- one isolated corpus example;
- one speaker judgment;
- teaching material without scope;
- another language variety;
- historical grammar used for current standard behavior;
- existing GF implementation with no external linguistic verification.

### Insufficient alone

- search-result snippet;
- unsourced forum comment;
- generated AI answer;
- project code comment;
- current gold file;
- passing compile;
- absence of a form in a small corpus;
- frequency without grammatical context.

---

## 16. Source registry

Create one row for every material source.

| Source ID | Short name | Type | Status | Language/variety | Date/version | Rights status | Primary use |
|---|---|---|---|---|---|---|---|
| `<SOURCE_ID>` | `<SHORT_NAME>` | `<SOURCE_TYPE>` | `<SOURCE_STATUS>` | `<VARIETY>` | `<DATE_OR_VERSION>` | `<RIGHTS_STATUS>` | `<USE>` |

The table is an index.

Each approved or restricted source requires a full record.

---

## 17. Full source record template

Copy this section for each source.

```markdown
## <SOURCE_ID> — <SHORT_NAME>

**Status:** candidate | reviewed | approved | restricted | deprecated | rejected | unavailable  
**Source type:** <SOURCE_TYPE>  
**Primary language/variety:** <LANGUAGE_OR_VARIETY>  
**Register/domain:** <REGISTER_OR_DOMAIN>  
**Time period:** <TIME_PERIOD>  
**Reviewed by:** <REVIEWER>  
**Reviewed at:** <YYYY-MM-DD>

### Bibliographic identity

- Author/editor/organization: <AUTHOR_OR_ORGANIZATION>
- Year/date: <YEAR_OR_DATE>
- Title: <TITLE>
- Container/publication: <JOURNAL_BOOK_SITE_OR_NONE>
- Publisher/institution: <PUBLISHER_OR_INSTITUTION>
- Edition/version: <EDITION_OR_VERSION>
- Pages/extent: <PAGES_OR_NONE>
- Identifier: <DOI_ISBN_HANDLE_CORPUS_ID_OR_NONE>
- Canonical URL: <URL_OR_NONE>
- Accessed at: <YYYY-MM-DD_OR_NONE>
- Local authorized reference: <PROJECT_RELATIVE_REFERENCE_OR_NONE>

### Scope and relevance

<WHAT_THE_SOURCE_COVERS_AND_WHY_IT_IS_RELEVANT>

### Applicability

- Variety match: exact | close | mixed | mismatch | unknown
- Register match: exact | close | mixed | mismatch | unknown
- Time-period match: current | historical_relevant | mixed | mismatch | unknown
- Population/data scope: <SCOPE>
- Known exclusions: <EXCLUSIONS>

### Quality review

- Authority: strong | moderate | weak | unknown
- Directness: direct | indirect | unclear
- Method transparency: high | medium | low | unknown
- Reproducibility: high | medium | low | not_applicable | unknown
- Independence: independent | derivative | unknown
- Main strengths: <STRENGTHS>
- Main limitations: <LIMITATIONS>
- Known source dependencies: <DEPENDENCIES_OR_NONE>

### Rights and handling

- Copyright holder: <HOLDER_OR_UNKNOWN>
- License/terms: <LICENSE_OR_TERMS>
- Rights clarity: clear | restricted | unclear
- Quotation allowed: <YES_NO_LIMITS>
- Redistribution allowed: <YES_NO_LIMITS>
- Local storage allowed: <YES_NO_LIMITS>
- Derived data allowed: <YES_NO_LIMITS>
- Attribution requirement: <REQUIREMENT>
- Privacy/personal data: <NONE_OR_DETAILS>
- Handling restrictions: <RESTRICTIONS_OR_NONE>

### Claims supported

- <CLAIM_ID>
- <CLAIM_ID>

### Claims challenged

- <CLAIM_ID_OR_NONE>

### Exact locators used

| Locator | Topic | Use |
|---|---|---|
| <PAGE_SECTION_EXAMPLE_QUERY> | <TOPIC> | <SUPPORT_CHALLENGE_CONTEXT> |

### Review notes

<NOTES>

### Supersession

- Replaced by: <SOURCE_ID_OR_NONE>
- Reason: <REASON_OR_NONE>
```

Do not paste long source passages into this record.

Use brief compliant quotations only when necessary and permitted.

Prefer paraphrase plus exact locator.

---

## 18. Claim registry

| Claim ID | Short claim | Type | Status | Confidence | Scope | Primary implementation area |
|---|---|---|---|---|---|---|
| `<CLAIM_ID>` | `<SHORT_CLAIM>` | `<CLAIM_TYPE>` | `<CLAIM_STATUS>` | `<CONFIDENCE>` | `<SCOPE>` | `<MODULE_OR_DOC>` |

The registry is an index.

Every material active claim requires a full record.

---

## 19. Full claim record template

Copy this section for each claim.

```markdown
## <CLAIM_ID> — <SHORT_CLAIM_TITLE>

**Claim type:** external_fact | project_convention | implementation_constraint | working_hypothesis | unverified_assumption  
**Status:** draft | supported | provisional | contested | rejected | superseded | not_applicable  
**Confidence:** high | medium | low | unknown  
**Owner:** <OWNER>  
**Last reviewed:** <YYYY-MM-DD>  
**Supersedes:** <CLAIM_ID_OR_NONE>  
**Superseded by:** <CLAIM_ID_OR_NONE>

### Claim

<ONE_PRECISE_FALSIFIABLE_OR_REVIEWABLE_STATEMENT>

### Scope

- Language/variety: <VARIETY>
- Register: <REGISTER>
- Time period: <TIME_PERIOD>
- Construction/domain: <DOMAIN>
- Applies to: <CATEGORIES_FUNCTIONS_OR_CONTEXTS>
- Does not apply to: <EXCLUSIONS>

### Terminology

<DEFINE_AMBIGUOUS_TERMS_USED_IN_THE_CLAIM>

### Supporting evidence

| Source/observation | Exact locator | Evidence relation | Strength | Notes |
|---|---|---|---|---|
| <SOURCE_ID_OR_OBS_ID> | <LOCATOR> | direct | <HIGH_MEDIUM_LOW> | <NOTES> |

### Counterevidence and limitations

| Source/observation | Exact locator | Conflict or limitation | Resolution |
|---|---|---|---|
| <SOURCE_ID_OR_OBS_ID_OR_NONE> | <LOCATOR> | <DETAIL> | <RESOLUTION_OR_OPEN> |

### Interpretation

<EXPLAIN_HOW_THE_EVIDENCE_SUPPORTS_THE_CLAIM_WITHOUT_EXCEEDING_IT>

### Alternatives considered

| Alternative | Evidence | Reason accepted/rejected |
|---|---|---|
| <ALTERNATIVE> | <SOURCE_IDS> | <RATIONALE> |

### Project decision

<STATE_THE_IMPLEMENTED_OR_DOCUMENTED_CHOICE>

For an external fact, distinguish the project’s implementation interpretation from the descriptive claim.

For a project convention, state explicitly that it is not a universal language fact.

### Implementation mapping

- Provider modules: <GF_MODULES_OR_NONE>
- Consumer modules: <GF_MODULES_OR_NONE>
- Categories/lincats: <CATEGORIES_OR_NONE>
- Functions/constructors: <FUNCTIONS_OR_NONE>
- Lexical entries: <ENTRIES_OR_NONE>
- Configuration fields: <FIELDS_OR_NONE>

### Validation mapping

- Checkpoint: <CHECKPOINT_OR_NONE>
- Scenario IDs: <SCENARIO_IDS_OR_NONE>
- Scenario sections: <SECTION_IDS_OR_NONE>
- Gold files: <GOLD_PATHS_OR_NONE>
- Manual review IDs: <REVIEW_IDS_OR_NONE>
- Last supporting run: <RUN_ID_OR_NONE>

### Release impact

- Release-blocking: yes | no | conditional
- Required maturity: <MATURITY>
- Accepted limitation: <LIMITATION_OR_NONE>
- Known issue: <KNOWN_ISSUE_ID_OR_NONE>
- Status-ledger entry: <LEDGER_ID_OR_NONE>

### Open questions

- <QUESTION_OR_NONE>

### Next action

- Action: <ACTION_OR_NONE>
- Owner: <OWNER_OR_NONE>
- Due/review trigger: <DATE_RELEASE_OR_CONDITION>
```

---

## 20. Claim-writing rules

A claim must be:

- precise;
- scoped;
- attributable;
- separable from implementation;
- reviewable;
- no broader than its evidence;
- explicit about variation;
- explicit about uncertainty;
- connected to project behavior when relevant.

### Good claim

```text
In the selected standard variety, the documented noun class distinguishes
<FEATURE VALUES> in <CONTEXT>, according to SRC-0001 §<LOCATOR> and
SRC-0002 example <NUMBER>.
```

### Weak claim

```text
The language always does this.
```

### Improved project convention

```text
For deterministic linearization, the project emits <VARIANT A> as canonical
output while accepting <VARIANT B> during parsing. This is a project
convention, not a claim that <VARIANT B> is ungrammatical.
```

---

## 21. Evidence-link relation vocabulary

Each evidence link uses one relation:

```text
supports
partially_supports
illustrates
defines_standard
attests
quantifies
challenges
contradicts
limits_scope
provides_method
provides_terminology
provides_implementation_precedent
```

### `supports`

Direct evidence for the claim.

### `partially_supports`

Supports only part of the claim or a narrower scope.

### `illustrates`

Provides an example but not sufficient general proof.

### `defines_standard`

Normative source establishes the selected standard convention.

### `attests`

Shows occurrence in data.

### `quantifies`

Provides frequency or distribution evidence.

### `challenges`

Raises a meaningful alternative or exception.

### `contradicts`

Directly conflicts under comparable scope.

### `limits_scope`

Shows the claim applies only under narrower conditions.

### `provides_method`

Supports research or validation methodology rather than language behavior.

### `provides_terminology`

Defines analytical terms.

### `provides_implementation_precedent`

Shows how another implementation modeled the issue.

Implementation precedent alone is not linguistic proof.

---

## 22. Observation register

Use observations for:

- corpus examples;
- elicitation responses;
- speaker review;
- field notes;
- reproducible experiments;
- project-specific data inspections.

| Observation ID | Type | Date | Variety/register | Related claims | Rights/privacy status |
|---|---|---|---|---|---|
| `<OBS_ID>` | `<OBSERVATION_TYPE>` | `<YYYY-MM-DD>` | `<SCOPE>` | `<CLAIM_IDS>` | `<STATUS>` |

---

## 23. Observation record template

```markdown
## <OBS_ID> — <SHORT_DESCRIPTION>

**Observation type:** corpus | elicitation | speaker_review | field_note | experiment | project_observation  
**Collected by:** <COLLECTOR>  
**Collected at:** <YYYY-MM-DD>  
**Reviewed by:** <REVIEWER>  
**Language/variety:** <VARIETY>  
**Register/context:** <REGISTER>  
**Related claims:** <CLAIM_IDS>

### Research question

<QUESTION>

### Method

<REPRODUCIBLE_METHOD>

### Data or prompt

<BOUNDED_DESCRIPTION_OR_AUTHORIZED_REFERENCE>

### Result

<RESULT>

### Interpretation

<INTERPRETATION>

### Limitations

<LIMITATIONS>

### Reproducibility

- Dataset/version: <DATASET_OR_NONE>
- Query/tool: <QUERY_OR_TOOL>
- Filters: <FILTERS>
- Random seed: <SEED_OR_NONE>
- Result count: <COUNT_OR_NONE>
- Preserved project-relative evidence: <PATH_OR_NONE>

### Consent, privacy, and rights

- Participant consent: <STATUS_OR_NOT_APPLICABLE>
- Anonymization: <STATUS_OR_NOT_APPLICABLE>
- Personal data: <DETAILS_OR_NONE>
- Redistribution: <ALLOWED_RESTRICTED_PROHIBITED>
- Quotation permission: <STATUS>
- Retention policy: <POLICY>

### Claim impact

- Supports: <CLAIM_IDS_OR_NONE>
- Challenges: <CLAIM_IDS_OR_NONE>
- Creates new question: <QUESTION_OR_NONE>
```

---

## 24. Speaker and consultant evidence

Speaker judgments can be valuable but require careful scope.

Record:

- participant code rather than unnecessary personal identity;
- self-described variety;
- relevant exposure and register;
- prompt wording;
- whether the task concerned acceptability, preference, interpretation, or production;
- whether alternatives were randomized;
- whether judgments were independent;
- whether discussion influenced later judgments;
- uncertainty and disagreement;
- consent and quotation rules.

Do not infer population-wide rules from one participant without qualification.

### 24.1 Participant code

Recommended form:

```text
SPK-<NUMBER>
```

The identity key, when needed, must be stored securely outside public project documentation.

### 24.2 Judgment vocabulary

Use explicit values such as:

```text
accepted
preferred
marginal
rejected
uncertain
not_evaluated
```

Do not reduce preference to grammaticality.

### 24.3 Disagreement

Speaker disagreement is evidence of variation or methodological uncertainty.

It must not be silently averaged away.

---

## 25. Corpus evidence

Every corpus-derived claim must record:

```text
corpus identity
version/date
language/variety composition
register composition
token/document scope
query
filters
normalization
deduplication
result count
sample-review method
negative controls
known bias
rights
```

### 25.1 Attestation versus grammar

Attestation supports occurrence.

It does not alone prove:

- full grammatical productivity;
- absence of alternatives;
- ungrammaticality of unattested forms;
- dialect universality;
- semantic equivalence.

### 25.2 Negative searches

A zero-result search must record:

- exact query;
- corpus size;
- spelling variants;
- morphological variants;
- tokenization assumptions;
- whether the construction is expected to be rare;
- why absence is informative.

Write:

```text
No instances were found under the recorded query.
```

Do not automatically write:

```text
The form does not exist.
```

### 25.3 Frequency

Frequency comparisons require comparable denominators and sampling conditions.

---

## 26. Dictionary evidence

Dictionary evidence may support:

- lemma spelling;
- inflection;
- gender or noun class;
- valency;
- register;
- meaning;
- multiword expressions;
- usage labels.

Dictionary evidence alone may be insufficient for:

- productive syntax;
- constituent order;
- full paradigm generalization;
- clause-level semantics;
- spoken acceptability.

Record edition, entry, sense, and usage labels precisely.

---

## 27. Grammar and article evidence

For grammar descriptions, record:

- selected variety;
- descriptive versus normative purpose;
- terminology mapping;
- example number;
- whether an example is constructed or attested;
- whether a rule is categorical or tendency-based;
- exceptions;
- scope limitations;
- publication date and later corrections.

Do not transfer an analysis into GF fields mechanically.

First state the linguistic claim, then document the project representation.

---

## 28. Official standards and style guides

Normative sources may define:

- spelling;
- punctuation;
- standard variants;
- terminology;
- official forms.

They do not necessarily describe:

- spontaneous usage;
- dialect variation;
- parse ambiguity;
- historical forms;
- all grammatical constructions.

A project may follow an official standard for canonical output while accepting additional attested input variants.

That relationship must be recorded as separate claims.

---

## 29. Existing GF implementations and source code

Existing GF/RGL code may provide:

- architecture precedent;
- constructor patterns;
- category mapping;
- compatibility insight;
- test ideas.

It must not be treated as sufficient linguistic evidence by itself.

For every borrowed or adapted pattern, record:

- upstream repository or distribution;
- exact revision/version;
- file and symbol;
- license;
- modification;
- linguistic verification;
- project-specific applicability.

Copying source without rights review is prohibited.

---

## 30. AI-generated material policy

AI-generated responses, summaries, translations, or analyses may be used only as:

```text
research leads
draft organization
query suggestions
candidate terminology
test brainstorming
```

They must not be registered as authoritative linguistic sources unless the actual underlying source is independently located and reviewed.

Requirements:

- verify every substantive claim independently;
- do not cite the AI response as primary evidence;
- do not upload restricted project data without authorization;
- preserve no secret or personal data in prompts;
- label any retained AI-assisted draft;
- review licensing and confidentiality policy.

A generated form is not evidence that speakers accept it.

A generated citation is not evidence that the source exists.

---

## 31. Web-source policy

Web sources require:

- stable publisher or responsible author;
- page title;
- publication/update date when available;
- access date;
- canonical URL;
- exact section or quoted locator;
- archived or preserved reference when permitted and necessary;
- assessment of volatility;
- assessment of derivative copying.

A web page can be authoritative when it is an official or scholarly publication.

“Found online” is not a quality category.

---

## 32. Citation and locator rules

Every evidence link must include the smallest useful locator.

Accepted locators:

```text
page number
page range
section heading
chapter
example number
table number
dictionary entry and sense
corpus query and result ID
dataset row or record ID
URL fragment
video/audio timestamp
source-code path and line/symbol
speaker observation ID
experiment run ID
```

Unacceptable locator:

```text
the whole book
somewhere on the website
a corpus search
the source code
```

When page numbering differs between print and PDF, record which numbering is used.

---

## 33. Quotation policy

Use quotation only when exact wording matters.

Requirements:

- quote minimally;
- include locator;
- respect copyright and license;
- distinguish quotation from translation;
- identify who produced any translation;
- preserve meaningful orthography;
- avoid copying large tables or paradigm sets without permission.

Prefer:

```text
paraphrased claim + exact locator
```

over long quotation.

---

## 34. Translation of source material

When evidence is translated:

- preserve the original source locator;
- identify original language;
- identify translator;
- label translation as project translation;
- record uncertainty;
- do not silently normalize technical terms;
- preserve relevant grammatical examples;
- retain original excerpt only within legal and practical limits.

Machine translation may assist review but requires human verification for material claims.

---

## 35. Terminology mapping

Different sources may use different analyses.

Maintain a mapping when terminology affects implementation.

| Project term | Source term | Source ID | Relationship | Notes |
|---|---|---|---|---|
| `<PROJECT_TERM>` | `<SOURCE_TERM>` | `<SOURCE_ID>` | equivalent | `<NOTES>` |
| `<PROJECT_TERM>` | `<SOURCE_TERM>` | `<SOURCE_ID>` | broader/narrower | `<NOTES>` |

Do not assume identical labels imply identical analyses.

Do not force all sources into one terminology before documenting differences.

---

## 36. Conflicting evidence

When sources conflict:

1. verify that they address the same variety and construction;
2. check time period and register;
3. inspect terminology differences;
4. inspect normative versus descriptive purpose;
5. inspect data and methodology;
6. seek independent evidence;
7. document the conflict;
8. select a project convention only when necessary;
9. retain alternatives and limitations;
10. define validation behavior explicitly.

Use claim status:

```text
contested
```

when no interpretation fully resolves the conflict.

Do not delete inconvenient counterevidence.

---

## 37. Variation policy

A claim about variation should distinguish:

```text
canonical output
accepted parse input
alternative linearization
dialect-specific form
register-specific form
historical form
marginal form
speaker-specific judgment
```

Possible project strategies:

- emit one canonical variant, parse several;
- emit several variants deterministically;
- separate variants by concrete language;
- restrict project scope to one variety;
- retain a provisional fallback;
- mark the feature out of scope.

The selected strategy is a project convention and must be documented.

---

## 38. Project convention record

A project convention may be recorded as a normal claim of type:

```text
project_convention
```

It should answer:

- What is selected?
- Why is selection necessary?
- Which alternatives exist?
- Is the selection linguistic, technical, or editorial?
- What input variants remain accepted?
- Which outputs are canonical?
- Which modules implement it?
- Which scenarios validate it?
- What would trigger reconsideration?

A project convention must not be worded as universal language truth.

---

## 39. Implementation-constraint record

An implementation constraint should answer:

- Which GF/RGL contract creates the constraint?
- Is the constraint temporary or stable?
- Which language distinction cannot currently be represented?
- What approximation is used?
- What evidence would justify architecture change?
- Does the constraint affect release claims?
- Which status-ledger entry tracks it?

Example structure:

```text
Current abstract syntax represents <DISTINCTION> as <CURRENT MODEL>.
This is an implementation constraint, not evidence that the language lacks
the distinction.
```

---

## 40. Working hypotheses and assumptions

### 40.1 Working hypothesis requirements

```text
evidence available
evidence missing
current interpretation
risk
test or research plan
owner
review trigger
```

### 40.2 Unverified assumption requirements

```text
assumption
implementation location
reason it was temporarily necessary
release impact
status-ledger ID
expiry
required research action
```

### 40.3 Promotion

A hypothesis or assumption becomes `supported` only after:

- evidence review;
- counterevidence review;
- scope definition;
- implementation mapping;
- validation mapping;
- reviewer approval.

Passing tests alone does not establish external linguistic truth.

---

## 41. Manual review register

Use manual reviews for criteria automation cannot establish fully.

| Review ID | Claim/domain | Reviewer role | Method | Evidence path | Decision | Date |
|---|---|---|---|---|---|---|
| `<REVIEW_ID>` | `<CLAIM_ID_OR_DOMAIN>` | `<ROLE>` | `<METHOD>` | `<PATH>` | `<DECISION>` | `<YYYY-MM-DD>` |

### 41.1 Review record template

```markdown
## <REVIEW_ID> — <TITLE>

**Reviewer:** <NAME_OR_ROLE>  
**Reviewer qualification/context:** <CONTEXT>  
**Date:** <YYYY-MM-DD>  
**Related claims:** <CLAIM_IDS>  
**Related scenarios:** <SCENARIO_IDS_OR_NONE>

### Material reviewed

<MATERIAL>

### Method

<METHOD>

### Acceptance criteria

<CRITERIA>

### Findings

<FINDINGS>

### Decision

accepted | accepted_with_limits | rejected | further_review_required

### Limitations

<LIMITATIONS>

### Follow-up

<ACTION_OR_NONE>
```

---

## 42. Implementation traceability

Every implemented material claim should map to one or more of:

```text
GF module
GF symbol
lincat field
parameter
paradigm
lexical entry
scenario
input file
gold section
manual review
release criterion
```

Recommended matrix:

| Claim ID | Provider modules | Consumer modules | Scenario IDs | Gold sections | Release criterion |
|---|---|---|---|---|---|
| `<CLAIM_ID>` | `<MODULES>` | `<MODULES>` | `<SCENARIOS>` | `<SECTIONS>` | `<CRITERION>` |

A claim with no implementation mapping may still be research background.

Mark it:

```text
implementation_status = not_implemented
```

where useful.

---

## 43. Validation traceability

Evidence and executable validation answer different questions.

| Evidence | Question |
|---|---|
| Grammar/dictionary/corpus | What behavior is externally supported? |
| Project convention | Which behavior did the project choose? |
| GF compile | Is the implementation type-correct? |
| Load scenario | Can the intended grammar load? |
| Linearization scenario | Does the project emit the expected form? |
| Parse scenario | Does the project accept the expected input? |
| Morphology scenario | Are expected paradigm cells produced? |
| Gold comparison | Did reviewed normalized output remain stable? |
| Manual review | Is output acceptable under the review criteria? |

A compile proves no linguistic claim by itself.

A source citation proves no implementation behavior by itself.

Both are needed for a release-significant implemented claim.

---

## 44. Research question backlog

| Question ID | Research question | Affected claims | Priority | Owner | Required evidence | Status |
|---|---|---|---|---|---|---|
| `RQ-<NUMBER>` | `<QUESTION>` | `<CLAIM_IDS>` | `<PRIORITY>` | `<OWNER>` | `<EVIDENCE_NEEDED>` | `<STATUS>` |

Recommended statuses:

```text
open
in_progress
blocked
answered
deferred
out_of_scope
```

An answered question should link to resulting claim or decision IDs.

---

## 45. Source acquisition backlog

| Candidate source | Reason needed | Access path | Rights concern | Owner | Status |
|---|---|---|---|---|---|
| `<SOURCE>` | `<REASON>` | `<PATH>` | `<CONCERN>` | `<OWNER>` | `<STATUS>` |

Do not register a source as reviewed before it is actually available and assessed.

---

## 46. Rights and licensing register

| Source/data ID | Copyright/owner | License or permission | Quotation | Redistribution | Derived data | Public release impact |
|---|---|---|---|---|---|---|
| `<ID>` | `<OWNER>` | `<TERMS>` | `<LIMITS>` | `<LIMITS>` | `<LIMITS>` | `<IMPACT>` |

### 46.1 Rights states

Use:

```text
clear
restricted
unclear
prohibited
not_applicable
```

### 46.2 Unclear rights

When rights are unclear:

- preserve only lawful bibliographic metadata;
- do not redistribute the source;
- avoid copied datasets or extensive excerpts;
- seek permission or replace the source;
- block public distribution when the release depends on unauthorized material.

### 46.3 Source code

Upstream GF/RGL code and copied lexical data require separate license review.

### 46.4 No license inference

Public availability does not imply permission to copy, redistribute, train models on, or publish derived datasets.

---

## 47. Privacy and ethics

### 47.1 Personal data

Collect only data necessary for the research purpose.

Avoid storing in public project files:

- legal names when a participant code is sufficient;
- contact details;
- private correspondence;
- voice recordings without permission;
- demographic details not needed for applicability;
- sensitive personal information.

### 47.2 Consent

Speaker or consultant evidence must record consent for:

- participation;
- quotation;
- anonymized publication;
- audio retention;
- redistribution;
- future research use.

### 47.3 Withdrawal

Where applicable, record the process for participant withdrawal and data removal.

### 47.4 Community sensitivity

Document known restrictions concerning sacred, private, stigmatized, endangered, or community-controlled language material.

### 47.5 Compensation and attribution

Record compensation or requested attribution where relevant and permitted.

### 47.6 Ethics uncertainty

When ethical handling is unclear, do not publish the material until reviewed.

---

## 48. Data retention

For each restricted dataset or observation, define:

```text
storage location
authorized users
encryption or access controls
retention period
backup policy
deletion policy
public/private classification
```

Do not place restricted raw data in:

```text
public project repository
gold files
AI-ready reports
unredacted CI artifacts
```

Validation assets should use approved, minimal, redistributable examples where possible.

---

## 49. Evidence files and repository policy

This register may reference authorized evidence files stored under a project-specific controlled path.

Recommended categories:

```text
project/research/bibliography/
project/research/notes/
project/research/queries/
project/research/derived/
```

These paths are illustrative.

The active project must define actual paths and source-selection exclusions.

Rules:

- GF source discovery must not include research files;
- restricted source copies must not be committed publicly;
- large corpora should not be duplicated unnecessarily;
- generated query results must record provenance;
- evidence file hashes may be recorded when integrity matters;
- local absolute paths must not be authoritative.

---

## 50. Reproducible corpus-query record

```markdown
## Query <QUERY_ID> — <TITLE>

- Dataset/source ID: <SOURCE_ID>
- Dataset version: <VERSION>
- Query language/tool: <TOOL>
- Query text or script: <PROJECT_RELATIVE_PATH_OR_INLINE_BOUNDED_QUERY>
- Filters: <FILTERS>
- Preprocessing: <PREPROCESSING>
- Deduplication: <METHOD>
- Date executed: <YYYY-MM-DD>
- Executed by: <RESEARCHER>
- Result count: <COUNT>
- Reviewed sample size: <COUNT>
- Preserved result path: <PATH>
- Result hash: <HASH_OR_NONE>
- Related claims: <CLAIM_IDS>
- Limitations: <LIMITATIONS>
```

A query result used in release-significant reasoning should be reproducible or its limitations explicit.

---

## 51. Lexical evidence record

Use a dedicated record when a lexical item has complex or contested behavior.

```markdown
## Lexical evidence — <LEMMA_OR_ENTRY_ID>

- Lemma: <LEMMA>
- Category: <GF_CATEGORY>
- Variety/register: <SCOPE>
- Canonical spelling: <FORM>
- Accepted variants: <FORMS>
- Morphological class: <CLASS>
- Valency/complements: <DETAILS>
- Meaning/sense scope: <SENSE>
- Usage labels: <LABELS>
- Sources: <SOURCE_IDS_AND_LOCATORS>
- Counterevidence: <SOURCE_IDS_OR_NONE>
- Project convention: <CONVENTION_OR_NONE>
- GF provider: <MODULE_AND_SYMBOL>
- Scenario coverage: <SCENARIO_IDS>
- Status: <STATUS>
```

Do not infer a complete paradigm from one dictionary form without an approved paradigm rule.

---

## 52. Paradigm evidence record

```markdown
## Paradigm evidence — <PARADIGM_ID>

- Category: <CATEGORY>
- Paradigm name: <NAME>
- Feature dimensions: <DIMENSIONS>
- Regularity class: <REGULAR_IRREGULAR_DEFECTIVE>
- Input/stem conditions: <CONDITIONS>
- Sources: <SOURCE_IDS_AND_LOCATORS>
- Attested examples: <EXAMPLES_OR_OBSERVATION_IDS>
- Exceptions: <EXCEPTIONS>
- Project implementation: <MODULE_AND_CONSTRUCTOR>
- Morphology scenario: <SCENARIO_ID>
- Gold sections: <SECTIONS>
- Confidence: <CONFIDENCE>
- Status: <STATUS>
```

---

## 53. Syntactic construction evidence record

```markdown
## Construction evidence — <CONSTRUCTION_ID>

- Construction: <NAME>
- Abstract function(s): <FUNCTIONS>
- GF categories: <CATEGORIES>
- Word order: <ORDER>
- Agreement: <AGREEMENT>
- Case/government: <CASE>
- Optionality: <OPTIONALITY>
- Semantic/pragmatic limits: <LIMITS>
- Sources: <SOURCE_IDS_AND_LOCATORS>
- Counterexamples: <SOURCE_OR_OBSERVATION_IDS>
- Project convention: <CONVENTION_OR_NONE>
- Implementation modules: <MODULES>
- Scenario coverage: <SCENARIOS>
- Parse expectations: <EXPECTATIONS>
- Linearization expectations: <EXPECTATIONS>
- Confidence/status: <CONFIDENCE_AND_STATUS>
```

---

## 54. Orthography evidence record

```markdown
## Orthography evidence — <ORTHOGRAPHY_RULE_ID>

- Rule: <RULE>
- Standard/variety: <SCOPE>
- Canonical output: <OUTPUT>
- Accepted input variants: <VARIANTS>
- Unicode code points when relevant: <CODE_POINTS>
- Sources: <SOURCE_IDS_AND_LOCATORS>
- Project convention: <CONVENTION_OR_NONE>
- Normalization impact: <IMPACT>
- Lexicon impact: <IMPACT>
- Scenario coverage: <SCENARIOS>
- Gold impact: <GOLD_SECTIONS>
- Status: <STATUS>
```

---

## 55. Evidence for negative or rejected behavior

A negative claim requires stronger care.

Examples:

```text
form is rejected
construction is unavailable
word order is not accepted
case cannot occur here
```

Accepted evidence may include:

- explicit grammar statement;
- controlled speaker rejection;
- contrastive elicitation;
- consistent absence plus positive controls in suitable data;
- formal incompatibility in the selected standard;
- project scope restriction labeled as convention.

Do not convert:

```text
not found
```

into:

```text
ungrammatical
```

without additional evidence.

Negative project tests must state whether they test:

- linguistic rejection;
- project scope;
- parser limitation;
- unsupported implementation;
- intentionally invalid GF input.

---

## 56. Evidence for ambiguity

When parsing or interpretation is ambiguous, record:

- all accepted readings;
- source evidence for each;
- whether ambiguity is lexical, morphological, syntactic, or contextual;
- whether the project preserves or resolves it;
- parse-count expectations;
- any deterministic report ordering;
- whether one reading is preferred but not exclusive.

Gold normalization must not remove meaningful ambiguity.

---

## 57. Evidence for defaults and fallbacks

A default or fallback must be classified.

| Kind | Meaning |
|---|---|
| Linguistic default | Evidence-supported unmarked language behavior |
| Project default | Deterministic project choice |
| Implementation fallback | Temporary technical substitute |
| Error recovery | Behavior used only after failure |

Do not describe an implementation fallback as a linguistic default.

Implementation fallbacks require `STATUS_LEDGER.md` entries.

---

## 58. Evidence-to-document map

| Claim domain | Documents that must agree |
|---|---|
| Language identity/variety | `LANGUAGE_OVERVIEW.md`, `project.toml` |
| Orthography | overview, morphology spec, validation spec |
| Morphology | `MORPHOLOGY_SPEC.md`, category contract |
| Syntax | `SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| Lincat interpretation | `CATEGORY_AND_LINCAT_CONTRACT.md` |
| Module ownership | architecture, dependency map, contract lock |
| Temporary approximation | status ledger, known issues |
| Breaking research-driven change | decision log |
| Validation expectation | validation spec, coverage matrix, scenarios/gold |
| Release claim | release criteria and release evidence |

An evidence-driven implementation change is incomplete until affected documents agree.

---

## 59. Research-driven change workflow

When new evidence changes project behavior:

1. create or update the source record;
2. create or update the claim;
3. record counterevidence;
4. review applicability;
5. decide whether the change is external fact, convention, or implementation constraint;
6. record an architectural decision when significant;
7. update morphology, syntax, lincat, or lexicon specifications;
8. update provider and consumers;
9. update scenarios;
10. review inputs;
11. update gold explicitly;
12. update status ledger and known issues;
13. run checkpoints and entrypoints;
14. run affected scenarios;
15. run release validation when release-significant;
16. record the supporting run and review.

No research-driven cross-file contract may change through one isolated source edit.

---

## 60. Claim review triggers

Review a claim when:

- a new authoritative source appears;
- a speaker or corpus observation conflicts;
- the selected variety changes;
- orthographic policy changes;
- a GF abstract or lincat changes;
- a scenario reveals unexplained output;
- a gold update changes accepted language behavior;
- a warning exposes a hidden assumption;
- a release blocker depends on the claim;
- a source is corrected, retracted, or becomes unavailable;
- rights or consent change;
- a major release is prepared.

---

## 61. Source review triggers

Review a source when:

- a new edition is used;
- the URL or dataset version changes;
- authors issue corrections;
- license terms change;
- the source becomes unavailable;
- applicability was misclassified;
- derivative copying is discovered;
- source quality was overstated;
- a claim relies on a passage not yet verified;
- the project moves to another language variety.

---

## 62. Evidence completeness levels

Use these project-level completeness labels:

```text
unregistered
catalogued
linked
triangulated
validated
release_supported
```

### `unregistered`

Evidence exists informally but has no source record.

Not acceptable for material release claims.

### `catalogued`

Source identity and rights are recorded.

### `linked`

Claims have precise evidence links.

### `triangulated`

Material claims use independent evidence or documented justification for a single-source exception.

### `validated`

Implemented claims map to executable or manual validation.

### `release_supported`

All release-significant claims meet project release criteria.

These are register-completeness labels, not source-quality scores.

---

## 63. Minimum evidence by claim impact

| Claim impact | Minimum expectation |
|---|---|
| Background only | catalogued source and scope |
| Documentation claim | precise source link and applicability |
| Lexical example | dictionary/attestation plus paradigm policy |
| Morphology rule | direct grammar evidence plus examples or reviewed data |
| Syntax constructor | direct description plus representative examples |
| Canonical output convention | evidence plus explicit project convention |
| Parse acceptance | evidence plus parse scenario |
| Negative parse expectation | explicit negative evidence or scoped project rule |
| Lincat architecture change | linguistic rationale plus GF contract decision |
| Release-significant behavior | reviewed evidence, implementation mapping, validation, release criterion |
| Public dataset or lexicon release | rights and attribution review |

A project may define stricter requirements.

---

## 64. Single-source exceptions

Sometimes only one usable source exists.

A single-source claim may be accepted when:

- the source is directly applicable;
- limitations are explicit;
- alternatives were searched;
- no material counterevidence is known;
- confidence reflects the limitation;
- project convention is distinguished from external fact;
- review trigger is recorded.

Write:

```text
Single-source exception approved because <REASON>.
```

Do not imply triangulation.

---

## 65. Evidence gaps

Use an evidence-gap record:

```markdown
## Evidence gap — <GAP_ID>

- Question: <QUESTION>
- Affected claims: <CLAIM_IDS>
- Current behavior: <IMPLEMENTATION_OR_NONE>
- Risk: <RISK>
- Sources searched: <SOURCE_IDS_OR_SEARCH_RECORD>
- Missing evidence: <MISSING_EVIDENCE>
- Temporary classification: working_hypothesis | unverified_assumption | out_of_scope
- Status-ledger ID: <ID_OR_NONE>
- Release impact: <IMPACT>
- Next action: <ACTION>
- Owner: <OWNER>
- Review trigger: <DATE_OR_CONDITION>
```

A gap must not disappear merely because the current code compiles.

---

## 66. Search record

For high-impact unresolved questions, record the search process.

```markdown
## Search record — <SEARCH_ID>

- Research question: <QUESTION>
- Date: <YYYY-MM-DD>
- Researcher: <NAME_OR_ROLE>
- Catalogs/databases/sites searched: <LIST>
- Search terms: <TERMS>
- Languages used in search: <LANGUAGES>
- Inclusion criteria: <CRITERIA>
- Exclusion criteria: <CRITERIA>
- Candidate sources found: <SOURCE_IDS>
- Unavailable sources: <SOURCES>
- Result: <SUMMARY>
- Limitations: <LIMITATIONS>
```

This does not need to become a systematic-review protocol unless the project requires one.

---

## 67. Release evidence integration

Before release, review:

```text
supported claims
provisional release-significant claims
contested claims
unverified assumptions
rights restrictions
manual reviews
open evidence gaps
research-driven known issues
```

Release is blocked when:

- a mandatory language claim is unsupported;
- a release-significant assumption has no approved exception;
- source rights prohibit intended distribution;
- participant consent is insufficient;
- a required manual review is incomplete;
- implementation contradicts the accepted claim;
- validation does not test the implemented interpretation;
- source scope does not match the declared language variety;
- decisive counterevidence is ignored.

---

## 68. Release sign-off summary

Copy this summary into the active project and complete it for a release.

```markdown
## Research evidence release sign-off — <PROJECT_VERSION>

- Project ID: <PROJECT_ID>
- Language/variety: <LANGUAGE_AND_VARIETY>
- Review date: <YYYY-MM-DD>
- Reviewer: <RESEARCH_REVIEWER>
- Supported active claims: <COUNT>
- Provisional active claims: <COUNT>
- Contested active claims: <COUNT>
- Unverified assumptions: <COUNT>
- Release-blocking evidence gaps: <COUNT>
- Restricted sources affecting release: <COUNT>
- Manual reviews complete: yes | no
- Rights review complete: yes | no
- Last validation run: <RUN_ID>
- Decision: approved | approved_with_limits | rejected

### Approved limitations

- <LIMITATION_OR_NONE>

### Required follow-up

- <ACTION_OR_NONE>
```

---

## 69. Initialization checklist

```text
[ ] Replace project identity placeholders
[ ] Identify primary language variety
[ ] Identify orthography standard
[ ] Name research reviewer or role
[ ] Create source registry
[ ] Register core grammar sources
[ ] Register core dictionary sources
[ ] Register official standards where applicable
[ ] Register corpora or datasets where applicable
[ ] Register existing GF/RGL precedents separately
[ ] Review source rights
[ ] Create initial claim registry
[ ] Classify every claim type
[ ] Assign claim statuses
[ ] Assign confidence
[ ] Add exact source locators
[ ] Add counterevidence
[ ] Record project conventions
[ ] Record implementation constraints
[ ] Record working hypotheses
[ ] Record unverified assumptions
[ ] Link assumptions to status ledger
[ ] Map claims to morphology and syntax documents
[ ] Map claims to GF modules
[ ] Map implemented claims to scenarios
[ ] Map release-significant claims to release criteria
[ ] Create manual review records where needed
[ ] Create research-question backlog
[ ] Document participant consent policy
[ ] Document corpus-query reproducibility
[ ] Document restricted-data handling
[ ] Remove example-only records
[ ] Verify no required placeholder remains
[ ] Verify every public linguistic claim has evidence or explicit classification
```

---

## 70. Review checklist

```text
[ ] Project identity is current
[ ] Selected variety is explicit
[ ] Every material source has a stable ID
[ ] Every material claim has a stable ID
[ ] Source bibliographic data is complete
[ ] Source status is accurate
[ ] Source applicability is assessed
[ ] Source limitations are recorded
[ ] Rights status is recorded
[ ] Exact locators are present
[ ] Claims are precise and scoped
[ ] Claim types are correct
[ ] Claim statuses are correct
[ ] Confidence is justified
[ ] Supporting evidence does not exceed source scope
[ ] Counterevidence is retained
[ ] Variation is explicit
[ ] Project conventions are labeled
[ ] Implementation constraints are labeled
[ ] Hypotheses have next actions
[ ] Assumptions have ledger entries
[ ] Speaker evidence has consent and scope
[ ] Corpus queries are reproducible
[ ] Negative claims meet stronger evidence requirements
[ ] Existing GF code is not treated as sole linguistic proof
[ ] AI-generated material is not treated as authority
[ ] Implementation mappings are current
[ ] Validation mappings are current
[ ] Gold changes are traceable
[ ] Known issues and release criteria agree
[ ] Restricted data is not exposed
[ ] Manual reviews are current
[ ] Superseded records remain traceable
[ ] Last reviewed date is current
```

---

## 71. Anti-drift indicators

Probable research-evidence drift exists when:

- a language claim appears in code or documentation with no claim ID;
- one source is cited with no exact locator;
- a source is called authoritative without quality review;
- evidence for another variety is presented as exact-match evidence;
- one speaker is treated as universal proof;
- a corpus attestation is treated as productivity proof;
- corpus absence is treated as ungrammaticality;
- a dictionary form is expanded into a full paradigm without a rule;
- an existing GF grammar is treated as linguistic authority by itself;
- an AI response is cited as source evidence;
- a project convention is presented as external fact;
- an implementation limitation is presented as a language property;
- a hypothesis is described as stable;
- counterevidence is omitted;
- a gold file becomes the only support for a claim;
- a compile result is presented as linguistic proof;
- a source edition changes but the record does not;
- a web page changes with no access/version review;
- quotation exceeds permission;
- restricted data appears in CI artifacts;
- participant identity is exposed unnecessarily;
- source rights are assumed from public availability;
- a release-significant assumption has no ledger entry;
- a claim changes without affected scenarios or docs;
- a gold change alters accepted behavior without evidence review;
- a source is superseded but active claims still rely on it silently;
- claims and selected project variety disagree;
- unresolved placeholders remain in the active file.

Every indicator requires review before completion or release.

---

## 72. Minimal active-project form

The active project may shorten the instructional sections, but it must retain:

```text
project identity
evidence classification
source registry
full source records
claim registry
full claim records
counterevidence
rights and privacy register
implementation mapping
validation mapping
research backlog
manual review records
release sign-off summary
last reviewed
```

Removing one of these elements requires a documented project reason.

---

## 73. Completion criteria

The active `RESEARCH_EVIDENCE.md` is structurally complete when:

```text
[ ] It describes one active GF project
[ ] No required placeholder remains
[ ] Core sources are registered
[ ] Core claims are registered
[ ] Claims have exact evidence links
[ ] Claim types distinguish facts, conventions, constraints, hypotheses, and assumptions
[ ] Applicability is reviewed
[ ] Counterevidence is recorded
[ ] Rights status is recorded
[ ] Restricted data handling is documented
[ ] Implemented claims map to GF modules
[ ] Release-significant claims map to validation
[ ] Assumptions map to the status ledger
[ ] Open questions have owners or are explicitly deferred
[ ] Manual review requirements are represented
[ ] Source and claim histories remain traceable
```

It is release-complete only when all release-significant claims satisfy project release criteria.

---

## 74. Compact record examples

These are structural examples only and must be replaced or removed.

### 74.1 Example source index row

```text
SRC-0001 | <SHORT GRAMMAR NAME> | reference_grammar | approved |
<PRIMARY_VARIETY> | <EDITION> | restricted | noun morphology
```

### 74.2 Example external-fact claim

```text
CLM-NOUN-001
Type: external_fact
Status: supported
Claim: <PRECISE NOUN-MORPHOLOGY CLAIM>
Evidence: SRC-0001 p. <PAGE>; SRC-0002 example <NUMBER>
Implementation: <MORPHOLOGY MODULE>
Validation: <MORPHOLOGY SCENARIO SECTION>
```

### 74.3 Example project convention

```text
CLM-ORTH-002
Type: project_convention
Status: supported
Claim: Canonical linearization uses <VARIANT A>; parsing may accept <VARIANT B>.
Evidence: SRC-0003 defines both variants.
Rationale: deterministic output and selected standard.
```

### 74.4 Example implementation constraint

```text
CLM-META-001
Type: implementation_constraint
Status: provisional
Claim: Current GF representation collapses <DISTINCTION> at <BOUNDARY>.
This does not assert that the language lacks the distinction.
Ledger: <LEDGER_ID>
```

---

## 75. Final enforcement rule

Research evidence is not a decorative bibliography.

It is the traceability layer connecting external language knowledge, project choices, GF implementation, executable validation, and release claims.

Therefore:

> No active GF project may present an externally testable linguistic statement as established project truth unless the statement has a stable claim record, appropriately scoped reviewed evidence, explicit treatment of counterevidence and uncertainty, and—when implemented—traceable GF and validation mappings.
