# Validation profile release criteria

## Principle

A profile may strengthen release requirements for a resolved language. It does
not define where the language lives or where Wordbench writes outputs.

A release decision is valid only when all required evidence comes from the
current run and matches the selected language and profile.

## Required categories

Complete only the categories used by this profile.

### Compatibility

- expected language key matches, when declared;
- profile schema is supported;
- no unresolved placeholders;
- no profile path escapes its owning root.

### Source and modules

- required and release entrypoints exist in the resolved inventory;
- required checkpoints pass in declared order;
- profile selection rules do not exclude required modules;
- no generated run output is selected as source.

### Scenarios and golds

- every required scenario is registered;
- every referenced script/input/gold exists;
- required scenarios pass;
- required gold comparisons pass under the declared normalization policy.

### Artifacts

- every required artifact is produced by the current run;
- hashes, sizes, media types, and requiredness are verified;
- PGF requirements are enabled only when targets and verification are defined.

### Quality gates

- required architecture, contract, schema, typing, lint, and test gates pass as
  declared by the release policy;
- approved exceptions are explicit, owned, justified, and reviewable.

## Release decision

A profile-driven release is `PASS` only when:

```text
compatibility passes
AND required modules/checkpoints pass
AND required scenarios/golds pass
AND required artifacts verify
AND required quality gates pass
AND no blocking exception remains
```

Otherwise the decision is `FAIL` or `BLOCKED` according to the canonical release
status model.

## Evidence rules

- current-run evidence only;
- no manual claim substitutes for a missing result;
- no stale PGF or manifest satisfies a gate;
- skipped required checks block release;
- optional checks must not silently become required.

## Profile checklist

- [ ] release policy adds value beyond default validation
- [ ] release entrypoints declared
- [ ] checkpoints declared where required
- [ ] required scenarios and golds declared
- [ ] expected artifacts declared
- [ ] quality gates declared
- [ ] exception policy documented
- [ ] coverage matrix complete
