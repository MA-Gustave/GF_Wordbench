# GF Wordbench — External Tool Contract Lock

**Document ID:** `GF-WB-EXT-TOOL-LOCK`  
**Status:** Normative  
**Contract version:** `2.0.0`  
**Applies to:** external executables and operating-system process services used by GF Wordbench for one active project and one run  
**Primary external tool:** Grammatical Framework (`gf` or `gf.exe`)  
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`  
**Implementation note:** exact supported flags and versions must be verified against current source and executable evidence before being documented as implemented

---

## 1. Purpose

This file prevents drift between Wordbench and external executables. It locks the structured request, process behavior, evidence capture and interpretation boundary.

GF is authoritative for GF parsing, type checking, compilation, interactive or scripted command semantics and GF-produced artifacts. Wordbench is authoritative for orchestration, process limits, evidence preservation, classification, normalization, comparison and reporting.

## 2. Product boundary

External tools are invoked only for one resolved active Wordbench project in one run.

Wordbench must not:

- discover or execute projects from a Portfolio workspace registry;
- invoke tools on behalf of cross-workspace aggregation;
- expose private process-runner APIs as a required `gf-portfolio` dependency;
- require Portfolio to resolve GF, execute a run or interpret process evidence.

`gf-portfolio` may consume completed public Wordbench artifacts. Any Portfolio-specific executable boundary belongs to the Portfolio product.

## 3. Process request contract

Every process request must represent at least:

```text
tool identifier
resolved executable path
argument vector
working directory
environment additions or removals
standard-input payload or input source
timeout or run-budget allocation
expected artifact roots
mutability classification
evidence-capture policy
```

Locked rules:

- commands are constructed as an executable plus an argument vector;
- project-controlled text must not become a shell command;
- shell execution is prohibited unless a separate accepted and security-reviewed contract explicitly requires it;
- executable and working-directory paths are resolved before launch;
- path resolution cannot escape approved roots;
- environment changes are explicit and local to the process;
- stdin bytes and encoding are explicit;
- a request cannot target several active projects;
- secrets must not be copied into reports or raw logs without an explicit redaction contract.

## 4. Process response contract

Every process response must distinguish:

```text
launch success or launch failure
exit code or absence of exit code
stdout bytes/text
stderr bytes/text
start and end timestamps or duration
timeout, cancellation or forced termination
produced, changed or missing artifacts
truncation or output-limit events
cleanup outcome
```

Raw evidence is captured before normalization or diagnostic parsing.

A response must not collapse these states:

- executable not found;
- permission or working-directory failure;
- timeout;
- user cancellation;
- non-zero tool exit;
- zero exit with missing required artifact;
- successful tool execution with language validation failure;
- Wordbench contract failure after tool completion.

## 5. GF executable resolution

Resolution sources may include only documented and controlled inputs, such as:

1. explicit run or environment configuration permitted by the owner schema;
2. validated application configuration;
3. documented platform lookup such as `PATH`;
4. no silent language-project fallback to a machine-specific absolute path.

Locked rules:

- the resolved file must exist and be executable for the platform;
- the resolution source is recorded in run evidence without leaking secrets;
- project documentation may state compatibility requirements but must not store an environment-specific executable path as a portable project fact;
- failure to resolve GF is a launch/configuration failure, not a language diagnostic;
- version probing uses the same controlled process boundary.

## 6. GF version compatibility

Compatibility claims require reproducible evidence from the current executable or supported test matrix.

Documentation must distinguish:

- minimum required version;
- tested versions;
- unsupported versions;
- unknown compatibility;
- accepted target policy not yet enforced by code.

Unknown output from version probing cannot be silently interpreted as compatible.

## 7. GF search paths and working directory

GF path inputs derive from the active project configuration and documented environment aliases.

Locked rules:

- path order is deterministic and semantically significant;
- project-relative paths resolve against the active project root;
- approved external RGL roots are resolved explicitly;
- duplicate normalized paths may be removed only without changing precedence;
- nonexistent required paths produce explicit evidence;
- command construction does not guess another language or workspace;
- the working directory is recorded and belongs to an approved root.

## 8. Static scan versus GF execution

A static scan is a Wordbench precheck. It is not GF parsing, type checking or compilation.

Only evidence from GF execution may support claims such as:

- GF accepted a module;
- a module compiled;
- a PGF was built;
- a `.gfs` command executed successfully;
- GF produced a diagnostic or artifact.

Static findings and GF findings may be correlated but remain distinct result kinds.

## 9. Compilation and PGF contract

A compile or PGF request identifies:

```text
one active project
one selected module or entrypoint
resolved GF path order
working directory
timeout or run budget
expected artifact root
```

Locked rules:

- source mutation is prohibited during normal validation;
- pre-existing artifacts are inventoried before execution when freshness matters;
- a required artifact must be attributable to the current request;
- stale `.gfo` or `.pgf` files do not satisfy current validation;
- artifact existence alone does not prove successful current execution;
- expected PGF identity is project-owned and must be explicit before release validation;
- compile and PGF results retain raw stdout, stderr and exit status.

## 10. Native `.gfs` scenario contract

Scenarios are project-owned native `.gfs` scripts executed through GF.

A scenario request identifies:

```text
scenario ID
scenario file
active project and entrypoint context
declared inputs
stable markers
normalization profile
timeout or run budget
expected gold when regression comparison is enabled
```

Locked rules:

- scenario IDs are registered in active-project configuration or its owner documentation;
- arbitrary unregistered scripts are not silently release-validating scenarios;
- scenario-controlled text does not become a host shell command;
- raw transcript is preserved before normalization;
- marker extraction failure is explicit;
- comparison uses normalized evidence while retaining raw evidence;
- normal validation never overwrites gold files;
- gold updates require an explicit reviewed workflow.

## 11. Output normalization

Normalization is deterministic, named and versioned when changes can alter comparisons.

It may normalize documented instability such as:

- line endings;
- approved path prefixes;
- approved nondeterministic timestamps;
- documented encoding artifacts;
- stable scenario marker extraction.

It must not:

- delete evidence required to understand a failure;
- turn failure output into success;
- reorder semantically ordered output without a specific contract;
- replace the raw transcript;
- hide tool-version incompatibility.

## 12. Timeout, cancellation and termination

Timeout and cancellation are first-class terminal conditions.

Locked rules:

- the requested timeout or budget is recorded;
- termination attempts include child processes where supported and documented;
- partial stdout, stderr and artifacts are retained;
- forced termination is not reported as ordinary tool failure;
- cleanup failures are recorded separately;
- no later stage treats a timed-out prerequisite as successful.

## 13. Diagnostic tool allowlist

Executable diagnostic tools are registered statically. Each entry defines:

```text
tool ID
purpose
executable resolution policy
allowed arguments
working-directory policy
input policy
output limits
timeout
mutability
network policy
evidence role
normalization and parser
implementation and verification status
```

Locked rules:

- arbitrary user-supplied commands are prohibited;
- diagnostic tools cannot bypass the central process boundary;
- mutating tools require explicit user intent and cannot run during normal read-only validation;
- AI-assisted tools are optional, visible and non-normative;
- tool absence cannot invalidate core GF evidence unless the tool is explicitly required by an accepted release contract;
- a registry entry marked planned is not executable capability.

## 14. Security boundary

- argument vectors are preferred over shells;
- approved roots are validated after normalization and symlink resolution where applicable;
- output-size limits prevent unbounded capture;
- timeouts and process-tree cleanup prevent abandoned work;
- untrusted scenario and source content is treated as active tool input, not passive text;
- raw logs are reviewed for secret and personal-data exposure;
- generated artifacts cannot escape approved output roots;
- external-tool contract changes require security review when they expand execution, network or mutation capability.

## 15. Evidence and reporting

Reports must preserve the distinction between:

```text
request configuration
resolved executable and version
launch result
tool result
validation interpretation
raw evidence
normalized evidence
generated artifacts
timeout or cancellation
```

A report may summarize raw evidence but must provide its artifact identity or path when retained.

## 16. Change control

Changing an external-tool contract requires coordinated review of:

1. request and result models;
2. executable resolver;
3. command builder;
4. process adapter;
5. diagnostics and normalization;
6. artifact ownership and persisted schemas;
7. tests and fixtures;
8. security consequences;
9. implementation alignment;
10. this lock and correction ledger.

## 17. Validation checklist

```text
[ ] one active project and one run are identified
[ ] executable resolution is explicit
[ ] argument vector is used; no uncontrolled shell interpolation
[ ] working directory and environment are explicit
[ ] timeout and cancellation are represented
[ ] raw stdout, stderr, exit state and artifacts are preserved
[ ] static scan is not presented as GF execution
[ ] stale artifacts cannot satisfy current execution
[ ] normalization is deterministic and non-destructive
[ ] scenario and gold mutation requires explicit workflow
[ ] diagnostic tools are allowlisted
[ ] Wordbench does not execute Portfolio workspaces
[ ] implementation claims have executable or source evidence
```
