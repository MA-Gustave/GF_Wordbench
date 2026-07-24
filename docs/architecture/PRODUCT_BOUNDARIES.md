# GF Wordbench — Product Boundaries

| Champ | Valeur |
|---|---|
| Document role | Product boundary authority |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## GF Wordbench

Autorité pour la validation, les diagnostics, les preuves et la release d’un projet GF actif.

## Grammatical Framework

Autorité pour la syntaxe GF, le typage, la résolution de modules, la compilation, le runtime, le parsing, la linéarisation, la génération et les diagnostics natifs.

## Produits compagnons

Un produit compagnon peut consommer les artefacts publics versionnés de Wordbench. Wordbench ne dépend pas de ce produit, de ses schémas privés, de son état ou de ses services.

## Test d’indépendance

Wordbench doit pouvoir être installé, exécuté et testé lorsque tous les produits compagnons sont absents.

## Direction

```text
companion product -> public Wordbench artifacts
Wordbench -X-> companion product
```
