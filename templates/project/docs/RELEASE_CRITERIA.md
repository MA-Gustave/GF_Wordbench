# GF Wordbench Project Template — Release Criteria

**Document ID:** `GF-WB-TEMPLATE-PROJECT-RELEASE-CRITERIA`  
**Status:** Normative project template  
**Applies to:** A project created from `templates/project/`  
**Template owner:** GF Wordbench maintainers  
**Project owner after initialization:** `<PROJECT_OWNER>`  
**Project identity after initialization:** `<PROJECT_ID>`  
**Target language after initialization:** `<LANGUAGE_NAME>`  
**Canonical target path after initialization:** `project/docs/RELEASE_CRITERIA.md`  
**Release-criteria version:** `1.0`  
**Last template review:** 2026-07-22  

---

## 1. Purpose

This document defines the release acceptance criteria for one GF language project created from the GF Wordbench project template.

It answers:

```text
What must be true before the active project may be declared release-ready?
```

The criteria cover:

- project identity;
- source completeness;
- module ownership;
- interfile contracts;
- dependency integrity;
- linguistic evidence;
- static scanning;
- GF compilation;
- checkpoints;
- native `.gfs` scenarios;
- output markers;
- gold comparisons;
- bounded generation;
- missing-function inspection;
- final PGF construction;
- artifact integrity;
- regression review;
- known issues;
- documentation;
- security;
- reproducibility;
- release approval.

This document is a template.

During project initialization, maintainers must:

1. replace every required placeholder;
2. delete non-applicable example criteria;
3. add project-specific criteria;
4. identify required evidence;
5. align `project.toml`;
6. align scenarios and gold files;
7. align the project contract lock;
8. record the initial baseline run.

An initialized active project must not retain unresolved required placeholders.

---

## 2. Core rule

> A project is release-ready only when every applicable required release gate is `OK`, every required artifact is verified, and every unresolved exception is explicitly approved under a documented release policy.

Compilation of individual files is necessary but insufficient.

A successful release requires the complete configured project surface to agree:

```text
project identity
source modules
providers and consumers
entrypoints
checkpoints
scenarios
gold expectations
research evidence
known issues
release artifact
reports
manifest
```

---

## 3. Relationship to GF Wordbench validation modes

Canonical validation modes:

```text
quick
checkpoint
release
diagnostic
```

This document governs:

```text
release
```

Checkpoint and diagnostic evidence may support release.

They do not replace a final release-mode run.

Recommended command:

```text
gf-wordbench validate \
  --mode release \
  --strict \
  --project-root <PROJECT_ROOT>
```

Windows PowerShell:

```powershell
gf-wordbench validate `
  --mode release `
  --strict `
  --project-root <PROJECT_ROOT>
```

The final project may require explicit environment paths according to installation policy.

---

## 4. Release status

Canonical project release decision:

```text
Ready
Not Ready
Blocked by Error
```

These are human governance labels.

The machine-authoritative run result uses:

```text
overall_status = OK | FAIL | ERROR
```

Mapping:

| Overall run status | Project decision default |
|---|---|
| `OK` | `Ready`, subject to approval and non-automated criteria |
| `FAIL` | `Not Ready` |
| `ERROR` | `Blocked by Error` |

A release approver must not override `FAIL` or `ERROR` by editing report prose.

---

## 5. Gate status

Every release gate uses:

```text
OK
FAIL
ERROR
SKIPPED
```

Meaning:

- `OK`: criterion was evaluated and passed;
- `FAIL`: criterion was evaluated reliably and did not pass;
- `ERROR`: criterion could not be evaluated reliably;
- `SKIPPED`: criterion was intentionally not evaluated.

A required release gate cannot remain `SKIPPED` in a successful release.

Canonical required-gate rule:

```text
required + SKIPPED -> release ERROR
```

---

## 6. Gate applicability

Applicability is separate from gate status.

Canonical applicability:

```text
Required
Conditional
Optional
Not Applicable
```

### 6.1 Required

Must be evaluated in every release.

### 6.2 Conditional

Becomes required when the documented condition is true.

### 6.3 Optional

May be evaluated for additional evidence.

Its failure policy must be explicit.

### 6.4 Not Applicable

The project does not implement the relevant feature.

The project must record why it is not applicable.

Do not use `SKIPPED` to mean permanently not applicable.

---

## 7. Gate severity

Canonical severity:

```text
Release Blocking
Advisory
```

Every required gate is normally:

```text
Release Blocking
```

An optional gate may be advisory.

A gate affecting integrity, security, source correctness, required scenarios, or release artifacts must not be advisory.

---

## 8. Gate identifier format

Canonical identifier:

```text
RC-<DOMAIN>-<NUMBER>
```

Examples:

```text
RC-CONFIG-001
RC-SOURCE-001
RC-COMPILE-001
RC-SCENARIO-001
RC-GOLD-001
RC-PGF-001
RC-DOC-001
RC-SECURITY-001
```

Rules:

- domain is uppercase ASCII;
- number is three digits;
- identifiers are stable;
- identifiers are never reused;
- retired identifiers remain documented where historical traceability matters;
- project-specific gates continue the appropriate domain sequence.

---

## 9. Canonical gate domains

```text
INIT
CONFIG
IDENTITY
SOURCE
ARCH
CONTRACT
DEPENDENCY
RESEARCH
SCAN
COMPILE
CHECKPOINT
SCENARIO
GOLD
MISSING
PARSE
LINEARIZE
GENERATION
MORPH
LEXICON
PGF
ARTIFACT
REGRESSION
STATUS
DOC
SECURITY
REPRO
REPORT
MANIFEST
COMPAT
APPROVAL
```

A project may add a domain when existing domains cannot express the criterion cleanly.

---

## 10. Gate registry summary

The template defines the following baseline registry.

| Gate ID | Criterion | Applicability | Severity | Evidence |
|---|---|---|---|---|
| `RC-INIT-001` | Template initialization complete | Required | Release Blocking | project checker |
| `RC-CONFIG-001` | `project.toml` valid and complete | Required | Release Blocking | schema/config validation |
| `RC-IDENTITY-001` | Project identity consistent | Required | Release Blocking | identifier scan |
| `RC-SOURCE-001` | Required source inventory complete | Required | Release Blocking | source selection |
| `RC-ARCH-001` | Architecture documentation matches source | Required | Release Blocking | documentation review |
| `RC-CONTRACT-001` | Project interfile contracts complete | Required | Release Blocking | contract checker |
| `RC-DEPENDENCY-001` | Dependency map complete and cycle-free | Required | Release Blocking | dependency checker |
| `RC-RESEARCH-001` | Research evidence reviewed | Conditional | Release Blocking | evidence review |
| `RC-SCAN-001` | Static scan policy satisfied | Required | Release Blocking | scan results |
| `RC-COMPILE-001` | Every required source compiles | Required | Release Blocking | per-file compile |
| `RC-CHECKPOINT-001` | Every required checkpoint passes | Required | Release Blocking | checkpoint runs |
| `RC-SCENARIO-001` | Required scenario registry valid | Required | Release Blocking | scenario checker |
| `RC-SCENARIO-002` | Required scenarios pass | Required | Release Blocking | scenario results |
| `RC-GOLD-001` | Required gold files exist | Conditional | Release Blocking | gold registry |
| `RC-GOLD-002` | Required gold comparisons match | Conditional | Release Blocking | normalized comparison |
| `RC-MISSING-001` | Required functions/linearizations complete | Required | Release Blocking | missing-function scenario |
| `RC-PARSE-001` | Required parse cases pass | Conditional | Release Blocking | parse scenario |
| `RC-LINEARIZE-001` | Required linearization cases pass | Required | Release Blocking | linearize scenario |
| `RC-GENERATION-001` | Required generation checks are bounded and pass | Conditional | Release Blocking | generation scenario |
| `RC-MORPH-001` | Required morphology checks pass | Conditional | Release Blocking | morphology scenario |
| `RC-LEXICON-001` | Required release lexicon is complete | Conditional | Release Blocking | lexicon validation |
| `RC-PGF-001` | Final PGF build succeeds | Required | Release Blocking | PGF process result |
| `RC-PGF-002` | Expected PGF exists and is non-empty | Required | Release Blocking | artifact check |
| `RC-ARTIFACT-001` | Required artifacts are registered | Required | Release Blocking | artifact registry |
| `RC-REGRESSION-001` | Regression comparison completed | Required | Release Blocking | compatible baseline diff |
| `RC-REGRESSION-002` | No unapproved regression remains | Required | Release Blocking | regression review |
| `RC-STATUS-001` | Status ledger has no blocking entry | Required | Release Blocking | ledger review |
| `RC-DOC-001` | Required project documentation complete | Required | Release Blocking | documentation checker |
| `RC-SECURITY-001` | Scenario and path security checks pass | Required | Release Blocking | security checker |
| `RC-REPRO-001` | Release run is reproducible and current | Required | Release Blocking | clean release run |
| `RC-REPORT-001` | Required reports are valid | Required | Release Blocking | report checker |
| `RC-MANIFEST-001` | Manifest integrity passes | Required | Release Blocking | manifest verifier |
| `RC-COMPAT-001` | GF/toolchain compatibility established | Required | Release Blocking | version/capability check |
| `RC-APPROVAL-001` | Release approval recorded | Required | Release Blocking | approval record |

The initialized project may add stricter criteria.

It must not remove a baseline required gate merely because implementation is incomplete.

---

# 11. `RC-INIT-001` — Template initialization complete

**Applicability:** Required  
**Severity:** Release Blocking  

## 11.1 Purpose

Ensure the active project is not still a generic template.

## 11.2 Required conditions

```text
project owner replaced
project ID replaced
language name replaced
language code replaced
module suffix replaced when applicable
source root replaced
entrypoints replaced
checkpoints replaced
scenario registry replaced
expected artifacts replaced
project documentation populated
non-applicable examples removed
required placeholders absent
```

## 11.3 Evidence

```text
gf-wordbench project check --strict
placeholder scan
documentation review
```

## 11.4 Failure conditions

- unresolved `<...>` required placeholders;
- template language examples presented as active facts;
- generic example module names in active configuration;
- example scenarios required without project review;
- project owner unresolved.

## 11.5 Release result

```text
any failure -> FAIL
checker unable to read project -> ERROR
```

---

# 12. `RC-CONFIG-001` — Project configuration valid and complete

**Applicability:** Required  
**Severity:** Release Blocking  

## 12.1 Authoritative provider

```text
project/project.toml
```

## 12.2 Required configuration domains

```text
project identity
source location
source glob
GF path parts
entrypoints
checkpoints
required scenarios
optional scenarios
release entrypoints
expected artifacts
timeouts or policy references
normalization policy where configured
```

## 12.3 Required logical fields

The initialized project must define the final schema’s required fields, including the canonical equivalents of:

```text
project.id
project.name
project.language_code
project.source_dir
project.source_glob
project.entrypoints
project.checkpoints
toolchain.gf_path_parts
validation.required_scenarios
validation.optional_scenarios
release.required_entrypoints
release.expected_artifacts
```

## 12.4 Invariants

- paths are project-relative where required;
- paths remain contained;
- IDs are unique;
- ordered lists are deterministic;
- required entrypoints exist;
- required checkpoints exist;
- required scenarios are registered;
- expected artifacts have stable identities;
- unknown required fields are rejected;
- active language facts do not come from GUI state;
- framework defaults do not override explicit project identity.

## 12.5 Evidence

```text
project schema validation
project checker
strict path validation
source/entrypoint existence checks
```

---

# 13. `RC-IDENTITY-001` — Project identity consistent

**Applicability:** Required  
**Severity:** Release Blocking  

## 13.1 Locked identity

```text
project ID: <PROJECT_ID>
project name: <PROJECT_NAME>
language name: <LANGUAGE_NAME>
language code: <LANGUAGE_CODE>
module suffix: <GF_MODULE_SUFFIX_OR_NONE>
source root: <SOURCE_ROOT>
release entrypoint: <RELEASE_ENTRYPOINT>
expected PGF: <EXPECTED_PGF>
```

Replace all required values during initialization.

## 13.2 Required consistency

Identity must agree across:

```text
project.toml
GF module names
source filenames where policy applies
entrypoints
checkpoints
scenarios
gold files
dependency map
validation specification
interfile contract lock
release criteria
release artifact names
```

## 13.3 Prohibited states

- old-language identifiers remain active;
- two module suffixes represent one active project;
- scenario loads a previous entrypoint;
- expected PGF name disagrees with configuration;
- state file overrides project identity;
- output directory names are used to infer identity.

---

# 14. `RC-SOURCE-001` — Required source inventory complete

**Applicability:** Required  
**Severity:** Release Blocking  

## 14.1 Required conditions

- configured source root exists;
- every required `.gf` source exists;
- every source file decodes as UTF-8 according to policy;
- each source contains one valid module declaration;
- module identities are unique;
- filename/module-name relation satisfies project policy;
- no required module is excluded by source selection;
- no unexpected active source is omitted from project architecture;
- no case collision exists;
- no path escapes the project root;
- generated `.gfo` files are not treated as source.

## 14.2 Evidence

```text
source selector result
module declaration checker
dependency-map inventory
project configuration
```

## 14.3 Counts

Record:

```text
files_seen
files_excluded
files_included
noise_excluded
```

Required invariant:

```text
files_included
=
files_ok
+ files_fail
+ files_error
+ files_skipped
```

---

# 15. `RC-ARCH-001` — Architecture matches source

**Applicability:** Required  
**Severity:** Release Blocking  

## 15.1 Required document

```text
project/docs/LANGUAGE_ARCHITECTURE.md
```

## 15.2 Required conditions

- target language variety/register defined;
- major source layers documented;
- module responsibilities current;
- entrypoints current;
- inherited RGL strategy documented;
- extension/override policy documented;
- structural preservation policy documented;
- architecture does not describe historical modules as current;
- implementation does not contradict the documented direction.

## 15.3 Evidence

```text
architecture review
module inventory comparison
dependency map
project decision log
```

---

# 16. `RC-CONTRACT-001` — Project interfile contracts complete

**Applicability:** Required  
**Severity:** Release Blocking  

## 16.1 Required document

```text
project/docs/INTERFILE_CONTRACT_LOCK.md
```

## 16.2 Required relationships

Document all release-significant:

```text
abstract -> concrete
resource/provider -> consumers
morphology -> paradigms
paradigms -> lexicon
category provider -> syntax
lincat provider -> field consumers
helper provider -> consumers
structural provider -> entrypoints
extension provider -> coordinator
interface -> instance
entrypoint -> scenarios
scenario -> input
scenario -> marker
scenario -> gold
entrypoint -> PGF
project document -> implementation
```

## 16.3 Contract status

Final active project contract lifecycle:

```text
Active
Deprecated
Retired
```

Project status/implementation problems belong in:

```text
project/docs/STATUS_LEDGER.md
```

Applicability belongs in a separate field:

```text
Required
Conditional
Optional
Not Applicable
```

## 16.4 Required conditions

- every public cross-file dependency has one provider;
- every direct consumer is listed;
- no hidden lincat field use;
- no duplicated authoritative helper;
- no undocumented fallback;
- every active contract has validation evidence;
- deprecated contracts have migration plans;
- retired IDs are not reused.

---

# 17. `RC-DEPENDENCY-001` — Dependency map complete and cycle-free

**Applicability:** Required  
**Severity:** Release Blocking  

## 17.1 Required document

```text
project/docs/MODULE_DEPENDENCY_MAP.md
```

## 17.2 Required conditions

- every active source module is inventoried;
- every module has a layer and role;
- every direct project import is represented;
- every external dependency is approved;
- every entrypoint is represented;
- every checkpoint is represented;
- every scenario dependency is represented;
- every gold relationship is represented;
- every release artifact provider is represented;
- no project-owned import cycle exists;
- no prohibited dependency direction exists;
- map and source reality agree.

## 17.3 Default direction

```text
resources/morphology
    -> category implementations
    -> syntax/structural/extensions
    -> grammar/syntax entrypoints
    -> language/API/release entrypoint
    -> PGF
```

## 17.4 Evidence

```text
dependency extraction
cycle check
direction check
clean compilation
documentation review
```

---

# 18. `RC-RESEARCH-001` — Research evidence reviewed

**Applicability:** Conditional  
**Condition:** Required whenever release behavior contains language-specific linguistic claims  
**Severity:** Release Blocking  

## 18.1 Required document

```text
project/docs/RESEARCH_EVIDENCE.md
```

## 18.2 Required conditions

- release-significant claims registered;
- sources verifiable;
- citations checked;
- scope/dialect/register explicit;
- high-risk claims adequately supported;
- counterevidence reviewed;
- implementation trace current;
- validation trace current;
- AI-generated material not treated as evidence;
- source licenses reviewed;
- privacy requirements satisfied;
- no blocking high-risk evidence gap remains.

## 18.3 Evidence-gap policy

Default:

```text
R1 -> may proceed with documented limitation
R2 -> requires owner and next action
R3 -> blocks affected stable feature unless approved exception
R4 -> blocks release
```

The project may define stricter policy.

---

# 19. `RC-SCAN-001` — Static scan policy satisfied

**Applicability:** Required  
**Severity:** Release Blocking  

## 19.1 Purpose

Identify suspicious source patterns without replacing GF compilation.

## 19.2 Required conditions

- every included source scanned;
- scanner completed without internal error;
- findings classified;
- prohibited patterns resolved;
- warning-only patterns reviewed;
- false-positive suppressions documented;
- scanner did not alter source;
- strings/comments handled under documented scanner rules.

## 19.3 Example finding families

The final scanner reference owns exact rules.

Possible families include:

```text
suspicious GF operator/token use
runtime string matching
untyped string patterns
trailing whitespace
deprecated identifiers
old-language identifiers
temporary markers
```

## 19.4 Release policy

Define project treatment:

| Finding family | Allowed count | Review requirement | Release effect |
|---|---:|---|---|
| `<FINDING_FAMILY>` | `<COUNT_OR_POLICY>` | `<REVIEW>` | `<FAIL_OR_ADVISORY>` |

Replace or delete this example table.

## 19.5 Separation rule

```text
scan finding != GF compile failure
GF compile success != scan finding resolution
```

---

# 20. `RC-COMPILE-001` — Every required source compiles

**Applicability:** Required  
**Severity:** Release Blocking  

## 20.1 Canonical operation

Per-file GF compilation:

```text
gf -batch -s <MODULE_OR_SOURCE>
```

with the resolved path options and working directory required by the external-tool contract.

## 20.2 Required conditions

For every included required file:

- process launches;
- no timeout;
- process completes;
- exit status indicates success;
- no fatal diagnostic;
- required `.gfo` exists when expected;
- artifact is non-empty when applicable;
- command and GF version recorded;
- stdout and stderr preserved;
- current-run artifact directory used;
- stale artifacts cannot mask failure.

## 20.3 Status requirements

A successful release cannot contain required file results with:

```text
FAIL
ERROR
SKIPPED
```

All required file results must be:

```text
OK
```

## 20.4 Classification

Direct/downstream classification is diagnostic support.

It does not make a failed file acceptable for release.

---

# 21. `RC-CHECKPOINT-001` — Every required checkpoint passes

**Applicability:** Required  
**Severity:** Release Blocking  

## 21.1 Configuration

Required checkpoints:

```text
<CHECKPOINT_ID_1> -> <CHECKPOINT_MODULE_1>
<CHECKPOINT_ID_2> -> <CHECKPOINT_MODULE_2>
```

Replace with actual ordered checkpoints.

## 21.2 Required conditions

Each checkpoint:

- exists;
- has a documented purpose;
- proves a coherent architectural layer;
- compiles from clean current sources;
- has required supporting scenarios;
- includes its dependency closure;
- is current in the dependency map;
- has no unresolved required status-ledger blocker.

## 21.3 Failure

A release entrypoint compiling successfully does not override a failed required lower checkpoint.

---

# 22. `RC-SCENARIO-001` — Required scenario registry valid

**Applicability:** Required  
**Severity:** Release Blocking  

## 22.1 Required sources

```text
project/project.toml
project/validation/scenarios/
project/validation/gold/
project/docs/VALIDATION_SPEC.md
```

## 22.2 Required conditions

- scenario IDs unique;
- required scripts exist;
- scripts decode as UTF-8;
- paths remain contained;
- every scenario has a purpose;
- every scenario loads documented entrypoints;
- every scenario input is declared;
- required markers are declared;
- gold policy declared;
- normalization version declared;
- mode applicability declared;
- required/optional distinction declared;
- scenario order deterministic;
- system commands prohibited;
- interactive commands prohibited;
- generation bounded;
- explicit termination included where required.

## 22.3 Project registry

Replace this table during initialization:

| Scenario ID | Script | Required | Modes | Entrypoint | Gold | Purpose |
|---|---|:---:|---|---|---|---|
| `<SCENARIO_ID>` | `validation/scenarios/<SCENARIO>.gfs` | Yes | `release` | `<ENTRYPOINT>` | `<GOLD_OR_NONE>` | `<PURPOSE>` |

---

# 23. `RC-SCENARIO-002` — Required scenarios pass

**Applicability:** Required  
**Severity:** Release Blocking  

## 23.1 Required conditions

For every required release scenario:

- GF process launches;
- finite timeout enforced;
- process completes;
- raw stdout saved;
- raw stderr saved;
- required outer marker seen;
- every required section marker complete;
- output not truncated;
- prohibited commands absent;
- assertions pass;
- expected artifacts exist;
- normalization succeeds;
- gold comparison passes when required.

## 23.2 Status requirements

Every required scenario result must be:

```text
OK
```

The following block release:

```text
FAIL
ERROR
SKIPPED
```

## 23.3 Zero exit rule

A zero GF process exit is insufficient when:

- markers are missing;
- output is incomplete;
- gold mismatches;
- required artifact is missing;
- scenario assertions fail.

---

# 24. `RC-GOLD-001` — Required gold files exist

**Applicability:** Conditional  
**Condition:** Required for every scenario configured for exact normalized comparison  
**Severity:** Release Blocking  

## 24.1 Required conditions

- one authoritative gold per scenario variant;
- gold path project-relative;
- file exists;
- file decodes as UTF-8;
- LF/canonical text policy satisfied;
- scenario ID and gold mapping agree;
- normalization major compatible;
- no orphan active gold;
- no required scenario lacks gold or an explicit non-gold assertion strategy.

## 24.2 Ownership

Gold files are owned by project maintainers.

Normal validation is read-only.

---

# 25. `RC-GOLD-002` — Required gold comparisons match

**Applicability:** Conditional  
**Condition:** At least one required exact-gold scenario exists  
**Severity:** Release Blocking  

## 25.1 Required conditions

- raw output preserved before normalization;
- normalization version recorded;
- normalized output deterministic;
- expected and actual comparison completed;
- no mismatch;
- diff empty;
- no output truncation;
- current scenario and gold hashes recorded where policy requires.

## 25.2 Gold update policy

A gold change is acceptable only through explicit review.

Required review distinguishes:

```text
linguistic behavior change
bug fix
scenario change
normalization change
GF-version formatting change
non-linguistic artifact change
```

The release must not approve a mismatch merely by regenerating gold automatically.

---

# 26. `RC-MISSING-001` — Required functions and linearizations complete

**Applicability:** Required  
**Severity:** Release Blocking  

## 26.1 Purpose

Detect incomplete concrete grammar coverage.

## 26.2 Recommended evidence

Native GF shell scenario using:

```text
pg -missing
```

or another version-compatible supported GF mechanism.

## 26.3 Required conditions

- required entrypoint loads;
- missing-function inspection completes;
- required markers complete;
- no required function remains missing;
- explicitly unsupported functions are documented and outside release scope;
- status ledger agrees;
- project contract agrees;
- scenario/gold assertion is stable.

## 26.4 Exceptions

A deliberate partial project must define:

- exact excluded surface;
- user impact;
- project version/maturity;
- status-ledger entries;
- release label;
- explicit approval.

A stable complete release cannot hide missing required functions.

---

# 27. `RC-PARSE-001` — Required parse cases pass

**Applicability:** Conditional  
**Condition:** Parsing belongs to the project release surface  
**Severity:** Release Blocking  

## 27.1 Required cases

Replace during initialization:

```text
positive parse cases
expected ambiguity cases
rejected/contrastive cases where testable
tokenization cases
orthographic variants
category-specific cases
```

## 27.2 Required conditions

- scenario loads release-compatible entrypoint;
- inputs are project-owned or declared;
- expected trees/categories documented;
- ambiguity policy explicit;
- parse result bounded;
- required cases pass;
- unexpected overgeneration reviewed;
- expected rejection is not represented merely by a process error.

## 27.3 Linguistic limitation

A successful parse proves current grammar acceptance.

Research evidence must support linguistic acceptance where release-significant.

---

# 28. `RC-LINEARIZE-001` — Required linearization cases pass

**Applicability:** Required  
**Severity:** Release Blocking  

## 28.1 Required coverage

At minimum, define representative trees for:

```text
core categories
core clause types
agreement
polarity
questions
relative clauses where supported
coordination where supported
required morphology
release-critical lexical items
known difficult constructions
```

Delete non-applicable families.

## 28.2 Required conditions

- every required tree linearizes;
- output is non-empty where required;
- output matches project orthography;
- agreement/ordering criteria pass;
- deterministic cases match gold;
- accepted variants follow project policy;
- no known release-blocking malformed output remains.

---

# 29. `RC-GENERATION-001` — Generation checks bounded and acceptable

**Applicability:** Conditional  
**Condition:** Generation belongs to release validation  
**Severity:** Release Blocking  

## 29.1 Required safeguards

- finite tree depth;
- finite result count;
- finite timeout;
- finite output size;
- stable sort/order policy where compared;
- no unbounded `generate all` behavior;
- truncation explicit;
- required completion marker.

## 29.2 Required review

Generation evidence should review:

```text
coverage
overgeneration
unexpected variants
empty outputs
duplicate outputs
nondeterministic ordering
```

## 29.3 Gold policy

Use exact gold only when deterministic and bounded.

Otherwise use structured assertions and reviewed evidence.

---

# 30. `RC-MORPH-001` — Required morphology checks pass

**Applicability:** Conditional  
**Condition:** Project includes morphology/paradigm providers  
**Severity:** Release Blocking  

## 30.1 Required coverage

Define relevant categories:

```text
noun
verb
adjective
pronoun
determiner
numeral
other language-specific classes
```

## 30.2 Required conditions

- required paradigms compile;
- parameter coverage complete;
- irregular forms tested;
- defective forms represented explicitly;
- orthographic alternations tested;
- agreement dimensions tested;
- representative productive forms tested;
- required negative/contrastive cases reviewed;
- no unsupported fallback presented as stable;
- evidence links to research claims.

---

# 31. `RC-LEXICON-001` — Required release lexicon complete

**Applicability:** Conditional  
**Condition:** Project release scope defines a required lexicon  
**Severity:** Release Blocking  

## 31.1 Required conditions

- required abstract identifiers present;
- duplicate identifiers absent;
- entries use approved paradigms;
- orthography policy followed;
- lexical category correct;
- inflection class assigned;
- required valency represented;
- temporary entries registered;
- source/licence policy satisfied;
- representative lexicon scenarios pass.

## 31.2 Completeness source

Define authoritative release lexicon specification:

```text
<LEXICON_SPEC_PATH_OR_NOT_APPLICABLE>
```

---

# 32. `RC-PGF-001` — Final PGF build succeeds

**Applicability:** Required  
**Severity:** Release Blocking  

## 32.1 Canonical operation

```text
gf -make -optimize-pgf <PATH_OPTIONS> <RELEASE_ENTRYPOINTS>
```

The final command is built by GF Wordbench according to the external-tool contract.

## 32.2 Configured release entrypoints

```text
<RELEASE_ENTRYPOINT_1>
<RELEASE_ENTRYPOINT_N>
```

## 32.3 Required conditions

- project configuration valid;
- entrypoint ordering deterministic;
- GF executable compatible;
- process launches;
- separate finite PGF timeout applied;
- process completes;
- exit status successful;
- no fatal diagnostic;
- exact command recorded;
- GF version recorded;
- working directory recorded;
- raw stdout/stderr preserved;
- build output belongs to current run.

## 32.4 Distinct stage

File `.gfo` success does not satisfy this gate.

PGF construction is a separate required release stage.

---

# 33. `RC-PGF-002` — Expected PGF exists and is non-empty

**Applicability:** Required  
**Severity:** Release Blocking  

## 33.1 Expected artifact

```text
<EXPECTED_PGF>
```

Replace during initialization.

## 33.2 Required conditions

- expected path deterministically derived or explicitly configured;
- artifact exists;
- regular file;
- non-empty;
- contained in owned run artifact directory;
- associated with the current run;
- provider entrypoint correct;
- artifact registered in manifest;
- SHA-256 recorded;
- no collision/overwrite ambiguity;
- artifact identity agrees with project docs and configuration.

## 33.3 Prohibited success

```text
zero process exit + missing PGF -> not success
```

This condition is at least:

```text
FAIL
```

or `ERROR` according to the final operation contract.

---

# 34. `RC-ARTIFACT-001` — Required artifacts registered

**Applicability:** Required  
**Severity:** Release Blocking  

## 34.1 Required run artifacts

Canonical framework outputs include:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
raw evidence
details as configured
release PGF
```

## 34.2 Project-required artifacts

Replace table:

| Artifact role | Expected path/name | Provider | Required | Integrity |
|---|---|---|:---:|---|
| Release PGF | `<EXPECTED_PGF>` | `<RELEASE_ENTRYPOINT>` | Yes | SHA-256 |
| `<PROJECT_ARTIFACT_ROLE>` | `<PATH>` | `<PROVIDER>` | `<YES_NO>` | `<POLICY>` |

## 34.3 Required conditions

- every required artifact exists;
- owner known;
- current-run provenance known;
- manifest role known;
- relative path canonical;
- size recorded;
- hash recorded where required;
- no required artifact points outside run ownership;
- no stale artifact substituted.

---

# 35. `RC-REGRESSION-001` — Regression comparison completed

**Applicability:** Required  
**Severity:** Release Blocking  

## 35.1 Baseline

Define baseline policy:

```text
automatic latest compatible finalized release run
```

or:

```text
explicit baseline: <BASELINE_POLICY>
```

## 35.2 Required conditions

- baseline selection deterministic;
- baseline finalized;
- schema compatible or migrated;
- project identity compatible;
- mode/scope compatible;
- GF/normalization differences considered;
- file subjects compared;
- scenario subjects compared;
- artifact/gate subjects compared where supported;
- comparison evidence persisted.

## 35.3 Missing automatic baseline

For the first release:

- absence may be accepted;
- release record states no compatible baseline;
- initial baseline is established from the successful release run.

The project must define this exception explicitly.

---

# 36. `RC-REGRESSION-002` — No unapproved regression remains

**Applicability:** Required  
**Severity:** Release Blocking  

## 36.1 Canonical change kinds

```text
unchanged
improved
regressed
new
removed
```

## 36.2 Required review

Every `regressed` subject must be:

- fixed;
- reclassified as non-comparable with reason;
- or approved as intentional through a project decision.

Every `new` and `removed` required subject must be reviewed.

## 36.3 Approval record

Intentional regression approval must identify:

```text
subject
previous status
current status
reason
user impact
source/research evidence
migration
scenario/gold impact
decision-log entry
approver
```

A broad “expected changes” note is insufficient.

---

# 37. `RC-STATUS-001` — No blocking status-ledger entry

**Applicability:** Required  
**Severity:** Release Blocking  

## 37.1 Required document

```text
project/docs/STATUS_LEDGER.md
```

## 37.2 Required conditions

- every temporary implementation registered;
- every fallback registered;
- every warning registered;
- every blocked feature registered;
- every disabled operation registered;
- source comments and ledger agree;
- resolved entries retain resolution;
- each active entry has owner;
- each active entry has next action or exit condition;
- no release-blocking entry remains unresolved.

## 37.3 Approval exception

A non-blocking known limitation may ship only when:

- user impact documented;
- release notes include it;
- validation coverage prevents accidental worsening;
- owner assigned;
- project maturity label is accurate.

---

# 38. `RC-DOC-001` — Required project documentation complete

**Applicability:** Required  
**Severity:** Release Blocking  

## 38.1 Required documents

At minimum:

```text
project/docs/LANGUAGE_ARCHITECTURE.md
project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
project/docs/MODULE_DEPENDENCY_MAP.md
project/docs/RESEARCH_EVIDENCE.md
project/docs/VALIDATION_SPEC.md
project/docs/RELEASE_CRITERIA.md
project/docs/STATUS_LEDGER.md
project/docs/DECISION_LOG.md
project/docs/INTERFILE_CONTRACT_LOCK.md
```

The project may mark `RESEARCH_EVIDENCE.md` not applicable only when no language-specific claim is distributed, which is uncommon for a GF language project.

## 38.2 Required conditions

- files exist;
- no unresolved required placeholders;
- current module names;
- current scenario IDs;
- current entrypoints;
- current gold paths;
- current PGF identity;
- no old-language identifiers;
- no historical architecture presented as current;
- internal links valid;
- documentation and configuration agree;
- documentation and source agree.

---

# 39. `RC-SECURITY-001` — Security checks pass

**Applicability:** Required  
**Severity:** Release Blocking  

## 39.1 Required conditions

- project paths contained;
- symlink/junction escapes rejected;
- `.gfs` scripts reviewed;
- operating-system commands absent;
- shell redirection not constructed from project text;
- interactive GF commands absent;
- generation bounded;
- timeouts finite;
- output limits finite;
- no source overwrite;
- no gold overwrite during validation;
- no secrets in project configuration or reports;
- no private environment dumps;
- research data privacy satisfied;
- untrusted assets not executed.

## 39.2 Scenario command prohibition

Normal project scenarios must not use commands capable of executing system commands or piping to system utilities.

Any future exception requires:

- explicit security policy;
- project decision;
- isolated environment;
- release review;
- external-tool contract update.

---

# 40. `RC-REPRO-001` — Release run reproducible and current

**Applicability:** Required  
**Severity:** Release Blocking  

## 40.1 Required conditions

- clean source revision;
- project configuration committed;
- scenarios committed;
- gold files committed;
- project docs committed;
- current GF version recorded;
- RGL/toolchain resolution recorded;
- no developer-only path dependence;
- clean/current artifact directory;
- deterministic file/scenario ordering;
- current source fingerprints recorded;
- final run not cancelled;
- final run finalized;
- release commit identified;
- rerun under equivalent environment produces equivalent required outcomes.

## 40.2 Dirty tree policy

Recommended:

```text
official release from clean working tree only
```

If local project policy differs, document the exact provenance and why release integrity remains established.

---

# 41. `RC-REPORT-001` — Required reports valid

**Applicability:** Required  
**Severity:** Release Blocking  

## 41.1 Required reports

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
```

plus project-required detail artifacts.

## 41.2 Required conditions

- report writers completed;
- schemas supported;
- required headings present;
- run ID consistent;
- project identity consistent;
- overall status consistent;
- counts consistent;
- file results complete;
- scenario results complete;
- regression results present;
- artifact links valid;
- no secret leakage;
- reports derived from structured results;
- report writers did not rerun GF.

## 41.3 Machine authority

```text
summary.json
```

is the machine-authoritative report.

Markdown is not the primary machine schema.

---

# 42. `RC-MANIFEST-001` — Manifest integrity passes

**Applicability:** Required  
**Severity:** Release Blocking  

## 42.1 Required conditions

- manifest exists;
- schema supported;
- run ID correct;
- generator version recorded;
- required artifacts listed;
- relative paths contained;
- artifact roles valid;
- sizes match;
- SHA-256 hashes match;
- no duplicate path/role ambiguity;
- final PGF listed;
- raw evidence required by policy listed;
- manifest validates after all artifacts are finalized.

## 42.2 Finalization

The manifest should be written only after required artifacts exist.

A manifest failure makes the release:

```text
ERROR
```

when integrity cannot be established reliably.

---

# 43. `RC-COMPAT-001` — Toolchain compatibility established

**Applicability:** Required  
**Severity:** Release Blocking  

## 43.1 Required compatibility metadata

```text
minimum supported GF version
tested GF versions
known incompatible GF versions
selected GF version
RGL/toolchain version or revision where available
Python version
supported operating system
normalization version
project schema version
```

## 43.2 Required conditions

- selected GF meets framework minimum;
- project-specific minimum met;
- selected version is tested or capability-approved;
- no known incompatibility applies;
- required GF commands supported;
- direct stdin scenarios supported;
- PGF build options supported;
- unknown newer version handled under strict release policy;
- silent semantic fallback absent.

## 43.3 Strict release default

Recommended:

```text
unknown untested GF version -> FAIL or ERROR
```

until capability and integration evidence is reviewed.

---

# 44. `RC-APPROVAL-001` — Release approval recorded

**Applicability:** Required  
**Severity:** Release Blocking  

## 44.1 Approval roles

Replace:

```text
Project maintainer: <NAME_OR_ROLE>
Language reviewer: <NAME_OR_ROLE>
Release reviewer: <NAME_OR_ROLE>
Security reviewer when required: <NAME_OR_ROLE>
```

Role names may be used instead of personal names.

## 44.2 Required conditions

- final release run `overall_status=OK`;
- all required gates `OK`;
- no required gate `SKIPPED`;
- known issues reviewed;
- intentional changes reviewed;
- gold changes reviewed;
- research evidence reviewed;
- artifact hashes recorded;
- release version chosen;
- release notes prepared;
- approval date recorded.

## 44.3 Approval record

```text
Project version: <PROJECT_VERSION>
GF Wordbench version: <FRAMEWORK_VERSION>
Release commit: <COMMIT>
Release run ID: <RUN_ID>
Expected PGF: <EXPECTED_PGF>
Manifest SHA-256: <MANIFEST_SHA256>
Decision: Ready
Approved by: <ROLE>
Approval date: <YYYY-MM-DD>
```

---

# 45. Project-specific criteria registry

Add project-specific gates here.

| Gate ID | Criterion | Applicability | Severity | Evidence | Owner |
|---|---|---|---|---|---|
| `<RC-DOMAIN-NNN>` | `<CRITERION>` | `<APPLICABILITY>` | `<SEVERITY>` | `<EVIDENCE>` | `<OWNER>` |

Delete the example row after initialization if no additional gates exist.

---

# 46. Criteria for a partial or preview release

A project may intentionally publish a partial release.

It must not use the same maturity claim as a complete stable release.

Required distinctions:

```text
Preview
Experimental
Incomplete
Stable
```

These are project release maturity labels.

## 46.1 Preview requirements

A preview release still requires:

- valid configuration;
- secure scenarios;
- reproducible build;
- manifest;
- documented incomplete surface;
- status ledger;
- no false claim of completeness;
- user-facing limitation list.

## 46.2 Stable release requirements

A stable release requires:

- every required release-scope function implemented;
- no blocking evidence gap;
- no blocking status-ledger entry;
- all required scenarios and gold pass;
- final PGF valid;
- all required gates `OK`.

---

# 47. Conditional feature declarations

The project must list optional language subsystems and whether they belong to release scope.

Replace table:

| Feature family | Release scope | Required gate(s) | Not-applicable rationale |
|---|:---:|---|---|
| Parsing | `<YES_NO>` | `RC-PARSE-001` | `<RATIONALE_IF_NO>` |
| Generation | `<YES_NO>` | `RC-GENERATION-001` | `<RATIONALE_IF_NO>` |
| Morphology | `<YES_NO>` | `RC-MORPH-001` | `<RATIONALE_IF_NO>` |
| Release lexicon | `<YES_NO>` | `RC-LEXICON-001` | `<RATIONALE_IF_NO>` |
| API entrypoint | `<YES_NO>` | `<GATES>` | `<RATIONALE_IF_NO>` |
| Research evidence | `<YES_NO>` | `RC-RESEARCH-001` | `<RATIONALE_IF_NO>` |

A blank value is not a valid decision.

---

# 48. Required checkpoint table

Replace:

| Checkpoint ID | Module | Purpose | Required scenarios | Acceptance criterion |
|---|---|---|---|---|
| `<CHECKPOINT_ID>` | `<MODULE>` | `<PURPOSE>` | `<SCENARIOS>` | `<CRITERION>` |

Rules:

- every configured checkpoint appears;
- order matches `project.toml`;
- checkpoint purpose is architectural;
- successful compile from clean source required;
- missing lower checkpoint cannot be ignored because the final entrypoint compiles.

---

# 49. Required scenario table

Replace:

| Scenario ID | Purpose | Entry point | Required markers | Gold/assertion strategy | Required modes |
|---|---|---|---|---|---|
| `<SCENARIO_ID>` | `<PURPOSE>` | `<ENTRYPOINT>` | `<MARKERS>` | `<GOLD_OR_ASSERTIONS>` | `release` |

Rules:

- every required scenario appears;
- no example row remains;
- gold path exact when used;
- non-gold assertion strategy explicit;
- required markers explicit;
- release mode listed.

---

# 50. Required artifact table

Replace:

| Artifact role | Provider | Expected identity | Required checks |
|---|---|---|---|
| Release PGF | `<ENTRYPOINT>` | `<EXPECTED_PGF>` | exists, non-empty, SHA-256, manifest |
| `<ROLE>` | `<PROVIDER>` | `<PATH_OR_NAME>` | `<CHECKS>` |

---

# 51. Required research-claim table

When `RC-RESEARCH-001` applies, replace:

| Claim ID | Release relevance | Risk | Required evidence | Validation |
|---|---|---|---|---|
| `<RE-CLM-NNNN>` | `<RELEVANCE>` | `<R1_R4>` | `<SOURCE_IDS>` | `<SCENARIO_OR_REVIEW>` |

The complete research registry remains in:

```text
project/docs/RESEARCH_EVIDENCE.md
```

---

# 52. Required documentation table

Replace status values during initialization:

| Document | Required | Completion owner | Review evidence |
|---|:---:|---|---|
| `LANGUAGE_ARCHITECTURE.md` | Yes | `<OWNER>` | `<REVIEW>` |
| `CATEGORY_AND_LINCAT_CONTRACT.md` | Yes | `<OWNER>` | `<REVIEW>` |
| `MODULE_DEPENDENCY_MAP.md` | Yes | `<OWNER>` | dependency gate |
| `RESEARCH_EVIDENCE.md` | `<YES_CONDITIONAL>` | `<OWNER>` | research gate |
| `VALIDATION_SPEC.md` | Yes | `<OWNER>` | scenario coverage |
| `RELEASE_CRITERIA.md` | Yes | `<OWNER>` | release review |
| `STATUS_LEDGER.md` | Yes | `<OWNER>` | ledger gate |
| `DECISION_LOG.md` | Yes | `<OWNER>` | decision review |
| `INTERFILE_CONTRACT_LOCK.md` | Yes | `<OWNER>` | contract gate |

---

# 53. Manual criteria

Automation is preferred.

When a criterion cannot be automated, it must define:

```text
criterion ID
reason automation is impossible
reviewer role
review method
acceptance threshold
evidence location
review date
expiration/review cadence
```

Manual approval without recorded method is not valid evidence.

---

# 54. Exception policy

An exception is allowed only when the criterion explicitly permits an exception.

No exception is allowed for:

- path security;
- source corruption;
- missing required PGF;
- manifest integrity failure;
- missing required project identity;
- unresolved R4 evidence gap;
- prohibited system commands;
- release run `ERROR`;
- required scenario `ERROR`;
- required report/manifest unreadable.

## 54.1 Exception record

```text
Exception ID: <EXCEPTION_ID>
Gate ID: <RC-ID>
Reason:
Scope:
User impact:
Temporary treatment:
Validation coverage:
Owner:
Approval:
Expiry/exit condition:
```

## 54.2 Expired exception

An expired exception blocks release.

---

# 55. Release run selection

The approval run must be:

- release mode;
- strict;
- finalized;
- current project revision;
- current project configuration;
- current scenarios/gold/docs;
- current GF version;
- not cancelled;
- not partial;
- not a quick/checkpoint substitute;
- not older than a project-defined freshness window.

Recommended freshness:

```text
same release commit
```

---

# 56. Release evidence package

The release record should retain:

```text
summary.json
summary.md
AI_READY.md
top_errors.txt
manifest.json
raw/compile/
raw/scenarios/
normalized scenario output
gold diffs
release PGF
release approval record
release notes
artifact hashes
```

Retention policy belongs to release documentation.

---

# 57. Release decision algorithm

```python
def decide_project_release(gates):
    required = [gate for gate in gates if gate.applicability == "Required"]

    if any(gate.status == "ERROR" for gate in required):
        return "Blocked by Error"

    if any(gate.status in {"FAIL", "SKIPPED"} for gate in required):
        return "Not Ready"

    return "Ready"
```

Conditional gates whose condition is true are normalized to required before evaluation.

The implementation may differ.

The behavior is normative.

---

# 58. Overall run aggregation

Canonical precedence:

```text
ERROR
>
FAIL
>
OK
```

Required subject results:

```text
FileResult
ScenarioResult
PGF result
release gate
required report/integrity result
```

A required skipped subject becomes an error before final success evaluation.

---

# 59. Regression approval workflow

```text
1. identify regressed subject
2. inspect raw evidence
3. verify baseline comparability
4. determine accidental or intentional change
5. review research evidence when linguistic
6. update implementation or decision
7. update scenarios/gold intentionally
8. record approval or fix
9. rerun release validation
10. verify regression gate
```

Do not approve regression solely from a changed gold file.

---

# 60. Gold-change workflow

```text
1. run scenario without modifying gold
2. inspect raw stdout/stderr
3. inspect normalized output
4. inspect diff
5. determine change category
6. review research evidence if linguistic
7. review normalization version if technical
8. update decision/validation spec
9. run explicit gold update
10. rerun scenarios
11. rerun release
12. commit gold with rationale
```

---

# 61. Breaking project change workflow

Breaking changes include:

- project ID rename;
- language code rename;
- module suffix rename;
- public module rename;
- public symbol rename;
- public lincat field change;
- constructor arity change;
- entrypoint change;
- checkpoint identity change;
- scenario ID change;
- normalization-major change;
- expected PGF rename;
- target language variety change.

Required:

```text
decision log
migration plan
provider/consumer update
configuration update
dependency-map update
contract-lock update
scenario/gold update
compatibility review
release validation
release note
```

---

# 62. Security review triggers

Explicit security review is required when release changes:

- scenario command set;
- process invocation;
- shell behavior;
- path containment;
- generated-file cleanup;
- gold-writing behavior;
- remote/network access;
- plugin/external tool;
- research-data storage;
- secret handling;
- manifest hashing;
- archive/export behavior.

---

# 63. Compatibility review triggers

Explicit compatibility review is required when release changes:

- project schema;
- public project module;
- public helper;
- lincat shape;
- entrypoint;
- scenario ID;
- gold format;
- normalization version;
- artifact name;
- project version support;
- GF minimum;
- Python/platform support.

---

# 64. Release versioning

The active project may use:

```text
MAJOR.MINOR.PATCH
```

Suggested meaning:

- `MAJOR`: incompatible public project/module/entrypoint change;
- `MINOR`: compatible coverage or linguistic feature expansion;
- `PATCH`: correction preserving public project contracts.

Project version is independent from:

```text
GF Wordbench framework version
project schema version
GF executable version
normalization version
```

Record every applicable version in release evidence.

---

# 65. First release policy

The first release has no previous compatible baseline.

Required first-release conditions:

- all baseline required gates pass;
- initial project identity frozen;
- source inventory complete;
- contract lock populated;
- dependency map populated;
- validation specification populated;
- required scenarios/gold established;
- release PGF verified;
- manifest verified;
- initial baseline run recorded;
- future baseline discovery can select it.

---

# 66. Preview-to-stable promotion

Promotion to stable requires review of all provisional exceptions.

Checklist:

```text
[ ] preview limitations reviewed
[ ] required feature scope finalized
[ ] all stable claims supported
[ ] temporary fallbacks resolved or removed
[ ] blocking status entries resolved
[ ] scenarios expanded to stable scope
[ ] gold reviewed
[ ] regression baseline available
[ ] public project contracts stabilized
[ ] release notes identify compatibility commitments
```

---

# 67. Release checklist — configuration and identity

```text
[ ] `project.toml` parses
[ ] schema ID/version supported
[ ] project ID final
[ ] project name final
[ ] language name final
[ ] language code final
[ ] module suffix final or not applicable
[ ] source root exists
[ ] source glob correct
[ ] entrypoints ordered
[ ] checkpoints ordered
[ ] scenario IDs unique
[ ] release entrypoints final
[ ] expected artifacts final
[ ] no old-language identifiers remain
[ ] no required placeholders remain
```

---

# 68. Release checklist — source and architecture

```text
[ ] source inventory complete
[ ] every module declaration valid
[ ] every module uniquely owned
[ ] architecture layers current
[ ] dependency map current
[ ] no import cycle
[ ] no prohibited direction
[ ] no hidden public helper
[ ] no hidden lincat field dependency
[ ] no duplicated provider
[ ] inherited RGL behavior reviewed
[ ] overrides documented
```

---

# 69. Release checklist — evidence and status

```text
[ ] research claims reviewed
[ ] R3/R4 evidence thresholds met
[ ] contradictions addressed
[ ] evidence gaps reviewed
[ ] status ledger current
[ ] no blocking status entry
[ ] temporary code has exit condition
[ ] decision log current
[ ] release-impacting decisions approved
```

---

# 70. Release checklist — validation

```text
[ ] static scans complete
[ ] all required files `OK`
[ ] all required checkpoints `OK`
[ ] scenario registry valid
[ ] all required scenarios `OK`
[ ] required markers complete
[ ] missing-function check passes
[ ] required parse checks pass
[ ] required linearization checks pass
[ ] required generation checks pass
[ ] required morphology checks pass
[ ] required gold files exist
[ ] required gold comparisons match
[ ] no output truncation invalidates evidence
```

---

# 71. Release checklist — build and artifacts

```text
[ ] PGF build process `OK`
[ ] expected PGF exists
[ ] expected PGF non-empty
[ ] PGF current-run provenance established
[ ] PGF SHA-256 recorded
[ ] required reports exist
[ ] report schemas valid
[ ] manifest exists
[ ] manifest hashes match
[ ] artifact paths contained
[ ] no stale artifact substituted
```

---

# 72. Release checklist — regression and compatibility

```text
[ ] baseline policy satisfied
[ ] regression comparison complete
[ ] every regression reviewed
[ ] intentional changes approved
[ ] GF version compatible
[ ] required GF capabilities pass
[ ] Python version supported
[ ] operating system supported
[ ] normalization versions compatible
[ ] migrations reviewed
```

---

# 73. Release checklist — security and reproducibility

```text
[ ] scenario system commands absent
[ ] path security passes
[ ] finite timeouts configured
[ ] output limits configured
[ ] gold remains unchanged during validation
[ ] source remains unchanged during validation
[ ] no secrets in reports
[ ] privacy-sensitive research data excluded
[ ] working tree/release revision policy satisfied
[ ] release run finalized
[ ] release evidence retained
[ ] equivalent rerun policy satisfied
```

---

# 74. Release checklist — documentation and approval

```text
[ ] all required documents exist
[ ] documentation links valid
[ ] documents match source
[ ] documents match configuration
[ ] documents match scenarios/gold
[ ] known limitations included in release notes
[ ] project version chosen
[ ] framework version recorded
[ ] release commit recorded
[ ] final run ID recorded
[ ] approval roles completed
[ ] final decision recorded
```

---

# 75. Release approval template

```markdown
## Release approval — <PROJECT_VERSION>

**Project:** `<PROJECT_NAME>`  
**Project ID:** `<PROJECT_ID>`  
**Language:** `<LANGUAGE_NAME>`  
**Project version:** `<PROJECT_VERSION>`  
**GF Wordbench version:** `<FRAMEWORK_VERSION>`  
**GF version:** `<GF_VERSION>`  
**Project schema:** `<PROJECT_SCHEMA_VERSION>`  
**Normalization version:** `<NORMALIZATION_VERSION>`  
**Release commit:** `<COMMIT>`  
**Release run ID:** `<RUN_ID>`  
**Expected PGF:** `<EXPECTED_PGF>`  
**Manifest:** `<MANIFEST_PATH>`  
**Manifest SHA-256:** `<MANIFEST_SHA256>`  
**Decision:** Ready | Not Ready | Blocked by Error  
**Approval date:** `<YYYY-MM-DD>`  

### Required-gate summary

| Result | Count |
|---|---:|
| `OK` | `<COUNT>` |
| `FAIL` | `<COUNT>` |
| `ERROR` | `<COUNT>` |
| `SKIPPED` | `<COUNT>` |

### Known limitations

- `<LIMITATION_OR_NONE>`

### Approved exceptions

- `<EXCEPTION_OR_NONE>`

### Reviewers

- Project maintainer: `<ROLE>`
- Language reviewer: `<ROLE>`
- Release reviewer: `<ROLE>`
- Security reviewer: `<ROLE_OR_NOT_APPLICABLE>`

### Final statement

`<FINAL_APPROVAL_STATEMENT>`
```

Store the completed approval in the project’s release evidence location.

---

# 76. Gate entry template

Copy for project-specific gates:

```markdown
## `RC-<DOMAIN>-<NUMBER>` — <Criterion title>

**Applicability:** Required | Conditional | Optional | Not Applicable  
**Condition:** <condition or none>  
**Severity:** Release Blocking | Advisory  
**Owner:** <role>  

### Purpose

<Why this criterion exists.>

### Required conditions

- <condition>;
- <condition>.

### Evidence

- <compile/scenario/gold/artifact/review>;
- <path or ID>.

### Failure conditions

- <failure>;
- <failure>.

### Exception policy

<None or exact policy.>

### Related contracts

- <contract ID>;
- <document path>.
```

---

# 77. Validation-spec alignment

Every release gate with executable evidence must be represented in:

```text
project/docs/VALIDATION_SPEC.md
```

The validation specification owns:

- scenario purpose;
- checkpoint purpose;
- acceptance criterion;
- required modes;
- evidence artifact.

This document owns:

- whether the criterion blocks release;
- the release decision rule;
- approval and exception policy.

---

# 78. Project configuration alignment

`project.toml` must contain enough structured information to execute every automated release gate.

Do not rely on this Markdown file for runtime selection.

Examples of project-owned structured values:

```text
entrypoints
checkpoints
required scenarios
optional scenarios
release entrypoints
expected artifacts
GF path parts
```

This document is governance, not runtime configuration.

---

# 79. Interfile-contract alignment

Every release criterion involving provider/consumer behavior must link to a project contract.

Examples:

```text
morphology provider -> paradigms
category provider -> syntax consumers
entrypoint -> scenario
scenario -> gold
entrypoint -> PGF
```

A release gate cannot repair an undocumented cross-file contract.

---

# 80. Research-evidence alignment

Every linguistically meaningful acceptance criterion should link to a research claim or reviewed project policy.

Examples:

- expected word order;
- agreement form;
- morphological paradigm;
- accepted variant;
- rejected variant;
- orthographic spelling;
- lexical valency.

Compilation and gold stability do not replace research support.

---

# 81. Dependency-map alignment

Every release entrypoint and required scenario must appear in the dependency map.

Release criteria should verify:

- entrypoint closure;
- scenario closure;
- expected artifact provider;
- no missing source dependency;
- no cycle.

---

# 82. Status-ledger alignment

A release criterion must not assume an implementation is stable when the status ledger marks it:

```text
temporary
fallback
warning
blocked
disabled
```

The release decision must use the ledger’s active information.

---

# 83. Decision-log alignment

A release-impacting intentional change requires a decision record when it changes:

- target scope;
- public project contract;
- lincat design;
- default variant;
- entrypoint;
- expected artifact;
- normalization meaning;
- evidence threshold;
- approved regression.

---

# 84. Report alignment

`summary.md` should display:

```text
release mode
overall status
required gate summary
file results
scenario results
regression comparison
artifact paths
```

`summary.json` remains authoritative.

This document must not be parsed to reconstruct run results.

---

# 85. Manifest alignment

Every required release artifact declared here must have a corresponding manifest role or documented artifact entry.

A required artifact absent from the manifest blocks release.

---

# 86. Release failure categories

Release failure may arise from:

```text
validation failure
execution error
configuration error
contract drift
evidence gap
security failure
integrity failure
approval failure
```

These categories should remain distinguishable.

Do not reduce all failures to “compile failed”.

---

# 87. Failure triage order

Recommended:

```text
1. configuration and identity
2. security/path integrity
3. GF/tool launch and timeout
4. direct source failures
5. downstream failures
6. required scenario failures
7. gold mismatch
8. PGF/artifact failure
9. regression review
10. documentation/evidence/approval gaps
```

This is a triage order, not status precedence.

---

# 88. Cancellation and timeout

A cancelled or timed-out required release operation is:

```text
ERROR
```

It is not:

```text
FAIL
SKIPPED
OK
```

The release decision becomes:

```text
Blocked by Error
```

---

# 89. Required skipped behavior

When a required operation was skipped unexpectedly:

```text
gate status = ERROR
```

A release cannot pass by omitting a difficult required criterion.

---

# 90. Optional-gate policy

For each optional gate, define:

```text
whether FAIL affects release
whether ERROR affects release
whether SKIPPED is expected
```

Recommended:

- optional `FAIL`: advisory unless it exposes required-scope failure;
- optional `ERROR`: release error when shared reliability is affected;
- optional `SKIPPED`: acceptable.

---

# 91. Advisory findings

Advisory findings must still be:

- recorded;
- assigned;
- reviewed;
- included in release notes when user-relevant.

An advisory label must not be used for security or integrity failure.

---

# 92. Determinism

Given equivalent:

```text
sources
configuration
GF version
RGL/toolchain
scenario inputs
normalization version
```

release results should be deterministic.

Nondeterministic criteria must define:

- stable assertion strategy;
- bounded output;
- allowed variation;
- comparison policy.

---

# 93. Clean-build policy

Release validation must use current sources and current-run artifacts.

Recommended:

- fresh run directory;
- isolated `.gfo`;
- no dependency on global stale artifacts;
- no overwrite of previous release PGF;
- artifact provenance checked.

---

# 94. Release freshness

The approval record must identify the exact release commit.

Any source/config/scenario/gold/document change after the approval run invalidates approval unless the change is proven non-semantic and release policy permits a documentation-only refresh.

Recommended default:

```text
any tracked project change -> rerun required release validation
```

---

# 95. Documentation-only changes

A post-run documentation correction may avoid a full GF rerun only when:

- no source/config/scenario/gold/contract meaning changed;
- artifact identities unchanged;
- report/manifest unaffected;
- release reviewer approves;
- a documentation checker reruns;
- the approval record identifies the correction.

A contract or criterion change is not documentation-only.

---

# 96. Release retention

Retain release evidence according to project policy.

Recommended retained items:

- release manifest;
- final summary JSON;
- release approval;
- final PGF hash;
- source commit;
- project version;
- GF version;
- key scenario/gold evidence;
- migration notes.

Generated bulk logs may follow a documented retention policy.

---

# 97. Post-release verification

After publication:

```text
[ ] published artifact hash matches approved artifact
[ ] tag/release commit correct
[ ] release notes correct
[ ] downloadable PGF opens under supported consumer
[ ] known limitations visible
[ ] no artifact was rebuilt under same version
```

A defect requires a new project release version.

---

# 98. Release rollback

Before rolling back, review:

- project schema;
- public module contracts;
- scenario/gold compatibility;
- normalization version;
- expected PGF identity;
- consumer compatibility.

Forward migrations may not be reversible automatically.

---

# 99. Hotfix release

A hotfix still requires:

- identified affected criterion;
- targeted tests;
- required scenario/checkpoint rerun;
- final PGF rebuild;
- manifest;
- approval;
- new project version.

Do not replace published artifact bytes under the old version.

---

# 100. Criteria change control

Changing this document’s required meaning requires review of:

```text
project.toml
VALIDATION_SPEC.md
INTERFILE_CONTRACT_LOCK.md
STATUS_LEDGER.md
DECISION_LOG.md
scenarios
gold files
release reports
release process
```

A criterion ID is never silently reused for a different meaning.

---

# 101. Adding a criterion

Required:

```text
[ ] new stable gate ID
[ ] applicability defined
[ ] severity defined
[ ] owner defined
[ ] acceptance conditions defined
[ ] evidence defined
[ ] failure conditions defined
[ ] exception policy defined
[ ] validation spec updated
[ ] configuration updated if automated
[ ] reports updated
[ ] tests updated
```

---

# 102. Removing a criterion

Removing a required criterion is compatibility-sensitive.

Required:

- decision record;
- rationale;
- affected release scope;
- user impact;
- contract review;
- migration;
- release-note entry;
- retired gate ID retained historically.

---

# 103. Changing criterion severity

Changing:

```text
Advisory -> Release Blocking
```

may be a compatible tightening when it enforces an already documented requirement.

Changing:

```text
Release Blocking -> Advisory
```

weakens release guarantees and requires explicit project decision and compatibility review.

---

# 104. Gate tests

Recommended tests:

```text
tests/project/
├── test_release_gate_ids.py
├── test_release_gate_registry.py
├── test_release_gate_applicability.py
├── test_release_gate_statuses.py
├── test_release_gate_aggregation.py
├── test_release_required_skipped.py
├── test_release_project_config.py
├── test_release_source_inventory.py
├── test_release_contracts.py
├── test_release_dependency_map.py
├── test_release_research_evidence.py
├── test_release_scenarios.py
├── test_release_gold.py
├── test_release_pgf.py
├── test_release_manifest.py
├── test_release_regression.py
├── test_release_security.py
├── test_release_documentation.py
└── test_release_approval.py
```

---

# 105. Required test cases

## 105.1 Aggregation

```text
all required OK -> Ready
one required FAIL -> Not Ready
one required ERROR -> Blocked by Error
one required SKIPPED -> Not Ready or normalized ERROR
optional SKIPPED -> permitted
conditional true + SKIPPED -> blocked
conditional false -> Not Applicable
```

## 105.2 PGF

```text
process success + artifact exists -> OK
process success + artifact missing -> FAIL/ERROR
timeout -> ERROR
wrong artifact name -> FAIL
zero-byte artifact -> FAIL
manifest missing PGF -> FAIL/ERROR
```

## 105.3 Scenarios

```text
zero exit + markers complete + assertions pass -> OK
zero exit + marker missing -> FAIL
gold mismatch -> FAIL
timeout -> ERROR
launch failure -> ERROR
required scenario absent -> ERROR/config failure
```

## 105.4 Documentation

```text
required file missing
placeholder remains
old identifier remains
dependency map empty
research evidence required but empty
contract/provider mismatch
```

---

# 106. Release checker

Recommended command:

```text
gf-wordbench validate --mode release --strict
```

A future explicit project check may provide preflight:

```text
gf-wordbench project check --strict
```

The release checker must not treat Markdown checkboxes as authoritative completion.

It uses structured configuration and current run results.

Manual criteria are recorded separately and joined during approval.

---

# 107. Anti-drift indicators

Probable release-criteria drift exists when:

- `project.toml` requires a scenario absent here;
- this document requires a scenario absent from configuration;
- an expected PGF name differs from configuration;
- a release gate uses `PASS` instead of `OK`;
- applicability is encoded as `SKIPPED`;
- a required gate remains skipped in a successful release;
- file compilation is treated as complete release proof;
- a zero GF exit is treated as complete scenario proof;
- missing PGF is accepted;
- gold changes during normal validation;
- research evidence is omitted for linguistic acceptance;
- status-ledger blocker is ignored;
- dependency map is incomplete;
- contract lock contains unresolved placeholders;
- reports show `OK` while manifest verification fails;
- release run predates source changes;
- approval record lacks run ID;
- exception has no expiry;
- project identity differs between documents;
- an active template example remains;
- gate ID is reused with a new meaning.

Any indicator blocks final release review.

---

# 108. Template initialization checklist

```text
[ ] Replace `<PROJECT_OWNER>`
[ ] Replace `<PROJECT_ID>`
[ ] Replace `<PROJECT_NAME>`
[ ] Replace `<LANGUAGE_NAME>`
[ ] Replace `<LANGUAGE_CODE>`
[ ] Replace `<GF_MODULE_SUFFIX_OR_NONE>`
[ ] Replace `<SOURCE_ROOT>`
[ ] Replace `<RELEASE_ENTRYPOINT>`
[ ] Replace `<EXPECTED_PGF>`
[ ] Replace checkpoint table
[ ] Replace scenario table
[ ] Replace artifact table
[ ] Replace feature applicability table
[ ] Replace documentation-owner table
[ ] Add project-specific gates
[ ] Delete non-applicable examples
[ ] Align project.toml
[ ] Align VALIDATION_SPEC.md
[ ] Align INTERFILE_CONTRACT_LOCK.md
[ ] Align MODULE_DEPENDENCY_MAP.md
[ ] Align RESEARCH_EVIDENCE.md
[ ] Align STATUS_LEDGER.md
[ ] Align DECISION_LOG.md
[ ] Run placeholder scan
[ ] Run project check
[ ] Record initialization review
```

---

# 109. Release-readiness completion checklist

```text
[ ] Every required gate has an owner
[ ] Every required gate has executable or manual evidence
[ ] Every required gate is `OK`
[ ] No required gate is `SKIPPED`
[ ] No required result is `FAIL`
[ ] No required result is `ERROR`
[ ] Final release run is current
[ ] Expected PGF verified
[ ] Manifest verified
[ ] Regression review complete
[ ] Status ledger clear
[ ] Research evidence reviewed
[ ] Documentation complete
[ ] Security review complete
[ ] Approval recorded
```

---

# 110. Related template documents

```text
templates/project/project.toml
templates/project/docs/LANGUAGE_ARCHITECTURE.md
templates/project/docs/CATEGORY_AND_LINCAT_CONTRACT.md
templates/project/docs/MODULE_DEPENDENCY_MAP.md
templates/project/docs/RESEARCH_EVIDENCE.md
templates/project/docs/VALIDATION_SPEC.md
templates/project/docs/RELEASE_CRITERIA.md
templates/project/docs/STATUS_LEDGER.md
templates/project/docs/DECISION_LOG.md
templates/project/docs/INTERFILE_CONTRACT_LOCK.md
templates/project/validation/scenarios/
templates/project/validation/gold/
```

---

# 111. Related framework documents

```text
docs/projects/PROJECT_MODEL.md
docs/projects/PROJECT_DIRECTORY_LAYOUT.md
docs/projects/ADDING_A_NEW_LANGUAGE.md
docs/validation/VALIDATION_MODES.md
docs/validation/RELEASE_GATES.md
docs/validation/REGRESSION_COMPARISON.md
docs/gf/GF_MODULE_COMPILATION.md
docs/gf/GF_SCRIPT_EXECUTION.md
docs/gf/GF_VERSION_COMPATIBILITY.md
docs/scenarios/SCENARIO_FORMAT.md
docs/scenarios/GOLDEN_TESTS.md
docs/scenarios/OUTPUT_NORMALIZATION.md
docs/scenarios/UPDATING_GOLD_FILES.md
docs/reports/SUMMARY_JSON_REFERENCE.md
docs/reports/ARTIFACT_MANIFEST.md
docs/reference/STATUS_VALUES.md
docs/reference/EXIT_CODES.md
docs/development/BACKWARD_COMPATIBILITY.md
docs/release/VERSIONING_POLICY.md
docs/release/RELEASE_PROCESS.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/EXTERNAL_TOOL_CONTRACT_LOCK.md
docs/PERSISTED_SCHEMA_LOCK.md
SECURITY.md
```

---

# 112. Final rule

A release is a verified project state, not a successful command invocation.

Therefore:

> Initialize every criterion for the actual language project, require every applicable blocking gate to be `OK`, preserve raw and normalized evidence, verify the final PGF and manifest, review linguistic and contractual changes, and record approval only for the exact source revision that produced the release artifacts.
