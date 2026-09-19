# GF Wordbench — Validation Profile Completion Checklist

**Document ID:** `GF-WB-PROFILE-COMPLETION-CHECKLIST`
**Status:** Normative checklist
**Last reviewed:** 2026-08-05

A profile is optional. This checklist applies only when one is explicitly used.

## Context compatibility

- [ ] The GF language path resolves without the profile.
- [ ] The profile was selected explicitly.
- [ ] Profile compatibility assertions match `ResolvedLanguageContext`.
- [ ] The profile does not redefine language identity, source roots, or GF paths.

## Portability

- [ ] All profile-owned paths are relative and contained.
- [ ] No machine-local RGL, GF executable, output, state, or run paths are stored.
- [ ] Deprecated `sources.directory` and `gf.path_parts` are absent from canonical output.
- [ ] No unresolved placeholders remain.

## Modules and selection

- [ ] Additional source filters are necessary and deterministic.
- [ ] Required entrypoints are explicit.
- [ ] Checkpoints are explicit and ordered.
- [ ] The profile does not duplicate the source-selection algorithm.

## Scenarios and golds

- [ ] Scenario IDs are unique and portable.
- [ ] Required and optional status is explicit.
- [ ] Scenario, input, and gold files exist and are contained.
- [ ] Golds are reviewed and not updated by normal validation.

## Release policy

- [ ] Release entrypoints and PGF targets are explicit where required.
- [ ] Expected artifacts are declared.
- [ ] Every required gate is evaluable.
- [ ] No flag can silently bypass a mandatory gate.
- [ ] Known limitations and release blockers are recorded.

## Evidence

- [ ] A compatible baseline run exists when regression comparison is required.
- [ ] Run summaries and manifests identify one resolved language and one profile version.
- [ ] Generated evidence is outside source and profile roots.
- [ ] No stale artifact can satisfy a current run.

## Completion rule

A profile is complete only when all applicable required items pass. The absence of a profile does not block basic source-ready, scan-ready, or compile-ready use.
