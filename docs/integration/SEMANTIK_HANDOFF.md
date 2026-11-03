# SemantiK candidate handoff

GF Wordbench 1.4 can inspect candidate bundles emitted by SemantiK Phrase Ops Console.

```bash
python -m gf_wordbench.validation.semantik_handoff <handoff.zip>
```

The inspector verifies the handoff schema, identities, aggregate counts and every declared SHA-256. A valid handoff is accepted only as **input to Wordbench validation**. It is never a linguistic verdict, a gold, a PGF release decision, or release evidence by itself.

This preserves the authority boundary: Phrase Ops may discover and package a candidate; Wordbench must reproduce GF/scenario evidence and own linguistic/release decisions.
