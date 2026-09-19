# ADR-0015 — Path-Resolved Single-Language Startup

**ADR ID:** `ADR-0015`
**Title:** Path-Resolved Language Selection and Startup
**Status:** Accepted
**Decision date:** 2026-07-30
**Last reviewed:** 2026-07-30
**Decision owners:** GF Wordbench maintainers
**Implementation status:** Not implemented
**Verification status:** Pending implementation and automated evidence
**Applies to:** GUI and CLI startup, language selection, source-root resolution, GF path resolution, project configuration, application state, bootstrap, validation planning, run construction, reporting, migration and tests
**Alignment authority:** `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`
**Related locks:** `docs/INTERFILE_CONTRACT_LOCK.md`, `docs/PERSISTED_SCHEMA_LOCK.md`, `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
**Related decisions:** `ADR-0001-SINGLE-ACTIVE-LANGUAGE.md`, `ADR-0002-GF-AS-EXECUTION-ENGINE.md`, `ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md`, `ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md`, `ADR-0011-SEPARATE-PORTFOLIO.md`, `ADR-0012-INDEPENDENT-PRODUCTS.md`, `ADR-0014-CATALOG-DRIVEN-LANGUAGE-STARTUP.md`
**Supersedes:** `ADR-0014-CATALOG-DRIVEN-LANGUAGE-STARTUP.md` in full, and the remaining portions of `ADR-0001-SINGLE-ACTIVE-LANGUAGE.md` that make `project/project.toml` or one physical workspace the mandatory language-startup authority
**Preserves:** exactly one resolved language context per running Wordbench session, exactly one language identity per ordinary run, centralized GF path resolution, GF as semantic authority, deterministic validation and no cross-language evidence mixing
**Superseded by:** None

---

## 1. Decision summary

GF Wordbench starts from one explicit filesystem selection supplied by the user:

```text
one GF language directory
or
one GF source file inside that language directory
```

Examples:

```text
C:\mycode\Grammatical_Framework\gf-rgl\src\english
C:\mycode\Grammatical_Framework\gf-rgl\src\english\LangEng.gf
C:\mycode\Grammatical_Framework\gf-rgl\src\english\AdjectiveEng.gf
```

Wordbench uses that selection to construct a bounded **language candidate**. It
then delegates validation to existing Wordbench services instead of maintaining
a second RGL catalog, a second source scanner, a second path resolver or a second
compiler.

The canonical startup sequence is:

```text
create QApplication or CLI request
→ load machine-local application state
→ show the introduction or language-open surface
→ receive one explicit file or directory selection
→ normalize and contain the selected path
→ derive the candidate language directory and RGL source root
→ enumerate candidate GF sources through the existing file-selection service
→ classify standard RGL module candidates from selected filenames
→ resolve the effective GF path through the existing GF path resolver
→ run structural preflight through the existing preflight service
→ construct one immutable ResolvedLanguageContext
→ compose the main Wordbench runtime
→ persist the successful selected path as convenience state
→ expose validation capabilities according to available tools and profiles
```

A successful language load does not require a static language catalog, a
mandatory `language.toml`, a mandatory language bundle, scenarios, gold files,
documentation assets or a successful release build.

Those assets remain available as optional validation profiles and release
contracts. They are not prerequisites for browsing, selecting, scanning or
performing targeted GF compilation against a standard RGL language directory.

The core rule is:

> Wordbench may discover candidate facts from one user-selected path, but every
> executable run uses one explicit, immutable and validated resolved context.

---

## 2. Supersession boundary

### 2.1 ADR-0014 is superseded

`ADR-0014-CATALOG-DRIVEN-LANGUAGE-STARTUP.md` is superseded in full.

The following ADR-0014 decisions no longer govern normal startup:

- `rgl-language-catalog.json` as the exclusive registry of selectable languages;
- a catalog language ID as the only selectable or persisted language identity;
- a mandatory catalog entry for every loadable language;
- a mandatory `wordbench_config` path;
- a mandatory `gf-rgl/wordbench/languages/<ID>/language.toml` bundle;
- catalog-owned ordered search-path parts;
- prohibition of bounded filesystem discovery after explicit user selection;
- prohibition of deriving language candidates from standard RGL module names;
- refusal to load a language that lacks scenarios, inputs, golds or Wordbench
  language-bundle documentation.

ADR-0014 remains in the ADR registry as historical reasoning and must be marked:

```text
Status: Superseded
Superseded by: ADR-0015-PATH-RESOLVED-LANGUAGE-STARTUP.md
```

### 2.2 ADR-0001 is preserved in part

The following ADR-0001 rules remain mandatory:

- a running session has no loaded language or exactly one resolved language;
- an ordinary run has exactly one language identity;
- language identity cannot change while a run is active;
- sources, scenarios, golds, baselines and release evidence from several
  languages cannot be merged into one ordinary run;
- switching language recreates the runtime rather than mutating it in place;
- `gf-portfolio` remains separate and optional;
- Wordbench does not perform portfolio aggregation.

The following workspace-coupled ADR-0001 rules are superseded:

- one language requires one physical Wordbench clone or worktree;
- `project/project.toml` must be loaded before any language can be opened;
- the GUI cannot offer a language selector;
- application state cannot remember a previously selected language path;
- a language must have a complete project documentation and scenario bundle
  before Wordbench can browse or compile its source files.

### 2.3 Decisions preserved without change

This ADR does not weaken:

- GF as the parser, type checker, compiler and module-resolution authority;
- the GF anti-corruption boundary;
- centralized external-process execution;
- separation of static scan and GF compilation;
- deterministic file selection;
- one effective GF path resolution reused by every GF operation in one run;
- read-only normal validation;
- explicit gold-update workflows;
- structured evidence and report ownership.

---

## 3. Context

GF Wordbench already contains the capabilities needed to inspect and validate a
GF language source tree:

```text
filesystem and path validation
source enumeration and filtering
explicit target resolution
module-name extraction from GF filenames
static source scanning
GF path resolution
preflight validation
GF version probing
GF compilation
native .gfs execution
diagnostic normalization
failure classification
run evidence and reports
```

A separate versioned inventory of the entire RGL duplicates facts that Wordbench
can verify directly from the selected source tree. A mandatory language bundle
also creates a second configuration layer before Wordbench can use its existing
source and validation services.

The prior design therefore imposed more configuration than the basic use case
requires.

The basic use case is:

```text
select one standard RGL language directory
→ browse its files
→ scan selected files
→ compile one file or a selected target set
→ inspect diagnostics and evidence
```

For that use case, Wordbench needs one reliable source root and one effective GF
module search path. It does not need a global registry of every language in the
RGL checkout.

---

## 4. Decision drivers

This decision prioritizes:

1. reuse of existing Wordbench capabilities;
2. one user-provided path instead of several machine-specific paths;
3. no duplicated scanner, path resolver, compiler or diagnostic parser;
4. compatibility with standardized RGL directory and module conventions;
5. bounded and explainable discovery;
6. explicit resolved configuration before execution;
7. support for browsing and static scanning when GF is unavailable;
8. optional advanced validation profiles rather than mandatory bundles;
9. deterministic behavior and reproducible evidence;
10. clear failure and ambiguity handling;
11. one active language per session and per run;
12. minimal migration cost for existing project-based workflows.

---

## 5. Normative terminology

### 5.1 Selected language path

The exact filesystem path explicitly selected by the user or explicitly supplied
through CLI or automation.

It is either:

- a readable directory containing GF language sources; or
- a readable `.gf` file whose parent directory is the candidate language
  directory.

The selected language path is machine-local configuration. It is not a portable
language identity.

### 5.2 Candidate language directory

The directory initially treated as the language source directory.

Resolution rule:

```text
selected directory → that directory
selected .gf file  → the file's parent directory
```

### 5.3 RGL source root

The nearest validated ancestor that contains the selected language directory as
one source subtree and satisfies the supported RGL-root structure contract.

For a standard checkout:

```text
<rgl-root>/src
```

The resolver must not search unrelated drives, user profiles or arbitrary parent
trees after the supported ancestor boundary has been exhausted.

### 5.4 RGL root

The parent of the resolved RGL source root for the standard layout:

```text
<rgl-root>/src
```

A nonstandard layout may be supported only through an explicit path override or
validation profile. It must not be guessed through an unbounded search.

### 5.5 Language candidate

A provisional, non-executable model containing facts observed or derived from
the selected path.

Candidate facts may include:

```text
selected path
candidate language directory
candidate RGL source root
candidate RGL root
selected GF file, when applicable
candidate module suffixes
candidate entrypoints
candidate shared path parts
structural diagnostics
```

A candidate is not yet a run authority.

### 5.6 Resolved language context

The immutable runtime model produced after required structural, path and
containment validation succeeds.

It is the only language authority consumed by the main runtime and ordinary run
construction.

### 5.7 Validation profile

An optional explicit configuration that adds project-specific policy, including:

```text
source include and exclude rules
required checkpoints
required entrypoints
scenarios
inputs
golds
release targets
expected artifacts
release gates
project-specific documentation contracts
```

An existing `project/project.toml` may serve as a validation profile after its
contract is migrated to distinguish profile facts from startup facts.

### 5.8 Capability status

A resolved language may expose different capabilities according to available
configuration and tools.

Canonical capability classes are:

```text
source-ready
scan-ready
compile-ready
scenario-ready
release-ready
```

A missing optional capability must not invalidate unrelated capabilities.

### 5.9 Language switch

A controlled transition that ends the current language runtime and returns to
the language-open surface before resolving another selected path.

It is not an in-place mutation of active run configuration.

---

## 6. User input contract

### 6.1 Exactly one primary selection

Normal language startup asks the user for one path.

Accepted forms:

```text
<rgl-root>/src/<language-directory>
<rgl-root>/src/<language-directory>/<module>.gf
```

The GUI must offer both file and directory selection. The CLI must accept the
same semantic input.

### 6.2 Preferred selection

A language directory is the preferred general-purpose input because it supports
browsing, inventory and arbitrary target selection.

A `.gf` file is the preferred focused input when the user intends to inspect or
compile one specific module.

Selection of a non-entrypoint file such as:

```text
AdjectiveEng.gf
```

is valid. It identifies a focused target inside the English language directory;
it does not make that module the release entrypoint.

### 6.3 Additional paths

Wordbench may request an additional path only when required resolution cannot be
completed safely, for example:

- the RGL source root cannot be determined;
- the selected directory contains no eligible GF sources;
- several source roots are equally plausible;
- a required external path is outside the resolved RGL source root;
- a missing module has several exact filesystem matches;
- the user explicitly chooses a nonstandard layout.

The interface must identify the missing fact and explain why another selection
is required.

### 6.4 No hidden selection

Wordbench must not silently select:

- the first directory returned by filesystem enumeration;
- the newest modified language directory;
- a fuzzy filename match;
- a language inferred from a previous run directory;
- a sibling language because the selected language failed;
- an arbitrary module when several candidates have equal rank.

---

## 7. Canonical startup flow

### 7.1 Interactive GUI flow

```text
create QApplication
→ load local application state
→ show introduction window
→ choose “Open last language”, “Choose language path” or “Quit”
→ obtain explicit selected path
→ invoke LanguageProbeService
→ present ambiguity or remediation when required
→ publish ResolvedLanguageContext
→ compose main runtime
→ show main window
```

The main runtime must not exist before a resolved language context is available.

### 7.2 CLI flow

```text
parse explicit language-path argument
→ invoke the same LanguageProbeService
→ render the same structured diagnostics
→ publish ResolvedLanguageContext
→ invoke requested validation use case
```

CLI and GUI must not implement separate inference, path or validation rules.

### 7.3 Last-language flow

Application state may remember the last successfully resolved selected path.

The introduction window may expose:

```text
Open last language
```

Selecting that action reruns full path and containment validation. Wordbench does
not trust the remembered result or automatically recreate a prior context.

A missing or stale path produces an explicit diagnostic and returns to language
selection.

### 7.4 Language switching

Switching is allowed only when no run is active.

Canonical transition:

```text
request switch
→ verify no active run
→ dispose current runtime and workers
→ return to introduction window
→ resolve another explicit selected path
→ compose a new runtime
```

No selected files, GF path entries, targets, scenarios, previous-run baselines or
report state may survive from the old language runtime.

---

## 8. Language probe ownership

### 8.1 New application service

One bounded application service coordinates discovery:

```text
LanguageProbeService
```

Recommended ownership:

```text
src/gf_wordbench/projects/languages/probe.py
```

The exact module layout may differ, but the ownership remains under the
`projects` functional module because the service resolves active language
identity and source boundaries.

### 8.2 Service responsibility

The probe owns only:

- interpreting the explicit selected path;
- coordinating existing public services;
- ranking standard RGL module candidates;
- collecting resolution diagnostics;
- deciding when user input is required;
- constructing the candidate model;
- publishing the final resolved language context.

### 8.3 Service non-responsibility

The probe must not own or duplicate:

- recursive source-selection rules;
- include or exclude filtering;
- path normalization algorithms already owned by the path resolver;
- GF command construction;
- subprocess execution;
- GF parsing, type checking or module semantics;
- static scan rules;
- diagnostic normalization;
- scenario execution;
- report formatting;
- application-state persistence implementation.

### 8.4 Public-contract rule

The probe may use only public contracts from other functional modules.

It must not import private helpers from:

```text
validation.selection
validation.compilation
runs.preflight
diagnostics
reporting
```

When a required capability exists only as a private helper, its owning module
must first expose a reviewed public operation rather than allowing cross-module
private imports.

---

## 9. Reuse of existing Wordbench services

### 9.1 File selection

The existing file-selection service owns:

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
module-name expectation from filenames
exclusion reasons
```

The probe constructs a minimal candidate selection request and invokes the
public selector.

It must not perform an independent recursive inventory of GF source files.

### 9.2 Module-name extraction

The existing public module-name extraction operation is reused for `.gf`
filenames.

The probe may classify names such as:

```text
LangEng
GrammarEng
AllEng
AdjectiveEng
```

It does not parse full GF source syntax to reproduce GF module semantics.

### 9.3 GF path resolution

The existing centralized GF path resolver remains the sole owner of the
effective path supplied to GF.

The probe supplies candidate path requirements and provenance. The resolver
owns:

- canonicalization;
- allowed-root enforcement;
- alias resolution;
- existence checks;
- deduplication;
- ordering;
- native serialization;
- effective-path evidence.

Compilation, scenarios and PGF construction consume the same resolution.

### 9.4 Preflight

The existing preflight service validates the resolved context before an
executable run.

Preflight remains responsible for checks such as:

```text
source directory exists and is readable
selected target exists and is readable
GF executable availability when required
GF path entries exist according to policy
output roots are valid
paths remain inside approved roots
run configuration is complete for the requested capability
```

The probe may perform structural preflight to load a source-ready context.
Capability-specific preflight occurs before compilation, scenario execution or
release work.

### 9.5 Compilation

The existing compiler remains responsible for:

```text
GF executable invocation
ordered arguments
effective GF path
working directory
timeout
cancellation
stdout and stderr
exit code
generated artifacts
diagnostic extraction
raw evidence
```

The probe does not implement a trial compiler.

An optional “Verify with GF” startup action may invoke the normal compiler on an
explicit candidate target. Its result is ordinary structured validation evidence,
not a hidden discovery mechanism.

### 9.6 Diagnostics

Existing diagnostic normalization and classification process GF errors.

The probe may consume a typed missing-module or path diagnostic when the
diagnostics module exposes one. It must not scrape console text independently
when a canonical parser already owns that output.

### 9.7 Reporting

Existing reporting projects the resolved language and path evidence from the run
result.

The probe does not write reports directly.

---

## 10. Structural resolution

### 10.1 Path normalization

The selected path is resolved using the existing filesystem abstraction and
path-security rules.

Required checks include:

- no NUL characters;
- supported absolute or explicitly based path semantics;
- existing readable path;
- regular `.gf` file or readable directory;
- symlink resolution according to the existing security policy;
- no escape from the approved root after a root is established.

### 10.2 Candidate language directory

```text
if selected path is a .gf file:
    candidate language directory = selected path parent
else:
    candidate language directory = selected path
```

The directory is then passed to the selector using a deterministic source glob
and the standard source exclusions owned by the selector.

### 10.3 RGL source-root detection

The probe walks upward only through ancestors of the selected path.

A candidate source root is accepted when:

1. it contains the selected language directory;
2. its layout satisfies the supported RGL source-root contract;
3. required resolved paths remain within the accepted root;
4. no nearer ancestor satisfies the same contract more precisely.

The standard accepted result is:

```text
<rgl-root>/src
```

The probe does not enumerate all languages to establish this root.

### 10.4 Nonstandard source trees

A source tree that is not a standard RGL checkout may still be usable as a GF
project, but it must use an explicit validation profile or explicit GF-path
configuration.

The standard-language probe must not invent a fake RGL root for an unrelated
source tree.

---

## 11. Language identity

### 11.1 Portable language key

The portable base identity is the selected language directory relative to the
resolved RGL source root, normalized with `/`.

Example:

```text
language_key = "english"
```

Run evidence may namespace this value when required by a persisted schema:

```text
rgl:english
```

The exact serialized field name is governed by the persisted-schema update.

### 11.2 Module suffix

The module suffix is a separate optional fact.

For English:

```text
module_suffix = "Eng"
```

The suffix may be accepted when one candidate is uniquely supported by standard
module roles found in the selected language directory.

The suffix must not be derived only by title-casing or abbreviating the directory
name.

### 11.3 Display name

A display name is presentation metadata. It may initially use a safe rendering of
the directory name or an explicit validation-profile value.

It must not control path or module resolution.

### 11.4 Identity precedence

Runtime identity uses:

```text
portable language key
+ resolved source root evidence
+ optional module suffix
```

Application-state labels, translated names and prior-run directory names do not
override this identity.

---

## 12. Standard RGL module classification

### 12.1 Purpose

Module classification helps the user choose meaningful validation targets. It is
not a replacement for GF dependency resolution.

### 12.2 Candidate roles

The probe may recognize standard filename roles:

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

The list is a classification vocabulary, not a requirement that every language
contain every role.

### 12.3 Candidate entrypoint order

When candidates exist for one unambiguous suffix, the default presentation order
is:

```text
Lang<Suffix>.gf
Grammar<Suffix>.gf
All<Suffix>.gf
```

This order expresses likely user intent only.

It does not declare that:

- every language has all three modules;
- `All` is always release-authoritative;
- `Grammar` is always preferable to a language-specific profile;
- a selected non-entrypoint file must be replaced automatically.

### 12.4 Focused file selection

When the user selected a specific `.gf` file, that file remains the focused
target.

Wordbench may additionally present detected entrypoint candidates, but it must
not silently replace the selected target.

### 12.5 Ambiguous suffixes

When several suffixes have equal support, the probe returns a structured
ambiguity result.

The user may then:

- choose one detected module group;
- select a specific `.gf` file;
- load an explicit validation profile;
- cancel.

No fuzzy or first-match rule is permitted.

---

## 13. GF path construction

### 13.1 Single resolver

Only the existing GF path resolver constructs the effective path.

The language probe supplies path requirements and provenance but does not
concatenate a command-line `-path` string.

### 13.2 Initial candidate path

For a standard RGL language, candidate requirements may include:

```text
selected language directory
standard shared RGL aliases supported by the existing alias registry
explicit path directives or profile requirements supported by existing contracts
```

Only existing directories are accepted according to required or optional path
policy.

### 13.3 No all-language path

Wordbench must not append every directory beneath the RGL source root.

That behavior would permit accidental cross-language module shadowing and make
results depend on directory contents unrelated to the selected language.

### 13.4 GF remains authoritative

GF owns module dependency resolution from the effective path and source-local GF
semantics.

Wordbench does not build a complete GF dependency graph during startup.

### 13.5 Missing-module assistance

When canonical diagnostics identify one missing module, Wordbench may perform a
bounded exact-name search beneath the resolved RGL source root.

Rules:

```text
zero exact matches
    report module absent from the resolved source root

one exact match
    present the containing directory as a remediation candidate

multiple exact matches
    present an ambiguity and require user choice
```

Automatic remediation is permitted only when:

- the match is exact;
- the path is inside the approved RGL source root;
- the path resolver validates it;
- the addition is recorded with provenance;
- the operation is bounded;
- the user requested automatic resolution or confirms the proposal.

The resolver must not repeatedly add directories without limit.

Recommended bounds:

```text
maximum additions per resolution attempt: 10
no directory added more than once
stop on ambiguity
stop when no progress occurs
```

### 13.6 Effective-path evidence

Every GF-backed run records:

- ordered effective path entries;
- each entry's source and provenance;
- required or optional classification;
- normalization and deduplication outcomes;
- omitted missing optional entries;
- selected language directory;
- resolved RGL source root.

---

## 14. Capability model

### 14.1 Source-ready

Requirements:

- selected path is valid;
- language directory is valid and readable;
- at least one eligible `.gf` source is selected;
- source containment is valid;
- language identity can be recorded.

Available operations:

```text
browse sources
select targets
view source metadata
compute fingerprints
```

### 14.2 Scan-ready

Requirements:

- source-ready;
- static scanner available;
- selected files satisfy scanner input contracts.

A GF executable is not required.

### 14.3 Compile-ready

Requirements:

- source-ready;
- GF executable resolved;
- effective GF path valid;
- explicit compile target set available;
- compilation preflight succeeds.

### 14.4 Scenario-ready

Requirements:

- compile-ready or otherwise GF-execution-ready according to scenario policy;
- explicit scenario registry or profile;
- scenario files and required inputs exist;
- scenario trust and path policy succeeds.

### 14.5 Release-ready

Requirements:

- explicit validation profile;
- required entrypoints and artifacts declared;
- required scenarios and golds declared where policy requires them;
- release gates configured;
- all release validation succeeds.

### 14.6 Capability isolation

Failure of one capability does not erase another valid capability.

Examples:

```text
GF executable missing
→ source-ready and scan-ready may remain available
→ compile-ready is unavailable

no scenarios configured
→ compilation remains available
→ scenario-ready and release-ready are unavailable

no release profile
→ ordinary source validation remains available
→ release readiness is not claimed
```

---

## 15. Optional validation profiles

### 15.1 Profile purpose

Advanced project policy remains explicit and versioned.

A validation profile may define:

```text
project identity extensions
source filters
entrypoints
checkpoints
GF path requirements
scenarios
inputs
golds
PGF targets
expected artifacts
release gates
known limitations
project-specific documentation
```

### 15.2 Existing project.toml

Existing `project/project.toml` remains supported through migration as an
explicit validation profile.

It is no longer required to open a language directory.

The profile must not contradict the selected source context. Conflicts are
configuration errors, not precedence opportunities.

Examples of conflicts:

```text
profile source root outside selected language context
profile language identity disagrees with resolved identity
profile target escapes approved roots
profile GF path selects another language directory
profile scenario or gold path belongs to another language
```

### 15.3 Profile discovery

A profile is loaded only when:

- explicitly selected by the user;
- explicitly supplied by CLI or automation; or
- referenced by a reviewed application configuration contract.

Wordbench must not search arbitrary ancestors and silently adopt the first
`project.toml` it finds.

### 15.4 Language bundles

A `gf-rgl/wordbench/languages/<ID>/` bundle may exist as one optional profile and
asset layout, but it is not a required startup contract.

Wordbench must not infer or require such a path merely because a module suffix is
known.

### 15.5 Template status

A generic language-project template may continue to support creation of advanced
validation assets.

It does not participate in normal path-resolved startup and is not rendered at
runtime.

---

## 16. Application state

### 16.1 Local convenience values

Application state may remember:

```text
last_selected_language_path
last_selected_validation_profile
last_rgl_root, when separately configured
```

These are machine-local convenience values.

### 16.2 State is not authority

Application state must not persist a complete executable resolved context as an
authority for future runs.

On every load, Wordbench revalidates:

- selected-path existence;
- selected-path type;
- language-directory containment;
- RGL source-root resolution;
- relevant profile paths;
- capability-specific configuration.

### 16.3 Failed state writes

A successful language load remains successful when best-effort state persistence
fails.

The failure is reported as a warning according to the application-state
contract.

### 16.4 Privacy

Absolute machine paths are stored only in local application state and permitted
local environment evidence.

Portable artifacts use relative identities and redaction rules defined by the
reporting and persisted-schema contracts.

---

## 17. ResolvedLanguageContext

### 17.1 Required base fields

The immutable base context contains at least:

```text
language_key
selected_path
selected_path_kind
language_directory
rgl_source_root
rgl_root, when resolved
selected_file, when applicable
module_suffix, when unambiguous
available_entrypoints
focused_target, when applicable
selected_source_inventory or stable inventory reference
GF path requirements
structural diagnostics
capability statuses
resolution provenance
```

### 17.2 Optional profile fields

When an explicit profile is loaded, the context may also contain:

```text
profile identity and digest
source filters
configured checkpoints
configured entrypoints
scenario registry
input and gold roots
release targets
release policy
project documentation references
```

### 17.3 Immutability

After publication, no component mutates the context.

A change to selected path, GF path requirements, validation profile or language
identity requires a new resolution and a new runtime.

### 17.4 Runtime authority

The resolved context is the single provider for language and source facts used by:

```text
main-window view models
run construction
file selection
static scan planning
GF path resolution
compilation planning
scenario discovery
PGF construction
previous-run eligibility
reporting and manifests
```

Consumers must not independently rediscover the language directory or source
root.

---

## 18. Run construction and evidence

### 18.1 Run gating

Run construction requires:

- one published resolved language context;
- a capability status compatible with the requested mode;
- successful capability-specific preflight;
- one immutable effective configuration snapshot.

### 18.2 Language-scoped outputs

Run paths and previous-run selection remain scoped by one portable language
identity.

No previous run is eligible when its language identity, selected source context
or relevant configuration digest is incompatible with the current run policy.

### 18.3 Required evidence

Each completed run records enough information to reproduce and attribute the
resolved source context:

```text
portable language key
module suffix, when available
selected path kind
selected source path as permitted local evidence
language directory relative to RGL source root
RGL source-root evidence
effective GF path and provenance
focused target or target-set identity
validation-profile identity and digest, when used
resolution diagnostics
capability status used by the run
```

### 18.4 No inference from run artifacts

A prior run may help comparison after compatibility checks. It must not become a
startup selector or source-root authority.

---

## 19. Error and ambiguity model

### 19.1 Result types

Language resolution produces a typed result:

```text
resolved
needs_user_input
invalid_selection
unsupported_layout
capability_unavailable
internal_error
```

### 19.2 Required diagnostic content

A resolution diagnostic includes:

```text
stable code
severity
stage
field or subject
human-readable message
technical detail
remediation
relevant path, when permitted
candidate choices, when applicable
```

### 19.3 Representative failures

```text
selected path does not exist
selected path is unreadable
selected file is not .gf
selected directory contains no eligible GF sources
RGL source root cannot be determined
path escapes approved root after resolution
module suffix is ambiguous
no standard entrypoint candidate exists
GF executable unavailable
required GF path entry missing
missing module has no exact match
missing module has several exact matches
validation profile conflicts with selected language
```

### 19.4 No false success

Structural resolution does not claim compilation success.

Compilation success does not claim scenario readiness.

Scenario success does not claim release readiness without an explicit release
profile and gates.

---

## 20. Security and safety

### 20.1 Read-only normal startup

Language probing and normal validation are observational.

They must not:

- modify GF source files;
- generate or rewrite a catalog;
- generate a language bundle;
- rewrite project configuration;
- update gold files;
- create files inside the RGL source tree;
- execute arbitrary shell fragments;
- follow unbounded filesystem searches;
- accept path escapes.

### 20.2 External execution

All GF execution continues through the approved process boundary and GF adapter.

The probe never invokes `subprocess` directly.

### 20.3 Bounded discovery

Discovery is restricted to:

- the explicit selected path;
- its ancestors while locating the supported source root;
- the selected language directory for source inventory;
- the resolved RGL source root for bounded exact-name remediation.

### 20.4 Symlinks and containment

Resolved filesystem identities, not lexical path strings alone, determine
containment according to the existing path-security contract.

### 20.5 User-controlled source

GF source and `.gfs` profiles are project-controlled inputs. Existing trust,
timeout, cancellation, output-size and evidence controls remain mandatory.

---

## 21. Catalog and scanner retirement

### 21.1 Runtime catalog removal

`rgl-language-catalog.json` is no longer a startup or runtime authority.

It may be removed from the product package after migration.

### 21.2 Optional inventory tooling

A separately invoked maintenance tool may still generate an RGL inventory for:

- diagnostics;
- documentation review;
- repository analysis;
- test fixtures;
- migration assistance.

Such output is:

```text
non-authoritative
regenerable
not read by normal startup
not sufficient to create a resolved context
```

### 21.3 No duplicate production scanner

A maintenance inventory tool must reuse approved filesystem and source-selection
contracts where practical. It must not become a second production language
resolver.

### 21.4 Removal candidates

After implementation and migration, review removal or repurposing of:

```text
root runtime rgl-language-catalog.json
catalog runtime adapters and schemas
catalog-only startup services
mandatory language-bundle loader
catalog generator scripts used by normal startup
catalog-specific app-state fields
catalog-specific tests and documentation
```

Removal must follow the normal deprecation and compatibility process.

---

## 22. Architecture and dependency direction

### 22.1 Functional ownership

| Responsibility | Owner |
|---|---|
| Selected-path intent | GUI or CLI entrypoint |
| Language candidate orchestration | `projects` application service |
| Source enumeration and filtering | `validation.selection` |
| Filesystem implementation | approved filesystem adapter |
| GF path resolution | GF anti-corruption adapter |
| Structural and run preflight | `runs` preflight/application services |
| GF compilation | `validation.compilation` through `GfToolPort` |
| Diagnostic parsing and normalization | `diagnostics` |
| Run lifecycle and context snapshot | `runs` |
| Reports and manifests | `reporting` |
| Last selected path | `state` repository |
| UI rendering and user choice | GUI entrypoint |

### 22.2 Dependency direction

```text
entrypoints
    → language probe application service
        → public selection port/service
        → public GF-path resolution port
        → public preflight service
        → public diagnostic models

bootstrap
    → composes implementations

language probe
    ✗ does not import GUI widgets
    ✗ does not import process adapters directly
    ✗ does not write reports
    ✗ does not mutate application state directly
```

### 22.3 No general service container

The implementation should use explicit, small dependency injection. This decision
does not authorize a general runtime service locator.

---

## 23. GUI requirements

### 23.1 Introduction surface

Every interactive launch shows the introduction surface before the main runtime.

Minimum actions:

```text
Open last language
Choose language directory or GF file
Configure GF executable or environment, when needed
Quit
```

### 23.2 Probe presentation

The GUI presents:

- selected path;
- resolved language directory;
- portable language key;
- module suffix when available;
- detected entrypoint candidates;
- capability statuses;
- warnings and remediation;
- exact ambiguities requiring a choice.

### 23.3 No GUI-owned inference

Widgets and view models do not enumerate source files, infer suffixes, resolve GF
paths or launch GF directly.

### 23.4 Background work

Potentially expensive inventory or GF verification runs through the existing
worker, cancellation and fatal-error contracts.

The base probe should remain bounded and responsive.

---

## 24. CLI and automation requirements

### 24.1 Equivalent input

CLI and automation accept the same selected-path semantics as the GUI.

The exact command names are owned by the command registry, but supported use
cases include:

```text
probe one language path
open or validate one language path
run one validation mode against one language path
load one optional validation profile
```

### 24.2 Structured output

Probe results must have a structured representation suitable for tests and
automation.

Human-readable output is a projection of that result.

### 24.3 Noninteractive ambiguity

In noninteractive mode, unresolved ambiguity is an explicit error unless the
caller supplies the missing choice.

Automation must not accept an implicit first candidate.

---

## 25. Migration

### 25.1 Documentation migration

Required coordinated updates include at least:

```text
docs/decisions/ADR-0014-CATALOG-DRIVEN-LANGUAGE-STARTUP.md
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/README.md
docs/PRODUCT_OVERVIEW.md
docs/SCOPE_AND_NON_GOALS.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/EXECUTION_FLOW.md
docs/architecture/DATA_MODEL.md
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/CONFIGURATION_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/gf/GF_PATH_RESOLUTION.md
docs/usage/GUI_REFERENCE.md
docs/usage/CLI_REFERENCE.md
docs/usage/QUICK_START.md
docs/validation/FILE_SELECTION.md
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/VALIDATION_PIPELINE.md
docs/release/MIGRATION_AND_DEPRECATION.md
```

### 25.2 State migration

Catalog-specific state such as:

```text
last_language_id
```

migrates to path-based convenience state such as:

```text
last_selected_language_path
```

Migration must preserve unrelated application preferences.

A stale catalog ID without a corresponding remembered path does not trigger a
filesystem-wide search. The user is asked to select a language path.

### 25.3 Existing project migration

Existing project-based workflows continue through an explicit validation profile.

Migration steps conceptually are:

```text
load existing project.toml explicitly
→ resolve its source directory
→ validate it against the selected language context
→ preserve scenarios, golds and release policy
→ stop treating it as mandatory application-startup authority
```

### 25.4 Catalog-era bundle migration

Existing language bundles may be retained as optional validation profiles and
asset directories.

They are not automatically deleted. Their configuration must be converted or
adapted to the optional-profile contract before use.

### 25.5 Compatibility period

A temporary compatibility adapter may accept the former catalog selection and
translate it into an explicit selected path.

Rules:

- compatibility behavior is opt-in or version-bounded;
- the adapter emits deprecation evidence;
- the adapter does not preserve catalog authority inside the resolved context;
- new GUI and CLI flows use path selection directly;
- removal criteria and version are documented.

---

## 26. Consequences

### 26.1 Benefits

- users provide one path instead of configuring a catalog and bundle;
- Wordbench directly serves its primary source-browsing and validation purpose;
- existing selection, path, preflight, compilation and diagnostic services are
  reused;
- source truth remains the checked-out GF code and explicit optional profile;
- new or locally modified RGL languages can be opened without editing a central
  registry;
- missing optional scenarios or golds do not block source work;
- browsing and static scan remain usable without GF;
- path resolution and external execution remain centralized;
- ambiguity is visible and reviewable;
- runtime state remains single-language and deterministic;
- global catalog drift is eliminated from normal startup.

### 26.2 Costs

- language discovery becomes a runtime application use case after explicit user
  selection;
- candidate ranking and ambiguity models require new tests;
- persisted identity changes from catalog ID to path-resolved identity;
- existing catalog and bundle documentation requires coordinated migration;
- nonstandard RGL layouts may need an explicit profile;
- exact missing-module remediation requires a bounded source index operation;
- GUI startup gains a language-probe step and capability presentation;
- previous-run compatibility rules require updated identity and digest logic.

### 26.3 Risks

- overexpanding discovery could recreate an implicit global scanner;
- direct use of private selection helpers could violate module boundaries;
- automatic path additions could hide ambiguous module ownership;
- directory-derived presentation names could be mistaken for identity;
- partial capability may be misreported as full validation readiness;
- a compatibility adapter could accidentally keep catalog behavior alive.

### 26.4 Mitigations

- discovery begins only from one explicit selected path;
- searches are bounded to approved roots;
- the probe coordinates public services rather than duplicating them;
- capability statuses are explicit;
- GF-backed readiness requires normal preflight and execution;
- exact ambiguity fails closed;
- all path additions record provenance;
- architecture tests prohibit duplicate resolver and process behavior;
- migration adapters have explicit removal criteria.

---

## 27. Alternatives rejected

### 27.1 Static global language catalog

Rejected as the normal startup authority because it duplicates filesystem facts,
requires maintenance for every language addition or local change, and prevents
Wordbench from opening a valid standard language until a separate registry is
edited.

A generated catalog may remain a maintenance report only.

### 27.2 Mandatory language bundle

Rejected for basic startup because browsing, selection, scanning and targeted
compilation do not require scenarios, golds or language-specific Wordbench
documentation.

Optional profiles remain supported for advanced validation and release policy.

### 27.3 User configures every GF path directory

Rejected because the user should not need to know or enter all shared RGL paths.
The existing path resolver and GF diagnostics can resolve and validate the
module-search environment.

### 27.4 Add every RGL source directory to GF path

Rejected because it permits cross-language shadowing, makes results depend on
unrelated directories and hides missing dependency contracts.

### 27.5 New RGL scanner and compiler

Rejected because Wordbench already owns deterministic source selection, GF path
resolution, compilation, diagnostics and evidence. Duplicating those functions
would create drift and architecture violations.

### 27.6 Parse all GF imports in Python

Rejected because GF remains the authoritative parser and module resolver. A
partial Python parser would be incomplete and could disagree with GF semantics.

### 27.7 Automatically choose the only apparent language at launch

Rejected because startup must preserve explicit user intent. The introduction
surface exposes the selected path and any remembered-path action.

### 27.8 Automatically trust the last resolved context

Rejected because files, symlinks, roots, executable configuration and profiles
may change between sessions. Remembered state is revalidated.

### 27.9 Keep project.toml as mandatory startup authority

Rejected because it blocks direct work on a standard RGL language directory and
combines basic source access with optional scenario and release policy.

### 27.10 Let the GUI implement discovery directly

Rejected because CLI, GUI and automation must share one application service and
one set of diagnostics.

---

## 28. Implementation sequence

Recommended order:

1. mark ADR-0014 superseded and align ADR-0001 and the ADR registry;
2. define `LanguageProbeRequest`, candidate, diagnostic and result models;
3. define the minimal immutable `ResolvedLanguageContext` base contract;
4. expose any missing public selection and module-name operations;
5. implement selected-path normalization and candidate language-directory logic;
6. implement bounded RGL source-root detection;
7. coordinate deterministic source enumeration through `SelectionService`;
8. implement standard module-role candidate classification;
9. adapt the centralized GF path resolver to path-resolved language requests;
10. implement structural preflight and capability status computation;
11. add optional GF verification through the normal compiler;
12. implement typed missing-module remediation through canonical diagnostics;
13. migrate application state to remember selected paths;
14. implement the GUI introduction and probe presentation;
15. add CLI and automation parity;
16. adapt existing `project.toml` loading as an optional validation profile;
17. update run construction, previous-run eligibility and evidence schemas;
18. retire catalog runtime code and catalog-specific tests;
19. update coordinated documentation and locks;
20. run two-language switching and no-contamination tests;
21. complete real-GF integration tests on at least two structurally different RGL
    languages.

---

## 29. Verification requirements

### 29.1 Unit tests

Required unit coverage includes:

```text
directory selection
.gf file selection
non-.gf file rejection
missing path
unreadable path
candidate language-directory derivation
nearest valid RGL source-root resolution
unsupported layout
portable language-key construction
unique module-suffix detection
ambiguous module-suffix detection
entrypoint candidate ordering
focused target preservation
capability-status computation
bounded exact missing-module search
zero, one and multiple missing-module matches
state migration
```

### 29.2 Contract tests

Required contracts include:

```text
probe uses public SelectionService contract
probe does not duplicate selection ordering or filtering
one GFPathResolution is reused across GF consumers
probe does not invoke subprocess directly
GUI and CLI project equivalent probe requests
application state is convenience only
optional profile conflicts fail explicitly
resolved context is immutable
run construction requires one context
```

### 29.3 Architecture tests

Architecture tests must verify:

```text
projects language probe does not import GUI
projects language probe does not import process adapters
projects language probe does not import reporting writers
entrypoints do not enumerate GF sources directly
no second production path resolver exists
no second production GF compiler exists
no runtime catalog reader participates in normal startup
no hard-coded language ID or directory appears in generic framework code
private helpers are not imported across functional-module boundaries
```

### 29.4 Integration tests

At minimum:

```text
open standard English directory
open one English .gf file
browse and static-scan without GF available
compile selected English target with real GF
open a language requiring a shared family directory
resolve one exact missing-module remediation
reject ambiguous missing-module remediation
load an existing project.toml as optional profile
switch from English to a second language without path contamination
reject a language switch during an active run
reopen the remembered path after restart
fail safely when remembered path is stale
```

### 29.5 Evidence tests

Finalized run evidence must prove:

- one portable language identity;
- one selected source context;
- one effective GF path and provenance;
- one target set;
- one optional validation-profile identity when present;
- no path or target contamination from a previous language runtime.

---

## 30. Acceptance criteria

This ADR is implemented only when all of the following are true:

```text
[ ] GUI always starts at the introduction window
[ ] user can select one language directory or one .gf file
[ ] normal startup does not require rgl-language-catalog.json
[ ] normal startup does not require language.toml
[ ] normal startup does not require scenarios, golds or language docs
[ ] selected-path discovery is bounded and path-contained
[ ] source enumeration is delegated to the existing selection service
[ ] module names use the existing public extraction contract
[ ] GF path is resolved once by the existing centralized resolver
[ ] GF execution uses the existing process and compiler boundary
[ ] canonical diagnostics are reused rather than reparsed independently
[ ] source-ready and scan-ready operation works without GF installed
[ ] compile-ready status requires GF-specific preflight
[ ] optional validation profiles remain supported
[ ] existing project.toml can be loaded explicitly as a profile
[ ] one immutable ResolvedLanguageContext gates main runtime creation
[ ] one language identity is recorded per ordinary run
[ ] switching language recreates the runtime
[ ] switching is impossible during an active run
[ ] previous-run comparison is language-context compatible
[ ] application state remembers only convenience paths and preferences
[ ] stale remembered paths fail safely
[ ] runtime catalog code is removed or quarantined from normal startup
[ ] architecture tests prohibit duplicate selection, path and process behavior
[ ] GUI and CLI probe parity is tested
[ ] two-language end-to-end replacement passes with no contamination
[ ] real-GF integration passes for at least two RGL language structures
[ ] all coordinated documents and locks are aligned
```

Documentation presence alone does not establish implementation or verification.

---

## 31. Required documentation alignment

The following documents must be updated before this ADR is considered adopted by
the product documentation set:

```text
docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md
docs/decisions/ADR-0014-CATALOG-DRIVEN-LANGUAGE-STARTUP.md
docs/decisions/README.md
docs/PRODUCT_OVERVIEW.md
docs/SCOPE_AND_NON_GOALS.md
docs/REPOSITORY_STRUCTURE.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/COMPONENT_MAP.md
docs/architecture/EXECUTION_FLOW.md
docs/architecture/DATA_MODEL.md
docs/architecture/PRODUCT_BOUNDARIES.md
docs/architecture/IMPLEMENTATION_ALIGNMENT.md
docs/configuration/CONFIGURATION_OVERVIEW.md
docs/configuration/CONFIGURATION_REFERENCE.md
docs/configuration/ENVIRONMENT_AND_PATHS.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/gf/GF_PATH_RESOLUTION.md
docs/usage/GUI_REFERENCE.md
docs/usage/CLI_REFERENCE.md
docs/usage/QUICK_START.md
docs/reference/COMMAND_REFERENCE.md
docs/reference/TERMINOLOGY_REFERENCE.md
docs/validation/FILE_SELECTION.md
docs/validation/VALIDATION_OVERVIEW.md
docs/validation/VALIDATION_PIPELINE.md
docs/validation/COMPILATION_VALIDATION.md
docs/release/MIGRATION_AND_DEPRECATION.md
docs/development/CODEBASE_GUIDE.md
docs/development/TESTING.md
```

The correction ledger and documentation map must record the coordinated change.

---

## 32. Reconsideration triggers

Reconsider this decision only when evidence shows that one or more of the
following is true:

- standard RGL source layouts cannot be identified reliably from an explicit
  selected path;
- bounded resolution cannot provide deterministic behavior across supported
  platforms;
- existing Wordbench selection and GF path services cannot expose suitable
  public contracts without architectural harm;
- path-resolved identity cannot support safe previous-run comparison;
- users require a centrally administered allowlist for security or deployment;
- a future official RGL manifest becomes stable, versioned and authoritative;
- startup probe cost becomes unacceptable for supported repository sizes;
- supported non-RGL projects require a distinct product mode.

A future official manifest may optimize or verify discovery. It must not silently
replace explicit selected-path intent or the resolved-context boundary without a
new ADR.

---

## 33. Governing rule

> The user selects one source location. Wordbench resolves it through its existing
> selection, path, preflight, GF and diagnostic boundaries. Discovery may propose;
> only one explicit immutable resolved context may execute.
