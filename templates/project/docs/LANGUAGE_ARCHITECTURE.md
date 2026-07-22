# GF Wordbench Project Template — Language Architecture

**Document ID:** `GF-WB-TEMPLATE-LANGUAGE-ARCHITECTURE`  
**Status:** Normative project template  
**Applies to:** One language project created from `templates/project/`  
**Template owner:** GF Wordbench maintainers  
**Project owner:** `<PROJECT_OWNER>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**GF suffix:** `<GF_SUFFIX>`  
**Source directory:** `<SOURCE_DIR>`  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\templates\project\docs\LANGUAGE_ARCHITECTURE.md`  
**Document version:** `1.0.0`  
**Last reviewed:** `<YYYY-MM-DD>`

---

## 1. Purpose

This document defines the intended architecture of one GF language project created from the GF Wordbench project template.

It must be instantiated for the selected language before the project is treated as initialized.

It describes:

- project identity;
- language scope;
- source-module layers;
- permitted dependency directions;
- ownership of abstract syntax, categories, morphology, paradigms, syntax, lexicon, structural vocabulary, extensions, interfaces, entrypoints, and release artifacts;
- lincat and parameter boundaries;
- module naming conventions;
- project configuration alignment;
- validation checkpoints;
- scenario and gold relationships;
- temporary and incomplete implementation policy;
- change classification;
- required architecture evidence;
- the initialization checklist.

This document defines architecture.

Exact GF symbol signatures belong in:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Exact import relationships belong in:

```text
project/docs/MODULE_DEPENDENCY_MAP.md
```

Actual implementation status belongs in:

```text
project/docs/STATUS_LEDGER.md
```

---

## 2. Template-use rule

This file is a template.

Before activating a new project:

1. replace every required placeholder;
2. remove example modules that do not apply;
3. add language-specific layers that do apply;
4. verify every listed module exists or is explicitly marked planned;
5. align `project.toml`;
6. align the dependency map;
7. align the interfile contract lock;
8. align the validation specification;
9. register incomplete areas in the status ledger;
10. execute a baseline validation run.

The initialized active-project copy must not retain unresolved required placeholders such as:

```text
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<SOURCE_DIR>
<ABSTRACT_ENTRYPOINT>
<CONCRETE_ENTRYPOINT>
<LANGUAGE_ENTRYPOINT>
<EXPECTED_PGF>
```

Optional placeholders may remain only when clearly marked:

```text
Not applicable
Not implemented
Planned
Blocked
```

---

## 3. Normative language

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **PROVIDER**: module or artifact supplying a public contract.
- **CONSUMER**: module, scenario, or process relying on a provider.
- **ENTRYPOINT**: top-level GF module compiled, loaded, or built into PGF.
- **LAYER**: group of modules with a shared architectural role.
- **CHECKPOINT**: configured validation target required at a development stage.
- **SCENARIO**: native `.gfs` validation script.
- **GOLD**: reviewed normalized expected output.
- **STABLE**: active, implemented, tested, and supported.
- **EXPERIMENTAL**: implemented for evaluation with limited compatibility.
- **FALLBACK**: temporary behavior used while the intended implementation is incomplete.
- **BLOCKED**: implementation cannot progress until a named prerequisite is resolved.

---

# 4. Project identity

Fill this table during initialization.

| Field | Value |
|---|---|
| Language name | `<LANGUAGE_NAME>` |
| Language code | `<LANGUAGE_CODE>` |
| GF suffix | `<GF_SUFFIX>` |
| Project ID | `<PROJECT_ID>` |
| Project version | `<PROJECT_VERSION_OR_NOT_YET_DEFINED>` |
| Source directory | `<SOURCE_DIR>` |
| RGL family/base | `<RGL_FAMILY_OR_NONE>` |
| Abstract entrypoint | `<ABSTRACT_ENTRYPOINT>` |
| Concrete entrypoint | `<CONCRETE_ENTRYPOINT>` |
| Syntax entrypoint | `<SYNTAX_ENTRYPOINT_OR_NONE>` |
| Language entrypoint | `<LANGUAGE_ENTRYPOINT>` |
| API entrypoint | `<API_ENTRYPOINT_OR_NONE>` |
| Release entrypoint | `<RELEASE_ENTRYPOINT>` |
| Expected PGF | `<EXPECTED_PGF>` |
| Primary dialect/register | `<DIALECT_AND_REGISTER>` |
| Project owner | `<PROJECT_OWNER>` |
| Architecture reviewer | `<REVIEWER>` |

---

## 4.1 Identity invariants

The project represents one active language.

The following must agree:

```text
project.toml identity
GF module suffixes
source filenames
GF module declarations
entrypoints
scenario registry
gold filenames
documentation
expected PGF name
```

Stale identifiers from a previously cloned language are prohibited.

---

## 4.2 GF suffix

All language-specific GF modules should use one suffix:

```text
<GF_SUFFIX>
```

Examples of expected naming patterns:

```text
Cat<GF_SUFFIX>.gf
Morpho<GF_SUFFIX>.gf
Paradigms<GF_SUFFIX>.gf
Noun<GF_SUFFIX>.gf
Verb<GF_SUFFIX>.gf
Grammar<GF_SUFFIX>.gf
Lang<GF_SUFFIX>.gf
All<GF_SUFFIX>.gf
```

These examples do not require every module family.

If the project follows another RGL naming convention, document it here and in the dependency map.

---

## 4.3 Language scope

Describe the intended language coverage.

```text
Target standard:
<DIALECT_OR_STANDARD>

Target register:
<REGISTER>

Orthography:
<ORTHOGRAPHY_STANDARD>

Primary use cases:
<USE_CASES>

Explicit exclusions:
<EXCLUSIONS>
```

Do not silently mix dialects, registers, historical stages, or orthographic standards.

Variants must have an explicit representation and selection rule.

---

# 5. Architectural goals

The language architecture should optimize for:

```text
semantic correctness
typed structures
clear module ownership
RGL compatibility
incremental compilation
diagnosable failures
portable scenarios
reviewable regression evidence
stable entrypoints
controlled extension
```

The architecture must not optimize for short-term source brevity at the cost of hidden contracts.

---

# 6. Global project invariants

## 6.1 One authoritative provider

Every public responsibility has one authoritative provider.

Examples:

```text
abstract category inventory
category lincats
noun morphology
verb morphology
adjective morphology
public paradigms
sentence construction
structural lexicon
extension coordination
release entrypoint
gold file for one scenario variant
```

Duplicated providers require a documented selection rule.

---

## 6.2 No hidden dependency

A consumer must not rely on an undocumented:

```text
module
public oper
public param
record field
lincat field
constructor default
side effect
artifact
scenario marker
```

Cross-module dependencies must appear in the interfile contract lock.

---

## 6.3 No silent flattening

Structured values must not be flattened to `Str` solely to satisfy one local consumer.

Examples:

```text
NP
CN
AP
VP
VPSlash
Cl
S
Prep
Pron
language-specific agreement records
morphological tables
```

A deliberate flattened design must document:

- why structure is unnecessary;
- which consumers are affected;
- what future extension is lost;
- validation proving the design is adequate.

---

## 6.4 Directed imports

Imports must follow the documented layer direction.

Lower-level modules must not import higher-level entrypoints.

Circular imports are prohibited.

---

## 6.5 Explicit incomplete state

Incomplete behavior must be labeled.

Allowed status labels:

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

A temporary or fallback implementation must be recorded in:

```text
project/docs/STATUS_LEDGER.md
```

---

## 6.6 Evidence for architecture

Every public boundary must have at least one validation proof:

```text
direct compilation
consumer compilation
entrypoint compilation
GF load scenario
parse scenario
linearization scenario
morphology scenario
missing-function inspection
gold comparison
PGF build
documented review when automation is impossible
```

---

# 7. Layer model

The default project architecture contains these conceptual layers:

```text
Layer 0 — Abstract syntax
Layer 1 — Low-level resources and morphology
Layer 2 — Category and lincat providers
Layer 3 — Paradigm and lexical-construction APIs
Layer 4 — Core syntax implementations
Layer 5 — Structural and closed-class vocabulary
Layer 6 — Lexicon
Layer 7 — Extension families
Layer 8 — Grammar and language entrypoints
Layer 9 — API/release entrypoint and PGF
Layer 10 — Validation scenarios and gold
```

A project may combine layers when the language is small.

Combined ownership must remain explicit.

---

# 8. Default dependency direction

Expected direction:

```text
abstract syntax
        ↓
low-level resources and morphology
        ↓
category/lincat providers
        ↓
paradigm APIs and lexical constructors
        ↓
core syntax modules
        ↓
structural vocabulary and lexicon
        ↓
extension coordinators
        ↓
grammar/syntax/language entrypoints
        ↓
API/release entrypoint
        ↓
PGF
```

Validation direction:

```text
project configuration
→ checkpoints and entrypoints
→ scenarios
→ normalized output
→ gold comparison
→ release decision
```

Documentation direction:

```text
architecture
→ dependency map
→ lincat contract
→ interfile lock
→ validation specification
→ coverage matrix
→ release criteria
```

---

# 9. Prohibited dependency directions

Normally prohibited:

```text
low-level morphology → final grammar entrypoint
resource module → API entrypoint
category provider → consumer-specific helper
lexicon → project configuration
scenario → undocumented private module
gold file → source generation logic
release entrypoint → test-only module
project configuration → generated run output
report artifact → GF source
```

Exceptions require:

```text
decision-log entry
interfile-contract entry
dependency-map update
validation evidence
```

---

# 10. Layer 0 — Abstract syntax

## 10.1 Purpose

The abstract layer defines language-independent or project-specific semantic structure.

Possible providers:

```text
<RGL_ABSTRACT_MODULES>
<PROJECT_ABSTRACT_CATEGORY_MODULE>
<PROJECT_ABSTRACT_FUNCTION_MODULE>
<PROJECT_EXTENSION_ABSTRACT_MODULES>
```

## 10.2 Ownership

The abstract layer owns:

```text
categories
functions
argument order
semantic distinctions
abstract API stability
```

It does not own:

```text
word order
inflection
orthography
concrete lincat fields
language-specific token joining
```

## 10.3 Abstract entrypoint

Declare:

```text
Module: <ABSTRACT_ENTRYPOINT>
Path: <ABSTRACT_ENTRYPOINT_PATH>
Status: <STATUS>
```

## 10.4 Abstract completeness

Concrete implementations must account for every required abstract function.

Incomplete functions must be visible through:

```text
GF compilation
pg -missing or equivalent
status ledger
release criteria
```

## 10.5 Breaking changes

Breaking abstract changes include:

```text
category removal
function removal
function rename
argument reorder
argument type change
semantic meaning change
```

Such changes require concrete, scenario, gold, entrypoint, and project-version review.

---

# 11. Layer 1 — Low-level resources

## 11.1 Purpose

Low-level resources define reusable language-specific machinery that is below category syntax.

Possible modules:

```text
Res<GF_SUFFIX>.gf
Types<GF_SUFFIX>.gf
Orthography<GF_SUFFIX>.gf
Common<GF_SUFFIX>.gf
```

Use only modules justified by the language architecture.

## 11.2 Responsibilities

Possible responsibilities:

```text
shared parameters
agreement types
record types
orthographic helpers
token joining
clitic utilities
common tables
feature conversion
low-level constructors
```

## 11.3 Constraints

Low-level resources must:

- remain independent from top-level entrypoints;
- avoid importing category consumers;
- document every public symbol;
- centralize shared transformations;
- keep private helpers private;
- expose typed values rather than opaque strings when consumers need structure.

---

# 12. Layer 1 — Morphology

## 12.1 Provider map

Fill:

| Responsibility | Provider | Consumers | Status |
|---|---|---|---|
| Noun morphology | `<NOUN_MORPHOLOGY_PROVIDER>` | `<CONSUMERS>` | `<STATUS>` |
| Verb morphology | `<VERB_MORPHOLOGY_PROVIDER>` | `<CONSUMERS>` | `<STATUS>` |
| Adjective morphology | `<ADJECTIVE_MORPHOLOGY_PROVIDER>` | `<CONSUMERS>` | `<STATUS>` |
| Pronoun morphology | `<PRONOUN_MORPHOLOGY_PROVIDER>` | `<CONSUMERS>` | `<STATUS>` |
| Determiner morphology | `<DETERMINER_MORPHOLOGY_PROVIDER>` | `<CONSUMERS>` | `<STATUS>` |
| Shared orthography | `<ORTHOGRAPHY_PROVIDER>` | `<CONSUMERS>` | `<STATUS>` |

## 12.2 Default module

If one module owns shared morphology:

```text
Morpho<GF_SUFFIX>.gf
```

Document the exact choice.

## 12.3 Morphology responsibilities

Morphology may own:

```text
inflection parameters
stems
inflection tables
agreement features
regular-class builders
irregular builders
defective-form representation
shared orthographic transformations
canonical-form extraction
```

## 12.4 Constraints

- inflection tables must be complete for declared domains;
- partial paradigms must be explicit;
- shared orthographic operations must have one provider;
- public helpers must document accepted input;
- unsafe runtime string matching must be documented;
- morphology must not import final entrypoints;
- morphology must return structures compatible with category lincats.

Detailed rules belong in:

```text
project/docs/MORPHOLOGY_SPEC.md
```

---

# 13. Layer 2 — Category and lincat providers

## 13.1 Default category provider

Typical module:

```text
Cat<GF_SUFFIX>.gf
```

or an equivalent set of category modules.

## 13.2 Responsibilities

The category layer owns:

```text
lincat definitions
record fields
table domains
agreement values
inherent grammatical properties
category-specific shared constructors
coercions shared by syntax modules
```

## 13.3 Lincat contract

Every cross-module field must be documented in:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

Required inventory fields:

```text
category
provider
GF type
record/table shape
field meaning
consumer list
initialization policy
status
validation
```

## 13.4 Field changes

Breaking changes include:

```text
field rename
field removal
field type change
meaning change
table-domain change
new mandatory field
agreement dimension removal
```

Adding a derivable or optional field requires an explicit initialization policy.

## 13.5 Category ownership map

Fill:

| Category family | Provider | Main consumers | Status |
|---|---|---|---|
| Noun categories | `<PATH>` | `<PATHS>` | `<STATUS>` |
| Adjective categories | `<PATH>` | `<PATHS>` | `<STATUS>` |
| Verb categories | `<PATH>` | `<PATHS>` | `<STATUS>` |
| Clause/sentence categories | `<PATH>` | `<PATHS>` | `<STATUS>` |
| Pronoun/determiner categories | `<PATH>` | `<PATHS>` | `<STATUS>` |
| Preposition categories | `<PATH>` | `<PATHS>` | `<STATUS>` |
| Language-specific categories | `<PATH>` | `<PATHS>` | `<STATUS>` |

Remove non-applicable rows.

---

# 14. Layer 3 — Paradigm APIs

## 14.1 Purpose

Paradigm modules provide stable lexical constructors for lexicon authors.

Typical module:

```text
Paradigms<GF_SUFFIX>.gf
```

## 14.2 Responsibilities

The paradigm API owns:

```text
mkN-like constructors
mkV-like constructors
mkA-like constructors
mkAdv-like constructors
mkPrep-like constructors
language-specific lexical constructors
documented overloads
regular defaults
irregular pathways
full-form escape hatches
```

Exact names are project-specific.

## 14.3 Constraints

Paradigm APIs must:

- use the authoritative morphology provider;
- not duplicate stem/inflection logic without justification;
- document arity and argument order;
- document defaults;
- return the documented category;
- expose explicit irregular alternatives;
- mark shallow constructors as temporary/fallback;
- remain stable for lexical consumers.

## 14.4 Public API inventory

Maintain in the lincat/contract documentation:

| Constructor | GF type | Inputs | Defaults | Irregular alternative | Consumers | Status |
|---|---|---|---|---|---|---|
| `<NAME>` | `<TYPE>` | `<INPUTS>` | `<DEFAULTS>` | `<NAME_OR_NONE>` | `<CONSUMERS>` | `<STATUS>` |

---

# 15. Layer 4 — Core syntax modules

## 15.1 Typical module families

Possible modules:

```text
Noun<GF_SUFFIX>.gf
Adjective<GF_SUFFIX>.gf
Verb<GF_SUFFIX>.gf
Adverb<GF_SUFFIX>.gf
Sentence<GF_SUFFIX>.gf
Question<GF_SUFFIX>.gf
Relative<GF_SUFFIX>.gf
Conjunction<GF_SUFFIX>.gf
Phrase<GF_SUFFIX>.gf
Text<GF_SUFFIX>.gf
Idiom<GF_SUFFIX>.gf
Numeral<GF_SUFFIX>.gf
Tense<GF_SUFFIX>.gf
```

Use only the families applicable to the selected RGL architecture.

## 15.2 Responsibilities

Core syntax owns:

```text
constituent composition
word order
agreement propagation
case selection
complement structure
auxiliary sequencing
negation placement
question formation
relative formation
coordination
subordination
punctuation composition
```

## 15.3 Constraints

Core syntax must:

- consume documented lincat fields only;
- preserve required structure;
- not reimplement shared morphology;
- not import final entrypoints;
- expose public constructors through documented providers;
- use language-specific helper modules only through registered contracts.

---

# 16. Noun-syntax layer

Fill:

```text
Provider: <NOUN_MODULE>
Categories implemented: <CATEGORIES>
Morphology provider: <PROVIDER>
Key lincat contracts: <CONTRACT_IDS>
Structural dependencies: <DEPENDENCIES>
Status: <STATUS>
```

Document ownership of:

```text
determiners
definiteness
case
adjective attachment
relative attachment
possessives
quantifiers
apposition
proper names
pronouns
prepositions
```

A responsibility must not be owned independently by multiple layers.

---

# 17. Verb-syntax layer

Fill:

```text
Provider: <VERB_MODULE>
Categories implemented: <CATEGORIES>
Morphology provider: <PROVIDER>
Clause provider: <PROVIDER>
Key lincat contracts: <CONTRACT_IDS>
Status: <STATUS>
```

Document ownership of:

```text
valency
object realization
complement order
tense/aspect/mood realization
auxiliaries
negation
voice
reflexives
clitics
particles
non-finite complements
```

---

# 18. Sentence layer

Fill:

```text
Provider: <SENTENCE_MODULE>
Clause representation: <DESCRIPTION>
Tense interface: <DESCRIPTION>
Polarity interface: <DESCRIPTION>
Word-order rules: <DESCRIPTION>
Status: <STATUS>
```

Sentence composition must preserve sufficient structure for:

```text
questions
relatives
subordination
coordination
embedding
punctuation
```

---

# 19. Question layer

Fill:

```text
Provider: <QUESTION_MODULE>
Question strategies: <DESCRIPTION>
Wh ownership: <MODULE>
Yes/no ownership: <MODULE>
Inversion/particle ownership: <MODULE>
Status: <STATUS>
```

Question syntax must not reconstruct clause internals from realized strings unless explicitly designed and documented.

---

# 20. Relative layer

Fill:

```text
Provider: <RELATIVE_MODULE>
Relative pronoun provider: <MODULE>
Gap representation: <DESCRIPTION>
Agreement behavior: <DESCRIPTION>
Status: <STATUS>
```

Relative syntax must preserve documented gap and agreement structures.

---

# 21. Coordination layer

Fill:

```text
Provider: <CONJUNCTION_MODULE>
Coordination representation: <DESCRIPTION>
Agreement resolution: <DESCRIPTION>
Punctuation ownership: <MODULE>
Status: <STATUS>
```

Coordination behavior should be shared where possible instead of copied across categories.

---

# 22. Layer 5 — Structural vocabulary

## 22.1 Typical module

```text
Structural<GF_SUFFIX>.gf
```

## 22.2 Responsibilities

Structural vocabulary may own:

```text
pronouns
determiners
prepositions
conjunctions
subjunctions
auxiliaries
question words
relative words
quantifiers
negation particles
punctuation-sensitive closed-class items
```

## 22.3 Constraints

- required structural symbols must be present before release;
- disabled symbols must appear in the status ledger;
- structural forms must use authoritative morphology/paradigm providers;
- `Prep`-like categories must preserve required government fields;
- entrypoint scenarios make referenced structural symbols release-significant.

## 22.4 Structural ownership map

| Family | Provider | Category/type | Consumers | Status |
|---|---|---|---|---|
| Pronouns | `<PATH>` | `<TYPE>` | `<PATHS>` | `<STATUS>` |
| Determiners | `<PATH>` | `<TYPE>` | `<PATHS>` | `<STATUS>` |
| Prepositions | `<PATH>` | `<TYPE>` | `<PATHS>` | `<STATUS>` |
| Conjunctions | `<PATH>` | `<TYPE>` | `<PATHS>` | `<STATUS>` |
| Auxiliaries | `<PATH>` | `<TYPE>` | `<PATHS>` | `<STATUS>` |
| Question/relative items | `<PATH>` | `<TYPE>` | `<PATHS>` | `<STATUS>` |

---

# 23. Layer 6 — Lexicon

## 23.1 Typical modules

```text
Lexicon<GF_SUFFIX>.gf
Dictionary<GF_SUFFIX>.gf
Irreg<GF_SUFFIX>.gf
ExtraLexicon<GF_SUFFIX>.gf
```

Use the actual project organization.

## 23.2 Responsibilities

The lexicon owns:

```text
lexical identity
lemma/principal parts
semantic category
paradigm constructor choice
lexical irregularity arguments
register/dialect annotations
closed versus open lexical status
```

## 23.3 Constraints

The lexicon must:

- use public paradigm constructors;
- avoid manually constructing undocumented lincat records;
- avoid duplicating morphology helpers;
- keep irregular forms explicit;
- record disputed forms in research evidence;
- compile after every paradigm API change.

## 23.4 Lexicon scale strategy

Document whether the project uses:

```text
hand-written GF lexicon
generated GF lexicon
external lexical source
hybrid approach
```

Generated lexical data must have:

```text
generator owner
input schema
deterministic output
review policy
source provenance
regeneration command
```

---

# 24. Layer 7 — Extensions

## 24.1 Typical modules

```text
Extend<GF_SUFFIX>.gf
Construction<GF_SUFFIX>.gf
Documentation<GF_SUFFIX>.gf
language-specific extension modules
```

## 24.2 Responsibilities

Extensions implement:

```text
optional RGL families
language-specific constructions
non-core features
experimental syntax
application-specific functions
```

## 24.3 Coordinator

If multiple extension providers exist, one coordinator should expose them to entrypoints.

Fill:

```text
Extension coordinator: <MODULE>
Extension providers: <MODULES>
Status: <STATUS>
```

## 24.4 Constraints

Extensions must not:

- patch private internals of core modules;
- duplicate core constructor ownership;
- become required silently;
- import release-only modules;
- hide experimental behavior as stable.

Experimental extensions must be registered in the status ledger.

---

# 25. Interface and instance modules

Some projects use GF interfaces and instances.

Possible pattern:

```text
interface <INTERFACE_MODULE>
instance <INSTANCE_MODULE>
```

## 25.1 Interface ownership

An interface owns:

```text
required operations
required types
semantic assumptions
default behavior when explicitly supplied
```

## 25.2 Instance ownership

An instance owns:

```text
language-specific implementation
parameter choices
resource binding
```

## 25.3 Constraints

- interface and instance signatures must match;
- an instance must implement every required operation;
- interface changes require all instances to be reviewed;
- instance modules must not redefine interface meaning;
- inherited placeholders must be listed as incomplete.

Fill:

| Interface | Instance | Main consumers | Status | Validation |
|---|---|---|---|---|
| `<MODULE>` | `<MODULE>` | `<PATHS>` | `<STATUS>` | `<CHECK>` |

Remove this section if not applicable.

---

# 26. Layer 8 — Grammar entrypoint

## 26.1 Concrete grammar entrypoint

Typical:

```text
Grammar<GF_SUFFIX>.gf
```

Fill:

```text
Module: <CONCRETE_ENTRYPOINT>
Path: <PATH>
Abstract implemented: <ABSTRACT_ENTRYPOINT>
Required consumers: <SCENARIOS_AND_ENTRYPOINTS>
Status: <STATUS>
```

## 26.2 Responsibilities

The grammar entrypoint coordinates:

```text
category modules
core syntax
structural vocabulary
required extension families
required lexicon
```

It should contain little or no local linguistic implementation.

Local entrypoint patches indicate lower-layer ownership drift.

## 26.3 Validation

Required evidence:

```text
direct compile
GF load
missing-function inspection
representative parse
representative linearization
downstream language entrypoint compile
```

---

# 27. Syntax entrypoint

Some RGL projects expose a syntax API.

Typical:

```text
Syntax<GF_SUFFIX>.gf
```

Fill:

```text
Module: <SYNTAX_ENTRYPOINT_OR_NONE>
Path: <PATH_OR_NONE>
Provided API: <DESCRIPTION>
Consumers: <CONSUMERS>
Status: <STATUS>
```

A syntax entrypoint should re-export stable construction APIs.

It should not bypass category contracts.

Remove this section if not applicable.

---

# 28. Language entrypoint

Typical:

```text
Lang<GF_SUFFIX>.gf
```

Fill:

```text
Module: <LANGUAGE_ENTRYPOINT>
Path: <PATH>
Imports: <MODULES>
Primary role: <ROLE>
Status: <STATUS>
```

The language entrypoint may combine:

```text
grammar
lexicon
structural layer
extensions
```

It must not hide incomplete required modules.

---

# 29. API entrypoint

Possible:

```text
All<GF_SUFFIX>.gf
Try<GF_SUFFIX>.gf
API<GF_SUFFIX>.gf
```

Fill:

```text
Module: <API_ENTRYPOINT_OR_NONE>
Path: <PATH_OR_NONE>
Audience: <USERS_OR_APPLICATIONS>
Public exports: <DESCRIPTION>
Status: <STATUS>
```

An API entrypoint is optional.

If present, its public exports are project-versioned contracts.

---

# 30. Layer 9 — Release entrypoint

The release entrypoint is the module or ordered entrypoint set used to build the final PGF.

Fill:

```text
Release entrypoint(s): <RELEASE_ENTRYPOINTS>
Expected PGF: <EXPECTED_PGF>
Required concrete languages: <LANGUAGES>
Build options: <OPTIONS>
Status: <STATUS>
```

## 30.1 Release constraints

- every required checkpoint must pass first;
- required scenarios must pass;
- missing required functions block release;
- the PGF must be generated by GF;
- the expected PGF must exist and be non-empty;
- the artifact must be listed in `manifest.json`;
- stale PGF files must not satisfy a new run.

---

# 31. Entrypoint hierarchy

Document the exact hierarchy:

```text
<ABSTRACT_ENTRYPOINT>
        ↓ implemented by
<CONCRETE_ENTRYPOINT>
        ↓ combined/re-exported by
<SYNTAX_ENTRYPOINT_OR_NONE>
        ↓ combined with lexicon by
<LANGUAGE_ENTRYPOINT>
        ↓ optionally re-exported by
<API_ENTRYPOINT_OR_NONE>
        ↓ built as
<EXPECTED_PGF>
```

Delete or modify non-applicable arrows.

---

# 32. Entrypoint ownership table

| Role | Module | Path | Consumers | Status |
|---|---|---|---|---|
| Abstract | `<MODULE>` | `<PATH>` | `<CONSUMERS>` | `<STATUS>` |
| Concrete grammar | `<MODULE>` | `<PATH>` | `<CONSUMERS>` | `<STATUS>` |
| Syntax API | `<MODULE_OR_NONE>` | `<PATH_OR_NONE>` | `<CONSUMERS>` | `<STATUS>` |
| Language | `<MODULE>` | `<PATH>` | `<CONSUMERS>` | `<STATUS>` |
| Public API | `<MODULE_OR_NONE>` | `<PATH_OR_NONE>` | `<CONSUMERS>` | `<STATUS>` |
| Release | `<MODULE_OR_SET>` | `<PATHS>` | PGF builder | `<STATUS>` |

---

# 33. Layer 10 — Validation

Validation is outside the GF source dependency graph but is part of the project architecture.

Canonical directories:

```text
project/validation/scenarios/
project/validation/inputs/
project/validation/gold/
```

## 33.1 Scenario direction

```text
scenario registry
→ native .gfs script
→ declared entrypoint
→ raw stdout/stderr
→ normalized output
→ gold comparison
→ structured scenario result
```

## 33.2 Constraints

- scenario IDs are unique;
- scenarios load documented entrypoints;
- required scenarios cannot be skipped silently;
- inputs are registered;
- markers are stable;
- output is bounded;
- normal validation never updates gold;
- gold files have one authoritative scenario mapping.

---

# 34. Project configuration alignment

`project/project.toml` must represent this architecture.

Required domains include:

```text
project identity
source directory
source glob
GF path additions
entrypoints
checkpoints
required scenarios
optional scenarios
release entrypoints
expected artifacts
```

Architecture documents must not name an entrypoint absent from configuration.

Configuration must not name a module absent from source or documented planned status.

---

# 35. Checkpoint architecture

Checkpoints should follow dependency order.

Recommended checkpoint families:

```text
resources
morphology
categories
paradigms
noun
adjective
verb
sentence
question
relative
structural
lexicon
extensions
grammar-entrypoint
language-entrypoint
release
```

Use only applicable checkpoints.

## 35.1 Checkpoint contract

Each checkpoint must define:

```text
ID
modules
dependency prerequisites
required scenarios
release significance
owner
status
```

## 35.2 Ordering

A lower checkpoint should normally precede a higher entrypoint.

A skipped required lower checkpoint must not be hidden by a successful top-level compile.

---

# 36. Recommended module table

Replace this example with the active architecture.

| Layer | Module/path | Role | Direct providers | Main consumers | Status |
|---|---|---|---|---|---|
| Abstract | `<PATH>` | categories/functions | RGL/project abstract | concrete grammar | `<STATUS>` |
| Resource | `<PATH>` | common types/helpers | RGL resources | morphology/categories | `<STATUS>` |
| Morphology | `<PATH>` | inflection/stems | resource | paradigms/categories | `<STATUS>` |
| Categories | `<PATH>` | lincats/params | morphology/resource | syntax | `<STATUS>` |
| Paradigms | `<PATH>` | lexical constructors | morphology/categories | lexicon | `<STATUS>` |
| Noun | `<PATH>` | NP/CN syntax | categories/paradigms | grammar | `<STATUS>` |
| Verb | `<PATH>` | VP syntax | categories/morphology | sentence/grammar | `<STATUS>` |
| Sentence | `<PATH>` | clause/sentence | verb/categories | question/grammar | `<STATUS>` |
| Structural | `<PATH>` | closed-class items | paradigms/categories | grammar/lang | `<STATUS>` |
| Lexicon | `<PATH>` | open lexicon | paradigms | language entrypoint | `<STATUS>` |
| Extensions | `<PATH>` | optional families | core modules | coordinator/entrypoint | `<STATUS>` |
| Grammar | `<PATH>` | concrete grammar | core modules | language entrypoint/scenarios | `<STATUS>` |
| Language | `<PATH>` | grammar + lexicon | grammar/lexicon | API/release | `<STATUS>` |
| API | `<PATH_OR_NONE>` | public re-export | language/syntax | applications | `<STATUS>` |

---

# 37. Module naming rules

## 37.1 Filename/module agreement

For a source file:

```text
<ModuleName>.gf
```

the declared GF module name must match:

```text
<ModuleName>
```

according to GF rules.

## 37.2 Language suffix

Language-specific modules should use `<GF_SUFFIX>` consistently.

## 37.3 Generic helpers

A helper without the language suffix must be truly language-neutral or project-generic.

Language-specific behavior must not hide in a generic-looking module.

## 37.4 Retired names

Retired module names remain documented in migration notes when external consumers may reference them.

They must not be reused for unrelated semantics.

---

# 38. Public symbol rules

A symbol is public when another file references it.

Public elements include:

```text
module names
categories
functions
lincats
lin definitions through abstract contract
oper values
param values
resource interfaces
instances
constructor names
record fields
artifact names
scenario IDs
```

Public elements must have:

```text
one provider
known consumers
stable meaning
validation evidence
contract entry
```

---

# 39. Helper ownership

Shared helpers require a registry.

Recommended fields:

| Helper | Provider | GF type | Purpose | Consumers | Status |
|---|---|---|---|---|---|
| `<NAME>` | `<MODULE>` | `<TYPE>` | `<PURPOSE>` | `<CONSUMERS>` | `<STATUS>` |

Duplicate helper implementations are prohibited unless intentionally specialized.

Specializations must have distinct names or explicit class ownership.

---

# 40. Orthography ownership

Document:

```text
Orthography provider: <MODULE>
Token joining provider: <MODULE>
Capitalization policy: <POLICY>
Unicode policy: UTF-8
Apostrophe/hyphen policy: <POLICY>
Multiword handling: <POLICY>
```

Orthographic transformations shared across morphology or syntax must have one provider.

---

# 41. Agreement architecture

Document the language’s agreement dimensions:

```text
gender: <VALUES_OR_NONE>
number: <VALUES>
person: <VALUES_OR_NONE>
case: <VALUES_OR_NONE>
definiteness: <VALUES_OR_NONE>
animacy: <VALUES_OR_NONE>
honorific/register: <VALUES_OR_NONE>
other: <VALUES_OR_NONE>
```

For each dimension, identify:

```text
parameter provider
inherent versus contextual status
lincat fields
pattern consumers
default/fallback
validation scenario
```

Removing an agreement dimension is a breaking architecture change.

---

# 42. Case architecture

If the language has case, document:

```text
case values
provider
noun/pronoun/adjective realization
preposition government
syntax consumers
syncretism representation
unsupported distinctions
```

Do not infer lost case information later from realized strings.

Remove this section or mark not applicable when the language has no grammatical case in the project model.

---

# 43. Definiteness architecture

Document whether definiteness is realized through:

```text
noun inflection
determiner
article
adjective linker
clitic
syntax-only distinction
multiple coordinated layers
```

Identify one owner for selection and one owner for ordering.

Prevent double realization.

---

# 44. Tense, aspect, and mood architecture

Document:

```text
morphological versus analytic distinctions
auxiliary ownership
tense parameter provider
mood parameter provider
clause consumers
non-finite forms
unsupported forms
```

A syntax layer must not guess morphology through strings.

---

# 45. Voice and valency architecture

Document:

```text
active/passive/middle/reflexive representation
valency records
object case selection
slash/gap representation
causative/applicative strategy
lexical versus productive alternations
```

Changes to valency or gap structures affect many consumers and require coordinated migration.

---

# 46. Clitic architecture

If applicable, document:

```text
clitic categories
full versus clitic forms
ordering provider
host selection
attachment/joining
agreement
doubling
negation interaction
scenario coverage
```

Clitic ordering must have one provider.

Remove this section when not applicable.

---

# 47. Word-order architecture

Document the default and marked orders relevant to the grammar.

```text
basic clause order: <ORDER>
NP internal order: <ORDER>
adjective position: <ORDER>
adverb placement: <ORDER>
question formation: <STRATEGY>
relative formation: <STRATEGY>
clitic placement: <STRATEGY>
negation placement: <STRATEGY>
```

Word order normally belongs to syntax, not morphology or lexicon.

---

# 48. Punctuation architecture

Document which layer owns:

```text
sentence-final punctuation
question punctuation
comma insertion
coordination punctuation
quotation marks
spacing
token joining
```

Do not duplicate punctuation in both abstract trees and concrete syntax without policy.

---

# 49. Inheritance and RGL reuse

Document the reuse strategy:

```text
RGL modules inherited
RGL modules overridden
project modules extended
interfaces instantiated
families intentionally unsupported
```

## 49.1 Inheritance rule

Reuse RGL structure when it matches the language.

Do not inherit a default only because it compiles.

## 49.2 Override rule

An override must state:

```text
reason
original provider
new provider
affected consumers
behavioral difference
validation
```

## 49.3 Placeholder rule

Inherited placeholder or shallow behavior must be recorded in the status ledger.

---

# 50. Unsupported families

List intentional omissions.

| Family | Status | Reason | Impact | Release policy |
|---|---|---|---|---|
| `<FAMILY>` | unsupported/blocked | `<REASON>` | `<IMPACT>` | allowed/blocks |

An omitted abstract family must not be silently presented as implemented.

---

# 51. Temporary architecture

Temporary modules or shortcuts must state:

```text
temporary provider
intended final provider
consumers
limitations
removal condition
release impact
```

Examples requiring ledger entries:

```text
flattened Str placeholder
invariant morphology fallback
disabled lincat field
copied helper
hard-coded word order
empty realization
Predef.error branch
partial interface instance
```

---

# 52. Error and failure architecture

Provider failures should remain visible at their source.

Expected causal behavior:

```text
provider fails directly
→ consumer compile may fail downstream
→ entrypoint may fail downstream
→ scenarios may be blocked
```

GF Wordbench classification should distinguish:

```text
direct
downstream
ambiguous
```

A top-level entrypoint must not contain emergency local code merely to hide a lower-layer failure.

---

# 53. Determinism

Given the same:

```text
source bytes
GF version
RGL revision
project configuration
scenario input
normalization version
```

the project should produce equivalent structured validation results.

Potential nondeterminism must be documented:

```text
free word-order variants
unordered generation
ambiguity ordering
random generation
version-dependent diagnostics
```

Gold-backed scenarios must use deterministic or deliberately normalized output.

---

# 54. Source layout

Fill the canonical source layout.

```text
<SOURCE_DIR>/
├── <ABSTRACT_OR_INTERFACE_MODULE>.gf
├── <RESOURCE_MODULE>.gf
├── <MORPHOLOGY_MODULE>.gf
├── <CATEGORY_MODULE>.gf
├── <PARADIGMS_MODULE>.gf
├── <NOUN_MODULE>.gf
├── <VERB_MODULE>.gf
├── <SENTENCE_MODULE>.gf
├── <QUESTION_MODULE>.gf
├── <RELATIVE_MODULE>.gf
├── <STRUCTURAL_MODULE>.gf
├── <LEXICON_MODULE>.gf
├── <EXTEND_MODULE>.gf
├── <CONCRETE_ENTRYPOINT>.gf
├── <LANGUAGE_ENTRYPOINT>.gf
└── <API_ENTRYPOINT>.gf
```

Remove files that do not apply.

Add actual language-specific modules.

---

# 55. Project document ownership

| Document | Owns |
|---|---|
| `LANGUAGE_OVERVIEW.md` | linguistic/project overview |
| `LANGUAGE_ARCHITECTURE.md` | layers, ownership, dependency direction |
| `MODULE_DEPENDENCY_MAP.md` | exact module imports and consumers |
| `CATEGORY_AND_LINCAT_CONTRACT.md` | exact lincats, fields, params, symbols |
| `MORPHOLOGY_SPEC.md` | morphological behavior |
| `SYNTAX_AND_CONSTRUCTOR_RULES.md` | composition and constructor semantics |
| `VALIDATION_SPEC.md` | validation modes, checkpoints, scenarios, gates |
| `TEST_COVERAGE_MATRIX.md` | feature-to-evidence coverage |
| `STATUS_LEDGER.md` | incomplete/fallback status |
| `DECISION_LOG.md` | deliberate architectural choices |
| `KNOWN_ISSUES.md` | unresolved user-visible issues |
| `RELEASE_CRITERIA.md` | project release gates |
| `RESEARCH_EVIDENCE.md` | linguistic evidence and sources |
| `INTERFILE_CONTRACT_LOCK.md` | cross-file public boundaries |

One document should own each fact.

Other documents should link rather than duplicate incompatible tables.

---

# 56. Architecture ownership map

Complete this table.

| Responsibility | Authoritative provider | Main consumers | Contract ID | Status |
|---|---|---|---|---|
| Abstract syntax | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Core categories | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Shared resources | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Noun morphology | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Verb morphology | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Adjective morphology | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Pronouns | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Determiners | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Paradigm API | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Noun syntax | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Verb syntax | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Sentence syntax | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Question syntax | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Relative syntax | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Coordination | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Structural lexicon | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Open lexicon | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Extension coordinator | `<PATH>` | `<PATHS>` | `<ID>` | `<STATUS>` |
| Grammar entrypoint | `<PATH>` | scenarios/language | `<ID>` | `<STATUS>` |
| Syntax entrypoint | `<PATH_OR_NONE>` | API/users | `<ID_OR_NONE>` | `<STATUS>` |
| Language entrypoint | `<PATH>` | API/release | `<ID>` | `<STATUS>` |
| API entrypoint | `<PATH_OR_NONE>` | applications | `<ID_OR_NONE>` | `<STATUS>` |
| Release entrypoint | `<PATH_OR_SET>` | PGF builder | `<ID>` | `<STATUS>` |
| Final PGF | `<ARTIFACT>` | applications/release | `<ID>` | `<STATUS>` |

---

# 57. Dependency-map requirements

`MODULE_DEPENDENCY_MAP.md` must contain:

```text
every active module
module path
module declaration
direct imports
direct consumers
architectural layer
checkpoint
status
entrypoint reachability
```

It should identify:

```text
cycles
orphan modules
unused providers
higher-to-lower violations
lower-to-higher violations
test-only modules
release-reachable modules
```

The architecture document describes intended direction.

The dependency map records actual relationships.

---

# 58. Interfile contract alignment

Every cross-module public relationship needs a stable contract ID.

Recommended format:

```text
IFC-PROJ-<DOMAIN>-<NUMBER>
```

Domains may include:

```text
CONFIG
MODULE
ABSTRACT
CONCRETE
LINC
MORPH
SYNTAX
LEXICON
HELPER
EXTEND
STRUCTURAL
SCENARIO
GOLD
ENTRY
PGF
DOC
```

The contract entry must name:

```text
provider
consumers
public surface
request
response
GF type or artifact type
invariants
breaking changes
validation
last reviewed
```

---

# 59. Architecture validation

Architecture validation should include:

```text
project configuration validation
module existence
module/file-name consistency
import-direction review
cycle detection
entrypoint existence
checkpoint registry
scenario registry
scenario-to-entrypoint mapping
scenario-to-gold mapping
public helper ownership
lincat consumer review
stale language-identifier scan
documentation existence
compile checkpoints
GF load scenarios
missing-function inspection
parse scenarios
linearization scenarios
bounded generation
gold comparison
PGF build
manifest verification
```

---

# 60. Baseline validation

After project initialization, execute one baseline validation.

Record:

```text
run ID
framework version
GF version
RGL revision
source revision
project version
overall status
known direct failures
known blocked areas
entrypoint status
scenario status
PGF status
```

Store the baseline reference in:

```text
project/docs/STATUS_LEDGER.md
```

or the project’s designated baseline record.

---

# 61. Architecture change classes

## 61.1 Internal compatible change

Examples:

```text
private helper refactor
algorithm improvement preserving output
performance optimization
comment clarification
local test addition
```

Required:

```text
provider tests
consumer smoke validation when risk exists
```

## 61.2 Compatible public extension

Examples:

```text
new optional helper
new optional constructor
new optional scenario
new derivable field with safe initialization
new optional entrypoint
```

Required:

```text
provider update
consumer review
contract update
tests
documentation
project-version review
```

## 61.3 Breaking architecture change

Examples:

```text
module rename
ownership move
public symbol rename
constructor arity change
lincat-field change
parameter-value change
entrypoint change
scenario-ID change
gold-normalization change
expected-PGF rename
dependency-direction redesign
```

Required:

1. identify contract IDs;
2. record the decision;
3. list all providers and consumers;
4. update all affected files;
5. update project configuration;
6. update scenarios and gold intentionally;
7. update dependency map;
8. update architecture and lock;
9. run checkpoints;
10. run release validation;
11. update project version as appropriate.

---

# 62. Adding a module

Checklist:

```text
[ ] Architectural layer selected
[ ] Responsibility has one owner
[ ] Module name follows suffix policy
[ ] Direct providers identified
[ ] Direct consumers identified
[ ] Import direction is valid
[ ] Public symbols documented
[ ] Contract IDs assigned
[ ] Dependency map updated
[ ] project.toml checkpoint/entrypoint impact reviewed
[ ] Scenario coverage added
[ ] Status assigned
[ ] Direct compile passes
[ ] Downstream entrypoint compile passes
```

---

# 63. Removing a module

Checklist:

```text
[ ] No active consumer remains
[ ] Public contracts are retired or migrated
[ ] Imports removed
[ ] Entry points updated
[ ] project.toml updated
[ ] Scenarios updated
[ ] Gold updated intentionally
[ ] Dependency map updated
[ ] Status ledger updated
[ ] Decision log updated when public
[ ] PGF/release validation passes
```

A module name must not be reused for unrelated semantics immediately.

---

# 64. Moving ownership

Moving a public responsibility between modules is breaking.

Required:

```text
old provider
new provider
all consumers
compatibility adapter or coordinated migration
contract update
dependency map
tests
entrypoints
scenarios
gold
decision log
project-version review
```

Do not leave both providers active without a selection rule.

---

# 65. Adding a lincat field

Before adding:

```text
purpose
provider
consumers
mandatory/optional/derivable
initialization policy
default semantics
serialization/output impact
```

Required:

```text
all constructors updated
all pattern consumers reviewed
lincat contract updated
compile checkpoints
representative scenarios
```

A new mandatory field is usually breaking.

---

# 66. Adding a parameter value

A new `param` value can make existing tables incomplete.

Required:

```text
all tables reviewed
all patterns reviewed
all constructors reviewed
all scenario matrices reviewed
all gold outputs reviewed
```

Do not treat it as automatically compatible.

---

# 67. Adding a constructor

A public constructor must define:

```text
GF type
argument order
defaults
regularity assumptions
failure behavior
returned category
irregular alternative
consumers
validation
```

Add it to the public API inventory.

---

# 68. Adding an entrypoint

Required:

```text
role
imports
audience
project.toml registration
checkpoint
scenario
release significance
PGF impact
contract ID
```

An optional entrypoint must not become required implicitly.

---

# 69. Adding a scenario

Required:

```text
unique scenario ID
registered .gfs file
declared entrypoint
finite timeout
required markers
input registration
gold/assertion policy
mode membership
owner
coverage row
```

See:

```text
project/validation/scenarios/README.md
```

---

# 70. Status model

Every architecture component should use one of:

```text
stable
experimental
temporary
fallback
warning
blocked
disabled
retired
not-applicable
```

## 70.1 Stable

Implemented, tested, documented, and release-eligible.

## 70.2 Experimental

Implemented but compatibility or coverage is not final.

## 70.3 Temporary

Interim implementation with a replacement plan.

## 70.4 Fallback

Simplified behavior used when intended behavior is unavailable.

## 70.5 Warning

Usable with a documented limitation.

## 70.6 Blocked

Cannot progress because a prerequisite is unresolved.

## 70.7 Disabled

Present but intentionally unavailable.

## 70.8 Retired

No longer part of active architecture.

## 70.9 Not applicable

The language/project intentionally does not use the component.

---

# 71. Status propagation

A stable entrypoint cannot rely on an undocumented fallback in a required path.

A component’s effective release status is constrained by required dependencies.

Example:

```text
stable entrypoint
+ blocked required morphology
= release-blocked entrypoint
```

The status ledger must preserve this relationship.

---

# 72. Known issues

Architecture-significant known issues include:

```text
missing provider
duplicate ownership
lincat flattening
incomplete table
unsupported abstract family
entrypoint inconsistency
scenario gap
PGF build defect
GF-version incompatibility
RGL inheritance problem
```

Each issue must state whether it blocks release.

---

# 73. Research-driven architecture

Linguistic architecture decisions should cite evidence in:

```text
project/docs/RESEARCH_EVIDENCE.md
```

Examples:

```text
agreement inventory
case inventory
clitic order
article placement
word order
morphological class
dialect variant
orthographic transformation
```

A linguistic claim and an implementation choice are related but distinct.

---

# 74. Security boundaries

GF source and `.gfs` scripts are executable project inputs.

Architecture must prohibit:

```text
scenario shell escapes
writes outside owned run directories
secret reads
environment dumps
source modification during validation
gold modification during normal validation
implicit shell command construction
```

Generated source or lexicon tools require their own documented trust and provenance model.

---

# 75. Performance boundaries

Performance-sensitive architecture choices may include:

```text
table size
shared stems
compile checkpoints
module granularity
lexicon generation
scenario bounds
PGF size
```

Optimization must preserve:

```text
public GF types
semantic output
diagnostic evidence
deterministic validation
```

Do not flatten structures solely for compile speed without a measured, reviewed decision.

---

# 76. Portability

Project-owned paths must be relative to the project root.

Do not hard-code:

```text
C:\...
/home/...
developer usernames
GF installation path
RGL installation path
run directories
```

Machine-local values belong in application state or environment configuration.

---

# 77. Release architecture

A project release requires:

```text
configured release entrypoint
complete required checkpoints
complete required scenarios
reviewed gold
accepted known issues
built PGF
manifested artifacts
documented GF version
documented RGL revision
documented project/source revision
```

Architecture documentation must match the release graph.

---

# 78. Release dependency chain

Fill the release chain:

```text
<LOWEST_REQUIRED_CHECKPOINT>
→ <NEXT_CHECKPOINT>
→ <CONCRETE_ENTRYPOINT>
→ <LANGUAGE_ENTRYPOINT>
→ <RELEASE_ENTRYPOINT>
→ <EXPECTED_PGF>
→ <RELEASE_SCENARIOS>
→ <RELEASE_DECISION>
```

Every node must have evidence.

---

# 79. Release architecture table

| Release component | Provider | Required prerequisites | Evidence | Status |
|---|---|---|---|---|
| Core morphology | `<MODULE>` | `<PREREQS>` | compile/scenario | `<STATUS>` |
| Core categories | `<MODULE>` | `<PREREQS>` | compile | `<STATUS>` |
| Core syntax | `<MODULES>` | `<PREREQS>` | compile/scenario | `<STATUS>` |
| Structural vocabulary | `<MODULE>` | `<PREREQS>` | scenario | `<STATUS>` |
| Lexicon | `<MODULE>` | `<PREREQS>` | compile/scenario | `<STATUS>` |
| Grammar entrypoint | `<MODULE>` | checkpoints | compile/load | `<STATUS>` |
| Language entrypoint | `<MODULE>` | grammar/lexicon | compile | `<STATUS>` |
| PGF | `<ARTIFACT>` | release entrypoints | build/hash | `<STATUS>` |
| Required scenarios | `<IDS>` | entrypoint/PGF | result/gold | `<STATUS>` |

---

# 80. Architecture drift indicators

Probable drift exists when:

- a source module is absent from this architecture and the dependency map;
- two modules claim the same public responsibility;
- a lower layer imports a final entrypoint;
- a consumer uses an undocumented record field;
- a provider renames a symbol without consumer updates;
- a category is flattened locally to `Str`;
- a helper is copied into several modules;
- a scenario loads a different entrypoint than configuration;
- an entrypoint contains emergency morphology or syntax;
- an inherited placeholder is treated as stable;
- a required abstract function lacks a concrete implementation;
- a required checkpoint is omitted;
- a gold file has no scenario;
- an expected PGF name differs across docs/configuration/output;
- an active module retains a previous language suffix;
- a status ledger entry has no affected provider;
- the dependency map and imports disagree;
- a project document lists a module that no longer exists;
- an API entrypoint exports undocumented symbols;
- a new extension becomes release-required without review.

Every drift must be resolved by:

1. restoring the current contract; or
2. changing the architecture deliberately and updating all coordinated files.

---

# 81. Architecture review checklist

```text
[ ] Project identity is complete
[ ] No required placeholder remains
[ ] Language scope is explicit
[ ] Source directory is correct
[ ] Every active module has a layer
[ ] Every public responsibility has one provider
[ ] Dependency direction is consistent
[ ] No circular imports exist
[ ] Entrypoint hierarchy is accurate
[ ] Public lincats are documented
[ ] Public params are documented
[ ] Public constructors are documented
[ ] Helper ownership is explicit
[ ] Morphology ownership is explicit
[ ] Structural ownership is explicit
[ ] Extension ownership is explicit
[ ] Unsupported families are explicit
[ ] Temporary behavior is in the ledger
[ ] Checkpoints follow dependency order
[ ] Scenarios map to entrypoints
[ ] Gold maps to scenarios
[ ] Expected PGF matches project configuration
[ ] Baseline validation exists
[ ] Release graph is complete
```

---

# 82. Initialization procedure

## Step 1 — Copy the template

Create the active project from:

```text
templates/project/
```

Do not edit the reusable template to hold active-language facts.

## Step 2 — Set identity

Replace:

```text
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<GF_SUFFIX>
<PROJECT_ID>
<PROJECT_OWNER>
```

across project configuration, docs, scenarios, and source placeholders.

## Step 3 — Select the RGL architecture

Determine:

```text
abstract modules
concrete base
interfaces/instances
required module families
optional module families
entrypoint conventions
```

## Step 4 — Define layers

Complete the module and ownership tables in this document.

## Step 5 — Create/update source files

Ensure module filenames and declarations match.

## Step 6 — Configure `project.toml`

Register:

```text
source directory
GF path additions
entrypoints
checkpoints
scenarios
release artifacts
```

## Step 7 — Define exact contracts

Complete:

```text
CATEGORY_AND_LINCAT_CONTRACT.md
INTERFILE_CONTRACT_LOCK.md
MODULE_DEPENDENCY_MAP.md
```

## Step 8 — Record incomplete work

Complete:

```text
STATUS_LEDGER.md
KNOWN_ISSUES.md
```

## Step 9 — Define validation

Complete:

```text
VALIDATION_SPEC.md
TEST_COVERAGE_MATRIX.md
validation/scenarios/
validation/inputs/
validation/gold/
```

## Step 10 — Execute baseline

Run diagnostic validation and record the baseline.

## Step 11 — Remove template residue

Search for:

```text
<LANGUAGE_
<GF_
<SOURCE_
<PROJECT_
<ABSTRACT_
<CONCRETE_
<ENTRYPOINT
<STATUS>
<PATH>
<MODULE>
```

Resolve every required occurrence.

---

# 83. Placeholder audit

Recommended command concept:

```text
gf-wordbench project contracts check --strict
```

Until implemented, use a repository search.

PowerShell example:

```powershell
Get-ChildItem project -Recurse -File |
    Select-String -Pattern '<[A-Z][A-Z0-9_ -]*>'
```

Review results.

Do not replace legitimate mathematical or GF syntax mechanically.

---

# 84. Architecture baseline record

Fill after initialization:

```text
Baseline run ID: <RUN_ID>
Date: <YYYY-MM-DD>
GF Wordbench version: <VERSION>
GF version: <VERSION>
RGL revision: <REVISION>
Project source revision: <REVISION>
Overall status: <STATUS>
Lowest failing checkpoint: <CHECKPOINT_OR_NONE>
Release entrypoint status: <STATUS>
PGF status: <STATUS>
Known accepted gaps: <IDS_OR_NONE>
```

---

# 85. Architecture decision record

For a significant architecture choice, add an entry to:

```text
project/docs/DECISION_LOG.md
```

Required fields:

```text
decision ID
date
status
context
options
decision
consequences
affected modules
affected contracts
validation
review trigger
```

Examples:

```text
merge resource and category providers
use interface/instance architecture
represent definiteness in morphology
represent clitics in syntax
omit an RGL family
expose an API entrypoint
split the lexicon
```

---

# 86. Template maintenance rule

Changes to this reusable template must remain language-neutral.

Template changes must not:

- add an active-language module name;
- assume a particular case/gender system;
- assume a particular word order;
- assume a particular RGL family is implemented;
- make an optional layer mandatory without project-schema review;
- overwrite initialized active-project documentation.

A template change should be validated by initializing at least one minimal synthetic project.

---

# 87. Template compatibility

The template should declare compatibility with:

```text
GF Wordbench framework version
project.toml schema version
interfile contract version
scenario contract version
normalization version
```

Exact machine-readable compatibility fields belong in the template/project schema when formally added.

---

# 88. Related template files

```text
templates/project/README.md
templates/project/project.toml
templates/project/docs/00_PROJECT_START_HERE.md
templates/project/docs/LANGUAGE_OVERVIEW.md
templates/project/docs/MODULE_DEPENDENCY_MAP.md
templates/project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
templates/project/docs/MORPHOLOGY_SPEC.md
templates/project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md
templates/project/docs/VALIDATION_SPEC.md
templates/project/docs/TEST_COVERAGE_MATRIX.md
templates/project/docs/STATUS_LEDGER.md
templates/project/docs/DECISION_LOG.md
templates/project/docs/KNOWN_ISSUES.md
templates/project/docs/RELEASE_CRITERIA.md
templates/project/docs/RESEARCH_EVIDENCE.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/validation/README.md
templates/project/validation/scenarios/README.md
templates/project/validation/inputs/README.md
templates/project/validation/gold/README.md
```

---

# 89. Final initialization checklist

```text
[ ] Replace project identity placeholders
[ ] Define language scope
[ ] Define RGL reuse strategy
[ ] Define source directory
[ ] Define abstract entrypoint
[ ] Define concrete entrypoint
[ ] Define language entrypoint
[ ] Define API entrypoint or mark not applicable
[ ] Define release entrypoint
[ ] Define expected PGF
[ ] Assign every module to a layer
[ ] Assign every responsibility to one provider
[ ] Complete category/lincat contracts
[ ] Complete morphology ownership
[ ] Complete syntax ownership
[ ] Complete structural ownership
[ ] Complete lexicon ownership
[ ] Complete extension ownership
[ ] Complete interface/instance mapping
[ ] Complete dependency map
[ ] Configure entrypoints
[ ] Configure checkpoints
[ ] Configure scenarios
[ ] Configure release artifacts
[ ] Record unsupported families
[ ] Record incomplete/fallback behavior
[ ] Define scenario coverage
[ ] Define gold coverage
[ ] Run placeholder scan
[ ] Run module-existence check
[ ] Run import-direction review
[ ] Compile checkpoints
[ ] Compile entrypoints
[ ] Run scenarios
[ ] Build PGF
[ ] Record baseline run
[ ] Review release criteria
```

---

# 90. Final enforcement rule

A language project is architecturally initialized only when its source graph, configuration, contracts, validation, and documentation describe the same system.

> Every public responsibility must have one provider, every consumer must depend only on documented contracts, every dependency must flow in an approved direction, and every release-significant boundary must have evidence.

This template must not become a generic essay left unchanged in an active project.

It must become the project’s concrete architectural map.
