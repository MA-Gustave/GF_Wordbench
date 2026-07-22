# GF Wordbench Project — Research Evidence

**Document ID:** `GF-WB-PROJECT-RESEARCH-EVIDENCE`  
**Status:** Normative project evidence registry  
**Applies to:** Linguistic claims, language-specific implementation decisions, source materials, elicitation, corpus observations, GF experiments, and validation evidence for the one active project under `project/`  
**Target path:** `project/docs/RESEARCH_EVIDENCE.md`  
**Owner:** Active project maintainers  
**Framework owner:** GF Wordbench maintainers  
**Canonical path base:** Active project root  
**Current evidence state:** No project-specific research claims or bibliographic sources were established from the available active-project materials  
**Last structural review:** 2026-07-22  

---

## 1. Purpose

This document records the evidence supporting language-specific decisions in the active GF project.

It provides traceability between:

```text
linguistic observation
    -> research claim
    -> cited evidence
    -> implementation decision
    -> GF provider and consumers
    -> executable validation
    -> reviewed project status
```

The registry exists to prevent unsupported analyses from becoming permanent project architecture merely because they:

- compile;
- appear plausible;
- were produced by an AI system;
- match one isolated example;
- were copied from another language;
- were inherited from a generic RGL implementation;
- have no immediate failing test.

This document distinguishes:

1. **linguistic evidence** — why a language analysis is believed to be accurate;
2. **implementation rationale** — why the analysis is encoded in a particular GF structure;
3. **validation evidence** — whether the implementation compiles and behaves as expected.

All three may be required.

---

## 2. Core rule

> Every release-significant language claim must have an identifiable source, a reviewable interpretation, an implementation trace, and validation evidence appropriate to its risk.

A GF compile result proves that GF accepts the implementation.

It does not, by itself, prove that the implementation describes the language correctly.

---

## 3. No-fabrication rule

The active project must not contain fabricated:

- citations;
- quotations;
- page numbers;
- corpus counts;
- speaker judgments;
- dictionary entries;
- grammatical examples;
- source metadata;
- research conclusions;
- consensus claims;
- publication identifiers;
- links;
- experiment results.

When evidence is unavailable, record:

```text
Evidence gap
```

Do not write a plausible replacement.

AI-generated content is not an external research source.

An AI system may help:

- organize material;
- generate search terms;
- compare supplied sources;
- draft a neutral summary;
- identify missing fields;
- propose tests.

Its output must be verified against identifiable evidence before being treated as a supported linguistic claim.

---

## 4. Current project-specific population state

The available active-project documentation does not establish a verified language identity, completed source inventory, or bibliographic research corpus.

Therefore, this version contains:

- a normative evidence methodology;
- stable identifiers;
- source-quality rules;
- traceability requirements;
- empty project-specific registries;
- release gates for future population.

It does not assert language-specific facts.

Current verified project-specific claims:

```text
None recorded.
```

Current verified bibliographic sources:

```text
None recorded.
```

Current verified corpus studies:

```text
None recorded.
```

Current verified elicitation sessions:

```text
None recorded.
```

Current verified research experiments:

```text
None recorded.
```

This absence must remain visible until authoritative material is reviewed.

---

# 5. Scope

This registry covers evidence for project decisions involving:

- orthography;
- phonology when represented by project resources;
- morphology;
- inflection;
- derivation;
- agreement;
- case;
- gender or noun class;
- number;
- person;
- tense;
- aspect;
- mood;
- voice;
- definiteness;
- polarity;
- clitics;
- word order;
- constituent structure;
- subcategorization;
- valency;
- auxiliaries;
- copulas;
- negation;
- questions;
- relative clauses;
- coordination;
- comparison;
- numerals;
- pronouns;
- determiners;
- adpositions;
- lexical selection;
- idiomatic or construction-specific behavior;
- punctuation affecting linearization;
- script and Unicode handling;
- dialect or register choices;
- accepted variants;
- excluded variants;
- fallback behavior;
- RGL inheritance and overrides;
- scenario examples used as linguistic acceptance criteria;
- gold output representing accepted behavior.

---

## 6. Out of scope

This document does not own:

- framework architecture;
- Python implementation contracts;
- external process contracts;
- persisted JSON/TOML schemas;
- module import inventory;
- lincat field definitions in full;
- temporary implementation status;
- release procedure;
- raw run logs;
- general project changelog entries.

Those belong to:

```text
docs/
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
project/docs/VALIDATION_SPEC.md
```

This document links to those owners.

It does not duplicate them.

---

# 7. Evidence model

The project evidence model contains six distinct entities:

```text
Source
Claim
Observation
Decision
Implementation trace
Validation trace
```

### 7.1 Source

An identifiable external or project-generated evidence provider.

### 7.2 Claim

A precise proposition about the language, usage, orthography, or implementation constraints.

### 7.3 Observation

A bounded datum obtained from a corpus, elicitation session, dictionary lookup, grammar passage, experiment, or expert review.

### 7.4 Decision

The project’s reviewed interpretation and chosen treatment.

### 7.5 Implementation trace

The modules, categories, functions, lincats, helpers, or lexicon entries implementing the decision.

### 7.6 Validation trace

The compile target, scenario, gold file, generated artifact, or manual review proving that the implementation satisfies the chosen contract.

These entities must not be collapsed into one free-form note.

---

# 8. Stable identifiers

Canonical identifiers:

```text
RE-SRC-NNNN   source
RE-CLM-NNNN   claim
RE-OBS-NNNN   observation
RE-DEC-NNNN   research-backed project decision
RE-EXP-NNNN   experiment or elicitation protocol
RE-GAP-NNNN   unresolved evidence gap
RE-CON-NNNN   contradiction or conflicting-evidence case
```

Examples of valid identifier form:

```text
RE-SRC-0001
RE-CLM-0001
RE-OBS-0001
RE-DEC-0001
RE-EXP-0001
RE-GAP-0001
RE-CON-0001
```

Numbers:

- are four digits;
- are unique within their entity family;
- are allocated sequentially;
- are never reused;
- remain stable after retirement;
- do not encode language, module, or category meaning.

---

## 9. Identifier lifecycle

A source or claim identifier remains stable even when:

- the source is superseded;
- the claim is narrowed;
- the implementation moves;
- a newer decision replaces it;
- evidence becomes disputed.

Do not renumber the registry to remove gaps.

A withdrawn record remains available with its final state and rationale.

---

# 10. Evidence-state vocabulary

Research evidence uses a dedicated human-governance vocabulary.

Canonical claim assessment:

```text
Open
Supported
Disputed
Rejected
Superseded
```

These values are not GF Wordbench validation statuses.

They must not appear in `FileResult.status` or `ScenarioResult.status`.

---

## 11. `Open`

Use when:

- the claim is under investigation;
- evidence is missing or insufficient;
- sources have not been reviewed;
- interpretation remains unresolved.

An `Open` release-significant claim must also have an evidence-gap record.

---

## 12. `Supported`

Use when:

- evidence satisfies the project’s threshold;
- source interpretation was reviewed;
- known important counterevidence is addressed;
- the claim is precise enough to implement or retain.

`Supported` does not mean universally undisputed in the academic literature.

The scope and limitations must remain explicit.

---

## 13. `Disputed`

Use when:

- credible sources conflict;
- speaker judgments vary;
- corpus behavior is unstable;
- dialect/register analysis is unresolved;
- project reviewers disagree about interpretation.

A disputed claim may still have a project implementation.

The implementation must be labeled as a project choice rather than universal language fact.

---

## 14. `Rejected`

Use when reviewed evidence does not support the claim or the project deliberately determines that it should not guide implementation.

Rejected claims remain recorded to prevent reintroduction without new evidence.

---

## 15. `Superseded`

Use when a newer claim or analysis replaces the record.

The record must identify:

```text
superseded_by
```

The newer record must identify:

```text
supersedes
```

---

# 16. Implementation-state separation

Research assessment and implementation state are separate.

Implementation state belongs primarily to:

```text
project/docs/STATUS_LEDGER.md
```

Possible ledger states may include:

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

Example:

```text
research assessment = Supported
implementation state = partial
```

Another example:

```text
research assessment = Disputed
implementation state = stable project choice
```

The research registry must not conceal implementation incompleteness.

---

# 17. Validation-status separation

Executable validation uses only:

```text
OK
FAIL
ERROR
SKIPPED
```

Research assessment uses:

```text
Open
Supported
Disputed
Rejected
Superseded
```

Valid relationship:

```text
Claim RE-CLM-0008 = Supported
Scenario result = FAIL
```

Meaning:

- the linguistic claim is supported;
- the current implementation does not satisfy it.

Another valid relationship:

```text
Claim RE-CLM-0012 = Open
Scenario result = OK
```

Meaning:

- the implementation behaves consistently;
- the project has not established that the behavior is linguistically correct.

---

# 18. Source classes

Canonical source classes:

```text
official_standard
descriptive_grammar
peer_reviewed_research
academic_reference
dictionary
corpus
language_resource
native_speaker_elicitation
expert_review
community_documentation
GF_or_RGL_documentation
upstream_source_code
project_experiment
project_validation
historical_project_note
web_reference
```

These values are documentation categories.

A future machine registry requires a schema before serializing them.

---

## 19. Official standard

Examples:

- orthographic standard;
- language academy publication;
- government language standard;
- official terminology guide;
- codified educational standard.

Strengths:

- authoritative for prescribed standard usage;
- often stable and citable.

Limitations:

- may not describe actual usage;
- may omit dialects;
- may be outdated;
- may prescribe rather than analyze.

Record whether the project implements:

```text
prescriptive standard
descriptive usage
both with explicit variants
```

---

## 20. Descriptive grammar

A descriptive grammar is often a primary source for broad morphology and syntax.

Required citation detail:

- author or editor;
- title;
- edition;
- publisher;
- year;
- page, section, table, or example number;
- language variety described;
- access location.

Do not cite an entire grammar for a narrow claim without a location.

---

## 21. Peer-reviewed research

Use for specialized or contested phenomena.

Record:

- authors;
- title;
- publication;
- year;
- volume/issue where applicable;
- pages;
- DOI or stable identifier where available;
- exact section supporting the claim;
- research population or variety;
- methodological limits.

Peer review increases credibility.

It does not eliminate the need to check scope.

---

## 22. Academic reference

Includes:

- handbook chapter;
- dissertation;
- thesis;
- conference proceedings;
- scholarly reference work;
- technical report from a recognized institution.

Assess quality based on:

- methods;
- documentation;
- accessibility;
- independent corroboration;
- relevance to the target variety.

Do not rank all academic-looking documents equally.

---

## 23. Dictionary

A dictionary can support:

- lemma existence;
- spelling;
- gender/class;
- inflection;
- valency notes;
- register;
- senses;
- examples.

A dictionary alone may be insufficient for:

- productive syntax;
- complete paradigms;
- word-order rules;
- absence claims;
- universal grammaticality.

Record dictionary edition and entry location.

---

## 24. Corpus

A corpus is evidence about attested use.

Every corpus observation must record:

```text
corpus name
corpus version or access date
license/access conditions
query
filters
sample size
raw hit count
reviewed hit count
excluded hits
annotation method
result summary
limitations
saved query or script path
saved result path where permitted
```

Corpus frequency does not automatically determine grammaticality.

Absence from a finite corpus is not proof of impossibility.

---

## 25. Language resource

Includes:

- treebank;
- tagged corpus;
- morphological lexicon;
- word list;
- terminology database;
- pronunciation lexicon;
- parallel corpus;
- Universal Dependencies resource;
- academic dataset.

Record:

- version;
- license;
- annotation scheme;
- data provenance;
- target variety;
- known errors;
- transformation applied;
- whether the project redistributes any content.

---

## 26. Native-speaker elicitation

Elicitation can provide valuable targeted judgments.

Required metadata:

```text
session identifier
date
protocol version
participant anonymized identifier
participant variety/background relevant to the claim
consent status
prompt set
presentation order
response scale
exact response or coded response
researcher notes
known priming/context effects
data-storage location
privacy restrictions
```

One speaker’s judgment must not be described as universal language behavior.

---

## 27. Expert review

Expert review may be used when:

- published sources are incomplete;
- terminology requires specialist interpretation;
- implementation choices need linguistic review.

Record:

- reviewer role;
- relevant expertise;
- review date;
- material reviewed;
- conclusion;
- disagreements;
- whether the review was independent.

Personal identity may be omitted from the public repository where privacy requires.

---

## 28. Community documentation

Community documentation may be useful for:

- colloquial usage;
- contemporary terminology;
- dialect notes;
- practical examples.

It must be labeled clearly.

It should not be the only support for a high-risk core grammar rule when stronger evidence is reasonably available.

---

## 29. GF or RGL documentation

GF/RGL documentation supports claims about:

- GF syntax;
- module composition;
- RGL APIs;
- category meanings;
- inherited implementation behavior;
- tool capabilities.

It does not automatically support language-specific correctness.

Example:

```text
RGL documents how a category is represented.
A language source is still needed to justify how the active language realizes it.
```

---

## 30. Upstream source code

Upstream GF/RGL source may be inspected when documentation is incomplete.

Record:

- repository/project;
- module path;
- commit/tag/version;
- relevant symbol;
- local interpretation;
- license;
- whether behavior was confirmed by an executable test.

Copying upstream implementation does not remove the need to justify language-specific applicability.

---

## 31. Project experiment

A project experiment is controlled evidence produced to answer a defined question.

Examples:

- compare two GF lincat representations;
- test a morphological table;
- examine generation coverage;
- check parse ambiguity;
- compare alternative word-order rules;
- measure corpus coverage;
- evaluate normalization stability.

An experiment must have:

- hypothesis;
- method;
- inputs;
- environment;
- output;
- interpretation;
- limitations;
- reproducibility path.

---

## 32. Project validation

Compilation, scenarios, gold comparisons, and PGF builds are implementation evidence.

They prove properties such as:

- type coherence;
- executable behavior;
- output stability;
- scenario completion;
- artifact production.

They do not replace independent linguistic evidence.

---

## 33. Historical project note

Historical notes may explain prior choices.

They are not automatically current evidence.

A historical note must be labeled:

```text
historical
```

and reviewed before reuse.

---

## 34. Web reference

A web page may support a claim when:

- the publisher is identifiable;
- content is stable enough to cite;
- authorship or institutional ownership is clear;
- stronger primary sources are unavailable or unnecessary.

Record:

- page title;
- author/organization;
- publication/update date where available;
- access date;
- stable URL;
- archived URL where permitted;
- exact section;
- reliability limitations.

Search-result snippets are not sources.

---

# 35. Source-quality assessment

Each source record includes a qualitative assessment:

```text
High
Moderate
Contextual
Weak
```

This assessment is project review metadata.

It is not an absolute ranking of publication types.

---

## 36. `High`

Use when the source is strongly authoritative and directly relevant to the claim.

Examples may include:

- authoritative descriptive grammar with exact section;
- official orthographic standard for a standard spelling claim;
- well-documented peer-reviewed study directly targeting the variety;
- high-quality corpus study with reproducible query and reviewed data.

---

## 37. `Moderate`

Use when the source is credible but has limitations.

Examples:

- respected dictionary for a syntax-adjacent claim;
- dissertation with clear methods but limited scope;
- corpus evidence with incomplete annotation;
- expert review without independent corroboration.

---

## 38. `Contextual`

Use when the source helps interpret or illustrate but should not carry the claim alone.

Examples:

- community documentation;
- educational page;
- upstream implementation;
- a small set of naturally occurring examples;
- one elicitation session.

---

## 39. `Weak`

Use when reliability or relevance is limited.

Examples:

- anonymous forum post;
- unsourced summary;
- search snippet;
- AI-generated answer;
- isolated example without context;
- inaccessible citation copied from another document.

Weak material may be recorded as a research lead.

It must not be cited as decisive evidence.

---

# 40. Evidence thresholds

The required threshold depends on claim risk.

Canonical risk levels:

```text
R1 low
R2 moderate
R3 high
R4 critical
```

---

## 41. R1 — Low risk

Examples:

- one lexical spelling;
- one non-release example;
- documentation wording;
- optional display label.

Recommended evidence:

- one credible source;
- or one reviewed project observation.

Validation:

- targeted compile or scenario where implemented.

---

## 42. R2 — Moderate risk

Examples:

- regular lexical paradigm;
- productive orthographic operation;
- category-specific agreement behavior;
- optional syntax variant.

Recommended evidence:

- one direct authoritative source;
- plus corpus, dictionary, elicitation, or independent corroboration.

Validation:

- provider compile;
- representative scenario;
- gold when output should remain stable.

---

## 43. R3 — High risk

Examples:

- core lincat design;
- case/agreement architecture;
- verb paradigm architecture;
- negation strategy;
- major word-order rule;
- pronoun/clitic architecture;
- entrypoint-wide syntax behavior.

Required evidence:

- at least one strong direct source;
- one independent corroborating source or reproducible dataset;
- documented counterevidence review;
- reviewed implementation decision.

Validation:

- provider and consumer compilation;
- checkpoint;
- representative positive cases;
- representative negative or contrastive cases where feasible;
- gold-backed scenario where deterministic.

---

## 44. R4 — Critical

Examples:

- language identity and script standard;
- release-wide module suffix or orthography choice;
- abstract/concrete category interpretation affecting the full grammar;
- breaking redesign of public lincats;
- dialect exclusion defining project scope;
- release entrypoint behavior with broad linguistic impact.

Required evidence:

- authoritative primary support;
- independent corroboration;
- explicit decision-log entry;
- affected-consumer review;
- migration analysis;
- release validation.

A critical claim cannot be accepted solely through implementation convenience.

---

# 45. Evidence sufficiency rules

Evidence is sufficient only when:

- the claim is precise;
- source scope matches claim scope;
- source locations are recorded;
- contradictory evidence is addressed;
- dialect/register assumptions are explicit;
- implementation interpretation is documented;
- required risk threshold is met;
- validation traces exist where implemented.

Evidence count alone is insufficient.

Three sources repeating the same unsupported statement do not equal independent corroboration.

---

# 46. Claim precision

A claim must be falsifiable or reviewable.

Poor:

```text
The language has flexible word order.
```

Better structure:

```text
In the project’s selected standard variety and clause type, constituent order X
is treated as the neutral linearization, while order Y is represented as an
explicit marked variant.
```

The final active claim must use the real language-specific terms and source references.

This document does not supply them.

---

# 47. Scope fields

Every claim records:

```text
language variety
register
time period
orthographic standard
construction
category
lexical class
polarity
clause type
information-structure condition
known exceptions
```

Use only applicable fields.

Do not generalize a restricted observation beyond its scope.

---

# 48. Positive and negative claims

Positive claim:

```text
A form or construction is accepted under defined conditions.
```

Negative claim:

```text
A form or construction is excluded under defined conditions.
```

Negative claims require special caution.

Recommended support:

- explicit source statement;
- controlled elicitation;
- robust contrastive evidence;
- analysis of alternative readings.

Corpus absence alone does not establish ungrammaticality.

---

# 49. Variant policy

When sources document multiple variants, record:

- each form;
- geographic scope;
- social/register scope;
- standard status;
- frequency evidence;
- project treatment;
- generation policy;
- parse acceptance policy;
- default linearization;
- validation scenarios.

Do not erase variation merely to simplify one string output.

A project may choose one default.

The choice must be labeled as a project policy.

---

# 50. Dialect and register

The active project must define its target scope in:

```text
project/docs/LANGUAGE_ARCHITECTURE.md
```

Research records must identify whether evidence applies to:

- selected standard;
- regional variety;
- historical variety;
- colloquial register;
- formal register;
- literary register;
- technical register;
- mixed or unspecified data.

Unspecified scope reduces evidence strength.

---

# 51. Orthography and Unicode

Evidence for orthographic behavior should record:

- standard or descriptive source;
- script;
- Unicode normalization assumptions;
- capitalization;
- punctuation;
- apostrophe/hyphen behavior;
- alternate spellings;
- transliteration policy;
- combining-mark policy;
- tokenization implications.

Implementation validation should include:

- exact source encoding;
- normalized output;
- representative round trips;
- Windows and POSIX path independence where text assets are involved.

---

# 52. Morphology evidence

A morphology claim should identify:

- lemma class;
- paradigm;
- parameters;
- stem alternations;
- affixes;
- irregularity;
- syncretism;
- defectiveness;
- orthographic changes;
- agreement effects;
- productive versus listed status;
- source examples;
- exception policy.

A table copied from one source must be checked for:

- dialect;
- transcription;
- abbreviations;
- omitted forms;
- editorial normalization.

---

# 53. Syntax evidence

A syntax claim should identify:

- construction;
- categories involved;
- argument order;
- agreement;
- government;
- optionality;
- movement or clitic behavior where relevant;
- polarity;
- clause type;
- register;
- ambiguity;
- exceptions;
- source examples.

A GF structure may represent one analysis among several.

Record when the project chooses an implementation-neutral abstraction rather than claiming a unique linguistic analysis.

---

# 54. Lexical evidence

A lexical record should distinguish:

```text
lemma existence
spelling
part of speech
inflection class
gender/class
valency
sense
register
multiword status
proper-name status
source license
```

Do not copy copyrighted dictionary definitions into the repository unnecessarily.

A concise paraphrase and exact citation are usually sufficient.

---

# 55. Semantic and pragmatic evidence

Semantic/pragmatic claims require explicit context.

Record:

- intended reading;
- competing readings;
- discourse context;
- presupposition;
- information structure;
- register;
- translation limitations;
- whether GF represents the distinction structurally or lexically.

Gold output in one context is not proof of all readings.

---

# 56. Corpus methodology

A corpus experiment must define:

```text
research question
query language
query string or script
tokenization assumptions
morphological filters
metadata filters
date range
genre/register
duplicate handling
manual review protocol
false-positive handling
false-negative risk
counting unit
statistical treatment
result storage
```

Queries must be stored in a project path where licensing permits.

Recommended location:

```text
project/research/queries/
```

This directory is optional and must be added deliberately to project layout/configuration.

---

# 57. Corpus-result preservation

Where licensing permits, preserve:

- query script;
- aggregate counts;
- reviewed anonymized examples;
- exclusion reasons;
- analysis notebook or plain-text report;
- corpus version;
- checksum of locally stored derived data.

Do not commit restricted source data without permission.

When raw data cannot be stored, preserve enough method detail to rerun the query.

---

# 58. Corpus interpretation

Avoid unsupported statements such as:

```text
The corpus proves construction X is impossible.
```

Prefer:

```text
No qualifying instance was found in corpus version V under query Q after
manual review; this is evidence of rarity under the sampled genres, not proof
of ungrammaticality.
```

Frequency differences require:

- comparable denominators;
- genre control;
- duplicate control;
- uncertainty discussion.

---

# 59. Elicitation methodology

An elicitation protocol should define:

- target claim;
- participant criteria;
- prompt language;
- task type;
- judgment scale;
- randomization;
- fillers;
- context;
- recording method;
- anonymization;
- consent;
- follow-up questions;
- analysis rule.

Avoid leading participants toward the expected project behavior.

---

# 60. Elicitation data protection

Do not commit:

- names;
- contact details;
- voice recordings without explicit permission;
- sensitive demographic data;
- private correspondence;
- consent forms containing identity.

Use anonymized identifiers.

Store restricted materials outside the public repository under the approved research-data policy.

This document records only non-sensitive summaries and evidence locations.

---

# 61. Elicitation interpretation

Report:

- number of participants;
- relevant variety/background;
- agreement and disagreement;
- context effects;
- uncertain responses;
- exclusions;
- limitations.

Do not transform variable judgments into a categorical universal rule without justification.

---

# 62. Literature review workflow

Canonical workflow:

```text
1. define a precise research question
2. register an evidence gap
3. identify search terms and known terminology
4. locate primary and secondary sources
5. record source metadata before interpretation
6. read the relevant section in context
7. record bounded observations
8. search for counterevidence
9. assess scope and quality
10. formulate or revise the claim
11. review implementation consequences
12. design executable validation
13. update decision and project contracts
```

Search terms alone are not evidence.

---

# 63. Citation verification

Before accepting a source record:

```text
[ ] Source exists
[ ] Author/organization is correct
[ ] Title is correct
[ ] Year/edition is correct
[ ] Stable identifier is correct where available
[ ] Page/section supports the claim
[ ] Quotation is exact when used
[ ] Paraphrase preserves meaning
[ ] Source scope matches claim scope
[ ] License/access restrictions are recorded
[ ] Counterevidence search was performed for high-risk claims
```

---

# 64. Bibliographic format

The project may use one consistent citation style.

Required information matters more than typography.

Recommended compact form:

```text
Author. Year. Title. Edition or publication. Publisher/journal.
Page/section/example. DOI/ISBN/stable URL where available. Access date for web.
```

Use Unicode consistently.

Do not alternate between incomplete ad hoc forms.

---

# 65. Source registry

Current verified source records:

```text
None recorded.
```

Required table:

| Source ID | Source class | Short citation | Scope | Quality | Access/licence | State |
|---|---|---|---|---|---|---|
| No verified source rows yet | — | — | — | — | — | — |

Canonical source state:

```text
Active
Deprecated
Retired
```

- `Active`: source currently used by one or more supported claims;
- `Deprecated`: source remains referenced while a better/revised source is adopted;
- `Retired`: source is historical and does not support current claims.

---

# 66. Full source record

Every source record must define:

```text
Source ID
Source class
Full citation
Author or organization
Title
Publication or publisher
Year
Edition/version
Page/section/example
Language variety
Research method
Stable identifier
URL where applicable
Access date where applicable
License/access restrictions
Local evidence path where applicable
Quality assessment
Claims supported
Limitations
Counterevidence relevance
Review date
Reviewer
State
Replacement source where deprecated
```

Unknown required metadata must be marked explicitly.

Do not omit it silently.

---

# 67. Claim registry

Current verified claim records:

```text
None recorded.
```

Required table:

| Claim ID | Domain | Claim summary | Risk | Assessment | Sources | Decision | Implementation | Validation |
|---|---|---|---|---|---|---|---|---|
| No verified claim rows yet | — | — | — | — | — | — | — | — |

Claim summaries must be precise enough to review.

---

# 68. Full claim record

Every claim record must define:

```text
Claim ID
Title
Domain
Exact claim
Scope
Known exceptions
Risk level
Assessment
Supporting sources
Supporting observations
Counterevidence
Alternative analyses
Project interpretation
Implementation impact
Decision ID
Implementation trace
Validation trace
Open questions
Supersedes
Superseded by
Review date
Reviewer
```

---

# 69. Observation registry

Current verified observations:

```text
None recorded.
```

Required table:

| Observation ID | Source | Method | Bounded result | Claim impact | Evidence location | Review |
|---|---|---|---|---|---|---|
| No verified observation rows yet | — | — | — | — | — | — |

An observation records data.

It should not contain a broader claim than the method supports.

---

# 70. Decision registry

Current verified research-backed decisions:

```text
None recorded.
```

Required table:

| Decision ID | Claim(s) | Project choice | Alternatives | Modules/contracts affected | State | Decision-log link |
|---|---|---|---|---|---|---|
| No verified decision rows yet | — | — | — | — | — | — |

Decision state:

```text
Active
Deprecated
Retired
```

A breaking or durable project choice must also appear in:

```text
project/docs/DECISION_LOG.md
```

---

# 71. Experiment registry

Current verified experiment records:

```text
None recorded.
```

Required table:

| Experiment ID | Question | Method | Inputs | Result | Reproducibility path | Claim impact | State |
|---|---|---|---|---|---|---|---|
| No verified experiment rows yet | — | — | — | — | — | — | — |

Experiment state:

```text
Active
Deprecated
Retired
```

Failed or inconclusive experiments remain recorded.

---

# 72. Evidence-gap registry

Current verified evidence gaps:

```text
None recorded.
```

Required table:

| Gap ID | Question | Risk | Affected implementation | Missing evidence | Next action | Release impact | Owner |
|---|---|---|---|---|---|---|---|
| No verified evidence-gap rows yet | — | — | — | — | — | — | — |

A gap is required when:

- a core rule lacks evidence;
- sources conflict;
- a copied inherited analysis is unverified;
- one speaker judgment is being generalized;
- a corpus claim lacks a reproducible query;
- a citation cannot be checked;
- implementation exists without known rationale.

---

# 73. Contradiction registry

Current verified contradiction cases:

```text
None recorded.
```

Required table:

| Contradiction ID | Claim | Evidence A | Evidence B | Scope difference | Current treatment | Resolution plan |
|---|---|---|---|---|---|---|
| No verified contradiction rows yet | — | — | — | — | — | — |

Do not remove contradictory evidence from the record merely because the project selected one implementation.

---

# 74. Evidence-to-implementation trace

Every implemented claim must link to one or more:

```text
project-relative GF source paths
module names
public categories
functions
lincat fields
oper/helpers
lexicon entries
project configuration fields
```

Required table:

| Claim ID | Provider | Public surface | Consumers | Implementation state | Contract reference |
|---|---|---|---|---|---|
| No verified implementation-trace rows yet | — | — | — | — | — |

Implementation state is read from the status ledger when applicable.

---

# 75. Evidence-to-validation trace

Every release-significant implemented claim must link to evidence such as:

```text
direct module compile
consumer compile
checkpoint
.gfs scenario
gold comparison
PGF artifact
manual review
```

Required table:

| Claim ID | Validation type | Validation ID/path | Acceptance criterion | Required modes | Latest evidence |
|---|---|---|---|---|---|
| No verified validation-trace rows yet | — | — | — | — | — |

A run ID may be recorded as latest evidence.

It does not replace the stable validation specification.

---

# 76. Claim-to-scenario rule

A scenario should test a claim only when:

- the scenario has a documented linguistic purpose;
- the inputs isolate or illustrate the claim;
- required markers prove completion;
- output normalization preserves relevant distinctions;
- gold output is appropriate for deterministic behavior;
- failure interpretation is clear.

One scenario may cover several related claims.

Each claim link must remain explicit.

---

# 77. Gold evidence rule

A `.gold` file records accepted normalized output.

It does not explain why that output is linguistically correct.

Every linguistically meaningful gold expectation should link to:

- one or more claim IDs;
- the corresponding decision;
- the normalization version;
- the scenario acceptance criterion.

Changing gold requires review of both:

```text
implementation behavior
research evidence
```

where the output change is linguistic.

---

# 78. Compilation evidence rule

Compilation proves:

- GF syntax is accepted;
- type contracts are coherent enough for the target;
- imports resolve under the recorded GF path;
- the requested module can produce expected compile artifacts.

Compilation does not prove:

- lexical correctness;
- naturalness;
- completeness;
- semantic appropriateness;
- preferred word order;
- dialect scope;
- absence of overgeneration;
- absence of undergeneration.

---

# 79. Generation evidence rule

Generation can reveal:

- coverage;
- alternative forms;
- ambiguity;
- overgeneration;
- morphology combinations.

Generation output must be bounded.

A generated form is not automatically attested or acceptable.

Generated forms used as research observations require independent review.

---

# 80. Parse evidence rule

Successful parsing proves that the current grammar accepts an input.

It does not prove:

- that the input is grammatical in the target variety;
- that the analysis is unique;
- that the intended reading was selected;
- that the linearization is natural.

Record parse ambiguity and tree choice where relevant.

---

# 81. Linearization evidence rule

Successful linearization proves that the grammar produces text for a tree.

It does not prove naturalness.

A linguistically significant output requires:

- source support;
- speaker/expert review;
- corpus support;
- or another documented validation method appropriate to risk.

---

# 82. Missing-function evidence

A missing-linearization or missing-function query can prove implementation incompleteness.

It does not prove linguistic invalidity.

The project should link missing-function evidence to:

- category/function contract;
- implementation state;
- affected claim;
- remediation plan.

---

# 83. Manual review

Manual review is allowed when automation is not sufficient.

Every manual review record must identify:

```text
reviewer role
date
material reviewed
method
acceptance criteria
result
limitations
evidence location
```

“Reviewed manually” without those fields is insufficient.

---

# 84. Reproducibility

A project-generated evidence record should be reproducible from:

- project revision;
- source data version;
- query or scenario;
- GF version;
- RGL/toolchain path policy;
- normalization version;
- execution command;
- working directory;
- inputs;
- expected outputs;
- environment assumptions.

When exact reproduction is impossible, state why.

---

# 85. Research artifact paths

Recommended optional project layout:

```text
project/research/
├── bibliography/
├── notes/
├── queries/
├── derived/
├── elicitation/
└── experiments/
```

This layout is not automatically active.

Before adding it:

- define project ownership;
- define licensing;
- define privacy rules;
- update project documentation;
- update ignore rules;
- update backup/export policy.

Restricted raw data must not be placed in a public repository.

---

# 86. Path rules

Research artifact paths recorded here are:

- project-relative;
- `/` separated;
- stable;
- free of drive letters;
- free of user names;
- contained within approved project roots.

External URLs remain URLs.

Local machine paths must not appear in canonical project records.

---

# 87. File integrity

Important locally stored research artifacts should record:

```text
size
SHA-256
source/version
license
```

when integrity matters.

Do not hash a remote source and imply the hash authenticates its publisher.

The hash identifies the obtained bytes.

---

# 88. Source snapshots

A source snapshot may be stored only when:

- license permits;
- privacy permits;
- redistribution is appropriate;
- repository size policy permits.

Otherwise store:

- citation;
- stable identifier;
- access date;
- notes;
- minimal lawful excerpt if necessary;
- archive reference where permitted.

---

# 89. Copyright

Do not commit:

- full copyrighted books;
- full paywalled articles;
- copied dictionary databases;
- large copyrighted text collections;
- scans without permission.

Use citations and bounded notes.

Project examples copied from sources must be limited and attributed according to applicable policy.

---

# 90. Licensing

For every dataset or reusable language resource, record:

- license name;
- license version;
- attribution requirements;
- redistribution rights;
- modification rights;
- share-alike requirements;
- non-commercial restrictions;
- compatibility with project distribution.

Unknown license means:

```text
do not redistribute
```

until clarified.

---

# 91. Ethical review

Research involving people requires:

- informed consent appropriate to the context;
- data minimization;
- privacy protection;
- withdrawal handling;
- secure storage;
- publication scope clarity;
- local legal/institutional compliance where applicable.

GF Wordbench does not provide a substitute for institutional ethics review.

---

# 92. AI-assisted research

AI systems may be used as research assistants only under explicit verification rules.

Allowed uses:

- generate source-search vocabulary;
- summarize supplied text with citations checked;
- compare two supplied analyses;
- draft data tables;
- propose scenario cases;
- identify contradictions;
- suggest questions for expert review.

Not acceptable as evidence:

- unsupported model memory;
- generated citation;
- generated quotation;
- generated corpus count;
- invented native-speaker judgment;
- unverified grammaticality claim.

Every AI-assisted record should identify:

```text
tool/model
date
task
human verification
sources checked
accepted/rejected output
```

when the assistance materially influenced a project decision.

---

# 93. Source conflict handling

When credible sources conflict:

1. register the contradiction;
2. compare target varieties;
3. compare publication dates;
4. compare methods;
5. compare descriptive versus prescriptive purpose;
6. inspect examples in context;
7. seek independent corroboration;
8. consider variant support;
9. choose project behavior explicitly;
10. record unresolved limitations.

Do not average incompatible analyses into an undocumented hybrid.

---

# 94. Source correction

When a citation or interpretation is wrong:

- correct the source record;
- preserve a review note;
- identify affected claims;
- review affected implementation;
- rerun affected validation;
- update gold if intentionally required;
- update decision log for material changes.

A correction must not silently rewrite project history.

---

# 95. New evidence

New evidence may:

- strengthen a claim;
- narrow a claim;
- introduce a variant;
- dispute a claim;
- reject a claim;
- supersede a claim;
- require implementation change;
- require no implementation change.

The research registry changes first or in the same coordinated change as the implementation.

---

# 96. Evidence-driven breaking change

A new analysis that changes public project behavior requires review of:

```text
source modules
providers and consumers
lincats
helpers
entrypoints
scenarios
gold files
dependency map
status ledger
decision log
interfile contract lock
release artifacts
migration
```

Evidence does not permit an isolated provider edit.

---

# 97. Evidence gap and release policy

An evidence gap affects release according to risk.

| Risk | Default release treatment |
|---|---|
| `R1` | May proceed with documented limitation |
| `R2` | Requires owner and next action |
| `R3` | Blocks affected stable feature unless explicit reviewed exception |
| `R4` | Blocks release |

A release exception must identify:

- gap ID;
- affected behavior;
- user impact;
- temporary treatment;
- owner;
- deadline/exit condition;
- validation coverage;
- approval.

---

# 98. Research-evidence release gate

Recommended gate ID:

```text
research-evidence-reviewed
```

Required in release mode when the active project contains linguistic claims.

Gate status:

```text
OK
FAIL
ERROR
```

`OK` requires:

- release-significant claims registered;
- critical/high-risk claims adequately supported;
- contradictions addressed;
- implementation traces current;
- validation traces current;
- no unresolved blocking evidence gap;
- sources and licenses reviewed;
- project-specific facts populated.

`FAIL` means evidence review completed and acceptance criteria were not met.

`ERROR` means the review could not be completed reliably.

---

# 99. Claim acceptance workflow

```text
1. allocate claim ID
2. state precise claim
3. assign domain and risk
4. register sources
5. register observations
6. search for counterevidence
7. assess source quality
8. record scope and limitations
9. review alternatives
10. assign claim assessment
11. create project decision where needed
12. trace implementation
13. add validation
14. review consumers
15. update contracts
16. record review
```

---

# 100. Source acceptance workflow

```text
1. allocate source ID
2. verify source existence
3. record full metadata
4. record exact relevant location
5. classify source
6. assess quality
7. record scope
8. record licensing/access
9. link observations
10. link claims
11. record reviewer and date
```

---

# 101. Experiment workflow

```text
1. allocate experiment ID
2. state question
3. state hypothesis
4. define method
5. define stopping rule
6. define inputs
7. record environment
8. run without rewriting expected evidence
9. preserve raw output
10. normalize only under documented rules
11. interpret conservatively
12. record limitations
13. link claims
14. add or revise validation
```

---

# 102. Elicitation workflow

```text
1. define claim/question
2. prepare protocol
3. review privacy and consent
4. allocate anonymized session ID
5. collect responses
6. preserve restricted raw data securely
7. code responses
8. review variability
9. record bounded observations
10. update claim assessment
11. avoid universal generalization
```

---

# 103. Corpus workflow

```text
1. define corpus question
2. select corpus/version
3. review license
4. store query
5. run query
6. preserve aggregate results
7. manually review sample or all hits as appropriate
8. record exclusions
9. interpret within corpus scope
10. link observation and claim
```

---

# 104. Review roles

Possible review roles:

```text
language specialist
native-speaker reviewer
corpus reviewer
GF implementation reviewer
project maintainer
release reviewer
licensing reviewer
privacy reviewer
```

One person may hold several roles.

High-risk claims should receive independent review where feasible.

---

# 105. Independence

Independent corroboration means the evidence is not merely copied from the same upstream assertion.

Potentially independent:

- grammar plus corpus;
- two grammars based on different fieldwork;
- official standard plus descriptive usage study;
- published analysis plus controlled elicitation.

Not independent:

- two websites copying the same unsourced paragraph;
- an AI answer repeating one cited page;
- two project notes derived from one source;
- generated examples all produced by the same current grammar.

---

# 106. Counterevidence search

For R3 and R4 claims, record:

```text
search terms
source types searched
variants considered
negative/contradictory findings
why counterevidence does or does not change the claim
```

“No counterevidence found” must describe the search performed.

---

# 107. Uncertainty language

Use precise wording.

Preferred:

```text
The reviewed sources support...
The project treats...
The available corpus sample suggests...
The claim is restricted to...
The evidence is insufficient to determine...
Speaker judgments varied...
```

Avoid:

```text
Obviously...
Everyone says...
The language always...
The language never...
It is well known...
```

unless the claim is genuinely and specifically supported.

---

# 108. Evidence summaries

A summary must distinguish:

```text
source statement
project interpretation
implementation consequence
remaining uncertainty
```

Do not merge those into one authoritative-sounding paragraph.

---

# 109. Quotations

Use direct quotation only when wording matters.

Rules:

- copy accurately;
- keep quotations bounded;
- include page/section;
- preserve original-language text where necessary;
- provide a project translation as a labeled translation;
- do not alter punctuation silently;
- respect copyright.

Most entries should use concise paraphrase plus citation.

---

# 110. Translation of evidence

When translating source material:

- preserve original excerpt where lawful and necessary;
- identify translator;
- mark project translation;
- note ambiguous terminology;
- avoid treating a translation choice as source wording.

A machine translation must be reviewed before use in a high-risk claim.

---

# 111. Terminology registry

Recurring linguistic terms should use consistent project definitions.

Recommended location:

```text
project/docs/GLOSSARY.md
```

This document should link claim terminology to the glossary.

A terminological disagreement may be superficial.

Compare underlying analysis before declaring sources contradictory.

---

# 112. Claim granularity

Do not create one claim for an entire language subsystem.

Split claims when they differ by:

- category;
- paradigm;
- construction;
- dialect;
- register;
- polarity;
- tense/aspect;
- lexical class;
- exception behavior;
- implementation consequence.

Smaller claims are easier to support, test, and supersede.

---

# 113. Claim grouping

Related claims may be grouped under a research topic.

Recommended topic identifiers:

```text
orthography
nominal_morphology
verbal_morphology
agreement
pronouns
clitics
word_order
negation
questions
relatives
coordination
lexicon
```

Topic labels are organizational.

They are not claim identifiers.

---

# 114. Evidence density

Avoid two extremes:

- one citation for hundreds of unrelated implementation decisions;
- one record for every trivial generated form.

Use one claim for one stable generalization plus separately documented exceptions.

---

# 115. Exception registry

Exceptions may be recorded as:

- separate claims;
- observations linked to a general claim;
- lexical records;
- status-ledger entries when implementation is incomplete.

A known exception must not be hidden inside code with no evidence trace.

---

# 116. Default and fallback behavior

A fallback may be necessary when research is incomplete.

Required documentation:

```text
gap ID
fallback implementation
why fallback is safe enough
known incorrect or incomplete cases
affected consumers
validation preventing regressions
exit condition
owner
```

Fallback state belongs in the status ledger.

The related claim remains `Open` or `Disputed`.

---

# 117. Inherited RGL behavior

When the project inherits RGL behavior without override, record whether:

- it was linguistically reviewed;
- it was only technically inherited;
- it is covered by scenarios;
- known limitations exist;
- the upstream version is locked.

Do not present inherited behavior as project-validated linguistic truth without review.

---

# 118. Override evidence

A language-specific override requires:

- claim ID;
- reason upstream behavior is insufficient;
- source evidence;
- affected parent symbol;
- consumer impact;
- compatibility impact;
- direct and downstream validation.

Duplicating inherited behavior without a documented difference is prohibited.

---

# 119. Cross-language analogy

Evidence from another language may support implementation exploration.

It cannot directly establish a claim about the active language.

Record cross-language material as:

```text
analogy
```

and obtain active-language evidence before acceptance.

---

# 120. Typological evidence

Typological databases or surveys may:

- suggest candidate analyses;
- provide comparative context;
- identify terminology.

They must not override direct evidence for the active language.

Record database version and feature definition.

---

# 121. Statistical evidence

When statistical claims are used, record:

- sample;
- unit of analysis;
- model/test;
- assumptions;
- uncertainty;
- effect size;
- multiple-comparison handling where relevant;
- script/notebook;
- software version.

Do not use p-values alone as project decision evidence.

---

# 122. Reanalysis

A reanalysis may preserve output while changing internal GF structure.

It still requires evidence review when it changes:

- category interpretation;
- public lincats;
- consumer assumptions;
- parse trees;
- generation coverage;
- semantic distinctions.

Output equivalence alone may not prove compatibility.

---

# 123. Overgeneration and undergeneration

Research evidence should identify both risks.

Overgeneration:

```text
grammar accepts or produces forms outside the intended project scope
```

Undergeneration:

```text
grammar fails to accept or produce forms supported by the project scope
```

Validation should include contrastive cases where feasible.

---

# 124. Ambiguity

A claim involving ambiguity should record:

- surface form;
- analyses;
- intended scope;
- whether parse ambiguity is expected;
- whether linearization collapses distinctions;
- whether project API exposes alternatives;
- validation method.

Do not treat multiple parses automatically as an error.

---

# 125. Frequency and default linearization

Corpus frequency may inform a default linearization.

The decision must distinguish:

```text
most frequent
neutral
prescribed
project-preferred
only grammatical
```

These are not equivalent.

Generation alternatives may remain available even when one default is selected.

---

# 126. Prescriptive versus descriptive evidence

Record whether a source is:

```text
prescriptive
descriptive
mixed
```

Project policy may prioritize one for a defined purpose.

Example project purposes may include:

- educational standard;
- broad descriptive coverage;
- formal writing;
- conversational interface;
- historical text processing.

The actual project purpose must be defined elsewhere and linked.

---

# 127. Temporal scope

Language changes.

Claims should record temporal scope when relevant:

- historical period;
- publication date;
- contemporary usage;
- obsolete form;
- emerging form.

A historical corpus must not be used as the sole basis for contemporary default behavior without review.

---

# 128. Proper names and sensitive data

Examples involving real people should be minimized.

Use neutral project-owned examples where possible.

Do not include personal or sensitive information in:

- scenarios;
- gold;
- corpus notes;
- elicitation summaries;
- research examples.

---

# 129. Research-note format

A research note should contain:

```text
Question
Background
Sources reviewed
Observations
Counterevidence
Interpretation
Implementation relevance
Validation plan
Open issues
Review
```

Research notes may live under an optional approved research directory.

The stable claim and source registries remain in this document.

---

# 130. Decision-log integration

A research-backed decision belongs in `DECISION_LOG.md` when it:

- changes public project behavior;
- selects among competing analyses;
- defines target dialect/register;
- changes a lincat architecture;
- changes release output materially;
- rejects an inherited RGL behavior;
- introduces a broad fallback;
- supersedes an earlier project decision.

The decision-log entry links to claim and source IDs.

---

# 131. Lincat-contract integration

A claim affecting a public lincat must link to:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

The lincat document states the structure.

This document states the research evidence supporting the structure.

---

# 132. Dependency-map integration

A research-backed implementation trace must agree with:

```text
project/docs/MODULE_DEPENDENCY_MAP.md
```

When a claim changes provider ownership or adds a consumer:

- update the map;
- update the project lock;
- compile downstream entrypoints.

---

# 133. Validation-spec integration

Every release-significant implemented claim should map to:

```text
project/docs/VALIDATION_SPEC.md
```

The validation specification states:

- purpose;
- acceptance criterion;
- required mode;
- evidence artifact.

This registry states why the criterion matters linguistically.

---

# 134. Status-ledger integration

Use the status ledger for:

- unsupported fallback;
- partial paradigm;
- known overgeneration;
- known undergeneration;
- disabled variant;
- blocked research question;
- temporary inherited behavior.

The ledger entry links to a claim or gap ID.

---

# 135. Interfile-lock integration

A research-backed cross-file behavior must have a contract entry when another file depends on it.

The contract entry links to:

- provider;
- consumers;
- claim ID;
- validation evidence;
- related decision.

---

# 136. Release artifact integration

When a research decision changes expected output:

- update scenarios;
- review gold;
- rebuild release PGF;
- record artifact evidence;
- update changelog/release notes where user-visible;
- preserve prior evidence through version control.

---

# 137. Research review cadence

Review this registry:

- before a project release;
- when a high-risk claim changes;
- when a source is corrected or superseded;
- when a new dialect/register is added;
- when GF/RGL inheritance changes materially;
- when gold changes for linguistic reasons;
- after a significant user-reported language error;
- during major module/lincat redesign;
- when an evidence gap reaches its deadline.

---

# 138. Stale evidence

Evidence may become stale when:

- a source edition is replaced;
- the target standard changes;
- corpus version changes;
- project scope changes;
- implementation no longer matches the decision;
- a scenario no longer isolates the claim;
- gold was updated without research review;
- the upstream RGL implementation changes;
- a URL disappears.

Stale evidence must be reviewed.

Do not silently retain `Supported` when the supporting context changed materially.

---

# 139. Source deprecation

Deprecate a source when:

- a corrected edition replaces it;
- the citation is unreliable;
- access is lost and no reviewer can verify it;
- it no longer matches project scope;
- its interpretation was shown to be wrong.

Claims must be reassessed before retiring their only active source.

---

# 140. Claim supersession

A superseding claim must state:

- old claim;
- new claim;
- evidence change;
- scope change;
- implementation impact;
- migration;
- validation updates;
- gold impact.

The old claim remains visible.

---

# 141. Research audit

A periodic research audit should sample:

- high-risk claims;
- citations;
- page references;
- corpus reproducibility;
- speaker-review metadata;
- implementation traces;
- validation traces;
- active evidence gaps;
- source licenses;
- AI-assisted records.

The audit result may be stored as a project decision/review note.

---

# 142. Quality checklist for a source

```text
[ ] Identifiable
[ ] Verifiable
[ ] Relevant
[ ] Scope recorded
[ ] Exact location recorded
[ ] Method understood
[ ] Quality assessed
[ ] License/access recorded
[ ] Claims linked
[ ] Limitations recorded
[ ] Review date recorded
```

---

# 143. Quality checklist for a claim

```text
[ ] Precise
[ ] Scoped
[ ] Risk assigned
[ ] Sources linked
[ ] Observations linked
[ ] Counterevidence reviewed
[ ] Alternatives recorded
[ ] Assessment justified
[ ] Decision linked
[ ] Implementation linked
[ ] Validation linked
[ ] Exceptions recorded
[ ] Review complete
```

---

# 144. Quality checklist for an experiment

```text
[ ] Question defined
[ ] Hypothesis defined
[ ] Method fixed before interpretation
[ ] Inputs preserved
[ ] Environment recorded
[ ] Raw evidence preserved
[ ] Normalization documented
[ ] Result reproducible
[ ] Limitations recorded
[ ] Claim impact reviewed
```

---

# 145. Quality checklist for elicitation

```text
[ ] Consent appropriate
[ ] Participant anonymized
[ ] Variety/background recorded safely
[ ] Protocol versioned
[ ] Prompts preserved
[ ] Context controlled
[ ] Response scale defined
[ ] Variation reported
[ ] Restricted data protected
[ ] Claim scope not overgeneralized
```

---

# 146. Quality checklist for corpus evidence

```text
[ ] Corpus/version identified
[ ] License recorded
[ ] Query preserved
[ ] Filters recorded
[ ] Denominator defined
[ ] Duplicates handled
[ ] Hits reviewed
[ ] Exclusions recorded
[ ] Limitations stated
[ ] Absence not overinterpreted
```

---

# 147. Release checklist

```text
[ ] Project-specific source registry is populated
[ ] Release-significant claims are populated
[ ] R3 and R4 claims meet evidence thresholds
[ ] No blocking evidence gap remains
[ ] Contradictions have explicit treatment
[ ] Sources remain verifiable
[ ] Licenses permit project use
[ ] Implementation traces match current source
[ ] Dependency map agrees
[ ] Lincat contract agrees
[ ] Status ledger agrees
[ ] Decision log agrees
[ ] Validation specification agrees
[ ] Required scenarios pass
[ ] Required gold comparisons pass
[ ] Release artifact is current
[ ] Research-evidence gate is OK
```

---

# 148. Test requirements

Recommended project tests:

```text
tests/project/
├── test_research_source_ids.py
├── test_research_claim_ids.py
├── test_research_registry_links.py
├── test_research_claim_evidence.py
├── test_research_implementation_trace.py
├── test_research_validation_trace.py
├── test_research_gap_release_policy.py
├── test_research_source_paths.py
├── test_research_no_placeholders.py
└── test_research_evidence_gate.py
```

If the project does not machine-parse this Markdown, lightweight document tests may still verify:

- unique IDs;
- valid links;
- no unresolved required placeholders;
- active source references;
- claim/source linkage;
- release checklist state.

---

# 149. Optional structured registry

The initial project does not require a machine-readable research schema.

Markdown is sufficient while:

- the registry remains maintainable;
- no runtime component depends on it;
- release checks can verify required links safely.

A future structured registry requires:

- schema ID;
- schema version;
- owner;
- validator;
- migrator;
- deterministic ordering;
- path rules;
- security review.

Do not create ad hoc JSON alongside this document without those contracts.

---

# 150. No runtime parsing rule

GF Wordbench runtime validation must not parse research prose to determine grammar behavior.

The research registry informs:

- maintainers;
- project decisions;
- validation design;
- release review.

GF source and project configuration remain executable authorities.

---

# 151. Suggested checker behavior

A project checker may verify structural properties:

```text
unique research IDs
source IDs referenced by claims exist
claim IDs referenced by decisions exist
implementation paths exist
scenario IDs exist
gold paths exist
gap IDs are unique
supersession links are reciprocal
no retired source is the only support for an active claim
no R4 open claim is release-unblocked
```

It must not automatically judge linguistic truth.

---

# 152. Deterministic ordering

Canonical registry ordering:

```text
sources:
    source ID

claims:
    claim ID

observations:
    observation ID

decisions:
    decision ID

experiments:
    experiment ID

gaps:
    gap ID

contradictions:
    contradiction ID

implementation traces:
    claim ID, provider

validation traces:
    claim ID, validation path
```

Do not reorder by subjective importance in the canonical tables.

Reports may create risk-prioritized views.

---

# 153. Search and retrieval

When searching external sources, record:

- database/search engine;
- date;
- query terms;
- filters;
- languages searched;
- inclusion/exclusion rules.

This is required for high-risk literature reviews.

A general web search without recorded follow-up does not satisfy the evidence threshold.

---

# 154. Inaccessible sources

A citation that no project reviewer can access must not be the only support for an R3 or R4 claim.

Possible actions:

- obtain lawful access;
- find independent corroboration;
- downgrade assessment;
- register evidence gap;
- preserve the inaccessible citation as a lead.

---

# 155. Secondary citation

Avoid citing a source only through another source.

When unavoidable:

- identify both;
- state that the original was not inspected;
- avoid direct quotation from the uninspected original;
- reduce confidence;
- seek the primary source.

---

# 156. Publication bias and sampling

Evidence reviews should consider:

- published examples favoring unusual phenomena;
- corpus genre bias;
- formal-language bias;
- urban/educated speaker bias;
- standard-language bias;
- historical sampling;
- annotation errors;
- researcher elicitation bias.

Relevant bias belongs in limitations.

---

# 157. Replication

A replicated observation should receive a new observation or experiment ID.

Do not overwrite the first result.

Record whether replication:

- confirmed;
- partially confirmed;
- failed;
- found a scope difference.

---

# 158. Null result

A null or inconclusive experiment is useful evidence.

Record:

- method;
- result;
- why it was inconclusive;
- next action.

Do not delete it merely because it did not support the intended implementation.

---

# 159. Failed hypothesis

When evidence rejects a hypothesis:

- mark the claim `Rejected`;
- preserve the experiment;
- remove or migrate implementation if it depended on the claim;
- update tests and gold intentionally;
- record the decision.

This prevents repeated rediscovery of the same failed analysis.

---

# 160. Research-driven bug report

A language bug should identify:

```text
affected claim
observed behavior
expected behavior
source support
counterexample
implementation path
scenario or reproduction
risk
```

A user report may be an observation.

It becomes supported evidence only after review and scope assessment.

---

# 161. User-contributed evidence

Contributions should include:

- source or speaker basis;
- target variety;
- reproducible example;
- expected behavior;
- permission to retain supplied data;
- privacy-safe content.

Maintainers verify before accepting a claim change.

---

# 162. Release note language

Release notes should distinguish:

```text
Corrected implementation to match existing supported analysis
Changed project analysis based on new evidence
Added documented variant
Changed default while retaining accepted alternatives
Updated normalization only
Updated gold for non-linguistic tool output
```

Do not label every gold change a linguistic correction.

---

# 163. Security

Research files and links are untrusted inputs.

Do not:

- execute downloaded files;
- run macros;
- deserialize arbitrary objects;
- build shell commands from citations;
- follow local paths outside approved roots;
- store credentials;
- include full environment dumps;
- commit malicious documents.

Use ordinary secure handling for external materials.

---

# 164. Privacy

Public project evidence must not expose:

- speaker identity;
- contact information;
- private correspondence;
- precise location when unnecessary;
- sensitive demographic attributes;
- confidential corpus data;
- restricted annotations.

Use aggregate, anonymized reporting.

---

# 165. Backup and retention

Retain:

- stable source metadata;
- claim history;
- decision history;
- reproducible queries;
- derived evidence permitted by license;
- anonymized elicitation summaries;
- release-significant review records.

Retention of restricted raw data follows its separate privacy policy.

---

# 166. Change classification

### 166.1 Internal documentation correction

Examples:

- citation punctuation;
- typo;
- broken internal link.

Required:

- review;
- no claim assessment change unless meaning changed.

### 166.2 Compatible evidence extension

Examples:

- add corroborating source;
- add replication;
- narrow limitation without changing implementation.

Required:

- update records;
- review claim assessment;
- rerun validation only when implementation relevance changes.

### 166.3 Claim revision

Examples:

- narrow scope;
- add variant;
- change default;
- reject former analysis.

Required:

- new or superseding claim;
- decision review;
- implementation impact review;
- validation/gold review.

### 166.4 Breaking research decision

Examples:

- redesign public lincats;
- change entrypoint-wide syntax;
- change target orthographic standard;
- change dialect scope.

Required:

- decision-log entry;
- migration;
- contract update;
- full affected validation;
- release note.

---

# 167. Change-control template

Every material evidence change should identify:

```text
Record IDs:
Research question:
Old assessment:
New assessment:
Sources added/removed:
Counterevidence:
Scope change:
Decision impact:
Implementation impact:
Consumer impact:
Scenario impact:
Gold impact:
Migration:
Release impact:
Reviewer:
```

---

# 168. Current population plan

Before this document can support a stable active-project release:

```text
[ ] establish authoritative project identity
[ ] define target language variety/register
[ ] collect current project notes and bibliographic sources
[ ] verify every citation
[ ] inventory core linguistic assumptions
[ ] allocate claim IDs
[ ] assign risk
[ ] register source IDs
[ ] register evidence gaps
[ ] identify inherited RGL assumptions
[ ] trace claims to modules and contracts
[ ] trace claims to scenarios and gold
[ ] add missing high-risk validation
[ ] review licenses
[ ] review privacy
[ ] resolve blocking R3/R4 gaps
[ ] record project review
```

No item may be completed solely through model-generated general knowledge.

---

# 169. Completion evidence

When project-specific population is complete, record:

```text
project revision
registry review date
reviewer roles
source count
claim count
open gap count by risk
contradiction count
latest release-validation run ID
research-evidence gate result
```

These metrics support review.

They do not replace record content.

---

# 170. Anti-drift indicators

Probable research-evidence drift exists when:

- implementation contains a broad linguistic rule with no claim ID;
- a claim cites no source;
- a source has no verifiable metadata;
- a page number does not support the claim;
- an AI answer is listed as linguistic authority;
- a corpus count has no query;
- an elicitation judgment has no protocol or scope;
- one speaker is generalized to the whole language;
- corpus absence is treated as ungrammaticality;
- a supported claim has only retired sources;
- contradictory evidence is deleted;
- a gold file changes without evidence review;
- a lincat redesign has no research decision;
- a copied RGL behavior is labeled language-validated without review;
- a source license is unknown but data is redistributed;
- personal data appears in the repository;
- implementation and claim scopes differ;
- scenarios no longer test the linked claim;
- project status claims stable behavior while the claim is open;
- a release contains an unresolved R4 gap;
- fabricated examples or citations appear;
- placeholders remain in project-specific evidence rows.

Any indicator requires correction before release-significant claims.

---

# 171. Implementation completion checklist

```text
[ ] stable identifier families are used
[ ] source registry is populated
[ ] claim registry is populated
[ ] observation registry is populated where needed
[ ] decision registry is populated
[ ] experiment registry is populated where needed
[ ] evidence gaps are registered
[ ] contradictions are registered
[ ] source quality is assessed
[ ] claim risk is assigned
[ ] claim scope is explicit
[ ] counterevidence is reviewed
[ ] citations are verified
[ ] corpus queries are reproducible
[ ] elicitation is privacy-safe
[ ] AI-generated material is not treated as evidence
[ ] implementation traces exist
[ ] validation traces exist
[ ] lincat contract agrees
[ ] dependency map agrees
[ ] status ledger agrees
[ ] decision log agrees
[ ] validation specification agrees
[ ] gold files link to claims
[ ] licences are reviewed
[ ] R3 and R4 thresholds are met
[ ] blocking gaps are resolved
[ ] release gate is OK
```

---

# 172. Related documents

```text
project/project.toml
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/VALIDATION_SPEC.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/GLOSSARY.md
project/validation/scenarios/
project/validation/gold/
docs/projects/PROJECT_MODEL.md
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/SCENARIO_VALIDATION.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
docs/reference/STATUS_VALUES.md
docs/development/BACKWARD_COMPATIBILITY.md
docs/release/VERSIONING_POLICY.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
SECURITY.md
```

---

# 173. Final rule

Research evidence is the bridge between a plausible grammar and a defensible language project.

Therefore:

> Record exact claims, cite verifiable sources, preserve counterevidence and uncertainty, separate linguistic support from GF execution success, trace every important decision into code and validation, and leave a visible evidence gap rather than inventing certainty.
