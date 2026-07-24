# <LANGUAGE_NAME> — Module Dependency Map

**Document ID:** `GF-WB-PROJECT-MODULE-DEPENDENCY-MAP`  
**Document role:** Normative project template  
**Decision status:** Accepted template contract  
**Implementation status:** Template available; active-project implementation depends on initialization  
**Verification status:** Requires placeholder, source, contract and validation checks after initialization  
**Applies to:** One initialized GF Wordbench project  
**Template owner:** GF Wordbench  
**Project owner:** `<PROJECT_OWNER>`  
**Project ID:** `<PROJECT_ID>`  
**Language:** `<LANGUAGE_NAME>`  
**Language code:** `<LANGUAGE_CODE>`  
**Module suffix:** `<MODULE_SUFFIX>`  
**Project root:** `<PROJECT_ROOT>`  
**Source root:** `<SOURCE_ROOT>`  
**Last reviewed:** `<YYYY-MM-DD>`  
**Map version:** `1.0.0`

**Normative counterparts:**
- `project/project.toml`
- `project/docs/INTERFILE_CONTRACT_LOCK.md`
- `project/docs/LANGUAGE_ARCHITECTURE.md`
- `project/docs/CATEGORY_AND_LINCAT_CONTRACT.md`
- `project/docs/MORPHOLOGY_SPEC.md`
- `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md`
- `project/docs/VALIDATION_SPEC__PROJECT_DOCS.md`
- `project/docs/TEST_COVERAGE_MATRIX__PROJECT_DOCS.md`
- `project/docs/STATUS_LEDGER__PROJECT_DOCS.md`
- `project/docs/DECISION_LOG.md`
- `project/docs/RELEASE_CRITERIA__PROJECT_DOCS.md`

---

## 1. Purpose

This document records the active project's complete GF module dependency graph.

It identifies:

- every project-owned GF module;
- every external GF or RGL module imported by project code;
- every direct import edge;
- every inheritance, interface, instance, and extension relationship;
- module layers;
- public providers and consumers;
- configured checkpoints;
- configured release entrypoints;
- scenario-to-entrypoint dependencies;
- expected `.gfo` and `.pgf` artifacts;
- dependency-related validation evidence;
- prohibited or exceptional dependency directions.

This map exists to prevent a change in one module from being reviewed as though it affected only that file.

> A provider change is complete only after every direct consumer, downstream checkpoint, release entrypoint, scenario, and affected gold has been reviewed.

---

## 2. Template completion rule

This file is a template.

Before the project becomes release-ready:

- replace every required `<PLACEHOLDER>`;
- delete non-applicable example rows;
- add every active project module;
- verify every direct import against source;
- document every RGL inheritance relationship;
- identify every configured checkpoint and entrypoint;
- record every scenario entrypoint;
- review the graph for cycles and forbidden directions;
- link every release-significant module to validation evidence.

A project must not ship this file with unresolved required placeholders.

---

## 3. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **MODULE**: one GF source module.
- **PROVIDER**: module exposing a category, function, lincat, helper, paradigm, lexicon entry, or entrypoint.
- **CONSUMER**: module importing, inheriting, opening, instantiating, extending, or otherwise relying on a provider.
- **DIRECT DEPENDENCY**: dependency stated directly by a module declaration or import/open relationship.
- **TRANSITIVE DEPENDENCY**: dependency reached through one or more direct edges.
- **EXTERNAL DEPENDENCY**: GF or RGL module outside the active project source root.
- **ENTRYPOINT**: top-level module used for loading, public syntax/API use, PGF construction, or release validation.
- **CHECKPOINT**: configured module whose successful validation proves a coherent project layer.
- **LEAF MODULE**: project module with no project-owned consumers.
- **ROOT PROVIDER**: low-level module with no project-owned dependencies or only external dependencies.
- **LAYER**: architectural group with one expected dependency direction.
- **EDGE**: one directed dependency from consumer to provider.
- **CYCLE**: path that returns to its starting module.
- **OPTIONAL EDGE**: dependency active only under an explicitly documented variant or feature.
- **BLOCKED EDGE**: declared dependency whose provider is incomplete or unavailable.
- **VALIDATED EDGE**: dependency covered by compilation or scenario evidence.
- **DRIFT**: disagreement between source imports, project configuration, documentation, or validation behavior.

---

## 4. Dependency direction convention

Tables in this document use:

```text
consumer → provider
```

Meaning:

```text
ConsumerModule imports, inherits, opens, instantiates, extends,
or otherwise depends on ProviderModule.
```

Architectural flow diagrams may use:

```text
low-level provider
    ↓
higher-level consumer
```

The arrow convention must be stated whenever a diagram differs from the table convention.

---

## 5. Project identity

| Field | Value |
|---|---|
| Project ID | `<PROJECT_ID>` |
| Display name | `<PROJECT_NAME>` |
| Language | `<LANGUAGE_NAME>` |
| Language code | `<LANGUAGE_CODE>` |
| Module suffix | `<MODULE_SUFFIX>` |
| Project root | `<PROJECT_ROOT>` |
| Source root | `<SOURCE_ROOT>` |
| Abstract syntax root | `<ABSTRACT_ROOT_OR_MODULE>` |
| Grammar entrypoint | `<GRAMMAR_ENTRYPOINT>` |
| Syntax/API entrypoint | `<SYNTAX_ENTRYPOINT_OR_NONE>` |
| Language/API entrypoint | `<LANGUAGE_ENTRYPOINT_OR_NONE>` |
| Expected PGF | `<EXPECTED_PGF_OR_NONE>` |

All values must agree with:

```text
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
```

---

## 6. Source inventory authority

The canonical source inventory comes from:

```toml
[sources]
directory = "<SOURCE_ROOT>"
glob = "<SOURCE_GLOB>"
include_regex = "<INCLUDE_REGEX>"
exclude_regex = "<EXCLUDE_REGEX>"
```

The dependency map must include every selected project-owned `.gf` file.

It must not include:

- generated `.gfo`;
- generated `.pgf`;
- editor backups;
- copied source files excluded by project policy;
- temporary disabled modules unless they remain project-significant and are marked;
- run-directory artifacts.

---

## 7. Dependency kinds

Use one or more of these canonical dependency kinds.

| Kind | Meaning |
|---|---|
| `import` | Direct module import or composition dependency |
| `open` | Opens names from another module |
| `inherit` | Concrete/resource/interface inheritance |
| `instance` | Instantiates a GF interface |
| `interface` | Implements or consumes an interface contract |
| `extend` | Extends or overrides an inherited module |
| `abstract-implements` | Concrete implements an abstract module |
| `lincat-consumer` | Reads category/lincat fields owned by provider |
| `helper-consumer` | Calls public `oper` or constructor owned by provider |
| `paradigm-consumer` | Uses morphology/paradigm constructors |
| `lexicon-consumer` | Imports lexical entries |
| `structural-consumer` | Imports structural/closed-class entries |
| `entrypoint-member` | Included in a top-level entrypoint |
| `scenario-load` | Scenario loads entrypoint |
| `pgf-input` | Module is a configured PGF input |
| `validation-prerequisite` | Checkpoint/scenario requires provider to pass |
| `optional` | Dependency exists only for a documented optional feature |
| `external` | Provider is outside active project source |
| `tooling-only` | Used only by validation fixtures, never release entrypoints |

Do not use a generic `depends` label when a more precise kind is known.

---

## 8. Module layer model

Expected default direction:

```text
external GF/RGL
        ↓
interfaces and low-level resources
        ↓
morphology and paradigms
        ↓
category/lincat provider
        ↓
lexicon and structural modules
        ↓
core syntax modules
        ↓
extension/coordinator modules
        ↓
grammar, syntax, and language entrypoints
        ↓
scenarios and PGF release build
```

A project may use a different architecture.

Any difference must be explicit in `LANGUAGE_ARCHITECTURE.md`.

---

## 9. Layer registry

Complete this table before filling the edge map.

| Layer ID | Layer name | Purpose | Allowed dependencies | Prohibited dependencies | Representative modules |
|---|---|---|---|---|---|
| `L00` | External GF/RGL | Upstream abstract APIs, resources, shared libraries | Upstream only | Project modules | `<RGL_MODULES>` |
| `L10` | Interfaces/resources | Shared types, parameters, utilities | `L00` | Syntax/entrypoints | `<RESOURCE_MODULES>` |
| `L20` | Morphology/paradigms | Inflection, stems, lexical constructors | `L00-L10` | Syntax entrypoints | `<MORPHOLOGY_MODULES>` |
| `L30` | Category/lincat | Concrete category representations | `L00-L20` | Final entrypoints | `<CATEGORY_MODULES>` |
| `L40` | Lexicon/structural | Lexical and closed-class providers | `L00-L30` | Final entrypoints except through documented composition | `<LEXICON_STRUCTURAL_MODULES>` |
| `L50` | Core syntax | Phrase/clause constructors | `L00-L40` | Final entrypoints as providers | `<SYNTAX_MODULES>` |
| `L60` | Extensions/coordinators | Overrides, additions, project extensions | `L00-L50` | Test-only providers | `<EXTENSION_MODULES>` |
| `L70` | Entrypoints | Grammar, syntax, API, language modules | `L00-L60` | Scenarios, generated output | `<ENTRYPOINT_MODULES>` |
| `L80` | Validation fixtures | GF fixture modules used only by tests | Explicit validated project modules | Release entrypoints unless declared | `<FIXTURE_MODULES_OR_NONE>` |

Delete or add layers as required.

---

## 10. Complete module inventory

Every project-owned module appears exactly once.

| Module ID | File | GF module name | Kind | Layer | Status | Public role | Configured checkpoint | Configured entrypoint |
|---|---|---|---|---|---|---|---|---|
| `MOD-001` | `<SOURCE_ROOT>/<MODULE>.gf` | `<MODULE>` | `resource` | `L10` | `<Active/Deprecated/Retired>` | `<ROLE>` | `no` | `no` |
| `MOD-002` | `<SOURCE_ROOT>/<MODULE>.gf` | `<MODULE>` | `concrete` | `L30` | `<STATUS>` | `<ROLE>` | `<yes/no>` | `<yes/no>` |

### 10.1 Allowed module kinds

Recommended values:

```text
abstract
concrete
resource
interface
instance
morphology
paradigm
category
syntax
extension
structural
lexicon
grammar-entrypoint
syntax-entrypoint
language-entrypoint
fixture
other
```

### 10.2 Inventory invariants

- module IDs are unique;
- paths are project-relative;
- GF module names are unique;
- every selected `.gf` file appears;
- checkpoint flags agree with `project.toml`;
- entrypoint flags agree with `project.toml`;
- retired modules are not imported by active release modules;
- fixture modules are not imported by release entrypoints unless explicitly approved.

---

## 11. External dependency inventory

List every external GF/RGL module directly referenced by project modules.

| External ID | GF/RGL module | Source identity | Purpose | Direct project consumers | Compatibility evidence |
|---|---|---|---|---|---|
| `EXT-001` | `<RGL_MODULE>` | `<RGL_TAG_COMMIT_OR_HASH>` | `<PURPOSE>` | `<MODULES>` | `<GF_CHECK_OR_SCENARIO>` |

### 11.1 External identity

Record the strongest available identity:

```text
release tag
Git commit
distribution manifest
directory manifest hash
explicit label with selected fingerprints
UNKNOWN
```

Do not invent an upstream version.

### 11.2 External dependency drift

Review the complete map when:

- GF version changes;
- RGL identity changes;
- imported RGL module changes;
- inherited interface changes;
- an upstream symbol is overridden locally;
- an upstream module is retired.

---

## 12. Direct dependency edge registry

Every direct edge appears once.

| Edge ID | Consumer module | Provider module | Kind | Imported/public surface | Required/optional | Status | Validation |
|---|---|---|---|---|---|---|---|
| `EDGE-001` | `<CONSUMER>` | `<PROVIDER>` | `import` | `<MODULE_OR_SYMBOLS>` | `required` | `Active` | `<CHECKPOINT/SCENARIO>` |
| `EDGE-002` | `<CONSUMER>` | `<RGL_PROVIDER>` | `inherit external` | `<INTERFACE_OR_MODULE>` | `required` | `Active` | `<COMPILE_TARGET>` |

### 12.1 Edge requirements

Each edge must identify:

- exact consumer;
- exact provider;
- dependency kind;
- public surface relied upon;
- whether required;
- current status;
- validation evidence.

### 12.2 Public surface

For release-significant edges, identify the consumed surface:

```text
module identity
category names
abstract functions
lincat fields
parameters
public oper
constructor
paradigm
lexical entries
entrypoint
```

Detailed lincat field ownership remains in `CATEGORY_AND_LINCAT_CONTRACT.md`.

---

## 13. Module declaration registry

Record the relevant GF declaration form.

| Module | Declaration form | Abstract/interface parent | Inherited modules | Opened modules | Local overrides |
|---|---|---|---|---|---|
| `<MODULE>` | `resource/concrete/instance/...` | `<PARENT_OR_NONE>` | `<MODULES>` | `<MODULES>` | `<SYMBOLS_OR_NONE>` |

This table is especially important for:

- concrete modules;
- interface/instance pairs;
- `**` inheritance;
- `with` substitutions;
- `open` declarations;
- local override/subtraction behavior.

---

## 14. Abstract-to-concrete map

| Abstract module | Concrete module | Language | Complete | Missing-function evidence | Release entrypoint |
|---|---|---|---|---|---|
| `<ABSTRACT>` | `<CONCRETE>` | `<LANGUAGE_CODE>` | `<yes/no/partial>` | `<SCENARIO_OR_ARTIFACT>` | `<ENTRYPOINT>` |

### 14.1 Invariants

- every release concrete maps to the intended abstract module;
- concrete category/function types match abstract declarations;
- partial concretes declare omissions;
- missing functions remain visible;
- scenarios identify the entrypoint they load.

---

## 15. Interface and instance map

| Interface | Instance | Parameters/substitutions | Direct consumers | Status | Validation |
|---|---|---|---|---|---|
| `<INTERFACE>` | `<INSTANCE>` | `<WITH_SUBSTITUTIONS>` | `<MODULES>` | `<STATUS>` | `<COMPILE/SCENARIO>` |

### 15.1 Required review

A change to an interface requires review of:

- every instance;
- every module consuming the interface;
- every inherited concrete/syntax module;
- entrypoints;
- scenarios.

---

## 16. Category/lincat dependency map

| Category provider | Category/lincat | Fields/parameters consumed | Consumer modules | Contract reference | Validation |
|---|---|---|---|---|---|
| `<CAT_MODULE>` | `<NP>` | `<s, a, ...>` | `<NOUN/SENTENCE/...>` | `<CONTRACT_ID>` | `<COMPILE/SCENARIO>` |

### 16.1 Rule

A consumer must not read an undocumented record field, table shape, or parameter value.

### 16.2 Field change impact

When a field changes, review every consumer listed here and in the interfile lock.

---

## 17. Morphology and paradigm map

| Provider | Public helper/paradigm | Direct consumers | Lexical categories | Status | Validation |
|---|---|---|---|---|---|
| `<MORPHOLOGY_MODULE>` | `<HELPER>` | `<PARADIGM/LEXICON/STRUCTURAL>` | `<N/V/A/...>` | `<STATUS>` | `<MORPHOLOGY_SCENARIO>` |

### 17.1 Invariants

- paradigms do not duplicate morphology logic without justification;
- public helpers have documented input contracts;
- incomplete paradigms are explicit;
- normalization/orthography behavior has one owner;
- lexicon modules use approved paradigms.

---

## 18. Syntax-family dependency map

| Syntax family | Provider module | Direct lower-level providers | Direct higher-level consumers | Checkpoint | Scenario coverage |
|---|---|---|---|---|---|
| Noun phrase | `<NOUN_MODULE>` | `<CAT, MORPHOLOGY, STRUCTURAL>` | `<GRAMMAR, SYNTAX_ENTRYPOINT>` | `<CHECKPOINT>` | `<SCENARIOS>` |
| Verb phrase | `<VERB_MODULE>` | `<CAT, MORPHOLOGY>` | `<SENTENCE, GRAMMAR>` | `<CHECKPOINT>` | `<SCENARIOS>` |
| Clause/sentence | `<SENTENCE_MODULE>` | `<CAT, NOUN, VERB>` | `<GRAMMAR>` | `<CHECKPOINT>` | `<SCENARIOS>` |
| Questions | `<QUESTION_MODULE>` | `<CAT, SENTENCE>` | `<GRAMMAR>` | `<CHECKPOINT>` | `<SCENARIOS>` |
| Relatives | `<RELATIVE_MODULE>` | `<CAT, SENTENCE>` | `<GRAMMAR>` | `<CHECKPOINT>` | `<SCENARIOS>` |
| Coordination | `<CONJUNCTION_MODULE>` | `<CAT, STRUCTURAL>` | `<GRAMMAR>` | `<CHECKPOINT>` | `<SCENARIOS>` |
| Extensions | `<EXTEND_MODULE>` | `<CORE_SYNTAX>` | `<GRAMMAR/SYNTAX>` | `<CHECKPOINT>` | `<SCENARIOS>` |

Delete non-applicable families.

---

## 19. Structural and lexicon dependency map

| Provider | Kind | Consumers | Public categories/symbols | Release significance | Validation |
|---|---|---|---|---|---|
| `<STRUCTURAL_MODULE>` | `structural` | `<MODULES>` | `<PRONOUNS/PREPOSITIONS/...>` | `<blocking/non-blocking>` | `<SCENARIOS>` |
| `<LEXICON_MODULE>` | `lexicon` | `<LANGUAGE_ENTRYPOINT/SCENARIOS>` | `<LEXICAL_ENTRIES>` | `<blocking/non-blocking>` | `<SCENARIOS>` |

### 19.1 Rule

Consumer modules must not reconstruct structural entries independently when the structural provider owns them.

---

## 20. Extension and override map

| Extension module | Upstream provider | Symbol | Action | Local reason | Consumers | Status | Validation |
|---|---|---|---|---|---|---|---|
| `<EXTEND_MODULE>` | `<RGL_OR_PROJECT_MODULE>` | `<SYMBOL>` | `inherit/override/subtract/add` | `<REASON>` | `<ENTRYPOINTS>` | `<STATUS>` | `<SCENARIO>` |

### 20.1 Invariants

- inherited behavior remains inherited unless override is justified;
- every override/subtraction is listed;
- abstract signatures remain compatible;
- temporary overrides have status-ledger entries;
- no duplicate upstream behavior is introduced without reason.

---

## 21. Entrypoint composition map

| Entrypoint | Kind | Direct project modules | External parents | Scenarios loading it | PGF input | Release required |
|---|---|---|---|---|---|---|
| `<GRAMMAR_ENTRYPOINT>` | `grammar` | `<MODULES>` | `<RGL_PARENT>` | `<SCENARIOS>` | `yes` | `yes` |
| `<SYNTAX_ENTRYPOINT>` | `syntax/API` | `<MODULES>` | `<RGL_PARENT>` | `<SCENARIOS>` | `<yes/no>` | `<yes/no>` |
| `<LANGUAGE_ENTRYPOINT>` | `language/API` | `<LEXICON, GRAMMAR>` | `<PARENT>` | `<SCENARIOS>` | `<yes/no>` | `<yes/no>` |

### 21.1 Entrypoint invariants

Each configured entrypoint:

- exists;
- matches its GF module name;
- imports every required component;
- depends on no test-only module unless explicitly declared;
- compiles from a clean artifact directory;
- is loadable by required scenarios;
- exposes missing functions before release;
- is listed in `project.toml`;
- produces expected current-run artifacts.

---

## 22. Checkpoint dependency map

Checkpoints appear in deterministic dependency order.

| Order | Checkpoint | Layer proven | Direct prerequisites | Downstream checkpoints | Release entrypoints reached | Required scenarios |
|---:|---|---|---|---|---|---|
| 1 | `<CHECKPOINT_1>` | `<LAYER>` | `<MODULES>` | `<CHECKPOINTS>` | `<ENTRYPOINTS>` | `<SCENARIOS>` |
| 2 | `<CHECKPOINT_2>` | `<LAYER>` | `<MODULES>` | `<CHECKPOINTS>` | `<ENTRYPOINTS>` | `<SCENARIOS>` |

### 22.1 Checkpoint invariants

- order follows dependency direction;
- every required checkpoint compiles before final entrypoint validation;
- a downstream failure is not misreported as an independent root failure;
- skipping a required checkpoint requires an explicit release exception;
- a checkpoint must not depend on a later checkpoint.

---

## 23. Scenario dependency map

| Scenario ID | Script | Loaded entrypoint | Project modules exercised | Inputs | Gold | Required | Modes |
|---|---|---|---|---|---|---|---|
| `<SCENARIO_ID>` | `project/validation/scenarios/<SCENARIO_ID>.gfs` | `<ENTRYPOINT>` | `<MODULES_OR_FAMILIES>` | `<INPUTS_OR_NONE>` | `<GOLD_OR_NONE>` | `<yes/no>` | `<quick/checkpoint/diagnostic/release>` |

### 23.1 Scenario invariants

- every scenario loads a configured/documented entrypoint;
- scenarios do not load undocumented temporary modules;
- required scenarios exist before release;
- optional scenarios remain distinguishable;
- gold mapping is explicit;
- scenario IDs match project configuration.

---

## 24. Artifact dependency map

| Artifact | Produced from | Direct prerequisites | Owner | Required mode | Validation |
|---|---|---|---|---|---|
| `<MODULE>.gfo` | `<MODULE>.gf` | `<DIRECT_IMPORTS>` | GF compile stage | `<MODE>` | current-run artifact check |
| `<EXPECTED_PGF>` | `<ENTRYPOINTS>` | all required checkpoints/scenarios | PGF build stage | `release` | manifest/hash/size |
| `<SCENARIO>.out` | `<SCENARIO>.gfs` | loaded entrypoint and inputs | scenario runner | `<MODE>` | schema/normalization |
| `<SCENARIO>.gold.diff` | current `.out` + project gold | successful comparison preconditions | comparator | on mismatch | diff artifact |

### 24.1 Rule

Generated artifacts are consumers of source/module state, but source modules never depend on generated run output.

---

## 25. Direct dependency adjacency list

Maintain a compact machine-reviewable list in addition to tables.

```text
<CONSUMER_A>:
  - <PROVIDER_1> [import]
  - <PROVIDER_2> [open]
  - <RGL_PROVIDER> [inherit, external]

<CONSUMER_B>:
  - <PROVIDER_A> [helper-consumer]
```

This list must agree with the edge registry.

---

## 26. Reverse dependency index

For every public provider, list direct consumers.

```text
<PROVIDER_1>:
  - <CONSUMER_A>
  - <CONSUMER_B>

<PROVIDER_2>:
  - <CONSUMER_C>
```

### 26.1 Purpose

The reverse index answers:

```text
If this provider changes, which modules must be reviewed first?
```

---

## 27. Transitive dependency summary

| Provider | Direct consumers | Transitive checkpoints | Transitive entrypoints | Scenarios affected | Golds affected |
|---|---|---|---|---|---|
| `<PROVIDER>` | `<DIRECT>` | `<CHECKPOINTS>` | `<ENTRYPOINTS>` | `<SCENARIOS>` | `<GOLDS>` |

### 27.1 Required providers

Include every provider whose public contract is consumed by more than one module or reaches a release entrypoint.

---

## 28. Critical dependency chains

List release-critical paths from low-level provider to entrypoint.

```text
<RESOURCE>
    → <CATEGORY_PROVIDER>
    → <SYNTAX_MODULE>
    → <GRAMMAR_ENTRYPOINT>
    → <REQUIRED_SCENARIO>
    → <GOLD>
```

```text
<MORPHOLOGY_PROVIDER>
    → <PARADIGM_MODULE>
    → <LEXICON_MODULE>
    → <LANGUAGE_ENTRYPOINT>
    → <PGF>
```

For each chain, identify:

- root provider;
- public contracts crossed;
- checkpoints;
- validation evidence;
- release impact.

---

## 29. Dependency depth

Optional analysis table:

| Module | Layer | Direct project dependencies | Maximum project dependency depth | Direct consumers | Maximum consumer depth |
|---|---:|---:|---:|---:|---:|
| `<MODULE>` | `<LAYER>` | `<N>` | `<N>` | `<N>` | `<N>` |

High depth or high fan-out modules require stronger review and scenario coverage.

---

## 30. High-impact providers

| Provider | Why high-impact | Direct consumer count | Entrypoints reached | Required review |
|---|---|---:|---|---|
| `<CAT_MODULE>` | Owns shared lincats | `<N>` | `<ENTRYPOINTS>` | all consumers + scenarios |
| `<MORPHOLOGY_MODULE>` | Owns paradigms | `<N>` | `<ENTRYPOINTS>` | morphology + lexicon + golds |

A high-impact provider should have:

- stable contract IDs;
- direct compile tests;
- downstream checkpoint tests;
- representative scenarios;
- decision-log review for breaking changes.

---

## 31. Leaf modules

| Leaf module | Why no project consumers | Loaded directly by | Release significance |
|---|---|---|---|
| `<MODULE>` | `<REASON>` | `<SCENARIO/ENTRYPOINT/NONE>` | `<VALUE>` |

A release-significant module with no consumer may indicate:

- missing entrypoint import;
- stale configuration;
- orphaned implementation;
- incomplete map.

---

## 32. Orphan detection

A project-owned module is orphaned when it:

- is selected by source rules;
- is not a configured entrypoint;
- is not a checkpoint;
- has no active project-owned consumer;
- is not loaded by a registered scenario;
- is not an approved fixture;
- is not explicitly retired.

Every orphan requires resolution:

```text
connect
configure
document as fixture
retire
remove
```

---

## 33. Circular dependency review

### 33.1 Rule

Circular GF module dependencies are prohibited.

### 33.2 Detection

The project checker should analyze the direct dependency graph using strongly connected components.

Any component containing more than one module is a cycle.

A self-import is also a cycle.

### 33.3 Resolution strategies

- move shared types/parameters downward;
- extract common helper provider;
- introduce an interface/instance boundary;
- split responsibilities;
- remove higher-level dependency;
- replace local duplicate with one lower-level owner.

### 33.4 Cycle exceptions

No cycle exception is allowed for actual GF import edges.

Conceptual bidirectional relationships must be redesigned into acyclic imports.

---

## 34. Forbidden dependency directions

Normally prohibited:

```text
low-level morphology → final grammar entrypoint
resource module → syntax/API entrypoint
category provider → consumer-specific helper
syntax module → scenario
scenario → undocumented temporary module
gold file → source module
project configuration → generated run output
release entrypoint → test-only module
source module → GF Wordbench Python code
source module → run directory
```

Framework-specific prohibited directions remain in the framework interfile lock.

---

## 35. Expected dependency directions

Expected:

```text
abstract syntax → implemented by concrete syntax
resource/category provider → syntax consumers
morphology → paradigms → lexicon
structural provider → syntax/entrypoint consumers
core syntax → grammar/syntax entrypoints
extension provider → extension coordinator
entrypoint → loaded by scenario
entrypoint → input to PGF build
scenario output → compared with gold
validation specification → defines scenario registry
```

The first relation above is semantic implementation direction; direct import arrows must still use the stated consumer-to-provider convention.

---

## 36. Test-only dependencies

| Fixture/test module | Providers used | Consumer tests/scenarios | Excluded from release entrypoints | Status |
|---|---|---|---|---|
| `<FIXTURE>` | `<MODULES>` | `<TESTS>` | `yes` | `<STATUS>` |

### 36.1 Rule

A release entrypoint must not import a test-only module.

A test fixture may import public project modules but must not become their provider.

---

## 37. Optional feature dependencies

| Feature ID | Activation condition | Additional modules/edges | Entry point affected | Scenarios | Release policy |
|---|---|---|---|---|---|
| `<FEATURE>` | `<CONDITION>` | `<MODULES>` | `<ENTRYPOINT>` | `<SCENARIOS>` | `<required/optional/out-of-scope>` |

Optionality must be explicit.

A missing required feature dependency is not treated as an optional omission.

---

## 38. Blocked dependencies

| Edge/module | Block reason | Upstream cause | Direct consumers blocked | Release impact | Exit condition |
|---|---|---|---|---|---|
| `<EDGE_OR_MODULE>` | `<REASON>` | `<CAUSE>` | `<CONSUMERS>` | `<BLOCKING/NON-BLOCKING>` | `<CONDITION>` |

Every blocked relationship must also appear in:

```text
project/docs/STATUS_LEDGER__PROJECT_DOCS.md
```

where applicable.

---

## 39. Deprecated and retired dependencies

| Provider/edge | Status | Replacement | Consumers remaining | Removal target | Migration evidence |
|---|---|---|---|---|---|
| `<OLD_PROVIDER>` | `Deprecated` | `<NEW_PROVIDER>` | `<MODULES>` | `<PROJECT_VERSION>` | `<SCENARIO/DECISION>` |

### 39.1 Final status vocabulary

Use:

```text
Active
Deprecated
Retired
```

for final contract status.

Temporary implementation state belongs in the status ledger.

---

## 40. Build ordering

A valid topological order should be recorded.

```text
1. <ROOT_PROVIDER_1>
2. <ROOT_PROVIDER_2>
3. <MORPHOLOGY_PROVIDER>
4. <CATEGORY_PROVIDER>
5. <CORE_SYNTAX_MODULES>
6. <EXTENSION_MODULES>
7. <ENTRYPOINTS>
```

### 40.1 Rule

The topological order is documentation and validation guidance.

GF remains authoritative for module loading and compilation.

### 40.2 Checkpoint order

Configured checkpoints should form a subsequence consistent with this order.

---

## 41. Clean compilation matrix

| Module/checkpoint | Direct compile required | Clean GFO directory | Expected `.gfo` | Downstream validation |
|---|---|---|---|---|
| `<MODULE>` | `yes` | `yes` | `<MODULE>.gfo` | `<CHECKPOINT/ENTRYPOINT>` |

A pre-existing `.gfo` must not substitute for current-run compilation evidence.

---

## 42. Change-impact procedure

When a module changes:

1. identify the module ID;
2. identify changed public/private surface;
3. find direct consumers in the reverse index;
4. find transitive checkpoints and entrypoints;
5. identify scenarios and golds;
6. classify change as internal, compatible extension, or breaking;
7. update provider and consumers;
8. update contracts and this map;
9. compile provider and direct consumers;
10. compile downstream checkpoints;
11. compile release entrypoints;
12. run affected scenarios;
13. review gold diffs;
14. record decision/status changes;
15. preserve release evidence.

---

## 43. Private compatible change

A private implementation change may leave this map unchanged when:

- no import edge changes;
- no public symbol changes;
- no lincat field changes;
- no constructor behavior changes;
- no output changes;
- all existing validation remains applicable.

The provider's tests may still require updates.

---

## 44. Compatible dependency extension

Examples:

- add a new module with no effect on existing entrypoints;
- add an optional consumer;
- add an optional helper;
- add a new checkpoint after existing layers;
- add a new scenario.

Required updates:

- module inventory;
- edge registry;
- reverse index;
- affected layer;
- project configuration when selected;
- contract lock;
- validation/coverage;
- project minor-version analysis.

---

## 45. Breaking dependency change

Examples:

- rename/move module;
- change entrypoint identity;
- remove provider;
- change interface/instance parent;
- move helper ownership;
- reverse a layer dependency;
- add mandatory dependency;
- replace inherited RGL provider;
- change lincat provider;
- alter checkpoint ordering incompatibly.

Required:

- decision-log entry;
- migration plan;
- provider/consumer updates;
- configuration update;
- scenario/gold review;
- contract version analysis;
- full release validation.

---

## 46. Module rename checklist

```text
[ ] Source filename updated
[ ] GF module declaration updated
[ ] All imports updated
[ ] project.toml updated
[ ] Module inventory updated
[ ] Edge registry updated
[ ] Reverse index updated
[ ] Entrypoints updated
[ ] Scenarios updated
[ ] Gold metadata reviewed
[ ] Documentation updated
[ ] Expected artifacts updated
[ ] Migration/decision recorded
[ ] Full compilation passes
```

Historical run evidence remains unchanged.

---

## 47. Module move checklist

```text
[ ] New path remains under source root
[ ] Selection rules include new path
[ ] GF path covers new location
[ ] Imports/module identity remain valid
[ ] Project configuration updated
[ ] Dependency map updated
[ ] Contract lock updated
[ ] Scenarios resolve
[ ] Clean compile passes
```

---

## 48. RGL inheritance change checklist

```text
[ ] Old external provider recorded
[ ] New external provider recorded
[ ] RGL identity recorded
[ ] Inherited symbol diff reviewed
[ ] Overrides/subtractions reviewed
[ ] Abstract signatures checked
[ ] All consumers compiled
[ ] Entrypoints compiled
[ ] Scenarios run
[ ] Gold diffs reviewed
[ ] Decision log updated
```

---

## 49. Automated extraction policy

GF Wordbench may eventually extract imports automatically.

Automated extraction is evidence, not the sole maintained contract.

### 49.1 Extractor should detect

- module declaration;
- module kind;
- abstract/concrete relationship;
- imported modules;
- inherited modules;
- opened modules;
- interface/instance relationships;
- entrypoint imports;
- missing source modules;
- cycles;
- duplicate module names.

### 49.2 Manual semantics remain required

Automation cannot infer reliably:

- why a dependency exists;
- which symbols are public contract;
- optional vs required status;
- release impact;
- ownership rationale;
- scenario coverage;
- accepted exceptions.

---

## 50. Automated anti-drift checks

Recommended command:

```text
gf-wordbench contracts check --strict
```

Project-specific checker should verify:

1. every inventory file exists;
2. every GF module name matches its declaration;
3. every direct source import has an edge row;
4. every edge row exists in source;
5. every configured checkpoint exists;
6. every configured entrypoint exists;
7. checkpoint order respects dependencies;
8. no cycle exists;
9. no forbidden direction exists;
10. every public lincat consumer has a category-contract entry;
11. every scenario loads a documented entrypoint;
12. every required gold maps to a scenario;
13. every release entrypoint reaches required modules;
14. no active module retains an old language suffix;
15. no release entrypoint imports a fixture;
16. every blocked dependency has a status-ledger entry.

---

## 51. Validation evidence matrix

| Dependency/chain ID | Direct compile | Consumer compile | Entrypoint compile | Scenario | Gold | Artifact | Last verified |
|---|---|---|---|---|---|---|---|
| `<EDGE_OR_CHAIN>` | `<MODULE>` | `<MODULES>` | `<ENTRYPOINT>` | `<SCENARIO>` | `<GOLD>` | `<GFO/PGF>` | `<DATE/RUN_ID>` |

Every release-significant edge needs at least one proof.

High-impact contracts should have several forms of evidence.

---

## 52. Coverage by checkpoint

| Checkpoint | Modules covered | Edges covered | Scenarios | Golds | Gaps |
|---|---|---|---|---|---|
| `<CHECKPOINT>` | `<MODULES>` | `<EDGES>` | `<SCENARIOS>` | `<GOLDS>` | `<NONE_OR_GAPS>` |

---

## 53. Coverage by release entrypoint

| Entrypoint | Reachable project modules | Unreachable selected modules | Required scenarios | PGF role | Status |
|---|---|---|---|---|---|
| `<ENTRYPOINT>` | `<MODULES>` | `<MODULES_OR_NONE>` | `<SCENARIOS>` | `<ROLE>` | `<STATUS>` |

An unreachable selected active module requires review.

---

## 54. Scenario-to-module coverage

| Module/family | Required scenario coverage | Actual scenarios | Gold-backed | Coverage status |
|---|---|---|---|---|
| `<MODULE>` | `<BEHAVIOR>` | `<SCENARIOS>` | `<yes/no>` | `<complete/gap/out-of-scope>` |

This table must agree with `TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md`.

---

## 55. Diagram — layer overview

Replace with the actual graph.

```text
                    +--------------------------+
                    | External GF / RGL        |
                    +------------+-------------+
                                 |
                                 v
                    +--------------------------+
                    | Resources / Interfaces   |
                    +------------+-------------+
                                 |
                  +--------------+--------------+
                  |                             |
                  v                             v
       +---------------------+       +---------------------+
       | Morphology          |       | Category / Lincat   |
       +----------+----------+       +----------+----------+
                  |                             |
                  +--------------+--------------+
                                 |
                                 v
                    +--------------------------+
                    | Lexicon / Structural     |
                    +------------+-------------+
                                 |
                                 v
                    +--------------------------+
                    | Core Syntax              |
                    +------------+-------------+
                                 |
                                 v
                    +--------------------------+
                    | Extend / Coordinator     |
                    +------------+-------------+
                                 |
                                 v
                    +--------------------------+
                    | Entrypoints              |
                    +------+-------------+-----+
                           |             |
                           v             v
                     Scenarios          PGF
```

The diagram must not contradict the tables.

---

## 56. Diagram — direct project graph

Replace this example with the complete project graph.

```text
<GRAMMAR_ENTRYPOINT>
├── <NOUN_MODULE>
│   ├── <CATEGORY_MODULE>
│   └── <MORPHOLOGY_MODULE>
├── <VERB_MODULE>
│   ├── <CATEGORY_MODULE>
│   └── <MORPHOLOGY_MODULE>
├── <SENTENCE_MODULE>
│   ├── <NOUN_MODULE>
│   └── <VERB_MODULE>
├── <STRUCTURAL_MODULE>
└── <EXTEND_MODULE>
    └── <RGL_EXTEND_MODULE> [external]
```

---

## 57. Diagram — release chain

```text
configured checkpoints
        ↓
release entrypoint compilation
        ↓
required scenario loading
        ↓
normalized scenario output
        ↓
gold comparison
        ↓
PGF build
        ↓
manifest and release decision
```

The dependency map must identify which modules feed each stage.

---

## 58. Dependency risks

| Risk ID | Module/edge | Risk | Probability | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|
| `DEP-RISK-001` | `<MODULE>` | `<RISK>` | `<low/medium/high>` | `<low/medium/high>` | `<ACTION>` | `<OWNER>` | `<STATUS>` |

Typical risks:

- high fan-out lincat provider;
- duplicated helper ownership;
- unstable RGL inheritance;
- shallow morphology fallback;
- entrypoint relying on test-only module;
- undocumented runtime string matching;
- one module combining too many layers;
- scenario loading non-release module;
- obsolete leaf module.

---

## 59. Known dependency exceptions

| Exception ID | Normal rule violated | Modules/edge | Justification | Decision reference | Validation | Expiry/review |
|---|---|---|---|---|---|---|
| `<EXCEPTION_ID>` | `<RULE>` | `<MODULES>` | `<REASON>` | `<DECISION_ID>` | `<EVIDENCE>` | `<DATE/CONDITION>` |

Every exception requires a decision-log entry.

No exception may permit an actual circular GF import.

---

## 60. Status ledger integration

Dependency-related status entries include:

```text
temporary provider
fallback helper
blocked consumer
deprecated module
planned replacement
incomplete entrypoint
unverified external inheritance
orphan under review
```

Each status entry should reference:

- module/edge ID;
- affected consumers;
- release impact;
- exit condition;
- validation evidence.

---

## 61. Decision-log integration

A decision record is required for:

- layer-boundary change;
- module ownership transfer;
- new interface/instance boundary;
- major entrypoint composition change;
- RGL inheritance replacement;
- accepted dependency exception;
- module split/merge affecting consumers;
- removal of public provider;
- new test-only dependency in release path;
- project-specific module suffix migration.

---

## 62. Release criteria

The dependency-map portion of release passes only when:

```text
[ ] Every selected project module appears in inventory
[ ] Every direct dependency appears in edge registry
[ ] Every edge row exists in source
[ ] No unresolved required placeholder remains
[ ] No circular dependency exists
[ ] No forbidden dependency direction exists
[ ] Every configured checkpoint exists
[ ] Checkpoint order follows dependencies
[ ] Every configured entrypoint exists
[ ] Every release entrypoint reaches required modules
[ ] No release entrypoint imports test-only modules
[ ] Every required scenario loads a documented entrypoint
[ ] Every required gold maps to a scenario
[ ] Every high-impact provider has validation
[ ] Every blocked edge is in the status ledger
[ ] Every exception has a decision
[ ] Project configuration and map agree
[ ] Interfile contract lock and map agree
[ ] Clean checkpoint compilation passes
[ ] Clean release-entrypoint compilation passes
```

---

## 63. Release blocker examples

- missing module row;
- undocumented direct import;
- cycle;
- lower-level module importing final entrypoint;
- configured checkpoint missing;
- checkpoint order reversed;
- scenario loads an undocumented temporary module;
- required module unreachable from every release entrypoint;
- fixture imported by release entrypoint;
- retired provider still imported;
- active consumer using undocumented lincat fields;
- unresolved external provider identity;
- stale old-language module name;
- dependency exception without decision.

---

## 64. Review workflow

### 64.1 Routine source change

```text
1. inspect changed imports/public surface
2. update edge registry if needed
3. inspect reverse dependencies
4. compile direct consumers
5. run affected checkpoint/scenario
6. update last-verified evidence
```

### 64.2 Architecture change

```text
1. create decision record
2. update LANGUAGE_ARCHITECTURE.md
3. update this dependency map
4. update interfile contracts
5. update source/provider/consumers
6. update configuration
7. update scenarios/golds
8. run full diagnostic/release validation
```

### 64.3 GF/RGL upgrade

```text
1. resolve new toolchain identity
2. compare external dependencies
3. review inheritance/override map
4. compile all project modules
5. run required scenarios
6. review gold diffs
7. update compatibility evidence
```

---

## 65. Initialization procedure

When creating a project from this template:

1. fill project identity;
2. scan active source files;
3. list every GF module;
4. assign each module to one layer;
5. identify abstract/concrete pairs;
6. identify interface/instance pairs;
7. list all external imports;
8. record every direct edge;
9. create reverse dependency index;
10. identify checkpoints and entrypoints;
11. map scenarios and golds;
12. identify expected GFO/PGF artifacts;
13. check cycles;
14. check forbidden directions;
15. link contract and validation evidence;
16. record first verified baseline run.

---

## 66. Baseline record

| Field | Value |
|---|---|
| Baseline run ID | `<RUN_ID>` |
| GF Wordbench version | `<GF_WORDBENCH_VERSION>` |
| GF version | `<GF_VERSION>` |
| RGL identity | `<RGL_IDENTITY>` |
| Project source revision | `<SOURCE_REVISION>` |
| Modules inventoried | `<COUNT>` |
| Direct edges inventoried | `<COUNT>` |
| Cycles | `<ZERO_OR_DETAILS>` |
| Release entrypoints compiled | `<RESULT>` |
| Last verified | `<YYYY-MM-DD>` |

---

## 67. Change history

| Map version | Date | Change | Decision/migration | Reviewer |
|---|---|---|---|---|
| `1.0.0` | `<YYYY-MM-DD>` | Initial project dependency map | `<DECISION_OR_NONE>` | `<REVIEWER>` |

Version this map when its normative structure or project graph changes.

---

## 68. Compact module template

Copy for each high-impact module.

```markdown
### <MODULE_ID> — `<MODULE_NAME>`

**File:** `<SOURCE_ROOT>/<MODULE_NAME>.gf`  
**Kind:** `<KIND>`  
**Layer:** `<LAYER>`  
**Status:** Active | Deprecated | Retired  
**Purpose:** `<PURPOSE>`

**Direct project dependencies**
- `<PROVIDER>` — `<KIND>` — `<PUBLIC SURFACE>`

**External dependencies**
- `<RGL/GF MODULE>` — `<PURPOSE>`

**Direct consumers**
- `<CONSUMER>`

**Public surface**
- `<CATEGORY/FUNCTION/LINCAT/OPER/CONSTRUCTOR>`

**Checkpoints**
- `<CHECKPOINT>`

**Entrypoints reached**
- `<ENTRYPOINT>`

**Scenarios**
- `<SCENARIO>`

**Golds**
- `<GOLD_OR_NONE>`

**Risks/status**
- `<STATUS_LEDGER_ID_OR_NONE>`

**Validation**
- direct compile: `<RESULT/EVIDENCE>`
- consumer compile: `<RESULT/EVIDENCE>`
- entrypoint compile: `<RESULT/EVIDENCE>`
- scenario: `<RESULT/EVIDENCE>`

**Last reviewed:** `<YYYY-MM-DD>`
```

---

## 69. Compact edge template

```markdown
### <EDGE_ID> — `<CONSUMER>` → `<PROVIDER>`

**Kind:** `<DEPENDENCY_KIND>`  
**Required:** yes | no  
**Status:** Active | Deprecated | Retired

**Consumed surface**
- `<SYMBOL/FIELD/MODULE CONTRACT>`

**Why required**
- `<RATIONALE>`

**Direct validation**
- `<COMPILE/SCENARIO>`

**Downstream impact**
- checkpoints: `<LIST>`
- entrypoints: `<LIST>`
- scenarios: `<LIST>`
- golds: `<LIST>`

**Breaking changes**
- `<CHANGES>`

**Decision/status references**
- `<REFERENCES_OR_NONE>`

**Last reviewed:** `<YYYY-MM-DD>`
```

---

## 70. Final checklist

```text
[ ] Project identity complete
[ ] Source root matches project.toml
[ ] Every selected .gf file inventoried
[ ] Every module name unique
[ ] Every module assigned a layer
[ ] Every direct import edge recorded
[ ] Every external dependency recorded
[ ] Abstract/concrete map complete
[ ] Interface/instance map complete
[ ] Lincat dependency map complete
[ ] Morphology/paradigm map complete
[ ] Syntax-family map complete
[ ] Structural/lexicon map complete
[ ] Override map complete
[ ] Entrypoint map complete
[ ] Checkpoint map complete
[ ] Scenario map complete
[ ] Artifact map complete
[ ] Reverse dependency index complete
[ ] Critical chains documented
[ ] No cycles
[ ] No forbidden direction
[ ] Orphans resolved
[ ] Fixtures excluded from release paths
[ ] Blocked edges recorded in status ledger
[ ] Exceptions recorded in decision log
[ ] Validation evidence current
[ ] No unresolved required placeholder
```

---

## 71. Final enforcement rule

The module dependency map is the authoritative project-level index of who depends on whom.

It must agree with source imports, project configuration, entrypoints, checkpoints, scenarios, golds, architecture, and the interfile contract lock.

> No module dependency may be added, removed, reversed, or redirected through an isolated source edit.

Every dependency change must be mapped, impact-reviewed, compiled through its downstream entrypoints, validated through affected scenarios, and recorded as one coordinated project change.
