# GF Wordbench Project Template — Interfile Contract Lock

**Document ID:** `GF-WB-PROJECT-TEMPLATE-INTERFILE-LOCK`  
**Status:** Normative reusable template contract  
**Contract version:** `2.0.0`  
**Applies to:** `templates/project/` before initialization and the structural handoff to one initialized active project  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Template owner:** GF Wordbench maintainers  
**Initialized project owner:** `<PROJECT_OWNER>`  
**Last reviewed:** `2026-07-24`

---

## 1. Purpose

This file prevents drift between the reusable project template and the active-project contract expected after initialization.

Each initialized template instance represents exactly one active GF language project and one normative language target in one Wordbench workspace.

The template must not introduce:

- several active projects in one workspace;
- a runtime language-profile selector;
- a Portfolio workspace registry;
- cross-project aggregation or readiness state;
- `gf-portfolio` private configuration, schemas, paths or runtime dependencies.

## 2. Placeholder rule

Before initialization, template-specific values are explicit placeholders, including as applicable:

```text
<PROJECT_ID>
<PROJECT_NAME>
<PROJECT_OWNER>
<LANGUAGE_NAME>
<LANGUAGE_CODE>
<MODULE_SUFFIX>
<SOURCE_DIRECTORY>
<ENTRYPOINTS>
<CHECKPOINTS>
<SCENARIO_IDS>
<RELEASE_ENTRYPOINT>
<EXPECTED_PGF>
<GF_RGL_COMPATIBILITY>
<LANGUAGE_VARIETY_POLICY>
<RESEARCH_AUTHORITIES>
```

Locked rules:

- placeholders are syntactically recognizable and never resemble verified real values accidentally;
- required placeholders are replaced or initialization fails;
- no initialized project is considered ready while required placeholders remain;
- examples are labeled examples and do not become active-project evidence;
- template files do not contain the identity of the repository's current active language.

## 3. Required initialized structure

The template preserves this single-project structure:

```text
project/
  project.toml
  README.md
  docs/
    00_PROJECT_START_HERE__TEMPLATES_PROJECT_DOCS.md
    LANGUAGE_OVERVIEW.md
    LANGUAGE_ARCHITECTURE.md
    MODULE_DEPENDENCY_MAP.md
    CATEGORY_AND_LINCAT_CONTRACT.md
    SYNTAX_AND_CONSTRUCTOR_RULES.md
    MORPHOLOGY_SPEC.md
    INTERFILE_CONTRACT_LOCK.md
    VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md
    TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md
    RESEARCH_EVIDENCE.md
    KNOWN_ISSUES.md
    STATUS_LEDGER__TEMPLATES_PROJECT_DOCS.md
    RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md
    DECISION_LOG.md
  validation/
    README.md
    scenarios/README.md
    inputs/README.md
    gold/README.md
```

Additional project-owned files may be introduced by an explicit contract change. Removing a required owner document requires coordinated migration.

## 4. Initialization handoff

Initialization is explicit and transactional where practical.

It must:

1. select an empty or approved destination active-project boundary;
2. validate requested identity values;
3. replace required placeholders deterministically;
4. create one project configuration;
5. preserve UTF-8 and canonical path rules;
6. reject path traversal and destination escape;
7. report every created or replaced file;
8. leave no half-initialized project presented as ready after failure;
9. transfer ownership of initialized files to project maintainers;
10. require source and validation verification before implementation claims become active.

Initialization must not create a Portfolio registry or register the project in an external product as an implicit side effect.

## 5. Template-to-project synchronization

The template and active-project structure must remain synchronized by role, not by language-specific content.

For every required active-project document, the template provides:

- the same purpose and owner boundary;
- generic required sections;
- explicit placeholders;
- instructions for evidence and verification;
- no claim that the initialized language already implements the contract.

The active project may contain concrete facts. The template remains language-neutral.

## 6. Generic GF interfile contract

An initialized project lock must cover:

```text
project identity
source root
GF search-path policy
entrypoints and checkpoints
module import relationships
category and lincat ownership
public constructor and helper contracts
scenario registry
input and marker contracts
normalization and gold contracts
release entrypoint and PGF expectations
research evidence
known blockers and decisions
```

Provider and consumer files form one coordinated change unit when their shared public contract changes.

## 7. Scenario and gold template rules

The template defines structure and instructions, not real linguistic expectations.

- scenario IDs are placeholders or generic examples;
- `.gfs` content must be replaced or verified for the initialized project;
- input files are project-owned after initialization;
- gold files are absent, placeholder-marked or explicitly unverified until reviewed output exists;
- normal validation cannot auto-approve template output as a gold;
- raw evidence and normalization remain distinct.

## 8. Documentation truth rules

After initialization:

- project identity comes from the generated `project.toml`;
- language facts come from current GF sources and project owner documents;
- compile and scenario status comes from reproducible GF evidence;
- placeholders, sample counts and sample claims are removed or marked unresolved;
- `STATUS_LEDGER__TEMPLATES_PROJECT_DOCS.md` records incomplete or blocked initialization work;
- `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md` cannot pass on template claims alone.

## 9. Portfolio boundary

An initialized Wordbench project may publish normal finalized Wordbench artifacts. Optional Portfolio ingestion remains outside this template.

The template must not define:

- Portfolio project IDs;
- Portfolio registry paths;
- portfolio-wide status values;
- Portfolio database fields;
- mandatory Portfolio adapters;
- reverse Wordbench dependencies on `gf-portfolio`.

## 10. Change control

A structural template change requires coordinated review of:

1. active-project required structure;
2. initialization and reset behavior;
3. project configuration schema;
4. project documentation owner map;
5. scenario/input/gold structure;
6. tests for placeholders and path safety;
7. migration effects on existing projects;
8. this lock, the active-project lock and correction ledger.

## 11. Validation checklist

```text
[ ] one initialized template equals one active project
[ ] required placeholders are explicit
[ ] initialized projects cannot retain required placeholders unnoticed
[ ] structure matches active-project owner roles
[ ] template remains language-neutral
[ ] no implementation claim is inferred from template availability
[ ] scenario and gold examples are not treated as verified evidence
[ ] initialization cannot escape its destination
[ ] no Portfolio registry or dependency is introduced
[ ] active-project and template locks are reviewed together
```
