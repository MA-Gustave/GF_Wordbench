# WordBench → SemantiK typed-attribute candidate (v0.7)

`tools/build_semantik_profile3_candidate.py` now supports a second **explicit** `--profile defluens-attribute-fr-1`, using the same WordBench compilation/process/hash-lock mechanism as the previous `konstellation-explorer-3` development profile. This is a small, RGL-backed demonstration of Semantic Architect's already-defined `clause.copular_attribute` operation.

- `--rgl-root` is mandatory for the new profile and must contain `src/api/SyntaxFre.gf` and standard RGL source directories.
- Source grammar and all bridge/profile/lexical contracts are **owned by SemantiK Architect** under `profiles/defluens-attribute-fr-1/`.
- Builds generate a separate `grammar.pgf`, `pipeline.lock.json` and `build-report.json` in the candidate output directory. Existing outputs are backed up when `--force` is used.
- Not a WordBench release artifact, not a SA `RELEASED` RuntimeSet. The old five-case profile remains unchanged.
- Test assertions against a fake executable only verify builder wiring and hashes; they do not establish linguistic correctness or GF 3.12 build success. The real compile belongs on the user Windows machine.
