# Gold outputs

Gold files record expected results for registered scenarios.

## Ownership

A gold belongs to the validation profile. It does not define language identity,
source location, or release status by itself.

## Required metadata

The referencing scenario or validation specification must define:

- producer scenario;
- input;
- normalization;
- comparison mode;
- encoding;
- requiredness.

## Update policy

Update a gold only after reviewing the behavioral change. Regeneration alone is
not approval.

For every update record:

- reason;
- affected scenario;
- reviewer/owner;
- compatibility or release impact.

## Safety

Golds must not contain:

- machine-specific absolute paths;
- volatile timestamps unless normalized;
- nondeterministic ordering;
- secrets;
- stale output copied from an unrelated language or profile.

A missing or mismatched required gold blocks the gate that requires it.
