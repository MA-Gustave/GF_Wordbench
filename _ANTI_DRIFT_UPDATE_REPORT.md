# GF Wordbench — Anti-drift update report

Date: `2026-07-24`

## Existing anti-drift locks identified and rewritten

1. `docs/INTERFILE_CONTRACT_LOCK.md`
2. `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md`
3. `docs/PERSISTED_SCHEMA_LOCK.md`
4. `project/docs/INTERFILE_CONTRACT_LOCK.md`
5. `templates/project/docs/INTERFILE_CONTRACT_LOCK.md`

The three framework locks and the generic template lock were rewritten rather than patched because the snapshot contained extensive legacy paths and implementation-specific assumptions. The Albanian active-project lock preserves its concrete identity and declared module/scenario contracts while adding the current product boundary and retaining unresolved release locks.

## New anti-drift controls

1. `docs/DOCUMENTATION_ALIGNMENT_LOCK.md`
2. `docs/DOCUMENTATION_CORRECTION_LEDGER.md`

## Locked decisions

- one active GF language project per Wordbench workspace;
- one resolved project and normative language target per run;
- GF authority with separate static scan and GF execution stages;
- native `.gfs` scenarios, raw evidence, named normalization and reviewed golds;
- hexagonal modular-monolith target with implementation status kept explicit;
- `gf-portfolio` as an independent optional consumer of public versioned artifacts;
- no reverse Wordbench dependency on Portfolio;
- no Portfolio registry or aggregation state in Wordbench schemas;
- controlled allowlist for executable diagnostic tools.

## Queue state

- 153 audited paths;
- 53 previously corrected minor files;
- 100-file remaining queue reconstructed;
- 3 queue locks corrected in this update and awaiting repository implementation verification;
- 97 queue files remain unedited.
