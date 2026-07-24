# GF Wordbench — GF Command Construction

| Champ | Valeur |
|---|---|
| Document role | GF request construction authority |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

Les commandes GF sont construites par opérations nommées, jamais par concaténation dispersée.

## Données d’une requête

```text
operation_kind
gf_version
executable
arguments[]
working_directory
gf_path[]
stdin_script
expected_artifacts[]
timeout
```

## Règles

- utiliser des tableaux d’arguments ;
- ne pas dépendre du shell ;
- enregistrer une représentation redacted de la commande ;
- versionner les variations de syntaxe ;
- valider les modules et chemins avant lancement ;
- vérifier les artefacts après exécution ;
- traiter un artefact manquant comme une violation de contrat distincte.
