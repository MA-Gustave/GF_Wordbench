# ADR-0001 — One Active Language Project per GF Wordbench Workspace

**ADR ID:** `ADR-0001`  
**Title:** Single Active Language  
**Status:** Accepted  
**Decision date:** 2026-07-22  
**Last reviewed:** 2026-07-22  
**Decision owners:** GF Wordbench maintainers  
**Applies to:** GF Wordbench workspace structure, active project configuration, CLI, GUI, validation, automation, templates, state, reports, and release artifacts  
**Supersedes:** None  
**Superseded by:** None  
**Related decisions:** `ADR-0002-GF-AS-EXECUTION-ENGINE.md`, `ADR-0003-SEPARATE-SCAN-AND-COMPILE.md`, `ADR-0004-NATIVE-GFS-SCENARIOS.md`  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\decisions\ADR-0001-SINGLE-ACTIVE-LANGUAGE.md`

---

## 1. Decision summary

GF Wordbench adopts the following architecture:

> One GF Wordbench workspace contains exactly one active GF language project.

The active project is represented by:

```text
project/
project/project.toml
project/docs/
project/validation/
the configured GF source tree
```

Every validation run resolves exactly one active project identity.

GF Wordbench does not provide a runtime language-profile selector, a multi-project registry, or simultaneous validation of several active language projects inside one workspace.

Supporting another language requires one of the following controlled operations:

```text
clone a fresh GF Wordbench workspace
instantiate `templates/project/`
reset or replace the active `project/` boundary
migrate one existing language project into a new workspace
```

A single installed GF Wordbench executable or Python package may be used by several isolated workspaces. The restriction applies to each workspace and each run, not to the executable binary for its entire lifetime.

---

## 2. Context

GF Wordbench is a development and validation environment for Grammatical Framework language projects.

Its responsibilities include:

- loading project configuration;
- discovering GF sources;
- scanning source text;
- compiling configured modules;
- classifying diagnostics;
- running native `.gfs` scenarios;
- comparing normalized output with reviewed gold files;
- constructing PGF artifacts;
- preserving evidence;
- comparing runs;
- producing reports;
- enforcing release criteria.

Many of these responsibilities depend on language-specific facts:

```text
project identity
language code
module suffix
source root
GF search paths
entrypoints
checkpoints
required scenarios
optional scenarios
scenario inputs
gold expectations
expected `.gfo` files
expected `.pgf`
project release criteria
linguistic architecture
category and lincat contracts
known issues
status ledger
```

A multi-language runtime design would require GF Wordbench to decide repeatedly which language profile owns each:

- path;
- module;
- scenario;
- gold file;
- report;
- state value;
- release artifact;
- previous run;
- contract;
- documentation statement.

That additional selection layer would create a second axis of identity throughout the system.

The project instead prioritizes:

- deterministic behavior;
- explicit ownership;
- low configuration ambiguity;
- reliable cloning;
- safe release evidence;
- simple project-level documentation;
- prevention of stale-language drift;
- one clear source of project truth.

---

## 3. Problem statement

Without an explicit architecture decision, GF Wordbench could drift toward one of several incompatible models:

1. one workspace with one active language;
2. one workspace with multiple named language profiles;
3. one workspace with a selectable current language stored in GUI state;
4. one workspace with many projects under `projects/<id>/`;
5. one command that accepts arbitrary external project roots;
6. one process that validates several languages in one run;
7. one global installation containing language-specific defaults.

These models differ materially in:

- configuration ownership;
- path resolution;
- state persistence;
- command semantics;
- run identity;
- artifact layout;
- report schemas;
- release gates;
- project-document ownership;
- migration behavior;
- test coverage;
- security.

Allowing the model to remain implicit would make local features choose different assumptions.

Examples of drift that would become likely:

- the GUI remembers one language while the CLI resolves another;
- a scenario loads an entrypoint from a different profile;
- a gold file is selected by filename guessing;
- a previous run from another language becomes the regression baseline;
- a report combines results from unrelated projects;
- a PGF artifact uses the wrong language identity;
- framework defaults contain language-specific paths;
- a project contract lock describes more than one active source tree;
- cleanup removes artifacts belonging to another profile;
- release mode validates only the currently selected subset without recording it clearly.

A single explicit project boundary is required.

---

## 4. Decision drivers

The decision is driven by the following priorities.

### 4.1 Deterministic project identity

Every run must resolve one project identity from one authoritative source.

### 4.2 Contract clarity

Project-level contracts must describe one active language architecture without profile qualifiers throughout every entry.

### 4.3 Evidence attribution

Every source, diagnostic, scenario, gold file, artifact, and report must belong unambiguously to one project.

### 4.4 Release integrity

A release decision must apply to one declared project and one declared set of entrypoints and artifacts.

### 4.5 Cloneability

The framework must be clonable and resettable for a new language without redesigning the framework.

### 4.6 Separation of framework and language

Language-specific values belong to the active project, not framework modules.

### 4.7 Minimal hidden state

Project selection must not depend on disposable GUI or application state.

### 4.8 Simpler security model

Paths, scenarios, inputs, and outputs can be contained within one active project boundary.

### 4.9 Simpler automation

CI can validate one project per workspace without a matrix of implicit profile selectors.

### 4.10 Controlled complexity

The architecture should not create a multi-project management platform without demonstrated requirements.

---

## 5. Definitions

### 5.1 Workspace

A **GF Wordbench workspace** is one checked-out, copied, or instantiated repository/work directory containing the framework structure and one active `project/` boundary.

Conceptual structure:

```text
GF_Wordbench/
├── app/
├── docs/
├── tests/
├── templates/
├── project/
│   ├── project.toml
│   ├── docs/
│   ├── validation/
│   └── <GF source tree>
└── ...
```

A workspace may be:

- a Git clone;
- a Git worktree;
- a copied directory;
- an initialized template;
- another isolated source checkout.

### 5.2 Active project

The **active project** is the one project described by:

```text
project/project.toml
```

and implemented under the project boundary.

### 5.3 Language project

A **language project** is the cohesive set of:

- GF source modules;
- project configuration;
- project documentation;
- validation scenarios;
- validation inputs;
- gold expectations;
- project release policy;
- expected artifacts.

### 5.4 Project identity

Project identity includes at least:

```text
project ID
display name
language name or code
module naming convention or suffix
source root
entrypoints
checkpoints
required scenarios
release targets
```

### 5.5 Workspace copy

The phrase **one GF Wordbench copy** means one workspace copy.

It does not mean:

- one machine;
- one user account;
- one Python installation;
- one package wheel;
- one executable binary;
- one organization.

### 5.6 Run

A **run** is one validation execution against exactly one resolved active project.

### 5.7 Multi-language workspace

A **multi-language workspace** is any design in which one workspace stores several independently selectable active project profiles.

This decision rejects that design for the core architecture.

### 5.8 Cross-project orchestration

**Cross-project orchestration** is an external automation layer that runs several isolated GF Wordbench workspaces separately and aggregates only their high-level statuses.

It is not the same as a multi-language GF Wordbench run.

---

## 6. Decision

### 6.1 One active project

A GF Wordbench workspace must contain exactly one active project.

The canonical project path is:

```text
project/
```

The canonical project configuration path is:

```text
project/project.toml
```

### 6.2 One project per run

Every run must resolve and validate exactly one project.

A run must not:

- switch project midway;
- merge file results from different project identities;
- execute scenarios from another project;
- compare gold files from another project;
- construct a PGF for an undeclared second project;
- use another project’s previous run as its regression baseline.

### 6.3 One authoritative project identity

The active project identity is owned by:

```text
project/project.toml
```

Project documentation and source files consume that identity.

The following are not authoritative project selectors:

```text
GUI state
application state
last run
output-directory name
current working directory
source filename guessing
environment variable alone
branch name
tag name
scenario contents
gold filename
```

### 6.4 No profile registry

The core project configuration must not contain a registry such as:

```toml
[projects.french]
...

[projects.albanian]
...
```

or:

```toml
active_project = "french"
```

The canonical schema represents one active project directly.

### 6.5 No runtime language switch

The canonical CLI and GUI must not require or expose a normal runtime selector such as:

```text
--language
--profile
--active-project
--switch-project
```

for selecting among several project profiles inside one workspace.

A command may accept an explicit workspace/project root where the public CLI architecture requires it, but that root must resolve one active `project/project.toml`, not a profile collection.

### 6.6 No language selection in application state

Application state may remember local convenience values.

It must not define which language project is active.

Deleting state must not change project identity.

### 6.7 Multiple languages through isolation

A user may maintain multiple languages by creating multiple isolated workspaces.

Example:

```text
C:/work/gf-wordbench-french/
C:/work/gf-wordbench-albanian/
C:/work/gf-wordbench-example/
```

Each contains:

```text
project/project.toml
```

for one active project.

### 6.8 Shared executable permitted

The same installed GF Wordbench package may execute several workspaces in separate invocations.

The invariant is:

```text
one resolved workspace
→ one active project
→ one run identity
```

### 6.9 External aggregate automation permitted

An external CI or orchestration system may run:

```text
workspace A → run A
workspace B → run B
workspace C → run C
```

It may then aggregate:

- success/failure;
- project IDs;
- run links;
- release statuses.

It must not merge their internal `RunResult` objects into one ordinary GF Wordbench run summary.

### 6.10 Project replacement is explicit

Replacing the active project requires an explicit lifecycle operation:

- initialize;
- clone;
- reset;
- migrate;
- archive and replace.

It must not happen as an incidental GUI selection.

---

## 7. Architectural boundary

The decision creates two principal ownership zones.

### 7.1 Framework-owned zone

```text
app/
docs/
tests/
templates/
root launchers
package metadata
framework configuration defaults
```

This zone must remain language-neutral.

### 7.2 Active-project-owned zone

```text
project/project.toml
project/docs/
project/validation/
project GF source tree
project release artifacts before publication
```

This zone may contain language-specific names and assumptions.

### 7.3 Boundary rule

Framework code may interpret generic project configuration fields.

It must not contain active-language values such as:

```text
specific language name
specific language code
specific module suffix
specific entrypoint name
specific checkpoint name
specific scenario ID required only by one language
specific source directory
specific expected PGF name
```

Exceptions are limited to:

- explicit migration fixtures;
- clearly labeled examples;
- historical compatibility tests;
- test fixture projects isolated from active defaults.

---

## 8. Configuration consequences

### 8.1 Project configuration shape

`project/project.toml` represents one project directly.

Conceptual shape:

```toml
schema_id = "gf-wordbench.project"
schema_version = "1.0"

[project]
id = "<project-id>"
name = "<display-name>"
language_code = "<language-code>"
root = "."

[sources]
directory = "<project-relative-source-directory>"
glob = "*.gf"

[modules]
entrypoints = ["<entrypoint>.gf"]
checkpoints = ["<checkpoint>.gf"]

[validation]
required_scenarios = ["load", "parse"]
optional_scenarios = ["generation"]
release_requires_pgf = true
```

The exact schema remains owned by `PERSISTED_SCHEMA_LOCK.md`.

### 8.2 Prohibited configuration shapes

The canonical project schema must not introduce:

```text
projects[]
languages[]
profiles[]
active_language
selected_language
profile_inheritance
per-language GUI state
```

without superseding this ADR.

### 8.3 Environment values

Machine-local values may differ by workspace:

- GF executable;
- RGL root;
- output root;
- temporary directory.

They do not define project identity.

### 8.4 Configuration precedence

Configuration precedence must never allow an environment or state value to silently replace the active project identity.

### 8.5 Validation

Project loading must verify:

```text
exactly one project configuration exists at the expected boundary
project identity is complete
configured source root exists
entrypoints belong to the project
scenarios belong to the project
gold paths remain project-contained
```

---

## 9. State consequences

### 9.1 Disposable state

Application state may store:

```text
last local GF executable
last local RGL path
last output root
last mode
last target file
last run pointer
display preferences
```

### 9.2 Prohibited state authority

Application state must not store as authoritative:

```text
active language ID
active project profile
entrypoints
checkpoints
required scenarios
source root
release targets
expected PGF
```

### 9.3 Safe deletion

Deleting `.gf_wordbench_state.json` must not alter:

- project identity;
- source selection policy;
- required validation;
- release policy;
- project documentation;
- project artifacts.

### 9.4 Legacy migration

Legacy state keys containing language-specific scan paths may be read during migration.

Once `project.toml` is authoritative:

- project-owned values are discarded from migrated state;
- local environment values may be retained;
- no legacy value may select another active language.

---

## 10. CLI consequences

### 10.1 Canonical behavior

The CLI operates on one workspace/project resolution per invocation.

### 10.2 No profile selector

The final CLI does not expose a normal command like:

```text
gf-wordbench run --profile french
```

inside a workspace containing several profiles.

### 10.3 Explicit root

If the CLI accepts a root argument, the root identifies one workspace or one active project boundary.

It does not identify an entry in a profile registry.

### 10.4 Mode independence

The validation modes:

```text
quick
checkpoint
release
diagnostic
```

change validation scope.

They do not change project identity.

### 10.5 Machine output

CLI machine-readable output must include or resolve:

```text
project ID
run ID
run directory
canonical mode
overall status
```

### 10.6 Errors

The CLI must reject:

- missing active project configuration;
- ambiguous project configuration;
- project path escaping its workspace policy;
- project identity conflicting with required run evidence;
- attempts to combine multiple projects in one standard run.

---

## 11. GUI consequences

### 11.1 GUI role

The GUI presents and configures validation for the active project.

### 11.2 No language-profile dropdown

The GUI must not provide a normal active-language profile selector backed by hidden state.

### 11.3 Project display

The GUI should display the resolved active project identity read from project configuration.

### 11.4 Workspace opening

A future GUI may open another workspace as an explicit operation.

Opening another workspace means:

- ending or isolating the current run context;
- loading another project boundary;
- not retaining mixed project results;
- not rewriting the current project;
- not treating the operation as a profile switch inside one project.

### 11.5 Running-state protection

The GUI must not change workspace/project identity while a run is active.

### 11.6 Recent workspaces

A recent-workspace list may exist as disposable convenience state.

It does not make multiple projects simultaneously active.

---

## 12. Validation consequences

### 12.1 File selection

File selection is bounded by the active project source roots.

### 12.2 Static scanning

Static findings are attributed to the active project and project-relative source paths.

### 12.3 Compilation

GF paths include exactly the active project’s source roots plus declared external/RGL roots.

### 12.4 Diagnostics

Diagnostic file identities are normalized against the active project root.

### 12.5 Classification

Direct and downstream classification uses dependencies from the active project only.

### 12.6 Scenarios

Every registered `.gfs` scenario belongs to the active project.

A scenario must not implicitly load another project.

### 12.7 Gold files

Gold files belong to the active project and scenario registry.

### 12.8 PGF

A release PGF is produced for the active project’s declared entrypoints.

### 12.9 Regression comparison

A previous run is compatible only when project identity matches according to the regression contract.

### 12.10 Release gates

Release mode evaluates one active project.

There is no partial release success across multiple profiles.

---

## 13. Run and artifact consequences

### 13.1 Run identity

Every run records one project ID.

### 13.2 Run directory

A run directory belongs to one project even when several workspaces share an external output root.

### 13.3 Summary

`summary.json` contains one active project context.

### 13.4 Manifest

`manifest.json` catalogs artifacts for one run and one project.

### 13.5 Report language

Reports may discuss many GF source modules, but they must not imply multiple active language projects.

### 13.6 Previous runs

Previous-run selection must reject or ignore runs from another project identity.

### 13.7 Artifact naming

Artifact roles and expected names derive from the active project configuration.

### 13.8 Cleanup

Cleanup may operate on the current workspace’s runs or an explicitly selected output scope.

It must not infer cross-project ownership from filename similarity.

---

## 14. Documentation consequences

### 14.1 Active project documents

Every file under:

```text
project/docs/
```

describes one active project.

### 14.2 Project lock

`project/docs/INTERFILE_CONTRACT_LOCK.md` locks relationships for one language project.

### 14.3 No profile qualifiers

Project documentation should not need repetitive qualifiers such as:

```text
for profile A
for profile B
when language C is selected
```

### 14.4 Template documents

`templates/project/docs/` contains generic placeholders for one project.

### 14.5 Framework documents

Framework documentation describes how one project is instantiated, validated, reset, migrated, and released.

### 14.6 Cross-language research

A project may cite or compare other languages in research documentation.

That comparison does not make those languages active GF Wordbench projects in the same workspace.

---

## 15. Template and cloning consequences

### 15.1 Template purpose

`templates/project/` is the canonical blank project structure.

### 15.2 Initialization

Initialization copies or instantiates the template into:

```text
project/
```

and requires replacement of placeholders.

### 15.3 Clone operation

A clone creates another isolated workspace with its own active project.

### 15.4 Reset operation

Resetting a workspace must be explicit.

It should:

- preserve or archive the outgoing project according to policy;
- instantiate a clean project boundary;
- remove stale project-specific identifiers;
- avoid preserving old project state as authority;
- require new project configuration.

### 15.5 No silent overwrite

Framework upgrades must not overwrite active project content from the template.

### 15.6 Template drift

Template changes require compatibility review, but do not automatically mutate existing projects.

---

## 16. Automation and CI consequences

### 16.1 One project per CI job

A GF Wordbench validation job operates on one workspace and one project.

### 16.2 Multiple project portfolio

An organization may run a CI matrix where each matrix entry identifies a separate workspace or repository.

### 16.3 No merged ordinary summary

A portfolio dashboard may aggregate:

```text
project ID
run status
release readiness
artifact links
```

It must not produce one ordinary `summary.json` pretending all projects form one run.

### 16.4 Cache separation

Caches that can contain project-derived artifacts must include project identity in the cache key.

### 16.5 Artifact separation

CI artifact bundles include project identity and run identity.

### 16.6 Release promotion

A release workflow promotes artifacts for one active project.

### 16.7 Cross-project orchestration boundary

Portfolio orchestration is an external integration.

It may not redefine core project configuration or run-result semantics.

---

## 17. Security consequences

### 17.1 Path containment

One active project creates a clear containment root for:

- GF source files;
- scenarios;
- inputs;
- gold files;
- project documents.

### 17.2 Reduced confused-deputy risk

A scenario cannot request a different profile through a hidden selector.

### 17.3 State isolation

Disposable UI state cannot redirect release validation to another language.

### 17.4 Artifact isolation

A required artifact cannot be satisfied by a second profile’s stale output.

### 17.5 Untrusted project handling

Opening another workspace remains an explicit trust decision.

### 17.6 Remaining risks

The decision does not eliminate:

- malicious `.gfs` scripts;
- path traversal;
- unsafe external tools;
- stale generated artifacts;
- untrusted project configuration.

Those remain governed by security and external-tool contracts.

---

## 18. Positive consequences

### 18.1 Simpler mental model

Users can understand:

```text
this workspace
→ this project
→ these sources
→ these scenarios
→ these artifacts
```

### 18.2 Stronger project identity

There is one authoritative identity rather than a current-profile selector plus profile definitions.

### 18.3 Less configuration duplication

Project fields do not require an additional profile namespace.

### 18.4 Safer state

GUI state cannot change the language under validation.

### 18.5 Cleaner reports

Every report belongs to one project.

### 18.6 Cleaner regression comparison

Runs are comparable only within one project identity.

### 18.7 Stronger release semantics

A release status applies to one complete project.

### 18.8 Easier contract documentation

Project interfile contracts can name real modules directly.

### 18.9 Easier project-specific research

Language documentation remains cohesive.

### 18.10 Easier cloning and migration

A new language starts from a known blank boundary.

### 18.11 Lower implementation complexity

No generic profile registry, profile inheritance, or cross-profile path resolver is required.

### 18.12 Lower testing burden

Core tests do not need to cover every operation under profile-switching combinations.

---

## 19. Negative consequences

### 19.1 Multiple workspaces

Users working on several languages maintain several workspaces.

### 19.2 Framework synchronization

Framework changes may need propagation across cloned workspaces when the framework is copied rather than installed as a shared package.

### 19.3 Storage duplication

Separate clones may duplicate framework files and dependencies.

### 19.4 Portfolio operations are external

Cross-language dashboards and batch validation are not core single-run features.

### 19.5 Workspace switching is explicit

A user cannot instantly switch profiles inside one active workspace.

### 19.6 Shared tests require fixtures

Framework tests covering multiple languages use isolated fixtures rather than live profiles.

### 19.7 Migration effort

Changing the active language requires a deliberate reset or new workspace.

---

## 20. Mitigations

### 20.1 Shared package installation

Several workspaces may use one installed GF Wordbench package, provided each workspace retains one active project.

### 20.2 Git operations

Users may use:

- separate clones;
- worktrees;
- branches created from a clean template;
- repository templates.

The chosen Git workflow must preserve one active project per checked-out workspace.

### 20.3 Upgrade tooling

A future framework-upgrade tool may apply reviewed framework changes to a workspace without touching active project content.

### 20.4 Portfolio CI

External automation may iterate across workspaces and show high-level status.

### 20.5 Template provenance

Projects may record which template/framework release initialized them.

### 20.6 Clear lifecycle documentation

Creating, cloning, resetting, and migrating projects are documented explicitly.

### 20.7 Storage optimization

Package caches and immutable toolchains may be shared safely.

Project-derived run artifacts remain isolated.

---

## 21. Alternatives considered

# 21.1 Alternative A — Multi-profile `project.toml`

Example:

```toml
active = "fra"

[projects.fra]
...

[projects.sqi]
...
```

### Advantages

- one repository can hold several projects;
- one GUI can switch among profiles;
- framework code is physically shared;
- portfolio access appears convenient.

### Disadvantages

- active profile becomes a second authoritative identity;
- every project field requires profile scoping;
- state and configuration precedence become complex;
- reports require profile identity everywhere;
- run comparison must reject cross-profile baselines;
- scenarios and gold files need profile namespaces;
- cleanup and artifact ownership become more complex;
- release mode may accidentally validate only one selected profile;
- profile switching while running becomes a new failure mode;
- contract locks become conditional and harder to review.

### Decision

Rejected.

The convenience does not justify the identity, state, schema, testing, and release complexity.

---

# 21.2 Alternative B — `projects/<id>/` monorepo managed by the core

Example:

```text
projects/french/
projects/albanian/
projects/german/
```

### Advantages

- centralized repository;
- one framework copy;
- explicit project directories;
- easier portfolio-wide commits.

### Disadvantages

- core becomes a project portfolio manager;
- every command needs project selection;
- every persisted run needs project-directory resolution;
- global and per-project configuration layers are required;
- cross-project CI semantics become core behavior;
- release and cleanup boundaries become more complex;
- template and active-project semantics blur;
- users may accidentally couple language projects.

### Decision

Rejected for the core product.

An external repository may contain several isolated GF Wordbench workspaces, but each workspace retains one active project.

---

# 21.3 Alternative C — Language selected only by CLI path

Example:

```text
gf-wordbench run --project-root C:/languages/french
```

with no fixed `project/` boundary.

### Advantages

- one package can validate arbitrary roots;
- no workspace duplication;
- convenient automation.

### Disadvantages

- project documentation and validation assets may live anywhere;
- template structure loses authority;
- containment is harder;
- framework docs and project docs are less clearly separated;
- root semantics become variable;
- local GUI state may become the practical selector;
- repository-level project lifecycle becomes weaker.

### Decision

Not selected as the primary workspace model.

A public CLI may accept an explicit workspace or active-project root when the command contract defines it, but the resolved root must expose one canonical project structure and one identity.

---

# 21.4 Alternative D — Simultaneous multi-project run

Example:

```text
gf-wordbench run --all-projects
```

### Advantages

- one command validates a portfolio;
- one combined dashboard;
- potential shared setup cost.

### Disadvantages

- one overall status hides project boundaries;
- partial success semantics become complex;
- run and artifact schemas require nesting;
- cancellation and timeout allocation become cross-project concerns;
- one project failure may block unrelated evidence;
- release status becomes ambiguous;
- raw evidence paths require project namespacing;
- report sizes grow;
- regression baselines require per-project resolution.

### Decision

Rejected.

External orchestration may launch independent runs and aggregate high-level statuses.

---

# 21.5 Alternative E — Branch-per-language in one working directory

### Advantages

- one repository history;
- framework updates can be merged;
- storage may be reduced.

### Disadvantages

- only one branch is checked out per workspace;
- switching branches can leave untracked generated artifacts;
- project identity may not match stale output;
- branch name may be mistaken for project identity;
- concurrent work requires worktrees or clones.

### Decision

Permitted only when each checked-out working tree still contains one active project.

The branch name is not authoritative project identity.

Git worktrees are preferred for simultaneous isolated work.

---

# 21.6 Alternative F — Dynamic Python project plugins

### Advantages

- arbitrary project-specific behavior;
- one framework installation;
- extensible selection logic.

### Disadvantages

- executes project-supplied Python;
- weakens security;
- language-specific behavior leaks into orchestration;
- reproducibility becomes harder;
- versioned plugin API required;
- does not solve project identity cleanly.

### Decision

Rejected.

The active project extends GF Wordbench through configuration, GF sources, `.gfs` scenarios, inputs, gold files, and documentation—not arbitrary Python plugins.

---

# 21.7 Alternative G — Selected design

```text
one isolated workspace
one `project/`
one `project/project.toml`
one active language identity
one project per run
```

### Advantages

- smallest reliable identity model;
- clear ownership;
- deterministic evidence;
- straightforward release semantics;
- strong clone/reset model;
- lower security and testing complexity.

### Disadvantages

- multiple workspaces for multiple languages;
- external orchestration needed for portfolio views.

### Decision

Accepted.

---

## 22. Decision matrix

| Criterion | Single active project | Multi-profile | Core monorepo | Simultaneous run |
|---|---:|---:|---:|---:|
| Identity clarity | High | Medium | Medium | Low |
| Configuration simplicity | High | Low | Medium-low | Low |
| State safety | High | Low | Medium | Medium |
| Evidence attribution | High | Medium | Medium | Low |
| Release clarity | High | Medium-low | Medium | Low |
| Security boundary | High | Medium-low | Medium | Low |
| Cloneability | High | Medium | Medium | Low |
| Portfolio convenience | Medium-low | High | High | High |
| Core implementation cost | Low | High | High | Very high |
| Contract-document clarity | High | Low | Medium | Low |
| Regression comparison safety | High | Medium | Medium | Low |
| Risk of stale-language drift | Low | High | Medium | High |

The selected design optimizes correctness and maintainability over portfolio convenience.

---

## 23. Invariants

The following invariants are mandatory.

```text
INV-001 One workspace contains one active project.
INV-002 One run resolves one project ID.
INV-003 `project/project.toml` owns project identity.
INV-004 Application state does not select the active language.
INV-005 Framework defaults contain no active-language values.
INV-006 Project scenarios belong to the active project.
INV-007 Project gold files belong to the active project.
INV-008 Previous-run comparison requires compatible project identity.
INV-009 Release status applies to one project.
INV-010 Required artifacts belong to the active project.
INV-011 Project documentation describes one active project.
INV-012 Project replacement is explicit.
INV-013 Multiple languages use isolated workspaces or external orchestration.
INV-014 A shared executable may serve several workspaces in separate runs.
INV-015 No ordinary run merges results from multiple projects.
```

---

## 24. Forbidden behavior

The following are prohibited unless this ADR is superseded.

```text
project profile registry in canonical project.toml
hidden active-language selector in GUI state
runtime switching between project profiles during a run
scenario choosing a different project implicitly
gold lookup across project boundaries
cross-project previous-run comparison
combined multi-project summary presented as one ordinary run
release status computed across unrelated projects
framework defaults containing active-language module names
artifact checks satisfied by another project’s output
project identity inferred from branch name
project identity inferred from output directory
automatic project replacement during framework upgrade
multiple active project locks under one canonical project boundary
```

---

## 25. Allowed behavior

The following remain allowed.

```text
several separate GF Wordbench workspaces
one globally installed GF Wordbench executable
one CI portfolio invoking separate workspaces
test fixtures for several languages
historical migration fixtures
comparative linguistic research documents
archived inactive projects outside the active project boundary
explicit workspace opening in a future GUI
explicit project reset or migration
shared immutable GF and RGL installations
```

Archived inactive projects must not be discoverable as active sources during normal validation.

---

## 26. Project lifecycle implications

### 26.1 Create

Creating a project instantiates the template and establishes one new identity.

### 26.2 Clone

Cloning creates a separate workspace.

The clone must replace template or prior-language values intentionally.

### 26.3 Reset

Reset removes or archives the current active project and creates a new blank active project.

### 26.4 Migrate

Migration imports one existing language project into one workspace.

### 26.5 Complete

Completion criteria apply to the active project only.

### 26.6 Release

A release artifact and release evidence bundle belong to the active project.

### 26.7 Archive

An archived project must be moved outside active source discovery or placed in a separate archive/workspace.

### 26.8 Replace

Replacement must invalidate or separate previous-run baselines where project identity differs.

---

## 27. Migration from the predecessor tool

The predecessor audit tool accepted explicit language-related paths through CLI and state.

Migration to GF Wordbench requires:

1. create `project/project.toml`;
2. move project-owned source-selection facts into project configuration;
3. keep machine-local GF and RGL paths in environment/state;
4. remove active-language authority from legacy GUI state;
5. move scenarios, inputs, and gold under `project/validation/`;
6. create or complete project documentation;
7. ensure one project ID is recorded in new runs;
8. prevent old run directories from selecting project identity;
9. retain legacy runs as historical evidence;
10. start new regression baselines only when identity compatibility is established.

Legacy state may be read for migration.

It must not remain an active multi-language profile store.

---

## 28. Implementation requirements

### 28.1 Project loader

The project loader must:

- locate one canonical project configuration;
- validate one project identity;
- reject unsupported multi-profile structures;
- resolve project-relative paths;
- return one typed project configuration;
- avoid reading GUI state for identity.

### 28.2 Bootstrap

Bootstrap must combine:

```text
framework defaults
active project configuration
machine-local environment
explicit run overrides
```

without changing project identity.

### 28.3 Run configuration

`RunConfig` must represent one project context.

### 28.4 Run result

`RunResult` must represent one project context.

### 28.5 State manager

State migration must discard project-owned legacy selectors once canonical project configuration is available.

### 28.6 Reports

Reports must show one project identity.

### 28.7 Manifest

Manifest entries must belong to one run/project root.

### 28.8 Regression selector

Previous-run discovery must compare project identity before accepting a baseline.

### 28.9 CLI

The CLI must reject ambiguous or multi-project invocation.

### 28.10 GUI

The GUI must display the active project rather than own it.

### 28.11 Template

The project template must contain placeholders for one project only.

### 28.12 CI

CI must use one active project per validation job.

---

## 29. Tests

Recommended test files:

```text
tests/contracts/test_single_active_project.py
tests/project/test_project_identity.py
tests/project/test_project_loader.py
tests/project/test_project_reset.py
tests/project/test_project_migration.py
tests/state/test_state_not_project_authority.py
tests/audit/test_cross_project_diff_rejection.py
tests/reports/test_single_project_identity.py
tests/automation/test_one_project_per_job.py
```

Required cases:

```text
one valid project loads
missing project configuration fails
two canonical project configurations fail
multi-profile TOML is rejected
project ID is stable
GUI state cannot override project ID
legacy state project path is discarded after migration
scenario outside project is rejected
gold outside project is rejected
source path traversal is rejected
previous run with same project ID is eligible
previous run with different project ID is rejected
run summary contains one project identity
manifest contains only current run artifacts
shared executable validates workspace A
shared executable validates workspace B separately
combined ordinary run request is rejected
template instantiates one project
reset removes stale active-language identity
framework defaults contain no active-language name
```

---

## 30. Contract checks

A future automated contract checker should verify:

```text
exactly one active project configuration
no profile registry in canonical project schema
no active-language selector in state schema
no language-specific value in framework defaults
all project scenarios remain under project boundary
all gold files remain under project boundary
all project documents refer to one project identity
summary and manifest project identities agree
previous-run comparison rejects other project IDs
release artifact identity matches active project
```

Strict mode should also detect:

```text
old-language names in active project files
inactive project directories inside source discovery
duplicate project IDs inside one workspace
project identity inferred by filename convention
GUI profile-switch code bypassing workspace loading
```

---

## 31. Operational guidance

### 31.1 Working on one language

Use the workspace directly.

### 31.2 Working on several languages

Use separate clones or worktrees.

Example:

```text
C:/work/gfwb-fra/
C:/work/gfwb-sqi/
```

### 31.3 Sharing framework updates

Use a controlled Git merge, package update, or future framework-upgrade workflow.

### 31.4 Sharing GF and RGL

Multiple workspaces may reference the same verified GF executable and RGL source.

### 31.5 Sharing output roots

An external output root may hold runs from several workspaces only when run/project identity and path isolation are guaranteed.

Separate project-specific output roots are simpler and preferred.

### 31.6 Portfolio reporting

Use an external dashboard that links to independent `summary.json` files.

Do not rewrite them into one canonical run summary.

---

## 32. Risks

### 32.1 Framework divergence across copies

Separate copied workspaces may run different GF Wordbench versions.

Mitigation:

- record producer version;
- use controlled upgrades;
- use compatibility CI;
- share package installation where appropriate.

### 32.2 Stale project remnants after reset

A reset may leave old names or generated artifacts.

Mitigation:

- stale-identifier scans;
- clean artifact directories;
- reset checklist;
- new project ID;
- project-completion checks.

### 32.3 User expectation of profile switching

Users may expect a multi-project IDE.

Mitigation:

- document workspace semantics;
- support recent workspace opening as convenience;
- keep profile management outside the core project model.

### 32.4 Cross-project reporting demand

Organizations may need portfolio views.

Mitigation:

- external orchestration;
- stable `summary.json`;
- project IDs;
- run links;
- no core multi-project result schema until justified.

### 32.5 Duplicate storage

Separate workspaces may duplicate files.

Mitigation:

- package installation;
- Git worktrees;
- shared dependency caches;
- shared immutable GF/RGL toolchains.

---

## 33. Rejected shortcuts

The following shortcuts do not satisfy the decision:

### 33.1 Rename-only switching

Renaming `project-fra/` to `project/` dynamically is an implicit profile system when automated without lifecycle controls.

### 33.2 Symlink switching

Pointing `project/` to different language directories through an unrecorded symlink is a hidden selector.

Strict mode should reject or explicitly govern such behavior.

### 33.3 GUI-only selector

A GUI dropdown stored in application state is not authoritative project configuration.

### 33.4 Environment-only selector

An environment variable choosing among project profiles is not acceptable as the canonical architecture.

### 33.5 Branch-name selector

The current Git branch does not define project identity.

### 33.6 Latest-output selector

The last run directory does not define project identity.

### 33.7 Scenario-selected language

A `.gfs` script must not load a different project as an implicit project selector.

---

## 34. Reconsideration triggers

This ADR should be reconsidered only when a concrete, measured requirement demonstrates that isolated workspaces are insufficient.

Potential triggers:

- a required transaction must validate multiple projects atomically;
- a large maintained portfolio makes isolated orchestration demonstrably unsafe or unmanageable;
- shared project assets require first-class cross-project dependency modeling;
- users need synchronized multi-project releases with one formal artifact;
- project duplication causes measured maintenance failure that package/worktree solutions cannot address;
- a stable external consumer requires a portfolio-level schema owned by GF Wordbench.

Convenience alone is not sufficient.

---

## 35. Conditions for superseding this ADR

A replacement multi-project architecture must define and implement:

```text
project registry schema
active-project selection ownership
CLI selection semantics
GUI selection semantics
state semantics
workspace and project path containment
cross-project scenario policy
cross-project gold policy
cross-project artifact ownership
run-result nesting
summary schema
manifest schema
regression baseline rules
release semantics
partial failure semantics
cancellation behavior
cache isolation
security threat model
migration from single-project workspaces
compatibility policy
contract tests
real-GF integration tests
```

The superseding ADR must answer:

1. What is the new authoritative project identity?
2. Can more than one project be active in one run?
3. How are release statuses aggregated?
4. How are artifacts isolated?
5. How are previous runs selected?
6. How is project-specific documentation organized?
7. How are secrets and untrusted scenarios isolated?
8. How are old single-project workspaces migrated?
9. Why external orchestration is insufficient?
10. What measurable benefit justifies the added complexity?

Until all questions are answered and implemented, this ADR remains active.

---

## 36. Compliance checklist

```text
[ ] One canonical `project/project.toml` exists
[ ] Project configuration describes one project
[ ] No project profile registry exists
[ ] No application-state language selector exists
[ ] Framework defaults are language-neutral
[ ] RunConfig identifies one project
[ ] RunResult identifies one project
[ ] Source selection is project-contained
[ ] Scenarios are project-contained
[ ] Inputs are project-contained
[ ] Gold files are project-contained
[ ] Previous-run comparison checks project identity
[ ] Reports show one project identity
[ ] Manifest catalogs one project run
[ ] Release gates apply to one project
[ ] GUI reads project identity
[ ] CLI does not use a hidden profile selector
[ ] CI validates one project per job
[ ] Template instantiates one project
[ ] Reset and migration are explicit
[ ] Multiple languages use isolated workspaces
[ ] Contract tests enforce the decision
```

---

## 37. Examples

### 37.1 Valid: two isolated workspaces

```text
C:/work/french-wordbench/
└── project/project.toml  # project.id = "fra"

C:/work/albanian-wordbench/
└── project/project.toml  # project.id = "sqi"
```

One installed CLI may validate each separately.

### 37.2 Valid: two Git worktrees

```text
C:/work/gfwb-fra/
C:/work/gfwb-sqi/
```

Each checked-out worktree contains one active project.

### 37.3 Valid: portfolio CI

```text
job fra:
  run workspace fra

job sqi:
  run workspace sqi

dashboard:
  show fra status
  show sqi status
```

### 37.4 Invalid: one profile registry

```toml
active_project = "fra"

[projects.fra]
...

[projects.sqi]
...
```

### 37.5 Invalid: state selects language

```json
{
  "selected_language": "sqi"
}
```

when that field determines project identity.

### 37.6 Invalid: scenario switches project

```text
scenario A loads an entrypoint outside the active project root
```

### 37.7 Invalid: combined canonical run

```text
summary.json contains ordinary file_results from unrelated project IDs
```

### 37.8 Valid: comparative research

```text
project/docs/RESEARCH_EVIDENCE.md compares the active language with another language
```

provided only one language project is active and validated.

---

## 38. Traceability

This decision is enforced by or reflected in:

```text
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/EXTENSION_BOUNDARIES.md
docs/validation/VALIDATION_OVERVIEW.md
docs/projects/PROJECT_MODEL.md
docs/projects/CREATING_A_PROJECT.md
docs/projects/CLONING_AND_RESETTING.md
docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md
docs/projects/PROJECT_COMPLETION_CHECKLIST.md
docs/operations/AUTOMATION_AND_CI.md
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/project.toml
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

Specialized documents own implementation details.

This ADR owns the architectural choice itself.

---

## 39. Consequence acceptance

The maintainers explicitly accept:

- separate workspaces for simultaneous language development;
- external rather than core portfolio orchestration;
- explicit project reset/migration;
- the cost of keeping project identity singular;
- the benefit of simpler, safer evidence and release contracts.

The maintainers explicitly reject:

- hidden project selection;
- multi-profile state;
- cross-project ordinary runs;
- framework language-specific defaults;
- profile convenience that weakens release attribution.

---

## 40. Final decision statement

GF Wordbench is a language-project workbench, not a multi-project portfolio manager.

Its framework is reusable, but each workspace is intentionally specialized by one active project.

Therefore:

> One GF Wordbench workspace must resolve exactly one active language project from `project/project.toml`; multiple languages must be represented by isolated workspaces or external orchestration, never by hidden or simultaneous project profiles inside one ordinary GF Wordbench run.
