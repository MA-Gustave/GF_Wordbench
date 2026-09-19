# Validation profile specification

## 1. Objective

A validation profile adds explicit validation and release policy to a language
that Wordbench has already resolved from an existing RGL source tree.

It is optional. It does not own source discovery, language identity, RGL
location, GF executable resolution, or run output.

## 2. Inputs to a profiled run

A profiled run combines three independent authorities:

1. `ResolvedLanguageContext`: selected language facts;
2. validation profile: additional policy;
3. environment/run configuration: machine and execution facts.

The run must reject contradictions instead of silently choosing one authority.

## 3. Compatibility

A profile may declare `expected_language_key`. When present, it must match the
resolved language key.

Compatibility checks may also validate:

- required modules are in the resolved inventory;
- profile-required capabilities are supported;
- referenced scenario and gold files exist;
- schema version is supported.

## 4. Selection policy

Profile include/exclude rules are additional constraints applied within the
already resolved language directory.

They may not:

- select files outside that directory;
- replace the canonical source inventory;
- add generated run output as source;
- weaken mandatory safety exclusions.

## 5. Module policy

Profiles may distinguish:

- `required_entrypoints`: must load or compile for the selected mode;
- `release_entrypoints`: must pass for release;
- `checkpoints`: ordered modules proving architectural layers.

All module paths are relative to the resolved language directory. Discovery of
candidate entrypoints remains owned by language resolution; the profile states
which discovered modules are required.

## 6. Scenarios

Each scenario has:

- stable ID;
- profile-relative script path;
- optional input path;
- optional gold path;
- required/optional status;
- applicable modes;
- normalization and comparison policy when needed.

Scenario files do not become source-language owners.

## 7. Inputs

Input files contain reusable test data. They must be deterministic, reviewable,
UTF-8 unless another encoding is explicitly required, and free of machine-local
paths or secrets.

## 8. Golds

Gold files are expected results for a declared scenario and normalization
policy. A gold is valid only when its producer inputs, normalization, and
comparison rules are documented.

Missing required golds block the scenario or release gate that requires them.
Optional scenarios may define a documented non-blocking policy.

## 9. Release policy

A profile may require:

- release entrypoints;
- checkpoints;
- scenarios;
- expected artifacts;
- PGF targets;
- quality gates;
- approved exceptions with owners and expiry/review conditions.

Release decisions must use evidence from the current run. Stale artifacts do not
satisfy a gate.

## 10. Output ownership

The profile never declares a run output directory. Wordbench writes logs,
reports, temporary files, and artifacts under its configured output root,
normally partitioned by language key and run ID.

## 11. Failure classes

Profile validation must report structured failures for:

- unsupported schema;
- language-key mismatch;
- unsafe or escaping path;
- missing module;
- duplicate ID;
- missing scenario/input/gold;
- contradictory required/optional membership;
- release requirement without evidence definition;
- profile attempt to override resolved or environment-owned facts.

## 12. Minimal profile

A profile with no scenarios and no release policy is valid only when it still
adds useful policy, such as required entrypoints or checkpoints. Otherwise,
running without a profile is preferable.

## 13. Migration from the legacy project model

Legacy profiles may contain project-owned source directories, GF path parts, and
active-language identity. Migration must:

1. resolve the language externally;
2. move language facts to `ResolvedLanguageContext`;
3. move machine facts to environment configuration;
4. retain only non-deducible validation policy;
5. update tests and documentation;
6. preserve scenario and gold IDs where their semantics remain valid.
