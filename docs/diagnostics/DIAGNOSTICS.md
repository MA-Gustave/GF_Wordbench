# GF Wordbench — Diagnostics

| Champ | Valeur |
|---|---|
| Document role | Diagnostic semantics authority |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Diagnostic class

```text
OK
DIRECT
DOWNSTREAM
AMBIGUOUS
NOISE
SKIPPED
```

## Error kind

```text
NONE
CONFIG
IO
TOOL
TIMEOUT
SYNTAX
TYPE
SCRIPT
INTERNAL
OTHER
```

## Finding

Un finding contient : identifiant, sévérité, classe, nature, message stable, cible, références de preuve, producteur et version.

## Règles

- la causalité est calculée à partir de résultats structurés ;
- le texte brut GF reste dans la preuve ;
- une classification ambiguë reste ambiguë ;
- un diagnostic non normatif ne satisfait pas une release gate ;
- l’absence de preuve ne devient pas un succès.
