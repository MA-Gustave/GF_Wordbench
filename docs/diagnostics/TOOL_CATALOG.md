# GF Wordbench — Diagnostic Tool Catalog

| Champ | Valeur |
|---|---|
| Document role | Safe diagnostic-tool registry contract |
| Decision status | Accepted |
| Owner | GF Wordbench maintainers |
| Alignment authority | `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` |
| External-tool authority | `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` |
| Product-boundary authority | ADR-0001, ADR-0011 and ADR-0012 |
| Last reviewed | 2026-07-24 |

## 1. Purpose

This document defines the catalog of diagnostic tools that GF Wordbench may execute.

The catalog is a static allowlist. A tool can be executed only when its identity, executable contract, inputs, flags, path boundaries, mutability, timeout, output limits and evidence role are explicitly registered.

The catalog prevents:

- arbitrary command execution;
- unreviewed binaries;
- undocumented flags;
- uncontrolled filesystem access;
- silent network use;
- unbounded output;
- unbounded execution time;
- mutable operations hidden inside read-only workflows;
- AI-assisted output being treated as normative evidence;
- product-specific integrations leaking into the Wordbench core.

## 2. Scope

This contract governs diagnostic executables invoked by the `diagnostics` module through the external-tool port.

It applies to tools used for:

- source inspection;
- structure analysis;
- syntax or encoding checks;
- dependency inspection;
- artifact inspection;
- report enrichment;
- controlled recovery diagnostics;
- optional AI-assisted analysis.

It does not govern:

- normal GF compilation;
- native `.gfs` scenario execution;
- arbitrary user scripts;
- shell aliases;
- editor plugins;
- `gf-portfolio` tools;
- tools executed outside GF Wordbench.

GF compilation and scenario execution remain governed by `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`.

## 3. Product boundary

GF Wordbench executes diagnostic tools only for the single active project in the current workspace and run.

The catalog must not contain:

- a multi-workspace registry;
- Portfolio aggregation commands;
- `gf-portfolio` private paths;
- `gf-portfolio` storage adapters;
- commands that require `gf-portfolio` to be installed;
- tools that mutate another product's state.

`gf-portfolio` may consume public, versioned Wordbench artifacts. It does not participate in Wordbench diagnostic execution.

## 4. Registry model

Each registered tool declares:

```text
tool_id
catalog_version
tool_version_policy
description
purpose
executable_resolution
input_contract
allowed_flags
working_directory_policy
environment_policy
mutability
confirmation_policy
allowed_paths
network_policy
timeout_sec
output_limit_bytes
evidence_roles
normalization_profile
parser_id
ai_assisted
normative
availability_policy
platforms
```

## 5. Field contracts

### 5.1 `tool_id`

`tool_id` is the stable catalog identity.

Rules:

- unique within the catalog;
- lowercase;
- ASCII;
- uses letters, digits and hyphens;
- never reused for a different command contract;
- independent from the executable filename.

Example:

```text
gf-version
source-encoding-check
dependency-inspector
```

### 5.2 `catalog_version`

`catalog_version` identifies the registry contract version that defines the entry.

A breaking change to flags, mutability, path access, evidence meaning or parser behavior requires a new catalog version or a new tool ID.

### 5.3 `tool_version_policy`

The version policy declares:

```text
minimum_version
maximum_version
tested_versions
blocked_versions
version_probe
unparseable_version_policy
```

A tool version outside policy cannot run silently.

### 5.4 `description`

The description states what the tool does in concise user-facing language.

It must not claim capabilities outside the registered command contract.

### 5.5 `purpose`

The purpose identifies the diagnostic question answered by the tool.

Examples:

```text
inspect source encoding
detect dependency cycles
summarize generated artifact metadata
analyze preserved logs
```

### 5.6 `executable_resolution`

Resolution declares the permitted executable sources.

Allowed forms include:

```text
bundled executable
configured absolute path
approved PATH lookup
platform-specific registered location
```

Rules:

- resolution is explicit;
- the resolved executable is recorded;
- no shell alias is treated as an executable contract;
- no project-controlled value becomes an arbitrary command;
- resolution failure is a tool availability error.

### 5.7 `input_contract`

The input contract defines:

```text
accepted subject kinds
accepted file types
accepted encodings
maximum input count
maximum input size
stdin policy
temporary-file policy
```

A tool receives only inputs permitted by its contract.

### 5.8 `allowed_flags`

Flags are statically enumerated.

Rules:

- arbitrary flags are prohibited;
- each flag has a defined type and meaning;
- mutually exclusive flags are declared;
- default flags are explicit;
- project content cannot inject new flags;
- unsupported flags cause request rejection.

### 5.9 `working_directory_policy`

The policy identifies the allowed working-directory class:

```text
run directory
active project root
source root
tool-owned temporary directory
```

The working directory must resolve inside an approved root.

### 5.10 `environment_policy`

Environment changes are minimal and explicit.

The entry declares:

```text
allowed variables
removed variables
inherited variables
secret-redaction rules
locale policy
encoding policy
```

Complete environment dumps are prohibited.

### 5.11 `mutability`

Canonical values:

```text
read_only
run_artifacts_only
project_mutating
external_mutating
```

Default:

```text
read_only
```

Rules:

- read-only tools cannot modify project files;
- run-artifact tools write only under the current run directory;
- project-mutating tools require a separate explicit operation;
- external-mutating tools are prohibited unless an accepted security decision defines the operation.

### 5.12 `confirmation_policy`

Canonical values:

```text
none
explicit_user_confirmation
reviewed_batch_operation
```

A mutable operation never inherits confirmation from a previous run.

### 5.13 `allowed_paths`

The entry declares readable and writable path classes separately.

Example:

```text
read:
  - project sources
  - current run evidence

write:
  - current run tool-output directory
```

Rules:

- path traversal is rejected;
- symlink escape is rejected under strict policy;
- source roots and run roots remain distinct;
- no tool writes outside registered roots;
- absolute developer-specific paths are not catalog contracts.

### 5.14 `network_policy`

Canonical values:

```text
denied
loopback_only
approved_endpoints
```

Default:

```text
denied
```

When `approved_endpoints` is used, the entry declares exact hosts, protocols, authentication policy and evidence-redaction rules.

### 5.15 `timeout_sec`

Every invocation has a finite positive timeout.

The catalog may define separate limits by operation class, but an invocation cannot run without an effective timeout.

### 5.16 `output_limit_bytes`

The tool entry declares bounded limits for:

```text
stdout
stderr
generated files
total retained output
```

Truncation is explicit and preserved as evidence.

### 5.17 `evidence_roles`

Evidence roles identify how retained outputs appear in the run manifest.

Canonical examples:

```text
tool_stdout
tool_stderr
tool_report
tool_metadata
tool_diff
tool_recovery_record
ai_annotation
```

Every retained output has one owner and one manifest role.

### 5.18 `normalization_profile`

Normalization is named and deterministic.

It may remove approved environmental instability, but it must not:

- replace raw evidence;
- hide failures;
- rewrite diagnostic meaning;
- remove security-relevant details;
- convert incomplete output into successful output.

### 5.19 `parser_id`

`parser_id` identifies the controlled parser that converts raw tool evidence into structured diagnostics.

Unknown or unparseable output remains visible.

A parser failure is distinct from a tool-reported project failure.

### 5.20 `ai_assisted`

Canonical values:

```text
false
true
```

When `true`:

- the operation is visibly identified as AI-assisted;
- raw source evidence remains available;
- prompts and supplied evidence are recorded according to policy;
- secrets and unrelated data are excluded;
- output is advisory;
- output cannot determine normative validation status;
- the tool cannot rewrite project sources during normal diagnostics.

### 5.21 `normative`

Canonical values:

```text
false
true
```

A normative tool may affect a validation or release decision only when:

- its contract is owned by Wordbench;
- its evidence is reproducible;
- its parser and status mapping are defined;
- its absence policy is explicit;
- its version compatibility is enforced.

AI-assisted tools always use:

```text
normative = false
```

### 5.22 `availability_policy`

Canonical values:

```text
required
optional
diagnostic_only
```

Rules:

- absence of an optional tool does not fail core validation;
- absence of a required tool produces an explicit configuration or tool error;
- diagnostic-only tools cannot become hidden release prerequisites.

### 5.23 `platforms`

The entry declares supported platforms and executable forms.

Example:

```text
windows
linux
macos
```

Unsupported platforms fail before execution.

## 6. Registry policies

- the registry is static, versioned and reviewable;
- every tool is identified by `tool_id`;
- no arbitrary executable or flag is accepted;
- read-only behavior is the default;
- mutable workflows are separate and explicitly confirmed;
- every process uses the shared external-tool port;
- every invocation has bounded time and output;
- stdout and stderr remain separate;
- raw evidence is preserved before normalization;
- tool versions and commands are recorded;
- unavailable tools are handled according to their availability policy;
- tools do not infer or change active project identity;
- tools do not bypass artifact ownership;
- tools do not write reports directly;
- tools do not mutate gold files during normal validation;
- AI-assisted tools remain optional, visible and non-normative.

## 7. Execution contract

A diagnostic request contains:

```text
tool_id
active_project_id
run_id
subject_ids
resolved_inputs
selected_registered_flags
working_directory
timeout_sec
output_limits
confirmation_record
```

Execution proceeds as follows:

```text
catalog lookup
→ request validation
→ executable resolution
→ path containment validation
→ confirmation validation
→ structured process request
→ execution through external-tool port
→ raw evidence capture
→ output-limit and timeout handling
→ parser and normalization
→ structured diagnostic result
→ manifest registration
```

A request is rejected before launch when any field violates the catalog entry.

## 8. Result contract

A diagnostic-tool result contains:

```text
tool_id
catalog_version
resolved_tool_version
status
execution_state
exit_code
duration_ms
command
working_directory
stdout_path
stderr_path
output_artifacts
truncated
diagnostics
evidence_roles
ai_assisted
normative
```

The result distinguishes:

- launch failure;
- timeout;
- cancellation;
- tool failure;
- parser failure;
- invalid request;
- unavailable optional tool;
- successful execution with findings;
- successful execution without findings.

## 9. Status semantics

A tool execution status must not reuse project-validation meaning ambiguously.

Canonical execution outcomes:

```text
completed
failed
error
skipped
```

Interpretation:

- `completed`: the tool ran and its output was processed;
- `failed`: the tool ran and reported a defined failed criterion;
- `error`: execution, parsing, evidence capture or contract enforcement failed;
- `skipped`: the tool was intentionally omitted under policy.

A diagnostic finding is not automatically a release failure. The owning validation contract defines whether a finding is gating.

## 10. Mutating operations

Mutating tools are isolated from normal diagnostic execution.

A mutating operation requires:

```text
separate tool entry
explicit mutability class
explicit user confirmation
declared writable roots
pre-change evidence
change manifest
post-change evidence
recovery or rollback policy
```

Normal validation must not invoke a project-mutating tool.

## 11. AI-assisted tools

AI-assisted diagnostics follow these additional rules:

- no automatic source modification;
- no autonomous gold update;
- no normative status decision;
- no hidden network transfer;
- no submission of unrelated repository content;
- no use of private consumer state;
- clear identification of the model or service when retained by policy;
- prompt and evidence provenance preserved where required;
- output stored under an `ai_annotation` or equivalent advisory role.

## 12. Security rules

- shell execution is prohibited unless a separate accepted contract requires it;
- arguments are passed as an executable and argument vector;
- project-controlled text cannot select a new executable;
- paths are normalized before containment checks;
- output files remain under approved roots;
- process-tree termination is enforced on timeout;
- secrets are redacted from rendered commands and logs;
- environment inheritance is minimized;
- network access is denied by default;
- generated files are inventoried;
- unexpected mutation stops the operation;
- untrusted output is never executed as code.

## 13. Catalog entry example

```yaml
tool_id: source-encoding-check
catalog_version: "1.0"
tool_version_policy:
  minimum_version: "1.0"
  tested_versions:
    - "1.0"
description: Validate source encoding and Unicode decoding.
purpose: Detect unreadable or incorrectly encoded project source files.
executable_resolution:
  type: bundled
input_contract:
  subject_kinds:
    - source_file
  file_types:
    - .gf
allowed_flags:
  strict:
    type: boolean
working_directory_policy: active_project_root
environment_policy:
  locale: utf-8
mutability: read_only
confirmation_policy: none
allowed_paths:
  read:
    - project_sources
  write:
    - current_run_tool_output
network_policy: denied
timeout_sec: 30
output_limit_bytes:
  stdout: 1048576
  stderr: 1048576
  total_files: 4194304
evidence_roles:
  - tool_stdout
  - tool_stderr
  - tool_report
normalization_profile: source-encoding-v1
parser_id: source-encoding-v1
ai_assisted: false
normative: true
availability_policy: required
platforms:
  - windows
  - linux
  - macos
```

## 14. Change control

A catalog change reviews:

```text
tool identity
version policy
executable resolution
flags
inputs
path access
mutability
confirmation
network access
timeout
output limits
parser
normalization
evidence roles
status mapping
platform support
security consequences
tests
documentation
```

A change that expands executable choice, writable paths, network access or mutability requires security review.

## 15. Validation checklist

```text
[ ] tool ID is unique
[ ] executable resolution is controlled
[ ] version policy is explicit
[ ] allowed flags are enumerated
[ ] inputs are bounded
[ ] working directory is approved
[ ] environment policy is minimal
[ ] mutability is explicit
[ ] confirmation is enforced where required
[ ] readable and writable roots are distinct
[ ] network is denied or explicitly constrained
[ ] timeout is finite
[ ] output limits are finite
[ ] stdout and stderr remain separate
[ ] raw evidence is preserved
[ ] parser failure remains visible
[ ] retained outputs have manifest roles
[ ] AI assistance is visible and non-normative
[ ] Wordbench remains independent from gf-portfolio
[ ] tests cover rejection and execution paths
```

## 16. Governing rule

> GF Wordbench executes only diagnostic tools whose complete command, input, path, mutability, timeout, output and evidence contracts are registered in this catalog.

Anything not registered is not executable through the diagnostic-tool subsystem.
