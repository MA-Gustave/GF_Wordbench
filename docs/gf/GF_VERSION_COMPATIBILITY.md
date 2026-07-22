# GF Wordbench — GF Version Compatibility

**Document ID:** `GF-WB-GF-VERSION-COMPATIBILITY`  
**Status:** Final technical specification  
**Applies to:** GF core, GF shell/compiler behavior, RGL compatibility, PGF construction, scenarios, and GF-backed release validation  
**Owner:** GF Wordbench maintainers  
**Compatibility policy version:** `1.0.0`  
**Verified baseline date:** `2026-07-22`  
**Normative counterparts:**
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
- `docs/gf/GF_TOOLCHAIN_INTEGRATION.md`
- `docs/gf/GF_PATH_RESOLUTION.md`
- `docs/gf/GF_COMPILATION.md`
- `docs/gf/GF_PGF_BUILD.md`
- `docs/gf/GF_SCRIPT_EXECUTION.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
- `docs/configuration/PROJECT_TOML_REFERENCE.md`

---

## 1. Purpose

This document defines how GF Wordbench identifies, classifies, tests, and accepts a Grammatical Framework installation.

A version string alone is not sufficient to prove compatibility.

GF compatibility depends on a combination of:

- GF core version;
- GF build identity;
- platform;
- available compiler and shell capabilities;
- command-line option behavior;
- output and diagnostic behavior;
- RGL identity;
- active project requirements;
- GF Wordbench validation mode.

GF Wordbench therefore uses both version policy and capability evidence.

> GF Wordbench MUST never silently assume that an unknown GF version behaves like a tested version.

The product should remain usable when a newer compatible GF release appears, but release certification must remain deliberate.

---

## 2. Current verified upstream baseline

As of the verified baseline date:

```text
Latest official stable GF core release: 3.12
Release date: 2025-08-08
Canonical normalized version: 3.12.0
```

GF 3.12 is the primary GF Wordbench target.

Relevant upstream facts:

- GF 3.12 added support for newer GHC versions and Apple Silicon;
- GF 3.12 includes compiler, shell, runtime, diagnostic, and performance improvements;
- the GF core distribution and the Resource Grammar Library are obtained separately;
- GF core and RGL release cycles must be treated independently;
- the official shell supports batch compilation, PGF construction, parsing, linearization, generation, morphology, and grammar inspection.

The baseline date records when this compatibility policy was last checked. It is not a promise that 3.12 will remain the newest upstream release indefinitely.

---

## 3. Compatibility goals

GF Wordbench MUST:

1. identify the executable actually used;
2. preserve the exact version-probe response;
3. normalize a usable GF version when possible;
4. distinguish supported, tested, untested, incompatible, and unknown states;
5. verify required capabilities before depending on them;
6. treat GF core and RGL identity separately;
7. keep compatibility behavior consistent across CLI, GUI, compilation, scenarios, and PGF builds;
8. record every compatibility override;
9. reject known-incompatible configurations;
10. avoid modifying user grammars during compatibility probing;
11. provide actionable diagnostics;
12. make release certification reproducible.

---

## 4. Non-goals

This document does not:

- promise support for every historical GF release;
- reproduce upstream GF release notes;
- define GF language semantics;
- define RGL language quality;
- guarantee that an arbitrary RGL revision works with an arbitrary GF core revision;
- infer project correctness from a successful version probe;
- replace integration tests with string comparison;
- automatically certify unknown future GF releases;
- require source builds of GF;
- require one installation method;
- treat a development build as equivalent to an official release without evidence.

---

## 5. Compatibility dimensions

GF Wordbench evaluates compatibility across six dimensions.

### 5.1 Core version

The normalized GF compiler/shell version.

Example:

```text
3.12.0
```

### 5.2 Build identity

Additional evidence when available:

```text
raw version line
build date
Git revision
build flags
runtime features
distribution name
```

### 5.3 Platform

At minimum:

```text
operating system
architecture
executable path
```

Recommended values:

```text
windows-x86_64
linux-x86_64
macos-x86_64
macos-arm64
```

### 5.4 Capability set

The operations and flags proven usable by probes or integration tests.

### 5.5 RGL identity

The RGL source or binary revision used by the run.

### 5.6 Project requirements

The active project may require a higher minimum version or a capability not required by the framework baseline.

---

## 6. Final support tiers

GF Wordbench uses the following support tiers.

### 6.1 `certified`

Meaning:

- explicitly supported by the framework;
- included in the compatibility matrix;
- required capability suite passes;
- release workflow is allowed;
- integration evidence exists for supported platforms.

Initial certified line:

```text
GF 3.12.x
```

### 6.2 `compatible`

Meaning:

- explicitly supported as a secondary line;
- core workflows are expected to work;
- a reduced or compatibility-adapted capability set may apply;
- release use may require stricter project evidence.

Initial compatible line:

```text
GF 3.11.x
```

### 6.3 `untested_newer`

Meaning:

- normalized version is greater than the highest certified line;
- no known incompatibility is registered;
- required capability probes may allow non-release work;
- the version is not automatically release-certified.

### 6.4 `legacy_unsupported`

Meaning:

- version is older than the minimum supported line;
- GF Wordbench may identify it and provide migration guidance;
- GF-backed project validation is blocked by default.

Initial legacy boundary:

```text
GF 3.10.x and older
```

### 6.5 `known_incompatible`

Meaning:

- an exact version, version range, build, platform combination, or capability configuration is registered as unsafe or semantically incompatible;
- execution is blocked for affected operations.

### 6.6 `unknown`

Meaning:

- GF launched, but a normalized version could not be determined;
- capability probing may still collect evidence;
- release validation is blocked.

### 6.7 `probe_failed`

Meaning:

- executable could not be launched;
- probe timed out;
- output could not be captured;
- process contract failed.

This is an execution/configuration error, not a compatibility tier.

---

## 7. Initial compatibility matrix

The matrix below is the initial GF Wordbench policy, not an upstream GF guarantee.

| GF core | GF Wordbench tier | Quick | Checkpoint | Diagnostic | Release |
|---|---|---:|---:|---:|---:|
| `3.12.x` | `certified` | allowed | allowed | allowed | allowed |
| `3.11.x` | `compatible` | allowed | allowed with probes | allowed | allowed only when release capability suite passes |
| `>3.12.x` | `untested_newer` | allowed with warning and probes | allowed with warning and probes | allowed | blocked by default |
| `3.10.x` | `legacy_unsupported` | scan-only or explicit override | blocked | limited migration diagnostics | blocked |
| `<3.10` | `legacy_unsupported` | scan-only | blocked | version diagnostics only | blocked |
| unknown version | `unknown` | scan-only or explicit diagnostic override | blocked | capability investigation only | blocked |
| registered bad build/range | `known_incompatible` | operation-dependent block | blocked as applicable | evidence collection only | blocked |

### 7.1 Why 3.11 is the minimum supported line

GF 3.11 established the modern distribution boundary in which GF core and RGL are separate release streams.

GF Wordbench's project and environment model is designed around that separation.

Older versions may still provide useful GF functionality, but supporting their bundled-library assumptions would add a second installation model and increase drift risk.

### 7.2 Policy flexibility

A future compatibility-policy revision may:

- certify newer GF lines;
- retire 3.11;
- add platform-specific restrictions;
- add exact build exclusions;
- introduce compatibility adapters.

Such changes require documented tests and a policy-version change.

---

## 8. Project-level minimum version

The active project may declare:

```toml
[gf]
minimum_version = "3.12"
```

An empty value means:

```text
use framework minimum
```

### 8.1 Effective minimum

The effective minimum is the stricter of:

```text
framework minimum
project minimum
```

### 8.2 Project restrictions

A project MAY eventually declare:

```toml
[gf.compatibility]
minimum_version = "3.12"
maximum_tested_version = "3.12"
required_capabilities = [
  "batch_compile",
  "pgf_build",
  "shell_import_retain",
  "parse",
  "linearize",
  "print_missing",
]
```

This extension requires a coordinated `project.toml` schema revision before becoming canonical.

### 8.3 Prohibited project behavior

The project MUST NOT silently lower the framework minimum.

A project MAY allow an untested newer version for development, but release certification remains governed by framework and project release policy.

---

## 9. Version-probe contract

### 9.1 Normative request

```text
<gf-executable> --version
```

### 9.2 Working directory

```text
resolved project root
```

### 9.3 Timeout

Default:

```text
10 seconds
```

The probe timeout is independent from compile, scenario, and PGF-build timeouts.

### 9.4 Captured evidence

The probe MUST capture separately:

```text
stdout
stderr
exit code
timeout state
duration
executed argument list
working directory
executable path
```

Recommended raw artifacts:

```text
raw/gf_version.out.txt
raw/gf_version.err.txt
```

### 9.5 Preferred raw version line

Use:

1. first non-empty stdout line;
2. otherwise first non-empty stderr line;
3. otherwise no version line.

The exact selected line and both raw streams MUST remain available.

### 9.6 Probe result states

```text
identified
unparseable
empty_output
nonzero_exit
timed_out
launch_failed
skipped
```

### 9.7 Skip behavior

Version probing MAY be skipped only by explicit configuration.

A skipped probe MUST record:

```text
probe_state = skipped
compatibility_tier = unknown
```

GF-backed release validation MUST NOT pass with a skipped probe.

---

## 10. Version normalization

GF Wordbench extracts a semantic numeric identity from the raw version response.

Expected examples may include:

```text
GF 3.12
GF 3.12.0
This is GF version 3.12.0.
Grammatical Framework 3.12
```

Canonical normalized form:

```text
MAJOR.MINOR.PATCH
```

Examples:

```text
3.12   -> 3.12.0
3.12.0 -> 3.12.0
3.11   -> 3.11.0
```

### 10.1 Parser rules

The parser MUST:

- preserve the raw text;
- prefer a version associated with `GF`, `Grammatical Framework`, or `version`;
- accept two or three numeric components;
- normalize a missing patch component to zero;
- reject negative or malformed components;
- avoid selecting unrelated build-tool versions;
- report ambiguity rather than choose silently;
- support pre-release/build metadata when present.

### 10.2 Recommended model

```python
@dataclass(frozen=True, order=True, slots=True)
class GFVersion:
    major: int
    minor: int
    patch: int
    prerelease: str | None = None
    build: str | None = None
```

### 10.3 Development builds

Examples:

```text
3.13.0-dev
3.12.0+git.abcdef
```

A development build is not certified solely because its numeric base matches a certified release.

Recommended normalized metadata:

```json
{
  "version": "3.12.0",
  "prerelease": null,
  "build": "git.abcdef",
  "is_development_build": true
}
```

### 10.4 Ambiguous output

When multiple plausible GF versions appear:

```text
probe_state = unparseable
compatibility_tier = unknown
```

The raw evidence is preserved for diagnosis.

---

## 11. Compatibility is capability-based

Version comparison provides policy context.

Capabilities provide operational proof.

GF Wordbench MUST NOT enable an operation only because a numeric version is high enough when:

- the option may vary by build;
- platform packaging may omit a runtime;
- a development build may differ;
- RGL compatibility is uncertain;
- a known regression exists.

### 11.1 Capability categories

```text
identity
compiler
shell
runtime
artifact
path
diagnostic
encoding
```

### 11.2 Capability states

```text
supported
unsupported
unknown
probe_failed
not_applicable
```

### 11.3 Evidence levels

```text
declared
help_detected
smoke_tested
integration_tested
release_tested
```

Higher levels provide stronger evidence.

---

## 12. Core capability registry

Canonical capability identifiers:

### Identity and process

```text
version_probe
help_query
batch_mode
silent_mode
utf8_source
```

### Compilation

```text
batch_compile
make_compile
gf_lib_path_option
gf_search_path_option
gfo_dir_option
output_dir_option
cpu_stats_option
```

### PGF

```text
pgf_build
pgf_optimize
pgf_nonempty_artifact
```

### Shell and scenarios

```text
shell_stdin_script
shell_import
shell_import_retain
shell_quit
shell_print_string
```

### Runtime grammar operations

```text
parse
linearize
generate
morpho_analyse
print_grammar
print_missing
compute_concrete
show_operations
show_dependencies
```

### Output behavior

```text
separate_stream_capture
stable_utf8_output
fatal_diagnostic_detection
```

Capability identifiers are stable internal contracts and MUST NOT be renamed without migration.

---

## 13. Capability discovery strategy

GF Wordbench uses the least invasive sufficient evidence.

### 13.1 Level 1 — Version declaration

Use the normalized version and policy matrix.

This level alone is insufficient for release certification.

### 13.2 Level 2 — Help inspection

Possible non-destructive requests:

```text
gf -help
```

and, through a controlled shell session:

```text
help -full
q
```

Help inspection MAY detect command or flag availability.

It MUST NOT treat translated wording or formatting as a permanent schema.

### 13.3 Level 3 — Minimal smoke grammar

A bundled language-neutral fixture SHOULD prove:

- `.gf` compilation;
- `.gfo` creation;
- grammar loading;
- parse;
- linearization;
- optional generation;
- PGF construction.

### 13.4 Level 4 — Active-project validation

The project's actual checkpoints and scenarios prove compatibility for that project.

### 13.5 Probe caching

Probe results MAY be cached using an identity key containing:

```text
GF executable fingerprint
raw version identity
platform
GF Wordbench compatibility-policy version
probe-suite version
```

A changed executable hash invalidates the cache.

---

## 14. Required capability suites

### 14.1 Scan-only suite

Required capabilities:

```text
none from GF
```

GF executable and RGL may be absent when the selected mode explicitly performs no GF operation.

### 14.2 Quick suite

```text
version_probe
batch_mode
batch_compile
gf_search_path_option
stable_utf8_output
```

### 14.3 Checkpoint suite

```text
all quick capabilities
shell_stdin_script
shell_import
parse or linearize as required by configured scenarios
```

### 14.4 Diagnostic suite

```text
version_probe
help_query
batch_compile
shell_stdin_script
shell_import
stable_utf8_output
fatal_diagnostic_detection
```

Additional diagnostic operations are required only when requested.

### 14.5 Release suite

```text
version_probe
batch_compile
pgf_build
pgf_nonempty_artifact
shell_stdin_script
shell_import
parse
linearize
stable_utf8_output
fatal_diagnostic_detection
all project-required capabilities
```

`pgf_optimize` is required when project release policy requires optimized PGF output.

---

## 15. Mode behavior by compatibility tier

### 15.1 Certified version

- run normally;
- execute the mode's capability suite;
- fail only on actual probe, validation, or known-regression evidence.

### 15.2 Compatible version

- run required capability probes;
- emit compatibility notice;
- allow release only after the full release suite and active-project release scenarios pass.

### 15.3 Untested newer version

#### Quick

Allowed with a warning when the quick suite passes.

#### Checkpoint

Allowed with a warning when the checkpoint suite passes.

#### Diagnostic

Allowed for evidence collection.

#### Release

Blocked by default.

An explicit override MAY run the release suite, but the result MUST be marked:

```text
release_certification = unverified_toolchain
```

A project MUST NOT claim a fully certified release unless policy explicitly approves that GF line.

### 15.4 Legacy unsupported version

- static scanning remains available;
- compatibility diagnostics remain available;
- GF-backed checkpoints and releases are blocked by default;
- an override is for migration investigation, not release certification.

### 15.5 Unknown version

- no certified GF-backed release;
- capability investigation may run under diagnostic mode;
- successful probes do not silently convert `unknown` into `certified`.

### 15.6 Known incompatible version

Affected operations are blocked regardless of override unless a dedicated emergency policy exists.

---

## 16. Unknown newer release policy

Unknown future releases should not make routine development impossible.

Default behavior:

```text
quick       -> warn, probe, proceed if required capabilities pass
checkpoint  -> warn, probe, proceed if required capabilities pass
diagnostic  -> proceed for evidence collection
release     -> block certification
```

Strict mode:

```text
all GF-backed modes -> fail before project validation
```

### 16.1 Certification workflow

To certify a newer GF line:

1. update official-release evidence;
2. run unit compatibility tests;
3. run the bundled smoke grammar;
4. run real-GF integration tests on supported platforms;
5. test path handling;
6. test diagnostics and normalization;
7. test PGF construction;
8. test representative active-project scenarios;
9. review RGL compatibility;
10. update the compatibility matrix;
11. update known incompatibilities;
12. increment compatibility-policy version;
13. update release notes.

---

## 17. Known-incompatibility registry

GF Wordbench MUST maintain a machine-readable or code-owned registry.

Recommended entry:

```python
@dataclass(frozen=True, slots=True)
class KnownGFIncompatibility:
    id: str
    version_spec: str
    platforms: tuple[str, ...]
    capability: str | None
    severity: str
    summary: str
    workaround: str | None
    source_reference: str
```

Recommended severities:

```text
warning
operation_block
release_block
total_block
```

### 17.1 Stable identifiers

Format:

```text
GF-INCOMPAT-<NUMBER>
```

Example:

```text
GF-INCOMPAT-0001
```

Identifiers are never reused.

### 17.2 No speculative entries

A version MUST NOT be marked incompatible from rumor or unverified output variation.

Required evidence:

- reproducible failure;
- upstream release note or issue;
- verified local integration result;
- documented platform/build combination.

### 17.3 Current initial registry

```text
No exact GF 3.11.x or 3.12.x core build is declared known-incompatible by this document.
```

Platform- or project-specific findings should be added only after verification.

---

## 18. RGL compatibility

GF core and RGL are separate compatibility subjects.

### 18.1 Required RGL identity

GF Wordbench SHOULD record the strongest available RGL identity:

1. explicit release/tag;
2. Git commit hash;
3. binary-distribution manifest;
4. directory manifest hash;
5. user-provided label plus selected file fingerprints;
6. `UNKNOWN`.

### 18.2 Recommended model

```python
@dataclass(frozen=True, slots=True)
class RGLIdentity:
    root: Path
    identity_kind: str
    identity_value: str
    git_commit: str | None = None
    release_tag: str | None = None
    dirty: bool | None = None
```

### 18.3 Dirty source checkout

When the RGL is a Git checkout with uncommitted changes:

```text
dirty = true
```

Release policy SHOULD require explicit acknowledgement.

### 18.4 RGL proof

A valid directory is not sufficient proof.

The compatibility suite SHOULD compile a fixture that imports required RGL modules.

### 18.5 Project-specific RGL requirements

The active project may depend on:

- particular RGL APIs;
- specific module names;
- a minimum RGL revision;
- project-maintained RGL changes.

Those requirements belong in project documentation and project configuration when a versioned schema supports them.

### 18.6 RGL mismatch behavior

Typical states:

```text
identified_and_tested
identified_untested
dirty_checkout
unknown_identity
required_module_missing
compile_incompatible
```

A missing required RGL module is a configuration/compatibility error, not a language-source syntax error.

---

## 19. PGF compatibility

A `.pgf` artifact is compiler/runtime output whose compatibility must not be assumed across arbitrary GF versions.

### 19.1 Build-time policy

The release manifest MUST record:

```text
GF core version
GF executable fingerprint
RGL identity
PGF build command
entrypoints
PGF size and hash
```

### 19.2 Runtime policy

When a PGF is consumed by another GF runtime or binding, GF Wordbench SHOULD record that runtime's identity separately.

### 19.3 Cross-version use

A PGF built by one GF version MUST NOT be declared compatible with another runtime version without a tested compatibility contract.

### 19.4 Release artifacts

A release SHOULD preserve enough toolchain identity to rebuild the PGF.

---

## 20. Python and C runtime bindings

GF installations may include or support runtime bindings.

These are optional unless a GF Wordbench feature explicitly depends on them.

Potential identities:

```text
pgf Python package version
C runtime version/build
server-mode capability
```

### 20.1 Isolation

Failure of an optional binding MUST NOT invalidate compiler/shell validation that does not use it.

### 20.2 Feature activation

A binding-backed feature requires its own capability and external-tool contract before becoming release-critical.

### 20.3 Java bindings

GF 3.12 release information indicates that Java bindings were temporarily dropped.

GF Wordbench MUST NOT make Java bindings part of the baseline GF 3.12 capability suite.

---

## 21. Platform policy

### 21.1 Windows

Primary requirements:

- `gf.exe` executable discovery;
- paths containing spaces;
- Unicode paths and output;
- argument-list execution;
- timeout containment;
- no dependency on a visible console;
- explicit RGL root;
- tested GF path separator behavior.

Initial primary environment:

```text
GF 3.12.x on Windows x86_64
```

### 21.2 Linux

Requirements:

- executable resolution;
- UTF-8 locale behavior;
- permissions;
- process-group termination;
- native path handling.

### 21.3 macOS

Supported architectures may include:

```text
x86_64
arm64
```

GF 3.12 is the first official release line in this policy explicitly targeted for Apple Silicon packages.

### 21.4 WSL

WSL is treated as a Linux execution environment.

Windows paths passed directly into a WSL GF process are not assumed compatible and require explicit path translation policy.

### 21.5 Unsupported platform

A platform not present in the tested-platform registry is:

```text
platform_support = untested
```

It may run development probes but is not release-certified by default.

---

## 22. Diagnostic and output compatibility

Version changes may alter:

- error wording;
- source locations;
- warning wording;
- banner text;
- shell prompts;
- command help;
- output ordering;
- generated artifact details.

### 22.1 Raw evidence

Raw stdout and stderr are never normalized in place.

### 22.2 Diagnostic parser

The parser MUST:

- use version-aware patterns when necessary;
- retain an `OTHER` fallback;
- avoid treating unknown wording as success;
- record parse uncertainty;
- preserve raw evidence paths.

### 22.3 Gold files

Normalization changes caused by a new GF version require:

- normalization review;
- deliberate gold diff review;
- scenario evidence;
- migration note when accepted.

### 22.4 Unknown diagnostic wording

Unknown wording should produce:

```text
error_kind = OTHER
diagnostic_parse_state = partial or unknown
```

It MUST NOT be discarded.

---

## 23. Encoding compatibility

Canonical GF Wordbench text handling is UTF-8.

### 23.1 Source files

GF 3.12 release notes indicate improvements that consistently treat GF files as UTF-8.

GF Wordbench nevertheless validates and records decoding errors independently.

### 23.2 Process streams

The process layer SHOULD decode as UTF-8 with an explicit fallback policy that preserves undecodable bytes or replacement diagnostics.

### 23.3 Locale

Locale-dependent output behavior MUST be visible in compatibility evidence.

Complete environment dumps are prohibited.

### 23.4 Gold stability

Unicode normalization MUST NOT erase distinctions relevant to the active language.

---

## 24. Compatibility result model

Recommended model:

```python
@dataclass(frozen=True, slots=True)
class GFCapabilityResult:
    capability: str
    state: str
    evidence_level: str
    message: str
    artifact_paths: tuple[Path, ...] = ()
```

```python
@dataclass(frozen=True, slots=True)
class GFCompatibilityResult:
    executable: Path
    executable_sha256: str
    raw_version_text: str
    normalized_version: GFVersion | None
    probe_state: str
    compatibility_tier: str
    platform: str
    capabilities: tuple[GFCapabilityResult, ...]
    rgl_identity: RGLIdentity | None
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    policy_version: str
```

### 24.1 Separation of concerns

`GFCompatibilityResult` describes toolchain compatibility.

It does not describe:

- whether project source compiles;
- whether scenarios pass;
- whether linguistic output is correct;
- whether the project is release-ready by itself.

---

## 25. Persisted evidence

`summary.json` SHOULD contain a structured compatibility section.

Recommended shape:

```json
{
  "gf_compatibility": {
    "policy_version": "1.0.0",
    "probe_state": "identified",
    "raw_version_text": "This is GF version 3.12.0.",
    "normalized_version": "3.12.0",
    "tier": "certified",
    "platform": "windows-x86_64",
    "executable_sha256": "<sha256>",
    "rgl": {
      "identity_kind": "git_commit",
      "identity_value": "<commit>",
      "dirty": false
    },
    "capabilities": {
      "batch_compile": "integration_tested",
      "pgf_build": "integration_tested",
      "parse": "integration_tested",
      "linearize": "integration_tested"
    },
    "warnings": [],
    "blockers": []
  }
}
```

The exact persisted schema must be coordinated with `PERSISTED_SCHEMA_LOCK.md`.

### 25.1 Artifact paths

Raw probe and capability artifacts are run-relative in canonical reports.

### 25.2 Determinism

Capability names and result arrays use deterministic ordering.

---

## 26. Compatibility overrides

Overrides are exceptional and explicit.

Recommended settings:

```text
allow_untested_gf
allow_legacy_gf
skip_version_probe
allow_dirty_rgl
```

### 26.1 Override evidence

Every used override MUST record:

```text
override name
resolved value
source
reason, when supplied
affected operation
```

### 26.2 Release behavior

An override does not automatically grant certification.

Example:

```text
allow_untested_gf = true
```

may allow release-suite execution, but the resulting release remains unverified unless policy explicitly certifies the toolchain.

### 26.3 GUI and CLI parity

Equivalent overrides must produce equivalent behavior through CLI and GUI.

### 26.4 No hidden defaults

Release mode MUST NOT enable compatibility overrides implicitly.

---

## 27. Failure semantics

### 27.1 Unsupported older version

```text
validation_status = ERROR
error_kind = TOOL
compatibility_tier = legacy_unsupported
execution_state = completed
project_validation_started = false
```

### 27.2 Unknown newer version in quick mode

```text
validation_status = determined by required capability results
compatibility_tier = untested_newer
warning = present
```

### 27.3 Unknown newer version in release mode

Default:

```text
validation_status = ERROR
error_kind = TOOL
release_certification = blocked
```

### 27.4 Probe timeout

```text
validation_status = ERROR
error_kind = TIMEOUT
probe_state = timed_out
```

### 27.5 Capability failure

```text
validation_status = ERROR or FAIL according to contract
error_kind = TOOL
failed_capability = <id>
```

A missing tool capability normally indicates an execution/tool compatibility error, not a project linguistic failure.

---

## 28. CLI behavior

Recommended commands:

```text
gf-wordbench gf version
gf-wordbench gf capabilities
gf-wordbench gf check
gf-wordbench gf compatibility
```

Suggested output:

```text
GF executable: C:/tools/gf-3.12/gf.exe
Raw version: This is GF version 3.12.0.
Normalized version: 3.12.0
Compatibility tier: certified
Platform: windows-x86_64
RGL identity: git:<commit>
Required suite: checkpoint
Result: OK
```

Strict check:

```text
gf-wordbench gf check --strict
```

These command names remain recommendations until locked by the CLI reference and implementation.

---

## 29. GUI behavior

The GUI SHOULD show:

- resolved executable;
- raw and normalized version;
- compatibility tier;
- RGL identity status;
- warning or blocker summary;
- capability-check action;
- evidence location.

The GUI MUST NOT maintain an independent compatibility matrix.

It consumes the same compatibility service as the CLI and audit core.

---

## 30. Implementation architecture

Recommended modules:

```text
app/gf/version.py
app/gf/capabilities.py
app/gf/compatibility.py
app/gf/rgl_identity.py
```

Recommended ownership:

| Module | Responsibility |
|---|---|
| `version.py` | probe parsing and normalized version model |
| `capabilities.py` | capability definitions and probes |
| `compatibility.py` | tier policy and decision result |
| `rgl_identity.py` | RGL revision evidence |

### 30.1 Forbidden duplication

The following components MUST NOT implement their own version policy:

```text
compiler
scenario runner
PGF builder
CLI
GUI
reports
```

They consume `GFCompatibilityResult`.

### 30.2 Command adapters

Version-specific command construction belongs in explicit compatibility adapters, not scattered conditionals.

Recommended interface:

```python
class GFCommandAdapter(Protocol):
    def compile_args(...) -> list[str]: ...
    def pgf_args(...) -> list[str]: ...
    def scenario_args(...) -> list[str]: ...
```

---

## 31. Migration from `gf-audit`

The earlier tool already supports:

- executable selection;
- optional `gf --version` probe;
- raw version text in run results;
- a `skip_version_probe` setting.

GF Wordbench must preserve that functioning behavior while replacing its string-only policy.

### 31.1 Migration steps

1. isolate version probing from compilation;
2. preserve stdout and stderr separately;
3. introduce `GFVersion`;
4. introduce `GFCompatibilityResult`;
5. add the support-tier matrix;
6. add capability probes;
7. add RGL identity;
8. persist policy version and evidence;
9. make CLI and GUI consume the same result;
10. block release when the toolchain is uncertified;
11. retain legacy summary loading;
12. add migration tests.

### 31.2 Legacy summaries

A legacy `gf_version` string remains readable.

Migration attempts normalization and records:

```text
source = legacy_summary
capability_evidence = unavailable
```

A historical run cannot be retroactively certified from its version string alone.

### 31.3 Skip-version legacy behavior

Legacy runs that skipped the probe remain:

```text
compatibility_tier = unknown
```

They are not rewritten as compatible.

---

## 32. Testing strategy

Recommended tests:

```text
tests/gf/test_version_parser.py
tests/gf/test_capabilities.py
tests/gf/test_compatibility_policy.py
tests/gf/test_rgl_identity.py
tests/contracts/test_gf_version_contract.py
tests/integration/test_gf_311.py
tests/integration/test_gf_312.py
tests/migrations/test_legacy_gf_version.py
```

### 32.1 Version parser tests

Required cases:

- `GF 3.12`;
- `GF 3.12.0`;
- `This is GF version 3.12.0.`;
- version in stderr;
- empty output;
- unrelated numeric versions;
- multiple plausible versions;
- pre-release;
- build metadata;
- malformed text;
- Unicode output.

### 32.2 Policy tests

- certified 3.12;
- compatible 3.11;
- unsupported 3.10;
- unknown 3.13;
- known-incompatible exact build;
- strict unknown-newer behavior;
- project minimum higher than framework minimum;
- project minimum lower than framework minimum;
- release override remains uncertified.

### 32.3 Capability tests

Use fake executables or mocked process evidence to test:

- help detection;
- missing command;
- command present but smoke test failing;
- timeout;
- nonzero exit;
- UTF-8 output;
- artifact missing;
- cached result invalidation.

### 32.4 Real-GF integration tests

For certified platforms and versions:

- version probe;
- batch compile success;
- batch compile failure;
- GF path handling;
- `.gfo` output;
- `.gfs` execution;
- import with `-retain`;
- parse;
- linearize;
- bounded generation;
- missing-linearization inspection;
- PGF build;
- optimized PGF build;
- paths containing spaces;
- Unicode source and output.

### 32.5 RGL integration tests

- known RGL identity;
- unknown identity;
- dirty checkout;
- required module compile;
- missing RGL module;
- incompatible API use.

---

## 33. Release-certification evidence

A GF Wordbench framework release SHOULD publish or preserve:

```text
compatibility-policy version
GF core versions tested
platforms tested
RGL identities tested
capability suites executed
fixture grammar revision
test results
known incompatibilities
```

An active language release SHOULD preserve:

```text
GFCompatibilityResult
project configuration
RGL identity
release scenario results
PGF manifest entry
```

---

## 34. Updating the compatibility baseline

The compatibility baseline must be reviewed when:

- upstream GF publishes a release;
- the project changes minimum version;
- a new platform is added;
- command behavior changes;
- a new required capability is introduced;
- RGL packaging changes;
- a diagnostic format changes materially;
- a known regression is discovered;
- a certified version is retired.

Review checklist:

```text
[ ] Official release identified
[ ] Release notes reviewed
[ ] Version parser verified
[ ] Help/capability probes reviewed
[ ] Compile fixture passed
[ ] Scenario fixture passed
[ ] PGF build passed
[ ] RGL compatibility reviewed
[ ] Windows path behavior tested
[ ] Other certified platforms tested
[ ] Diagnostics reviewed
[ ] Gold normalization reviewed
[ ] Compatibility matrix updated
[ ] Known incompatibility registry updated
[ ] Policy version updated
[ ] Documentation updated
```

---

## 35. Drift indicators

Compatibility drift exists when:

- one component parses version differently;
- CLI and GUI assign different tiers;
- a command flag is version-gated in only one caller;
- release mode accepts an unknown version silently;
- the recorded executable differs from the executed executable;
- RGL identity is omitted from a release run;
- a newer GF changes output and normalization hides it;
- a capability is assumed from version without evidence;
- a compatibility override is not recorded;
- a legacy summary is treated as capability-tested;
- reports infer compatibility from prose;
- a known-incompatible build runs without a blocker;
- a project lowers the framework minimum silently;
- a development build is treated as an official release;
- the support matrix changes without tests.

Any indicator requires compatibility review.

---

## 36. Change policy

A change to any of the following is a compatibility-contract change:

- minimum supported GF version;
- certified version line;
- compatibility tier semantics;
- unknown-newer behavior;
- version parser;
- required capability suites;
- RGL identity rules;
- platform certification;
- known-incompatibility registry;
- release override behavior;
- persisted compatibility evidence.

A coordinated change MUST update:

1. compatibility policy;
2. version parser;
3. capability registry;
4. command adapters;
5. project configuration reference;
6. persisted schema when affected;
7. CLI and GUI behavior;
8. report output;
9. unit tests;
10. real-GF integration tests;
11. migration tests;
12. external-tool contract lock;
13. this document;
14. release notes.

---

## 37. Final policy

The initial final GF Wordbench policy is:

```text
Primary certified GF core: 3.12.x
Secondary compatible GF core: 3.11.x
Minimum supported GF core: 3.11.0
Legacy unsupported: 3.10.x and older
Unknown newer versions: development use by capability probe; release blocked by default
RGL compatibility: independently identified and tested
Release certification: version policy + required capabilities + active-project release suite
```

> A recognized version permits evaluation. Only tested capabilities and complete release evidence permit certification.
