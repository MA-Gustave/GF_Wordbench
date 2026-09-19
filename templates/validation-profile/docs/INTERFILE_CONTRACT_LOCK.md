# Validation-profile interfile contract lock

## Scope

This lock applies to `templates/validation-profile/` and to every profile
created from it.

## One profile, one policy package

One profile describes one coherent validation policy package. It may be reused
only when its compatibility constraints and policy are valid for the resolved
language.

A Wordbench installation may contain many profiles. A run selects zero or one
profile explicitly.

## Ownership lock

| Concern | Authoritative owner |
|---|---|
| selected source path | resolved language context |
| language directory and language key | resolved language context |
| RGL root and observed source inventory | resolved language context |
| executable and environment | environment configuration |
| run mode, budgets, output root | run request/configuration |
| profile ID and compatibility guard | `project.toml` profile metadata |
| additional selection rules | `project.toml` selection policy |
| required entrypoints and checkpoints | `project.toml` module policy |
| scenarios and gold references | `project.toml` plus validation files |
| release requirements | `project.toml` plus release criteria document |
| produced evidence | current Wordbench run |

No profile document may claim ownership of a concern owned elsewhere.

## Path lock

- language module paths are relative to the resolved language directory;
- profile assets are relative to the profile root;
- paths must be normalized and must not escape their owner root;
- absolute machine-specific paths are forbidden;
- output and temporary paths are never profile-owned.

## Consistency lock

The following must agree:

- scenario IDs in `project.toml`, the scenario directory, coverage matrix, and
  release criteria;
- gold IDs and paths in scenario declarations and `validation/gold/`;
- required entrypoints/checkpoints and the resolved source inventory;
- release gates and the evidence described by the validation specification.

A mismatch is an error. Do not infer missing policy from filenames.

## Compatibility lock

`compatibility.expected_language_key` is a guard, not an identity source. When
present, it must equal the resolved language key. It cannot change the selected
language.

## Template neutrality

The template must not contain:

- a real language path or source inventory;
- a concrete local RGL installation;
- a machine-specific executable;
- another language's identifiers;
- final gold values presented as universal;
- enabled release requirements without matching evidence definitions.

## Change protocol

When a profile contract changes:

1. update `project.toml`;
2. update referenced scenarios, inputs, or golds;
3. update the coverage matrix;
4. update release criteria when release evidence changes;
5. update compatibility/migration notes;
6. validate all references before release use.
