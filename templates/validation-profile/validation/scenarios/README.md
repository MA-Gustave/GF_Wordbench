# Scenario scripts

Scenario scripts exercise behavior that source scanning and module compilation
cannot prove alone.

## Registration

Each scenario must be registered in the validation profile with:

- stable scenario ID;
- script path;
- required or optional status;
- applicable modes;
- input and gold references when used;
- normalization/comparison policy when used.

Filesystem order is not authoritative.

## Script rules

- deterministic;
- non-interactive unless explicitly supported;
- no machine-specific absolute path;
- no dependency on prior run output;
- no mutation of canonical language sources;
- clear timeout and failure behavior through canonical run configuration.

## Language sources

A scenario runs against the resolved language context. Do not copy the language
into this directory.

## Required scenarios

A missing or skipped required scenario blocks the gate that requires it.
Optional scenarios remain non-blocking unless release policy explicitly promotes
them.
