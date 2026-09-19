# Validation-profile assets

This directory contains profile-owned validation assets. It never contains a
copy of the selected RGL language sources.

## Layout

```text
validation/
├── scenarios/
├── inputs/
└── gold/
```

## Ownership

- `scenarios/`: executable scenario scripts;
- `inputs/`: reusable external inputs;
- `gold/`: expected normalized outputs.

Module entrypoints and checkpoints refer to files in the resolved language
directory, not files copied here.

## Path rules

- all asset paths are relative to the profile root;
- no path may escape the profile root;
- no absolute machine path;
- no run output or temporary file;
- no source-language `.gf` copy unless a scenario explicitly needs a standalone
  fixture that is clearly identified as test data rather than canonical source.

## Registration

Assets are active only when referenced by the profile. Directory enumeration
does not define scenario order or requiredness.

## Validation

Before release use, verify:

- unique IDs;
- referenced files exist;
- required/optional sets do not overlap;
- gold normalization is declared;
- every release-required scenario appears in the coverage matrix.
