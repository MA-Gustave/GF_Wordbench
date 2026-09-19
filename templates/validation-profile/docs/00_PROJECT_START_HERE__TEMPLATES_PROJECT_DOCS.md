# Start here — validation profile

> The legacy filename contains `PROJECT` for compatibility. This document
> describes an optional **validation profile**, not a copied or self-contained
> language project.

## What to select

Select a language directory or `.gf` file in the existing RGL checkout.
Wordbench resolves the language directory, RGL source root, language key,
source inventory, and candidate entrypoints from that selection.

Do not copy the language into the Wordbench repository or into this profile.

## When to use a profile

Use a profile when the validation contract contains policy that source
inspection cannot determine reliably:

- required or release entrypoints;
- ordered architectural checkpoints;
- scenario membership;
- external scenario inputs;
- expected gold output;
- release artifacts and gates;
- approved exceptions or limitations.

Do not use a profile merely to repeat:

- the selected language path;
- the RGL root;
- the language source inventory;
- the GF executable;
- the output directory;
- application preferences.

## Setup

1. Copy the validation-profile template to a controlled profile location.
2. Edit `project.toml`.
3. Keep every file reference relative to the profile root.
4. Create scenario, input, and gold files only when needed.
5. Attach the profile explicitly when starting a run.
6. Validate the profile against the resolved language context.

## Runtime relationship

```text
resolved language facts + optional profile policy + environment/run settings
                                  │
                                  ▼
                         one validation run
                                  │
                                  ▼
               isolated Wordbench run output and evidence
```

The profile cannot replace or contradict resolved language facts. A mismatch is
a configuration error.

## Required reading

1. `INTERFILE_CONTRACT_LOCK.md`
2. `VALIDATION_SPEC__TEMPLATES_PROJECT_DOCS.md`
3. `TEST_COVERAGE_MATRIX__TEMPLATES_PROJECT_DOCS.md`
4. `RELEASE_CRITERIA__TEMPLATES_PROJECT_DOCS.md`
5. `../validation/README.md`

## Ready-for-use checklist

- [ ] profile has a stable profile ID
- [ ] compatibility language key is correct, when declared
- [ ] required entrypoints and checkpoints are source-relative paths
- [ ] scenarios and golds are profile-relative
- [ ] no source, executable, RGL, output, or temporary absolute paths
- [ ] release requirements are disabled until evidence requirements are complete
