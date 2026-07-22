# GF Wordbench — Automation and CI

**Document ID:** `GF-WB-OPS-AUTOMATION-CI`  
**Status:** Normative  
**Applies to:** Continuous integration, scheduled validation, release automation, and machine-driven GF Wordbench execution  
**Owner:** GF Wordbench maintainers  
**Operations contract version:** `1.0.0`  
**Target path:** `C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench\docs\operations\AUTOMATION_AND_CI.md`  
**Last structural review:** 2026-07-22

---

## 1. Purpose

This document defines how GF Wordbench is executed safely and reproducibly by automation.

It establishes:

- the supported automation boundary;
- the required CI workflow families;
- job and stage responsibilities;
- environment and toolchain preparation;
- source and dependency pinning;
- command invocation rules;
- status and exit handling;
- evidence preservation;
- artifact upload and retention;
- release promotion;
- security for trusted and untrusted changes;
- caching constraints;
- concurrency and cancellation;
- failure recovery;
- provider-neutral CI requirements;
- the transition from the predecessor `gf-audit` interface.

The central rule is:

> Automation must call GF Wordbench through its public interface, preserve the resulting evidence, and decide gates from structured results rather than recreating validation logic in CI configuration.

---

## 2. Scope

This document governs automation that performs one or more of the following:

- Python syntax and package checks;
- unit tests;
- contract tests;
- schema tests;
- project-structure checks;
- GF executable and version preflight;
- `quick` validation;
- `checkpoint` validation;
- `diagnostic` validation;
- `release` validation;
- report verification;
- artifact-manifest verification;
- artifact archival;
- release promotion;
- scheduled regression checks;
- manual CI dispatch;
- compatibility matrices;
- release evidence retention.

It applies to:

- hosted CI;
- self-hosted CI;
- local CI emulation;
- protected release runners;
- repository automation scripts;
- external orchestrators that invoke the CLI.

---

## 3. Non-scope

This document does not define:

- the exact CLI spelling of every command and option;
- vendor-specific action versions;
- provider account administration;
- cloud billing;
- runner image maintenance outside GF Wordbench requirements;
- repository branch-protection UI steps;
- the internal implementation of validation stages;
- automatic AI diagnosis;
- automatic source modification;
- automatic gold acceptance;
- deployment of services unrelated to GF Wordbench;
- a general workflow engine.

Exact command syntax belongs to:

```text
docs/usage/CLI_REFERENCE.md
```

Exact exit-code values belong to:

```text
docs/reference/EXIT_CODES.md
```

This document defines the behavioral contract those interfaces must support.

---

## 4. Related normative documents

```text
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/EXTENSION_BOUNDARIES.md
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/VALIDATION_MODES.md
docs/validation/RELEASE_GATES.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/AI_READY_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
docs/operations/RUN_DIRECTORY_LIFECYCLE.md
docs/operations/CLEANUP_BACKUP_AND_RECOVERY.md
docs/operations/WINDOWS_LAUNCHERS.md
docs/release/VERSIONING_POLICY.md
docs/release/RELEASE_PROCESS.md
docs/reference/EXIT_CODES.md
docs/reference/COMMAND_REFERENCE.md
project/docs/VALIDATION_SPEC.md
project/docs/RELEASE_CRITERIA.md
```

When a CI rule overlaps a persisted artifact schema, `PERSISTED_SCHEMA_LOCK.md` is authoritative.

When it overlaps GF process behavior, `EXTERNAL_TOOL_CONTRACT_LOCK.md` is authoritative.

When it overlaps project release policy, `project/docs/RELEASE_CRITERIA.md` may add stricter requirements but may not weaken framework integrity requirements.

---

## 5. Normative terms

- **MUST**: mandatory.
- **MUST NOT**: prohibited.
- **SHOULD**: expected unless a documented exception exists.
- **SHOULD NOT**: normally prohibited.
- **MAY**: optional.
- **AUTOMATION**: non-interactive execution initiated by a CI system, scheduler, script, or release controller.
- **PIPELINE**: one automation execution associated with a source state and trigger.
- **WORKFLOW**: declared automation definition containing jobs or stages.
- **JOB**: execution unit running on one environment.
- **STEP**: ordered operation inside a job.
- **RUNNER**: machine or isolated environment executing a job.
- **TRUSTED CHANGE**: source change whose author and execution context are authorized to access protected resources.
- **UNTRUSTED CHANGE**: source change, fork, patch, scenario, or input that must not receive secrets or privileged execution.
- **VALIDATION JOB**: job that invokes GF Wordbench.
- **GATE JOB**: job that decides pass/fail from structured evidence and recorded process status.
- **PUBLISH JOB**: job that distributes already validated release artifacts.
- **PROMOTION**: movement of the exact validated artifact into a release destination.
- **PROVENANCE**: source revision, toolchain identity, runner identity, and configuration associated with evidence.
- **CACHE**: reusable performance data that is never proof of validation success.
- **CI ARTIFACT**: bundle uploaded by the CI provider for inspection or transfer.
- **RELEASE ARTIFACT**: project artifact approved for release, such as a `.pgf`.
- **PUBLIC INTERFACE**: supported CLI or explicitly documented application API.
- **STRUCTURED SOURCE OF TRUTH**: `summary.json` and, for artifact integrity, `manifest.json`.

---

# 6. Automation principles

## 6.1 Public-interface rule

Automation must invoke GF Wordbench through:

```text
supported installed CLI entrypoint
```

or:

```text
python -m app.main_cli
```

during a documented source-tree development transition.

Automation must not import private helpers to assemble a custom pipeline.

## 6.2 One core path

Local CLI, CI, and release automation must reach the same:

```text
bootstrap
→ audit core
→ validation stages
→ result construction
→ reports
```

CI must not create an alternate compiler, scanner, scenario runner, classifier, or report writer.

## 6.3 Structured-decision rule

CI gate decisions must use:

1. process exit category;
2. `summary.json`;
3. `manifest.json` when artifact verification applies.

CI must not decide release status by parsing:

- `summary.md`;
- `AI_READY.md`;
- console prose;
- `top_errors.txt`;
- arbitrary log substrings.

## 6.4 Evidence-first rule

A failing validation job must still preserve available evidence.

Artifact upload and final gate evaluation must be designed so validation failure does not prevent evidence collection.

## 6.5 No mutation rule

Normal CI validation must not modify:

- GF source files;
- `project/project.toml`;
- `.gfs` scenarios;
- scenario inputs;
- `.gold` files;
- project documentation;
- previous run evidence;
- release tags.

## 6.6 Reproducibility rule

Every release-significant run must identify:

- source revision or immutable snapshot;
- GF Wordbench version;
- Python version;
- GF executable identity and version;
- RGL identity;
- project ID;
- project configuration version;
- canonical validation mode;
- runner operating system;
- run ID;
- output artifact identities.

## 6.7 No hidden CI semantics

CI configuration must not silently change:

- source selection;
- required scenarios;
- release requirements;
- timeout policy;
- gold comparison;
- artifact names;
- normalization profile;
- failure classification.

Overrides must be explicit and recorded in resolved run evidence.

---

# 7. Supported automation workflows

GF Wordbench defines four automation workflow families.

```text
pull-request
integration-checkpoint
scheduled-diagnostic
release
```

These workflow families map to canonical validation modes.

They are not additional GF Wordbench modes.

---

# 8. Pull-request workflow

## 8.1 Purpose

Provide bounded feedback before integration.

## 8.2 Default validation mode

Use:

```text
quick
```

or:

```text
checkpoint
```

when the changed area maps safely to a declared checkpoint.

## 8.3 Required jobs

A balanced pull-request workflow should include:

```text
repository checks
unit tests
contract and schema checks
project configuration check
bounded GF validation
structured result verification
artifact upload
final gate
```

## 8.4 Required behavior

```text
[ ] Source revision is checked out immutably for the job.
[ ] Python dependencies are installed from the approved lock or constraints.
[ ] Tests not requiring GF run first.
[ ] Project configuration is validated before GF execution.
[ ] GF validation is bounded.
[ ] Validation evidence is uploaded on success and failure.
[ ] The final status is derived from exit category and structured summary.
```

## 8.5 Changed-file optimization

Changed-file optimization may select a `quick` target or checkpoint only when:

- mapping is deterministic;
- mapping is owned by project configuration or documented automation policy;
- dependency impact is understood;
- required contract changes trigger relevant broader checks;
- fallback is a broader checkpoint, not silent omission.

A changed-file filter must not skip release-significant validation merely because:

- only documentation changed;
- only a gold file changed;
- only project configuration changed;
- only a contract lock changed;
- only a scenario changed;
- only normalization code changed.

Those files can change validation meaning and require targeted contract checks.

## 8.6 Untrusted pull requests

Untrusted changes must run under the security policy in Section 32.

A fork-origin pull request must not receive protected secrets.

Executing project `.gfs` scenarios from untrusted changes requires an approved sandbox and explicit policy.

---

# 9. Integration-checkpoint workflow

## 9.1 Purpose

Validate integrated work on the protected development or main branch.

## 9.2 Default validation mode

Use:

```text
checkpoint
```

## 9.3 Trigger examples

- push to protected integration branch;
- merge queue;
- approved manual dispatch;
- completion of a significant module layer.

## 9.4 Required scope

The workflow should validate:

- framework tests;
- project contracts;
- every checkpoint affected by the change;
- declared checkpoint scenarios;
- checkpoint gold comparisons;
- relevant downstream entrypoint compilation;
- regression comparison when a compatible baseline exists.

## 9.5 Required artifact retention

Retain:

```text
summary.json
summary.md
AI_READY.md
manifest.json
top_errors.txt
raw compile evidence
raw scenario evidence
normalized scenario outputs
gold diffs
```

The exact retention period is owned by operations policy.

---

# 10. Scheduled-diagnostic workflow

## 10.1 Purpose

Detect drift, environment changes, compatibility changes, and broad failures not exercised by bounded pull-request checks.

## 10.2 Default validation mode

Use:

```text
diagnostic
```

## 10.3 Typical trigger

A scheduled job may run:

- nightly;
- weekly;
- after GF or RGL updates;
- after runner-image changes;
- after dependency updates.

Frequency should match project change rate and resource cost.

## 10.4 Recommended scope

```text
full project configuration preflight
broad source inventory
full static scan
configured diagnostic compile set
required and optional diagnostic scenarios
normalization checks
gold comparison where stable
regression comparison
contract checks
schema checks
artifact verification
```

## 10.5 Notification policy

A scheduled failure should create a visible CI failure or tracked issue according to repository policy.

Automation must avoid creating duplicate notification noise for the same unchanged failure.

Notification deduplication must not hide new evidence or a changed failure state.

## 10.6 Scheduled run is not release approval

A passing diagnostic workflow does not replace a clean `release` run.

---

# 11. Release workflow

## 11.1 Purpose

Produce the authoritative evidence and artifacts for one release decision.

## 11.2 Required validation mode

Use:

```text
release
```

No legacy alias is permitted in canonical release evidence.

## 11.3 Trusted context

Release validation must run in a trusted context:

- protected branch, tag, or immutable revision;
- approved runner;
- approved toolchain;
- no unreviewed source mutation;
- no untrusted secrets exposure;
- explicit release authorization where policy requires it.

## 11.4 Required phases

```text
1. Resolve immutable source revision
2. Prepare clean runner workspace
3. Install pinned dependencies
4. Resolve and verify GF and RGL
5. Run repository, contract, and schema checks
6. Run GF Wordbench release validation
7. Verify summary.json
8. Verify manifest.json
9. Archive complete release evidence
10. Promote exact validated release artifacts
11. Record release sign-off
```

## 11.5 No rebuild during publication

The publish job must not rebuild the release PGF or other release artifact.

It must promote the exact bytes validated by the release job.

If publication requires format conversion, signing, or packaging:

- the operation must be documented;
- the original validated artifact must be retained;
- derived artifact identity must be recorded;
- the conversion must not alter the validated semantic artifact unnoticed.

## 11.6 Release gate

Release promotion is allowed only when:

- validation command exit category indicates success;
- `summary.json` is valid;
- overall status is `OK`;
- canonical mode is `release`;
- required stages are complete;
- required scenarios pass;
- required artifacts exist;
- `manifest.json` verifies;
- no blocking issue or expired exception remains;
- sign-off requirements are satisfied.

---

# 12. Workflow selection table

| Trigger | Workflow family | Canonical mode | Typical purpose |
|---|---|---|---|
| Pull request | `pull-request` | `quick` or `checkpoint` | Fast review feedback |
| Merge queue | `integration-checkpoint` | `checkpoint` | Protect integration |
| Protected-branch push | `integration-checkpoint` | `checkpoint` | Validate merged state |
| Schedule | `scheduled-diagnostic` | `diagnostic` | Detect broad drift |
| Manual investigation | `scheduled-diagnostic` | `diagnostic` | Collect deep evidence |
| Release candidate | `release` | `release` | Full release gate |
| Protected tag | `release` | `release` | Validate and promote release |

---

# 13. Job architecture

A provider-neutral pipeline should use the following logical jobs.

```text
source-and-policy
python-quality
unit-tests
contract-tests
gf-preflight
gf-validation
result-verification
artifact-archive
release-promotion
```

Not every workflow needs every job.

Logical separation may be implemented as separate jobs or explicit steps when the runner is simple.

---

# 14. Source-and-policy job

## 14.1 Responsibilities

- resolve source revision;
- classify trigger and trust level;
- determine workflow family;
- identify project configuration;
- validate whether protected resources are allowed;
- expose stable metadata to later jobs.

## 14.2 Required provenance

Record through CI metadata or run evidence:

```text
repository identity
source revision
branch or tag
trigger type
trusted or untrusted classification
workflow identity
attempt number
runner OS
```

Do not add a new persisted GF Wordbench file solely for CI metadata unless the persisted-schema lock defines it.

## 14.3 Checkout rules

- checkout exact revision;
- avoid floating branch content after job start;
- include required submodules only when approved;
- pin submodule revisions;
- avoid credentials persisting into later untrusted steps;
- ensure line-ending conversion does not modify reviewed source semantics.

---

# 15. Python-quality job

## 15.1 Required minimum

The minimum language-neutral quality checks are:

```text
Python bytecode compilation
test discovery
unit test execution
```

## 15.2 Optional configured checks

When part of the project toolchain:

```text
formatter check
lint
static typing
dependency consistency
package build
documentation-link check
```

## 15.3 No invented tool requirement

A quality tool becomes mandatory only when:

- project configuration or development documentation declares it;
- its version is pinned or constrained;
- its CI behavior is tested;
- failure semantics are understood.

CI must not introduce a tool only because the provider offers it conveniently.

## 15.4 GF independence

Pure unit tests should remain runnable without a GF installation when practical.

Real-GF integration tests must be marked or selected separately.

---

# 16. Contract and schema checks

## 16.1 Required domains

Automation should verify:

```text
Python interfile contracts
external-tool contracts
persisted schemas
active-project contracts
project structure
scenario registration
gold registration
artifact ownership
documentation existence
```

## 16.2 Target command concepts

The final CLI may expose command concepts equivalent to:

```text
contracts check
schemas check
project contracts check
project completion check
scenarios check
```

Exact syntax belongs to `CLI_REFERENCE.md`.

CI must not implement independent partial versions of these checks once supported commands exist.

## 16.3 Strict mode

Protected integration and release workflows should use strict contract checking when available.

Pull-request workflows may use strict mode unless cost is excessive.

## 16.4 Drift failures

Contract or schema drift is a CI failure even when GF source compilation still succeeds.

---

# 17. GF preflight job

## 17.1 Purpose

Prove that the required GF environment can be used before expensive validation begins.

## 17.2 Required checks

```text
GF executable resolves
GF executable exists
GF executable launches
GF version probe completes
GF version is supported
RGL root resolves
required GF path parts exist
working directory is valid
output root is writable
UTF-8 policy is available
```

## 17.3 Evidence

Preflight evidence should include:

- resolved executable path or stable identity;
- GF version output;
- RGL identity;
- relevant environment overrides;
- preflight stdout and stderr;
- preflight status.

## 17.4 No `PATH` ambiguity

Using `gf` from `PATH` is permitted only when the resolved executable is recorded.

A release workflow should prefer an explicit executable identity.

## 17.5 Failure behavior

GF preflight failure prevents GF validation but does not prevent:

- Python tests;
- contract checks;
- evidence upload;
- clear final CI failure.

---

# 18. GF validation job

## 18.1 Invocation

Automation invokes the public CLI with:

- canonical mode;
- project root;
- GF executable or resolvable environment configuration;
- RGL root;
- output root;
- documented mode-specific target where applicable;
- finite timeout settings;
- regression option where policy requires it.

## 18.2 Exact command ownership

This document uses:

```text
<GF_WORDBENCH_CLI>
```

as a placeholder for the canonical command defined in `CLI_REFERENCE.md`.

Conceptual invocation:

```text
<GF_WORDBENCH_CLI> run --mode <quick|checkpoint|release|diagnostic> <documented options>
```

CI files must use the actual documented command, not retain this placeholder.

## 18.3 Non-interactive behavior

The CI command must:

- never prompt for file selection;
- never open the GUI;
- never wait for a keypress;
- never pause on error;
- never rely on a launcher shortcut;
- never require a user profile;
- emit a process exit code;
- write structured results.

## 18.4 UTF-8

CI should enable the documented UTF-8 Python and process policy.

On Windows, the invocation must avoid locale-dependent decoding where the implementation supports explicit UTF-8 mode.

## 18.5 Output directory

Each validation job must use a unique output root or run directory context.

Parallel jobs must never write to the same run directory.

## 18.6 Result capture pattern

The validation step should:

1. execute GF Wordbench;
2. capture the process exit code;
3. preserve the run directory path;
4. continue to result verification and artifact upload;
5. fail the final gate after evidence is archived.

A CI provider’s temporary `continue-on-error` mechanism may be used only to preserve evidence.

It must not mark the final workflow successful.

---

# 19. Exit-code contract

## 19.1 Minimum invariant

```text
exit 0
```

means the requested command completed and its required criteria passed.

Any non-zero exit means the command must not be treated as successful.

## 19.2 Exact values

Exact numeric categories are owned by:

```text
docs/reference/EXIT_CODES.md
```

The final system should distinguish at least:

```text
validation failure
invalid invocation or configuration
runtime or framework error
contract or schema failure when separately exposed
```

## 19.3 Exit and summary consistency

When `summary.json` exists:

- exit success requires overall status `OK`;
- overall `FAIL` must not produce exit success;
- overall `ERROR` must not produce exit success;
- release-mode mismatch must fail release;
- contradictory exit and summary values indicate a contract error.

## 19.4 Missing summary

A non-zero command with no summary may still be a valid:

- argument failure;
- configuration failure;
- launch failure before run initialization;
- internal runtime error.

CI must preserve available bootstrap stderr and fail clearly.

An exit `0` without the required summary is a contract failure.

## 19.5 Transitional predecessor behavior

The predecessor CLI currently distinguishes:

```text
0 success
1 audit failures
2 invalid arguments
3 runtime error
```

Its current success calculation is based on file `fail_count`.

That behavior is transitional.

The final CI gate must use final overall status, including:

- file failures;
- file errors;
- scenario failures;
- scenario errors;
- required skipped work;
- artifact failures;
- report and manifest requirements.

---

# 20. `summary.json` verification

## 20.1 Required checks

The result-verification job must verify:

```text
file exists
valid UTF-8 JSON
recognized schema_id
supported schema_version
recognized producer
expected project identity
expected source/run identity when represented
expected canonical mode
recognized overall status
required totals present
required result arrays present
required artifact paths present
```

## 20.2 Release checks

For release:

```text
mode == release
overall_status == OK
required stage completion == true
required scenario failures == 0
required artifact failures == 0
required skipped work == 0
```

Exact fields are governed by the persisted schema.

## 20.3 No Markdown fallback

If `summary.json` is missing or invalid, CI must not reconstruct success from `summary.md`.

## 20.4 Legacy schema

Legacy summary loading may be used in migration and regression comparison.

A final release run must emit the canonical current schema.

---

# 21. `manifest.json` verification

## 21.1 Applicability

Manifest verification is required for:

- release workflows;
- artifact-promotion workflows;
- any workflow claiming artifact integrity.

## 21.2 Required checks

```text
manifest exists
schema is supported
run identity matches summary
project identity matches summary
required roles are present
paths resolve within authorized roots
sizes match
required hashes match
missing required artifact count is zero
manifest does not list itself as a hashed artifact
```

## 21.3 Timing

The manifest must be finalized after all manifest-owned artifacts are stable.

CI must not modify a hashed artifact after verification.

## 21.4 Upload packaging

A CI provider may package files into an archive after manifest verification.

The archive is a transport container.

It must not replace the internal artifact manifest.

---

# 22. CI artifact policy

## 22.1 Always-retained core evidence

Upload on success and failure when produced:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
master log
preflight output
```

## 22.2 Failure evidence

On failure, also retain:

```text
per-file compile stdout
per-file compile stderr
scan logs
scenario stdout
scenario stderr
normalized scenario output
gold diffs
artifact verification details
bootstrap stderr
```

## 22.3 Release evidence

A release workflow retains the complete release evidence bundle defined by project and release policy.

## 22.4 Artifact naming

CI bundle names should include stable context such as:

```text
project ID
workflow family
source revision abbreviation
run ID
attempt number
```

CI bundle naming does not change internal run-relative artifact paths.

## 22.5 Sensitive evidence

Before upload, enforce the reporting and redaction policy.

CI artifacts must not contain:

- secrets;
- private keys;
- tokens;
- complete environment dumps;
- unrelated credentials;
- unauthorized proprietary source excerpts.

## 22.6 Artifact upload failure

Failure to upload mandatory release evidence is a release error.

For a non-release pull request, upload failure should fail the workflow when evidence is required to review a validation failure.

---

# 23. Retention policy

## 23.1 Categories

Recommended retention categories:

```text
pull-request evidence
integration evidence
scheduled diagnostic evidence
release-candidate evidence
released evidence
```

## 23.2 Policy ownership

Exact durations belong to:

```text
docs/operations/CLEANUP_BACKUP_AND_RECOVERY.md
```

and repository governance.

## 23.3 Minimum behavior

- failed pull-request evidence should outlive normal review;
- integration evidence should support regression investigation;
- scheduled evidence should permit trend comparison;
- release-candidate evidence should survive until release decision;
- released evidence should follow durable archival policy.

## 23.4 Provider expiration

CI-provider artifact expiration must not be the only retention mechanism for required released evidence.

---

# 24. Toolchain pinning

## 24.1 Python

Release and protected integration workflows should pin or constrain:

- Python major and minor version;
- package installer;
- dependency lock or constraints;
- build backend;
- required quality tools.

## 24.2 GF

Release workflows must identify and verify:

- GF executable distribution;
- GF version;
- executable hash when policy requires it;
- supported command capabilities.

## 24.3 RGL

Release workflows must identify:

- RGL version, release, or immutable source revision;
- expected root;
- compatibility with selected GF version.

## 24.4 CI actions and reusable components

Provider actions, plugins, container images, and reusable workflows should be pinned to immutable identities for protected and release workflows.

A floating major tag is not an immutable identity.

## 24.5 Update policy

Toolchain updates must run compatibility validation before becoming the release default.

---

# 25. Dependency installation

## 25.1 Reproducible install

CI should install from:

```text
lock file
```

or:

```text
documented constraints with verified resolver behavior
```

## 25.2 No hidden global dependencies

A job must not depend on undeclared packages already installed on a runner.

## 25.3 Offline or mirrored operation

Organizations may use an internal package mirror.

Mirror use must preserve package identity and integrity.

## 25.4 Release installation

Release dependencies should be installed into a clean environment.

Editable installs are acceptable for source-tree testing only when documented and equivalent behavior is tested.

---

# 26. Cache policy

## 26.1 Purpose

Caches improve speed.

They are not validation evidence.

## 26.2 Safe cache candidates

Examples:

```text
Python download cache
package-manager cache
verified immutable GF distribution
verified immutable RGL checkout
tool download cache
```

## 26.3 Unsafe proof sources

The following must not be restored and accepted as proof of current release success:

```text
old run directory
summary.json from another run
manifest.json from another run
cached `.gfo`
cached `.pgf`
cached normalized scenario output
cached gold diff
cached validation status
```

## 26.4 Generated artifact cache

Generated GF artifacts may be used for explicitly documented developer acceleration only when cache invalidation is proven.

Release validation must build required artifacts from the current source state or use a verified build system whose provenance is equivalent and documented.

## 26.5 Cache key

A cache key should include all relevant identity dimensions:

```text
runner OS
architecture
Python version
dependency lock hash
GF version or distribution hash
RGL revision
GF Wordbench version
project configuration hash where relevant
```

## 26.6 Cache miss

A cache miss must reduce performance only.

It must not change validation semantics.

## 26.7 Cache poisoning

Untrusted workflows must not write to protected caches consumed by trusted release workflows unless the CI provider guarantees isolation and policy explicitly permits it.

---

# 27. Workspace policy

## 27.1 Clean workspace

Release jobs require a clean workspace.

## 27.2 Source and output separation

Recommended layout:

```text
<workspace>/source/
<workspace>/toolchain/
<workspace>/runs/
<workspace>/package/
```

Exact paths are provider-specific.

## 27.3 No cross-job writable sharing

Jobs must not share a writable run directory concurrently.

Transfer between jobs should use immutable CI artifacts or approved read-only storage.

## 27.4 Cleanup

Cleanup must not delete evidence before upload.

Cleanup failure must not overwrite the validation result, but may fail release if workspace integrity is uncertain.

---

# 28. Environment configuration

## 28.1 Machine-local values

CI supplies machine-local facts such as:

```text
GF executable
RGL root
output root
temporary directory
optional tool paths
```

These values must not be written into `project/project.toml`.

## 28.2 Project-owned values

The project supplies:

```text
project identity
source root
source selection
entrypoints
checkpoints
scenarios
gold mappings
release requirements
```

CI must not duplicate these values unless a documented override is required.

## 28.3 Environment-variable names

CI-provider or repository variable names are not automatically GF Wordbench public API.

Exact supported environment variables must be documented in:

```text
docs/configuration/ENVIRONMENT_AND_PATHS.md
```

## 28.4 Environment evidence

Record relevant overrides without dumping the complete environment.

Secret values must be redacted.

---

# 29. Windows runners

## 29.1 Supported invocation

Windows CI should use:

```text
PowerShell
```

or direct process invocation by the CI provider.

Interactive `.bat` launchers that pause on error are not CI interfaces.

## 29.2 Path handling

- pass paths as distinct arguments;
- quote through the process API, not by concatenating a command string;
- use resolved absolute environment paths where required;
- preserve project-relative paths in project configuration and reports;
- avoid relying on the current drive or shortcut directory;
- account for path-length policy.

## 29.3 Encoding

Enable the documented UTF-8 policy for Python and captured GF output.

## 29.4 Exit capture

PowerShell automation must capture the native process exit code through the supported mechanism and preserve it until the final gate.

## 29.5 Launcher transition

A local Windows launcher may delegate to the CLI.

CI should invoke the CLI directly.

Launcher-specific behavior must not be required for correct validation.

---

# 30. Unix-like runners

Unix-like runners may be supported only when:

- GF Wordbench declares the platform supported;
- the intended GF distribution exists;
- path and process tests pass;
- project behavior is compatible;
- release policy identifies whether the platform is authoritative or compatibility-only.

Automation must not assume Windows-only paths on Unix-like runners or vice versa.

---

# 31. Container policy

## 31.1 Optional use

Containers may improve reproducibility but are not required by the architecture.

## 31.2 Requirements

A release container must identify:

- base image identity;
- Python version;
- GF distribution;
- RGL revision;
- installed dependencies;
- locale and encoding;
- entrypoint behavior.

## 31.3 Immutable identity

Protected workflows should pin container images by immutable digest.

## 31.4 Mounted paths

Mounted project and output paths must obey containment and ownership rules.

## 31.5 Nested process behavior

GF timeout and child-process termination must still work inside the container.

## 31.6 No false portability claim

A container that runs on one host does not automatically prove native support on every operating system.

---

# 32. Trust and security model

## 32.1 Trust classification

Every workflow invocation must be classified as:

```text
trusted
untrusted
```

before secrets or privileged runners are available.

## 32.2 Untrusted source

Treat as untrusted:

- fork pull requests;
- externally supplied patches;
- unreviewed `.gfs` scenarios;
- unreviewed scenario inputs;
- unreviewed tool paths;
- user-controlled artifact paths;
- source from unknown branches.

## 32.3 Secrets

Untrusted workflows must receive no protected secrets.

GF Wordbench validation should not require secrets.

## 32.4 Minimal permissions

Default CI permissions should be read-only.

Write permissions are granted only to jobs that need them, such as an approved publish job.

## 32.5 Scenario risk

A `.gfs` file is executable input.

Untrusted scenario execution must be:

- disabled;
- sandboxed;
- or explicitly approved under a documented threat model.

## 32.6 Shell escape

Scenario shell escape or OS-command capability is prohibited in normal CI unless:

- explicitly enabled;
- limited to a trusted workflow;
- reviewed;
- sandboxed;
- recorded in external-tool policy.

## 32.7 Protected runners

Self-hosted or release runners must not execute untrusted fork content with privileged access.

## 32.8 Path containment

CI must reject project, scenario, input, and output paths that escape authorized roots.

## 32.9 Network

Normal validation should not require outbound network access after dependencies and toolchain are provisioned.

Release validation may disable network access during GF execution when practical.

## 32.10 AI artifacts

Generating `AI_READY.md` does not authorize sending it to an external AI service.

CI must not upload it to an AI provider unless separately authorized.

---

# 33. Supply-chain policy

## 33.1 Protected components

Review and pin:

```text
CI actions or plugins
runner image
container image
Python dependencies
GF distribution
RGL revision
optional external tools
release packaging tools
```

## 33.2 Integrity verification

Use available checksums, signatures, or immutable source revisions according to project policy.

## 33.3 Dependency updates

Automated dependency-update pull requests are untrusted until reviewed.

They must pass the appropriate compatibility workflow.

## 33.4 No automatic promotion

A dependency update must not automatically become the release toolchain merely because its pull request passed unit tests.

GF and RGL updates require real-GF compatibility validation.

---

# 34. Timeouts

## 34.1 Layered timeouts

Automation should define:

```text
per-process timeout
per-stage timeout where supported
job timeout
workflow timeout
```

## 34.2 Relationship

The job timeout must allow GF Wordbench to:

- terminate owned processes;
- write final structured results;
- write reports;
- upload evidence.

The provider must not normally kill the job before GF Wordbench’s own timeout policy can act.

## 34.3 Timeout result

A timeout is not a syntax failure.

It must remain visible as execution state and produce a non-successful gate.

## 34.4 Release timeout

A release timeout cannot be waived by rerunning only the publish job.

A new release validation run is required.

---

# 35. Concurrency

## 35.1 Default

Sequential GF validation is acceptable and preferred until safe concurrency provides measured benefit.

## 35.2 Parallel jobs

Independent jobs may run in parallel when:

- they use separate output roots;
- no artifact path collides;
- shared caches are read-safe;
- source revision is identical;
- result combination is deterministic.

## 35.3 Matrix jobs

Compatibility matrices must identify one primary release environment and any secondary compatibility environments.

A matrix must not create ambiguity about which artifact is released.

## 35.4 In-process concurrency

Parallel file or scenario execution inside GF Wordbench requires:

- deterministic result order;
- isolated artifact paths;
- safe GF behavior;
- controlled cancellation;
- attributable logs;
- contract-test proof.

CI must not externally parallelize individual GF Wordbench-owned stages in a way that bypasses the audit core.

---

# 36. Cancellation

## 36.1 Pull-request supersession

Older pull-request workflows may be cancelled when a newer revision supersedes them.

## 36.2 Release protection

A release validation job should not be automatically cancelled by unrelated branch activity.

## 36.3 Evidence

Cancellation should preserve partial evidence when possible.

## 36.4 Status

Cancellation must not be reported as:

```text
OK
```

or as a GF syntax/type failure.

## 36.5 Promotion

A cancelled release validation cannot feed a publish job.

---

# 37. Retry policy

## 37.1 New run identity

Every retry is a new automation attempt and a new GF Wordbench run.

It must not overwrite earlier evidence.

## 37.2 No pass-by-retry

A later success does not erase the earlier failure.

The workflow may use the latest attempt as the current gate, but investigation records should retain the prior failure where policy requires it.

## 37.3 Flaky classification

A failure may be called flaky only after evidence identifies nondeterminism or environmental instability.

Repeated reruns alone are not proof.

## 37.4 Release retry

A release retry must repeat the complete required release validation, not only the failed stage, unless the release process explicitly supports equivalent immutable stage promotion.

---

# 38. Failure-containment pattern

A robust validation job uses this logical sequence:

```text
run validation and capture exit
locate run directory
verify available structured output
upload available evidence
evaluate summary/manifest consistency
apply final CI failure
```

The validation step must not terminate the job before mandatory evidence upload.

The final gate must preserve the original validation failure category when possible.

---

# 39. Result-verification failure classes

CI should distinguish:

| Class | Example |
|---|---|
| Validation failure | Required GF module, scenario, assertion, or gold criterion failed |
| Invocation failure | Invalid CLI argument or missing required configuration |
| Toolchain failure | GF unavailable or unsupported |
| Runtime failure | GF Wordbench internal or filesystem error |
| Contract failure | Exit and summary disagree |
| Schema failure | `summary.json` or `manifest.json` is invalid |
| Artifact failure | Required evidence or release artifact is missing |
| Infrastructure failure | Runner, checkout, provider, or upload failed |
| Security failure | Trust, path, permission, or secret policy violated |

CI reporting should retain these distinctions.

---

# 40. Status presentation

The CI job summary should show:

```text
project ID
source revision
workflow family
canonical mode
GF Wordbench version
GF version
RGL identity
run ID
overall status
direct failure count
downstream failure count
ambiguous failure count
scenario failure count
artifact failure count
summary path
AI-ready path
manifest path
```

This presentation is convenience output.

It must derive from structured results and must not become the source of truth.

---

# 41. Pull-request annotations

CI may publish bounded annotations for:

- configuration failures;
- first direct compile errors;
- contract failures;
- scenario assertion failures;
- gold mismatches;
- missing artifacts.

Annotations must:

- preserve file and line attribution when reliable;
- avoid presenting downstream errors as root causes;
- avoid flooding;
- link to full evidence;
- escape untrusted output;
- disclose when location is ambiguous.

Annotations are optional derived presentation.

They must not alter run status independently.

---

# 42. Branch and tag policy integration

## 42.1 Protected branches

Protected branches should require the appropriate GF Wordbench gate.

## 42.2 Merge queues

Merge-queue validation should run against the actual queued merge revision, not only the pull-request head.

## 42.3 Tags

Release tags should identify an immutable source revision.

## 42.4 Moving tags

Release automation must reject or explicitly review moved tags.

## 42.5 Branch name

Branch names are metadata.

They must not select a different active language project.

---

# 43. Release promotion

## 43.1 Inputs

A publish job consumes:

```text
validated release evidence bundle
validated release artifact
validated manifest
release metadata
approval state
```

## 43.2 Verification before promotion

Reverify:

- source revision;
- run ID;
- manifest hash entries;
- release artifact hash;
- overall status;
- mode;
- approval state.

## 43.3 Immutable promotion

Promote exact validated bytes.

## 43.4 Publish failure

Publication failure does not invalidate the prior validation result.

It does mean the release is not fully published.

Retry may reuse the same validated immutable artifact if:

- evidence remains intact;
- release policy permits it;
- no source or metadata affecting the artifact changed.

## 43.5 No source mutation

Publish jobs must not commit generated changes back to the source branch unless a separate, explicitly authorized workflow owns that behavior.

---

# 44. Gold-update automation

## 44.1 Normal CI

Normal CI must never update gold.

## 44.2 Proposed gold workflow

A dedicated maintenance workflow may generate proposed normalized output or a patch for review.

It must:

- require explicit manual invocation;
- run in a trusted context;
- preserve old and new raw evidence;
- never merge automatically;
- show diffs;
- require project review;
- update validation specification when semantics changed;
- rerun release-relevant validation after approval.

## 44.3 Release restriction

A release workflow must fail on gold mismatch.

It must not repair the mismatch.

---

# 45. Documentation-only changes

Documentation-only optimization is permitted only after classifying the changed documents.

## 45.1 Always relevant normative documents

Changes to these normally require contract or schema tests:

```text
contract locks
validation specifications
configuration references
scenario references
report references
release criteria
project completion checklist
```

## 45.2 Prose-only changes

A verified prose-only change may skip real GF execution when:

- no path, identifier, command, schema, contract, scenario, gold, or release criterion changed;
- documentation link and existence checks still run;
- repository policy permits the optimization.

## 45.3 Conservative fallback

When classification is uncertain, run the broader check.

---

# 46. Compatibility matrices

## 46.1 Purpose

A matrix may test supported combinations of:

```text
operating system
Python version
GF version
RGL version
```

## 46.2 Scope control

Do not test arbitrary Cartesian products.

Use combinations defined by compatibility policy.

## 46.3 Authoritative release environment

One combination must be identified as the release-producing environment.

Other combinations are compatibility evidence unless release policy says otherwise.

## 46.4 Matrix artifacts

Each matrix job uses a unique run and artifact bundle.

Results must not be merged by copying human reports together.

A coordinating job may aggregate structured statuses.

## 46.5 Partial matrix failure

Compatibility failure must remain visible.

Whether it blocks release is defined by supported-platform policy.

---

# 47. Provider-neutral workflow skeleton

The following is conceptual.

It does not define exact provider syntax.

```text
workflow: pull-request

job source-and-policy:
  checkout exact revision
  determine trust
  record provenance

job python-quality:
  install pinned Python dependencies
  compile Python
  run configured lint/type checks

job unit-tests:
  run tests not requiring GF

job contract-tests:
  run schema and contract checks

job gf-validation:
  depends on required earlier jobs
  provision approved GF and RGL
  run GF preflight
  invoke <GF_WORDBENCH_CLI> in quick/checkpoint mode
  save exit category and run path

job result-verification:
  run even when validation failed
  validate summary.json when present
  validate manifest when present
  create bounded job summary

job artifact-archive:
  run even when validation failed
  upload available run evidence

job final-gate:
  fail according to saved exit and structured verification
```

---

# 48. GitHub Actions adaptation example

This section is illustrative and non-normative regarding exact action identifiers.

Provider actions must be pinned according to supply-chain policy.

```yaml
name: GF Wordbench Check

on:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  validate:
    runs-on: <SUPPORTED_RUNNER>
    timeout-minutes: <JOB_TIMEOUT>

    steps:
      - name: Checkout
        uses: <CHECKOUT_ACTION>@<IMMUTABLE_ID>

      - name: Set up Python
        uses: <PYTHON_SETUP_ACTION>@<IMMUTABLE_ID>
        with:
          python-version: "<PINNED_PYTHON>"

      - name: Install dependencies
        shell: pwsh
        run: |
          <INSTALL_COMMAND_FROM_LOCK>

      - name: Run unit and contract tests
        shell: pwsh
        run: |
          <TEST_COMMANDS>

      - name: Provision GF and RGL
        shell: pwsh
        run: |
          <VERIFIED_PROVISIONING_COMMANDS>

      - name: Run GF Wordbench
        id: wordbench
        shell: pwsh
        continue-on-error: true
        run: |
          <INVOKE_DOCUMENTED_CLI_AND_SAVE_EXIT_AND_RUN_PATH>

      - name: Verify structured results
        if: always()
        shell: pwsh
        run: |
          <VERIFY_SUMMARY_AND_MANIFEST>

      - name: Upload evidence
        if: always()
        uses: <ARTIFACT_UPLOAD_ACTION>@<IMMUTABLE_ID>
        with:
          name: <STABLE_BUNDLE_NAME>
          path: <RESOLVED_RUN_DIRECTORY>

      - name: Apply final gate
        if: always()
        shell: pwsh
        run: |
          <FAIL_FROM_SAVED_VALIDATION_AND_VERIFICATION_STATUS>
```

`continue-on-error` in this pattern is temporary control flow.

The final gate must still fail the job.

---

# 49. PowerShell invocation pattern

This pattern is conceptual and must be replaced with the documented CLI syntax.

```powershell
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"

$runStatusFile = Join-Path $env:CI_TEMP "gf-wordbench-exit.txt"
$runPathFile = Join-Path $env:CI_TEMP "gf-wordbench-run-path.txt"

$arguments = @(
    "run",
    "--mode", "checkpoint",
    "--project-root", $env:CI_PROJECT_ROOT,
    "--gf-exe", $env:CI_GF_EXE,
    "--rgl-root", $env:CI_RGL_ROOT,
    "--out-root", $env:CI_OUTPUT_ROOT
)

& $env:CI_GF_WORDBENCH_CLI @arguments
$exitCode = $LASTEXITCODE

Set-Content -LiteralPath $runStatusFile -Value $exitCode -Encoding utf8

# Resolve the run path through documented CLI output or an explicit output contract.
# Do not guess the newest directory when concurrent runs may exist.

exit 0
```

The capture step exits successfully only so evidence steps can continue.

A later gate exits with the saved non-zero result when appropriate.

CI variable names shown above are workflow-local examples, not GF Wordbench public environment-variable names.

---

# 50. Run-directory discovery

## 50.1 Preferred mechanism

The CLI should expose the created run directory through a stable machine-consumable mechanism defined in `CLI_REFERENCE.md`.

Possible mechanisms include:

- explicit requested run output path;
- structured console record;
- provider output written by a wrapper;
- canonical result pointer.

## 50.2 Forbidden heuristic

CI must not select:

```text
the newest run_* directory
```

when concurrent or previous runs can exist.

## 50.3 Unique output root

Until a dedicated machine output exists, CI should provide a unique job-specific output root and require exactly one run directory beneath it.

This transitional rule must be tested.

---

# 51. Current implementation transition

## 51.1 Existing interface

The predecessor implementation currently provides:

```text
console entrypoint: gf-audit-cli
module entrypoint: python -m app.main_cli
modes: all, file
required environment arguments:
  --project-root
  --rgl-root
  --gf-exe
  --out-root
```

It also exposes:

```text
--scan-dir
--scan-glob
--gf-path
--timeout-sec
--max-files
--target-file
--include-regex
--exclude-regex
--skip-version-probe
--no-compile
--emit-cpu-stats
--keep-ok-details
--diff-previous
```

## 51.2 Existing exit behavior

The current CLI uses:

```text
0 = success
1 = audit failures
2 = invalid arguments
3 = runtime error
```

## 51.3 Existing launcher behavior

The current Windows CLI launcher can delegate through:

- an explicit Python environment variable;
- a local virtual environment;
- `uv`;
- the Python launcher;
- `python` on `PATH`.

It may pause interactively on errors.

CI must not use the interactive pause behavior.

## 51.4 Mode migration

During migration:

```text
file → quick
all  → diagnostic
```

Checkpoint and release workflows must not pretend that legacy `all` proves the new final release contract.

## 51.5 Package and command rename

The final installed command should use the GF Wordbench product identity defined by `CLI_REFERENCE.md` and package metadata.

Legacy command aliases may remain temporarily with deprecation warnings.

Canonical CI examples and new workflows must use only the final command after it is implemented.

## 51.6 Exit migration

The final CLI exit decision must use overall structured status rather than only file `fail_count`.

## 51.7 Transitional CI

A transitional CI pipeline may run the current interface, but it must state that the resulting evidence covers only implemented predecessor capabilities.

It must not claim scenario, gold, PGF, manifest, or final release gates passed when those capabilities did not execute.

---

# 52. Automation wrappers

## 52.1 Default

Provider configuration may invoke the CLI directly.

## 52.2 Wrapper threshold

A repository wrapper is justified when it centralizes repeated, stable behavior such as:

- UTF-8 setup;
- CLI invocation;
- exit capture;
- run-path capture;
- summary verification;
- artifact-list creation.

## 52.3 Wrapper constraints

A wrapper must not:

- duplicate mode policy;
- duplicate project configuration;
- parse human Markdown;
- build its own GF path inconsistently;
- change requiredness;
- update gold;
- classify failures;
- hide exit codes.

## 52.4 Cross-provider reuse

A small Python verification script may be preferable to duplicating JSON validation in PowerShell, Bash, and provider expressions.

Such a script becomes a supported operations component and requires tests.

---

# 53. Result verification implementation

A verifier should:

```text
accept explicit summary path
accept explicit expected mode
accept explicit expected project ID
load canonical or explicitly allowed schema
validate required invariants
optionally load manifest
emit bounded machine-readable result
return non-zero on inconsistency
```

It should not:

- rerun validation;
- repair JSON;
- infer missing fields from Markdown;
- accept unknown major schema versions;
- modify the run directory.

---

# 54. CI test strategy

Automation itself requires tests.

## 54.1 Unit tests

Test:

```text
trigger-to-workflow mapping
trust classification
mode selection
command argument construction
exit capture
summary verification
manifest verification
artifact selection
redaction
cache key construction
```

## 54.2 Contract tests

Test:

```text
CI uses public CLI
canonical modes only
release mode cannot be downgraded
gold files remain unchanged
artifact upload includes required files
exit and summary consistency
manifest verification before promotion
publish job does not rebuild
untrusted jobs receive no secrets
```

## 54.3 Integration tests

Use a local or provider test environment to verify:

```text
successful quick workflow
failing quick workflow with evidence upload
checkpoint workflow
diagnostic timeout
release success
release failure
missing summary
invalid summary schema
missing manifest artifact
artifact upload failure
cancelled job
retry with new run ID
```

## 54.4 Configuration validation

CI workflow files should be syntax-validated by the provider or an approved local validator.

---

# 55. Release rehearsal

Before relying on release automation:

```text
[ ] Run against a disposable release candidate.
[ ] Verify clean toolchain setup.
[ ] Verify source revision identity.
[ ] Verify release mode.
[ ] Verify complete evidence upload.
[ ] Verify manifest hashes.
[ ] Verify release artifact identity.
[ ] Verify publish job consumes the validated artifact.
[ ] Verify publish failure recovery.
[ ] Verify no gold or source mutation.
[ ] Verify retention.
[ ] Verify protected permissions.
```

A rehearsal artifact must not be confused with a public release artifact.

---

# 56. Infrastructure failures

## 56.1 Examples

- runner unavailable;
- checkout failure;
- network failure during dependency provisioning;
- provider outage;
- artifact service failure;
- disk exhaustion;
- permission failure;
- job killed externally.

## 56.2 Classification

Infrastructure failures are not GF language failures.

## 56.3 Retry

Retry is permitted when source and toolchain identity remain unchanged.

## 56.4 Release behavior

A release cannot be promoted from an incomplete infrastructure run.

---

# 57. Observability

## 57.1 Required job-level facts

Expose:

- step durations;
- validation duration;
- toolchain versions;
- run ID;
- artifact upload status;
- final category.

## 57.2 No sensitive logging

Do not print:

- tokens;
- full secret values;
- complete environment;
- protected credentials;
- private signing material.

## 57.3 Diagnostic verbosity

Diagnostic mode may retain deeper evidence.

Console output should remain bounded and direct reviewers to artifacts.

---

# 58. Notifications

## 58.1 Source of notification

Notifications must derive from final job status and structured result.

## 58.2 Content

A notification should include:

```text
project ID
source revision
workflow family
mode
overall status
primary direct or toolchain failure
run or artifact link
```

## 58.3 No unsupported diagnosis

Notifications must not invent root causes.

## 58.4 No external AI by default

Notifications must not automatically send project evidence to an AI service.

---

# 59. Scheduled maintenance

Automation maintainers should periodically review:

```text
runner images
Python support
GF support
RGL revision
dependency lock
pinned CI component identities
cache policy
retention policy
branch protections
release permissions
artifact storage
timeout values
```

A runner-image change is an environment change and should trigger diagnostic validation.

---

# 60. CI ownership

Every automation responsibility must have one owner.

| Responsibility | Owner |
|---|---|
| Workflow trigger policy | Repository operations policy |
| Canonical mode semantics | GF Wordbench validation policy |
| Project requiredness | `project/project.toml` and project release criteria |
| CLI syntax | `CLI_REFERENCE.md` and CLI implementation |
| Exit codes | `EXIT_CODES.md` and CLI implementation |
| GF process contract | External-tool contract owner |
| Summary schema | Persisted-schema owner |
| Manifest schema | Persisted-schema and manifest owner |
| Artifact upload | CI workflow |
| Release promotion | Release workflow |
| Gold approval | Project maintainer |
| Secrets and permissions | Repository owner |
| Retention | Operations policy |

No CI provider expression may silently become the owner of a GF Wordbench validation rule.

---

# 61. Anti-overengineering constraints

The automation architecture does not require:

- a custom distributed scheduler;
- a message broker;
- a database;
- a remote validation service;
- a generic DAG definition inside GF Wordbench;
- a custom CI plugin;
- a container for every local check;
- one workflow per GF module;
- automatic AI diagnosis;
- dynamic plugin discovery;
- simultaneous active-language profiles;
- rebuilding reports in separate services.

Add infrastructure only when a measured requirement cannot be met by:

- provider jobs;
- the public CLI;
- structured artifacts;
- small tested wrappers.

---

# 62. Drift indicators

Probable automation drift exists when:

- CI invokes a private Python helper;
- CI builds its own source list;
- CI builds a GF path differently from GF Wordbench;
- CI classifies direct/downstream failures independently;
- CI parses `summary.md` for status;
- CI treats console wording as a schema;
- CI treats exit `0` as success when `summary.json` is missing;
- CI ignores overall `ERROR`;
- CI uses legacy `all` as final release proof;
- CI skips required scenarios through an undocumented flag;
- CI updates gold;
- CI reuses cached `.pgf` as current proof;
- CI uploads no evidence on failure;
- CI publishes an artifact rebuilt after validation;
- CI promotes an artifact whose hash differs from the manifest;
- CI secrets are available to untrusted forks;
- CI executes untrusted `.gfs` on a privileged runner;
- CI uses floating toolchain identities for release;
- CI uses an interactive launcher;
- CI discovers the newest run directory heuristically;
- concurrent jobs share an output root;
- report or manifest verification is omitted in release;
- a cancelled release job feeds promotion;
- a retry overwrites earlier evidence;
- a dependency update becomes authoritative without compatibility validation;
- a documentation change alters a contract but skips all contract checks;
- provider action versions drift without review.

Every drift indicator requires either restoration of the established boundary or a coordinated documented change.

---

# 63. Automation review checklist

```text
[ ] Workflow family is identified
[ ] Canonical mode is correct
[ ] Exact source revision is recorded
[ ] Trust level is determined before privileged access
[ ] Permissions are minimal
[ ] Secrets are absent from untrusted jobs
[ ] Python version is pinned or constrained
[ ] Dependencies are installed reproducibly
[ ] GF executable identity is recorded
[ ] GF version is probed
[ ] RGL identity is recorded
[ ] Working directory is explicit
[ ] Output root is unique
[ ] UTF-8 policy is explicit
[ ] Unit tests run
[ ] Contract tests run
[ ] Schema tests run
[ ] Project configuration preflight runs
[ ] GF validation uses public CLI
[ ] No interactive launcher is used
[ ] Per-process timeouts are finite
[ ] Job timeout permits evidence finalization
[ ] Exit code is captured
[ ] Run path is captured without newest-directory guessing
[ ] `summary.json` is verified
[ ] Canonical mode in summary matches expected mode
[ ] Overall status matches exit category
[ ] `manifest.json` is verified when required
[ ] Required artifacts exist
[ ] Evidence uploads run on failure
[ ] Excerpts and reports contain no secrets
[ ] Caches are not used as validation proof
[ ] Protected caches cannot be poisoned by untrusted jobs
[ ] Parallel jobs cannot collide
[ ] Cancellation policy is appropriate
[ ] Retry creates new evidence
[ ] Release job runs from clean state
[ ] Publish job uses exact validated bytes
[ ] Publish job does not rebuild
[ ] Gold files remain unchanged
[ ] Release evidence is retained
[ ] Final gate cannot be bypassed by temporary continue-on-error
[ ] Workflow and wrapper tests pass
[ ] Related operations documentation is current
```

---

# 64. Implementation completion criteria

The automation system is complete when:

```text
[ ] Public non-interactive CLI is final
[ ] Canonical modes are supported
[ ] Exact exit-code contract is documented
[ ] Machine-consumable run-path capture exists
[ ] Summary verifier exists
[ ] Manifest verifier exists
[ ] Pull-request workflow exists
[ ] Integration-checkpoint workflow exists
[ ] Scheduled-diagnostic workflow exists
[ ] Release workflow exists
[ ] Evidence uploads execute on failure
[ ] Trust classification is enforced
[ ] Untrusted workflows receive no secrets
[ ] GF and RGL identities are recorded
[ ] Dependency installation is reproducible
[ ] Cache policy is enforced
[ ] Release artifacts are promoted without rebuild
[ ] Workflow tests cover success and failure
[ ] Transition from legacy CLI is documented
[ ] Release rehearsal passes
```

---

# 65. Final enforcement rule

CI is an orchestrator of GF Wordbench, not a second implementation of GF Wordbench.

The repository, project configuration, validation core, result models, reports, and manifests already own the relevant semantics.

Therefore:

> No automated workflow may claim validation or release success unless it invoked the supported GF Wordbench path, preserved the run evidence, verified the canonical structured result, and—when artifacts are promoted—proved that the published bytes are the same bytes that passed release validation.
