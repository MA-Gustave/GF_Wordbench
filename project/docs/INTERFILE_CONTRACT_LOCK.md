# Albanian (`Sqi`) — Interfile Contract Lock

**Document ID:** `GF-WB-PROJECT-SQI-INTERFILE-LOCK`  
**Status:** Normative active-project contract  
**Contract version:** `1.2.0`  
**Decision status:** Project-owned and active  
**Implementation status:** configuration-derived contracts recorded; unresolved release locks remain open  
**Verification status:** current source inventory and reproducible release evidence still required  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** Albanian project maintainers  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This file prevents drift between the Albanian GF sources, project configuration, scenarios, inputs, golds, project documentation and release evidence.

The active `project/` boundary represents exactly one GF language project and one normative language target. It owns Albanian-specific facts only.

It must not contain:

- a registry of other Wordbench workspaces;
- selectable language profiles;
- cross-project aggregation or Portfolio readiness rules;
- `gf-portfolio` private configuration, schemas or storage paths;
- framework implementation claims unsupported by current source or run evidence.

## 2. Authority order

For Albanian project facts:

1. current GF sources and reproducible GF evidence;
2. `project/project.toml` for declared project configuration;
3. this interfile contract lock;
4. project owner documents such as architecture, dependency, category/lincat and morphology specifications;
5. overview and historical records.

A conflict is recorded in `project/docs/KNOWN_ISSUES.md`, `project/docs/STATUS_LEDGER.md` or `project/docs/DECISION_LOG.md`; it is not silently resolved in a downstream document.

## 3. Locked project identity

```text
project ID: sqi
language: Albanian
language code: sqi
documented module suffix: Sqi
source directory: lib/src/albanian
active project root: project/
```

The active-project identity comes from `project/project.toml`, not GUI state, previous runs, filename guessing or Portfolio membership.

## 4. Configured module contract

Declared entrypoints:

```text
GrammarSqi.gf
SyntaxSqi.gf
```

Declared checkpoints:

```text
MorphoSqi.gf
NounSqi.gf
VerbSqi.gf
ExtendSqi.gf
StructuralSqi.gf
```

Locked rules:

- every configured module exists under the resolved source root before its validation gate can pass;
- module names, filenames and GF declarations agree;
- imports resolve through the configured GF/RGL path order;
- providers and all direct consumers change together when a public contract changes;
- category and `lincat` ownership is unique and documented;
- public constructors, records, fields and helper assumptions are not changed in isolation;
- a release/PGF entrypoint is not inferred merely from the entrypoint list; it must be explicitly locked and verified.

## 5. Scenario contract

Required scenario IDs:

```text
load
missing
linearize
parse
```

Optional scenario IDs:

```text
generation
morphology
```

Each registered ID maps consistently to:

```text
one .gfs file
declared inputs
stable markers
normalization profile
reviewed gold when regression comparison applies
relevant module or entrypoint context
```

Locked rules:

- GF executes native `.gfs` scenarios;
- raw transcript is preserved before normalization;
- scenario ID, file, inputs and gold use the same identity;
- normal validation never mutates scenarios, inputs or golds;
- missing markers, inputs or required golds fail explicitly for the applicable gate;
- gold updates require explicit review and evidence.

## 6. Documentation ownership

| Subject | Owner document |
|---|---|
| Project identity and navigation | `project/README.md`, `project/docs/00_PROJECT_START_HERE.md` |
| Language scope and variety | `project/docs/LANGUAGE_OVERVIEW.md` |
| Linguistic/module architecture | `project/docs/LANGUAGE_ARCHITECTURE.md` |
| Imports and provider/consumer map | `project/docs/MODULE_DEPENDENCY_MAP.md` |
| Categories and `lincat` records | `project/docs/CATEGORY_AND_LINCAT_CONTRACT.md` |
| Syntax and constructor rules | `project/docs/SYNTAX_AND_CONSTRUCTOR_RULES.md` |
| Morphology contracts | `project/docs/MORPHOLOGY_SPEC.md` |
| Validation requirements | `project/docs/VALIDATION_SPEC.md` |
| Coverage claims | `project/docs/TEST_COVERAGE_MATRIX.md` |
| Research authorities and evidence | `project/docs/RESEARCH_EVIDENCE.md` |
| Current blockers | `project/docs/KNOWN_ISSUES.md`, `project/docs/STATUS_LEDGER.md` |
| Release gates | `project/docs/RELEASE_CRITERIA.md` |
| Accepted project decisions | `project/docs/DECISION_LOG.md` |

A document may summarize another owner but cannot redefine its normative facts independently.

## 7. Evidence rules

- GF source claims require current source evidence.
- Compile claims require current GF execution evidence.
- Scenario and regression claims require current run evidence and the relevant raw/normalized artifacts.
- Coverage claims must distinguish declared, executed and passing coverage.
- Research claims cite approved authorities and separate evidence from implementation.
- Historical or planned behavior is labeled as such.
- A stale artifact never satisfies a current release gate.

## 8. Open release locks

The supplied configuration and documentation do not yet establish the following as verified release contracts:

- one unique release/PGF entrypoint;
- expected PGF filename and required contents;
- supported GF and RGL version matrix;
- canonical Albanian variety and orthography policy;
- approved linguistic research authorities;
- reproducible current counts for coverage and blockers.

These remain release blockers until owner documents and reproducible evidence agree.

## 9. Portfolio boundary

Public finalized Wordbench artifacts for this project may later be read by `gf-portfolio`. That optional consumption:

- does not change Albanian project identity;
- does not permit Portfolio to edit project files or run artifacts;
- creates no Wordbench dependency on Portfolio;
- does not move Albanian linguistic facts into a portfolio registry.

## 10. Change control

A breaking project-contract change updates, in one reviewed unit:

1. provider source;
2. every direct and relevant downstream consumer;
3. `project/project.toml` when configuration changes;
4. scenarios, inputs and golds;
5. dependency, category/lincat, syntax or morphology owner documents;
6. validation specification and coverage matrix;
7. issue, status and decision records;
8. release criteria and current evidence;
9. this lock and the documentation correction ledger.

## 11. Validation checklist

```text
[ ] project identity agrees with project.toml
[ ] configured modules exist and names agree
[ ] providers and consumers are synchronized
[ ] category/lincat ownership is unique
[ ] required scenarios are registered and reproducible
[ ] raw evidence precedes normalization
[ ] golds are reviewed and not auto-mutated
[ ] claims match current source or run evidence
[ ] open release locks remain explicit
[ ] no Portfolio registry or cross-project rule entered project/
[ ] project status and decisions are updated
```
