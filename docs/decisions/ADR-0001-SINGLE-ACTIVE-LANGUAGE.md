# ADR-0001 — One Active Language Project per GF Wordbench Workspace

**ADR ID:** `ADR-0001`  
**Title:** Single Active Language  
**Status:** Accepted  
**Decision date:** 2026-07-22  
**Last reviewed:** 2026-07-24  
**Decision owners:** GF Wordbench maintainers  
**Applies to:** workspace structure, project configuration, CLI, GUI, validation, automation, templates, application state, reports and release artifacts  
**Alignment authority:** `../DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Related decisions:** `ADR-0002-GF-AS-EXECUTION-ENGINE.md`, `ADR-0003-SEPARATE-SCAN-AND-COMPILE.md`, `ADR-0004-NATIVE-GFS-SCENARIOS.md`, `ADR-0011-SEPARATE-PORTFOLIO.md`, `ADR-0012-INDEPENDENT-PRODUCTS.md`  
**Related contracts:** `../INTERFILE_CONTRACT_LOCK.md`, `../PERSISTED_SCHEMA_LOCK.md`, `../../project/docs/INTERFILE_CONTRACT_LOCK.md`, `../../templates/project/docs/INTERFILE_CONTRACT_LOCK.md`

---

## 1. Decision summary

GF Wordbench uses the following project model:

> One GF Wordbench workspace contains exactly one active GF language project, and every ordinary validation run resolves exactly that one project.

The canonical active-project boundary is:

```text
project/
├── project.toml
├── docs/
├── validation/
└── configured GF source tree
```

The active project identity is defined by:

```text
project/project.toml
```

GF Wordbench does not provide:

- a registry of several active project profiles inside one workspace;
- a runtime language-profile selector;
- simultaneous validation of several projects in one ordinary run;
- cross-workspace aggregation or portfolio views;
- project identity selected by GUI state, application state, branch name, output directory or filename inference.

Several languages are supported through separate workspaces. A shared GF Wordbench executable or package may serve those workspaces in separate invocations.

Multi-workspace management and portfolio aggregation belong to the independent companion product `gf-portfolio`.

---

## 2. Context

GF Wordbench validates, diagnoses and prepares release evidence for one Grammatical Framework language project. Its work includes:

- loading project configuration;
- discovering and scanning GF sources;
- compiling configured modules with GF;
- executing native `.gfs` scenarios;
- normalizing evidence and comparing reviewed gold files;
- constructing configured PGF artifacts;
- classifying failures and regressions;
- preserving raw evidence;
- producing reports and manifests;
- applying project release criteria.

These operations depend on project-owned facts such as:

```text
project ID
language code
source root
GF search paths
module naming rules
entrypoints
checkpoints
required and optional scenarios
scenario inputs
gold expectations
expected artifacts
release criteria
linguistic architecture and interfile contracts
```

Allowing several selectable projects inside one workspace would introduce a second project-selection axis into configuration, state, path resolution, scenarios, reports, regression comparison, cleanup and release decisions. The selected design avoids that ambiguity by making the workspace boundary and `project/project.toml` authoritative.

---

## 3. Definitions

### 3.1 Workspace

A **GF Wordbench workspace** is one checked-out, copied, instantiated or worktree-based repository directory containing the framework and one canonical `project/` boundary.

### 3.2 Active project

The **active project** is the project described by `project/project.toml` and represented by the files under the active-project boundary.

### 3.3 Project identity

Project identity includes the stable facts required to attribute configuration, sources, validation evidence and artifacts to one project. At minimum, it includes:

```text
project ID
display name
language code
source root
entrypoints
checkpoints
required scenarios
release targets
```

The exact persisted fields are governed by `docs/PERSISTED_SCHEMA_LOCK.md` and the project configuration reference.

### 3.4 Run

A **run** is one validation execution against exactly one resolved active project.

### 3.5 Multi-project workspace

A **multi-project workspace** is a design in which one workspace stores several independently selectable active project profiles. This ADR rejects that design for GF Wordbench.

### 3.6 Portfolio orchestration

**Portfolio orchestration** discovers, invokes or aggregates several independent GF Wordbench workspaces. It belongs to `gf-portfolio`, not to the GF Wordbench run model.

---

## 4. Decision

### 4.1 One canonical active-project boundary

A GF Wordbench workspace MUST contain exactly one canonical active-project boundary:

```text
project/
```

Its canonical configuration MUST be:

```text
project/project.toml
```

Inactive or archived projects MAY exist outside active discovery, but they MUST NOT be interpreted as additional active projects.

### 4.2 One project per run

Every ordinary run MUST resolve exactly one project identity before project-owned paths or validation assets are used.

A run MUST NOT:

- change project identity while running;
- merge source or validation results from different project identities;
- execute scenarios owned by another project;
- compare gold files owned by another project;
- use another project's run as a regression baseline;
- satisfy required artifacts with another project's output;
- produce one ordinary summary that represents unrelated projects.

### 4.3 One authoritative project identity

`project/project.toml` owns the active project identity.

The following MUST NOT override or silently replace that identity:

```text
GUI state
application state
last-run metadata
output-directory names
current working directory
source filename inference
environment variables alone
Git branch or tag names
scenario contents
gold filenames
```

A command MAY accept an explicit workspace or project root when its public contract requires one. The resolved root MUST expose one canonical project configuration, not a collection of selectable profiles.

### 4.4 No project-profile registry

The canonical project schema MUST represent one project directly. It MUST NOT introduce structures such as:

```text
projects[]
languages[]
profiles[]
active_project
active_language
selected_language
profile_inheritance
```

without an ADR that supersedes this decision and updates every affected schema and contract.

### 4.5 No hidden runtime switch

The normal CLI and GUI MUST NOT select among several project profiles within one workspace through controls or options such as:

```text
--language
--profile
--active-project
--switch-project
```

A GUI MAY open another workspace as an explicit operation. Opening another workspace creates a separate run context; it is not a profile switch inside the current workspace.

### 4.6 Application state is not project authority

Application state MAY retain machine-local convenience values such as:

```text
GF executable path
RGL path
output root
temporary directory
last validation mode
last target
last run pointer
display preferences
recent workspaces
```

Application state MUST NOT own:

```text
active project ID
active language selection
source root
entrypoints
checkpoints
required scenarios
release targets
expected PGF identity
```

Deleting disposable application state MUST NOT change the active project or its validation contract.

### 4.7 Multiple languages use isolated workspaces

A user MAY maintain several languages through separate clones, worktrees, copied workspaces or initialized workspace directories.

Example:

```text
C:/work/gfwb-fra/
└── project/project.toml

C:/work/gfwb-sqi/
└── project/project.toml
```

The same installed GF Wordbench executable or package MAY validate each workspace in a separate invocation.

The invariant is:

```text
one resolved workspace
→ one active project
→ one run identity
```

### 4.8 Project replacement is explicit

Changing the active project requires an explicit lifecycle operation such as:

- initialize;
- clone;
- migrate;
- reset;
- archive and replace;
- open another isolated workspace.

Project replacement MUST NOT occur as a side effect of selecting a GUI item, changing application state, changing an environment variable or following an unrecorded symlink.

### 4.9 Portfolio capabilities belong to `gf-portfolio`

The following capabilities are outside GF Wordbench:

- registry of several Wordbench workspaces;
- cross-workspace discovery and navigation;
- multilingual aggregation;
- portfolio-wide readiness or comparison;
- coordinated portfolio dashboards;
- consumer-specific storage or indexing of Wordbench artifacts.

They belong to the independent product `gf-portfolio` under ADR-0011 and ADR-0012.

The dependency direction is:

```text
gf-portfolio → public versioned GF Wordbench artifacts
GF Wordbench -X→ gf-portfolio runtime, private schemas, storage or configuration
```

GF Wordbench MUST start, validate, report, release and pass its own tests without `gf-portfolio` installed or reachable.

`gf-portfolio` MAY invoke separate Wordbench workspaces and consume their published public artifacts. It MUST NOT redefine the identity or contents of an ordinary GF Wordbench run.

---

## 5. Ownership boundaries

### 5.1 Framework-owned zone

```text
app/
docs/
tests/
templates/
root launchers
package metadata
framework defaults
```

This zone MUST remain language-neutral except for isolated examples, migration fixtures and test fixtures.

### 5.2 Active-project-owned zone

```text
project/project.toml
project/docs/
project/validation/
project GF source tree
project-derived release artifacts
```

This zone owns language-specific names, paths, modules, scenarios, expectations and release rules.

### 5.3 Boundary rule

Framework code MAY interpret generic project configuration fields. It MUST NOT embed the active project's:

```text
language name or code
module suffix
entrypoint or checkpoint names
project-specific scenario IDs
source directory
expected PGF name
linguistic contracts
```

Language-specific values belong to the active project or to isolated fixtures, not to framework defaults.

---

## 6. Configuration and path consequences

### 6.1 Project configuration shape

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

The exact schema, defaults, compatibility and migration rules are owned by `docs/PERSISTED_SCHEMA_LOCK.md` and `docs/configuration/PROJECT_TOML_REFERENCE.md`.

### 6.2 Path containment

Project-owned paths MUST resolve within the boundaries permitted by the project and external-tool contracts.

Project loading MUST reject:

- missing or ambiguous canonical project configuration;
- unsupported profile registries;
- incomplete project identity;
- project-owned paths that escape allowed containment;
- scenarios, inputs or gold files that resolve to another project;
- entrypoints or release artifacts inconsistent with the active project.

### 6.3 Environment values

Machine-local values MAY differ by workspace, including the GF executable, RGL root, output root and temporary directory. They configure execution but MUST NOT define project identity.

---

## 7. CLI and GUI consequences

### 7.1 CLI

Each CLI invocation MUST resolve one workspace and one project before validation begins.

Validation modes such as `quick`, `checkpoint`, `release` or `diagnostic` MAY change validation scope. They MUST NOT change project identity.

Machine-readable CLI output MUST identify or unambiguously resolve:

```text
project ID
run ID
run directory
canonical validation mode
overall run status
```

The CLI MUST reject requests that combine unrelated projects in one ordinary run.

### 7.2 GUI

The GUI displays and operates on the project identity loaded from project configuration. It does not own that identity.

The GUI MUST NOT:

- expose a hidden active-language profile selector;
- change workspace or project identity while a run is active;
- retain mixed results when another workspace is opened;
- rewrite the current project merely because another workspace is selected.

A recent-workspace list MAY exist as disposable convenience state. It does not make several projects simultaneously active.

---

## 8. Validation and artifact consequences

### 8.1 Source selection and scanning

Source selection is bounded by the active project's configured source roots. Static findings use project-relative identities and belong to the active project.

### 8.2 GF compilation and PGF build

GF search paths include the active project's declared roots and permitted external or RGL roots. Compiled modules and PGF artifacts MUST be attributable to the active project and its declared entrypoints.

### 8.3 Diagnostics

Diagnostic paths are normalized against the active project. Direct and downstream classification MUST use dependencies from that project only.

### 8.4 Scenarios, inputs and gold files

Every registered `.gfs` scenario, scenario input and gold expectation belongs to the active project. Cross-project lookup or implicit project switching is prohibited.

### 8.5 Regression comparison

A previous run is eligible as a regression baseline only when its project identity is compatible under the regression contract. Runs from another project identity MUST be rejected or excluded.

### 8.6 Run directories and reports

Every run directory, summary, manifest, report and evidence bundle belongs to one project and one run.

`summary.json` and `manifest.json` MUST agree on project identity. An ordinary report MAY discuss several GF modules, but it MUST NOT imply that several language projects were active in the run.

### 8.7 Cleanup

Cleanup MAY operate on the current workspace's run scope or on an explicitly selected output scope. It MUST NOT infer cross-project ownership from filename similarity or remove another project's artifacts accidentally.

---

## 9. Templates and project lifecycle

### 9.1 Template

`templates/project/` is the reusable blank structure for one active project. It MUST contain placeholders rather than an active language identity or a Portfolio registry.

### 9.2 Initialization

Initialization instantiates the template into `project/` and requires replacement of project placeholders.

### 9.3 Clone and migration

A clone creates another isolated workspace. Migration imports one existing language project into one workspace and establishes one canonical project identity.

### 9.4 Reset and replacement

Reset or replacement MUST:

- preserve or archive the outgoing project according to policy;
- create one clean active-project boundary;
- remove stale project-specific identifiers;
- separate incompatible previous-run baselines;
- require a complete new project configuration.

### 9.5 Framework upgrades

Framework upgrades MUST NOT overwrite active project content from the template. Template evolution does not mutate existing projects automatically.

---

## 10. Automation and CI

A GF Wordbench validation job operates on one workspace and one project.

An organization MAY run a matrix of isolated Wordbench jobs. `gf-portfolio` or another external orchestrator MAY aggregate their high-level public results, including:

```text
project ID
run status
release status
artifact links
```

The orchestrator MUST NOT merge internal run objects from unrelated projects into one ordinary GF Wordbench summary.

Caches and artifact bundles that contain project-derived data MUST include project identity and run identity in their isolation rules.

A release workflow promotes artifacts for one active project.

---

## 11. Security consequences

The single-project boundary establishes a clear containment root for project configuration, GF sources, scenarios, inputs, gold files and project documents.

The design reduces:

- hidden project redirection through GUI state;
- cross-project gold or artifact substitution;
- accidental regression comparison against another project;
- confused-deputy behavior caused by profile selectors;
- cleanup across unrelated project boundaries.

It does not remove the need to validate untrusted configuration, `.gfs` scripts, external-tool paths, path traversal, generated artifacts or process execution. Those controls remain governed by the security and external-tool contracts.

---

## 12. Consequences

### 12.1 Positive consequences

- one authoritative project identity;
- deterministic evidence attribution;
- simpler configuration and state semantics;
- clearer project/framework ownership;
- safer regression and release decisions;
- simpler cloning, reset and migration;
- lower testing and security complexity;
- cohesive project-specific documentation.

### 12.2 Accepted costs

- users working on several languages maintain several isolated workspaces;
- copied workspaces may require coordinated framework upgrades;
- storage may be duplicated when package installation or worktrees are not used;
- portfolio operations require `gf-portfolio` or another external orchestrator;
- changing the active project is an explicit lifecycle operation.

These costs are accepted because they preserve project identity and release attribution.

---

## 13. Alternatives rejected

### 13.1 Multi-profile `project.toml`

Rejected because it introduces a second active-project selector and requires profile scoping across configuration, state, scenarios, reports, artifacts, regression and release rules.

### 13.2 Core `projects/<id>/` monorepo

Rejected because it turns GF Wordbench into a portfolio manager and requires project selection in every command and persisted contract.

### 13.3 Simultaneous multi-project run

Rejected because ordinary run status, cancellation, evidence, artifact ownership, regression baselines and release semantics would become nested and partially successful across unrelated projects.

### 13.4 Environment-, branch-, symlink- or GUI-selected project

Rejected because each creates a hidden or weak project authority outside the canonical project configuration.

### 13.5 Dynamic project Python plugins

Rejected because arbitrary project-supplied Python weakens security, reproducibility and the generic framework boundary.

### 13.6 Selected design

```text
one isolated workspace
one `project/`
one `project/project.toml`
one active language identity
one project per ordinary run
```

This is the accepted design.

---

## 14. Mandatory invariants

```text
INV-001 One workspace contains one canonical active project.
INV-002 One ordinary run resolves one project ID.
INV-003 `project/project.toml` owns project identity.
INV-004 Application state does not select the active project.
INV-005 Framework defaults contain no active-language values.
INV-006 Project scenarios, inputs and gold files belong to the active project.
INV-007 Previous-run comparison requires compatible project identity.
INV-008 Release status applies to one project.
INV-009 Required artifacts belong to the active project and run.
INV-010 Project documentation describes one active project.
INV-011 Project replacement is explicit.
INV-012 Multiple languages use isolated workspaces.
INV-013 A shared executable may serve several workspaces in separate runs.
INV-014 No ordinary run merges results from unrelated projects.
INV-015 Portfolio aggregation belongs outside GF Wordbench.
INV-016 GF Wordbench has no runtime dependency on `gf-portfolio`.
```

---

## 15. Required contract coverage

The framework contracts and tests MUST cover at least:

```text
one valid canonical project loads
missing or ambiguous project configuration is rejected
multi-profile project configuration is rejected
project identity remains stable during a run
application state cannot override project identity
project-owned path traversal is rejected
scenarios, inputs and gold files outside the project are rejected
previous runs from another project are rejected
summary and manifest project identities agree
ordinary combined multi-project runs are rejected
template initialization creates one project
reset removes stale project identity and incompatible baselines
framework defaults remain language-neutral
GF Wordbench operates without `gf-portfolio`
```

These checks are maintained with the owning loaders, schemas, reports, lifecycle operations and integration tests.

---

## 16. Traceability

This decision is reflected in:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/PRODUCT_BOUNDARIES.md
docs/architecture/EXTENSION_BOUNDARIES.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/projects/PROJECT_MODEL.md
docs/projects/CREATING_A_PROJECT.md
docs/projects/CLONING_AND_RESETTING.md
docs/projects/MIGRATING_AN_EXISTING_LANGUAGE.md
docs/operations/AUTOMATION_AND_CI.md
project/project.toml
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/project.toml
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

Specialized owner documents define the detailed schemas, paths, lifecycle operations and validation behavior. This ADR owns the architectural choice that project identity is singular per workspace and per ordinary run.

---

## 17. Reconsideration

This ADR may be superseded only by a decision that defines, as one coordinated contract change:

```text
project registry schema
project-selection authority
CLI and GUI selection semantics
application-state semantics
path containment
scenario, input and gold ownership
run-result and artifact nesting
regression-baseline rules
release and partial-failure semantics
cache isolation
security model
migration from single-project workspaces
compatibility and contract tests
```

The replacement decision must explain why isolated workspaces and external portfolio orchestration no longer satisfy the product requirements.

---

## 18. Decision statement

GF Wordbench is a single-language-project workbench, not a multi-project portfolio manager.

> One GF Wordbench workspace resolves exactly one active language project from `project/project.toml`; several languages use isolated workspaces, while `gf-portfolio` may consume their public artifacts without becoming a GF Wordbench runtime dependency.
