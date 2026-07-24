# Security Policy

**Status:** Normative  
**Applies to:** GF Wordbench, the active project in the current workspace, external-tool execution, persisted evidence and local operations  
**Owner:** GF Wordbench maintainers  
**Last reviewed:** `2026-07-24`  
**Authority:** accepted ADRs, `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` and the specialized contract locks

---

## 1. Purpose

GF Wordbench is a local validation, diagnostics, regression-testing and release-readiness workbench for Grammatical Framework language projects.

It launches external tools, reads language-project files, executes GF scenarios, creates run directories, writes reports, and compares generated output with reviewed expectations. Those operations cross trust boundaries and can affect the local filesystem and process environment.

This policy defines:

- the supported security model;
- what GF Wordbench trusts and does not trust;
- mandatory implementation safeguards;
- secure operating practices;
- vulnerability-reporting procedures;
- incident and release expectations.

This document is normative for GF Wordbench maintainers and contributors.

---

## 2. Security model

GF Wordbench is designed as a local developer tool.

The core workflow:

- reads the one active GF language project configured for the current workspace;
- launches an explicitly resolved GF executable;
- captures stdout, stderr, exit state, duration, and artifacts;
- writes evidence under a controlled run root;
- produces machine-readable and human-readable reports;
- may execute project-owned `.gfs` scenarios.

Each run is scoped to one active project in one workspace. Portfolio-wide aggregation and cross-workspace orchestration belong to the independent `gf-portfolio` product; GF Wordbench has no runtime dependency on it.

GF Wordbench is **not a security sandbox**.

A GF project, scenario, executable, launcher, plugin, or auxiliary tool obtained from an untrusted source must be treated as potentially hostile.

Do not rely on GF Wordbench to safely execute arbitrary untrusted projects.

---

## 3. Supported versions

Security fixes are applied to:

- the current maintained GF Wordbench release line;
- the current development branch when it is preparing the next release.

Older releases may receive fixes only when explicitly declared supported.

Pre-release builds are intended for evaluation and may change without backward-compatibility guarantees.

The release documentation must identify:

- the supported GF Wordbench version;
- supported Python versions;
- supported GF versions;
- supported operating systems;
- known incompatible tool versions.

---

## 4. Reporting a vulnerability

Do not disclose a suspected vulnerability in a public issue, discussion, pull request, log attachment, or public chat before maintainers have assessed it.

Use the repository host's private vulnerability-reporting feature when available.

When private repository reporting is unavailable, contact the project maintainers through a private channel identified in the repository metadata or release documentation.

A useful report includes:

- affected GF Wordbench version or commit;
- operating system and Python version;
- GF executable and GF version;
- affected command, component, or persisted format;
- required configuration;
- minimal reproduction steps;
- expected behavior;
- observed behavior;
- security impact;
- proof-of-concept files with secrets removed;
- whether the issue is already public;
- suggested mitigation, when known.

Do not include:

- credentials;
- access tokens;
- private keys;
- proprietary language sources not needed for reproduction;
- complete environment dumps;
- personal information;
- production data.

### Response targets

The following are targets, not guarantees:

- acknowledgment within five business days;
- initial triage within ten business days;
- coordinated remediation planning after impact is confirmed;
- public disclosure after a fix or mitigation is available, unless immediate disclosure is necessary to protect users.

Maintainers may request additional evidence or a reduced reproduction.

---

## 5. Security scope

Security issues include, but are not limited to:

- command or argument injection;
- unintended shell execution;
- execution of an unexpected executable;
- path traversal;
- writing outside approved output roots;
- unsafe deletion or cleanup;
- symlink, junction, or reparse-point escape;
- overwriting source files or reviewed gold files;
- insecure temporary-file handling;
- unsafe deserialization;
- schema confusion that changes security-relevant meaning;
- secrets or environment leakage;
- tampering with raw evidence;
- forged or incomplete manifests;
- failure to enforce process timeouts;
- orphaned child processes;
- uncontrolled output or disk exhaustion;
- bypass of required validation markers;
- incorrect trust of exit code alone;
- loading of an unintended GF library path;
- insecure migration of configuration or state;
- malicious archive extraction;
- dependency or executable substitution;
- security-relevant divergence between CLI and GUI behavior.

The following are generally not security vulnerabilities by themselves:

- incorrect linguistic output;
- an ordinary GF syntax or type error;
- expected validation failure;
- inaccurate documentation without security impact;
- performance limitations within configured bounds;
- execution of explicitly trusted project code as designed;
- an upstream GF defect with no GF Wordbench-specific security impact.

Upstream defects that become exploitable through GF Wordbench's integration remain relevant and should be reported with the affected integration path.

---

## 6. Trust boundaries

### 6.1 Trusted framework code

Code shipped as part of a reviewed GF Wordbench release is trusted to enforce this policy.

Local modifications change that trust assumption.

### 6.2 GF executable

The selected `gf` or `gf.exe` is executable code with the user's operating-system permissions.

GF Wordbench must record the resolved executable actually invoked.

Users must obtain GF from a trusted source and verify its origin using available release signatures, hashes, package-manager guarantees, or organizational controls.

An executable discovered through `PATH` must be resolved to a concrete path before execution.

### 6.3 Active language project

The active project is data and executable validation content.

GF source files may cause heavy compilation or generation.

`.gfs` files are executable tool input and may expose shell-like capabilities depending on GF commands and configuration.

An untrusted active project must not be run as though it were passive text.

### 6.4 RGL and library roots

The RGL root and GF search path determine which modules are loaded.

A malicious or unexpected path entry can substitute code or alter validation results.

The effective GF path must be explicit, normalized, recorded, and reproducible.

### 6.5 Environment variables

Inherited environment variables can change:

- executable resolution;
- GF library resolution;
- locale and decoding;
- temporary directories;
- process behavior.

Correctness-critical values must come from resolved configuration rather than an undocumented inherited environment.

### 6.6 Generated artifacts

Raw stdout, stderr, `.gfo`, `.pgf`, normalized outputs, manifests, summaries, and reports are evidence.

Raw evidence must not be rewritten and then represented as original tool output.

### 6.7 GUI and launchers

The GUI and Windows launchers are convenience entry points.

They must not introduce hidden execution semantics, environment changes, or weaker security checks than the CLI.

---

## 7. External process security

### 7.1 No implicit shell

Normal external-tool execution must use an argument list and avoid an intermediate command shell.

Preferred model:

```python
subprocess.run(
    [executable, *args],
    shell=False,
    cwd=working_directory,
)
```

GF Wordbench must not concatenate project-controlled text into one shell command string.

Shell execution is permitted only when:

- a dedicated external-tool contract explicitly requires it;
- the security impact is documented;
- inputs are strictly controlled;
- tests cover quoting and injection resistance;
- the feature is disabled by default when untrusted project input could reach it.

### 7.2 Explicit executable

Each process request must identify the executable explicitly.

The framework must record:

- resolved executable path;
- ordered arguments;
- working directory;
- relevant environment overrides;
- timeout class.

A human-readable command may be logged, but the structured executable and argument list remain authoritative.

### 7.3 Explicit working directory

Every process invocation must define its working directory.

Execution must not depend on:

- the caller's terminal directory;
- an IDE default;
- a shortcut location;
- the GUI process directory;
- a batch file's accidental current directory.

### 7.4 Environment minimization

GF Wordbench should inherit only the environment needed for normal operation.

Security-relevant overrides must be explicit and scoped to the child process.

Reports must not contain:

- complete environment dumps;
- tokens;
- passwords;
- private variables;
- unrelated user data.

### 7.5 Timeouts

Every external process must have a finite timeout.

Timeouts must be configurable by operation class, including:

- version probe;
- file compilation;
- PGF build;
- scenario execution;
- generation;
- diagnostic introspection.

A timeout must remain distinguishable from:

- GF-reported failure;
- launch failure;
- user cancellation;
- contract failure;
- validation failure.

### 7.6 Process termination

On timeout or cancellation, GF Wordbench must attempt to terminate the process and owned child processes.

Partial stdout and stderr must be retained.

A terminated process must not continue writing into a run that has been finalized.

Platform-specific process-group or process-tree handling must remain isolated in the process layer.

### 7.7 Output limits

The framework should enforce configurable limits for:

- stdout size;
- stderr size;
- generated tree count;
- generated sentence count;
- scenario duration;
- artifact size;
- total run size.

Limits protect against:

- runaway generation;
- memory exhaustion;
- disk exhaustion;
- oversized reports;
- denial of service.

When evidence is truncated, the truncation must be explicit and recorded.

### 7.8 Exit-code caution

An exit code is evidence, not the full security or validation result.

A zero exit code must not override:

- missing required markers;
- absent required artifacts;
- fatal diagnostics;
- incomplete scenario output;
- failed gold comparison;
- manifest mismatch.

A non-zero exit code must not cause stdout or stderr to be discarded.

---

## 8. Scenario security

### 8.1 Scenarios are executable input

A `.gfs` file must be treated as executable project content.

Review scenarios before running projects from outside the trusted development boundary.

### 8.2 Operating-system commands

GF shell features capable of invoking operating-system commands, executing shell escapes, or piping to system utilities must be prohibited in normal validation scenarios unless explicitly authorized by project policy.

Authorization must be:

- explicit;
- documented;
- disabled by default;
- visible in reports;
- covered by tests;
- limited to a specific scenario or operation.

### 8.3 Scenario path containment

Scenario files, input files, and gold files must resolve inside approved project roots.

Path traversal outside approved roots must be rejected.

### 8.4 Required markers

A scenario must not pass solely because GF exited successfully.

Required begin/end markers and assertions must complete.

Missing, duplicated, malformed, or out-of-order required markers must produce a contract or validation failure.

### 8.5 Gold files

Normal validation is read-only with respect to `.gold` files.

Gold files may be updated only through an explicit update workflow.

The update workflow must:

- run the scenario;
- normalize the output;
- show or save the difference;
- require explicit authorization;
- write atomically;
- preserve a reviewable version-control change.

A missing required gold file must not be created silently.

### 8.6 Random generation

Random or nondeterministic generation must not be used as an exact golden-output contract unless the random source, seed, bounds, and output order are fully controlled.

Random generation should be used for bounded robustness checks, not for unstable exact expectations.

---

## 9. Filesystem security

### 9.1 Approved roots

The framework must distinguish:

- framework root;
- active project root;
- source root;
- RGL root;
- run root;
- temporary root;
- artifact root.

Source and output roots should be separate.

Run-owned directories may be created automatically.

Missing source directories must not be created to hide configuration errors.

### 9.2 Path normalization

Paths must be normalized before policy checks.

Canonical checks must account for:

- `.` and `..`;
- mixed slash forms;
- Windows drive letters;
- UNC paths;
- case behavior on the current filesystem;
- symlinks;
- directory junctions;
- reparse points;
- long paths;
- spaces and Unicode.

String-prefix checks are not sufficient for containment.

### 9.3 Path traversal

Any output path that resolves outside its approved root must be rejected.

Archive members, scenario outputs, artifact names, and report paths must not escape through:

- `..`;
- absolute paths;
- alternate drive roots;
- UNC paths;
- symlink or junction redirection;
- crafted separator sequences.

### 9.4 Symlinks and reparse points

Strict mode should reject run-owned output paths that traverse symlinks, junctions, or reparse points outside approved roots.

Cleanup and overwrite operations must inspect the resolved target, not only the visible path.

### 9.5 Safe creation

Parent directories must be created only under approved roots.

Artifact filenames must be sanitized without losing identity.

Filename collisions must be resolved deterministically.

### 9.6 Safe overwrite

Every writer must define an overwrite policy.

Existing files must not be overwritten merely because a generated name collides.

Reviewed source files, configuration, scenarios, inputs, and gold files are read-only during normal validation.

### 9.7 Safe deletion

Cleanup is a security-sensitive operation.

Deletion must:

- require a resolved approved root;
- refuse filesystem roots and project source roots;
- reject empty or ambiguous targets;
- avoid following links outside the approved root;
- operate only on framework-owned run or temporary directories;
- preserve evidence when retention policy requires it;
- provide a dry-run mode for broad cleanup;
- log what was deleted.

Recursive deletion must never accept raw unvalidated project-controlled paths.

### 9.8 Temporary files

Temporary files containing sensitive diagnostics or project content must:

- be created under a controlled temporary or run root;
- use unpredictable names;
- avoid world-writable locations when stronger local alternatives exist;
- be closed before replacement;
- be removed when no longer needed;
- not replace canonical files until validation succeeds.

### 9.9 Atomic writes

State, summaries, manifests, migrations, and gold updates must use atomic replacement where supported:

1. write a sibling temporary file;
2. flush and close it;
3. validate it;
4. replace the destination.

A failed write must not destroy the last valid file.

---

## 10. Persisted data security

### 10.1 Schema validation

Machine-readable persisted files must use explicit schema identifiers and versions.

Readers must validate required fields and reject unsupported major versions.

Unknown enum values must not be silently reinterpreted.

### 10.2 No unsafe deserialization

GF Wordbench must not load untrusted persisted data through unsafe object deserialization.

Prohibited formats for untrusted input include mechanisms that can construct arbitrary Python objects or execute code during loading.

Use validated JSON, TOML, and canonical text formats.

### 10.3 State file

The application state is disposable convenience data.

It must not contain:

- credentials;
- tokens;
- private keys;
- complete environment snapshots;
- in-memory objects;
- active execution state restored as running;
- authoritative language-project contracts.

A malformed state file should be ignored or quarantined rather than causing unsafe recovery behavior.

### 10.4 Summary and manifest integrity

`summary.json` is the machine-readable run record.

`manifest.json` records artifact identity, size, and hash.

Manifest validation must detect:

- missing required artifacts;
- duplicate paths;
- paths outside the run root;
- modified artifact bytes;
- size mismatch;
- hash mismatch.

The manifest must not hash itself unless a separate signed envelope is introduced.

### 10.5 Migrations

Schema migrations must:

- read without modifying the source;
- validate before conversion;
- write to a separate destination or atomically replace only after success;
- report warnings and losses;
- preserve raw legacy evidence;
- be idempotent;
- avoid interpreting data as code.

Opening a project must not silently rewrite its canonical configuration.

---

## 11. Evidence integrity

### 11.1 Raw evidence

Raw evidence includes:

- executed command structure;
- working directory;
- relevant environment overrides;
- exit code;
- timeout state;
- launch error;
- stdout;
- stderr;
- generated artifacts.

Raw evidence must be captured before normalization.

### 11.2 Derived evidence

Derived artifacts include:

- normalized scenario output;
- diagnostic summaries;
- top-error groups;
- Markdown reports;
- AI handoff packets;
- gold differences.

Derived evidence must reference its raw source.

### 11.3 No evidence rewriting

A component must not modify tool-generated content and then label it raw.

Normalization must create a separate artifact.

### 11.4 Hashing

Important persisted artifacts should be hashed with SHA-256 in the run manifest.

Hashes detect accidental or malicious changes; they do not prove publisher identity.

Cryptographic signing, when added, must use a separate documented trust and key-management policy.

---

## 12. Secrets and privacy

### 12.1 Secret handling

GF Wordbench is not a secret-management system.

Do not store secrets in:

- `project.toml`;
- application state;
- scenarios;
- input fixtures;
- gold files;
- reports;
- logs;
- command-line arguments;
- checked-in launchers.

### 12.2 Reports

Reports may expose:

- local absolute paths;
- usernames embedded in paths;
- source filenames;
- language examples;
- diagnostics;
- fragments of project source;
- tool versions;
- project structure.

Review reports before sharing them outside the project boundary.

### 12.3 AI handoff

`AI_READY.md` may contain proprietary or sensitive development context.

Before sharing it:

- inspect included excerpts;
- remove secrets;
- remove unnecessary personal paths;
- confirm that source snippets may be disclosed;
- confirm that logs do not contain private environment values.

AI handoff generation must not dump the complete environment.

### 12.4 Redaction

Redaction must occur in derived reports, not by mutating raw evidence.

A redacted export should record that redaction occurred.

### 12.5 Network behavior

Core GF Wordbench validation should not require network access.

A future feature that initiates network connections must document:

- destination;
- transmitted data;
- authentication;
- timeout;
- retry policy;
- certificate validation;
- privacy impact;
- offline fallback;
- security tests.

Network behavior must not be added silently.

---

## 13. Dependency and supply-chain security

### 13.1 Python dependencies

Dependencies must be declared in `pyproject.toml`.

Security-sensitive changes require review of:

- package origin;
- maintained status;
- license;
- supported Python versions;
- transitive dependencies;
- installation behavior;
- known vulnerabilities.

Runtime dependencies should remain minimal.

### 13.2 Dependency updates

Dependency updates must:

- be deliberate;
- preserve reproducible constraints;
- run the full test suite;
- run security-relevant contract tests;
- be documented in the changelog when behavior changes.

### 13.3 External tools

A new external tool must not be added merely for convenience.

Before adoption, document:

- tool name and version;
- purpose;
- why existing capabilities are insufficient;
- source and installation method;
- license;
- supported platforms;
- command contract;
- security impact;
- fallback behavior;
- tests.

### 13.4 Executable substitution

The executable actually invoked must be resolved and recorded.

GUI, CLI, launchers, and automation must not resolve different executables for equivalent configuration.

### 13.5 Release artifacts

Official releases should provide enough information to verify:

- version;
- source commit;
- package contents;
- dependency metadata;
- build procedure;
- hashes or signatures when available.

---

## 14. Secure coding requirements

### 14.1 Boundary validation

Validate data at trust boundaries:

- CLI arguments;
- GUI fields;
- project configuration;
- state files;
- persisted summaries;
- scenario identifiers;
- paths;
- external-tool outputs;
- manifest entries;
- migration inputs.

Internal callers must not bypass shared validators.

### 14.2 Least authority

Components should receive only the paths and capabilities they require.

Examples:

- report writers consume results and must not launch GF;
- GUI widgets invoke the audit orchestrator and must not launch GF directly;
- the process runner launches processes but does not classify GF errors;
- cleanup operates only on framework-owned roots.

### 14.3 Error handling

Security-sensitive failures must be explicit.

Do not convert:

- launch failure into GF syntax failure;
- timeout into ordinary compile failure;
- path rejection into missing-file success;
- manifest mismatch into a warning when integrity is required;
- malformed schema into default success;
- incomplete scenario into pass.

### 14.4 Logging

Logs should contain enough information for diagnosis without exposing unnecessary sensitive data.

Do not log:

- passwords;
- tokens;
- secret environment values;
- complete environment dumps;
- hidden GUI fields;
- private keys.

### 14.5 Assertions

Python `assert` statements must not be the only enforcement of security checks because optimized execution may remove them.

Use explicit validation and exceptions or structured failures.

### 14.6 Regular expressions

Regular expressions processing project-controlled text must be reviewed for pathological backtracking and bounded where necessary.

User-provided regular expressions should be validated and executed against bounded inputs.

### 14.7 Archive handling

Any future import/export archive feature must:

- reject absolute member paths;
- reject `..` traversal;
- reject links escaping the destination;
- enforce member-count and size limits;
- extract under a new controlled directory;
- avoid overwriting existing project files by default;
- validate the resulting project before activation.

---

## 15. Secure defaults

The default configuration should:

- resolve an explicit GF executable;
- use `shell=False`;
- set finite timeouts;
- disable operating-system commands in scenarios;
- keep gold files read-only during validation;
- separate source and output roots;
- reject output path traversal;
- capture stdout and stderr separately;
- preserve raw evidence;
- limit generation and output size;
- avoid complete environment logging;
- avoid network access;
- require explicit action for destructive cleanup;
- require explicit action for migration and gold updates.

A convenience feature must not silently weaken these defaults.

---

## 16. Security modes

### 16.1 Normal mode

Normal mode is intended for trusted local projects.

It still enforces:

- path containment;
- process timeouts;
- no implicit shell;
- read-only gold behavior;
- raw evidence preservation;
- schema validation.

### 16.2 Strict mode

Strict mode should additionally:

- require explicit executable paths;
- reject environment fallback for GF path resolution;
- reject unsupported or untested GF versions according to policy;
- reject shell-capable scenario commands;
- reject symlink or reparse-point output traversal;
- require all expected markers and artifacts;
- validate manifests and hashes;
- reject unknown persisted-schema fields when policy requires;
- enforce output and artifact limits;
- require project-relative canonical paths;
- fail on missing required gold files.

Suggested command form:

```text
gf-wordbench validate --strict
```

### 16.3 No sandbox mode

There is no mode in which arbitrary untrusted scenarios become safe merely by setting a flag.

Strict mode reduces risk; it does not provide operating-system isolation.

Use a separate low-privilege account, container, virtual machine, or organizational sandbox when evaluating untrusted projects.

---

## 17. Secure operational guidance

### 17.1 Run with least privilege

Do not run GF Wordbench:

- as Administrator or root unless absolutely required;
- with write access to unrelated repositories;
- with access to unnecessary secrets;
- from a highly privileged service account.

### 17.2 Isolate untrusted projects

For projects that are not fully trusted:

- use a disposable workspace;
- use a low-privilege account;
- remove credentials from the environment;
- disable network access where practical;
- restrict writable directories;
- set conservative timeouts and size limits;
- inspect `.gfs` files before execution;
- retain logs for review;
- discard the environment afterward.

### 17.3 Protect evidence

Run directories may contain proprietary source fragments and local paths.

Apply filesystem permissions appropriate to the project.

Do not publish raw runs automatically.

### 17.4 Backup

Back up:

- active project sources;
- reviewed scenarios;
- gold files;
- project configuration;
- documentation alignment and contract locks;
- decision logs;
- release evidence.

Generated run directories may follow a separate retention policy.

### 17.5 Cleanup

Review cleanup scope before deletion.

Prefer dry-run output for bulk cleanup.

Do not use third-party cleanup scripts unless their path and deletion rules have been reviewed.

---

## 18. Security testing

The test suite should include dedicated security and contract tests.

Recommended structure:

```text
tests/security/
├── test_command_injection.py
├── test_shell_disabled.py
├── test_executable_resolution.py
├── test_environment_redaction.py
├── test_path_traversal.py
├── test_symlink_escape.py
├── test_safe_cleanup.py
├── test_atomic_writes.py
├── test_schema_validation.py
├── test_manifest_integrity.py
├── test_scenario_markers.py
├── test_gold_read_only.py
├── test_output_limits.py
├── test_timeout_termination.py
├── test_secret_redaction.py
└── test_archive_safety.py
```

### 18.1 Required process tests

Test:

- ordered arguments;
- paths with spaces;
- Unicode paths;
- missing executable;
- executable substitution;
- timeout;
- cancellation;
- non-zero exit with retained streams;
- output-size limit;
- child-process containment where supported.

### 18.2 Required filesystem tests

Test:

- `..` traversal;
- absolute output path;
- alternate-drive path;
- UNC path policy;
- symlink escape;
- junction or reparse-point escape on Windows;
- filename collision;
- overwrite refusal;
- cleanup outside run root;
- filesystem-root refusal;
- atomic replacement failure.

### 18.3 Required persisted-data tests

Test:

- unsupported schema version;
- malformed JSON and TOML;
- unknown security-relevant enum;
- unsafe path in manifest;
- hash mismatch;
- duplicate artifact path;
- legacy migration;
- idempotent migration;
- secrets excluded from state and reports.

### 18.4 Required scenario tests

Test:

- shell-capable command rejection;
- missing marker;
- duplicated marker;
- incomplete scenario with zero exit code;
- missing required artifact;
- gold file unchanged during normal run;
- explicit gold update;
- unbounded generation rejected or bounded.

### 18.5 Real-tool integration tests

A small trusted fixture grammar should test:

- version probing;
- successful compile;
- failed compile;
- PGF build;
- scenario loading;
- parse;
- linearize;
- bounded generation;
- timeout behavior when safely testable.

Tests requiring real GF should be isolated and clearly marked.

---

## 19. Security review triggers

A security review is required when changing:

- process execution;
- executable discovery;
- shell policy;
- scenario syntax or permissions;
- GF path construction;
- output or temporary paths;
- cleanup behavior;
- archive handling;
- state or summary schema;
- manifest rules;
- gold-update behavior;
- network behavior;
- dependency set;
- launcher behavior;
- report redaction;
- artifact retention;
- supported GF or Python versions.

A review must identify:

- trust boundary changed;
- new inputs;
- new outputs;
- new permissions;
- new persisted fields;
- new executable behavior;
- rollback or migration plan;
- tests added.

---

## 20. Incident response

When a vulnerability is confirmed:

1. preserve the report and minimal evidence privately;
2. identify affected versions and configurations;
3. assess exploitability and impact;
4. define immediate mitigation;
5. create and test the fix;
6. review adjacent contracts for similar defects;
7. update security tests;
8. update affected owner documents, alignment or contract locks, and schemas;
9. prepare release notes and migration guidance;
10. coordinate disclosure.

If evidence may contain secrets or proprietary sources, restrict access and distribute only redacted copies.

A security fix must not silently alter persisted formats or external-tool contracts without the required versioning and migration work.

---

## 21. Severity guidance

Severity depends on realistic impact and required preconditions.

### Critical

Examples:

- arbitrary command execution from ordinary untrusted project data without explicit authorization;
- arbitrary write or deletion outside approved roots;
- credential disclosure with broad impact;
- release artifact compromise.

### High

Examples:

- shell escape bypass;
- persistent executable substitution;
- symlink or junction escape enabling sensitive overwrite;
- unsafe deserialization leading to code execution;
- security checks bypassed in normal supported workflows.

### Medium

Examples:

- sensitive path or environment leakage;
- denial of service beyond configured limits;
- manifest-integrity bypass;
- incomplete process termination;
- insecure migration requiring local project control.

### Low

Examples:

- limited information disclosure;
- unsafe behavior requiring unusual explicit opt-in;
- missing hardening with no demonstrated exploit path.

Severity may change after reproducibility and deployment context are understood.

---

## 22. Security release checklist

Before a production release:

```text
[ ] Supported Python versions are documented
[ ] Supported GF versions are documented
[ ] Dependency review is complete
[ ] Full tests pass
[ ] Security tests pass
[ ] Real-GF integration tests pass where available
[ ] CLI and GUI resolve equivalent security settings
[ ] Documentation alignment and affected owner documents are current
[ ] External-tool contracts are current
[ ] Persisted schemas and migrations are current
[ ] Path-containment tests pass
[ ] Cleanup tests pass
[ ] Gold files remain read-only in normal runs
[ ] Output and timeout limits are enforced
[ ] Reports contain no test secrets
[ ] State contains no runtime objects or credentials
[ ] Manifest validation passes
[ ] Release artifacts are reviewable and hashed
[ ] Changelog includes security-relevant changes
[ ] SECURITY.md is reviewed
```

---

## 23. Related normative documents

Security-sensitive behavior is also governed by:

```text
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
```

`docs/DOCUMENTATION_CORRECTION_LEDGER.md` coordinates documentation corrections performed across branches, but it does not replace an owner document or a specialized contract lock.

This policy defines security expectations. The documentation alignment lock defines cross-document authority and interpretation. The specialized contract locks define the exact boundaries that code, configuration, persisted data, project assets and templates must preserve.

Resolve documentary authority according to `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`. Until the owner documents are corrected together:

1. choose the safer behavior temporarily;
2. preserve raw evidence;
3. stop destructive or external execution when necessary;
4. record the conflict in `docs/DOCUMENTATION_CORRECTION_LEDGER.md`;
5. update every affected owner document and lock together;
6. add a regression test.

---

## 24. Final rule

GF Wordbench operates on local code, executes external tools, and writes persistent evidence.

Therefore:

> No project-controlled text may become a shell command, no output may escape its approved root, no untrusted scenario may be treated as passive data, and no security-relevant contract may change without coordinated review and tests.
