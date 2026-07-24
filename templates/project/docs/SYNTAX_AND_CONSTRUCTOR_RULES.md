# GF Wordbench Project Template — Syntax and Constructor Rules

**Document ID:** `GF-WB-PROJECT-TEMPLATE-SYNTAX-CONSTRUCTORS`  
**Document role:** Normative template  
**Decision status:** Accepted template contract  
**Implementation status:** Template available; active-project implementation depends on initialization  
**Verification status:** Requires placeholder, source, contract and validation checks after initialization  
**Target path:** `templates/project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md`  
**Applies to:** One active GF project created from this template  
**Template owner:** GF Wordbench maintainers  
**Project owner after initialization:** `<PROJECT_OWNER>`  
**Language after initialization:** `<LANGUAGE_NAME>`  
**Language code after initialization:** `<LANGUAGE_CODE>`  
**GF module suffix after initialization:** `<GF_SUFFIX>`  
**Primary contract references:** `PIFC-MODULE-001`, `PIFC-MODULE-002`, `PIFC-LINCAT-001`, `PIFC-HELPER-001`, `PIFC-DOC-002`, `PIFC-DOC-005`  
**Document version:** `1.0.0`  
**Last reviewed:** `<YYYY-MM-DD>`

---

## 1. Purpose

This document is the normative project specification for syntax composition and public constructor behavior in one active GF project.

It records how the project combines linguistic values into larger values, including:

```text
phrases
clauses
sentences
questions
relative clauses
coordination
subordination
modification
complementation
predication
polarity
tense, aspect and mood
agreement propagation
case or adposition selection
word order
clitic or particle placement
punctuation and orthography
language-specific extensions
```

It also records the behavior expected from public GF constructors, including:

```text
abstract functions
concrete `lin` rules
shared constructor `oper` values
coercions
structural helpers
extension helpers
interface and instance operations
entrypoint-visible functions
```

The central rule is:

> Every public syntax constructor must have one authoritative provider, a documented GF type and composition rule, explicit dependencies on public lincat fields, deterministic output within its declared scope, and validation evidence covering its meaningful alternatives.

---

## 2. Template use

This file is copied from:

```text
templates/project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
```

to:

```text
project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
```

during project reset or initialization.

The template contains generic rules and placeholders.

After initialization, project maintainers must:

1. replace required identity placeholders;
2. remove non-applicable example sections;
3. identify the authoritative syntax providers;
4. inventory public constructors;
5. record language-specific ordering and agreement rules;
6. link all public lincat dependencies;
7. identify fallbacks, experimental rules and blockers;
8. define validation scenarios;
9. update the project interfile contract lock;
10. record the initial review date and evidence.

A populated active-project copy must not remain a generic catalogue of possibilities.

It must state what the active GF project actually guarantees.

---

## 3. Scope

This document governs project-owned syntax and constructor behavior involving:

```text
abstract functions implemented by concrete syntax
concrete linearization rules
syntax module responsibilities
structural module responsibilities
extension module responsibilities
public constructor helpers
phrase and clause composition
argument realization
agreement selection
feature propagation
word-order selection
case and adposition selection
polarity and negation
tense, aspect and mood realization
question formation
relative-clause formation
coordination
subordination
ellipsis when explicitly supported
punctuation and spacing
orthographic composition
variants used by public constructors
failure or incompleteness behavior
```

This document does not govern:

```text
the complete lincat field inventory
the complete morphology paradigm inventory
private local helpers with no consumer
GF Wordbench Python behavior
process execution
report formatting
scenario normalization
application state
generated run evidence
```

The complete public lincat shapes belong to:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

The complete morphology contract belongs to:

```text
project/docs/MORPHOLOGY_SPEC.md
```

This document references those fields and operations; it does not redefine them independently.

---

## 4. Related authoritative documents

```text
project/project.toml
project/docs/00_PROJECT_START_HERE.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/LANGUAGE_OVERVIEW.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MORPHOLOGY_SPEC.md
project/docs/VALIDATION_SPEC.md
project/docs/TEST_COVERAGE_MATRIX.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
project/docs/KNOWN_ISSUES.md
project/docs/RELEASE_CRITERIA.md
project/docs/RESEARCH_EVIDENCE.md
project/validation/
```

### 4.1 Ownership map

| Question | Authoritative owner |
|---|---|
| Which project is active? | `project/project.toml` |
| Which module owns a constructor? | `MODULE_DEPENDENCY_MAP.md` and contract lock |
| Which fields exist on a lincat? | `CATEGORY_AND_LINCAT_CONTRACT.md` |
| How are lexical and inflectional forms produced? | `MORPHOLOGY_SPEC.md` |
| How are values composed syntactically? | This document |
| Which cross-file promises are locked? | `INTERFILE_CONTRACT_LOCK.md` |
| Which rules are temporary or fallback-backed? | `STATUS_LEDGER.md` |
| Why was a major syntax choice made? | `DECISION_LOG.md` |
| Which evidence proves the rule? | `VALIDATION_SPEC.md` and coverage matrix |
| Does the rule block release? | `RELEASE_CRITERIA.md` |

---

## 5. Normative terms

- **MUST**: mandatory project rule.
- **MUST NOT**: prohibited behavior.
- **SHOULD**: expected unless a documented project exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional behavior within the documented scope.
- **CONSTRUCTOR**: public abstract function, concrete `lin`, or public helper that combines linguistic values.
- **PROVIDER**: GF module that owns a constructor, helper, field or composition rule.
- **CONSUMER**: module, scenario or entrypoint that relies on that provider.
- **PUBLIC SURFACE**: symbol, GF type, lincat field, record shape, parameter, ordering rule or artifact visible across a file boundary.
- **COMPOSITION RULE**: documented method by which constructor inputs determine result structure and linearization.
- **FEATURE**: grammatical value such as number, gender, person, case, tense, aspect, mood, polarity or definiteness.
- **FEATURE PROPAGATION**: transfer or calculation of features from constructor inputs to output.
- **HEAD**: input that controls one or more grammatical properties of the result.
- **DEPENDENT**: input whose realization is constrained by the head or construction.
- **LINEARIZATION ORDER**: deterministic ordering of realized components.
- **COERCION**: documented conversion from one category or representation to another.
- **FALLBACK**: reduced or generic behavior used when the intended implementation is unavailable.
- **VARIANT**: one of several GF outputs intentionally exposed by a constructor.
- **INCOMPLETE CONSTRUCTOR**: public constructor whose documented semantic or syntactic scope is not fully implemented.
- **BLOCKED CONSTRUCTOR**: constructor that cannot be completed because a named dependency is unresolved.
- **GOLD**: reviewed normalized expected output for a scenario.

---

# Part I — Global syntax architecture

## 6. Syntax architecture inventory

Populate the final project-specific inventory.

| Layer | Authoritative module or modules | Public responsibility | Direct consumers | Checkpoint |
|---|---|---|---|---|
| Abstract syntax | `<ABSTRACT_MODULE>` | Public categories and functions | Concrete syntaxes | `<CHECKPOINT>` |
| Shared resources | `<RESOURCE_MODULES>` | Parameters, helpers and shared records | Category and syntax providers | `<CHECKPOINT>` |
| Category implementation | `<CATEGORY_MODULES>` | Public lincats and low-level constructors | Syntax modules | `<CHECKPOINT>` |
| Core syntax | `<SYNTAX_MODULES>` | Phrase and clause composition | Structural, extension and entrypoint modules | `<CHECKPOINT>` |
| Structural lexicon | `<STRUCTURAL_MODULES>` | Closed-class words and structural constructors | Syntax and grammar entrypoints | `<CHECKPOINT>` |
| Extensions | `<EXTENSION_MODULES>` | Language-specific or optional constructions | Extension coordinator and entrypoints | `<CHECKPOINT>` |
| Grammar entrypoint | `<GRAMMAR_ENTRYPOINT>` | Final grammar surface | Scenarios and PGF build | `<CHECKPOINT>` |
| API entrypoint | `<API_ENTRYPOINT_OR_NONE>` | Application-facing surface | Runtime consumers | `<CHECKPOINT_OR_NONE>` |

### 6.1 Required direction

Expected dependency direction:

```text
abstract syntax
      ↓
shared resources and morphology
      ↓
category implementations
      ↓
core syntax
      ↓
structural and extension modules
      ↓
grammar or language entrypoints
      ↓
API or PGF entrypoint
```

Lower-level modules MUST NOT import final entrypoints.

Circular imports are prohibited.

### 6.2 One authoritative provider

Each public constructor family must have one authoritative provider.

Examples:

```text
noun-phrase formation
adjective modification
verb-phrase complementation
clause predication
sentence formation
question formation
relative-clause formation
coordination
subordination
negation
tense realization
```

Duplicated providers require an explicit selection rule and decision record.

---

## 7. Separation of type shape and constructor behavior

`CATEGORY_AND_LINCAT_CONTRACT.md` owns:

```text
category names
lincat GF types
record fields
table indices
parameter values
field meanings
initialization requirements
```

This document owns:

```text
which fields a constructor reads
which input controls agreement
which features are propagated
which helper realizes a component
which order is selected
which variants are emitted
which output fields are built
which failure or fallback occurs
```

### 7.1 No duplicate field definitions

This document may show a short referenced field shape for clarity.

It MUST link to the canonical lincat contract.

When the two disagree, the project is inconsistent and must be corrected.

### 7.2 No hidden lincat dependency

A constructor MUST NOT read a record field, table dimension or parameter value that is absent from the public lincat contract.

### 7.3 No silent flattening

Structured categories such as:

```text
NP
AP
CN
VP
Cl
S
QS
RS
Prep
Pron
Adv
```

or language-specific records MUST NOT be reduced to `Str` solely to make one constructor easier to implement.

A flattening that affects consumers is a breaking project change.

---

## 8. Abstract-to-concrete rule

Every public abstract function must have:

```text
one documented GF type
one owning abstract module
one or more declared concrete providers
explicit implementation status
validation or explicit omission
```

### 8.1 Type preservation

A concrete `lin` implementation MUST satisfy the abstract function type.

Changing:

```text
argument category
argument order
result category
function name
category name
```

is a breaking project contract change unless the function was explicitly experimental and unconsumed.

### 8.2 Incomplete concrete syntax

An incomplete concrete syntax must identify omissions through:

```text
GF missing-function inspection
status ledger entries
validation scenarios
release policy
```

Missing functions MUST NOT be concealed through meaningless placeholder output.

### 8.3 Inheritance

When a concrete module inherits another module:

- inherited public behavior must be identified;
- overridden behavior must be listed;
- unsupported inherited assumptions must be reviewed;
- the origin of every public constructor must remain traceable.

---

# Part II — Constructor registry

## 9. Constructor registry requirement

The active-project copy must maintain a registry of every public constructor family that affects documented project behavior.

The registry may group closely related functions when they share one contract.

Minimum registry columns:

| Field | Meaning |
|---|---|
| Constructor ID | Stable project-local identifier |
| Abstract function | Public GF function name |
| Provider | Owning concrete or resource module |
| GF type | Exact abstract type |
| Head | Input controlling result features |
| Required fields | Public lincat fields read |
| Output category | Result lincat |
| Order rule | Linearization order |
| Agreement rule | Feature selection or propagation |
| Status | `active`, `experimental`, `blocked`, `deprecated`, `retired` |
| Scenario | Primary validation scenario |
| Gold | Expected output when applicable |

---

## 10. Constructor identifiers

Recommended format:

```text
SYN-<DOMAIN>-<NUMBER>
```

Examples:

```text
SYN-NP-001
SYN-AP-001
SYN-VP-004
SYN-CL-002
SYN-Q-001
SYN-REL-001
SYN-COORD-001
SYN-EXT-003
```

Identifiers must remain stable after being referenced by:

```text
scenarios
coverage matrix
status ledger
decision log
known issues
release criteria
```

Retired identifiers are not reused.

---

## 11. Constructor registry template

| Constructor ID | Abstract function | Provider | GF type | Head | Order | Agreement | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| `SYN-<DOMAIN>-001` | `<FUNCTION>` | `<MODULE>.gf` | `<A -> B -> C>` | `<INPUT>` | `<ORDER>` | `<RULE>` | `<STATUS>` | `<SCENARIO/GOLD>` |

Delete the sample row after the active registry is populated.

---

## 12. Detailed constructor template

Use this template for every public constructor or coherent constructor family.

```markdown
## SYN-<DOMAIN>-<NUMBER> — <constructor or family name>

**Status:** `active | experimental | blocked | deprecated | retired`  
**Abstract provider:** `<ABSTRACT_MODULE>.gf`  
**Concrete provider:** `<CONCRETE_OR_RESOURCE_MODULE>.gf`  
**Direct consumers:** `<MODULES, ENTRYPOINTS, SCENARIOS>`  
**Affected project contracts:** `<PIFC-...>`  
**Status-ledger entry:** `<STAT-... or none>`  
**Decision reference:** `<DEC-... or none>`  
**Last reviewed:** `<YYYY-MM-DD or release>`

### Public function

```gf
fun <FUNCTION> : <INPUT_1> -> <INPUT_2> -> <RESULT> ;
```

### Input contracts

| Input | Category | Required public fields | Semantic or syntactic role |
|---|---|---|---|
| `<x>` | `<CATEGORY>` | `<FIELDS>` | `<ROLE>` |

### Head and agreement controller

```text
<which input controls which features>
```

### Composition rule

Describe:

- selected forms;
- helper calls;
- feature propagation;
- case or adposition selection;
- polarity or tense interaction;
- result-field construction.

### Linearization rule

```text
<component order and conditions>
```

### Output contract

| Result field or form | Value rule |
|---|---|
| `<FIELD>` | `<RULE>` |

### Variants

```text
<none or exact controlled variants>
```

### Unsupported or excluded scope

```text
<explicit limitations>
```

### Failure behavior

```text
<compile-time impossibility, missing function, empty variant, fallback, or blocked state>
```

### Validation

```text
direct provider compile
consumer compile
entrypoint compile
scenario ID
gold file
manual review when unavoidable
```

### Breaking changes

```text
<changes requiring coordinated migration>
```
```

---

# Part III — General constructor invariants

## 13. Determinism

Given equivalent:

```text
input values
project configuration
GF version
RGL identity
source revision
```

a constructor must produce deterministic logical output within the declared variant policy.

### 13.1 Variants

When GF `variants` are intentionally used:

- the variant set must be bounded;
- ordering must be stable where gold comparison relies on it;
- each variant must be linguistically justified;
- accidental duplicate variants must be removed;
- scenarios must test the intended alternatives.

### 13.2 Randomness

Public exact-gold behavior must not depend on random generation.

Generation scenarios must be bounded and compared according to the validation specification.

---

## 14. Argument order

The order of abstract-function arguments is public.

A concrete implementation must not reinterpret:

```text
first argument
second argument
head argument
dependent argument
```

in a way inconsistent with the abstract type and project specification.

Changing argument order requires:

```text
abstract update
all concrete providers
all consumers
scenarios
gold review
contract update
decision log
project release impact review
```

---

## 15. Head selection

Every multi-input constructor must document which input controls:

```text
number
gender
person
case
definiteness
animacy
polarity
tense
aspect
mood
voice
register
language-specific agreement dimensions
```

When no input controls a feature, document:

```text
constant value
derived value
context-supplied value
underspecified value
not applicable
```

Hidden head selection is prohibited.

---

## 16. Feature propagation

Every output feature must be:

```text
copied from a named input
calculated from named inputs
provided by a helper
set to a documented constant
left intentionally underspecified by a documented type
```

A constructor must not silently discard a feature needed by downstream consumers.

### 16.1 New mandatory field

Adding a mandatory output field requires coordinated updates to:

```text
all constructors producing the lincat
all coercions
all record extensions
all pattern matches
all consumers
scenarios
gold
lincat contract
```

### 16.2 Derivable field

A newly derivable field requires an explicit initialization policy and consumer review.

---

## 17. Linearization order

Every public constructor must define its canonical order or selection conditions.

Possible rule forms:

```text
A B
B A
A before B unless condition C
position selected by polarity
position selected by clause type
position selected by information structure
language-defined variants
```

### 17.1 No incidental order

Source-code concatenation order becomes contractual when another module, scenario or user relies on it.

### 17.2 Empty components

The rule must state how empty or optional components affect:

```text
spacing
punctuation
clitic adjacency
particle placement
capitalization
variants
```

---

## 18. String composition

Public syntax should use structured GF values and project-owned helpers.

Direct string concatenation is permitted only when the project contract proves that:

- no lost feature is required;
- spacing is correct;
- punctuation is correct;
- orthographic transformations are correct;
- no lower-level structured provider should own the operation.

### 18.1 Whitespace

Constructors must not encode accidental leading or trailing whitespace.

Whitespace behavior used by gold comparison is public output.

### 18.2 Token boundaries

The project must document any language-specific behavior involving:

```text
contractions
elision
clitic attachment
hyphenation
apostrophes
multiword tokens
orthographic fusion
```

---

## 19. Failure behavior

A constructor must not manufacture apparently valid output when a required dependency is absent.

Allowed behaviors depend on the project contract and may include:

```text
GF compile failure during incomplete development
explicit missing function
empty `variants {}` for an explicitly unavailable branch
documented fallback
blocked provider
explicit placeholder only during bootstrap
```

### 19.1 Placeholder output

Output such as:

```text
TODO
UNKNOWN
?
dummy
placeholder
```

must not enter a release grammar unless explicitly required as user-visible behavior, which is unusual and requires a decision.

### 19.2 `Predef.error`

Use of `Predef.error` or equivalent failure behavior must be documented with:

```text
trigger condition
affected constructor
consumer expectations
scenario
release treatment
```

---

## 20. Fallback behavior

Every fallback constructor must be registered in:

```text
project/docs/STATUS_LEDGER.md
```

The entry must identify:

```text
fallback trigger
current output
lost features
preferred implementation
direct consumers
scenario evidence
release impact
exit condition
```

A fallback is not stable merely because it compiles.

---

# Part IV — Phrase-level rules

## 21. Noun phrase formation

Populate the project-specific rules for applicable constructor families.

Typical questions:

```text
Which input controls agreement?
How is definiteness represented?
How is case selected?
How are determiners realized?
How are quantifiers realized?
How are pronouns distinguished?
How are proper names represented?
How are premodifiers and postmodifiers ordered?
How are appositives handled?
How is coordination agreement resolved?
```

### 21.1 Required noun-phrase inventory

| Constructor family | Applicable | Provider | Head | Agreement rule | Order rule | Evidence |
|---|---|---|---|---|---|---|
| Determiner + common noun | `<yes/no>` | `<MODULE>` | `<INPUT>` | `<RULE>` | `<ORDER>` | `<SCENARIO>` |
| Quantifier + noun | `<yes/no>` | `<MODULE>` | `<INPUT>` | `<RULE>` | `<ORDER>` | `<SCENARIO>` |
| Pronoun NP | `<yes/no>` | `<MODULE>` | `<INPUT>` | `<RULE>` | `<ORDER>` | `<SCENARIO>` |
| Proper-name NP | `<yes/no>` | `<MODULE>` | `<INPUT>` | `<RULE>` | `<ORDER>` | `<SCENARIO>` |
| Modified NP | `<yes/no>` | `<MODULE>` | `<INPUT>` | `<RULE>` | `<ORDER>` | `<SCENARIO>` |
| Coordinated NP | `<yes/no>` | `<MODULE>` | `<RULE>` | `<RULE>` | `<ORDER>` | `<SCENARIO>` |

Remove non-applicable rows after project initialization.

---

## 22. Common-noun modification

Document applicable behavior for:

```text
adjective modification
relative-clause modification
prepositional modification
genitive or possessive modification
compound modification
numeral modification
language-specific attributive constructions
```

For each, record:

```text
modifier position
agreement
case requirements
definiteness interaction
head-feature preservation
recursive behavior
scope
```

---

## 23. Adjective phrase formation

Document:

```text
positive use
comparative use
superlative use
degree modification
complement selection
attributive versus predicative realization
agreement dimensions
case forms
adverbial conversion
```

Do not assume the RGL default is correct for the project without review.

---

## 24. Adverbial modification

Document the placement and scope of:

```text
VP adverbs
sentence adverbs
degree adverbs
temporal adverbs
locative adverbs
manner adverbs
focus particles
negation particles when modeled as adverbials
```

When placement has variants, state their semantic or register distinction.

---

## 25. Preposition or adposition phrases

Document:

```text
preposition versus postposition behavior
governed case
complement category
contraction or fusion
pronoun-specific forms
stranding or pied-piping when applicable
coordination behavior
attachment ambiguity
```

The `Prep` or language-specific lincat contract owns required fields.

This document owns how constructors select and use them.

---

# Part V — Verb phrase and clause rules

## 26. Verb phrase formation

For each valency family, document:

```text
intransitive
transitive
ditransitive
sentential complement
question complement
VP complement
AP complement
NP predicate
reflexive
reciprocal
impersonal
copular
light-verb or periphrastic
language-specific valencies
```

### 26.1 Valency registry

| Valency | Constructor ID | Provider | Complement realization | Case/adposition | Agreement | Evidence |
|---|---|---|---|---|---|---|
| V | `<ID>` | `<MODULE>` | none | n/a | `<RULE>` | `<SCENARIO>` |
| V2 | `<ID>` | `<MODULE>` | `<RULE>` | `<RULE>` | `<RULE>` | `<SCENARIO>` |
| V3 | `<ID>` | `<MODULE>` | `<RULE>` | `<RULE>` | `<RULE>` | `<SCENARIO>` |
| VS | `<ID>` | `<MODULE>` | `<RULE>` | `<RULE>` | `<RULE>` | `<SCENARIO>` |
| VQ | `<ID>` | `<MODULE>` | `<RULE>` | `<RULE>` | `<RULE>` | `<SCENARIO>` |
| VV | `<ID>` | `<MODULE>` | `<RULE>` | `<RULE>` | `<RULE>` | `<SCENARIO>` |
| VA | `<ID>` | `<MODULE>` | `<RULE>` | `<RULE>` | `<RULE>` | `<SCENARIO>` |
| VN | `<ID>` | `<MODULE>` | `<RULE>` | `<RULE>` | `<RULE>` | `<SCENARIO>` |

Remove or extend rows according to the active grammar.

---

## 27. Complement selection

A complement-taking constructor must document:

```text
required complement category
case or adposition
finite versus non-finite form
complementizer
control or raising behavior
subject sharing
object sharing
polarity interaction
word order
clitic behavior
```

### 27.1 No generic complement string

A structured complement must not be reduced to arbitrary `Str` when downstream syntax needs:

```text
case
agreement
clause type
polarity
tense
subject control
extraction
```

---

## 28. Predication

Document the clause constructor linking a subject and predicate.

Required decisions:

```text
subject agreement
predicate agreement
person resolution
number resolution
gender or class resolution
subject case
null-subject behavior
expletive behavior
copula selection
word order
focus or topic effects
```

### 28.1 Agreement source

The agreement source must be explicit.

Example placeholder:

```text
The subject NP provides `<AGR_FIELD>`.
The VP selects its finite form through `<VERB_FORM_FIELD>`.
```

Replace with the real project rule.

---

## 29. Clause representation

Document the public `Cl` or equivalent result shape through a reference to the lincat contract.

This document must explain:

```text
which forms are delayed until sentence construction
which features are stored
which arguments remain unrealized
how polarity is applied
how tense/aspect/mood is applied
how clause type affects order
how punctuation is deferred
```

---

## 30. Sentence formation

Document how clauses become sentences.

Possible dimensions:

```text
tense
anteriority
aspect
mood
polarity
clause type
register
capitalization
punctuation
```

The rule must identify whether these dimensions are:

```text
stored in the clause
supplied by the sentence constructor
realized by auxiliaries
realized morphologically
realized by particles
not supported
```

---

## 31. Tense

Populate the supported tense inventory.

| Tense value | Semantic scope | Morphological or periphrastic realization | Provider | Scenario | Status |
|---|---|---|---|---|---|
| `<TENSE>` | `<SCOPE>` | `<RULE>` | `<MODULE>` | `<SCENARIO>` | `<STATUS>` |

### 31.1 Unsupported distinctions

An unsupported abstract tense distinction must be handled explicitly through:

```text
documented syncretism
documented fallback
missing implementation
experimental rule
scope limitation
```

Do not claim a distinct realization when outputs are accidentally identical.

---

## 32. Aspect and anteriority

Document applicable distinctions such as:

```text
perfective
imperfective
progressive
habitual
perfect/anterior
prospective
language-specific aspect
```

For each, state:

```text
where the feature is represented
which helper selects forms
auxiliary behavior
participle or infinitive behavior
agreement
word order
interaction with negation
interaction with questions
```

---

## 33. Mood and modality

Document applicable behavior for:

```text
indicative
subjunctive
conditional
imperative
optative
infinitival or non-finite clauses
modal auxiliaries
evidential or language-specific mood
```

A mood distinction may be:

```text
morphological
periphrastic
particle-based
construction-specific
unsupported
syncretic
```

The project must state which.

---

## 34. Polarity and negation

Document:

```text
positive form
negative marker or morphology
negative concord
placement relative to verb and auxiliaries
interaction with clitics
interaction with questions
interaction with imperatives
scope behavior
double-negation interpretation when relevant
```

### 34.1 Polarity propagation

State whether polarity is applied:

```text
inside VP
inside clause
at sentence construction
through an auxiliary helper
through a negative particle
```

### 34.2 No hidden default

A constructor must not silently force positive polarity when the public type permits negative use.

---

## 35. Voice

Document applicable behavior for:

```text
active
passive
middle
reflexive
impersonal
causative
applicative
language-specific voice
```

For each supported transformation, state:

```text
argument promotion or suppression
case changes
agreement controller
auxiliary or morphology
participle agreement
agent phrase behavior
word order
semantic restrictions
```

---

# Part VI — Clause-type rules

## 36. Declarative clauses

Document the canonical declarative order and any controlled variants.

Required scope:

```text
neutral order
subject omission
object placement
adverb placement
auxiliary placement
clitic placement
focus or topic positions
embedded declarative order
```

---

## 37. Yes/no questions

Document:

```text
question particle
inversion
intonation-only behavior
auxiliary movement
clitic placement
subject position
embedded yes/no question behavior
punctuation
```

A question constructor must not reuse declarative output without a documented reason.

---

## 38. Wh-questions

Document:

```text
wh phrase position
movement versus in-situ realization
case marking
preposition behavior
subject versus object asymmetry
embedded question behavior
agreement effects
multiple-wh policy
```

### 38.1 Extraction contract

When extraction is modeled through gaps or delayed arguments, the relevant lincat fields and helpers must be public and documented.

---

## 39. Imperatives

Document:

```text
supported persons
number distinctions
polarity
subject expression
clitic placement
object realization
prohibitive construction
punctuation
```

Unsupported imperative forms require explicit status.

---

## 40. Relative clauses

Document:

```text
relative marker or pronoun
head agreement
gap role
case marking
preposition behavior
restrictive versus non-restrictive scope
finite versus non-finite relatives
relative-clause order
attachment to common nouns or NPs
```

### 40.1 Gap representation

The project must state whether the gap is represented by:

```text
record field
parameter
missing argument
relative pronoun constructor
resumptive element
language-specific helper
```

Hidden gap conventions are prohibited.

---

## 41. Subordinate clauses

Document applicable subordinate types:

```text
complement clauses
adverbial clauses
conditional clauses
causal clauses
temporal clauses
purpose clauses
concessive clauses
comparative clauses
reported speech
```

For each type, state:

```text
subordinator
clause form
mood selection
word order
tense interaction
polarity
punctuation
```

---

## 42. Coordination

Document coordination for every supported category.

Possible categories:

```text
NP
AP
Adv
VP
Cl
S
QS
RS
CN
language-specific categories
```

### 42.1 Required coordination rules

```text
conjunction position
two-item form
multi-item form
separator or punctuation
agreement resolution
shared dependents
ellipsis
case behavior
polarity or tense compatibility
variant ordering
```

### 42.2 Agreement resolution

For coordinated controllers, define:

```text
person hierarchy
number
gender or noun-class resolution
animacy
default agreement
mixed-feature behavior
```

A generic default must be documented and tested.

---

# Part VII — Structural and function-word constructors

## 43. Determiners and quantifiers

Document applicable behavior for:

```text
articles
demonstratives
possessives
indefinites
universals
numerals
partitives
negative quantifiers
interrogative determiners
```

State:

```text
agreement
definiteness
case
position
co-occurrence restrictions
zero determiner
article fusion
```

---

## 44. Pronouns

Document constructor behavior involving:

```text
personal pronouns
reflexives
reciprocals
demonstratives
indefinites
interrogatives
relatives
possessives
clitic pronouns
strong pronouns
```

The morphology specification owns pronoun paradigms.

This document owns syntactic placement and use.

---

## 45. Auxiliaries and copulas

Document:

```text
auxiliary selection
copula selection
tense/aspect/mood contribution
agreement
participle or complement form
negation placement
question behavior
word order
omission conditions
```

If several auxiliaries are possible, state the selection rule.

---

## 46. Complementizers and subordinators

Document:

```text
constructor ownership
selected clause type
selected mood
position
optional omission
interaction with extraction
embedded question behavior
```

---

## 47. Particles and clitics

Document every public placement rule involving:

```text
object clitics
subject clitics
reflexive clitics
negative particles
question particles
focus particles
tense/aspect particles
discourse particles
```

Required detail:

```text
host
ordering among multiple clitics
placement relative to auxiliaries
phonological or orthographic attachment
duplication
blocking conditions
variants
```

A clitic cluster must not be assembled through undocumented string order.

---

# Part VIII — Coercions and shared helpers

## 48. Coercion policy

Every public coercion must identify:

```text
source category
target category
information preserved
information lost
conditions
provider
consumers
validation
```

Examples may include:

```text
A → AP
N → CN
PN → NP
Cl → S
Adv → modifier
VP → predicate
```

### 48.1 Lossy coercions

A lossy coercion requires:

```text
explicit documentation
status review
consumer review
scenario evidence
```

It must not become a general shortcut that bypasses structured syntax.

---

## 49. Helper ownership

Each shared syntax helper must have one owner.

Examples:

```text
clause builder
word-order selector
agreement resolver
negation inserter
auxiliary selector
case selector
clitic cluster builder
punctuation helper
coordination builder
```

The helper registry belongs in the project contract lock or dependency map.

### 49.1 Public versus private helper

A helper is public when another file:

```text
imports it
calls it
matches on its result
assumes its record shape
depends on its ordering or side effect
```

A public helper requires a contract.

---

## 50. Helper input validation

Document the accepted input domain.

A helper must not silently accept malformed values and produce misleading valid-looking output.

GF’s type system should enforce structure wherever possible.

---

## 51. Override policy

When an inherited helper or constructor is overridden:

```text
name the inherited provider
name the overriding provider
state why the inherited behavior is unsuitable
state whether the override is complete
identify consumers
test inherited and overridden scope where relevant
```

Copying and modifying a helper without recording the ownership change is prohibited.

---

## 52. Interface and instance policy

For projects using GF interfaces and instances, document:

```text
interface owner
required operations
instance provider
operation types
semantic expectations
default operations
unsupported operations
consumers
```

An instance must not satisfy an operation with a placeholder while being presented as complete.

---

# Part IX — Language-specific extension rules

## 53. Extension inventory

Populate the active extension inventory.

| Extension family | Provider | Public constructors | Consumers | Status | Validation |
|---|---|---|---|---|---|
| `<FAMILY>` | `<MODULE>.gf` | `<FUNCTIONS>` | `<MODULES>` | `<STATUS>` | `<SCENARIOS>` |

Examples of possible extension domains:

```text
language-specific word order
clitic doubling
evidential constructions
special case alternations
topic/focus constructions
serial verbs
light verbs
applicatives
causatives
non-canonical agreement
special relative strategies
special negation
register-specific constructions
```

Do not retain example domains that do not apply.

---

## 54. Extension boundary

An extension should add behavior without silently redefining core constructors.

When an extension changes core behavior, document:

```text
override or replacement
affected core contract
consumer migration
entrypoint selection
scenario differences
release impact
```

---

## 55. Extension coordinator

When several extension modules feed one coordinator:

- provider order must be explicit;
- duplicate constructors must be rejected or selected explicitly;
- optional families must remain distinguishable;
- disabled families must have status-ledger entries when expected by project scope.

---

# Part X — Punctuation and orthography

## 56. Punctuation ownership

State where punctuation is added.

Possible owners:

```text
sentence constructor
question constructor
imperative constructor
coordination helper
quotation constructor
entrypoint presentation layer
```

Punctuation must not be added independently by several layers unless composition is explicitly defined.

---

## 57. Capitalization

Document whether capitalization is:

```text
stored in lexical forms
applied by sentence constructors
left to external presentation
language-specific and context-sensitive
unsupported
```

Gold files must reflect the documented policy.

---

## 58. Quotations and parentheticals

When supported, document:

```text
quote marks
nesting
punctuation placement
speaker or attribution syntax
parenthetical separators
spacing
```

---

## 59. Orthographic fusion

Document constructions involving:

```text
contraction
elision
apostrophe
hyphen
clitic attachment
article-preposition fusion
compound spelling
```

State whether the rule is owned by:

```text
morphology
syntax helper
structural lexicon
orthography resource
```

Do not implement the same fusion independently in several syntax modules.

---

# Part XI — Unsupported and incomplete behavior

## 60. Scope declaration

The active project copy must state its supported syntax scope.

Recommended table:

| Domain | Supported | Partial | Unsupported | Evidence or status entry |
|---|---|---|---|---|
| Basic declaratives | `<yes/no>` | `<scope>` | `<scope>` | `<REFERENCE>` |
| Negation | `<yes/no>` | `<scope>` | `<scope>` | `<REFERENCE>` |
| Questions | `<yes/no>` | `<scope>` | `<scope>` | `<REFERENCE>` |
| Relative clauses | `<yes/no>` | `<scope>` | `<scope>` | `<REFERENCE>` |
| Coordination | `<yes/no>` | `<scope>` | `<scope>` | `<REFERENCE>` |
| Subordination | `<yes/no>` | `<scope>` | `<scope>` | `<REFERENCE>` |
| Imperatives | `<yes/no>` | `<scope>` | `<scope>` | `<REFERENCE>` |
| Passive or voice | `<yes/no>` | `<scope>` | `<scope>` | `<REFERENCE>` |
| Extensions | `<yes/no>` | `<scope>` | `<scope>` | `<REFERENCE>` |

---

## 61. Incomplete constructors

Every incomplete public constructor must have:

```text
contract status
status-ledger entry
known missing behavior
consumer impact
scenario showing current behavior or omission
release treatment
next action
```

An incomplete constructor must not be omitted from documentation merely because GF compiles around it.

---

## 62. Disabled constructors

A disabled constructor or family must identify:

```text
disablement mechanism
reason
consumers prevented from use
scenario status
gold status
release impact
re-enable condition
```

---

## 63. Experimental constructors

Experimental syntax must not be imported by stable entrypoints without explicit project policy.

If it is imported:

- the entrypoint’s status and release scope must state this;
- affected scenarios must be marked;
- incompatible change risk must be documented.

---

# Part XII — Validation

## 64. Validation strategy

Every stable constructor must have evidence proportional to its public impact.

Evidence may include:

```text
direct GF compilation
consumer compilation
checkpoint compilation
entrypoint compilation
missing-function inspection
linearization scenario
parse scenario
generation scenario
gold comparison
PGF runtime scenario
documented manual review
```

Compilation proves type consistency.

It does not prove linguistic correctness.

---

## 65. Minimum constructor evidence

For each active public constructor:

```text
[ ] provider compiles
[ ] direct consumers compile
[ ] relevant checkpoint compiles
[ ] final entrypoint compiles
[ ] one positive scenario exists
[ ] important alternatives are covered
[ ] important negative or unsupported cases are documented
[ ] gold output is reviewed when exact comparison applies
```

---

## 66. Scenario categories

Syntax validation should cover applicable categories.

### 66.1 Construction

```text
build representative abstract trees
linearize representative trees
verify agreement and order
```

### 66.2 Parsing

```text
parse representative strings
inspect intended trees
inspect ambiguity
reject or document unintended parses
```

### 66.3 Generation

```text
generate bounded forms
verify feature combinations
verify no placeholder output
```

### 66.4 Missing functions

```text
inspect incomplete concrete functions
ensure required constructors are present
```

### 66.5 Regression

```text
compare normalized output with reviewed gold
```

---

## 67. Scenario registry template

| Scenario ID | Constructor IDs | Entrypoint | Purpose | Required | Gold | Status |
|---|---|---|---|---|---|---|
| `<SCENARIO>` | `<SYN-...>` | `<ENTRYPOINT>` | `<PURPOSE>` | `<yes/no>` | `<GOLD_OR_NONE>` | `<STATUS>` |

Scenario IDs must match `project/project.toml`.

---

## 68. Test sentence selection

Test data should include:

```text
minimal examples
representative common examples
agreement contrasts
case contrasts
positive and negative polarity
relevant tense/aspect/mood contrasts
word-order contrasts
question and relative contrasts
coordination contrasts
known difficult examples
known unsupported examples
Unicode and orthographic edge cases
```

Avoid relying only on one lexical item whose morphology hides syntax behavior.

---

## 69. Gold policy

Gold files must capture reviewed normalized behavior.

A syntax change that modifies gold requires review of:

```text
constructor contract
linguistic intent
scenario input
normalization version
GF version
RGL identity
unrelated output
release impact
```

Normal validation must not modify gold.

---

## 70. Parsing ambiguity

When a constructor affects parsing, document:

```text
expected tree
accepted alternative trees
unwanted ambiguity
ambiguity count when stable and meaningful
disambiguating morphology or syntax
known ambiguity status
```

A parse merely succeeding is not always sufficient.

---

## 71. Validation matrix

Update:

```text
project/docs/TEST_COVERAGE_MATRIX.md
```

Recommended row fields:

```text
constructor ID
function
provider
consumer checkpoint
linearization scenario
parse scenario
gold
status
release relevance
```

Every release-critical constructor must map to current evidence.

---

# Part XIII — Change control

## 72. Internal compatible change

Examples:

```text
private helper refactor
performance improvement
equivalent table lookup
clearer local variable names
source formatting
```

Required:

```text
public type unchanged
public fields unchanged
order unchanged
agreement unchanged
output unchanged or intentionally equivalent
focused validation
```

---

## 73. Compatible constructor extension

Examples:

```text
new optional abstract function
new extension constructor
new supported feature combination
new controlled variant
new optional consumer
```

Required:

1. identify provider;
2. identify consumers;
3. update abstract and concrete modules;
4. update this document;
5. update the contract lock;
6. update dependency map;
7. add scenarios;
8. review gold;
9. update coverage matrix;
10. review project release impact.

---

## 74. Breaking constructor change

Breaking changes include:

```text
renaming a public function
changing function type
changing argument order
changing result category
changing required lincat fields
changing agreement controller
changing canonical word order
removing a supported variant
changing case or adposition selection
changing polarity semantics
changing entrypoint exposure
moving constructor ownership
flattening a structured value
changing scenario identity
```

Required workflow:

1. identify constructor and contract IDs;
2. record a decision;
3. enumerate providers and consumers;
4. define migration;
5. update abstract syntax;
6. update every concrete provider;
7. update shared helpers;
8. update lincat contract;
9. update dependency map;
10. update scenarios and inputs;
11. review gold explicitly;
12. update status ledger;
13. validate checkpoints and entrypoints;
14. review project release version impact;
15. update release criteria when scope changes.

An isolated file edit is prohibited.

---

## 75. Lincat migration

A lincat change affecting syntax requires:

```text
old shape
new shape
field-by-field migration
all producing constructors
all consuming constructors
all coercions
all helpers
all pattern matches
all entrypoints
scenarios
gold
decision
status ledger
```

The lincat contract remains the source of truth for the shape.

---

## 76. Helper ownership transfer

Moving a shared constructor helper requires:

```text
old provider
new provider
consumer import updates
duplicate-removal proof
dependency direction review
contract update
source compile
scenario evidence
```

Both providers must not remain active unintentionally.

---

## 77. RGL or inherited behavior change

When a GF or RGL upgrade changes inherited syntax output:

1. record tool identity;
2. identify affected inherited functions;
3. determine whether the change is compatible;
4. review overrides;
5. run affected scenarios;
6. review gold;
7. update known issues or decisions;
8. update compatibility documentation.

Do not normalize away a meaningful linguistic change.

---

# Part XIV — Documentation and status integration

## 78. Status ledger integration

Create or update a ledger entry for:

```text
temporary constructor
fallback constructor
blocked constructor
disabled syntax family
known warning
experimental public behavior
accepted release exception
```

A source `TODO` is not sufficient.

---

## 79. Decision-log integration

Record a project decision when changing:

```text
module ownership
lincat structure
head selection
agreement resolution
canonical word order
inheritance or override policy
fallback acceptance
clitic ordering
case selection
polarity strategy
tense/aspect/mood strategy
relative strategy
coordination strategy
entrypoint exposure
```

---

## 80. Known-issue integration

Use `KNOWN_ISSUES.md` for confirmed defects such as:

```text
wrong agreement
wrong order
missing negation
incorrect case
unwanted ambiguity
missing parse
incorrect linearization
crash or `Predef.error`
```

Link the issue to the affected constructor IDs.

---

## 81. Research-evidence integration

Language-specific syntax decisions should link to:

```text
grammar descriptions
corpus evidence
academic references
native-speaker review
project-approved linguistic sources
```

Distinguish:

```text
documented linguistic fact
project modeling choice
RGL compatibility choice
temporary implementation convenience
```

---

# Part XV — Template population

## 82. Required placeholders

The active-project copy must replace or remove:

```text
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<YYYY-MM-DD>
<ABSTRACT_MODULE>
<RESOURCE_MODULES>
<CATEGORY_MODULES>
<SYNTAX_MODULES>
<STRUCTURAL_MODULES>
<EXTENSION_MODULES>
<GRAMMAR_ENTRYPOINT>
<API_ENTRYPOINT_OR_NONE>
<CHECKPOINT>
<FUNCTION>
<MODULE>
<SCENARIO>
<GOLD_OR_NONE>
```

A placeholder shown only inside a clearly marked reusable template block may remain when the block is intentionally retained as an authoring aid.

Required project metadata and active registry rows must not contain unresolved placeholders.

---

## 83. Initial population workflow

1. load `project/project.toml`;
2. identify source root;
3. identify abstract and concrete entrypoints;
4. identify syntax-related checkpoints;
5. inspect module imports;
6. inventory public abstract functions;
7. inventory concrete `lin` providers;
8. inventory imported public helpers;
9. map every lincat field read by syntax;
10. identify agreement and ordering rules;
11. identify inheritance and overrides;
12. identify temporary and fallback behavior;
13. identify required scenarios;
14. create constructor IDs;
15. populate the registry;
16. update the contract lock;
17. update the coverage matrix;
18. run baseline validation;
19. record baseline evidence;
20. set the review date.

---

## 84. Initial source search

Review source patterns equivalent to:

```text
fun
lin
lincat
oper
param
table
case
variants
Predef.error
TODO
FIXME
temporary
fallback
override
inherit
with
open
```

A textual match is a review candidate, not automatically a public contract.

---

## 85. Initial review questions

For each public constructor ask:

```text
Who owns it?
What is its exact GF type?
Which input is the head?
Which features are read?
Which features are propagated?
Which case or form is selected?
What is the order?
What variants exist?
What inherited behavior is used?
What fallback exists?
Which consumers depend on it?
Which scenario proves it?
Does it block release?
```

---

# Part XVI — Anti-drift

## 86. Syntax drift indicators

Probable drift exists when:

- a constructor reads an undocumented lincat field;
- a field meaning differs between syntax modules;
- a provider changes a record field without updating constructors;
- two modules own the same constructor family;
- a helper is copied instead of shared deliberately;
- a lower-level module imports a final entrypoint;
- circular imports appear;
- an abstract function has no declared concrete provider;
- a concrete function type differs from the abstract type;
- an inherited function is overridden without documentation;
- a structured value is flattened to `Str`;
- agreement is selected from an undocumented input;
- word order changes without scenario review;
- a fallback has no status-ledger entry;
- placeholder output reaches a stable entrypoint;
- `variants` introduces unbounded or accidental alternatives;
- a required scenario omits a changed constructor;
- a gold change lacks constructor and decision review;
- a constructor is documented as stable but remains missing;
- an extension silently replaces core behavior;
- a clitic order is encoded in several modules;
- punctuation is added by several layers inconsistently;
- the dependency map names a provider that no longer exists;
- an old language suffix remains in the active project;
- this document defines a lincat shape conflicting with the lincat contract;
- release claims exceed the supported-syntax table.

Every detected drift must be resolved by restoring the current contract or changing it deliberately through the coordinated workflow.

---

## 87. Contract consistency checks

Project checks should verify:

```text
constructor IDs unique
public function names exist
providers exist
consumers exist
abstract types match concrete providers
required lincat fields exist
documented helpers exist
entrypoints expose intended modules
scenario IDs exist
gold mappings exist
status-ledger references resolve
decision references resolve
no required placeholder remains
```

---

# Part XVII — Checklists

## 88. New constructor checklist

```text
[ ] constructor ID assigned
[ ] abstract function declared
[ ] GF type documented
[ ] concrete provider selected
[ ] direct consumers listed
[ ] head identified
[ ] required fields documented
[ ] feature propagation documented
[ ] order documented
[ ] variants documented
[ ] unsupported scope documented
[ ] failure behavior documented
[ ] contract lock updated
[ ] dependency map updated
[ ] lincat contract reviewed
[ ] morphology spec reviewed
[ ] scenario added
[ ] gold reviewed
[ ] coverage matrix updated
[ ] status ledger updated when non-stable
[ ] decision recorded when significant
```

---

## 89. Constructor modification checklist

```text
[ ] constructor and contract IDs identified
[ ] compatibility classified
[ ] provider reviewed
[ ] all direct consumers reviewed
[ ] downstream entrypoints reviewed
[ ] argument type and order reviewed
[ ] head and agreement reviewed
[ ] lincat fields reviewed
[ ] case/adposition selection reviewed
[ ] word order reviewed
[ ] polarity reviewed
[ ] tense/aspect/mood reviewed
[ ] variants reviewed
[ ] helpers reviewed
[ ] scenarios reviewed
[ ] gold reviewed
[ ] documentation updated
[ ] status and decisions updated
[ ] checkpoints pass
```

---

## 90. New syntax-module checklist

```text
[ ] module responsibility unique
[ ] architecture layer identified
[ ] imports follow dependency direction
[ ] public exports listed
[ ] providers and consumers registered
[ ] no duplicate helper ownership
[ ] lincat dependencies documented
[ ] constructor registry updated
[ ] checkpoint selected
[ ] entrypoint exposure explicit
[ ] scenarios added
[ ] contract lock updated
```

---

## 91. Fallback review checklist

```text
[ ] fallback trigger explicit
[ ] lost information explicit
[ ] preferred behavior explicit
[ ] provider and consumers listed
[ ] output distinguishable
[ ] scenario exists
[ ] release impact stated
[ ] status-ledger entry exists
[ ] exit condition objective
```

---

## 92. Release review checklist

```text
[ ] constructor registry complete
[ ] no unresolved required placeholders
[ ] all active providers exist
[ ] all active abstract functions implemented
[ ] required missing-function check passes
[ ] all release checkpoints compile
[ ] final entrypoints compile
[ ] agreement scenarios pass
[ ] word-order scenarios pass
[ ] polarity scenarios pass
[ ] tense/aspect/mood scenarios pass where in scope
[ ] question scenarios pass where in scope
[ ] relative scenarios pass where in scope
[ ] coordination scenarios pass where in scope
[ ] required gold comparisons pass
[ ] fallbacks reviewed
[ ] disabled required constructors reviewed
[ ] known issues reviewed
[ ] accepted exceptions explicit
[ ] release criteria agree with documented syntax scope
```

---

# Part XVIII — Active project sections to complete

## 93. Project identity

| Field | Value |
|---|---|
| Project ID | `<PROJECT_ID>` |
| Language | `<LANGUAGE_NAME>` |
| Language code | `<LANGUAGE_CODE>` |
| GF suffix | `<GF_SUFFIX>` |
| Source root | `<SOURCE_ROOT>` |
| Abstract entrypoint | `<ABSTRACT_ENTRYPOINT>` |
| Concrete entrypoint | `<CONCRETE_ENTRYPOINT>` |
| Grammar entrypoint | `<GRAMMAR_ENTRYPOINT>` |
| API entrypoint | `<API_ENTRYPOINT_OR_NONE>` |

---

## 94. Active constructor registry

Replace the placeholder row.

| Constructor ID | Function or family | Provider | GF type | Head | Required fields | Status | Validation |
|---|---|---|---|---|---|---|---|
| `<SYN-ID>` | `<FUNCTION_OR_FAMILY>` | `<MODULE>.gf` | `<GF_TYPE>` | `<HEAD>` | `<FIELDS>` | `<STATUS>` | `<SCENARIO/GOLD>` |

---

## 95. Active ordering rules

| Construction | Neutral order | Conditional alternatives | Provider | Evidence |
|---|---|---|---|---|
| Basic clause | `<ORDER>` | `<CONDITIONS>` | `<MODULE>` | `<SCENARIO>` |
| Noun phrase | `<ORDER>` | `<CONDITIONS>` | `<MODULE>` | `<SCENARIO>` |
| Adjective modification | `<ORDER>` | `<CONDITIONS>` | `<MODULE>` | `<SCENARIO>` |
| Negation | `<ORDER>` | `<CONDITIONS>` | `<MODULE>` | `<SCENARIO>` |
| Yes/no question | `<ORDER>` | `<CONDITIONS>` | `<MODULE>` | `<SCENARIO>` |
| Wh-question | `<ORDER>` | `<CONDITIONS>` | `<MODULE>` | `<SCENARIO>` |
| Relative clause | `<ORDER>` | `<CONDITIONS>` | `<MODULE>` | `<SCENARIO>` |
| Coordination | `<ORDER>` | `<CONDITIONS>` | `<MODULE>` | `<SCENARIO>` |

Remove non-applicable rows.

---

## 96. Active agreement rules

| Controller | Target | Features | Resolution rule | Provider | Evidence |
|---|---|---|---|---|---|
| `<CONTROLLER>` | `<TARGET>` | `<FEATURES>` | `<RULE>` | `<MODULE>` | `<SCENARIO>` |

---

## 97. Active polarity and TAM rules

| Dimension | Values supported | Realization | Provider | Limitations | Evidence |
|---|---|---|---|---|---|
| Polarity | `<VALUES>` | `<RULE>` | `<MODULE>` | `<LIMITS>` | `<SCENARIO>` |
| Tense | `<VALUES>` | `<RULE>` | `<MODULE>` | `<LIMITS>` | `<SCENARIO>` |
| Aspect/anteriority | `<VALUES>` | `<RULE>` | `<MODULE>` | `<LIMITS>` | `<SCENARIO>` |
| Mood | `<VALUES>` | `<RULE>` | `<MODULE>` | `<LIMITS>` | `<SCENARIO>` |
| Voice | `<VALUES>` | `<RULE>` | `<MODULE>` | `<LIMITS>` | `<SCENARIO>` |

---

## 98. Active fallback and experimental inventory

| Constructor ID | State | Current behavior | Lost capability | Ledger entry | Exit condition |
|---|---|---|---|---|---|
| — | — | No project-specific inventory has been populated in this template | — | — | Complete initialization review |

The row above is administrative and not a stability claim.

---

## 99. Active validation mapping

| Constructor ID or family | Compile checkpoint | Linearize scenario | Parse scenario | Gold | Release critical |
|---|---|---|---|---|---|
| `<SYN-ID>` | `<CHECKPOINT>` | `<SCENARIO_OR_NONE>` | `<SCENARIO_OR_NONE>` | `<GOLD_OR_NONE>` | `<yes/no>` |

---

## 100. Review record

| Review date | Reviewer | Source revision | GF version | RGL identity | Result |
|---|---|---|---|---|---|
| `<YYYY-MM-DD>` | `<REVIEWER>` | `<REVISION>` | `<GF_VERSION>` | `<RGL_IDENTITY>` | `<RESULT>` |

---

# Part XIX — Final enforcement rule

Syntax is a network of public types, providers, consumers and evidence.

Therefore:

> No public constructor may change through an isolated `lin` edit. Its abstract type, authoritative provider, lincat dependencies, agreement and ordering rules, helpers, direct consumers, downstream entrypoints, scenarios, gold expectations, status and project contracts must remain coordinated and reviewable as one complete project change.
