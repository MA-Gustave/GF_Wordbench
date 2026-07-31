# GF Wordbench — Configuration Overview

**Document ID:** `GF-WB-CONFIGURATION-OVERVIEW`  
**Status:** Normative overview  
**Implementation status:** Not established by this documentation update  
**Verification status:** Requires current code and reproducible test evidence  
**Applies to:** framework defaults, path-resolved language startup, optional validation profiles, application state, environment resolution, CLI, GUI, bootstrap, validation runs, reports, migrations and tests  
**Owner:** GF Wordbench maintainers  
**Canonical path:** `docs/configuration/CONFIGURATION_OVERVIEW.md`  
**Configuration contract:** `2.0.0`  
**Governing decision:** `docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md`  
**Superseded configuration model:** catalog-driven startup and mandatory `project/project.toml` startup authority  
**Last reviewed:** `2026-07-30`

---

## 1. Purpose

This document defines the configuration architecture of GF Wordbench.

It explains:

- which configuration sources exist;
- what each source is allowed to own;
- how a user-selected GF language path becomes a resolved language context;
- how existing Wordbench selection, path, preflight, compilation and diagnostic services are reused;
- which values may be derived, selected, overridden or remembered;
- which values must remain explicit before execution;
- how machine-local paths remain separate from portable validation policy;
- how an optional validation profile extends a resolved language without becoming mandatory startup configuration;
- how one immutable run configuration is produced;
- how configuration errors and ambiguities are reported;
- how CLI and GUI remain semantically equivalent;
- how persisted configuration and state are migrated;
- how the system avoids duplicated, hidden or competing configuration.

This document is the normative overview of configuration ownership and resolution.

Detailed field definitions belong to:

```text
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/gf/GF_PATH_RESOLUTION.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
```

Exact persisted field names and schema versions remain owned by their schema references and locks. Conceptual examples in this overview do not independently create persisted contracts.

---

## 2. Core rules

### 2.1 One authoritative owner per value

> Every configuration value has one authoritative owner, one documented resolution path and one effective value for a run.

Configuration must not be assembled through unrelated modules reading different files, widgets, environment variables or state independently.

### 2.2 One explicit language selection

Normal startup begins with one explicit user or automation selection:

```text
one GF language directory
or
one .gf file inside a GF language directory
```

Examples:

```text
C:/mycode/Grammatical_Framework/gf-rgl/src/english
C:/mycode/Grammatical_Framework/gf-rgl/src/english/LangEng.gf
C:/mycode/Grammatical_Framework/gf-rgl/src/english/AdjectiveEng.gf
```

The selected path is the initial machine-local input. It is not by itself the complete executable configuration.

### 2.3 One resolved language context

The selected path is processed through the path-resolved language startup flow and produces one immutable `ResolvedLanguageContext`.

The main runtime and ordinary run construction consume that context. They do not rediscover language identity or source roots independently.

### 2.4 One active language per runtime and run

A GF Wordbench runtime has:

```text
no loaded language
or
exactly one resolved language context
```

An ordinary run records exactly one language identity and one source context.

A language switch destroys the old runtime and resolves a new context. It does not mutate an active context in place.

### 2.5 Optional validation policy

`project/project.toml`, language bundles, scenarios, gold files and release documentation may extend a resolved language as an explicit validation profile.

They are not required to:

```text
open a language directory
browse GF sources
select files
run static scans
perform targeted GF compilation
inspect diagnostics
```

### 2.6 Existing services remain authoritative

Path-resolved startup must reuse existing public Wordbench contracts for:

```text
source selection
path validation
GF path resolution
preflight
GF execution
diagnostic normalization
run evidence
state persistence
```

The startup probe coordinates these services. It does not reimplement them.

### 2.7 No catalog authority

A generated RGL catalog may exist as diagnostics, inventory, documentation or migration assistance.

It is not a normal startup authority and must not determine which languages are loadable.

---

## 3. Product and session boundary

### 3.1 Wordbench remains single-language at runtime

GF Wordbench does not become a multi-project portfolio manager.

It may let a user choose or replace the active language, but only one resolved language runtime exists at a time.

### 3.2 Language selection is not portfolio management

The introduction window may offer:

```text
Open last language
Choose language directory or GF file
Configure GF environment
Quit
```

This is a startup selection surface, not a registry of simultaneously active projects.

### 3.3 Portfolio responsibilities remain external

GF Wordbench does not own:

- a database of many workspaces;
- cross-language dashboards;
- aggregate release readiness;
- portfolio-wide comparisons;
- synchronization between several active language runtimes.

Those responsibilities remain outside the product boundary defined by the portfolio ADRs.

---

## 4. Configuration source model

GF Wordbench uses the following configuration sources:

```text
package metadata
framework defaults
explicit selected language path
language-probe observations
resolved language context
optional validation profile
application state
environment and controlled discovery
explicit CLI or GUI run input
runtime-derived values
```

These sources do not have equal authority over every domain.

A source may define, select or override a value only when its ownership contract permits it.

---

## 5. Configuration sources at a glance

| Source | Typical owner | Purpose | Portable | Persisted | May define validation policy |
|---|---|---|---:|---:|---:|
| Package metadata | Package/build system | Application identity and version | Yes | Yes | No |
| Framework defaults | Framework configuration owner | Language-neutral operational defaults | Yes | Yes | No |
| Selected language path | User, CLI or GUI | Explicit startup intent | No | Optionally in local state | No |
| Language-probe observations | Language probe plus public services | Candidate source and path facts | No | Run evidence when relevant | No |
| `ResolvedLanguageContext` | Language-resolution application service | Effective language and source authority | Run-scoped | Run evidence | No |
| Optional validation profile | Project/profile owner | Scenarios, checkpoints, entrypoints, release policy | Yes | Yes | Yes |
| Application state | State service | Disposable local preferences and last paths | No | Yes | No |
| Environment/discovery | Environment and path resolvers | Local tools and machine paths | No | Usually no | No |
| CLI input | CLI user or automation | Explicit startup/run selections and allowed overrides | No | Run evidence | No |
| GUI input | GUI user | Same semantics as CLI | No | State and run evidence | No |
| Runtime-derived values | Bootstrap and orchestrator | Run ID, effective targets, artifacts and budgets | Run-specific | Run evidence | No |

---

## 6. Package metadata

### 6.1 Purpose

Package metadata owns:

```text
application name
application version
package version
supported Python requirement
distribution identity
```

### 6.2 Single source of truth

Application version must come from one package metadata source.

It must not be duplicated independently in:

- CLI;
- GUI;
- reports;
- application state;
- validation profiles;
- documentation constants;
- persisted schema versions.

### 6.3 Package version versus schema versions

These values are distinct:

```text
GF Wordbench package version
configuration contract version
application-state schema version
validation-profile schema version
run-summary schema version
manifest schema version
scenario-output version
```

A reader must not infer one version from another.

---

## 7. Framework defaults

### 7.1 Purpose

Framework defaults provide safe, language-neutral operational values.

Examples:

```text
default validation mode
default timeout classes
default report behavior
default output limits
default state filename
default encoding policy
default bounded-discovery limits
default log-retention behavior
```

### 7.2 Ownership

Framework defaults have one designated owner.

Bootstrap consumes these defaults but must not redefine competing copies.

### 7.3 Language neutrality

Framework defaults must not contain active-language assumptions.

Prohibited production defaults include:

```text
English
Eng
LangEng.gf
GrammarEng.gf
src/english
language-specific scenario IDs
language-specific accepted warnings
```

Language-specific values may appear only in clearly labeled examples, fixtures or tests.

### 7.4 Safe fallback rule

A default may fill an optional operational value.

A default must not invent a correctness-critical language fact.

```text
default report detail level       allowed
default finite timeout            allowed
default output-size limit         allowed
default probe iteration limit     allowed
invented language directory       prohibited
invented module suffix            prohibited
invented entrypoint               prohibited
invented required scenario        prohibited
invented release target           prohibited
```

---

## 8. Explicit selected language path

### 8.1 Role

The selected language path expresses user intent for startup.

It is the only mandatory language-specific input for normal path-resolved startup.

### 8.2 Accepted path kinds

Accepted inputs are:

```text
readable directory
readable .gf file
```

A selected directory becomes the candidate language directory.

A selected `.gf` file keeps that file as the focused target and uses its parent as the candidate language directory.

### 8.3 Focused file semantics

Selecting:

```text
.../src/english/AdjectiveEng.gf
```

means:

```text
candidate language directory = .../src/english
focused target               = AdjectiveEng.gf
```

It does not silently convert `AdjectiveEng.gf` into the primary language entrypoint.

### 8.4 Selected path is not portable identity

Absolute paths are machine-local.

Portable language identity is derived only after the RGL source root and relative language directory are validated.

### 8.5 Explicit selection precedence

An explicit current selection outranks remembered paths.

The application must not replace an explicit selection with:

- the last successful language;
- a project profile path;
- a catalog entry;
- the first candidate found under an RGL root;
- the newest modified directory.

---

## 9. Language probe

### 9.1 Purpose

The language probe converts one selected path into either:

```text
ResolvedLanguageContext
needs-user-input result
invalid-selection result
unsupported-layout result
capability-unavailable result
internal-error result
```

### 9.2 Ownership

The probe is an application service owned by the active-language or project functional module.

A recommended conceptual name is:

```text
LanguageProbeService
```

### 9.3 Probe responsibilities

The probe may:

- classify the selected path as file or directory;
- derive the candidate language directory;
- locate a bounded candidate RGL source root from ancestors;
- invoke the existing selection service;
- consume existing module-name extraction;
- classify standard RGL module-role candidates;
- submit path requirements to the existing GF path resolver;
- invoke structural preflight;
- consume canonical diagnostics;
- request user input when ambiguity remains;
- publish one immutable resolved context.

### 9.4 Probe non-responsibilities

The probe must not independently implement:

- recursive source enumeration rules;
- include or exclude filtering;
- symlink and containment policy;
- GF command construction;
- process execution;
- GF parsing or type checking;
- complete GF dependency parsing;
- diagnostic text scraping when typed diagnostics exist;
- report writing;
- state-file I/O.

### 9.5 Bounded discovery

The probe may inspect only:

```text
the explicit selected path
its ancestors while locating a supported source root
the selected language directory for source inventory
the approved RGL source root for bounded exact-name remediation
```

It must not search unrelated drives, home directories or arbitrary repositories.

---

## 10. Candidate and resolved models

### 10.1 Language candidate

A language candidate is provisional and non-executable.

It may contain:

```text
selected path
selected path kind
candidate language directory
candidate RGL source root
candidate RGL root
focused file
candidate portable language key
candidate module suffixes
candidate entrypoints
candidate GF path requirements
structural diagnostics
```

### 10.2 Resolved language context

The resolved context is the single language and source authority for the main runtime.

Conceptual fields include:

```text
language_key
selected_path
selected_path_kind
language_directory
rgl_source_root
rgl_root
selected_file
focused_target
module_suffix
available_entrypoints
source_inventory or stable inventory reference
GF path requirements
structural diagnostics
base capability statuses
resolution provenance
```

The optional validation profile remains a separate run-configuration input and is not embedded as language authority in the resolved context.

### 10.3 Portable language key

For a standard checkout, the base portable language key is the validated language directory relative to the RGL source root.

Example:

```text
rgl_source_root  = C:/mycode/Grammatical_Framework/gf-rgl/src
language_dir     = C:/mycode/Grammatical_Framework/gf-rgl/src/english
language_key     = english
```

A persisted schema may namespace this value, for example:

```text
rgl:english
```

The exact serialized representation belongs to the persisted-schema contract.

### 10.4 Module suffix

A suffix such as `Eng` is a separate optional fact.

It may be accepted when standard module roles uniquely support it.

It must not be invented solely from the directory name.

### 10.5 Immutability

After publication, the resolved context is immutable.

Changing any of these values requires a new resolution and runtime:

```text
selected path
language directory
RGL source root
GF path requirements
portable language identity
module suffix
```

A validation-profile change requires a new run-configuration resolution. It requires a new language resolution only when the profile conflicts with or attempts to change language-context facts.

---

## 11. Optional validation profiles

### 11.1 Purpose

A validation profile adds explicit project policy to a resolved language context.

Typical profile domains include:

```text
project display identity
source include and exclude rules
entrypoints
checkpoints
required and optional scenarios
inputs and golds
release targets
expected artifacts
release gates
known limitations
project-specific documentation
```

### 11.2 `project/project.toml`

`project/project.toml` remains supported as an explicit validation profile.

It is no longer mandatory before the user can open or inspect a language directory.

### 11.3 Explicit profile loading

A profile is loaded only when:

- explicitly selected by the user;
- explicitly supplied by CLI or automation; or
- referenced through another reviewed configuration contract.

Wordbench must not silently search ancestors and adopt the first `project.toml` it finds.

### 11.4 Profile authority

When loaded, the profile is authoritative for the policy it explicitly owns, such as:

- configured checkpoint sets;
- configured entrypoints for a validation mode;
- scenario registry;
- gold requirements;
- release scope;
- expected artifacts.

It is not authoritative for:

- the current machine’s absolute GF executable;
- the current output root;
- the current explicit selected path;
- a source path outside the resolved language context;
- application presentation preferences.

### 11.5 Profile conflict rule

A profile must agree with the resolved language context.

Conflicts are configuration errors.

Examples:

```text
profile source root outside resolved language directory
profile language key disagrees with resolved language key
profile target escapes approved roots
profile GF path selects an unrelated language directory
profile scenario or gold belongs to another language
```

There is no precedence rule that silently makes one conflicting authority win.

### 11.6 Language bundles

A language-specific Wordbench bundle may exist as one optional profile and asset layout.

It is not required for normal startup.

A known module suffix must not cause Wordbench to invent or require:

```text
wordbench/languages/<suffix>/language.toml
```

### 11.7 Templates

Project and language-profile templates may initialize advanced validation assets.

Templates are authoring tools. They do not participate in runtime language resolution.

---

## 12. Application state

### 12.1 Purpose

Application state stores disposable machine-local preferences.

Deleting the state file must not damage a language source tree or validation profile.

### 12.2 Appropriate state values

Application state may store:

```text
last selected language path
last selected validation profile
last selected GF executable
last selected output root
last selected mode
last selected target
timeout preferences
detail-retention preference
previous-run diff preference
last run directory
last summary path
GUI presentation preferences
```

A separately selected or derived RGL root may also be remembered as a convenience value when the state schema permits it.

### 12.3 Prohibited state authority

Application state must not be authoritative for:

```text
portable language identity
validated language directory
validated RGL source root
module suffix
source inventory
entrypoints
checkpoints
required scenarios
release gates
expected PGF
current RunResult
is_running across restarts
```

### 12.4 Last-language behavior

`Open last language` reads the remembered selected path and reruns full resolution.

The application must not deserialize and trust a previously resolved executable context.

### 12.5 Stale path behavior

A missing, unreadable or structurally invalid remembered path produces a structured warning or error and returns the user to language selection.

It must not trigger a filesystem-wide search.

### 12.6 Safe corruption behavior

A missing or malformed state file must not prevent source use when required inputs can otherwise be resolved.

The application should:

1. report or log the state problem;
2. use safe defaults;
3. avoid overwriting malformed source state until policy permits;
4. continue to the language-selection surface.

### 12.7 Atomic writes

State writes use atomic replacement where supported.

A failed state write must not destroy the last valid state or invalidate a successfully resolved language context.

---

## 13. Environment configuration

### 13.1 Purpose

Environment configuration supplies machine-specific values required for execution.

Typical values:

```text
GF executable
optional explicit RGL root
output root
temporary root
optional diagnostic-tool locations
locale policy
approved process environment overrides
```

### 13.2 Sources

Machine-specific values may come from:

- explicit CLI input;
- explicit GUI input;
- application state;
- documented environment variables;
- optional executable discovery;
- platform-specific defaults;
- controlled `PATH` lookup.

### 13.3 Environment is not validation policy

Environment resolution must not define:

- required scenarios;
- release gates;
- expected linguistic behavior;
- project-owned golds;
- a profile-owned entrypoint list;
- a portable language identity that conflicts with the resolved source context.

### 13.4 Explicit values before inherited environment

Correctness-critical explicit values precede inherited process environment.

For the GF executable:

```text
explicit CLI or GUI value
→ explicit environment configuration
→ valid application-state preference
→ documented environment variable
→ controlled PATH discovery
→ unavailable
```

### 13.5 RGL root semantics

The RGL source root is normally derived from the explicit selected language path.

An explicit RGL root may be supplied when:

- the source tree is nonstandard;
- automatic ancestor resolution is ambiguous;
- automation requires a fixed approved root;
- security policy restricts discovery.

An explicit root must contain the selected language path or satisfy the explicit nonstandard profile contract.

### 13.6 Secrets

GF Wordbench must not persist or report:

- access tokens;
- private keys;
- passwords;
- complete environment dumps;
- unrelated private variables.

Only approved, relevant environment values may be recorded.

---

## 14. Explicit CLI and GUI input

### 14.1 Purpose

CLI and GUI collect explicit startup and run selections.

Typical inputs include:

```text
selected language path
optional validation profile
mode
target
GF executable
optional explicit RGL root
output root
timeout override
detail level
previous-run comparison
diagnostic subprofile
```

### 14.2 Shared semantics

Equivalent CLI and GUI inputs must produce equivalent normalized requests and resolved configuration.

The interfaces may differ in presentation.

They must not differ in:

- language-probe behavior;
- selected-path interpretation;
- source enumeration;
- GF path construction;
- GF executable resolution;
- profile loading;
- mode meaning;
- timeout semantics;
- release-gate enforcement;
- persisted result fields.

### 14.3 Interface input is not policy authority

An interface may select among allowed policies.

It must not redefine those policies.

```text
choose a language directory                   allowed
choose a focused .gf target                   allowed
choose a configured checkpoint                allowed
increase a timeout                            allowed
add optional diagnostics                      allowed
silently replace focused file with LangX      prohibited
remove required release scenario              prohibited
disable release manifest verification         prohibited
choose first ambiguous suffix automatically   prohibited
```

### 14.4 Noninteractive ambiguity

In noninteractive mode, unresolved ambiguity is an explicit error unless the caller supplies the required choice.

Automation must not accept an implicit first candidate.

---

## 15. Runtime-derived configuration

Some values exist only after language resolution, bootstrap and orchestration.

Examples:

```text
portable language key
resolved language directory
resolved RGL source root
run ID
run directory
resolved native paths
effective GF search path
resolved executable
normalized mode
resolved target set
ordered selected files
ordered selected checkpoints
ordered selected scenarios
effective timeout per stage
effective evidence level
previous compatible run
artifact paths
effective capability statuses
```

These values are derived facts, not new configuration authorities.

They must be recorded in run evidence where relevant.

---

## 16. Configuration domains and owners

| Domain | Authoritative owner |
|---|---|
| Application name and package version | Package metadata |
| Language-neutral defaults | Framework configuration |
| Current selected path | Explicit current GUI, CLI or automation input |
| Remembered selected path | Application state |
| Candidate source facts | Language probe using public selection/path services |
| Portable language identity | `ResolvedLanguageContext` |
| Language directory and RGL source root | `ResolvedLanguageContext` |
| Source enumeration behavior | Existing selection service |
| Standard module-role candidates | Language probe classification over selected inventory |
| Effective GF path | Central GF path resolver |
| Profile-owned source filters | Explicit validation profile |
| Profile entrypoints and checkpoints | Explicit validation profile |
| Scenario registry | Explicit validation profile |
| Release requirements | Explicit validation profile plus framework safety invariants |
| GF executable location | Explicit environment resolution |
| Output root | Explicit environment resolution |
| Mode selection | Explicit run input or documented default |
| Mode semantics | Framework validation contract |
| Target selection | Explicit run input and validated candidate/profile set |
| Run paths | Run-path builder |
| Artifact filenames | Artifact model and schema owner |
| Stage timeouts | Framework defaults plus permitted override |
| Effective run configuration | Bootstrap and run-config builder |
| Run truth | Structured run result and summary |

A value must not have two competing owners.

---

## 17. Domain-specific precedence

There is no universal precedence list for all configuration.

Resolution depends on the domain.

### 17.1 Language-selection precedence

```text
explicit current selected path
→ explicitly requested “Open last language” remembered path
→ needs user input
```

Wordbench must not infer startup identity from:

- previous run output;
- a GUI label;
- framework defaults;
- a global catalog;
- a source filename outside the selected path;
- an unrelated project profile.

### 17.2 Language identity precedence

```text
validated selected path
→ validated language directory relative to validated RGL source root
→ portable language key
```

A profile may add presentation metadata or policy, but it cannot replace a conflicting resolved language identity.

### 17.3 Validation-profile precedence

```text
explicit profile selection
→ no profile
```

There is no implicit ancestor search.

When present, the profile owns only its declared policy domains.

### 17.4 GF executable precedence

```text
explicit CLI or GUI value
→ explicit environment configuration
→ valid application-state preference
→ documented environment variable
→ controlled PATH discovery
→ capability unavailable
```

The resolved executable is recorded and reused.

### 17.5 RGL source-root precedence

```text
validated root derived from explicit selected path
→ compatible explicit root override
→ needs user input or unsupported layout
```

A remembered root may assist the user, but it must be revalidated against the selected path.

### 17.6 GF path precedence

```text
resolved language directory requirement
→ explicit compatible validation-profile requirements
→ framework-approved standard aliases or shared paths
→ documented controlled environment fallback
→ configuration failure for required entries
```

The central resolver owns ordering, normalization, containment, deduplication and serialization.

### 17.7 Output-root precedence

```text
explicit CLI or GUI value
→ automation value
→ valid application-state preference
→ framework local default
```

The output root must be writable and separate from protected source roots.

### 17.8 Mode precedence

```text
explicit CLI or GUI selection
→ explicit automation selection
→ profile default when defined
→ framework default
```

A default must never silently choose `release`.

### 17.9 Target precedence

```text
explicit focused target or run target
→ explicit profile-defined mode target
→ detected candidate presented to the user
→ failure when the mode requires a target
```

A selected `.gf` file remains the focused target unless the user explicitly chooses another target.

### 17.10 Timeout precedence

```text
explicit permitted run override
→ profile operation-specific override when supported
→ framework operation-class default
```

All external execution timeouts remain finite.

### 17.11 Release-policy precedence

```text
explicit validation-profile release policy
→ framework mandatory safety invariants
```

CLI, GUI, state and environment cannot weaken release policy.

---

## 18. Override classes

Every override is one of three classes.

### 18.1 Strengthening override

Adds validation or evidence.

Examples:

```text
add scenarios
add entrypoints
enable strict scan
retain more detail
verify additional artifacts
compare an additional baseline
```

Generally allowed when path and trust policies succeed.

### 18.2 Neutral override

Changes local execution without weakening truth.

Examples:

```text
change output root
select an equivalent GF executable
increase timeout
change GUI presentation
enable CPU statistics
```

Allowed when valid and recorded.

### 18.3 Weakening override

Removes required validation.

Examples:

```text
skip required compile
skip required scenario
skip required gold
skip required PGF
ignore required artifact
disable release gate
```

Allowed only in explicitly defined non-release exploratory workflows.

Never allowed to preserve release eligibility.

---

## 19. Bootstrap responsibility

### 19.1 Two-phase composition

Bootstrap has two distinct composition phases.

#### Startup runtime

The startup runtime contains only the services required to select and resolve a language:

```text
package metadata
framework defaults
application-state reader
language probe
selection service
path and environment resolvers
introduction GUI or CLI request handler
```

#### Language runtime

The main runtime is composed only after one `ResolvedLanguageContext` exists.

It may include:

```text
main-window view models
run orchestration
static scan
GF compilation
scenario execution
reporting
artifact persistence
previous-run resolution
```

### 19.2 Startup sequence

Bootstrap should:

1. load package metadata;
2. load framework defaults;
3. load application state safely;
4. collect an explicit selected language path or remembered-path action;
5. invoke the language probe;
6. resolve structural paths and source inventory through existing services;
7. return structured ambiguity or failure when needed;
8. construct one immutable resolved language context;
9. persist the successful selected path as best-effort local state;
10. compose the main runtime;
11. collect run-specific mode and target input;
12. load an optional explicit validation profile;
13. resolve environment paths;
14. validate profile/context compatibility;
15. construct the immutable run configuration;
16. return errors before dependent execution.

### 19.3 Bootstrap prohibitions

Bootstrap must not:

- implement source enumeration independently;
- invoke GF directly;
- run scenarios while resolving base configuration;
- write reports;
- display GUI-specific dialogs from domain or application services;
- infer language identity from run history;
- silently rewrite profiles;
- create missing source directories;
- hide missing required values;
- create a general service locator.

---

## 20. Capability model

A resolved language context exposes base source capabilities. The resolved run configuration finalizes capabilities that depend on the selected profile, environment, GF executable, mode and target.

### 20.1 `source-ready`

Requirements:

- selected path is valid;
- language directory is readable;
- at least one eligible `.gf` source exists;
- source containment succeeds;
- portable language identity can be recorded.

Available operations:

```text
browse sources
select targets
view source metadata
compute fingerprints
```

### 20.2 `scan-ready`

Requirements:

- `source-ready`;
- scanner available;
- selected files satisfy scanner contracts.

GF is not required.

### 20.3 `compile-ready`

`compile-ready` is an effective run-configuration capability, not a language-context fact established by path probing alone.

Requirements:

- `source-ready`;
- GF executable resolved;
- effective GF path valid;
- explicit target set available;
- compilation preflight succeeds.

### 20.4 `scenario-ready`

`scenario-ready` is an effective run-configuration capability.

Requirements:

- required GF execution capability;
- explicit scenario registry or validation profile;
- scenario files and inputs exist;
- trust and path policies succeed.

### 20.5 `release-ready`

`release-ready` is an effective run-configuration capability.

Requirements:

- explicit validation profile;
- release entrypoints and expected artifacts declared;
- required scenarios and golds declared where applicable;
- release gates configured;
- release validation succeeds.

### 20.6 Capability isolation

Failure of one capability does not erase another valid capability.

```text
GF unavailable
→ source-ready and scan-ready may remain available
→ compile-ready is unavailable

no scenarios configured
→ targeted compilation may remain available
→ scenario-ready is unavailable

no release profile
→ ordinary validation remains available
→ release-ready is unavailable
```

---

## 21. Resolved run configuration

### 21.1 Purpose

The resolved run configuration is the single object consumed by orchestration for one run.

It combines:

```text
one immutable ResolvedLanguageContext
one optional validated profile snapshot
one resolved environment
one explicit mode and target selection
one timeout and evidence policy
one output policy
```

### 21.2 Characteristics

The resolved run configuration is:

- immutable after run start;
- fully validated for the requested capability;
- independent of GUI widget objects;
- independent of raw CLI parser objects;
- explicit about language identity and paths;
- explicit about mode and targets;
- explicit about selected stages;
- serializable into run evidence;
- safe to pass to workers.

### 21.3 Conceptual domains

```text
language
environment
profile
selection
validation
timeouts
evidence
output
compatibility
```

### 21.4 No late configuration reads

After resolution, validation stages must not independently reread:

- application state;
- CLI arguments;
- GUI widgets;
- environment variables;
- validation profiles;
- framework defaults;
- language catalogs;
- source-root guesses.

A stage receives values through the run configuration or a bounded request model derived from it.

---

## 22. Example path-resolved startup

```text
GUI selects:
  selected_path = C:/mycode/Grammatical_Framework/gf-rgl/src/english/LangEng.gf

language probe derives:
  selected_path_kind = file
  language_directory = C:/mycode/Grammatical_Framework/gf-rgl/src/english
  rgl_source_root = C:/mycode/Grammatical_Framework/gf-rgl/src
  rgl_root = C:/mycode/Grammatical_Framework/gf-rgl
  focused_target = LangEng.gf

selection service returns:
  deterministic eligible .gf inventory for src/english

module classification observes:
  LangEng.gf
  GrammarEng.gf
  AllEng.gf
  module_suffix = Eng

language probe publishes:
  one ResolvedLanguageContext
  source-ready = true
  scan-ready = true
  GF path requirements and structural diagnostics

main runtime:
  is composed only after context publication

run-configuration resolution:
  loads an optional explicit validation profile
  resolves gf_executable = C:/tools/gf/gf.exe
  resolves output_root = C:/work/gf-wordbench-runs
  produces one ordered effective GF path with provenance
  combines the context, environment, profile, mode and target
  computes compile-ready, scenario-ready and release-ready
```

No catalog or mandatory language bundle participates in this flow.

---

## 23. Conceptual application-state example

The persisted schema lock owns the exact canonical shape and version.

A conceptual state may resemble:

```json
{
  "schema_id": "gf-wordbench.app-state",
  "schema_version": "<current>",
  "environment": {
    "last_selected_language_path": "C:/mycode/Grammatical_Framework/gf-rgl/src/english",
    "last_selected_validation_profile": null,
    "gf_executable": "C:/tools/gf/gf.exe",
    "output_root": "C:/work/gf-wordbench-runs"
  },
  "selection": {
    "mode": "quick",
    "target_file": null,
    "timeout_sec": 60,
    "max_files": 0,
    "keep_ok_details": false,
    "diff_previous": true,
    "skip_version_probe": false,
    "no_compile": false,
    "emit_cpu_stats": false
  },
  "last_run": {
    "run_dir": null,
    "summary_path": null,
    "status_message": ""
  }
}
```

This file stores convenience values.

It does not define language truth or executable context.

---

## 24. Conceptual optional validation-profile example

The profile reference and persisted-schema lock own exact fields.

A simplified profile may resemble:

```toml
schema_id = "gf-wordbench.validation-profile"
schema_version = "<current>"

[profile]
id = "english-rgl-release"
name = "English RGL Release Validation"

[sources]
include_regex = "^[A-Z][A-Za-z0-9_]*\\.gf$"
exclude_regex = "(\\.bak\\.gf$|\\.tmp\\.gf$)"

[modules]
entrypoints = [
  "LangEng.gf",
  "GrammarEng.gf",
]
checkpoints = [
  "MorphoEng.gf",
  "NounEng.gf",
  "VerbEng.gf",
]

[validation]
required_scenarios = [
  "load-main",
  "linearize-basic",
]
optional_scenarios = [
  "generation-bounded",
]
release_requires_pgf = true
```

The profile does not define an unrelated absolute language source path.

It is applied only after a compatible language context has been resolved.

---

## 25. Path classes

Configuration paths belong to explicit classes.

### 25.1 Selected language path

Machine-local explicit startup input.

Examples:

```text
C:/work/gf-rgl/src/english
C:/work/gf-rgl/src/english/LangEng.gf
```

### 25.2 Language directory

Validated source directory for one active language.

It is derived from the selected path and stored in the resolved context.

### 25.3 RGL source root

Validated root containing the selected standard RGL language directory.

Typical form:

```text
C:/work/gf-rgl/src
```

### 25.4 RGL root

Parent repository root when resolved:

```text
C:/work/gf-rgl
```

### 25.5 Profile-relative path

Portable path stored relative to the validation profile’s approved root.

Examples:

```text
validation/scenarios/load-main.gfs
validation/golds/load-main.gold
```

### 25.6 Environment path

Machine-specific absolute path.

Examples:

```text
C:/tools/gf/gf.exe
C:/work/gf-wordbench-runs
```

### 25.7 Run-relative path

Stored relative to one run directory.

Examples:

```text
summary.json
raw/compile/LangEng.stdout.txt
artifacts/pgf/Lang.pgf
```

### 25.8 Source and output separation

Source directories must not be created automatically to hide configuration errors.

Run-owned output directories may be created automatically under approved output roots.

Source and output roots remain distinct.

---

## 26. GF path configuration

### 26.1 One owner

Effective GF search-path construction has one owner.

The compiler, scenario runner and PGF builder consume one equivalent resolved GF path.

### 26.2 Inputs

GF path resolution may combine:

```text
resolved language directory
explicit compatible profile requirements
framework-approved standard shared aliases
configured or derived RGL source root
operation-specific documented additions
controlled inherited fallback when policy permits
```

### 26.3 Ordering

Path order is semantically significant.

The resolved order is deterministic and recorded.

### 26.4 Duplicate removal

Equivalent normalized paths appear once.

Deduplication preserves first-occurrence order unless an explicit compatibility contract states otherwise.

### 26.5 Missing paths

A missing required path is a configuration error before dependent GF execution.

A missing optional path is visible evidence and may leave unrelated capabilities available.

### 26.6 No all-language path

Wordbench must not add every directory below the RGL source root.

Doing so would permit module shadowing and make validation depend on unrelated languages.

### 26.7 Inherited environment

Inherited `GF_LIB_PATH` may be used only as a documented, controlled fallback.

Its effective contribution must be visible in diagnostics and evidence.

### 26.8 Missing-module remediation

When canonical GF diagnostics identify one missing module, Wordbench may perform a bounded exact-name search under the approved RGL source root.

```text
zero matches
→ report absent module

one exact match
→ present or apply the containing path according to explicit policy

multiple exact matches
→ require user choice
```

Every added path is validated, bounded and recorded with provenance.

---

## 27. GF executable configuration

### 27.1 Resolution

The executable may be supplied as:

- an explicit absolute path;
- a documented resolvable executable name;
- an approved environment-discovery result.

### 27.2 Validation

Before required GF execution begins, the executable must:

- exist or resolve;
- represent a file where the platform can verify it;
- be launchable;
- remain unchanged for the run.

### 27.3 Version probe

The configured executable is used for:

```text
<gf-executable> --version
```

Version probing must not silently use another installation.

### 27.4 Paths with spaces

Paths with spaces must be supported.

Executable and arguments are passed as structured process fields, not one shell command string.

---

## 28. Source-selection configuration

### 28.1 Existing owner

The existing selection service owns:

```text
source-root validation
candidate enumeration
regular-file checks
readability checks
path containment
include and exclude rules
deduplication
deterministic ordering
explicit target resolution
selection diagnostics
```

### 28.2 Probe integration

The language probe constructs a minimal request for the selected language directory and invokes the public selection contract.

It must not duplicate recursive enumeration or sorting.

### 28.3 Profile extensions

An explicit validation profile may strengthen or narrow source-selection policy when compatible with the resolved language directory.

It cannot expand selection into an unrelated language directory.

### 28.4 Static scan boundary

Static scanning consumes selected files.

It does not establish GF semantic validity or replace GF module resolution.

---

## 29. Module-role and target configuration

### 29.1 Standard role classification

The language probe may recognize standard filename roles such as:

```text
Lang<Suffix>.gf
Grammar<Suffix>.gf
All<Suffix>.gf
Syntax<Suffix>.gf
Lexicon<Suffix>.gf
Paradigms<Suffix>.gf
Morpho<Suffix>.gf
Cat<Suffix>.gf
Noun<Suffix>.gf
Verb<Suffix>.gf
Structural<Suffix>.gf
```

These are candidate roles, not mandatory files.

### 29.2 Candidate entrypoint order

When one suffix is unambiguous, presentation may prefer:

```text
Lang<Suffix>.gf
Grammar<Suffix>.gf
All<Suffix>.gf
```

This is a user-facing candidate order, not a release contract.

### 29.3 Target kinds

Canonical target kinds may include:

```text
file
module
checkpoint
entrypoint
scenario
language
regression
```

### 29.4 Explicit target preservation

A selected `.gf` file remains the focused target.

Wordbench may present other candidates but must not replace the target silently.

### 29.5 Configured checkpoint rule

An arbitrary file path is not automatically a configured checkpoint.

Checkpoint identity requires an explicit profile or an explicit one-run target classification supported by the validation-mode contract.

---

## 30. Scenario, gold and release configuration

### 30.1 Optional base behavior

A resolved language can be source-ready, scan-ready or compile-ready without scenarios or gold files.

### 30.2 Scenario registry

An explicit validation profile owns the scenario registry.

A scenario registration may resolve:

```text
scenario ID
script path
required or optional state
applicable modes
checkpoint association
entrypoint
input assets
gold path
timeout class
assertion profile
```

The `.gfs` file does not independently own this metadata.

### 30.3 Gold policy

Normal validation never creates or rewrites missing gold files.

Gold updates remain explicit, reviewed operations.

### 30.4 Release readiness

Release readiness requires explicit profile policy.

Wordbench must not infer release entrypoints, required scenarios, golds or expected PGF artifacts from filename patterns alone.

---

## 31. Validation-mode configuration

Canonical modes remain owned by the validation-mode contract.

Typical modes include:

```text
quick
checkpoint
release
diagnostic
```

Configuration selects a mode and supplies compatible language/profile content.

Examples:

```text
resolved context provides available source targets
profile defines configured checkpoints
framework defines what checkpoint mode means
profile defines required release scenarios
framework defines that release cannot skip them
```

A language may be open even when a selected mode is unavailable.

The UI and CLI must report capability or configuration insufficiency instead of treating language resolution as failed.

---

## 32. Timeout configuration

### 32.1 Operation classes

Timeouts should be configured by operation class:

```text
language probe optional GF verification
version probe
file compilation
checkpoint compilation
entrypoint compilation
PGF build
scenario
generation
diagnostic introspection
```

### 32.2 Finite values

Every external execution has a finite timeout.

No normal configuration value means infinite execution.

### 32.3 Probe bounds

Filesystem discovery and missing-module remediation are also bounded by explicit limits, such as:

```text
maximum ancestor depth
maximum inventory size where policy applies
maximum exact-name remediation additions
no duplicate path addition
stop when no progress occurs
```

### 32.4 Recording

The effective timeout or bound for each operation is recoverable from diagnostics or run evidence where relevant.

---

## 33. Output configuration

Output configuration may control:

```text
output root
run-directory policy
evidence detail
successful-result detail retention
raw output-size limits
aggregate log generation
AI-ready report generation
manifest generation
retention behavior
```

Artifact names and run-directory layouts are owned by artifact and persisted-schema contracts.

A UI must not rename canonical reports independently.

Language-scoped output policy must prevent cross-language run mixing.

---

## 34. Logging and evidence configuration

Configuration may select an evidence level such as:

```text
bounded
standard
complete
expanded
```

Evidence level may affect:

- successful-detail retention;
- diagnostic excerpts;
- optional timing;
- optional intermediate files;
- report verbosity.

It must not affect validation truth.

Raw evidence required by a mode or contract must not be disabled by presentation preferences.

---

## 35. Previous-run configuration

Previous-run comparison may use:

```text
automatic compatible previous run
explicit previous run
no comparison where the mode permits
```

Compatibility must consider at least:

```text
portable language identity
resolved source context
relevant profile identity and digest
schema compatibility
mode and target compatibility
```

The resolver must not select a previous run solely by newest directory name.

A previous run is never a startup language authority.

---

## 36. Configuration validation phases

Configuration validation occurs in phases.

### 36.1 Syntax validation

Validate:

- TOML and JSON parsing;
- schema identity and version;
- primitive field types;
- enum values;
- regular expressions;
- numeric ranges.

### 36.2 Selected-path validation

Validate:

- path existence;
- path readability;
- accepted file or directory kind;
- `.gf` extension for selected files;
- path normalization;
- symlink policy;
- candidate language-directory derivation.

### 36.3 Structural language validation

Validate:

- eligible source presence;
- bounded RGL source-root detection;
- containment;
- portable identity construction;
- candidate suffix and entrypoint ambiguity;
- capability prerequisites.

### 36.4 Profile validation

When a profile is present, validate:

- schema identity and version;
- required sections and fields;
- unique IDs;
- ordered arrays;
- authorized overrides;
- compatibility with resolved language context.

### 36.5 Path validation

Validate:

- language directory;
- RGL source root;
- GF executable;
- effective GF path;
- output root;
- scenario and gold paths when configured;
- containment;
- writable output.

### 36.6 Referential validation

When applicable, validate:

- profile entrypoint files exist;
- checkpoint IDs resolve;
- scenario IDs resolve;
- input files exist;
- required gold files exist;
- release targets resolve;
- duplicate scenario registration is absent.

### 36.7 Capability validation

Validate:

- static scanner availability;
- GF launchability;
- supported or permitted GF version;
- required command capabilities;
- platform restrictions;
- optional tools when selected.

### 36.8 Mode validation

Validate:

- required target;
- selected checkpoint;
- release scope;
- forbidden weakening flags;
- applicable scenarios;
- required PGF policy.

---

## 37. Configuration and probe error model

Configuration errors and resolution ambiguities are structured.

Recommended fields:

```text
error_kind
stage
configuration_source
field_path or subject
provided_value
message
technical_detail
remediation
relevant_path
candidate_choices
```

Representative errors include:

```text
selected path does not exist
selected path is unreadable
selected file is not .gf
selected directory contains no eligible GF sources
RGL source root cannot be determined
path escapes approved root
module suffix is ambiguous
no standard entrypoint candidate exists
GF executable unavailable
required GF path entry missing
missing module has no exact match
missing module has several exact matches
validation profile conflicts with selected language
```

Secrets and sensitive paths are redacted according to evidence policy.

---

## 38. Error severity and capability effect

Configuration findings may be:

```text
error
warning
info
```

### 38.1 Error

Prevents the requested resolution or capability from being evaluated correctly.

Examples:

- selected path missing;
- no eligible source file;
- invalid profile schema major;
- ambiguous required target in noninteractive mode;
- missing GF executable for a requested compile;
- missing required release scenario.

An error for one capability does not automatically invalidate unrelated capabilities.

### 38.2 Warning

Execution or source use may proceed under documented policy.

Examples:

- GF version newer than tested range;
- optional scenario missing;
- state file unreadable;
- deprecated compatibility input;
- release profile absent while only quick scanning is requested.

### 38.3 Info

Useful resolution evidence.

Examples:

- executable discovered from `PATH`;
- remembered path ignored because explicit selection won;
- module suffix identified from unique standard-role candidates;
- optional environment variable absent;
- optional profile not loaded.

Release policy may promote specified warnings to errors.

---

## 39. No silent fallback

A fallback is acceptable only when:

- the fallback order is documented;
- the selected source is recorded;
- semantics are preserved;
- the fallback is allowed for the requested capability;
- ambiguity is absent.

Prohibited silent fallbacks include:

```text
invalid selected path → search entire disk
ambiguous language suffix → choose first candidate
selected AdjectiveEng.gf → replace with LangEng.gf
missing GF module → add every RGL language directory
missing GF executable → use another installation without notice
invalid release scenario → skip it
missing gold → use current output
invalid output root → write into source tree
unknown mode → use quick
profile conflict → let profile override resolved language silently
```

---

## 40. Configuration provenance

Every diagnostically important resolved value retains provenance.

Possible provenance values include:

```text
package_metadata
framework_default
explicit_selected_path
remembered_selected_path
language_probe
selection_service
path_discovery
validation_profile
application_state
environment_variable
cli
gui
automation
runtime_derived
legacy_migration
```

Example:

```text
language_directory:
  value = C:/work/gf-rgl/src/english
  source = language_probe

gf_executable:
  value = C:/tools/gf/gf.exe
  source = cli
```

The persisted schema may store provenance selectively rather than for every field.

---

## 41. Run configuration snapshot

Each run records enough effective configuration to reproduce or explain it.

Recommended metadata includes:

```text
portable language key
selected path kind
selected path as permitted local evidence
language directory relative to RGL source root
RGL source-root evidence
module suffix when available
focused target or target-set identity
validation-profile identity and digest when used
GF executable
GF version
effective GF path and provenance
output root
mode
target
selected files
selected checkpoints
selected entrypoints
selected scenarios
timeout values
important overrides
evidence level
capability status used by the run
resolution diagnostics
compatibility warnings
```

Sensitive or irrelevant environment values must not be recorded.

---

## 42. CLI/GUI parity tests

Equivalent interface inputs must produce equal normalized probe and run configuration.

Required parity cases include:

```text
same selected language directory
same selected .gf file
same optional profile
same GF executable
same explicit RGL root
same output root
same mode
same target
same timeout
same detail options
same previous-run option
same ambiguity choice
```

Presentation-only GUI values are excluded from semantic comparison.

---

## 43. Application-state migration

### 43.1 Catalog-era state

State fields such as:

```text
last_language_id
catalog_path
last_catalog_entry
```

are no longer runtime authorities.

### 43.2 Path-resolved state

Migration may introduce:

```text
last_selected_language_path
last_selected_validation_profile
last_rgl_root
```

Exact fields and schema version belong to the application-state reference and persisted-schema lock.

### 43.3 Migration rules

- preserve unrelated local preferences;
- preserve local GF and output paths when valid;
- discard stale catalog authority;
- do not search the filesystem from a catalog ID alone;
- ask the user for a selected language path when no path can be migrated safely;
- discard `is_running`;
- preserve the source until canonical output is written successfully;
- canonical writers emit only the current schema.

---

## 44. Validation-profile migration

A profile migration may be required when:

- converting mandatory `project.toml` startup configuration into an optional profile;
- changing profile schema major version;
- changing profile ID;
- moving scenario or gold roots;
- changing entrypoint identity;
- changing GF path requirements;
- changing scenario identifiers;
- separating source-context facts from validation policy.

A migration must:

1. read the original without modifying it;
2. identify which values belong to the resolved language context;
3. preserve only profile-owned policy in the profile;
4. report warnings and losses;
5. validate compatibility with an explicit selected language path;
6. produce canonical configuration;
7. write atomically;
8. preserve the source until success;
9. update project documentation and contracts.

Opening a language or profile must not silently rewrite configuration.

---

## 45. Catalog and bundle migration

### 45.1 Runtime catalog

`rgl-language-catalog.json` is no longer a required runtime configuration source.

It may be:

- removed;
- retained as a non-authoritative inventory;
- used in diagnostics or migration tooling;
- used as test fixture data.

### 45.2 Existing language bundles

Existing language bundles may remain as optional validation profiles and assets.

They are not loaded merely because a suffix or language directory is detected.

### 45.3 Compatibility adapter

A temporary compatibility adapter may translate a former catalog selection into an explicit selected path.

It must:

- be version-bounded;
- emit deprecation evidence;
- resolve to the path-based model before runtime creation;
- not retain catalog authority inside the resolved context;
- have documented removal criteria.

---

## 46. Configuration files and version control

### 46.1 Normally commit

```text
framework defaults
optional validation profiles
profile templates
project validation metadata
scenario registrations
gold files
schema definitions
migration code
```

### 46.2 Usually do not commit

```text
.gf_wordbench_state.json
local run directories
machine-specific environment files
temporary discovery caches
local GUI geometry
absolute selected-language paths
```

### 46.3 Catalog outputs

Generated inventory catalogs are committed only when a separate documented purpose requires them.

They are not required for normal startup correctness.

---

## 47. Security requirements

Configuration handling must:

- validate path containment;
- resolve symlinks according to policy;
- avoid shell command strings;
- reject unauthorized traversal;
- avoid arbitrary filesystem searches;
- restrict exact-name remediation to approved roots;
- avoid reading arbitrary files through profile values;
- redact secrets;
- restrict environment propagation;
- use atomic writes;
- treat scenarios as executable project inputs;
- distinguish user input, local state and trusted profile policy;
- bound discovery, process time and output size.

A valid schema does not automatically make a configuration safe.

Semantic security validation remains required.

---

## 48. Platform behavior

### 48.1 Windows

Must support:

- drive-letter paths;
- paths with spaces;
- `gf.exe`;
- mixed input slash forms;
- native process behavior;
- GUI startup without a visible console;
- controlled child-process termination.

### 48.2 Canonical serialization

Portable profile paths use `/`.

Local Windows paths may be accepted with `\` and normalized internally.

### 48.3 Platform-neutral orchestration

Windows-specific behavior remains in environment, launcher, filesystem or process adapters.

Language-probe and validation policy remain platform-neutral where possible.

---

## 49. Configuration anti-patterns

### 49.1 Duplicate source scanner

Bad:

```text
LanguageProbeService uses its own recursive scanner
SelectionService performs a second inventory
```

Correct:

```text
LanguageProbeService delegates enumeration to SelectionService
```

### 49.2 Duplicate GF path construction

Bad:

```text
probe builds one -path
compiler builds another
scenario runner reads GF_LIB_PATH directly
```

Correct:

```text
one central resolver produces one effective GF path
all GF operations consume it
```

### 49.3 Mandatory profile startup

Bad:

```text
no project.toml → application refuses to browse src/english
```

Correct:

```text
selected path → source-ready context
optional profile → advanced validation policy
```

### 49.4 Catalog-derived runtime authority

Bad:

```text
catalog says Eng exists → runtime trusts paths without validating checkout
```

Correct:

```text
explicit selected path → bounded probe → validated resolved context
```

### 49.5 Project policy in application state

Bad:

```json
{
  "required_scenarios": ["load-main"]
}
```

Correct:

```text
required scenarios belong to an explicit validation profile
```

### 49.6 Local paths in portable profile

Bad:

```toml
gf_executable = "C:/Users/name/tools/gf.exe"
language_directory = "C:/Users/name/gf-rgl/src/english"
```

Correct:

```text
local paths resolved from explicit input, state or environment
portable policy remains relative
```

### 49.7 Stage-specific environment reads

Bad:

```text
compiler reads GF_LIB_PATH
scenario runner uses profile path parts
PGF builder performs PATH discovery again
```

Correct:

```text
bootstrap resolves one environment and GF path
all stages consume the resolved values
```

### 49.8 Report-derived startup

Bad:

```text
next run parses summary.md to select a language
```

Correct:

```text
explicit or remembered selected path is revalidated
```

### 49.9 Hidden entrypoint substitution

Bad:

```text
user selects AdjectiveEng.gf
probe silently compiles LangEng.gf instead
```

Correct:

```text
AdjectiveEng.gf remains focused target
other entrypoint candidates are presented separately
```

---

## 50. Automated checks

Recommended conceptual commands include:

```text
gf-wordbench language probe <path>
gf-wordbench config check
gf-wordbench config check --strict
```

Exact command names belong to the CLI registry and reference documentation.

A configuration check should validate:

1. package metadata is readable;
2. framework defaults are internally valid;
3. selected path exists and is readable;
4. candidate language directory is valid;
5. bounded source-root resolution succeeds;
6. source selection is deterministic;
7. portable language identity is constructible;
8. candidate suffix and entrypoint ambiguity is reported;
9. optional profile schema and compatibility;
10. environment path resolution;
11. GF executable validation when required;
12. GF version policy when required;
13. effective GF path;
14. output-root writability;
15. mode and target combination;
16. required profile scenario and gold references;
17. prohibited release overrides;
18. state-schema compatibility;
19. legacy migration availability;
20. effective capability statuses.

Strict mode may additionally detect:

- unused profile fields;
- deprecated keys;
- duplicate normalized paths;
- state values duplicating profile policy;
- absolute machine paths in portable profiles;
- undocumented environment-variable use;
- framework defaults containing language identifiers;
- configuration reads outside approved owners;
- runtime catalog dependencies;
- duplicate source scanners or GF path builders.

---

## 51. Required tests

Recommended test structure:

```text
tests/configuration/
├── test_framework_defaults.py
├── test_language_probe.py
├── test_language_identity.py
├── test_validation_profile.py
├── test_application_state.py
├── test_environment_resolution.py
├── test_configuration_precedence.py
├── test_gf_path_resolution.py
├── test_run_config.py
├── test_configuration_errors.py
├── test_cli_gui_parity.py
└── test_configuration_migrations.py
```

### 51.1 Framework-default tests

- all defaults are language-neutral;
- all timeouts and discovery limits are finite;
- duplicate constants are absent;
- package version has one owner.

### 51.2 Language-probe tests

- directory selection;
- `.gf` file selection;
- non-`.gf` file rejection;
- missing path;
- unreadable path;
- candidate directory derivation;
- nearest valid RGL source root;
- unsupported layout;
- portable language key;
- unique suffix detection;
- ambiguous suffix detection;
- entrypoint candidate ordering;
- focused target preservation;
- no filesystem-wide search.

### 51.3 Profile tests

- no profile is valid for source-only workflows;
- valid explicit profile;
- invalid schema major;
- incompatible language identity;
- source escape rejected;
- duplicate scenario;
- missing configured entrypoint;
- absolute machine path rejected where prohibited;
- deterministic ordering preserved.

### 51.4 State tests

- missing state;
- valid state;
- malformed JSON;
- unknown optional field;
- invalid major version;
- atomic write;
- remembered path revalidated;
- stale remembered path fails safely;
- no language truth restored from state;
- `is_running` discarded.

### 51.5 Precedence tests

- explicit selected path wins over remembered path;
- GUI and CLI resolve equivalently;
- explicit GF executable wins;
- derived source root is validated;
- compatible explicit RGL root is accepted;
- incompatible explicit root is rejected;
- profile policy cannot replace language identity;
- release gates cannot be weakened;
- environment fallback is visible.

### 51.6 Path tests

- Windows drive path;
- path containing spaces;
- selected directory;
- selected `.gf` file;
- mixed slash input;
- parent traversal rejection;
- symlink escape rejection;
- missing source root;
- writable output creation;
- source root is not auto-created;
- all-language GF path is prohibited.

### 51.7 Migration tests

- catalog ID without path requires user selection;
- former catalog path migrates when safely available;
- mandatory project config becomes explicit profile;
- unrelated state preferences preserved;
- source preserved until successful migration;
- canonical writer emits only current schema.

### 51.8 Architecture tests

- probe uses public selection contract;
- probe does not invoke subprocess;
- probe does not write reports;
- GUI does not enumerate GF sources directly;
- one GF path resolver exists;
- one GF execution boundary exists;
- runtime catalog reader is absent from normal startup;
- private helpers are not imported across functional boundaries.

---

## 52. Configuration change policy

A configuration change is complete only when:

```text
[ ] Authoritative owner identified
[ ] ADR alignment confirmed
[ ] Field purpose documented
[ ] Type and default defined
[ ] Required or optional status defined
[ ] Capability impact defined
[ ] Override policy defined
[ ] Precedence defined
[ ] Ambiguity behavior defined
[ ] Security impact reviewed
[ ] Discovery bounds reviewed
[ ] Path semantics reviewed
[ ] Persistence impact reviewed
[ ] Schema-version impact classified
[ ] Migration provided where needed
[ ] CLI impact reviewed
[ ] GUI impact reviewed
[ ] Reporting impact reviewed
[ ] Tests updated
[ ] Reference documentation updated
[ ] Contract locks updated
```

Changing a field’s owner is normally a breaking architectural change.

---

## 53. Configuration drift indicators

Probable drift exists when:

- the same value exists in framework defaults and an explicit profile;
- CLI and GUI resolve different contexts from equivalent selected paths;
- the GUI enumerates language files independently;
- the probe implements a second recursive scanner;
- a compiler reads environment variables directly;
- a scenario runner builds a different GF path;
- state contains required project scenarios;
- a report determines startup language;
- language identity is inferred from an output directory;
- a local absolute path appears in portable profile policy;
- a release flag can skip a mandatory gate;
- an unknown profile field is silently interpreted;
- a legacy catalog ID is emitted by a canonical writer as runtime authority;
- environment fallback is used but not reported;
- a missing source directory is created automatically;
- a profile is rewritten during normal validation;
- configuration changes after a run starts;
- a stage rereads GUI state;
- one interface supports an undocumented override;
- schema changes without version or migration updates;
- every RGL language directory is added to GF path;
- a selected file is silently replaced by a guessed entrypoint;
- missing scenarios block basic source browsing.

Every drift indicator requires correction or an explicit architecture decision.

---

## 54. Documentation ownership map

| Configuration topic | Document |
|---|---|
| Overall configuration architecture | `docs/configuration/CONFIGURATION_OVERVIEW.md` |
| Path-resolved startup decision | `docs/decisions/ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md` |
| Exact optional profile fields | `docs/configuration/PROJECT_TOML_REFERENCE.md` or successor profile reference |
| Exact state fields | `docs/configuration/APPLICATION_STATE_REFERENCE.md` |
| Environment variables and local paths | `docs/configuration/ENVIRONMENT_AND_PATHS.md` |
| Effective GF path | `docs/gf/GF_PATH_RESOLUTION.md` |
| Persisted schemas and migrations | `docs/PERSISTED_SCHEMA_LOCK.md` |
| Validation-mode behavior | `docs/validation/VALIDATION_MODES.md` |
| Source-selection contract | `docs/validation/FILE_SELECTION.md` |
| CLI options | `docs/usage/CLI_REFERENCE.md` |
| GUI controls | `docs/usage/GUI_REFERENCE.md` |
| Python provider-consumer contracts | `docs/INTERFILE_CONTRACT_LOCK.md` |
| External GF and process contracts | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |

Rules must not be duplicated inconsistently.

Detailed references may repeat concise context, but one document remains authoritative for each exact contract.

---

## 55. Configuration contract

GF Wordbench configuration is divided into distinct responsibilities:

```text
package metadata
    owns application identity and version

framework defaults
    own safe language-neutral operational defaults

explicit selected language path
    owns current startup intent

language probe
    coordinates candidate resolution through existing public services

ResolvedLanguageContext
    owns effective active-language and source facts

optional validation profile
    owns explicit advanced validation and release policy

application state
    owns disposable local preferences and remembered paths

environment resolution
    owns machine-specific tool and output paths

CLI and GUI
    own explicit startup and run selections

bootstrap
    owns composition, compatibility validation and immutable snapshots

resolved run configuration
    owns effective values for one run

run summary
    records the effective configuration and evidence used
```

The configuration invariants are:

```text
one explicit selected language path
one resolved language context per active runtime
one portable language identity per ordinary run
one authoritative owner per value
one effective GF path per run
one resolved run configuration per run
no hidden late reads
no duplicate source scanner
no duplicate GF path builder
no project policy in application state
no machine paths in portable validation policy
no mandatory catalog for startup
no mandatory profile for source browsing
no silent ambiguity resolution
no silent release weakening
no differing CLI and GUI semantics
no unrecorded environment fallback
no unversioned persisted configuration
```

Configuration is correct only when:

- the user’s explicit selected path remains visible;
- the source context is resolved through bounded, reusable services;
- optional policy remains portable and explicit;
- local execution paths remain machine-specific and observable;
- every stage receives the same immutable interpretation of the language and run;
- capability claims match the configuration and evidence actually available.
