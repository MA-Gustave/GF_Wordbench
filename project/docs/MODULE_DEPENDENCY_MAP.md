# GF Wordbench Project — Module Dependency Map

**Document ID:** `GF-WB-PROJECT-MODULE-DEPENDENCY-MAP`  
**Status:** Normative project reference  
**Applies to:** The one active GF language project under `project/`  
**Target path:** `project/docs/MODULE_DEPENDENCY_MAP.md`  
**Owner:** Active project maintainers  
**Framework owner:** GF Wordbench maintainers  
**Canonical path base:** Active project root  
**Current concrete-inventory state:** Not established from the available active-project source inventory  
**Last structural review:** 2026-07-22  

---

## 1. Purpose

This document defines the dependency architecture of the active GF language project.

It records:

- every GF source module that belongs to the project;
- the architectural layer owned by each module;
- every important provider-to-consumer relationship;
- permitted import direction;
- prohibited import direction;
- entrypoints and checkpoints;
- scenario-to-entrypoint dependencies;
- scenario-to-input dependencies;
- scenario-to-gold dependencies;
- entrypoint-to-artifact dependencies;
- documentation-to-source contracts;
- validation evidence for each important edge;
- the procedure for detecting and resolving drift.

The dependency map is both:

1. a human-maintained architectural reference;
2. a release-verifiable inventory derived from actual project configuration and source imports.

It must never become a speculative diagram.

---

## 2. Core rule

> Every dependency recorded here must be supported by active configuration, a GF source import, a scenario registration, an artifact contract, or another explicit project contract.

The reverse rule is equally important:

> Every cross-file dependency that affects compilation, validation, scenarios, gold output, or release artifacts must appear here.

---

## 3. No-guess policy

Concrete project facts must come from authoritative project assets.

The dependency map must not invent:

- language identity;
- module suffix;
- source directory;
- module names;
- entrypoint names;
- checkpoint names;
- scenario IDs;
- gold filenames;
- PGF filenames;
- import edges;
- public helpers;
- lincat fields;
- RGL parent modules.

When an authoritative fact is unavailable, this document records the gap explicitly instead of inserting a placeholder or a plausible-looking example.

For the current documentation generation step, the available active-project contract material does not establish a completed concrete module inventory.

Therefore:

- the architectural layer model below is normative;
- the concrete inventory tables remain empty until derived from the active project;
- no language-specific module name is asserted here;
- release readiness requires the concrete inventory to be populated and verified.

---

## 4. Authoritative sources

Dependency facts are derived in this order.

### 4.1 Project configuration

```text
project/project.toml
```

Owns:

- project identity;
- source root;
- source glob;
- ordered entrypoints;
- ordered checkpoints;
- required scenarios;
- optional scenarios;
- release entrypoints;
- expected artifacts;
- configured GF path parts.

### 4.2 GF source files

```text
configured source root/**/*.gf
```

Own:

- module declaration;
- module kind;
- imported or inherited modules;
- opened modules;
- implemented abstract interface;
- extended parent modules;
- public symbols;
- concrete lincats and linearizations;
- source-level provider/consumer relationships.

### 4.3 Scenario registry

```text
project/project.toml
project/validation/scenarios/*.gfs
```

Owns:

- scenario IDs;
- script paths;
- loaded entrypoints;
- declared inputs;
- expected markers;
- output behavior;
- gold relationships.

### 4.4 Gold files

```text
project/validation/gold/*.gold
```

Own reviewed expected output for registered scenarios.

### 4.5 Project interfile contract lock

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Owns the current provider/consumer promises at project file boundaries.

### 4.6 Project architecture documents

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/VALIDATION_SPEC.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
```

Own architectural intent, structured category contracts, validation intent, temporary states, and durable project decisions.

### 4.7 Generated evidence

Current-run evidence may confirm the map:

```text
summary.json
manifest.json
raw compile evidence
scenario results
PGF artifacts
```

Generated evidence is not the source of project identity.

---

## 5. Source precedence

When sources disagree, use this procedure:

1. stop release-significant validation claims;
2. inspect `project.toml`;
3. inspect actual GF module declarations and imports;
4. inspect scenario scripts and registrations;
5. inspect the interfile contract lock;
6. inspect architecture and decision documents;
7. decide whether code or documentation is wrong;
8. update all affected assets as one coordinated change;
9. rerun validation;
10. record evidence.

Do not silently prefer whichever source is easiest to edit.

---

# 6. Dependency-map completeness

The map is complete only when all of the following are true:

```text
every configured source file is inventoried
every source module has one stable identity
every module has one architectural layer
every direct project import is represented
every entrypoint is represented
every checkpoint is represented
every registered scenario is represented
every scenario entrypoint is represented
every declared scenario input is represented
every required gold file is represented
every expected PGF artifact is represented
every documented public helper dependency is represented
every cross-module lincat dependency is represented
every deprecated edge has a migration target
every prohibited cycle check passes
```

A structurally valid document with an empty concrete inventory is not a complete active-project dependency map.

---

## 7. Completeness state

Canonical human state:

```text
Architecture defined; concrete inventory pending authoritative source extraction.
```

This is not a runtime validation status.

The release workflow must evaluate a dedicated dependency-map gate.

Recommended gate ID:

```text
dependency-map-complete
```

Required release result while the concrete inventory is absent:

```text
FAIL
```

Once extraction and review are complete:

```text
OK
```

An extraction or checker failure uses:

```text
ERROR
```

---

# 8. Dependency semantics

An edge is directed from provider to consumer.

Notation:

```text
PROVIDER -> CONSUMER
```

Meaning:

```text
The consumer depends on a public surface, artifact, identity, or behavior owned by the provider.
```

Example at role level:

```text
MORPHOLOGY_PROVIDER -> NOUN_IMPLEMENTATION
```

This does not assert an active module name.

It states the expected architectural relationship.

---

## 9. Direct dependency

A direct dependency exists when a consumer:

- imports a provider;
- opens a provider;
- extends a provider;
- instantiates a provider interface;
- implements an abstract provider;
- calls a provider’s public helper;
- depends on a provider’s public lincat field;
- loads a provider as a scenario entrypoint;
- compares output against a provider gold file;
- packages a provider entrypoint into an artifact.

Direct edges must be recorded individually.

---

## 10. Transitive dependency

A transitive dependency exists through one or more direct edges.

Example:

```text
MORPHOLOGY -> NOUN -> GRAMMAR -> LANGUAGE_ENTRYPOINT
```

The map records the direct edges.

A generated view may also display transitive reachability.

Do not replace direct edges with only a high-level transitive arrow.

---

## 11. External dependency

An external dependency targets a module not owned by the active project.

Examples:

- RGL abstract modules;
- RGL concrete modules;
- RGL resource modules;
- GF prelude modules;
- supported external lexicon resources.

External dependencies must record:

```text
external module identity
dependency purpose
minimum compatible GF/RGL policy
project consumers
validation evidence
```

External source files are not copied into the project inventory unless the project owns the copy.

---

## 12. Artifact dependency

Artifact edges connect source or execution providers to produced or consumed files.

Examples:

```text
SOURCE_MODULE -> GFO_ARTIFACT
RELEASE_ENTRYPOINT -> PGF_ARTIFACT
SCENARIO -> NORMALIZED_OUTPUT
SCENARIO -> GOLD_FILE
RUN -> MANIFEST
```

Artifact dependencies are distinct from GF import edges.

---

## 13. Documentation dependency

Documentation can be a provider when code or release review depends on a locked documented contract.

Examples:

```text
CATEGORY_AND_LINCAT_CONTRACT -> CATEGORY_IMPLEMENTATION
VALIDATION_SPEC -> REQUIRED_SCENARIO
STATUS_LEDGER -> TEMPORARY_FALLBACK
DECISION_LOG -> BREAKING_PROJECT_CHANGE
```

Documentation edges do not mean runtime import.

They mean governance dependency.

---

# 14. Architectural layers

The active project should assign every owned module to one primary layer.

Canonical role layers:

```text
L0 external foundations
L1 project resources and morphology
L2 category implementations and paradigms
L3 syntax, structural lexicon, extensions, and shared helpers
L4 grammar composition and syntax entrypoints
L5 language and API entrypoints
L6 validation scenarios and project inputs
L7 reviewed gold and release artifacts
```

A project may refine the layer model in `LANGUAGE_ARCHITECTURE.md`.

It must not reverse the dependency direction without an explicit reviewed project contract.

---

## 15. L0 — External foundations

Typical providers:

- GF prelude;
- RGL abstract grammar;
- RGL resource grammar;
- RGL interfaces;
- RGL paradigms;
- external Unicode or lexical resources approved by project policy.

Expected consumers:

```text
L1
L2
L3
L4
L5
```

Rules:

- project modules may depend on documented supported external modules;
- external modules do not depend on active project modules;
- version/capability assumptions are documented;
- local shadow copies are explicit project-owned providers;
- inherited behavior must not be silently duplicated.

---

## 16. L1 — Project resources and morphology

Responsibilities may include:

- inflection tables;
- agreement parameters;
- case, gender, number, person, tense, mood, or definiteness parameters;
- orthographic operations;
- stem formation;
- clitic or affix resources;
- morphology-specific records;
- low-level resource helpers.

Expected dependencies:

```text
L0 only
```

Expected consumers:

```text
L2
L3
possibly L4 through documented public resources
```

Prohibited:

```text
L1 -> L4 entrypoint
L1 -> L5 language/API entrypoint
L1 -> scenario
L1 -> gold
```

---

## 17. L2 — Category implementations and paradigms

Responsibilities may include:

- noun implementation;
- verb implementation;
- adjective implementation;
- adverb implementation;
- pronoun implementation;
- determiner implementation;
- preposition implementation;
- numeral implementation;
- conjunction implementation;
- category-specific paradigms.

Expected dependencies:

```text
L0
L1
documented peer interfaces
```

Expected consumers:

```text
L3
L4
L5 through composition
```

Rules:

- peer dependencies must be explicit;
- public lincat fields must be documented;
- category providers must not import top-level entrypoints;
- duplicate public morphology helpers are prohibited unless differentiated.

---

## 18. L3 — Syntax, structural, extension, and helper modules

Responsibilities may include:

- syntax constructors;
- sentence and clause composition;
- structural lexicon;
- extension constructors;
- project-wide helpers;
- compatibility instances;
- inherited RGL overrides;
- bounded language-specific augmentation.

Expected dependencies:

```text
L0
L1
L2
documented L3 peers
```

Expected consumers:

```text
L4
L5
scenarios through entrypoints
```

Rules:

- mutual L3 dependencies require cycle review;
- helper ownership must be unique;
- extension modules must document inherited parent modules;
- overrides must be intentional and validated;
- structural words must expose expected categories.

---

## 19. L4 — Grammar composition and syntax entrypoints

Responsibilities may include:

- concrete grammar composition;
- top-level syntax composition;
- grammar checkpoints;
- syntax checkpoints;
- composition of category, structural, and extension modules.

Expected dependencies:

```text
L0
L1
L2
L3
abstract counterpart
```

Expected consumers:

```text
L5
scenarios
PGF builder when configured as release entrypoint
```

Prohibited:

```text
L4 -> L5 consumer entrypoint
```

unless the project architecture explicitly defines L5 as a lower-level provider, which requires a documented layer revision.

---

## 20. L5 — Language and API entrypoints

Responsibilities may include:

- final language grammar;
- final language concrete;
- API surface;
- release entrypoint;
- public syntax entrypoint;
- final composition for PGF construction.

Expected dependencies:

```text
L0 through L4
```

Expected consumers:

```text
GF compiler
scenario runner
PGF builder
release workflow
external project users where explicitly supported
```

Rules:

- entrypoints must be configured;
- entrypoint imports must remain deterministic;
- release entrypoint identity is locked;
- entrypoint renames are breaking project migrations;
- lower layers must not import L5.

---

## 21. L6 — Scenarios and project inputs

Responsibilities:

- load configured entrypoints;
- exercise parse, linearize, generation, morphology, missing functions, and introspection contracts;
- consume declared input files;
- emit stable markers;
- produce normalized output;
- select gold-backed assertions.

Expected dependencies:

```text
configured L4 or L5 entrypoint
declared project inputs
scenario registry
GF shell contract
```

Prohibited:

- undocumented local source paths;
- arbitrary unregistered scripts;
- direct mutation of source or gold;
- hidden system-command dependencies;
- unbounded generation;
- reliance on stale compiled artifacts.

---

## 22. L7 — Gold and release artifacts

Includes:

- reviewed `.gold` files;
- generated `.gfo`;
- generated `.pgf`;
- normalized scenario outputs;
- gold diffs;
- manifests;
- release evidence.

Rules:

- gold is project source;
- generated artifacts are run-owned;
- normal validation never updates gold;
- PGF identity must match the configured release entrypoint;
- generated artifacts must not become hidden source dependencies;
- stale `.gfo` files must not mask current source failures.

---

# 23. Canonical dependency direction

Default expected direction:

```text
L0 external foundations
    -> L1 resources and morphology
    -> L2 category implementations
    -> L3 syntax, structural, extension, helpers
    -> L4 grammar composition and syntax entrypoints
    -> L5 language/API/release entrypoints
    -> L6 scenarios
    -> L7 normalized evidence, gold comparison, and release artifacts
```

Additional permitted edges:

```text
L0 -> L2
L0 -> L3
L0 -> L4
L0 -> L5
L1 -> L3
L1 -> L4 when explicitly documented
L2 -> L4
L2 -> L5 through explicit composition
L3 -> L5
L4 -> L6
L5 -> L6
L6 -> L7
L5 -> L7 for PGF
```

Every exception must be documented in the concrete edge registry.

---

# 24. Prohibited dependency direction

Default prohibited edges:

```text
L1 -> L4 entrypoint
L1 -> L5 entrypoint
L2 -> L5 API consumer merely for convenience
L2 -> L6 scenario
L3 -> L5 consumer that already imports L3
L4 -> L5 when L5 is defined as a higher layer
L5 -> lower layer through circular import
scenario -> undocumented source path
gold -> source generation logic
generated artifact -> source import
documentation -> runtime dynamic import
```

Also prohibited:

- circular project imports;
- hidden import through filename convention;
- importing a top-level grammar to obtain one helper;
- moving a helper upward to avoid a proper lower-level provider;
- using an API entrypoint as a resource library;
- duplicating a provider to break a cycle without recording the design decision;
- introducing an external dependency only through a developer’s local GF path;
- allowing a scenario to load a module absent from project configuration or its declared policy.

---

# 25. Cycle policy

Project-owned GF import cycles are prohibited.

A cycle includes:

```text
A -> B -> A
A -> B -> C -> A
```

Apparent inheritance or interface relationships must still be checked under GF semantics.

The checker must:

1. build direct project-owned edges;
2. normalize module identities;
3. ignore permitted non-import documentation edges for cycle analysis;
4. run strongly connected component detection;
5. report every component containing more than one project module;
6. report a self-import;
7. preserve the exact edge evidence.

A detected cycle causes:

```text
dependency-map gate = FAIL
```

A checker crash causes:

```text
dependency-map gate = ERROR
```

---

# 26. Module identity

Each GF source module is identified by:

```text
module_name
```

and mapped to:

```text
project-relative source path
```

Required invariants:

- one module declaration per source file;
- one project-relative path per owned module;
- no duplicate module name in the active source scope;
- filename/module-name relation follows project policy;
- module suffix agrees with project identity when applicable;
- canonical project paths use `/`;
- case collisions are rejected;
- symlink aliases do not create duplicate identity.

---

## 27. Module kind

Canonical descriptive kinds:

```text
abstract
concrete
resource
interface
instance
incomplete_concrete
extension
entrypoint
support
```

The exact GF declaration is preserved separately.

A module may have one primary kind and one architectural role.

Example at role level:

```text
kind = resource
layer = L1
role = morphology
```

Do not invent a new GF kind to express a project role.

---

## 28. Module role

Recommended project roles:

```text
abstract_categories
abstract_grammar
morphology
resource
paradigms
noun
verb
adjective
adverb
pronoun
determiner
preposition
numeral
conjunction
syntax
sentence
question
relative
structural
extend
lexicon
helper
grammar_entrypoint
syntax_entrypoint
language_entrypoint
api_entrypoint
release_entrypoint
```

A project may add roles.

Each added role requires a definition in `LANGUAGE_ARCHITECTURE.md`.

---

# 29. Concrete module inventory

The concrete inventory must be populated from actual active-project source files.

Current verified rows:

```text
None recorded.
```

Reason:

```text
The available documentation source does not provide a completed active-project
identity table or authoritative source-file inventory.
```

This statement is deliberate.

It is not a template placeholder.

---

## 30. Required inventory table

When populated, use:

| Module | Source path | GF kind | Layer | Primary role | Status | Checkpoint | Release entrypoint |
|---|---|---|---|---|---|:---:|:---:|
| No verified module rows yet | — | — | — | — | — | — | — |

Canonical module status for this registry:

```text
Active
Deprecated
Retired
```

Status meaning:

- `Active`: current owned project module;
- `Deprecated`: still present for compatibility, with a replacement plan;
- `Retired`: historical identity retained for migration/reference, not compiled as active source.

Do not use `Experimental` or `Planned` as final module lifecycle values.

Temporary or blocked implementation quality belongs in:

```text
project/docs/STATUS_LEDGER.md
```

---

# 31. Module inventory row rules

Every active row must include:

- exact GF module name;
- canonical project-relative source path;
- GF module kind;
- architectural layer;
- primary role;
- lifecycle status;
- checkpoint membership;
- release-entrypoint membership.

Optional columns may include:

- abstract counterpart;
- external parent;
- owner;
- notes;
- first introduced release;
- replacement module.

Do not place multiline contract prose inside the compact inventory.

Use the edge registry and interfile contract lock.

---

# 32. Direct import edge registry

Current verified project import edges:

```text
None recorded.
```

The registry must be populated from actual GF declarations and reviewed contracts.

Required table:

| Provider | Consumer | Edge kind | Public surface | Status | Evidence |
|---|---|---|---|---|---|
| No verified project import edges yet | — | — | — | — | — |

Canonical edge lifecycle:

```text
Active
Deprecated
Retired
```

---

## 33. Edge kinds

Canonical descriptive edge kinds:

```text
imports
opens
extends
implements
instantiates
uses_helper
uses_lincat
loads
reads_input
compares_gold
builds_artifact
documents
validates
```

These are documentation values.

If persisted for automation, they require a schema.

---

## 34. `imports`

Use when the consumer’s GF module declaration directly imports the provider.

Record the exact declaration evidence.

---

## 35. `opens`

Use when the consumer opens a provider namespace.

Opening creates a dependency even when no symbol use is immediately obvious.

---

## 36. `extends`

Use when a module extends or composes an inherited parent.

Record whether the provider is project-owned or external.

---

## 37. `implements`

Use for abstract-to-concrete relationships.

Record:

- abstract provider;
- concrete consumer/provider;
- category/lincat contract;
- required linearizations;
- validation evidence.

---

## 38. `instantiates`

Use for interface-to-instance relationships.

Record:

- interface;
- instance;
- parameter bindings;
- consumers of the instance.

---

## 39. `uses_helper`

Use when a consumer calls a documented public helper owned by another project module.

Private local helper use is not a map edge.

---

## 40. `uses_lincat`

Use when a consumer depends on a public lincat field or record shape from another module.

Every such edge must link to:

```text
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
```

---

## 41. `loads`

Use when a `.gfs` scenario loads or imports a configured entrypoint.

---

## 42. `reads_input`

Use when a scenario consumes a declared project input file.

---

## 43. `compares_gold`

Use when normalized scenario output is compared with a reviewed gold file.

---

## 44. `builds_artifact`

Use for:

```text
source -> gfo
entrypoint -> pgf
scenario -> normalized output
run -> manifest
```

---

## 45. `documents`

Use when a document defines a contract that maintainers and release review must follow.

This is not a runtime edge.

---

## 46. `validates`

Use when a checkpoint, scenario, or release gate supplies evidence for a provider/consumer edge.

---

# 47. External dependency registry

Current verified external module dependencies:

```text
None recorded.
```

Required table:

| External provider | Project consumers | Purpose | Version/capability policy | Status | Evidence |
|---|---|---|---|---|---|
| No verified external module rows yet | — | — | — | — | — |

External dependency status:

```text
Active
Deprecated
Retired
```

---

# 48. Abstract-to-concrete registry

Current verified relationships:

```text
None recorded.
```

Required table:

| Abstract provider | Concrete implementation | Categories covered | Required functions covered | Status | Evidence |
|---|---|---|---|---|---|
| No verified abstract/concrete rows yet | — | — | — | — | — |

A concrete implementation must not be considered complete solely because its file compiles.

Validation should include:

- missing-linearization inspection;
- representative linearization;
- project-specific category checks;
- entrypoint compilation;
- release PGF where required.

---

# 49. Public helper registry

Current verified public cross-module helpers:

```text
None recorded.
```

Required table:

| Provider | Helper | GF type | Consumers | Stability | Validation |
|---|---|---|---|---|---|
| No verified public helper rows yet | — | — | — | — | — |

Helper stability uses:

```text
Active
Deprecated
Retired
```

A helper not listed here and not listed in the interfile lock is treated as private.

A consumer must not depend on it.

---

# 50. Lincat dependency registry

Current verified cross-module lincat dependencies:

```text
None recorded.
```

Required table:

| Category/provider | Public fields or shape | Consumers | Status | Contract reference | Evidence |
|---|---|---|---|---|---|
| No verified lincat dependency rows yet | — | — | — | — | — |

A public field rename, removal, or type change is a breaking project contract change.

---

# 51. Entrypoint registry

Configured entrypoints must be copied exactly from `project.toml`.

Current verified entrypoints:

```text
None recorded.
```

Required table:

| Entrypoint | Source path | Kind | Purpose | Direct dependencies | Scenarios | Release role |
|---|---|---|---|---|---|---|
| No verified entrypoint rows yet | — | — | — | — | — | — |

Entrypoint order must match configuration order.

---

# 52. Checkpoint registry

Configured checkpoints must be copied exactly from `project.toml`.

Current verified checkpoints:

```text
None recorded.
```

Required table:

| Checkpoint ID | Module | Layer proven | Required dependencies | Required scenarios | Release significance |
|---|---|---|---|---|---|
| No verified checkpoint rows yet | — | — | — | — | — |

A checkpoint must prove a coherent architectural layer.

It must not be an arbitrary file chosen only because it compiles quickly.

---

# 53. Scenario dependency registry

Current verified scenarios:

```text
None recorded.
```

Required table:

| Scenario ID | Script | Loaded entrypoint | Inputs | Gold | Required modes | Status |
|---|---|---|---|---|---|---|
| No verified scenario rows yet | — | — | — | — | — | — |

Scenario lifecycle:

```text
Active
Deprecated
Retired
```

Optionality and required modes are separate fields.

---

# 54. Scenario edge rules

Every registered scenario must record:

- exact scenario ID;
- project-relative script path;
- loaded module or entrypoint;
- every declared input;
- every required marker section;
- gold path or no-gold policy;
- execution modes;
- required flag;
- normalization version;
- bounded-generation policy where applicable.

A scenario must not depend on a local developer-only module.

---

# 55. Gold dependency registry

Current verified gold relationships:

```text
None recorded.
```

Required table:

| Scenario ID | Gold file | Normalization version | Comparison type | Required | Status |
|---|---|---|---|:---:|---|
| No verified gold rows yet | — | — | — | — | — |

Gold lifecycle:

```text
Active
Deprecated
Retired
```

A retired gold file remains historical source evidence if retained.

It is not used by current normal validation.

---

# 56. Release artifact registry

Current verified release artifacts:

```text
None recorded.
```

Required table:

| Provider entrypoint | Artifact | Artifact kind | Required mode | Status | Validation |
|---|---|---|---|---|---|
| No verified release artifact rows yet | — | — | — | — | — |

Required artifact identity must match:

```text
project.toml
project interfile contract lock
release validation
scenario intent
manifest
release documentation
```

---

# 57. Documentation dependency registry

Active project documentation edges:

| Provider document | Consumers | Dependency |
|---|---|---|
| `project/docs/LANGUAGE_ARCHITECTURE.md` | source layout, this map, project lock | Defines intended layers and ownership |
| `project/docs/CATEGORY_AND_LINCAT_CONTRACT.md` | category providers, syntax modules, scenarios | Defines shared category and lincat promises |
| `project/docs/MODULE_DEPENDENCY_MAP.md` | maintainers, release review, classifier context | Defines provider/consumer graph |
| `project/docs/VALIDATION_SPEC.md` | project configuration, scenarios, gold, release | Defines required evidence |
| `project/docs/STATUS_LEDGER.md` | temporary code, known issues, release | Defines temporary and blocked implementation states |
| `project/docs/DECISION_LOG.md` | breaking project changes | Records durable project decisions |
| `project/docs/INTERFILE_CONTRACT_LOCK.md` | all project providers and consumers | Locks active cross-file promises |

These edges are active governance relationships.

---

# 58. Role-level architecture graph

The following graph is normative at the role level.

```text
EXTERNAL_GF_AND_RGL
    |
    +--> ABSTRACT_CATEGORIES
    |
    +--> PROJECT_RESOURCES
            |
            +--> MORPHOLOGY
                    |
                    +--> CATEGORY_IMPLEMENTATIONS
                            |
                            +--> PARADIGMS
                            |
                            +--> SYNTAX_CONSTRUCTORS
                            |
                            +--> STRUCTURAL_LEXICON
                            |
                            +--> EXTENSION_MODULES
                            |
                            +--> SHARED_HELPERS
                                    |
                                    +--> GRAMMAR_COMPOSITION
                                            |
                                            +--> SYNTAX_ENTRYPOINT
                                            |
                                            +--> LANGUAGE_ENTRYPOINT
                                                    |
                                                    +--> API_ENTRYPOINT
                                                    |
                                                    +--> RELEASE_ENTRYPOINT
                                                            |
                                                            +--> PGF_ARTIFACT

CONFIGURED_ENTRYPOINT
    |
    +--> REGISTERED_SCENARIOS
            |
            +--> DECLARED_INPUTS
            |
            +--> NORMALIZED_OUTPUT
                    |
                    +--> REVIEWED_GOLD
                    |
                    +--> GOLD_DIFF
```

The graph does not assert that every project requires every optional role.

Non-applicable roles may be absent.

---

# 59. Minimal project graph

A small valid project may contain:

```text
abstract provider
concrete implementation
language or release entrypoint
one load scenario
one release artifact
```

The map must reflect actual structure rather than forcing a large RGL-style layout.

---

# 60. Large project graph

A larger project may contain:

- multiple resource modules;
- multiple category modules;
- separate morphology and paradigms;
- structural lexicon;
- extension modules;
- syntax and grammar checkpoints;
- API entrypoint;
- multiple scenario suites;
- multiple external RGL interfaces.

The same direction and evidence rules apply.

---

# 61. Module extraction

A dependency extractor may inspect GF source declarations.

It must remain conservative.

Potential declaration forms include:

```gf
abstract ...
concrete ... of ...
resource ...
interface ...
instance ... of ...
incomplete concrete ...
```

The extractor may identify dependencies from declaration syntax such as:

```text
of
with
**
-
open
```

Exact parsing must follow supported GF syntax.

A regex-only extractor may provide candidate edges.

It must not claim full correctness when syntax is ambiguous.

---

# 62. Preferred extraction strategy

Recommended staged strategy:

```text
1. enumerate configured source files
2. decode UTF-8
3. mask strings and comments safely
4. parse module declaration
5. extract module identity
6. extract declared providers/imports
7. normalize project-owned versus external identity
8. build direct edge candidates
9. compare with documented contracts
10. report unresolved declarations
11. perform cycle detection
12. produce deterministic inventory
13. require human review before updating this document
```

GF itself remains authoritative for compilation semantics.

The dependency extractor is architectural tooling.

---

# 63. Import evidence

Each concrete import edge should preserve one or more evidence forms:

```text
source file
declaration line or normalized declaration excerpt
provider module
consumer module
edge kind
extraction method
review date
validation target
```

Line numbers may drift.

The source declaration remains primary.

---

# 64. Generated map updates

An automated command may propose updates.

Suggested future command:

```text
gf-wordbench project dependencies check
```

or:

```text
gf-wordbench project check
```

with dependency-map checks included.

A separate public command is unnecessary until a stable user workflow requires it.

Generated output must not overwrite this file silently.

Recommended workflow:

```text
extract
compare
show proposed diff
review
accept documentation update
run project checks
commit source and map together
```

---

# 65. Deterministic ordering

Concrete tables use:

```text
module inventory:
    layer
    then module name

direct edges:
    provider
    then consumer
    then edge kind

external dependencies:
    external provider
    then project consumer

entrypoints:
    project.toml declaration order

checkpoints:
    project.toml declaration order

scenarios:
    project.toml scenario order

gold:
    scenario order

artifacts:
    provider entrypoint
    then artifact path
```

Do not rely on filesystem enumeration order.

---

# 66. Canonical paths

Project-owned paths are:

- relative to the active project root;
- separated with `/`;
- free of drive letters;
- free of `..` after normalization;
- stable across developer machines.

Example structural path:

```text
src/module.gf
```

This is a path-form example, not an assertion about the current project layout.

Environment paths do not belong in concrete module inventory.

---

# 67. Case policy

Preserve declared module and path case for display.

Comparison must account for platform behavior.

Reject:

- two source paths that collide case-insensitively on supported Windows;
- two module identities differing only by unsupported case distinctions;
- a filename whose case disagrees with locked project policy;
- scenario references with inconsistent module case.

---

# 68. Missing module behavior

A configured source or entrypoint absent from disk causes:

```text
project check = FAIL
dependency-map gate = FAIL
```

A filesystem or decoding error causes:

```text
project check = ERROR
dependency-map gate = ERROR
```

Do not create the source directory automatically to hide the error.

---

# 69. Extra module behavior

A source module inside the configured source scope but absent from the concrete inventory causes:

```text
dependency-map gate = FAIL
```

The maintainer must decide whether to:

- add it to the map;
- exclude it through project configuration;
- retire/delete it;
- classify it as non-source noise.

---

# 70. Missing edge behavior

An actual direct project import absent from the edge registry causes:

```text
dependency-map gate = FAIL
```

A documented edge absent from source/configuration causes:

```text
dependency-map gate = FAIL
```

unless the edge is explicitly `Deprecated` during a migration window.

---

# 71. Unknown external module

An imported module that is neither project-owned nor in the approved external registry causes:

```text
project check = FAIL
```

or:

```text
ERROR
```

when toolchain resolution cannot determine identity reliably.

Do not approve it only because it exists on one developer machine.

---

# 72. Checkpoint dependency closure

Each checkpoint must have a dependency closure.

The closure includes:

- direct project providers;
- transitive project providers;
- approved external providers;
- required configuration;
- required scenarios;
- expected artifacts where applicable.

Checkpoint validation should prove the entire closure.

A checkpoint is not valid evidence if it passes only because stale `.gfo` files satisfy missing providers.

---

# 73. Entrypoint dependency closure

Each entrypoint must record:

```text
direct providers
transitive project providers
external providers
scenarios loading it
release artifacts built from it
```

A release entrypoint closure must contain every required active project module intended for the release surface.

Unintended omission is a release failure.

---

# 74. Scenario dependency closure

Each scenario closure includes:

```text
scenario script
loaded entrypoint
entrypoint transitive source closure
declared input files
normalization rules
gold file where applicable
produced artifacts
GF executable contract
```

A scenario is not independent evidence from the grammar it loads.

Its result remains a separate `ScenarioResult`.

---

# 75. Root-failure context

This map may support diagnostic reasoning.

Example role-level chain:

```text
MORPHOLOGY -> NOUN -> GRAMMAR -> LANGUAGE_ENTRYPOINT
```

If morphology fails and dependent modules fail, the classifier may use:

- GF diagnostic references;
- current failed result set;
- verified dependency edges.

The map is supporting evidence.

It must not override contradictory GF diagnostics silently.

A conflict produces:

```text
diagnostic_class = ambiguous
```

plus a warning or project drift finding.

---

# 76. No report-side dependency inference

Reports may display:

- direct providers;
- blockers;
- dependency paths;
- entrypoint closure.

Report writers must not parse GF source or rebuild the dependency graph.

They consume structured project/dependency evidence.

---

# 77. Change impact

When a provider changes, review:

```text
direct consumers
transitive entrypoints
affected checkpoints
affected scenarios
affected gold files
affected PGF artifacts
category/lincat contract
status ledger
decision log
interfile contract lock
this dependency map
```

A provider edit is incomplete until required consumers validate.

---

# 78. Module addition

Adding a module requires:

```text
[ ] source file added
[ ] module identity valid
[ ] project selection includes it
[ ] inventory row added
[ ] layer and role assigned
[ ] direct edges added
[ ] external dependencies added
[ ] public helpers/lincats documented
[ ] checkpoint impact reviewed
[ ] entrypoint closure reviewed
[ ] scenarios added or reviewed
[ ] project lock updated
[ ] validation evidence recorded
```

---

# 79. Module removal

Removing a module requires:

```text
[ ] all consumers identified
[ ] imports removed or migrated
[ ] entrypoint closures updated
[ ] checkpoints updated
[ ] scenarios updated
[ ] gold reviewed
[ ] project configuration updated
[ ] inventory status changed to Retired or row archived by policy
[ ] edge statuses updated
[ ] project lock updated
[ ] status ledger resolved
[ ] release evidence recorded
```

Do not delete the provider first and discover consumers through compilation failures.

---

# 80. Module rename

A module rename is a breaking project migration.

Required coordinated changes:

```text
filename
module declaration
all imports
all opens
all extends/instance relationships
project.toml
entrypoints
checkpoints
scenarios
gold headers or content where identity appears
artifact names where derived
documentation
dependency map
contract lock
decision log
release evidence
```

A rename appears as a retired identity and a new active identity when historical traceability is required.

---

# 81. Responsibility transfer

Moving public behavior from one provider module to another requires:

- explicit project decision;
- consumer migration;
- helper and lincat contract review;
- edge registry changes;
- checkpoint and scenario validation;
- deprecation period when compatibility is required.

Do not keep duplicate active providers indefinitely.

---

# 82. New dependency

Adding a direct edge requires:

```text
[ ] architectural direction allowed
[ ] provider public surface documented
[ ] consumer need documented
[ ] cycle check passes
[ ] edge registry updated
[ ] project lock updated when contract-significant
[ ] provider and consumer compile
[ ] downstream entrypoints validate
[ ] scenarios/gold reviewed
```

---

# 83. Dependency removal

Removing an edge requires proof that the consumer no longer depends on the provider.

Evidence:

- source declaration changed;
- consumer compiles from clean artifacts;
- entrypoint closure passes;
- relevant scenarios pass;
- no hidden helper/lincat dependence remains.

---

# 84. Deprecated dependency

A deprecated edge remains active for compatibility.

Required fields:

```text
Status = Deprecated
replacement provider or edge
affected consumers
earliest removal milestone
migration evidence
```

New consumers must not adopt the deprecated edge.

---

# 85. Retired dependency

A retired edge is historical.

It is not part of the active graph or cycle analysis.

Its identifier or row history may be retained for migration traceability.

---

# 86. Clean-build requirement

Dependency verification must not rely on stale generated files.

For release-significant checks:

- isolate current-run `.gfo`;
- clean or use a fresh artifact directory;
- record GF command and search path;
- ensure current source fingerprints correspond to produced artifacts;
- verify expected entrypoint and PGF artifact.

---

# 87. Validation evidence matrix

Each important edge should have one or more evidence kinds.

| Edge kind | Minimum evidence |
|---|---|
| Project import | Consumer compile from clean current sources |
| Abstract/concrete | Concrete compile plus missing-linearization scenario where applicable |
| Public helper | Provider compile, consumer compile, representative scenario |
| Lincat field | Provider and all direct consumers compile; category contract review |
| Entrypoint | Entrypoint compile/load |
| Scenario load | Scenario marker-complete execution |
| Gold comparison | Normalized actual/gold match |
| Release artifact | Current-run process success plus artifact existence/integrity |
| External module | GF version/path evidence plus consumer compile |
| Deprecated edge | Current compatibility test plus migration plan |

---

# 88. Validation modes

## 88.1 Quick

Quick mode validates one target and its available dependency context.

It cannot prove the complete map.

## 88.2 Checkpoint

Checkpoint mode validates a declared closure.

It can prove one architectural layer and its dependencies.

## 88.3 Release

Release mode validates:

- complete required inventory;
- every required entrypoint;
- every required scenario;
- required gold;
- release artifact;
- no prohibited cycles;
- dependency-map completeness.

## 88.4 Diagnostic

Diagnostic mode provides broad evidence and may compare the extracted graph with this document.

---

# 89. Dependency-map release gate

Recommended gate fields:

```text
gate_id = dependency-map-complete
required = true
status = OK | FAIL | ERROR
message
evidence
```

`OK` requires:

- complete concrete inventory;
- source/configuration agreement;
- no unexplained modules;
- no missing edges;
- no cycles;
- no forbidden directions;
- all entrypoints/checkpoints/scenarios represented;
- documentation links valid.

---

# 90. Checker algorithm

```python
def check_project_dependency_map(project):
    config = load_project_config(project)
    sources = enumerate_configured_sources(config)
    modules = extract_module_declarations(sources)
    source_edges = extract_dependency_edges(modules)
    documented = load_dependency_map(project)

    findings = []

    findings += compare_module_inventory(modules, documented.modules)
    findings += compare_edges(source_edges, documented.edges)
    findings += check_entrypoints(config, modules, documented)
    findings += check_checkpoints(config, modules, documented)
    findings += check_scenarios(config, documented)
    findings += check_gold(config, documented)
    findings += check_release_artifacts(config, documented)
    findings += check_cycles(source_edges)
    findings += check_direction_policy(source_edges, documented.layers)
    findings += check_contract_links(documented)

    return build_dependency_map_gate(findings)
```

The checker implementation may differ.

The behavior is normative.

---

# 91. Parser limitations

A dependency extractor must report uncertainty.

Examples:

- unsupported GF declaration form;
- preprocessor or generated source behavior;
- module aliasing;
- conditional inheritance;
- ambiguous operator use;
- external module not resolvable;
- incomplete concrete composition difficult to classify.

Uncertain extraction does not become a verified edge automatically.

Required action:

```text
manual review
```

and, when release-significant:

```text
gate = ERROR or FAIL according to evidence reliability
```

---

# 92. Documentation update workflow

```text
1. modify provider/consumer source
2. run dependency extraction/check
3. review proposed map changes
4. update this document
5. update interfile contract lock
6. update architecture/lincat documents
7. update scenarios and gold
8. clean-build provider and consumers
9. run checkpoints
10. run release validation when required
11. record evidence
12. commit coordinated change
```

---

# 93. Human review checklist

```text
[ ] Every module name matches its declaration
[ ] Every source path exists
[ ] Every module has one layer
[ ] Every module has one role
[ ] Every direct import edge is present
[ ] Every public helper edge is present
[ ] Every public lincat edge is present
[ ] Every external provider is approved
[ ] No cycle exists
[ ] No prohibited direction exists
[ ] Every entrypoint is configured
[ ] Every checkpoint proves a coherent closure
[ ] Every scenario loads a documented entrypoint
[ ] Every scenario input is declared
[ ] Every required gold exists
[ ] Every release artifact has one provider
[ ] Deprecated edges have replacement plans
[ ] Retired edges are absent from active execution
[ ] Documentation and source agree
```

---

# 94. Source-review checklist

For each changed GF module:

```text
[ ] Module declaration reviewed
[ ] Imported modules reviewed
[ ] Opened modules reviewed
[ ] Extended parents reviewed
[ ] Interface/instance relationships reviewed
[ ] Public helpers reviewed
[ ] Lincat dependencies reviewed
[ ] Direct consumers reviewed
[ ] Entrypoints reviewed
[ ] Scenarios reviewed
[ ] Gold impact reviewed
[ ] Dependency map updated
```

---

# 95. Scenario-review checklist

```text
[ ] Scenario ID is registered
[ ] Script path exists
[ ] Loaded entrypoint is active
[ ] Entrypoint appears in this map
[ ] Inputs are declared
[ ] Markers are stable
[ ] Generation is bounded
[ ] Gold relationship is documented
[ ] Normalization version is correct
[ ] No prohibited system command exists
[ ] Scenario result remains distinct from file results
```

---

# 96. Release-review checklist

```text
[ ] Concrete module inventory is non-empty
[ ] Inventory equals configured active source set
[ ] Every required entrypoint is active
[ ] Every required checkpoint is mapped
[ ] Every required scenario is mapped
[ ] Every required gold file is mapped
[ ] Expected PGF is mapped
[ ] Cycle check passes
[ ] Direction check passes
[ ] Clean build passes
[ ] Required scenarios pass
[ ] Gold comparisons pass
[ ] Manifest records release artifact
[ ] Dependency-map gate is OK
```

---

# 97. Test requirements

Recommended project tests:

```text
tests/project/
├── test_project_module_inventory.py
├── test_project_module_declarations.py
├── test_project_dependency_edges.py
├── test_project_dependency_cycles.py
├── test_project_dependency_direction.py
├── test_project_entrypoint_closure.py
├── test_project_checkpoint_closure.py
├── test_project_scenario_dependencies.py
├── test_project_gold_dependencies.py
├── test_project_release_artifacts.py
├── test_project_dependency_map_docs.py
└── test_project_dependency_map_determinism.py
```

---

# 98. Required test cases

## 98.1 Inventory

- configured source file present;
- extra source file;
- missing source file;
- duplicate module name;
- filename/module mismatch;
- case collision;
- Unicode path;
- Windows separator input;
- canonical `/` output.

## 98.2 Edges

- direct import present in map;
- source edge missing from map;
- documented edge missing from source;
- external edge approved;
- unknown external edge;
- helper edge;
- lincat edge;
- abstract/concrete edge;
- deprecated edge;
- retired edge excluded from active graph.

## 98.3 Cycles

- no cycle;
- two-node cycle;
- multi-node cycle;
- self-import;
- external/provider edge excluded correctly;
- documentation edge excluded correctly.

## 98.4 Direction

- allowed lower-to-higher edge;
- prohibited higher-to-lower edge;
- approved documented exception;
- entrypoint imported by resource;
- scenario undocumented path.

## 98.5 Closures

- checkpoint complete;
- checkpoint missing provider;
- entrypoint complete;
- entrypoint omits required active module;
- scenario closure complete;
- missing gold;
- release artifact mismatch.

---

# 99. Determinism

Equivalent source/configuration input must produce equivalent:

- module inventory;
- edge list;
- cycle findings;
- closure sets;
- checker messages;
- proposed document diff.

Do not include:

- filesystem discovery order;
- hash-randomized order;
- local absolute paths;
- current clock time in canonical graph data.

---

# 100. Security

Dependency extraction treats project files as untrusted text.

It must not:

- execute source;
- execute scenarios;
- follow arbitrary external paths;
- invoke shell commands;
- import Python code from the project;
- deserialize arbitrary objects;
- resolve symlinks outside approved roots silently.

Strict mode should reject path escapes through:

- symlink;
- junction;
- reparse point.

---

# 101. Privacy

The map contains project architecture.

It should not contain:

- developer usernames;
- workstation paths;
- secrets;
- tokens;
- private environment variables;
- complete GF search paths;
- raw diagnostic logs.

Project-relative paths are sufficient.

---

# 102. Version control

This document is project source.

Changes must be committed with the source/configuration change that caused them.

Do not generate it only inside run artifacts.

Review diffs carefully because they expose architectural changes.

---

# 103. Backward compatibility

Historical module identities may remain as `Retired` rows when needed for migration.

Canonical active graph excludes retired nodes and edges.

Deprecated nodes remain active until migration completes.

Changing:

- project ID;
- language code;
- module suffix;
- entrypoint name;
- scenario ID;
- gold filename;
- PGF identity;

requires project migration and compatibility review.

---

# 104. Relationship to `LANGUAGE_ARCHITECTURE.md`

`LANGUAGE_ARCHITECTURE.md` explains:

- architectural intent;
- layer responsibilities;
- category strategy;
- composition strategy.

This file records:

- concrete modules;
- concrete edges;
- concrete entrypoints;
- concrete checkpoints;
- concrete scenario/artifact dependencies.

When they disagree, release claims stop until corrected.

---

# 105. Relationship to `CATEGORY_AND_LINCAT_CONTRACT.md`

That document owns:

- category lincat shapes;
- public fields;
- agreement dimensions;
- shared structured values.

This file records which modules depend on those shapes.

It must not duplicate every field definition.

---

# 106. Relationship to the interfile contract lock

The project interfile lock owns contractual promises.

This file owns graph completeness and architectural direction.

Every important contract provider/consumer relationship should have a matching dependency edge.

Every important dependency edge that exposes a public contract should link back to the lock.

---

# 107. Relationship to `STATUS_LEDGER.md`

Temporary, fallback, warning, or blocked implementation states belong in the status ledger.

This map records lifecycle only as:

```text
Active
Deprecated
Retired
```

A module may be active while one of its implementations is temporarily blocked.

The status ledger explains that condition.

---

# 108. Relationship to `VALIDATION_SPEC.md`

The validation specification owns:

- required criteria;
- checkpoint purpose;
- scenario purpose;
- release acceptance.

This file connects those criteria to actual providers and consumers.

A required criterion without a mapped provider/evidence path is incomplete.

---

# 109. Relationship to reports

`summary.md` and `AI_READY.md` may link to this document.

They must not treat it as proof that the current source still agrees.

Current-run dependency-map checks provide that proof.

---

# 110. Current population action

Before this document can serve as a complete active-project map:

```text
[ ] complete project identity in project.toml
[ ] enumerate configured GF source files
[ ] extract module declarations
[ ] extract direct dependencies
[ ] classify project-owned and external modules
[ ] assign architectural layers
[ ] assign module roles
[ ] register entrypoints
[ ] register checkpoints
[ ] register scenarios
[ ] register gold files
[ ] register release artifacts
[ ] document public helpers
[ ] document lincat dependencies
[ ] run cycle and direction checks
[ ] align project interfile lock
[ ] replace the empty concrete tables with verified rows
[ ] record baseline validation evidence
```

No item may be checked solely from memory.

---

# 111. Completion evidence

When populated, add:

```text
Project configuration version
Source inventory fingerprint
Dependency extraction tool version
GF version used for validation
Baseline run ID
Review date
Reviewer
```

These are evidence metadata.

They do not replace the concrete rows.

---

# 112. Anti-drift indicators

Probable dependency drift exists when:

- a source module is missing from the inventory;
- the inventory lists a nonexistent source;
- module declaration and filename disagree;
- an import edge exists only in code;
- a documented edge no longer exists;
- a module imports a higher-level entrypoint;
- a cycle appears;
- a scenario loads an undocumented entrypoint;
- `project.toml` names an entrypoint absent from the map;
- a required scenario has no dependency row;
- a gold file has no scenario;
- a scenario has an undeclared input;
- an expected PGF has no provider entrypoint;
- a public helper is consumed but not registered;
- a lincat field is consumed but not registered;
- an external module is resolved only through a local environment;
- a deprecated edge has no replacement;
- a retired edge remains active in source;
- generated `.gfo` hides a missing source dependency;
- report prose claims a dependency not supported by structured evidence;
- concrete rows contain guessed language facts;
- placeholders remain in the active concrete inventory.

Any indicator requires correction before release-significant claims.

---

# 113. Change-control template

Every dependency-map change should identify:

```text
Changed provider:
Changed consumers:
Edge added/removed:
Layer impact:
Cycle impact:
Entrypoint impact:
Checkpoint impact:
Scenario impact:
Gold impact:
Artifact impact:
External dependency impact:
Contract impact:
Compatibility impact:
Validation evidence:
```

---

# 114. Implementation completion checklist

```text
[ ] active project identity is authoritative
[ ] source root is authoritative
[ ] concrete module inventory is populated
[ ] every source module is listed
[ ] every module role is assigned
[ ] every direct project edge is listed
[ ] external dependencies are listed
[ ] abstract/concrete edges are listed
[ ] helper edges are listed
[ ] lincat edges are listed
[ ] entrypoints are listed
[ ] checkpoints are listed
[ ] scenarios are listed
[ ] gold relationships are listed
[ ] release artifacts are listed
[ ] role graph matches architecture
[ ] no cycle exists
[ ] no prohibited direction exists
[ ] clean-build evidence exists
[ ] scenario evidence exists
[ ] gold evidence exists
[ ] PGF evidence exists where required
[ ] project lock agrees
[ ] status ledger agrees
[ ] validation spec agrees
[ ] release gate is OK
```

---

# 115. Related documents

```text
project/project.toml
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/INTERFILE_CONTRACT_LOCK.md
project/docs/VALIDATION_SPEC.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
project/validation/scenarios/
project/validation/gold/
docs/projects/PROJECT_MODEL.md
docs/projects/PROJECT_DIRECTORY_LAYOUT.md
docs/validation/COMPILATION_VALIDATION.md
docs/validation/SCENARIO_VALIDATION.md
docs/diagnostics/DIRECT_AND_DOWNSTREAM_FAILURES.md
docs/gf/GF_MODULE_COMPILATION.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/reference/STATUS_VALUES.md
docs/development/BACKWARD_COMPATIBILITY.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
SECURITY.md
```

---

# 116. Final rule

A dependency map is useful only when it matches the project that actually compiles and runs.

Therefore:

> Derive concrete nodes and edges from authoritative configuration and source, preserve the intended lower-to-higher architecture, reject cycles and hidden dependencies, connect every important edge to validation evidence, and never fill an active project map with guessed module names.
