# GF Wordbench — Extending GF Wordbench

**Document ID:** `GF-WB-DEV-EXTENDING`  
**Status:** Normative development guide  
**Applies to:** Framework extensions, validation stages, reports, schemas, commands, GUI features, external tools, project templates, and active-project capabilities  
**Primary owners:** GF Wordbench maintainers  
**Target architecture:** Final GF Wordbench architecture  
**Last structural review:** 2026-07-22

---

## 1. Purpose

This document defines how to extend GF Wordbench without creating duplicate ownership, hidden contracts, incompatible persisted data, or unnecessary architectural layers.

It covers additions to:

- Python framework components;
- audit and validation stages;
- shared result models;
- diagnostics and classification;
- reports and artifacts;
- CLI commands;
- GUI workflows;
- project configuration;
- project templates;
- `.gfs` scenarios;
- gold comparison;
- external-tool integrations;
- persisted schemas;
- compatibility and migration support.

The objective is not to make every behavior pluggable.

The objective is to provide enough extension structure to keep the system maintainable while preserving a small, explicit architecture.

---

## 2. Core extension rule

> Extend the existing owner when the new behavior belongs to its responsibility. Create a new component only when a real independent boundary exists.

A new file, class, or command does not automatically justify a new architectural component.

A new component is justified when at least one of the following is true:

1. it owns a distinct public contract;
2. it owns a distinct persisted artifact;
3. it has multiple independent consumers;
4. it has a distinct lifecycle;
5. it requires its own compatibility policy;
6. it forms a security or trust boundary;
7. it requires isolated integration tests;
8. keeping it inside the current owner would create conflicting responsibilities.

Otherwise, keep the behavior as an internal helper of the existing owner.

---

## 3. Related normative documents

Extensions must remain consistent with:

```text
CONTRIBUTING.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/DEPENDENCY_RULES.md
docs/architecture/ERROR_HANDLING_MODEL.md
docs/development/CODING_STANDARDS.md
docs/development/TESTING_GF_WORDBENCH.md
docs/development/BACKWARD_COMPATIBILITY.md
docs/release/VERSIONING_POLICY.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

Authority boundaries:

| Extension subject | Authoritative document |
|---|---|
| Python provider/consumer boundary | framework interfile lock |
| External executable or runtime | external-tool lock |
| Persisted field, schema, path, or artifact name | persisted-schema lock |
| Component ownership | component map |
| Error semantics | error-handling model |
| Project GF module relationship | project interfile lock |
| Version and deprecation | versioning and compatibility policy |

No extension may bypass the relevant lock because it appears small.

---

## 4. Extension philosophy

GF Wordbench favors:

```text
explicit ownership
typed boundaries
deterministic behavior
small public APIs
shared orchestration
versioned persistence
testable external requests
language-neutral framework code
project-owned language behavior
```

GF Wordbench avoids:

```text
dynamic discovery without need
implicit global registries
reflection-driven public APIs
one class per small behavior
one component per validation rule
GUI-specific execution engines
CLI-specific execution engines
report-time validation
unversioned extension data
language-specific framework plugins
```

A simple explicit import is preferable to a plugin loader when the set of components is maintained in the same repository.

---

# 5. Extension categories

Every extension must be classified before implementation.

Canonical categories:

```text
internal helper
compatible behavior
validation rule
validation stage
result-model extension
diagnostic extension
report extension
artifact extension
CLI extension
GUI extension
project-configuration extension
project-template extension
scenario extension
external-tool extension
persisted-schema extension
architectural component
```

The classification determines which contracts and tests apply.

---

## 5.1 Internal helper

Use when:

- only one component consumes the logic;
- no persisted format changes;
- no public symbol is required;
- no independent lifecycle exists;
- no separate configuration is required.

Examples:

```text
private marker parser inside scenario_runner.py
private compile-artifact verification helper
private Markdown table renderer
private scanner rule implementation
```

Requirements:

- keep the symbol private;
- test through the owner or focused unit tests;
- do not add it to a public registry;
- do not document it as a component.

---

## 5.2 Compatible behavior extension

Use when existing public contracts remain true.

Examples:

```text
better internal algorithm
faster deterministic sorting
clearer non-contractual log wording
additional internal validation
optional in-memory metadata not serialized
```

Requirements:

- preserve public signatures;
- preserve statuses and artifacts;
- add regression tests;
- update documentation only when observable behavior changes.

---

## 5.3 Validation-rule extension

Use when adding a rule to an existing validation stage.

Examples:

```text
new static source pattern
new scenario marker check
new artifact freshness check
new configuration invariant
```

The rule belongs to the stage that owns its evidence.

A validation rule does not justify a new stage unless it requires a distinct request, lifecycle, result, or gating policy.

---

## 5.4 Validation-stage extension

Use when the operation:

- executes independently;
- has distinct inputs and evidence;
- may be required or optional by mode;
- has its own timeout or failure semantics;
- produces a structured result;
- participates independently in aggregation.

Examples:

```text
new GF introspection stage
new PGF runtime smoke stage
new language-independent package verification stage
```

Adding a validation stage is an architectural change.

---

## 5.5 Result-model extension

Use when structured data must cross a component boundary.

Examples:

```text
new optional artifact reference
new optional timing detail
new stage result
new warning record
```

Determine whether the data is:

```text
in-memory only
public Python API
persisted
```

Each level has different compatibility requirements.

---

## 5.6 Report extension

Use when adding a new derived representation of completed results.

A report extension may:

- render existing fields;
- summarize evidence;
- link artifacts;
- apply bounded presentation formatting.

It must not:

- rerun validation;
- infer missing facts as success;
- become a second source of truth;
- rewrite stage evidence.

---

## 5.7 External-tool extension

Use when GF Wordbench invokes a new executable, service, runtime, or operating-system capability.

A new tool must provide a capability not adequately supplied by:

- GF;
- Python standard library;
- existing GF Wordbench components.

Every tool needs an external contract before it becomes required.

---

## 5.8 Persisted-schema extension

Use when a new field, enum, file, marker, report identity, directory, or path survives beyond one in-memory operation.

Persisted changes require:

```text
schema identity
version decision
writer
readers
migration
defaults
ordering
tests
lock update
```

---

# 6. Extension decision tree

Use this sequence.

```text
Does the behavior belong to an existing component?
    yes
        Is it consumed only inside that component?
            yes → private helper
            no  → public compatible extension or shared model
    no
        Does it own a distinct request/result/artifact/lifecycle?
            no  → reconsider the proposed boundary
            yes → new component candidate

Does it call an external process?
    yes → external-tool contract required

Does it persist data?
    yes → persisted-schema review required

Does it change project GF behavior?
    yes → project contract review required

Does it affect CLI and GUI?
    yes → shared application service required

Does it affect release readiness?
    yes → release-gate and migration review required
```

When uncertain, prefer the smaller boundary until evidence shows that separation is needed.

---

# 7. Standard extension workflow

Every non-trivial extension follows:

```text
1. define user or maintenance need
2. classify extension category
3. identify current owner
4. identify providers and consumers
5. define request and response
6. define failure behavior
7. define artifacts and persistence
8. decide compatibility
9. update locks before or with implementation
10. implement the smallest viable boundary
11. add unit tests
12. add contract tests
13. add integration tests where required
14. update CLI and GUI through shared services
15. update documentation
16. run applicable validation modes
17. review drift indicators
```

An implementation is incomplete when documentation and consumers still describe the old boundary.

---

# 8. Extension proposal template

For significant extensions, document:

```text
Name:
Category:
Problem:
Why existing behavior is insufficient:
Current owner:
Proposed owner:
Callers:
Consumers:
Inputs:
Outputs:
Side effects:
Artifacts:
Persistence:
Errors:
Security:
Compatibility:
Migration:
CLI impact:
GUI impact:
Project impact:
Template impact:
Tests:
Documentation:
Release impact:
Alternatives rejected:
```

Use an ADR when ownership, dependency direction, execution strategy, or schema strategy changes materially.

---

# 9. Adding an internal helper

A helper remains internal when it has one owner.

Recommended pattern:

```python
def _normalize_target_key(path: Path) -> str:
    ...
```

Rules:

- prefix private helpers with `_`;
- keep types explicit;
- avoid hidden filesystem or process side effects;
- avoid importing a higher architectural layer;
- return deterministic values;
- test edge cases;
- do not expose the helper merely for test convenience.

If multiple components need the same behavior, determine whether:

1. one component should remain the provider; or
2. a true shared infrastructure primitive exists.

Do not create a generic utility module as a dumping ground.

---

# 10. Adding shared infrastructure

Shared infrastructure belongs under a focused owner such as:

```text
app/utils/process_utils.py
app/utils/io_utils.py
app/utils/path_utils.py
app/utils/logging_utils.py
```

A shared primitive must be:

- domain-neutral;
- deterministic where applicable;
- free of GUI dependencies;
- free of active-language assumptions;
- free of report semantics;
- independently tested.

Examples:

```text
atomic UTF-8 write
safe relative path
bounded process execution
root containment check
```

Not shared infrastructure:

```text
GF type-error classification
scenario gold comparison
active-project entrypoint resolution
Markdown report section selection
```

Those belong to domain components.

---

# 11. Adding a static scan rule

Static scan rules belong to:

```text
app/audit/scanner.py
```

or a scanner-owned private rule module.

A scan rule proposal must define:

```text
rule ID
purpose
source pattern
comment/string masking policy
false-positive policy
count or finding representation
severity/gating policy
examples
tests
```

Rules:

- static scanning does not replace GF compilation;
- a finding must not be described as a GF error unless GF confirms it;
- rule ordering must be deterministic;
- counts must remain non-negative;
- persisted counters require schema review;
- project-specific rules belong in project policy, not hardcoded generic code.

A new rule does not require a new scanner component.

---

# 12. Adding a validation stage

A new stage needs a stable owner.

Recommended stage interface:

```python
@dataclass(frozen=True, slots=True)
class StageRequest:
    ...

@dataclass(frozen=True, slots=True)
class StageResult:
    status: ValidationStatus
    duration_ms: int
    error_kind: ErrorKind
    primary_message: str
    evidence_paths: tuple[str, ...]
```

Recommended stage service:

```python
def run_stage(request: StageRequest) -> StageResult:
    ...
```

Exact models should be domain-specific and locked before public use.

## 12.1 Required stage definition

Document:

```text
stage ID
owner
purpose
mode participation
prerequisites
request model
result model
timeout
artifacts
status criteria
continuation policy
overall-status impact
reporting
tests
```

## 12.2 Stage placement

A stage should normally live under:

```text
app/audit/
```

unless it is purely infrastructure or project lifecycle.

## 12.3 Orchestrator integration

Only `audit_core.py` owns stage planning.

The stage must not:

- add itself dynamically to the pipeline;
- call reports;
- call GUI code;
- decide the full run order;
- mutate unrelated stage results.

The orchestrator must:

- construct the request;
- apply mode policy;
- capture the result;
- apply continuation;
- aggregate the outcome.

## 12.4 Stage gating

Declare whether the stage is:

```text
required
optional
diagnostic-only
release-only
```

Optional results remain visible.

---

# 13. Adding a GF-backed stage

A GF-backed stage must reuse:

```text
resolved RunConfig
shared GF path resolution
process_utils
diagnostics
run-owned evidence directories
```

It must not create:

```text
a second process runner
a second GF executable resolver
a second GF path builder
a second diagnostic parser
```

Required evidence:

```text
resolved executable
GF version
ordered command
working directory
environment overrides
timeout
stdout
stderr
exit code
duration
produced artifacts
```

Success must evaluate more than exit code.

A new GF command requires external-tool contract review.

---

# 14. Adding a scenario capability

Scenario capabilities belong to:

```text
app/audit/scenario_runner.py
project/validation/scenarios/
```

Examples:

```text
new supported marker type
new assertion type
new bounded introspection operation
new scenario-produced artifact
```

Requirements:

- preserve raw output;
- keep required/optional distinction;
- use stable markers;
- version normalization when output changes;
- preserve semantic GF output;
- keep ordinary validation read-only for gold;
- add fixture and real-GF tests where appropriate.

Project-specific scenario content belongs under `project/`.

Generic scenario parsing and execution belongs in the framework.

---

# 15. Adding an assertion type

An assertion type is justified when exact gold is inappropriate.

Examples:

```text
section completed
output non-empty
output empty
contains exact line
does not contain line
count equals value
count within range
artifact exists
parse count threshold
```

Assertion definitions must include:

```text
assertion ID
input fields
evaluation rule
failure message
normalization dependency
ordering semantics
serialization
tests
```

Do not allow arbitrary Python expressions in project configuration.

Use a bounded declarative assertion vocabulary.

If assertions are persisted, update the schema lock.

---

# 16. Adding a report

New report writers belong under:

```text
app/reports/
```

Recommended API:

```python
def write_<report_name>(run_result: RunResult) -> Path:
    ...
```

A report proposal must define:

```text
report purpose
audience
canonical filename
required or optional status
source fields
minimum sections
artifact role
size policy
security policy
tests
```

Rules:

- consume completed structured results;
- do not invoke GF;
- do not rerun scanner or scenarios;
- do not modify gold;
- use owned paths;
- write atomically when required;
- preserve deterministic ordering;
- register retained files in the manifest.

A report that introduces a stable filename or machine-consumed format requires persisted-schema review.

---

# 17. Adding an artifact

An artifact extension must define:

```text
artifact role
owner
producer
consumers
path
required flag
media type
lifecycle
hash policy
cleanup policy
manifest behavior
```

Rules:

- one writer owns the artifact;
- observers do not rewrite it;
- run artifacts remain inside the run root;
- project source artifacts remain inside the project root;
- required artifacts affect finalization;
- final bytes are hashed before manifest publication;
- directories are not manifest file entries.

Do not create a new artifact when an existing structured result is sufficient.

---

# 18. Adding a result field

Before adding a field, decide:

```text
Is it needed outside the owner?
Is it derivable?
Is it stable?
Is it optional?
Is it persisted?
Who reads it?
What does absence mean?
```

## 18.1 In-memory optional field

Usually compatible when:

- default is explicit;
- existing consumers remain valid;
- serialization does not change.

## 18.2 Public Python field

Requires:

- model update;
- provider update;
- consumer review;
- contract tests;
- compatibility review.

## 18.3 Persisted field

Requires:

- schema version decision;
- canonical type;
- null/absence semantics;
- writer;
- every reader;
- migration;
- fixtures;
- schema tests;
- schema-lock update.

Do not expose internal implementation state through persisted fields merely for convenience.

---

# 19. Adding or changing an enum

Enums include:

```text
validation status
error kind
diagnostic class
mode
artifact role
change kind
scenario assertion type
```

Enum changes are high risk because many consumers perform branching.

Required review:

```text
shared model
serializers
readers
CLI rendering
GUI rendering
reports
diff logic
aggregation
tests
migration
documentation
```

Unknown enum values must not be silently interpreted as existing values.

Prefer an optional detail field over a new top-level enum when the distinction does not alter control flow.

---

# 20. Adding an error code

Stable error codes use:

```text
GF-WB-<DOMAIN>-<NUMBER>
```

A new code must define:

```text
owner
meaning
status mapping
error-kind mapping
retryability
user message
evidence
tests
```

Do not create one error code per dynamic message.

Do not reuse retired codes.

If codes are persisted or consumed externally, they become schema or API contracts.

---

# 21. Adding a CLI command

CLI commands belong to:

```text
app/main_cli.py
```

Business logic belongs to a shared service, not the parser.

Recommended flow:

```text
parse arguments
→ validate plain values
→ call bootstrap or application service
→ receive structured result
→ render concise output
→ map to exit code
```

A command proposal must define:

```text
command name
purpose
arguments
defaults
configuration precedence
side effects
structured result
exit codes
artifacts
interactive behavior
non-interactive behavior
tests
```

Rules:

- CLI must not call low-level stages directly when a shared service exists;
- CLI and GUI must share semantics;
- destructive commands require explicit intent;
- paths must be validated;
- machine-readable output requires a versioned format when stable.

---

# 22. Adding a GUI feature

GUI features belong under:

```text
app/gui/
```

The GUI must call the same application service as the CLI.

A GUI extension may:

- collect values;
- show validation;
- start a service call;
- display progress;
- display structured results;
- open artifacts.

It must not:

- build GF commands;
- call `subprocess` directly;
- implement different status meanings;
- reconstruct project identity;
- write gold directly;
- mutate persisted schemas directly.

Persist only disposable UI preferences through `app/state.py`.

---

# 23. Adding project configuration

Project configuration lives in:

```text
project/project.toml
```

A new field belongs there only when it describes:

```text
language identity
project source structure
GF project path
entrypoints
checkpoints
scenario policy
release policy
language-project validation facts
```

It does not belong there when it describes:

```text
local GF executable path
local RGL checkout path
local output root
window geometry
last selected tab
last run directory
temporary runtime state
```

A project-config extension must define:

```text
table/key
type
requiredness
default
ordering
path base
validation
compatibility
template value
migration
readers
```

Update both:

```text
project/project.toml
templates/project/project.toml
```

when the structure changes.

---

# 24. Extending the project template

The project template is language-neutral.

Template changes must preserve:

```text
cloneability
placeholder clarity
required structure
no active-language leakage
matching project documentation set
matching validation directories
```

A template extension requires review of:

```text
initializer
project loader
active project
template project
required-document checker
migration guide
tests
```

Do not copy active project linguistic data into the template.

Use placeholders only where the maintainer must supply a project-specific fact.

---

# 25. Adding a project document

A new project document is justified when it owns a stable responsibility not already covered.

Before adding one, ask:

```text
Does an existing project document already own this?
Will this file have a distinct maintainer or change cycle?
Is the content normative or merely a subsection?
Will another component or checker depend on its presence?
```

Prefer a section in an existing document when the topic has no independent owner.

If a project document becomes required:

- update the project template;
- update project completion checks;
- update repository/documentation maps;
- update migration instructions.

---

# 26. Adding an external tool

A new external tool requires an `EXT-OPTIONAL-*` contract before adoption.

The proposal must define:

```text
tool name
supported versions
purpose
why GF or Python is insufficient
license
installation
platforms
executable resolution
ordered arguments
working directory
environment
stdin
stdout
stderr
timeout
artifacts
success criteria
failure classes
security
fallback
tests
```

Rules:

- optional by default;
- no hidden auto-installation;
- no shell command string from untrusted input;
- exact executable is recorded;
- stdout and stderr are captured separately;
- timeout is finite;
- missing optional tool does not become a language failure;
- required adoption requires release and installation policy updates.

Examples that may justify an optional tool:

```text
Graphviz for dependency diagrams
archive utility for distribution
external PGF runtime smoke verifier
specialized coverage renderer
```

Convenience alone is insufficient.

---

# 27. Adding a dynamic plugin system

GF Wordbench does not require a general dynamic plugin system for the final core architecture.

Do not introduce one unless there is demonstrated need for:

```text
third-party extensions maintained outside the repository
independent version lifecycles
stable public extension API
sandboxing or trust policy
plugin discovery
compatibility negotiation
installation and removal
failure isolation
```

Before adding plugins, define:

```text
plugin manifest schema
API version
loading order
trust model
permissions
failure containment
dependency resolution
configuration namespace
artifact namespace
schema ownership
uninstall behavior
tests
```

Until those needs exist, use explicit repository-owned registration.

This avoids a large compatibility surface with little current value.

---

# 28. Explicit registries

Small explicit registries are acceptable when they improve deterministic ownership.

Examples:

```text
scanner rule registry
report writer registry
validation stage plan
artifact role registry
error-code registry
```

Registry requirements:

- declared in one owner;
- deterministic order;
- no import-time side effects;
- duplicate ID rejection;
- explicit metadata;
- unit tests;
- no filesystem scanning for Python modules;
- no entrypoint discovery from arbitrary installed packages.

A registry is not automatically a plugin system.

---

# 29. Dependency-direction review

Every extension must preserve expected flow:

```text
CLI / GUI
    → application services
    → bootstrap / audit core
    → stages and result services
    → infrastructure

reports
    → completed models

compiler / scenario runner
    → process runner

project loader
    → project.toml

active project
    → GF
```

Prohibited examples:

```text
report → compiler
GUI widget → process runner
process runner → diagnostic classifier
models → GUI
scanner → reports
project config → GUI state
template → active project
```

An extension creating a reverse dependency must be redesigned or justified by an architectural decision.

---

# 30. Configuration precedence

New settings must declare precedence.

Framework run settings normally use:

```text
explicit CLI or GUI value
→ active project value where override is allowed
→ framework default
```

Disposable UI state may suggest values but must not override required project identity or release policy silently.

A setting must not have different precedence in CLI and GUI.

---

# 31. Extension status lifecycle

Recommended lifecycle:

```text
experimental
active
deprecated
retired
```

Project-specific incomplete behavior may additionally use:

```text
temporary
fallback
warning
blocked
disabled
```

## 31.1 Experimental

Allowed when:

- API may still change;
- not required for release;
- clearly marked;
- tests exist;
- persisted compatibility is avoided or explicitly versioned.

## 31.2 Active

Requires:

- locked contract;
- stable behavior;
- tests;
- documentation;
- ownership;
- supported migration policy.

## 31.3 Deprecated

Requires:

- replacement;
- warning;
- deprecation version;
- removal target;
- compatibility tests;
- documentation.

## 31.4 Retired

Requires:

- no active caller;
- retained historical contract ID when applicable;
- migration completed;
- dead compatibility code removed according to policy.

---

# 32. Compatibility classification

Every extension is one of:

```text
internal compatible
compatible public extension
breaking public change
experimental
```

## 32.1 Internal compatible

No public or persisted contract changes.

## 32.2 Compatible public extension

Examples:

```text
optional field with documented default
optional scenario
optional report
optional manifest role
new CLI command
new non-gating stage
```

Requires consumer review.

## 32.3 Breaking public change

Examples:

```text
renamed public symbol
changed function signature
changed status meaning
changed artifact path
changed schema type
changed scenario ID
changed normalization
changed entrypoint semantics
changed command arguments
```

Requires migration and versioning.

---

# 33. Persisted-schema procedure

For any persisted change:

```text
1. identify schema ID
2. identify current version
3. classify compatible or breaking
4. define canonical writer behavior
5. identify all readers
6. define defaults and null semantics
7. define deterministic ordering
8. define migration
9. preserve legacy read support where required
10. add schema fixtures and tests
11. update PERSISTED_SCHEMA_LOCK.md
12. update schema reference documents
```

Canonical writers must not continue emitting legacy aliases.

Readers must not rewrite sources during ordinary loading.

---

# 34. External-contract procedure

For any command or tool change:

```text
1. identify external contract ID
2. record current request
3. define new request
4. record GF/tool versions
5. define working directory
6. define environment
7. define timeout
8. define stream handling
9. define artifacts
10. define success and failure
11. update request builder
12. update process/result models
13. add fake-process tests
14. add real integration tests
15. update external-tool lock
```

Do not change one caller's command independently.

---

# 35. Project-contract procedure

When an extension changes active-language files:

```text
provider
→ direct consumers
→ downstream entrypoints
→ scenarios
→ inputs
→ gold
→ project configuration
→ dependency map
→ status ledger
→ project contract lock
→ release evidence
```

Language-specific extension code and configuration belong under `project/`, not the generic framework.

---

# 36. Security review

Security review is required when an extension:

- launches a process;
- accepts paths;
- writes source-controlled files;
- reads untrusted configuration;
- supports shell escapes;
- extracts archives;
- follows symlinks;
- loads external code;
- persists environment data;
- exposes a network service.

Review:

```text
path containment
symlink handling
argument separation
shell usage
secret redaction
output bounds
overwrite policy
permissions
trust boundary
failure cleanup
```

A dynamic plugin system requires a separate trust model and must not be added casually.

---

# 37. Performance review

Performance optimization must not weaken correctness.

Before adding caches, concurrency, or lazy behavior, define:

```text
cache key
invalidations
deterministic ordering
artifact isolation
failure behavior
release-mode policy
tests
```

Do not introduce a cache solely because GF execution is slow.

First measure:

```text
stage duration
target count
artifact size
repeated work
```

Release mode should prefer clean reproducible evidence.

---

# 38. Concurrency extension

Parallel execution is allowed only when:

- requests are independent;
- output paths cannot collide;
- result ordering remains deterministic;
- process count is bounded;
- cancellation is safe;
- timeout handling is independent;
- Windows behavior is tested;
- GF behavior supports concurrency.

Completion order must not become persisted order.

Start with serial execution unless measured need justifies concurrency.

---

# 39. Cancellation extension

A cancellable operation must define:

```text
cancellation point
active process termination
partial evidence
status mapping
not-started item handling
CLI exit
GUI presentation
persistence
```

Cancellation is not a language `FAIL`.

Do not add cancellation to one frontend only.

The shared service must own semantics.

---

# 40. Observability extension

New logs or metrics must have a purpose.

Allowed examples:

```text
stage timing
target counts
artifact sizes
cache hits
process launch facts
```

Rules:

- logs do not replace structured results;
- metrics do not contain secrets;
- high-cardinality path data is bounded;
- runtime logs do not become accidental persisted APIs;
- stable machine-consumed metrics require schema review.

---

# 41. Documentation updates

An extension may require updates to:

```text
component map
architecture overview
execution flow
data model
artifact model
error-handling model
validation pipeline
mode reference
CLI reference
GUI reference
configuration reference
report reference
schema reference
project template
migration guide
release process
changelog
ADR
```

Avoid duplicating normative content.

Link to the owning lock or reference.

---

# 42. Test strategy

Every extension should use the smallest appropriate test layers.

## 42.1 Unit tests

Use for:

```text
pure parsing
path validation
request construction
normalization
classification
serialization
formatting
```

## 42.2 Contract tests

Use for:

```text
public signatures
provider/consumer boundaries
artifact ownership
dependency direction
status semantics
schema fields
CLI/GUI shared service
read-only gold behavior
```

## 42.3 Integration tests

Use for:

```text
real GF execution
filesystem behavior
atomic replacement
process timeout
project initialization
report finalization
```

## 42.4 Platform tests

At minimum review:

```text
Windows paths with spaces
UTF-8
CRLF inputs
native gf.exe
missing executable
unwritable output
timeout
```

---

# 43. Test fixture policy

Fixtures must be:

- small;
- deterministic;
- language-neutral when testing framework behavior;
- explicit about GF version requirements;
- independent of the active project;
- free of personal absolute paths;
- free of stale generated artifacts.

Use the active language project only for project validation, not as the sole framework test fixture.

---

# 44. Adding a fixture grammar

A fixture grammar should contain only what is needed to test:

```text
successful compile
syntax failure
type failure
PGF build
load scenario
linearization
parse
bounded generation
UTF-8 behavior
```

Keep fixture entrypoints and artifacts distinct from the active project.

Document any expected GF-version differences.

---

# 45. Release-gate integration

An extension affecting release must define:

```text
whether it gates release
which modes execute it
required success criteria
required artifacts
failure status
skip policy
migration for existing projects
```

A new required release stage is a breaking operational change unless existing projects receive a migration path and defaults.

Do not make an experimental stage release-required.

---

# 46. Adding a mode

Adding a validation mode is strongly discouraged.

The canonical modes are:

```text
quick
checkpoint
release
diagnostic
```

A new mode is justified only when its stage-selection semantics cannot be expressed through:

- target selection;
- required/optional configuration;
- command flags;
- scenario selection;
- fail-fast behavior.

A new mode affects:

```text
configuration
state
CLI
GUI
orchestration
summary schema
migration aliases
documentation
tests
```

Prefer extending existing modes.

---

# 47. Adding a status

Adding a validation status is strongly discouraged.

Canonical statuses are:

```text
OK
FAIL
ERROR
SKIPPED
```

Most new distinctions belong in:

```text
execution facts
error kind
diagnostic class
warning records
detail fields
```

A new status changes aggregation, reports, CLI exits, GUI rendering, schemas, migrations, and consumers.

Use it only when existing dimensions cannot represent the semantics.

---

# 48. Extension examples

## 48.1 Example — New scanner rule

Need:

```text
detect one suspicious GF source pattern
```

Correct design:

```text
add scanner-owned rule
add count/finding
add tests
review persistence if count is serialized
```

Incorrect design:

```text
create a new validation component and report
```

---

## 48.2 Example — Dependency diagram

Need:

```text
render project dependency graph
```

Balanced design:

```text
dependency data remains owned by project/dependency analysis
optional report writer creates DOT
Graphviz rendering remains optional external tool
SVG/PNG artifact gets manifest role
```

Do not make Graphviz required for validation.

---

## 48.3 Example — PGF runtime smoke check

Need:

```text
load built PGF in another runtime
```

This may justify:

- a new optional external-tool contract;
- a new release stage;
- a distinct result;
- runtime-specific artifact evidence.

It should not be folded into the generic process runner or Markdown report.

---

## 48.4 Example — New report field

Need:

```text
show compile duration percentile
```

If computed only for a human report:

- derive from existing results;
- no schema change needed.

If automation consumes it from `summary.json`:

- define persisted field;
- update schema and readers.

---

## 48.5 Example — Language-specific morphology validation

Need:

```text
validate a language-specific paradigm
```

Correct design:

```text
project .gfs scenario
project input file
optional gold/assertion
project validation docs
```

Incorrect design:

```text
hardcode the language paradigm in app/audit/
```

---

# 49. Common overengineering traps

Avoid:

```text
abstract base class with one implementation
dependency-injection container for simple construction
runtime plugin scanning
event bus for direct calls
separate component for every report section
separate result class for every small rule
generic repository layer for local files
new schema for temporary debug output
automatic code generation without stable need
configuration key for every constant
```

Introduce abstraction after repeated concrete need, not before.

---

# 50. Common underengineering traps

Also avoid:

```text
one large audit_core.py implementing every stage
duplicate command building
duplicate GF path resolution
untyped dictionaries crossing boundaries
reports reading raw logs to infer status
GUI launching processes directly
new fields without defaults
silent schema aliases
gold rewriting during validation
project-specific framework conditionals
```

Balanced architecture means clear ownership without fragmentation.

---

# 51. Drift indicators

Extension drift likely exists when:

- two components implement the same rule;
- CLI and GUI produce different requests;
- a report invokes validation;
- a new persisted field has no schema update;
- a project field appears in application state;
- a framework module contains a language suffix;
- a new external option appears in only one caller;
- a reader rewrites an asset it does not own;
- a validation stage changes status vocabulary;
- a new artifact is absent from the manifest;
- a template differs structurally from the active project requirements;
- an experimental feature becomes required silently;
- a private helper is imported by another component;
- completion order changes persisted order;
- an optional tool becomes an undeclared dependency;
- tests rely on developer-global paths.

Any indicator requires ownership and contract review.

---

# 52. Extension review checklist

```text
[ ] Problem is concrete
[ ] Existing owner considered first
[ ] Extension category identified
[ ] New component threshold satisfied if applicable
[ ] Provider identified
[ ] Consumers identified
[ ] Public API defined
[ ] Failure semantics defined
[ ] Status/error dimensions reviewed
[ ] Artifacts and ownership reviewed
[ ] Persistence reviewed
[ ] External-tool boundary reviewed
[ ] Project boundary reviewed
[ ] CLI and GUI share a service
[ ] Security reviewed
[ ] Determinism reviewed
[ ] Compatibility classified
[ ] Migration defined
[ ] Unit tests added
[ ] Contract tests added
[ ] Integration tests added where required
[ ] Windows behavior reviewed
[ ] Locks updated
[ ] Documentation updated
[ ] Release impact reviewed
[ ] No unnecessary abstraction added
```

---

# 53. Definition of extension complete

An extension is complete when:

1. its need is documented;
2. its owner is unambiguous;
3. its boundary is no larger than necessary;
4. providers and consumers agree;
5. errors are represented correctly;
6. artifacts have one owner;
7. persisted changes are versioned;
8. external requests are contracted;
9. language-specific behavior remains in the project;
10. CLI and GUI share semantics;
11. tests cover normal and failure paths;
12. compatibility and migration are documented;
13. required locks are updated;
14. documentation matches implementation;
15. release behavior remains explicit.

---

# 54. Final invariants

Extensions must preserve:

1. Python orchestrates and GF executes GF semantics.
2. One active language project remains authoritative.
3. Framework code remains language-neutral.
4. Every public responsibility has one owner.
5. Every external request is explicit.
6. Every external process has a timeout.
7. Raw evidence is captured before interpretation.
8. Reports consume results and do not rerun validation.
9. Gold remains read-only during ordinary validation.
10. Persisted formats are versioned and migrated.
11. CLI and GUI use shared application services.
12. Deterministic ordering is preserved.
13. Optional extensions remain visible but non-gating unless declared.
14. Experimental behavior does not become stable silently.
15. New abstractions require a real boundary.
16. New statuses and modes are exceptional.
17. Active-project changes update project contracts.
18. Required artifacts appear in the manifest.
19. Security boundaries are explicit.
20. Existing projects receive compatibility or migration.

---

# 55. Final rule

> Extend GF Wordbench by adding the smallest explicit contract that solves the real problem.

Do not create architecture for hypothetical extensions.

Do not hide real cross-component behavior inside informal conventions.

The correct extension is the one that adds capability while preserving ownership, evidence, compatibility, and a comprehensible system.
