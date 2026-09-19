# Scenario inputs

This directory stores profile-owned test inputs that are not part of the
canonical language source tree.

## Suitable content

- parse or linearization examples;
- UTF-8 text fixtures;
- structured scenario parameters;
- representative regression cases.

## Unsuitable content

- copied RGL language directories;
- generated run output;
- secrets or credentials;
- machine-specific paths;
- files whose semantic owner is the language source tree.

## Identity

Each canonical input has a stable profile-relative path and is referenced by a
registered scenario. Renaming an input requires updating every reference and
the coverage matrix when applicable.

## Determinism

Inputs must be reviewable and deterministic. Encoding, normalization, and
newline assumptions must be explicit when they affect expected results.
