# Active Project — Syntax and Constructor Rules

**Document ID:** `GF-WB-PROJECT-SYNTAX-CONSTRUCTOR-RULES`  
**Status:** Active project specification — project-specific rule registry not yet completed  
**Applies to:** Every syntax module, public syntax constructor, structural constructor, extension constructor, lexicon-facing syntax constructor, scenario, and release entrypoint in the active GF language project  
**Owner:** Active project maintainers  
**Primary source authorities:**
- active project GF source;
- `project/project.toml`;
- `project/docs/INTERFILE_CONTRACT_LOCK.md`;
- `project/docs/CATEGORY_AND_LINCAT_CONTRACT.md`;
- `project/docs/LANGUAGE_ARCHITECTURE.md`;
- `project/docs/MODULE_DEPENDENCY_MAP.md`;
- `project/docs/MORPHOLOGY_SPEC.md`;
- `project/docs/VALIDATION_SPEC.md`;
- `project/docs/TEST_COVERAGE_MATRIX.md`;
- `project/docs/STATUS_LEDGER.md`;
- `project/docs/DECISION_LOG.md`.

**Document version:** `1.0.0`  
**Last structural review:** `2026-07-22`

---

## 1. Purpose

This document defines the active project's syntax and constructor contract.

It governs how abstract functions become concrete linearization rules and how syntax-facing constructors:

- consume category values;
- inspect lincat fields;
- propagate agreement;
- select forms;
- order constituents;
- insert structural words;
- represent optional material;
- manage complements;
- preserve clause state;
- expose reusable operations;
- compose with morphology, lexicon, structural, and extension modules;
- remain testable through GF scenarios and gold comparisons.

The document has two responsibilities:

1. lock the rules that every project syntax implementation must obey;
2. record the active language's actual syntax decisions.

The first responsibility is fully specified here.

The second responsibility is currently incomplete because no authoritative active-language identity, module inventory, lincat table, or language-specific rule inventory was present in the available project sources used to prepare this file.

Therefore:

```text
project-specific syntax registry status = NOT YET RECORDED
release impact = BLOCKING
```

This is an explicit project status, not a template placeholder.

> No language-specific word order, agreement rule, clitic rule, complement rule, or constructor behavior may be inferred merely from GF conventions or another language implementation.

---

## 2. Completion requirement

This document becomes release-complete only when all syntax constructors used by release entrypoints are covered by one of:

- an explicit rule in this document;
- an explicit category/lincat contract referenced from this document;
- an explicit inherited RGL contract whose compatibility has been verified;
- an explicitly accepted omission recorded in `STATUS_LEDGER.md`.

A release is blocked when:

- a public constructor has no documented rule;
- a constructor reads an undocumented lincat field;
- a rule relies on an undocumented default;
- a temporary fallback is not registered;
- a scenario exercises behavior absent from this specification;
- this document contains a project-specific section marked `NOT YET RECORDED`;
- source behavior and this document disagree.

---

## 3. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **ABSTRACT FUNCTION**: function declared in an abstract GF module.
- **CONCRETE RULE**: `lin` implementation of an abstract function.
- **SYNTAX CONSTRUCTOR**: public or shared `oper`, `lin`, `lincat`, or helper that combines grammatical values.
- **LEXICAL CONSTRUCTOR**: constructor that creates a lexical category from strings or paradigms.
- **STRUCTURAL CONSTRUCTOR**: constructor involving closed-class material, function words, punctuation, or grammatical particles.
- **EXTENSION CONSTRUCTOR**: project- or RGL-extension function outside the core syntax family.
- **LINCATEGORY / LINCAT**: concrete representation of an abstract category.
- **FIELD**: named record member in a lincat or helper record.
- **PARAMETER**: GF `param` value used to model grammatical distinctions.
- **AGREEMENT DIMENSION**: grammatical feature propagated or selected across constituents.
- **STATE**: non-surface information required for later composition.
- **SURFACE STRING**: final or intermediate `Str` material.
- **FORM TABLE**: table indexed by grammatical parameters.
- **COERCION**: operation converting one category representation into another.
- **DEFAULT**: behavior chosen when the caller omits an explicit distinction.
- **FALLBACK**: temporary or reduced behavior used when full implementation is unavailable.
- **PUBLIC**: consumed by another module, entrypoint, scenario, lexicon, or external project API.
- **PRIVATE**: local implementation detail with no external consumer.
- **RELEASE-SIGNIFICANT**: behavior whose change can affect required scenarios, golds, entrypoints, or PGF output.

---

## 4. Authority order

When sources disagree, review them in this order:

1. GF abstract function type;
2. active concrete source accepted by GF;
3. `CATEGORY_AND_LINCAT_CONTRACT.md`;
4. project interfile contract lock;
5. this document;
6. language architecture and dependency map;
7. validation scenarios and reviewed golds;
8. status ledger and decision log;
9. explanatory comments.

This order does not allow source drift to become accepted automatically.

A disagreement requires either:

- restoring source to the documented contract; or
- changing all affected contracts, documentation, scenarios, and golds deliberately.

---

## 5. Project-specific registry status

The following project facts were not available in authoritative form at the time of this document's creation.

| Required fact | Current recorded value | Release impact |
|---|---|---|
| Active language name | Not yet recorded in available sources | Blocking |
| Language code | Not yet recorded in available sources | Blocking |
| Module suffix | Not yet recorded in available sources | Blocking |
| Category provider module | Not yet recorded in available sources | Blocking |
| Core syntax module inventory | Not yet recorded in available sources | Blocking |
| Grammar entrypoint | Not yet recorded in available sources | Blocking |
| Syntax/API entrypoint | Not yet recorded in available sources | Blocking |
| Clause representation | Not yet recorded in available sources | Blocking |
| NP agreement representation | Not yet recorded in available sources | Blocking |
| VP complement representation | Not yet recorded in available sources | Blocking |
| Word-order rules | Not yet recorded in available sources | Blocking |
| Negation strategy | Not yet recorded in available sources | Blocking |
| Question strategy | Not yet recorded in available sources | Blocking |
| Relative-clause strategy | Not yet recorded in available sources | Blocking |
| Coordination strategy | Not yet recorded in available sources | Blocking |
| Constructor registry | Not yet recorded in available sources | Blocking |

The maintainer must replace each `Not yet recorded in available sources` status with verified project facts before release.

These phrases are status statements, not initializer tokens.

---

# Part I — Architectural rules

## 6. Syntax-layer position

The expected dependency direction is:

```text
abstract syntax
    ↓
category/resource provider
    ↓
morphology and paradigms
    ↓
lexicon and structural lexicon
    ↓
core syntax modules
    ↓
extension/coordinator modules
    ↓
grammar and syntax entrypoints
    ↓
scenarios and PGF build
```

### 6.1 Allowed dependencies

Syntax modules MAY depend on:

- category/lincat provider;
- shared resource modules;
- morphology interfaces needed for form selection;
- structural modules where architecture assigns ownership;
- documented lower-level syntax modules;
- RGL interfaces explicitly adopted by the project.

### 6.2 Prohibited dependencies

Syntax modules MUST NOT depend on:

- final grammar entrypoints;
- scenarios;
- gold files;
- generated run artifacts;
- report files;
- GUI or Python framework code;
- undocumented temporary modules;
- consumer-specific helpers owned by higher layers;
- source files outside the project/RGL contract.

### 6.3 Dependency cycles

Import cycles are prohibited.

A conceptual mutual dependency must be resolved by:

- moving shared state/types to a lower resource provider;
- introducing an interface/instance boundary;
- splitting the constructor family;
- recording an architectural decision.

---

## 7. Module ownership

Every syntax family has one primary owner.

Recommended family inventory:

```text
Noun
Adjective
Adverb
Verb
Sentence
Question
Relative
Conjunction
Phrase
Structural
Extend
```

Actual module names must be recorded in the project dependency map.

### 7.1 One owner per public rule

A public constructor or helper family MUST have one authoritative provider.

Copying equivalent helper logic into multiple modules is prohibited unless:

- the duplication is required by GF module constraints;
- behavior is tested for equivalence;
- the reason is documented;
- future synchronization ownership is explicit.

### 7.2 Re-export

A higher-level module may re-export a lower-level constructor.

It must not redefine incompatible behavior under the same public name.

### 7.3 Coordinator modules

A coordinator module may combine inherited modules and extensions.

It SHOULD contain minimal language logic.

Language logic belongs in the lowest coherent owner.

---

## 8. Abstract-to-concrete contract

Every concrete `lin` implementation MUST match the abstract function type exactly.

### 8.1 Stable identifiers

Abstract category and function names are public project identifiers.

Renaming or removing them is a breaking project change.

### 8.2 Function arity

Concrete implementation must preserve:

- number of arguments;
- argument categories;
- argument order;
- result category.

### 8.3 Incomplete implementation

An abstract function without a complete concrete implementation must be:

- visible through GF missing-function inspection;
- recorded in the status ledger;
- classified for release impact;
- covered by an explicit scenario or completeness gate.

### 8.4 No silent semantic substitution

A concrete rule MUST NOT return an unrelated generic phrase merely to satisfy the type.

Fallbacks require:

- stable status ID;
- documented behavior;
- test coverage;
- release decision.

---

## 9. Category/lincat dependency

The category provider owns:

- lincat record shapes;
- field names;
- field meanings;
- grammatical parameters;
- agreement dimensions;
- state invariants;
- shared category constructors;
- coercions.

Syntax consumers MUST use only declared fields.

### 9.1 Breaking lincat changes

The following are breaking project changes:

- field rename;
- field removal;
- field meaning change;
- parameter value removal;
- change from scalar string to form table;
- change from form table to scalar string;
- agreement dimension removal;
- state-field semantic change;
- mandatory field addition without coordinated initialization.

### 9.2 Derivable field addition

A derivable field may be added compatibly only when:

- all constructors initialize it deterministically;
- old consumers do not require it;
- no existing output changes unexpectedly;
- direct and downstream modules compile;
- scenarios validate the new behavior.

---

# Part II — General constructor contract

## 10. Constructor registry

Every public constructor must have a registry entry with:

```text
constructor ID
GF name
provider module
visibility
kind
input categories
output category
argument order
preconditions
selected lincat fields
propagated fields
surface-order rule
agreement rule
default behavior
failure/fallback behavior
consumers
validation
release significance
```

### 10.1 Constructor ID

Recommended format:

```text
SYN-<FAMILY>-<NUMBER>
```

Examples:

```text
SYN-NP-001
SYN-VP-004
SYN-CL-002
SYN-Q-001
```

IDs remain stable when implementation moves.

### 10.2 Registry status

Current active-project constructor registry:

```text
NOT YET RECORDED
```

Release impact:

```text
BLOCKING
```

---

## 11. Constructor arity

Constructor arity is locked.

Changing arity requires coordinated updates to:

- provider;
- every direct consumer;
- abstract functions where applicable;
- lexicon entries;
- structural entries;
- scenarios;
- golds;
- project contract lock;
- migration/release notes.

### 11.1 Convenience overloads

GF does not provide ordinary overloaded functions by signature.

Convenience variants must have distinct names or be represented through documented helper patterns.

### 11.2 Partial application

Where GF permits partial application, the public contract must state whether consumers may rely on it.

---

## 12. Argument order

Argument order is semantic.

Examples of distinctions that must remain explicit:

```text
head before complement
subject before predicate
determiner before noun
matrix clause before subordinate clause
coordinator before right conjunct
```

The actual active-language order is not recorded in available sources.

Therefore all family-specific order rules remain blocking until documented.

### 12.1 No order inference from names

A constructor named similarly to an RGL function does not automatically inherit that function's internal order.

### 12.2 Named local bindings

Complex constructors SHOULD bind arguments to meaningful local names before composition to reduce order errors.

---

## 13. Return category

A public constructor MUST return the documented category.

A helper that returns an internal record must not be exposed as though it returned the public category.

### 13.1 Coercions

Coercions must document:

- source category;
- target category;
- information preserved;
- information lost;
- default state introduced;
- release-significant effects.

### 13.2 Lossy coercion

A lossy coercion requires explicit justification and tests.

It must not silently discard agreement or clause state needed by downstream constructors.

---

## 14. Totality

Public constructors SHOULD be total over their documented input domain.

### 14.1 Restricted domain

When a constructor accepts only a subset of values, document:

- restriction;
- detection strategy;
- failure/fallback behavior;
- test cases.

### 14.2 Empty string fallback

Returning `[]` or an empty string for unsupported input is prohibited unless:

- empty output is semantically correct;
- the behavior is documented;
- a scenario asserts it.

### 14.3 Unsafe pattern matching

A pattern match that does not cover all parameter values is a release blocker unless GF's type system proves totality or the omission is intentionally registered.

---

## 15. Determinism

Given the same:

- project source;
- constructor inputs;
- GF version;
- RGL identity;
- environment-independent state;

a constructor must produce deterministic output.

### 15.1 Prohibited nondeterminism

Syntax rules must not depend on:

- current time;
- filesystem state;
- process environment;
- random choice;
- run directory;
- GUI state;
- previous validation output.

### 15.2 Ambiguity

Grammatical ambiguity is permitted when represented intentionally through GF.

It must not arise from unstable implementation order.

---

## 16. Purity and side effects

GF syntax constructors are declarative.

They MUST NOT depend on shell commands or external runtime effects.

Scenarios may inspect behavior, but syntax code remains independent from GF Wordbench execution infrastructure.

---

# Part III — Surface strings and state

## 17. String composition

Surface strings should be composed through documented GF operations and category fields.

### 17.1 No opaque concatenation

Large unstructured concatenations SHOULD be decomposed into named components.

### 17.2 Spacing

Spacing and token boundaries must be governed by GF string composition semantics and project conventions.

Manual embedded leading/trailing spaces are prohibited unless documented and tested.

### 17.3 Punctuation

Punctuation ownership must be explicit:

```text
clause
sentence
phrase
utterance
scenario presentation
```

Two layers must not add the same punctuation.

### 17.4 Empty material

Optional empty material must compose without:

- duplicate spaces;
- orphan punctuation;
- duplicate particles;
- broken clitic placement.

---

## 18. State preservation

A category may carry non-surface state.

Examples:

```text
agreement
case requirement
polarity
tense/anteriority
clause type
inversion requirement
extraction state
complement frame
preposition requirement
is-pronominal flag
is-definite flag
```

The actual active-project fields are not yet recorded.

### 18.1 Propagation

Every constructor must document which state is:

- selected;
- copied;
- transformed;
- reset;
- consumed;
- introduced.

### 18.2 No silent reset

A constructor must not reset a meaningful state field to a default merely because it does not currently use the field.

### 18.3 State finalization

A final sentence/utterance constructor may consume intermediate state.

The point of consumption must be documented.

---

## 19. Form selection

When a category exposes a form table, consumers must select it with documented parameters.

### 19.1 Parameter source

Every selected parameter must come from an explicit source:

- head agreement;
- controller agreement;
- syntactic case;
- clause state;
- lexical requirement;
- construction-specific constant.

### 19.2 No magic constants

Hardcoded parameter choices require a rule ID and explanation.

### 19.3 Form completeness

All parameter combinations required by release scenarios must be implemented.

Unimplemented cells are tracked explicitly.

---

# Part IV — Agreement

## 20. Agreement registry

The active project must document every agreement dimension.

Potential dimensions include:

```text
person
number
gender
case
animacy
definiteness
politeness
noun class
verb class
tense
mood
aspect
polarity
```

This list is illustrative, not a claim about the active language.

### 20.1 Current status

```text
active agreement dimensions = NOT YET RECORDED
release impact = BLOCKING
```

### 20.2 Controller

Every agreement rule must identify:

- controller;
- target;
- dimensions;
- default/neutral value;
- coordination behavior;
- exceptional behavior.

### 20.3 Conflict resolution

When multiple potential controllers exist, the rule must define precedence.

### 20.4 Agreement loss

No coercion or constructor may discard required agreement before all dependent targets are resolved.

---

## 21. Subject–predicate agreement

The project must record:

- subject agreement representation;
- finite-verb agreement selection;
- behavior for pronouns;
- behavior for coordinated subjects;
- behavior for expletive/impersonal clauses if in scope;
- behavior for missing/implicit subjects;
- default when agreement is underspecified.

Current active rule:

```text
NOT YET RECORDED
```

Release impact:

```text
BLOCKING if finite clauses are in scope
```

---

## 22. Determiner–noun agreement

The project must record whether and how determiners agree with nouns.

Required facts:

- agreement dimensions;
- case source;
- definiteness behavior;
- number/gender/class propagation;
- zero-determiner behavior;
- partitive/quantificational behavior if in scope.

Current active rule:

```text
NOT YET RECORDED
```

---

## 23. Adjective agreement

The project must record:

- attributive agreement;
- predicative agreement;
- adjective position;
- degree/comparison interaction;
- coordination;
- invariant adjective behavior;
- case/definiteness marking if applicable.

Current active rule:

```text
NOT YET RECORDED
```

---

## 24. Pronoun agreement and reference

The project must record:

- person/number/gender distinctions;
- case/form selection;
- reflexive behavior;
- possessive behavior;
- clitic vs full forms;
- politeness distinctions;
- agreement defaults for underspecified reference.

Current active rule:

```text
NOT YET RECORDED
```

---

## 25. Coordination agreement

The project must record how coordination determines agreement.

Required facts:

- person resolution;
- number resolution;
- gender/class resolution;
- mixed-feature resolution;
- conjunction-specific behavior;
- singular coordination exceptions;
- punctuation/list behavior.

Current active rule:

```text
NOT YET RECORDED
```

---

# Part V — Nominal syntax

## 26. Noun phrase representation

The project must define the public NP lincat and its semantic fields.

At minimum, record whether NP carries:

```text
surface form(s)
agreement
case table
person
number
gender/class
definiteness
is-pronominal
preposition interaction
clitic forms
```

Current active NP representation:

```text
NOT YET RECORDED
```

---

## 27. Common noun construction

The project must document constructors that form common-noun phrases from:

- lexical nouns;
- adjective modification;
- relative clauses;
- complements;
- apposition;
- coordination;
- compounds if in scope.

For each constructor, document:

- head;
- modifier order;
- agreement;
- case behavior;
- number behavior;
- definiteness interaction.

Current rules:

```text
NOT YET RECORDED
```

---

## 28. Determination

The project must document:

- article/determiner placement;
- zero article;
- demonstratives;
- possessives;
- quantifiers;
- numerals;
- definiteness propagation;
- case selection;
- agreement.

Current rules:

```text
NOT YET RECORDED
```

---

## 29. Numerals and quantity

If numerals/quantifiers are in scope, record:

- numeral position;
- noun number/case effects;
- agreement;
- classifier or measure behavior;
- cardinal vs ordinal distinction;
- complex numeral composition.

Current rules:

```text
NOT YET RECORDED
```

---

## 30. Possession

The project must document supported possession strategies.

Potential strategies:

```text
possessive determiner
genitive/dependent NP
prepositional phrase
clitic/affix
construct state
```

Actual active strategy:

```text
NOT YET RECORDED
```

Required rule details:

- possessor position;
- agreement;
- case/preposition;
- definiteness;
- recursive possession;
- pronominal possession.

---

## 31. Nominal complementation

Document noun constructors that select complements.

Required facts:

- complement category;
- preposition/case;
- order;
- optionality;
- extraction/relative behavior;
- lexical vs construction ownership.

Current rules:

```text
NOT YET RECORDED
```

---

# Part VI — Adjectival and adverbial syntax

## 32. Adjective phrase representation

Document:

- positive/comparative/superlative forms;
- agreement table;
- complement frame;
- adverb modification;
- predicative form;
- attributive form.

Current active representation:

```text
NOT YET RECORDED
```

---

## 33. Adjective modification

For attributive adjectives, record:

- position relative to noun;
- agreement controller;
- stacking order;
- coordination;
- punctuation;
- semantic classes with exceptional placement.

Current rules:

```text
NOT YET RECORDED
```

---

## 34. Predicative adjectives

Record:

- copular support;
- agreement;
- complement order;
- negation;
- tense/mood support;
- subject controller.

Current rules:

```text
NOT YET RECORDED
```

---

## 35. Adverb placement

Record placement for:

- VP adverbs;
- sentence adverbs;
- adjective modifiers;
- degree adverbs;
- focus particles;
- interrogative adverbs;
- temporal/locative adjuncts.

Current rules:

```text
NOT YET RECORDED
```

A single generic adverb concatenation rule is insufficient when placement differs by class.

---

# Part VII — Verbal syntax

## 36. Verb category hierarchy

The active project must document every verb valency category used.

Typical RGL categories may include:

```text
V
V2
V3
VV
VS
VQ
VA
V2V
V2S
V2Q
V2A
```

This list is illustrative.

The active project's actual categories:

```text
NOT YET RECORDED
```

### 36.1 Valency contract

Each category must define:

- complement count;
- complement categories;
- prepositions/cases;
- complement order;
- optionality;
- extraction behavior;
- passive behavior if supported.

---

## 37. Verb phrase representation

The project must record the VP lincat and state.

Potential components:

```text
verb form table
complement slots
adverb slots
object agreement
polarity state
tense/aspect state
voice state
clitic state
subject agreement function
```

Current active VP representation:

```text
NOT YET RECORDED
```

---

## 38. Complement saturation

A constructor that adds a complement must document:

- required verb category;
- complement category;
- selected form/case;
- inserted preposition;
- order;
- VP category returned;
- remaining unsaturated complements;
- optionality;
- effect on extraction/passive state.

### 38.1 No valency erasure

A constructor must not coerce an unsaturated verb to a complete VP without recording how missing complements are handled.

### 38.2 Lexical prepositions

When a verb owns a required preposition, the responsibility must be located in:

- lexical verb record; or
- valency constructor;

not duplicated inconsistently.

---

## 39. Direct and indirect objects

The project must document:

- case/preposition selection;
- order relative to verb;
- order between objects;
- clitic/full NP behavior;
- pronoun placement;
- agreement;
- passivization;
- extraction;
- optional omission.

Current rules:

```text
NOT YET RECORDED
```

---

## 40. Sentential complements

Document constructors for:

```text
declarative complement
question complement
infinitival/non-finite complement
adjectival complement
```

Required details:

- complementizer;
- mood/tense;
- subject control/raising;
- order;
- punctuation;
- finite/non-finite distinction.

Current rules:

```text
NOT YET RECORDED
```

---

## 41. Auxiliary and periphrastic constructions

If supported, document:

- auxiliary ownership;
- main-verb form selected;
- agreement carrier;
- negation placement;
- clitic placement;
- tense/aspect/voice meaning;
- word order.

Current rules:

```text
NOT YET RECORDED
```

---

## 42. Voice

Document:

- active;
- passive;
- reflexive/middle;
- impersonal;
- causative;

only when in project scope.

For each voice:

- argument remapping;
- agreement controller;
- auxiliary/morphology;
- agent expression;
- complement retention;
- scenario coverage.

Current rules:

```text
NOT YET RECORDED
```

---

## 43. Non-finite forms

Document:

- infinitive;
- participle;
- gerund/converb;
- verbal noun;

as applicable.

Required facts:

- subject expression;
- agreement;
- complement retention;
- tense/aspect;
- clause embedding;
- punctuation.

Current rules:

```text
NOT YET RECORDED
```

---

# Part VIII — Clause and sentence syntax

## 44. Clause representation

The active project must document the clause lincat completely.

Potential fields:

```text
subject slot
predicate function
finite form table
word-order state
polarity state
tense/anteriority
question state
subordination state
extraction gap
agreement controller
```

Current active clause representation:

```text
NOT YET RECORDED
```

---

## 45. Basic declarative clause

The project must record:

- canonical constituent order;
- finite verb position;
- subject expression;
- object/adjunct order;
- agreement;
- tense/aspect;
- negation;
- punctuation ownership.

Current rule:

```text
NOT YET RECORDED
```

This is a release blocker for any project claiming declarative-sentence support.

---

## 46. Subjectless and impersonal clauses

If supported, document:

- omitted subject conditions;
- expletive form;
- default agreement;
- weather/existential behavior;
- pronoun suppression;
- scenario cases.

Current rule:

```text
NOT YET RECORDED
```

---

## 47. Tense, anteriority, aspect, and mood

The project must record which distinctions are:

- morphological;
- periphrastic;
- unsupported;
- mapped to shared GF parameters;
- collapsed intentionally.

Required table:

| Dimension | Supported values | Realization owner | Release coverage |
|---|---|---|---|
| Tense | Not yet recorded | Not yet recorded | Blocking |
| Anteriority | Not yet recorded | Not yet recorded | Blocking |
| Aspect | Not yet recorded | Not yet recorded | Blocking |
| Mood | Not yet recorded | Not yet recorded | Blocking |

No unsupported distinction may silently linearize as another value without a documented mapping.

---

## 48. Polarity and negation

The project must document:

- positive realization;
- negative particle/affix/auxiliary;
- placement;
- interaction with tense/aspect;
- interaction with infinitives;
- negative concord;
- constituent negation;
- question negation;
- imperative negation.

Current rule:

```text
NOT YET RECORDED
```

---

## 49. Sentence construction

Document how a clause becomes a sentence or utterance.

Required facts:

- state consumed;
- punctuation;
- capitalization responsibility;
- final ordering;
- question/declarative distinction;
- embedded vs root clause distinction.

Current rule:

```text
NOT YET RECORDED
```

---

## 50. Subordination

Document:

- complementizers;
- subordinate word order;
- tense/mood changes;
- subject behavior;
- punctuation;
- adverbial clauses;
- conditional clauses;
- purpose/cause/time clauses as in scope.

Current rules:

```text
NOT YET RECORDED
```

---

# Part IX — Questions

## 51. Question representation

Document:

- question lincat;
- direct vs embedded question;
- polarity vs content question;
- inversion state;
- interrogative constituent state;
- punctuation.

Current representation:

```text
NOT YET RECORDED
```

---

## 52. Polar questions

The project must identify the strategy:

```text
inversion
question particle
intonation-only representation
auxiliary movement
special morphology
mixed strategy
```

Actual strategy:

```text
NOT YET RECORDED
```

Required details:

- word order;
- negation;
- tense;
- subject pronouns;
- punctuation;
- embedded form.

---

## 53. Content questions

For each interrogative category, document:

- interrogative form;
- case/preposition;
- fronting or in-situ behavior;
- gap representation;
- agreement;
- embedded form;
- ambiguity.

Current rules:

```text
NOT YET RECORDED
```

---

## 54. Question complements

Document verbs/adjectives/nouns selecting question complements.

Required facts:

- complementizer;
- direct/indirect distinction;
- word order;
- punctuation;
- tense/mood.

Current rules:

```text
NOT YET RECORDED
```

---

# Part X — Relative clauses and extraction

## 55. Relative representation

The project must document:

- relative-clause lincat;
- gap/category representation;
- relative pronoun/complementizer;
- agreement;
- antecedent feature access;
- restrictive/non-restrictive distinction if supported.

Current representation:

```text
NOT YET RECORDED
```

---

## 56. Subject relatives

Record:

- gap position;
- relative marker;
- subject agreement;
- word order;
- resumptive strategy if any.

Current rule:

```text
NOT YET RECORDED
```

---

## 57. Object and oblique relatives

Record:

- case/preposition;
- pied-piping vs stranding;
- resumptive pronouns;
- gap behavior;
- agreement;
- unsupported combinations.

Current rules:

```text
NOT YET RECORDED
```

---

## 58. Relative attachment

Document:

- attachment to common noun/NP;
- agreement/feature transfer;
- punctuation;
- definiteness interaction;
- stacking.

Current rules:

```text
NOT YET RECORDED
```

---

# Part XI — Coordination

## 59. Coordination representation

The project must document coordination lists and final coordination constructors.

Required facts:

- list representation;
- minimum conjunct count;
- conjunction placement;
- separator punctuation;
- agreement resolution;
- category-specific behavior.

Current representation:

```text
NOT YET RECORDED
```

---

## 60. Category-specific coordination

Document at least the categories used in release scenarios:

```text
NP
AP
Adv
VP
S
Cl
```

Actual supported set:

```text
NOT YET RECORDED
```

### 60.1 No universal assumption

One generic string-joining rule must not be applied to every category unless category state and agreement are preserved correctly.

---

## 61. Correlative and alternative coordination

If supported, record behavior for:

```text
both … and
either … or
neither … nor
not only … but also
```

Actual support:

```text
NOT YET RECORDED
```

---

# Part XII — Structural constructors

## 62. Structural ownership

Structural modules own closed-class lexical material used by syntax.

Examples:

```text
pronouns
determiners
conjunctions
prepositions
auxiliaries
negation markers
complementizers
interrogatives
relative markers
punctuation tokens
```

The actual inventory must be recorded in project documentation.

### 62.1 Required presence

A structural symbol consumed by an entrypoint or required scenario is release-significant.

### 62.2 Disabled symbol

A disabled or fallback symbol must have a status-ledger entry.

### 62.3 Category integrity

Structural constructors must return fully initialized documented categories.

---

## 63. Prepositions and case selectors

The project must document the `Prep` or equivalent representation.

Potential fields:

```text
surface string
required case
postposition/preposition state
contraction behavior
government class
```

Current representation:

```text
NOT YET RECORDED
```

No syntax module may assume a field absent from the category contract.

---

## 64. Pronoun constructors

Structural pronoun constructors must document:

- paradigm inputs;
- agreement;
- case forms;
- clitic/full forms;
- reflexive forms;
- possessive forms;
- politeness;
- defaults.

Current constructors:

```text
NOT YET RECORDED
```

---

## 65. Determiner and quantifier constructors

Document:

- arity;
- agreement;
- definiteness;
- number constraints;
- noun-class/gender behavior;
- case forms;
- zero realization.

Current constructors:

```text
NOT YET RECORDED
```

---

# Part XIII — Extension rules

## 66. Extension ownership

Extension functions must be coordinated through the project's extension owner.

### 66.1 Inherited extension

When inherited from RGL:

- imported provider must be documented;
- overridden functions must be listed;
- unsupported functions must be visible;
- compatibility must be tested.

### 66.2 Local extension

A local extension must define:

- abstract provider;
- concrete provider;
- categories/lincats used;
- public constructor contract;
- scenario coverage;
- release status.

### 66.3 Shadowing

Local redefinition of an inherited function requires explicit policy and a decision-log entry.

---

## 67. Construction-specific exceptions

Language-specific exceptions belong in the narrowest coherent owner.

They must not be implemented as broad string tests scattered across syntax modules.

### 67.1 Lexical exceptions

Prefer lexical feature/state or paradigm ownership when the exception is lexical.

### 67.2 Structural exceptions

Prefer structural entries when the exception belongs to a closed-class item.

### 67.3 Syntax exceptions

Use syntax-level exception logic only when the construction itself requires it.

---

# Part XIV — Pattern matching and string rules

## 68. Parameter pattern matching

Pattern matching over grammatical parameters is permitted and expected.

It must be:

- exhaustive;
- type-driven;
- documented when behavior differs materially;
- tested for every release-significant branch.

### 68.1 Parameter evolution

Adding a parameter value requires review of every pattern match.

### 68.2 Wildcards

A wildcard branch must not hide a missing newly added case.

Strict review SHOULD flag wildcard fallbacks in release-significant parameter matches.

---

## 69. Runtime string matching

Branching on surface strings is discouraged.

Examples:

```text
case np.s of { "..." => ... }
```

### 69.1 Allowed use

Runtime string matching requires explicit documentation when:

- no typed grammatical distinction is available;
- the match is bounded and stable;
- Unicode/normalization behavior is defined;
- false matches are considered;
- scenarios cover it;
- status is recorded when temporary.

### 69.2 Preferred alternative

Prefer:

- `param`;
- typed lincat field;
- lexical feature;
- separate constructor;
- paradigm distinction.

### 69.3 Release review

Undocumented runtime string matching is a release-blocking static finding.

---

## 70. Untyped string-pattern blocks

Untyped `case` or `table` patterns based on string concatenation are high-risk.

They must be replaced by typed distinctions or explicitly justified.

### 70.1 Prohibited reliance

A constructor must not rely on incidental spelling to recover grammatical category or agreement.

### 70.2 Evidence

An accepted exception requires:

- status-ledger ID;
- examples;
- negative cases;
- normalization behavior;
- exit condition.

---

## 71. String normalization

Shared orthographic normalization must have one owner.

Syntax modules must not duplicate:

- case conversion;
- apostrophe rules;
- hyphenation;
- elision;
- spacing normalization;
- diacritic manipulation.

The owner is normally a morphology or resource module.

Actual project owner:

```text
NOT YET RECORDED
```

---

# Part XV — Defaults and fallbacks

## 72. Default-value registry

Every default must be documented.

Potential defaults:

```text
default number
default gender/class
default case
default polarity
default tense
default mood
default person
default word order
default complementizer
```

Actual active defaults:

```text
NOT YET RECORDED
```

### 72.1 Safe default requirement

A default is acceptable only when:

- semantically justified;
- deterministic;
- visible to consumers;
- tested;
- does not hide missing implementation.

---

## 73. Fallback policy

A fallback is not a final implementation by default.

Every fallback requires:

```text
status ID
provider
affected constructors
behavior
reason
known incorrect cases
release impact
replacement plan
exit condition
validation
```

### 73.1 Fallback statuses

Use project status values such as:

```text
temporary
fallback
warning
blocked
resolved
```

### 73.2 Release

An unapproved fallback blocks release.

An approved fallback may be non-blocking only when project scope explicitly accepts it.

---

## 74. Placeholder output

Strings such as:

```text
TODO
TBD
FIXME
UNKNOWN
placeholder
```

must not appear in release linguistic output unless they are actual intended language data.

A placeholder used as fallback output is release-blocking.

---

# Part XVI — Public API and lexicon constructors

## 75. Paradigm-to-lexicon contract

Lexicon-facing constructors such as:

```text
mkN
mkV
mkA
mkAdv
mkPrep
```

or project equivalents must document:

- arity;
- argument order;
- accepted principal parts;
- inferred forms;
- default grammatical features;
- irregular pathways;
- result category.

Actual active constructor registry:

```text
NOT YET RECORDED
```

---

## 76. Shallow constructors

A shallow constructor accepts insufficient data to guarantee complete inflection or syntax.

It must be marked:

```text
temporary
fallback
or deliberately limited public API
```

### 76.1 Required disclosure

Document:

- inferred assumptions;
- unsupported forms;
- behavior under morphology analysis;
- release policy.

### 76.2 No masquerading

A shallow constructor must not be documented as complete.

---

## 77. Constructor naming

Names should communicate:

- result category;
- irregularity;
- argument distinction;
- valency;
- special behavior.

### 77.1 Compatibility

Renaming a public constructor is breaking.

### 77.2 Aliases

A compatibility alias may be retained during migration.

Canonical new code should use the current name.

---

# Part XVII — Error and unsupported behavior

## 78. Unsupported construction

An unsupported abstract function or construction must be represented explicitly.

Allowed mechanisms:

- missing concrete linearization;
- documented blocked status;
- explicit project-scope exclusion;
- deliberate restricted constructor with clear diagnostics.

### 78.1 Prohibited mechanism

Returning unrelated generic text to avoid a missing function is prohibited.

---

## 79. Internal impossibility

When typed state represents an impossible combination, the design should prevent construction where possible.

If impossible states remain representable:

- document invariant;
- assert through construction discipline;
- test public constructors;
- avoid silent arbitrary output.

---

## 80. GF diagnostics

GF remains authoritative for:

- type mismatch;
- missing field;
- missing function;
- invalid pattern;
- module-resolution error;
- syntax error.

Project documentation and static scanning supplement but do not replace GF evidence.

---

# Part XVIII — Validation

## 81. Compilation validation

Every changed public syntax constructor requires compilation of:

1. provider module;
2. direct consumers;
3. downstream checkpoints;
4. release entrypoints.

### 81.1 Lincat changes

A lincat field change requires compilation of all consumers, not only the provider.

### 81.2 Constructor changes

An arity/order/result change requires compilation of every call site.

---

## 82. Scenario validation

Each release-significant rule requires at least one scenario case.

A scenario case should identify:

```text
rule ID
constructor/function
input tree or phrase
expected operation
expected behavior
section marker
```

### 82.1 Minimum scenario families

For in-scope project features, expected scenario families include:

```text
load
linearize
parse
missing
```

Additional families:

```text
agreement
negation
questions
relatives
coordination
complements
morphology
round-trip
```

### 82.2 Current coverage

Project-specific mapping:

```text
NOT YET RECORDED
```

Release impact:

```text
BLOCKING
```

---

## 83. Gold validation

Use golds for deterministic, reviewable syntax output.

Examples:

- representative linearizations;
- parse trees;
- ambiguity lists;
- missing-function inventory;
- morphology forms.

### 83.1 Rule traceability

Each gold section SHOULD reference a rule/case ID in the validation specification.

### 83.2 Intentional change

Changing a syntax rule that changes normalized output requires deliberate gold review.

Normal validation must never update gold.

---

## 84. Parse validation

Parsing scenarios should test:

- accepted representative phrases;
- rejected or ambiguous cases where meaningful;
- expected abstract trees;
- preposition/case behavior;
- word order;
- question/relative constructions;
- lexical/syntax boundaries.

### 84.1 Parse availability

If parsing is outside project scope, the release criteria must state so explicitly.

---

## 85. Linearization validation

Linearization scenarios should cover:

- every public constructor family;
- agreement branches;
- polarity;
- tense/mood/aspect;
- complement frames;
- questions;
- relatives;
- coordination;
- structural items;
- accepted exceptions.

### 85.1 Negative evidence

A single happy-path output is insufficient for a parameterized rule.

---

## 86. Missing-function validation

Required release inspection:

```text
pg -missing
```

or the compatible GF operation.

Every reported missing function must be:

- implemented;
- explicitly accepted by scope;
- or release-blocking.

---

## 87. Round-trip validation

Where appropriate:

```text
tree → linearize → parse
```

Round-trip expectations must account for legitimate ambiguity.

Round-trip is supportive evidence, not a universal identity guarantee.

---

## 88. Constructor unit fixtures

GF scenarios or minimal fixture modules SHOULD isolate complex constructors.

A fixture must use the real public provider, not duplicate its logic.

---

# Part XIX — Coverage matrix

## 89. Required rule coverage fields

Every rule entry must map to:

```text
provider
consumers
compile checkpoint
linearization case
parse case when applicable
gold section
status-ledger entry when incomplete
decision-log entry when breaking
```

### 89.1 Current matrix status

```text
NOT YET RECORDED
```

Release impact:

```text
BLOCKING
```

---

## 90. Minimum release coverage

For every release entrypoint:

- every abstract function is implemented or accepted explicitly;
- every public syntax constructor has a rule entry;
- every lincat field consumed by syntax is documented;
- every agreement branch is covered;
- every required scenario passes;
- every required gold matches;
- no blocking fallback remains.

---

# Part XX — Change control

## 91. Internal compatible change

Examples:

- refactor private helper;
- optimize a table;
- rename a local binding;
- decompose a long expression;
- improve comments;
- add tests without output change.

Required:

- provider compile;
- affected scenarios when risk exists.

---

## 92. Compatible public extension

Examples:

- add a new constructor;
- add a derivable optional field;
- add a new supported construction without changing existing output.

Required:

- constructor registry entry;
- provider/consumer update;
- architecture/dependency update;
- validation cases;
- project minor-release analysis.

---

## 93. Breaking change

Examples:

- rename constructor;
- change arity;
- change argument order;
- change result category;
- rename/remove lincat field;
- change agreement controller;
- change canonical word order;
- change negation strategy;
- change question/relative representation;
- redefine default;
- remove supported construction.

Required sequence:

1. decision-log entry;
2. contract version analysis;
3. provider update;
4. all consumer updates;
5. entrypoint update;
6. scenario update;
7. gold review/update;
8. status/issue update;
9. full checkpoint/release validation;
10. project release-version analysis.

---

## 94. GF/RGL migration impact

A GF or RGL update may change:

- inherited constructor availability;
- lincat representations;
- shell output;
- parse trees;
- linearization;
- missing-function behavior.

Required review:

- compatibility result;
- inherited interface diff;
- source compilation;
- scenarios;
- golds;
- this document;
- decision log.

---

## 95. Source move or module rename

A module rename requires updates to:

- module declaration;
- imports;
- `project.toml`;
- dependency map;
- interfile lock;
- constructor registry;
- scenarios;
- gold metadata where relevant;
- documentation;
- release entrypoints.

Historical evidence remains unchanged.

---

# Part XXI — Rule entry format

## 96. Canonical syntax-rule entry

Use this structure for each project rule:

```markdown
### SYN-<FAMILY>-<NUMBER> — <rule name>

**Status:** Active | Deprecated | Retired

**Provider:** `path/to/module.gf`

**Public functions/constructors:**
- `FunctionName`
- `constructorName`

**Inputs:**
- category and required state

**Output:**
- category and guaranteed state

**Surface order:**
- exact constituent order

**Agreement:**
- controller, target, dimensions

**Form selection:**
- table and parameters selected

**State propagation:**
- copied, transformed, consumed, introduced

**Defaults:**
- explicit defaults

**Exceptions/fallbacks:**
- stable status IDs or none

**Consumers:**
- modules, entrypoints, scenarios

**Validation:**
- compile checkpoints
- scenario IDs/case IDs
- gold sections

**Breaking changes:**
- incompatible edits

**Last reviewed:** date/release
```

### 96.1 Final contract statuses

Release-critical final entries use:

```text
Active
Deprecated
Retired
```

Temporary implementation status belongs to `STATUS_LEDGER.md`.

---

## 97. Canonical constructor entry

```markdown
### SYN-CONSTRUCTOR-<NUMBER> — `constructorName`

**Provider:** `path/to/module.gf`  
**Visibility:** Public  
**Kind:** syntax | structural | lexical | coercion | extension  
**GF type:** exact type  
**Argument order:** exact order  
**Preconditions:** explicit  
**Result category:** exact category  
**Initialized fields:** complete list  
**Selected fields:** complete list  
**Defaults:** explicit  
**Fallback:** none or status ID  
**Direct consumers:** complete list  
**Validation:** cases/checkpoints  
**Release significance:** blocking | non-blocking
```

---

# Part XXII — Project rule inventory

## 98. Core family inventory

The following inventory must be completed from actual source.

| Family | Provider | Public rule IDs | Status |
|---|---|---|---|
| Category/lincat provider | Not yet recorded | Not yet recorded | Blocking |
| Noun syntax | Not yet recorded | Not yet recorded | Blocking if in scope |
| Adjective syntax | Not yet recorded | Not yet recorded | Blocking if in scope |
| Adverb syntax | Not yet recorded | Not yet recorded | Blocking if in scope |
| Verb syntax | Not yet recorded | Not yet recorded | Blocking if in scope |
| Clause/sentence syntax | Not yet recorded | Not yet recorded | Blocking |
| Question syntax | Not yet recorded | Not yet recorded | Blocking if in scope |
| Relative syntax | Not yet recorded | Not yet recorded | Blocking if in scope |
| Coordination | Not yet recorded | Not yet recorded | Blocking if in scope |
| Structural syntax | Not yet recorded | Not yet recorded | Blocking |
| Extensions | Not yet recorded | Not yet recorded | Blocking if used |
| Grammar entrypoint | Not yet recorded | Not yet recorded | Blocking |
| Syntax/API entrypoint | Not yet recorded | Not yet recorded | Blocking if configured |

---

## 99. Constructor inventory

Current authoritative inventory:

```text
NOT YET RECORDED
```

Required action:

1. enumerate every public `oper` used outside its provider;
2. enumerate every release-significant `lin`;
3. record exact GF type;
4. identify direct consumers;
5. link validation;
6. classify fallback/deprecation;
7. reconcile with project interfile lock.

---

## 100. State-field inventory

Current authoritative inventory:

```text
NOT YET RECORDED
```

Required table columns:

```text
category
field
GF type
meaning
owner
writers
readers
default
invariant
validation
```

This table should align with `CATEGORY_AND_LINCAT_CONTRACT.md`, which remains the primary detailed field authority.

---

## 101. Word-order inventory

Current authoritative inventory:

```text
NOT YET RECORDED
```

Required construction rows:

```text
basic clause
transitive clause
ditransitive clause
NP internal order
adjective placement
adverb placement
negation
polar question
content question
relative clause
coordination
subordinate clause
non-finite complement
```

For unsupported constructions, record:

```text
out of project scope
```

with release-criteria alignment.

---

## 102. Agreement inventory

Current authoritative inventory:

```text
NOT YET RECORDED
```

Required rows:

```text
subject–verb
determiner–noun
adjective–noun
predicative adjective–subject
pronoun/case
possessive
relative marker
coordination
participle
object agreement, if applicable
```

---

## 103. Complement inventory

Current authoritative inventory:

```text
NOT YET RECORDED
```

Required columns:

```text
verb/category
complement category
preposition/case
order
optional
passive behavior
extraction behavior
constructor
validation
```

---

# Part XXIII — Static review rules

## 104. Release-significant scan indicators

The project static policy SHOULD detect:

- runtime string matching on `.s`;
- untyped string-pattern cases/tables;
- public constructor without type/contract reference;
- unresolved conflict markers;
- `TODO`/`TBD`/`FIXME` in active syntax code;
- duplicate helper definitions;
- undocumented empty-string fallback;
- wildcard parameter branch hiding new cases;
- stale language suffix;
- commented-out required `lin`;
- copied/backup source file;
- trailing whitespace only as a non-blocking style rule unless project policy says otherwise.

### 104.1 Scan authority

Static findings are heuristic/project-policy evidence.

GF compilation remains authoritative for GF syntax/type correctness.

---

## 105. Manual review indicators

Manual review is required for:

- output changes without type changes;
- agreement-controller changes;
- order changes;
- default changes;
- new coercions;
- lossy state transformations;
- new string matching;
- new fallback;
- inherited RGL override;
- new ambiguity;
- punctuation ownership changes.

---

# Part XXIV — Release gates

## 106. Syntax release criteria

The syntax/constructor portion of release passes only when:

```text
[ ] Active language identity is recorded
[ ] Module inventory is recorded
[ ] Category/lincat contract is complete
[ ] Constructor registry is complete
[ ] State-field registry is complete
[ ] Word-order rules are complete
[ ] Agreement rules are complete
[ ] Complement frames are complete
[ ] All configured checkpoints compile
[ ] All release entrypoints compile
[ ] Missing-function policy passes
[ ] Required syntax scenarios pass
[ ] Required golds match
[ ] No undocumented fallback remains
[ ] No blocking runtime string match remains
[ ] Dependency map matches imports
[ ] Interfile contract lock matches source
[ ] Breaking changes have decisions
```

### 106.1 Current result

Based on currently available documentation:

```text
syntax release criteria = NOT SATISFIED
reason = project-specific registries not yet recorded
```

This statement must be re-evaluated after the active source and project identity are documented.

---

## 107. Required evidence

Release evidence should include:

- compile results for syntax providers and consumers;
- entrypoint compile results;
- scenario results;
- normalized outputs;
- gold comparisons;
- missing-function output;
- relevant static findings;
- source fingerprints;
- GF/RGL identity;
- manifest references.

---

# Part XXV — Diagnostics and drift

## 108. Drift indicators

Syntax contract drift exists when:

- source uses a field absent from the lincat contract;
- two modules define the same constructor family;
- constructor arity differs between docs and source;
- argument order differs between source and consumers;
- a scenario tree calls an undocumented function;
- a gold changes without rule review;
- a fallback has no ledger entry;
- parameter value is added without pattern review;
- word order changes without a decision;
- agreement state is lost in a coercion;
- an entrypoint imports a test-only helper;
- runtime string matching appears without exception record;
- this document says `Not yet recorded` for a release-used construction;
- source behavior is inferred from another language rather than recorded.

Every indicator requires:

1. restore the existing rule; or
2. change the contract deliberately.

---

## 109. Recommended diagnostic codes

```text
SYNTAX_RULE_UNDOCUMENTED
SYNTAX_CONSTRUCTOR_UNREGISTERED
SYNTAX_CONSTRUCTOR_ARITY_MISMATCH
SYNTAX_ARGUMENT_ORDER_MISMATCH
SYNTAX_RESULT_CATEGORY_MISMATCH
SYNTAX_LINCAT_FIELD_UNDOCUMENTED
SYNTAX_STATE_DROPPED
SYNTAX_AGREEMENT_UNDOCUMENTED
SYNTAX_WORD_ORDER_UNDOCUMENTED
SYNTAX_COMPLEMENT_FRAME_UNDOCUMENTED
SYNTAX_DEFAULT_UNDOCUMENTED
SYNTAX_FALLBACK_UNREGISTERED
SYNTAX_STRING_MATCH_UNDOCUMENTED
SYNTAX_PATTERN_NONEXHAUSTIVE
SYNTAX_DUPLICATE_HELPER_OWNER
SYNTAX_SCENARIO_COVERAGE_MISSING
SYNTAX_GOLD_COVERAGE_MISSING
SYNTAX_RELEASE_REGISTRY_INCOMPLETE
```

---

# Part XXVI — Maintenance workflow

## 110. Adding a constructor

Required workflow:

1. identify owning family/module;
2. define exact GF type;
3. define lincat fields read/written;
4. define agreement and order;
5. add constructor registry entry;
6. update interfile contract;
7. update dependency map;
8. implement;
9. compile provider and consumers;
10. add scenario;
11. add/update gold if appropriate;
12. update coverage matrix;
13. review release impact.

---

## 111. Changing a constructor

Required workflow:

1. classify internal/compatible/breaking;
2. identify all consumers;
3. record decision when breaking;
4. update this document before or with source;
5. update lincat contract if needed;
6. update provider/consumers;
7. compile all checkpoints/entrypoints;
8. run relevant scenarios;
9. review gold diffs;
10. update release/status records.

---

## 112. Removing a constructor

Required workflow:

- prove no active consumer remains;
- deprecate when public;
- update abstract syntax if applicable;
- update scenarios/golds;
- update entrypoints/API;
- update project contract version;
- document migration;
- remove only under project version policy.

---

## 113. Completing this document

To convert the current incomplete registry into a release-ready project specification:

1. read `project/project.toml`;
2. record project identity and module suffix;
3. inventory active `.gf` source;
4. identify category/lincat provider;
5. extract public lincats and fields;
6. inventory public syntax `oper` and release-significant `lin`;
7. map imports and consumers;
8. record family-specific order/agreement/complement rules;
9. link scenarios and golds;
10. reconcile status ledger and known issues;
11. compile all consumers;
12. run required scenarios;
13. replace every blocking `Not yet recorded` status with verified content;
14. complete release checklist.

No step should infer language behavior from filenames alone.

---

# Part XXVII — Review checklist

## 114. Constructor review

```text
[ ] Exact GF type recorded
[ ] Provider recorded
[ ] Direct consumers recorded
[ ] Argument order recorded
[ ] Result category recorded
[ ] Fields selected recorded
[ ] Fields initialized recorded
[ ] Agreement recorded
[ ] Surface order recorded
[ ] Defaults recorded
[ ] Fallback status recorded
[ ] Compilation evidence exists
[ ] Scenario evidence exists
[ ] Gold reviewed when output stable
```

---

## 115. Family review

```text
[ ] Family owner is unique
[ ] Dependencies point downward
[ ] Lincat fields are documented
[ ] Parameter matches are exhaustive
[ ] Word order is explicit
[ ] Agreement controller is explicit
[ ] Complement frames are explicit
[ ] Unsupported constructions are explicit
[ ] Temporary behavior is in status ledger
[ ] Entry points expose intended surface
```

---

## 116. Release review

```text
[ ] No project-specific registry remains not recorded
[ ] No unresolved placeholder output exists
[ ] No unapproved missing function exists
[ ] No undocumented string match exists
[ ] All checkpoints compile
[ ] All entrypoints compile
[ ] Required scenarios pass
[ ] Required golds match
[ ] Contract lock and dependency map agree
[ ] Release manifest contains evidence
```

---

# Part XXVIII — Final enforcement rule

Syntax is not only the final order of strings.

It is the complete contract by which typed grammatical values are combined, transformed, and preserved until final linearization.

> Every public syntax constructor must have a documented type, owner, argument order, result category, state behavior, agreement rule, surface-order rule, consumer set, and validation proof.

The active project's language-specific rule inventory is currently not recorded in the available sources. Until it is completed and validated against actual GF modules, this document correctly reports the syntax contract as incomplete and release-blocking rather than inventing linguistic behavior.
