# GF Wordbench — Scenarios and Golds

| Champ | Valeur |
|---|---|
| Document role | Scenario and gold contract |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Emplacements

```text
project/validation/scenarios/<scenario-id>.gfs
project/validation/inputs/
project/validation/gold/<scenario-id>.gold
```

## Contrat scénario

Un scénario possède : identifiant stable, but unique, entrée revue, marqueurs début/fin, sortie bornée, timeout et arrêt explicite.

## Normalisation

La normalisation retire uniquement les variations déclarées comme non sémantiques. Sa version est enregistrée et la sortie brute reste disponible.

## Mise à jour des golds

```text
gf-wordbench gold update --scenario <id>
```

L’opération affiche le diff, exige une intention explicite et ne s’exécute jamais pendant `validate`.
