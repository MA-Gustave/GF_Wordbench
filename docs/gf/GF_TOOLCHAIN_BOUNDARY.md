# GF Wordbench — GF Toolchain Boundary

| Champ | Valeur |
|---|---|
| Document role | External GF contract |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Autorité GF

GF possède la vérité pour : syntaxe, typage, imports, compilation, PGF, chargement, parsing, linéarisation, génération, morphologie et diagnostics natifs.

## Autorité Wordbench

Wordbench possède : sélection du binaire, construction structurée des requêtes, working directory, environnement, timeouts, capture, vérification d’artefacts, normalisation, assertions, comparaison, classification et reporting.

## Interface cible

```text
GfToolPort
├── probe_version()
├── compile_module()
├── build_pgf()
├── run_scenario()
└── inspect_grammar()
```

Chaque réponse contient des références vers stdout, stderr, commande résolue, version GF et artefacts observés.

## Interdictions

- aucune commande GF dans le domaine ;
- aucun parseur de diagnostic GF dans CLI ou GUI ;
- aucun succès déduit du seul exit code lorsque des artefacts sont requis ;
- aucune normalisation destructive de la preuve brute.
