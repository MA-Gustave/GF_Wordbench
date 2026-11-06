# WordBench — explicit diK → SemantiK lexical bindings (v0.9)

This is a **reviewed mapping candidate** builder, not a GF compiler, conjugator,
semantic authority, source importer or release orchestrator.

## Development workflow

1. In diK, produce the immutable `semantik.knowledge.json` candidate and the
   `gf-mapping-review.template.json`.
2. **Copy** the template outside the original bundle. Review source identity,
   source rights, target semantic authority and the *actual* GF function/category.
3. For an accepted decision, explicitly set: `decision=accept`, `reviewer`,
   `mapping_reviewed=true`, `license_reviewed=true`,
   `semantic_identity_reviewed=true`, `target_semantic_ref`,
   `semantic_authority_ref`, `gf_function`, `gf_category`.
   Reject or leave unreviewed any unsupported correspondence.
4. Run:

```powershell
cd C:\mycode\Grammatical-Framework\GF_Wordbench
python tools\build_dik_semantik_lexicon.py build --dik-bundle C:\lex-data\sa-knowledge-fr --decisions C:\lex-data\gf-mapping-review.edited.json --output C:\lex-data\wordbench-fr
python tools\build_dik_semantik_lexicon.py audit --bundle C:\lex-data\wordbench-fr
```

Output: candidate SemantiK lexical schema v1.1, SHA-256 manifest and unchanged
Wikidata knowledge records. Approved **references** are encoded as
`source_kind=project`, `use_for=binding`, `binding_kind=gf_expr`; each records its
original source Lexeme and explicit target semantic owner. There is no promise
that the referenced function exists in a compiled PGF. `gf_verified=false`,
`released=false` and `activated=false` are invariant.

## Separation of authorities

- diK: lexical evidence and dictionary governance.
- WordBench: GF mapping review and later GF/PGF compilation/validation.
- SemantiK Architect: semantic request planning and lexical binding/realization.
- Runtime Orchestrator: production conformance/release/activation.
- Spek: documents **only**, not dictionary management.
- Defluens: local orchestration, not a lexical database.

A candidate mapping to a Kristal semantic reference requires an *independent,
explicitly authorized* semantic identity decision; GF/diK never mint one.
