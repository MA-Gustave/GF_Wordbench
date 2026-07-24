# GF Wordbench Project Template — Category and Lincat Contract

**Document ID:** `GF-WB-TEMPLATE-CATEGORY-LINCAT-CONTRACT`  
**Document role:** Normative project template  
**Decision status:** Accepted template contract  
**Implementation status:** Template available; active-project implementation depends on initialization  
**Verification status:** Requires placeholder, source, contract and validation checks after initialization  
**Applies to:** One initialized active GF project  
**Template owner:** GF Wordbench maintainers  
**Project owner:** `<PROJECT_OWNER>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**GF module suffix:** `<GF_SUFFIX>`  
**Source root:** `<SOURCE_ROOT>`  
**Project configuration:** `project/project.toml`  
**Project contract lock:** `project/docs/INTERFILE_CONTRACT_LOCK.md`  
**Validation specification:** `project/docs/VALIDATION_SPEC.md`  
**Target template path:** `templates/project/docs/CATEGORY_AND_LINCAT_CONTRACT.md`  
**Contract version:** `1.0.0`  
**Last reviewed:** `<YYYY-MM-DD OR PROJECT RELEASE>`

---

## 1. Template use

This file is a template.

When initializing an active GF project:

1. copy it to:

   ```text
   project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
   ```

2. replace every required placeholder;
3. remove non-applicable example categories and sections;
4. add every public or cross-module category contract used by the project;
5. verify every provider and consumer against actual GF source;
6. link every contract to validation evidence;
7. record temporary or incomplete structures in `STATUS_LEDGER.md`;
8. run project contract checks;
9. remove this initialization section from the active-project document when no longer useful.

The initialized active-project document must not retain unresolved required placeholders.

Placeholders are valid in this template only.

---

## 2. Purpose

This document defines the public category, `lincat`, record, table, parameter, agreement, lock, helper, and initialization contracts of one active GF project.

It prevents drift between:

```text
abstract categories
concrete lincats
resource records
morphology providers
category implementations
syntax modules
structural modules
extension modules
entrypoints
native .gfs scenarios
gold expectations
project documentation
```

A GF module may compile internally while still violating a project contract.

The project remains coherent only when providers and consumers agree about:

- category identity;
- exact GF type;
- record fields;
- table indices;
- parameter values;
- agreement dimensions;
- ordering assumptions;
- initialization policy;
- empty or missing value semantics;
- helper ownership;
- inheritance and override policy;
- accepted coercions;
- validation evidence.

---

## 3. Core anti-drift rule

> A consumer may depend only on a category or lincat property explicitly guaranteed by its authoritative provider and documented here.

A provider change is complete only when all affected elements are updated together:

```text
provider module
direct consumers
downstream entrypoints
interfaces and instances
constructors
helpers
project configuration when affected
scenarios
inputs
gold
architecture documentation
dependency map
validation specification
status ledger
decision log when required
interfile contract lock
validation evidence
```

An isolated field, parameter, or lincat change is prohibited when another file depends on it.

---

## 4. Authority and document boundaries

### 4.1 This document owns

This document owns project-level declarations for:

```text
category purpose
authoritative lincat provider
exact lincat shape
public record fields
public table indices
public parameter values
agreement dimensions
lock fields
field initialization policy
field semantic invariants
consumer assumptions
allowed coercions
stable helper relationships
validation evidence
```

### 4.2 Other documents own

| Topic | Authority |
|---|---|
| Project identity and inventory | `project/project.toml` |
| Module layers and responsibilities | `project/docs/LANGUAGE_ARCHITECTURE.md` |
| Direct import relationships | `project/docs/MODULE_DEPENDENCY_MAP.md` |
| Morphological paradigms | `project/docs/MORPHOLOGY_SPEC.md` |
| Constructor behavior and syntax rules | `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| Validation requirements | `project/docs/VALIDATION_SPEC.md` |
| Temporary or incomplete structures | `project/docs/STATUS_LEDGER.md` |
| Significant project decisions | `project/docs/DECISION_LOG.md` |
| Cross-file contract registry | `project/docs/INTERFILE_CONTRACT_LOCK.md` |
| Release acceptance | `project/docs/RELEASE_CRITERIA.md` |

This document may summarize those topics only where needed to define a category boundary.

---

## 5. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **CATEGORY**: abstract GF category or project-defined category-like public contract.
- **Lincat**: concrete linearization type assigned to a category.
- **PROVIDER**: module that defines or authoritatively supplies a category shape, field, parameter, helper, or behavior.
- **CONSUMER**: module that imports, constructs, reads, pattern-matches, modifies, linearizes, or otherwise depends on the provider.
- **PUBLIC FIELD**: record field read or written by a module other than its provider.
- **PRIVATE FIELD**: provider-local field or detail with no external consumer.
- **TABLE INDEX**: parameter or type indexing a GF table.
- **PARAMETER**: GF `param` type or equivalent finite grammatical dimension.
- **AGREEMENT DIMENSION**: grammatical information whose value must remain coherent across category or module boundaries.
- **LOCK FIELD**: field preserving constraints or deferred choices needed by downstream consumers.
- **INITIALIZATION POLICY**: rule defining how every field obtains a valid value.
- **TOTAL CONTRACT**: every allowed index or case has defined behavior.
- **PARTIAL OR INCOMPLETE CONTRACT**: behavior intentionally absent or blocked and explicitly registered.
- **FLATTENING**: replacing a structured category or record with `Str` or another less informative shape.
- **COERCION**: documented conversion from one category or representation to another.
- **INVARIANT**: property that must remain true for every conforming value.
- **BREAKING CHANGE**: change requiring consumers, scenarios, golds, or documentation to adapt.
- **EVIDENCE**: compile, scenario, gold, artifact, or documented manual proof.

---

# 6. Project identity

Fill from `project/project.toml`.

| Field | Value |
|---|---|
| Project ID | `<PROJECT_ID>` |
| Language name | `<LANGUAGE_NAME>` |
| Language code | `<LANGUAGE_CODE>` |
| GF suffix | `<GF_SUFFIX>` |
| Source root | `<SOURCE_ROOT>` |
| Abstract entrypoint | `<ABSTRACT_ENTRYPOINT>` |
| Main concrete entrypoint | `<CONCRETE_ENTRYPOINT>` |
| Syntax entrypoint | `<SYNTAX_ENTRYPOINT OR NOT-APPLICABLE>` |
| Language/API entrypoint | `<LANGUAGE_OR_API_ENTRYPOINT OR NOT-APPLICABLE>` |
| Release PGF | `<EXPECTED_PGF OR NOT-APPLICABLE>` |
| Architecture document | `project/docs/LANGUAGE_ARCHITECTURE.md` |
| Morphology specification | `project/docs/MORPHOLOGY_SPEC.md` |
| Syntax specification | `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md` |

These values must agree with source and configuration.

---

# 7. Contract status model

Each category contract has a lifecycle status:

```text
Active
Deprecated
Retired
```

Implementation readiness is tracked separately in `STATUS_LEDGER.md`.

Examples of implementation states:

```text
stable
experimental
temporary
fallback
warning
blocked
disabled
```

Do not use an implementation state as a contract lifecycle status.

An `Active` contract with temporary implementation must link to a ledger entry.

A `Retired` contract identifier must not be reused.

---

# 8. Contract identifiers

Each stable category or cross-module lincat relationship must have a unique identifier.

Format:

```text
CAT-<DOMAIN>-<NUMBER>
```

Recommended domains:

```text
CORE
NOUN
ADJ
VERB
ADV
PREP
PRON
DET
CLAUSE
SENTENCE
QUESTION
RELATIVE
COORD
STRUCT
EXTEND
API
```

Examples:

```text
CAT-NOUN-001
CAT-VERB-003
CAT-CLAUSE-002
```

Related interfile contracts should reference corresponding IDs such as:

```text
PIFC-LINCAT-001
PIFC-LINCAT-002
PIFC-HELPER-001
```

Identifiers remain stable across wording corrections.

---

# 9. Global category invariants

The following invariants apply unless a project-specific contract explicitly and deliberately overrides them.

## 9.1 One authoritative provider

Every public lincat shape must have one authoritative provider.

Several modules may construct or transform the category.

They must not redefine incompatible shapes.

## 9.2 No hidden field dependency

A consumer must not read, write, or pattern-match a field absent from this document.

## 9.3 No silent flattening

A structured category must not be replaced by:

```gf
Str
```

solely to make one local implementation compile.

A flattening decision is breaking when consumers lose information or behavior.

It requires:

```text
decision record
provider and consumer migration
scenario review
gold review
release impact review
```

## 9.4 Complete initialization

Every record constructor must initialize every required field.

No consumer may rely on:

- undefined values;
- accidental empty strings;
- arbitrary default agreement;
- uninitialized lock fields;
- inherited values whose source is undocumented.

## 9.5 Stable field meaning

A public field name has one meaning.

The same field name must not mean different things in different providers unless the distinction is explicit and nonconflicting.

## 9.6 Stable parameter meaning

A public parameter value must retain its documented meaning.

Renaming, adding, removing, or reinterpreting a value requires consumer review.

## 9.7 Import direction

Lower-level morphology and resource providers must not import higher-level grammar or API entrypoints to obtain convenience values.

## 9.8 Totality or explicit incompleteness

A table or constructor must be total over its declared domain, or its incomplete behavior must be explicit, validated, and registered.

## 9.9 Determinism

Given identical source, inputs, GF version, RGL revision, and configuration, lincat-dependent validation should be deterministic.

## 9.10 Evidence

Every active cross-module category contract must have at least one current proof.

---

# 10. Category inventory

Replace this table with the active project inventory.

Delete rows for categories the project does not expose.

Add language-specific categories where required.

| Contract ID | Category | Abstract provider | Lincat provider | Main consumers | Status | Evidence |
|---|---|---|---|---|---|---|
| `<CAT-ID>` | `N` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `CN` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `NP` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `Pron` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `Det` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `Quant` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `Num` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `Ord` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `A` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `AP` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `Adv` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `AdV` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `AdA` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `V` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `V2` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `V3` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `VA` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `VV` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `VS` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `VQ` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `VP` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `VPSlash` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `Prep` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `Cl` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `ClSlash` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `S` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `QS` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `RS` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `Utt` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<CAT-ID>` | `<LANGUAGE-SPECIFIC-CATEGORY>` | `<PATH>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |

This table is an index.

Each important structured category requires a detailed entry later in this document.

---

# 11. Category-family overview

Replace the following with project-specific summaries.

## 11.1 Nominal family

Categories:

```text
<LIST NOMINAL CATEGORIES>
```

Primary responsibilities:

```text
number
gender or noun class
case
definiteness
person where applicable
agreement
determiner composition
pronoun behavior
```

Authoritative provider modules:

```text
<PATHS>
```

## 11.2 Adjectival family

Categories:

```text
<LIST ADJECTIVAL CATEGORIES>
```

Primary responsibilities:

```text
agreement
degree
position
predicative or attributive behavior
complement structure
```

Authoritative provider modules:

```text
<PATHS>
```

## 11.3 Verbal family

Categories:

```text
<LIST VERBAL CATEGORIES>
```

Primary responsibilities:

```text
tense
aspect
mood
voice
person
number
polarity
valency
complement structure
nonfinite forms
```

Authoritative provider modules:

```text
<PATHS>
```

## 11.4 Clause and sentence family

Categories:

```text
<LIST CLAUSE AND SENTENCE CATEGORIES>
```

Primary responsibilities:

```text
subject-predicate composition
tense and anteriority
polarity
word order
question formation
subordination
relative formation
utterance rendering
```

Authoritative provider modules:

```text
<PATHS>
```

## 11.5 Structural and function-word family

Categories:

```text
<LIST STRUCTURAL CATEGORIES>
```

Primary responsibilities:

```text
prepositions
conjunctions
subjunctions
determiners
quantifiers
pronouns
particles
fixed functional expressions
```

Authoritative provider modules:

```text
<PATHS>
```

---

# 12. Parameter inventory

Record every public GF `param` type whose values cross module boundaries.

| Parameter contract | Parameter | Provider | Values | Semantic dimension | Consumers | Status |
|---|---|---|---|---|---|---|
| `<PARAM-ID>` | `<PARAM>` | `<PATH>` | `<VALUES>` | `<MEANING>` | `<PATHS>` | `<STATUS>` |

Examples of dimensions to consider:

```text
number
gender
noun class
case
person
animacy
definiteness
polarity
tense
aspect
mood
voice
degree
formality
clitic status
word-order state
question type
relative type
agreement state
```

Delete non-applicable dimensions.

Add project-specific dimensions explicitly.

---

# 13. Parameter contract rules

## 13.1 Exhaustive values

List every value in source order or another documented canonical order.

## 13.2 Stable meaning

A value must not be repurposed.

## 13.3 Pattern completeness

Every consumer pattern match must be complete or intentionally use a documented compatible default.

## 13.4 Table completeness

Every public table indexed by a parameter must define every required combination.

## 13.5 Addition of values

Adding a value requires review of:

```text
every table indexed by the parameter
every pattern consumer
every constructor
every helper
every entrypoint
generation scenarios
gold output
```

## 13.6 Removal or merge

Removing or merging parameter values is breaking unless no active consumer can observe the difference.

---

# 14. Agreement-dimension registry

Record how agreement information travels through the grammar.

| Agreement ID | Dimension | Provider category/field | Propagated through | Read by | Default policy | Evidence |
|---|---|---|---|---|---|---|
| `<AGR-ID>` | `<DIMENSION>` | `<CATEGORY.FIELD>` | `<CATEGORIES>` | `<CONSUMERS>` | `<POLICY>` | `<EVIDENCE>` |

Agreement values must not be reconstructed independently in multiple consumers when a shared provider already owns them.

---

# 15. Lock-field registry

Lock fields preserve constraints, deferred choices, or compatibility information.

| Lock ID | Category | Field | Type | Meaning | Set by | Read by | Release status |
|---|---|---|---|---|---|---|---|
| `<LOCK-ID>` | `<CATEGORY>` | `<FIELD>` | `<TYPE>` | `<MEANING>` | `<PROVIDERS>` | `<CONSUMERS>` | `<STATUS>` |

For every lock field, document:

- why the information cannot be represented directly in the surface string;
- when it is initialized;
- whether consumers may change it;
- whether it survives coercion;
- how scenarios exercise it.

A lock field with no consumer should be removed or justified.

---

# 16. Public-field registry

Every public record field must appear here or in a detailed category entry.

| Field ID | Category | Field | GF type | Provider | Consumers | Meaning | Required |
|---|---|---|---|---|---|---|---:|
| `<FIELD-ID>` | `<CATEGORY>` | `<FIELD>` | `<TYPE>` | `<PATH>` | `<PATHS>` | `<MEANING>` | `<YES/NO>` |

A field becomes public when any external module depends on it, even if source does not explicitly label it public.

---

# 17. Field naming policy

Document project conventions.

Recommended rules:

```text
field names are stable once consumed
one field name has one semantic meaning
string-bearing fields are distinguishable from grammatical metadata
lock fields are identifiable
table fields use names indicating their index domain
boolean-like states use project-owned parameters when more than two semantic states exist
```

Project-specific naming conventions:

```text
<FIELD NAMING RULES>
```

---

# 18. Exact type policy

Every detailed category entry must show the exact GF type as implemented.

Example template:

```gf
lincat <CATEGORY> = {
  <FIELD_1> : <TYPE_1> ;
  <FIELD_2> : <TYPE_2> ;
  <FIELD_3> : <TYPE_3>
} ;
```

For aliases:

```gf
lincat <CATEGORY> = <OTHER_TYPE> ;
```

For tables:

```gf
lincat <CATEGORY> = <INDEX_1> => <INDEX_2> => Str ;
```

Documentation must not simplify a structured type to prose that hides fields or indices.

---

# 19. Record-field contract template

Use this table for every structured lincat.

| Field | GF type | Cardinality/index | Meaning | Initialization | Consumers | Invariant |
|---|---|---|---|---|---|---|
| `<FIELD>` | `<TYPE>` | `<INDEX OR ONE>` | `<SEMANTICS>` | `<POLICY>` | `<PATHS>` | `<INVARIANT>` |

Record separately:

```text
field order significance: <YES/NO AND WHY>
private fields: <LIST>
derived fields: <LIST>
lock fields: <LIST>
empty-value policy: <POLICY>
```

---

# 20. Table contract template

For a table-valued field or lincat:

```gf
<INDEX_1> => <INDEX_2> => <VALUE_TYPE>
```

Document:

| Property | Contract |
|---|---|
| First index | `<PARAMETER AND MEANING>` |
| Second index | `<PARAMETER AND MEANING OR NOT-APPLICABLE>` |
| Value type | `<GF TYPE>` |
| Totality | `<TOTAL OR DOCUMENTED EXCEPTION>` |
| Default selection | `<NONE OR POLICY>` |
| Ordering | `<CANONICAL INDEX ORDER>` |
| Missing-form policy | `<POLICY>` |
| Consumers | `<PATHS>` |
| Evidence | `<SCENARIOS OR COMPILE TARGETS>` |

A missing table case must not silently become an unrelated grammatical form.

---

# 21. Empty-string and missing-value policy

The project must distinguish:

```text
valid empty surface realization
missing implementation
optional component absent
unknown grammatical information
blocked or temporary implementation
```

Do not use empty `Str` as a universal substitute for all five states.

Document category-specific policy:

| Category/field | Empty string allowed | Meaning | Missing represented by | Validation |
|---|---:|---|---|---|
| `<CATEGORY.FIELD>` | `<YES/NO>` | `<MEANING>` | `<REPRESENTATION>` | `<EVIDENCE>` |

A valid zero realization must have scenarios proving it does not hide missing behavior.

---

# 22. Optional-value policy

GF records do not gain an implicit optional type merely because a field may be unused.

For every conditionally used field, document:

- presence representation;
- absence representation;
- invariant connecting the field to its controlling parameter;
- constructors that initialize it;
- consumers allowed to read it;
- invalid state combinations.

Template:

```text
When <CONTROL CONDITION>:
    <FIELD> means <MEANING>

Otherwise:
    <FIELD> must contain <REPRESENTATION>
    consumers must <BEHAVIOR>
```

---

# 23. Initialization policy

Every constructor must produce valid values for all public fields.

Record initialization sources:

```text
literal
morphology table
agreement provider
copied field
derived helper
parameter default
documented empty realization
documented fallback linked to ledger
```

Prohibited:

```text
arbitrary placeholder
unexplained constant agreement
field omitted because current consumer ignores it
copy from unrelated category
temporary value presented as stable
```

---

# 24. Default-value registry

| Default ID | Category/field | Default value | Applies when | Justification | Consumers | Ledger link |
|---|---|---|---|---|---|---|
| `<DEFAULT-ID>` | `<CATEGORY.FIELD>` | `<VALUE>` | `<CONDITION>` | `<REASON>` | `<PATHS>` | `<ID OR NONE>` |

A default is part of the contract when consumers can observe it.

---

# 25. Derived-field registry

A derived field must have one documented derivation rule.

| Derived ID | Category/field | Inputs | Derivation owner | Formula or rule | Consumers | Evidence |
|---|---|---|---|---|---|---|
| `<DERIVED-ID>` | `<CATEGORY.FIELD>` | `<FIELDS>` | `<PATH>` | `<RULE>` | `<PATHS>` | `<EVIDENCE>` |

Consumers should not independently rederive the same information unless the duplication is deliberate and tested.

---

# 26. Coercion registry

Record every project-owned coercion between categories or representations.

| Coercion ID | From | To | Provider | Information preserved | Information lost | Consumers | Status |
|---|---|---|---|---|---|---|---|
| `<COERCION-ID>` | `<SOURCE>` | `<TARGET>` | `<PATH>` | `<FIELDS>` | `<FIELDS OR NONE>` | `<PATHS>` | `<STATUS>` |

A coercion that loses externally required information is breaking or invalid.

---

# 27. Flattening review

For every category represented as `Str`, record why no richer public structure is required.

| Category | Current lincat | Consumers | Richer information needed? | Decision |
|---|---|---|---:|---|
| `<CATEGORY>` | `Str` | `<PATHS>` | `<YES/NO>` | `<RATIONALE OR DECISION ID>` |

A `Str` lincat is not inherently incorrect.

It is incorrect when consumers need grammatical information that the flattening discards.

---

# 28. Inheritance and override policy

Record concrete inheritance, subtraction, and override behavior affecting category contracts.

| Override ID | Module | Inherits from | Excludes or overrides | Reason | Affected categories | Validation |
|---|---|---|---|---|---|---|
| `<OVERRIDE-ID>` | `<PATH>` | `<MODULE>` | `<SYMBOLS>` | `<RATIONALE>` | `<CATEGORIES>` | `<EVIDENCE>` |

Rules:

- inherited structure must be understood;
- local redefinition must be explicit;
- duplicate ownership is prohibited;
- subtraction lists must remain synchronized with providers;
- changing an inherited lincat requires consumer review.

---

# 29. Interface and instance contracts

When the project uses GF interfaces and instances, record category-related obligations.

| Interface ID | Interface | Instance | Required symbols/types | Defaults allowed | Evidence |
|---|---|---|---|---|---|
| `<INTERFACE-ID>` | `<PATH>` | `<PATH>` | `<SYMBOLS>` | `<POLICY>` | `<COMPILE/SCENARIO>` |

Adding a required interface symbol requires:

- every instance to implement it;
- or a compatible documented default.

Removing a symbol requires every consumer and instance to migrate.

---

# 30. Helper ownership

Public helpers used to construct, transform, or inspect category values require one owner.

| Helper ID | Helper | GF type | Provider | Consumers | Categories affected | Status |
|---|---|---|---|---|---|---|
| `<HELPER-ID>` | `<OPER>` | `<GF TYPE>` | `<PATH>` | `<PATHS>` | `<CATEGORIES>` | `<STATUS>` |

For every helper, document:

- input assumptions;
- output guarantee;
- fields preserved;
- fields changed;
- table totality;
- side effects or none;
- failure behavior;
- validation.

---

# 31. Helper contract template

## `<HELPER-ID>` — `<HELPER-NAME>`

**Status:** `<ACTIVE | DEPRECATED | RETIRED>`

**Provider**

```text
<PATH>
```

**Consumers**

```text
<PATHS>
```

**GF type**

```gf
<OPER> : <GF TYPE> ;
```

**Request**

```text
<INPUT ASSUMPTIONS>
```

**Response**

```text
<GUARANTEES>
```

**Fields preserved**

```text
<FIELDS>
```

**Fields changed**

```text
<FIELDS>
```

**Forbidden behavior**

```text
<PROHIBITIONS>
```

**Validation**

```text
<COMPILE TARGETS, SCENARIOS, GOLD>
```

---

# 32. Category construction ownership

For every major category, identify modules that construct values.

| Category | Authoritative shape provider | Construction providers | Transformation providers | Read-only consumers |
|---|---|---|---|---|
| `<CATEGORY>` | `<PATH>` | `<PATHS>` | `<PATHS>` | `<PATHS>` |

A constructor provider may create values.

It does not own the public shape unless designated as authoritative.

---

# 33. Consumer-access registry

Record consumers that access fields directly.

| Access ID | Consumer | Category | Fields read | Fields written | Purpose | Evidence |
|---|---|---|---|---|---|---|
| `<ACCESS-ID>` | `<PATH>` | `<CATEGORY>` | `<FIELDS>` | `<FIELDS OR NONE>` | `<PURPOSE>` | `<EVIDENCE>` |

Direct field access is contractual.

A change in provider shape must review every row.

---

# 34. Read-only versus mutable transformation

GF values are functional, but modules may construct modified records.

Document whether a consumer:

```text
reads fields only
copies and preserves all fields
copies and changes listed fields
rebuilds the record from a helper
coerces to another category
```

A record update must not accidentally drop fields introduced later.

Prefer provider-owned helpers for recurring updates when this reduces drift.

---

# 35. Ordering contracts

Category behavior may depend on ordering.

Document:

```text
word order
prefix and suffix order
clitic order
determiner-noun order
adjective position
subject-verb-object order
auxiliary order
negation placement
complement order
coordination order
record-to-string assembly order
```

Template:

| Ordering ID | Category or helper | Input components | Required order | Conditions | Evidence |
|---|---|---|---|---|---|
| `<ORDER-ID>` | `<SUBJECT>` | `<COMPONENTS>` | `<ORDER>` | `<CONDITIONS>` | `<SCENARIO/GOLD>` |

Ordering behavior belongs in the syntax specification as well when it is linguistic policy.

---

# 36. Orthography and spacing fields

If lincats store spacing, tokenization, elision, capitalization, or orthographic locks, document them.

| Orthography ID | Category/field | Meaning | Provider | Consumers | Normalization restrictions | Evidence |
|---|---|---|---|---|---|---|
| `<ORTH-ID>` | `<CATEGORY.FIELD>` | `<MEANING>` | `<PATH>` | `<PATHS>` | `<RULES>` | `<SCENARIO>` |

Gold normalization must not erase meaningful orthographic distinctions.

---

# 37. Polarity and negation fields

When polarity is represented in a category or lock:

```text
<DESCRIBE POLARITY REPRESENTATION>
```

Document:

- parameter owner;
- fields carrying negation;
- constructors setting polarity;
- consumers realizing it;
- interaction with tense, mood, or word order;
- positive and negative scenarios.

---

# 38. Tense, aspect, mood, and voice fields

When applicable, document:

| Dimension | Parameter/provider | Categories carrying it | Realization owner | Default | Evidence |
|---|---|---|---|---|---|
| Tense | `<VALUE>` | `<CATEGORIES>` | `<PATH>` | `<DEFAULT>` | `<EVIDENCE>` |
| Aspect | `<VALUE>` | `<CATEGORIES>` | `<PATH>` | `<DEFAULT>` | `<EVIDENCE>` |
| Mood | `<VALUE>` | `<CATEGORIES>` | `<PATH>` | `<DEFAULT>` | `<EVIDENCE>` |
| Voice | `<VALUE>` | `<CATEGORIES>` | `<PATH>` | `<DEFAULT>` | `<EVIDENCE>` |

Delete non-applicable rows.

---

# 39. Case and preposition fields

When case or complement selection crosses modules, document:

```text
case parameter
governing provider
preposition representation
selected complement category
case-assignment helper
default or no-case behavior
```

Template:

| Contract ID | Provider | Governing field | Complement category | Consumers | Evidence |
|---|---|---|---|---|---|
| `<CASE-ID>` | `<PATH>` | `<FIELD>` | `<CATEGORY>` | `<PATHS>` | `<EVIDENCE>` |

Consumers must not independently guess a preposition’s required case when the `Prep` provider owns it.

---

# 40. Person, number, gender, and class fields

Document which categories carry person, number, gender, or noun class.

| Dimension | Source category/field | Propagation path | Agreement consumers | Unknown/default policy | Evidence |
|---|---|---|---|---|---|
| Person | `<VALUE>` | `<PATH>` | `<CONSUMERS>` | `<POLICY>` | `<EVIDENCE>` |
| Number | `<VALUE>` | `<PATH>` | `<CONSUMERS>` | `<POLICY>` | `<EVIDENCE>` |
| Gender/class | `<VALUE>` | `<PATH>` | `<CONSUMERS>` | `<POLICY>` | `<EVIDENCE>` |

Do not add dimensions irrelevant to the language.

---

# 41. Definiteness and quantification fields

When represented, document:

```text
definiteness parameter
quantifier behavior
determiner agreement
article realization
zero-determiner behavior
mass/count distinctions if contractual
```

Link this contract to representative scenarios.

---

# 42. Valency and complement fields

Verb categories often encode complement requirements.

Record:

| Verb category | Provider | Complement contract | Preposition/case field | Consumers | Evidence |
|---|---|---|---|---|---|
| `<CATEGORY>` | `<PATH>` | `<TYPE/MEANING>` | `<FIELD OR NONE>` | `<PATHS>` | `<EVIDENCE>` |

A valency category must not be coerced to another valency without documenting preserved and lost requirements.

---

# 43. Slash-category contracts

When categories such as `VPSlash` or `ClSlash` are used, document:

- missing argument type;
- complement position;
- preposition or case requirement;
- extraction information;
- gap realization;
- conversion to nonslash category;
- relative and question consumers.

Template:

| Slash category | Gap contract | Fields | Filled by | Consumers | Evidence |
|---|---|---|---|---|---|
| `<CATEGORY>` | `<DESCRIPTION>` | `<FIELDS>` | `<HELPER/CONSTRUCTOR>` | `<PATHS>` | `<EVIDENCE>` |

---

# 44. Coordination fields

When coordination uses special records or lock fields, document:

```text
conjunction form
number agreement
person resolution
gender resolution
serial or binary representation
punctuation
shared determiner or complement behavior
```

A coordination helper must preserve required fields of every coordinated category.

---

# 45. Question and relative fields

Document fields that distinguish:

```text
direct and indirect question
yes/no and wh-question
relative gap type
relative agreement
resumptive behavior
question word order
```

Link these fields to question and relative scenarios.

---

# 46. Extension-category policy

Project extension categories must not bypass core category contracts.

For every extension category:

- identify its provider;
- identify inherited core structure;
- identify added fields;
- identify coercions;
- identify consumers;
- identify fallback status;
- provide family-level scenario evidence.

---

# 47. Structural-category policy

Structural entries such as pronouns, determiners, conjunctions, and prepositions must use approved category shapes.

Do not reconstruct structural records independently in consumer modules when an authoritative provider exists.

Temporary structural entries must link to `STATUS_LEDGER.md`.

---

# 48. Lexical-category policy

Lexical entries must be created through approved paradigms or constructors.

For each lexical category, document:

```text
approved constructor or paradigm
required fields
irregular override policy
orthography policy
duplicate identifier policy
temporary lexical status policy
```

Lexicon changes affecting expected output require scenario and gold review.

---

# 49. Resource-record contracts

Some public structures are `oper` record types rather than category lincats.

Record them with the same discipline.

| Record ID | GF type name | Provider | Fields | Consumers | Category relationship | Status |
|---|---|---|---|---|---|---|
| `<RECORD-ID>` | `<TYPE>` | `<PATH>` | `<FIELDS>` | `<PATHS>` | `<CATEGORIES>` | `<STATUS>` |

A public resource record must not remain undocumented merely because it is not a `lincat`.

---

# 50. Category alias policy

A category may alias another public type.

Example:

```gf
lincat <CATEGORY> = <PUBLIC_TYPE> ;
```

Document:

- alias provider;
- aliased type owner;
- whether the alias is exact or semantically narrower;
- consumers relying on the alias;
- whether future divergence is allowed.

An alias is a contract, not merely an implementation convenience.

---

# 51. Wrapper-record policy

A category may wrap another value with metadata.

Example:

```gf
lincat <CATEGORY> = {
  core : <TYPE> ;
  lock : <LOCK_TYPE>
} ;
```

Document why the wrapper exists and which consumers need each layer.

Do not unwrap and rewrap in multiple modules with inconsistent initialization.

---

# 52. Category equality and identity assumptions

GF code may not expose general runtime equality for all values, but consumers may assume identity-like properties.

Document assumptions such as:

```text
same agreement metadata is preserved
same lexical stem is retained
same missing-complement contract is retained
same lock state survives a constructor
```

These assumptions need validation through observable behavior.

---

# 53. Construction invariants

For each major category, define invariants.

Examples to adapt:

```text
all inflection table cells are defined
agreement fields match the head
lock fields reflect the unresolved complement
surface strings do not contain debug markers
optional fields follow their controlling parameter
coercions preserve required agreement
constructors never return temporary placeholders in release mode
```

Do not retain generic invariants that do not apply.

---

# 54. Detailed category entry template

Copy this section for every important category.

## `<CAT-ID>` — `<CATEGORY>`

**Status:** `<ACTIVE | DEPRECATED | RETIRED>`

**Purpose**

```text
<WHAT THE CATEGORY REPRESENTS>
```

**Abstract provider**

```text
<PATH>
```

**Lincat provider**

```text
<PATH>
```

**Construction providers**

```text
<PATHS>
```

**Direct consumers**

```text
<PATHS>
```

**Downstream entrypoints**

```text
<PATHS>
```

**Exact GF type**

```gf
lincat <CATEGORY> = <EXACT TYPE> ;
```

**Public fields**

| Field | Type | Meaning | Initialization | Consumers | Invariant |
|---|---|---|---|---|---|
| `<FIELD>` | `<TYPE>` | `<MEANING>` | `<POLICY>` | `<PATHS>` | `<INVARIANT>` |

**Table indices**

```text
<INDEX CONTRACT OR NONE>
```

**Agreement dimensions**

```text
<DIMENSIONS OR NONE>
```

**Lock fields**

```text
<FIELDS OR NONE>
```

**Empty or missing behavior**

```text
<POLICY>
```

**Ordering behavior**

```text
<POLICY>
```

**Allowed coercions**

```text
<COERCIONS OR NONE>
```

**Construction invariants**

```text
<INVARIANTS>
```

**Forbidden behavior**

```text
<PROHIBITIONS>
```

**Failure behavior**

```text
<COMPILE, LOAD, RUNTIME OR COMPARISON FAILURE>
```

**Validation evidence**

```text
direct compile: <TARGET>
consumer compile: <TARGETS>
entrypoint compile: <TARGET>
scenario: <SCENARIO-ID>
gold: <PATH OR NONE>
manual review: <CRITERION OR NONE>
```

**Related contracts**

```text
<INTERFILE CONTRACT IDS>
```

**Related documentation**

```text
<PATHS>
```

**Status-ledger link**

```text
<LEDGER ID OR NONE>
```

**Last reviewed**

```text
<YYYY-MM-DD OR PROJECT RELEASE>
```

---

# 55. Detailed parameter entry template

## `<PARAM-ID>` — `<PARAMETER>`

**Status:** `<ACTIVE | DEPRECATED | RETIRED>`

**Provider**

```text
<PATH>
```

**Exact GF declaration**

```gf
param <PARAMETER> =
    <VALUE_1>
  | <VALUE_2>
  | <VALUE_3> ;
```

**Value semantics**

| Value | Meaning | Produced by | Pattern consumers | Evidence |
|---|---|---|---|---|
| `<VALUE>` | `<MEANING>` | `<PATHS>` | `<PATHS>` | `<EVIDENCE>` |

**Indexed tables**

```text
<TABLES>
```

**Default policy**

```text
<POLICY OR NONE>
```

**Extension policy**

```text
<HOW A NEW VALUE IS ADDED>
```

**Breaking changes**

```text
<REMOVAL, MERGE OR REINTERPRETATION POLICY>
```

---

# 56. Detailed resource-record entry template

## `<RECORD-ID>` — `<TYPE-NAME>`

**Status:** `<ACTIVE | DEPRECATED | RETIRED>`

**Provider**

```text
<PATH>
```

**GF type**

```gf
oper <TYPE-NAME> : Type = {
  <FIELD_1> : <TYPE_1> ;
  <FIELD_2> : <TYPE_2>
} ;
```

**Consumers**

```text
<PATHS>
```

**Field contracts**

| Field | Type | Meaning | Initialization | Consumers | Invariant |
|---|---|---|---|---|---|
| `<FIELD>` | `<TYPE>` | `<MEANING>` | `<POLICY>` | `<PATHS>` | `<INVARIANT>` |

**Relationship to categories**

```text
<CATEGORIES AND HELPERS>
```

**Validation**

```text
<EVIDENCE>
```

---

# 57. Constructor-to-field matrix

Maintain a matrix for constructors that initialize important structured categories.

| Constructor/function | Module | Output category | Fields set directly | Fields derived | Helper used | Evidence |
|---|---|---|---|---|---|---|
| `<FUNCTION>` | `<PATH>` | `<CATEGORY>` | `<FIELDS>` | `<FIELDS>` | `<HELPER>` | `<EVIDENCE>` |

This matrix may be moved to `SYNTAX_AND_CONSTRUCTOR_RULES.md` when large, but field-initialization contracts must remain linked here.

---

# 58. Category-consumer matrix

| Category | Provider | Morphology consumers | Syntax consumers | Structural consumers | Entrypoints | Scenarios |
|---|---|---|---|---|---|---|
| `<CATEGORY>` | `<PATH>` | `<PATHS>` | `<PATHS>` | `<PATHS>` | `<PATHS>` | `<IDS>` |

The matrix must reflect actual imports and field access.

---

# 59. Abstract-to-concrete coverage

For every required abstract category:

```text
abstract category exists
→ concrete lincat exists
→ required functions linearize
→ missing-linearization policy passes
→ representative scenarios pass
```

Registry:

| Abstract category | Abstract provider | Concrete provider | Lincat contract | Missing policy | Scenario evidence |
|---|---|---|---|---|---|
| `<CATEGORY>` | `<PATH>` | `<PATH>` | `<CAT-ID>` | `<POLICY>` | `<IDS>` |

---

# 60. Missing-linearization policy

The project must define its accepted release policy.

Recommended final release policy:

```text
no required abstract function remains without a concrete linearization
```

Document exceptions only when project scope explicitly permits them.

Each exception requires:

```text
function ID
reason
consumer impact
scenario evidence
status-ledger entry
release decision
exit condition
```

An empty string is not automatically a valid substitute for missing linearization.

---

# 61. Scenario coverage

Category contracts should be validated through representative native GF scenarios.

Recommended scenario classes:

```text
load
missing linearizations
linearization
parse
round trip
morphology
bounded generation
operation introspection
```

Registry:

| Contract ID | Category/parameter | Scenario ID | Assertion or gold | Mode | Blocking |
|---|---|---|---|---|---:|
| `<CAT/PARAM-ID>` | `<SUBJECT>` | `<SCENARIO>` | `<STRATEGY>` | `<MODES>` | `<YES/NO>` |

---

# 62. Gold coverage

Gold-backed output must preserve category-relevant behavior.

Examples:

```text
agreement
inflection
word order
function names
abstract trees
ambiguity
missing-linearization names
orthography
```

Gold normalization must not remove meaningful category behavior.

Registry:

| Contract ID | Scenario | Gold | Normalization profile | Meaning protected |
|---|---|---|---|---|
| `<ID>` | `<SCENARIO>` | `<PATH>` | `<PROFILE>` | `<BEHAVIOR>` |

---

# 63. Compile coverage

A lincat contract requires more than provider compilation when consumers use its fields.

Minimum proof sequence:

```text
provider compile
→ direct consumer compile
→ downstream checkpoint compile
→ required entrypoint compile
```

Registry:

| Contract ID | Provider compile | Consumer compile | Checkpoint | Entrypoint | Last run |
|---|---|---|---|---|---|
| `<ID>` | `<TARGET>` | `<TARGETS>` | `<ID>` | `<TARGET>` | `<RUN-ID>` |

---

# 64. Generation coverage

Bounded generation can exercise table and parameter combinations.

For every generation scenario, document:

```text
category
depth
number limit
language
expected output policy
parameter coverage
timeout
```

Random generation must not serve as exact deterministic gold unless the project proves deterministic behavior.

---

# 65. Manual validation

Manual review is allowed only when executable validation cannot assess the required linguistic property.

Record:

| Criterion ID | Contract | Reviewer role | Method | Evidence location | Blocking |
|---|---|---|---|---|---:|
| `<MANUAL-ID>` | `<CAT/PARAM-ID>` | `<ROLE>` | `<METHOD>` | `<PATH>` | `<YES/NO>` |

Undocumented manual inspection is not release evidence.

---

# 66. Validation result interpretation

Category contract failures may appear as:

```text
syntax error
type error
missing symbol
incomplete pattern
missing linearization
empty unexpected output
wrong agreement
wrong inflection
wrong order
parse-tree mismatch
gold mismatch
artifact failure
configuration drift
```

Preserve the original GF diagnostic and classify separately.

A downstream consumer failure should not be presented as an independent root failure when a provider failure is known.

---

# 67. Contract-change classification

## 67.1 Internal compatible change

Examples:

- optimize a private table;
- refactor a private helper;
- rename a local variable;
- improve implementation while preserving every public field and output contract.

Required validation:

```text
provider compile
affected scenarios
consumer smoke proof
```

## 67.2 Compatible contract extension

Examples:

- add a derivable public field with safe initialization;
- add an optional helper;
- add a new category not consumed by existing contracts;
- add an optional parameter dimension with compatible defaults where semantically valid.

Required actions:

```text
provider update
consumer review
documentation update
tests
scenario coverage
interfile lock update
```

## 67.3 Breaking change

Examples:

- remove or rename a public field;
- change a field type;
- change a table index;
- add a parameter value without updating consumers;
- change field meaning;
- change category provider;
- flatten a structured category;
- change coercion information loss;
- change ordering behavior;
- change empty-value semantics;
- change constructor initialization.

Required actions:

1. identify the contract ID;
2. record the reason;
3. list providers and consumers;
4. update every consumer;
5. update interfaces and instances;
6. update scenarios and inputs;
7. review gold;
8. update architecture and syntax documentation;
9. update the status ledger;
10. record a decision;
11. update the interfile lock;
12. run checkpoints and release validation.

---

# 68. Lincat migration plan

For a breaking lincat change, record:

```text
migration ID
source shape
target shape
affected categories
affected providers
affected consumers
field mapping
default policy
information loss
temporary compatibility helpers
scenario migration
gold migration
removal milestone
```

Migration template:

| Old field/type | New field/type | Mapping | Lossless | Consumer action |
|---|---|---|---:|---|
| `<OLD>` | `<NEW>` | `<RULE>` | `<YES/NO>` | `<ACTION>` |

Do not maintain an undocumented dual shape.

---

# 69. Transitional compatibility

A temporary compatibility helper may bridge old and new shapes.

It must have:

```text
owner
GF type
supported direction
information preserved
information lost
consumer list
status-ledger ID
removal criterion
validation evidence
```

A transitional helper must not become permanent accidentally.

---

# 70. Deprecation

A deprecated category, field, parameter, or helper remains supported during the declared window.

Record:

```text
replacement
deprecation project version
earliest removal version
consumer migration
scenario migration
gold impact
```

Deprecated identifiers must not be reused.

---

# 71. Temporary and fallback structures

Every temporary or fallback category implementation must link to `STATUS_LEDGER.md`.

Record:

| Ledger ID | Contract ID | Temporary behavior | Consumer impact | Validation impact | Exit condition |
|---|---|---|---|---|---|
| `<LEDGER-ID>` | `<CAT-ID>` | `<BEHAVIOR>` | `<IMPACT>` | `<IMPACT>` | `<CONDITION>` |

A fallback must not be presented as stable release behavior without explicit acceptance.

---

# 72. Known issues

Known lincat or category defects belong in `KNOWN_ISSUES.md`.

Examples:

```text
incorrect agreement branch
missing inflection cell
overgeneration
unexpected ambiguity
flattened temporary structure
incomplete lock propagation
wrong preposition case
incorrect coercion
```

Each issue must identify release impact.

---

# 73. Decision records

A decision is required when changing:

```text
category ownership
lincat structure
field semantics
parameter inventory
agreement model
lock design
inheritance or subtraction
coercion policy
flattening policy
accepted empty realization
release-visible ordering
```

Record project decisions in:

```text
project/docs/DECISION_LOG.md
```

---

# 74. Documentation consistency

The following must agree:

```text
this document
actual lincat declarations
resource type declarations
constructor initialization
module dependency map
architecture document
morphology specification
syntax specification
interfile contract lock
validation specification
scenarios
gold
```

A stale document is a contract failure for release-significant structure.

---

# 75. Automated contract checks

Recommended command:

```text
gf-wordbench project contracts check
```

Category and lincat checks should detect:

1. documented provider missing;
2. documented consumer missing;
3. category absent from provider;
4. lincat shape differs from documented shape;
5. public field used but undocumented;
6. documented field absent;
7. duplicate public helper ownership;
8. parameter value drift;
9. table consumer not reviewed after parameter extension;
10. active category without evidence;
11. flattened category without decision;
12. temporary field without ledger entry;
13. deprecated identifier without replacement;
14. scenario coverage missing;
15. gold reference missing;
16. stale module suffix;
17. unresolved required placeholder in active project;
18. category contract contradicting interfile lock.

Some checks may require structured project metadata or manual review until GF-aware static extraction is implemented.

---

# 76. Scanner limitations

Text-based contract scanning may detect names and likely field access.

It cannot prove full GF semantics.

GF compilation and native scenario execution remain authoritative.

A scanner result is evidence, not a substitute for GF.

---

# 77. Required tests

Project contract tests should cover:

```text
category provider existence
consumer existence
lincat declaration presence
field-name consistency
parameter-value consistency
interface-instance agreement
helper ownership
constructor field initialization where statically checkable
direct provider compile
direct consumer compile
checkpoint compile
entrypoint compile
missing-linearization scenario
representative linearization
representative parse
bounded generation
gold comparison
PGF build when applicable
```

---

# 78. Category-specific validation checklist

For each detailed category:

```text
[ ] Stable contract ID
[ ] Purpose documented
[ ] Abstract provider exists
[ ] Lincat provider exists
[ ] Exact GF type copied accurately
[ ] Every public field documented
[ ] Every table index documented
[ ] Every parameter value documented
[ ] Agreement dimensions documented
[ ] Lock fields documented
[ ] Empty-value policy documented
[ ] Initialization policy documented
[ ] Construction providers listed
[ ] Direct consumers listed
[ ] Downstream entrypoints listed
[ ] Coercions listed
[ ] Ordering behavior documented
[ ] Forbidden behavior documented
[ ] Provider compiles
[ ] Direct consumers compile
[ ] Checkpoint passes
[ ] Entrypoint passes
[ ] Scenario evidence passes
[ ] Gold reviewed
[ ] Ledger and issues reviewed
```

---

# 79. Parameter-change checklist

```text
[ ] Parameter owner identified
[ ] Exact declaration updated
[ ] Every value documented
[ ] Every indexed table reviewed
[ ] Every pattern match reviewed
[ ] Every constructor reviewed
[ ] Every helper reviewed
[ ] Every entrypoint reviewed
[ ] Generation coverage reviewed
[ ] Scenarios updated
[ ] Gold reviewed
[ ] Decision recorded when breaking
[ ] Checkpoints pass
[ ] Release passes when applicable
```

---

# 80. Field-change checklist

```text
[ ] Field contract ID identified
[ ] Provider updated
[ ] Type impact classified
[ ] Meaning impact classified
[ ] Initialization updated
[ ] Every direct reader updated
[ ] Every writer or record update updated
[ ] Coercions updated
[ ] Helpers updated
[ ] Interfaces and instances updated
[ ] Constructors updated
[ ] Scenarios updated
[ ] Gold reviewed
[ ] Documentation updated
[ ] Interfile lock updated
[ ] Validation passes
```

---

# 81. Flattening checklist

Before approving `record/table → Str`:

```text
[ ] No consumer requires lost grammatical information
[ ] No agreement dimension is discarded
[ ] No lock field is discarded
[ ] No valency information is discarded
[ ] No ordering behavior becomes unrecoverable
[ ] No public helper requires prior fields
[ ] Architecture permits flattening
[ ] Decision log records rationale
[ ] Scenario coverage proves compatibility
[ ] Gold changes are reviewed
[ ] Project release impact is accepted
```

If any required information is lost, flattening is prohibited.

---

# 82. Project initialization procedure

When creating an active project from this template:

1. fill project identity;
2. inspect every abstract category;
3. identify its concrete lincat provider;
4. copy exact GF type declarations;
5. enumerate public fields;
6. enumerate parameter types and values;
7. enumerate direct consumers;
8. identify lock and agreement fields;
9. identify public resource records;
10. identify helper ownership;
11. identify interfaces and instances;
12. identify coercions;
13. identify temporary or fallback structures;
14. create scenario coverage;
15. create gold coverage where appropriate;
16. update `INTERFILE_CONTRACT_LOCK.md`;
17. update `VALIDATION_SPEC.md`;
18. run baseline validation;
19. remove non-applicable template rows;
20. verify no required placeholder remains.

---

# 83. Initial extraction worksheet

Use this temporary worksheet during initialization.

| Source file | Category/type | Exact declaration located | Public consumers found | Detailed contract created |
|---|---|---:|---:|---:|
| `<PATH>` | `<CATEGORY/TYPE>` | `<YES/NO>` | `<YES/NO>` | `<YES/NO>` |

Delete this worksheet from the active document after initialization if no longer needed.

---

# 84. Review procedure

For each provider:

1. read exact GF declaration;
2. list imported consumers;
3. search for field access;
4. search for record updates;
5. inspect constructors;
6. inspect interfaces and instances;
7. inspect scenarios;
8. inspect gold;
9. compare documentation;
10. run compile and behavior evidence.

Review both directions:

```text
Does the provider still guarantee the documented shape?
Does each consumer depend only on the documented guarantee?
```

---

# 85. Release gate

The category and lincat contract passes release review only when:

```text
all active required categories are documented
all exact public shapes match source
all public fields and parameters are documented
all known consumers are registered
all temporary structures are visible
all blocking issues are resolved
all required checkpoints pass
all required entrypoints pass
all required scenarios pass
all required gold matches
documentation and implementation agree
```

A release cannot rely on a remembered or implicit lincat contract.

---

# 86. Anti-patterns

Prohibited:

```text
consumer reads undocumented record field
provider removes field without consumer migration
same helper copied into several modules
parameter value added without table review
structured category flattened to Str to silence a type error
empty string used as undocumented missing value
arbitrary agreement default
consumer reconstructs structural record independently
interface and instance diverge
temporary field presented as stable
scenario validates obsolete category shape
gold updated only to hide regression
documentation lists old provider
active project retains template placeholders
```

---

# 87. Drift indicators

Probable drift exists when:

- GF source contains a public field absent here;
- this document contains a field absent from source;
- two modules define equivalent public record types independently;
- a parameter has different value sets across modules;
- a consumer pattern omits a new value;
- a record update drops a field;
- a scenario loads a provider different from the documented provider;
- a gold change follows a lincat change without review;
- a helper is used by a consumer but has no owner;
- a lock field is never set or never read;
- a structured category becomes `Str` without a decision;
- status ledger and implementation disagree;
- architecture and provider location disagree.

Every drift indicator requires correction or a deliberate coordinated contract change.

---

# 88. Compact contract registry

Replace this registry with current project entries.

| Contract ID | Subject | Provider | Consumers | Status | Main evidence |
|---|---|---|---|---|---|
| `<CAT-ID>` | `<CATEGORY>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<PARAM-ID>` | `<PARAMETER>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<RECORD-ID>` | `<RESOURCE TYPE>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<HELPER-ID>` | `<HELPER>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |
| `<COERCION-ID>` | `<COERCION>` | `<PATH>` | `<PATHS>` | `<STATUS>` | `<EVIDENCE>` |

---

# 89. Related documents

```text
project/README.md
project/project.toml
project/docs/00_PROJECT_START_HERE.md
project/docs/LANGUAGE_OVERVIEW.md
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/MODULE_DEPENDENCY_MAP.md
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

---

# 90. Final contract

The active project must preserve this relationship:

```text
abstract category
    defines the linguistic interface

authoritative concrete provider
    defines the exact lincat shape

resource and morphology providers
    supply valid structured values

constructors and helpers
    initialize and transform those values

syntax and structural consumers
    rely only on documented fields and parameters

entrypoints
    integrate the complete contract

native GF scenarios
    exercise observable behavior

gold files
    preserve reviewed expectations

GF Wordbench
    verifies compilation, behavior, evidence, and release gates
```

The governing invariant is:

> Every cross-module category assumption must be explicit, typed, owned, initialized, consumed only as documented, and proven by current validation evidence.
