# GF Wordbench — Scenarios and Golds

| Champ | Valeur |
|---|---|
| Document role | Scenario and gold contract |
| Decision status | Accepted |
| Implementation status | Implemented |
| Verification status | Runtime and test coverage present |
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

Pour une certification alignée Compendium, le profil de validation doit aussi
rendre traçables les éléments suivants, dans la documentation du scénario ou
dans la matrice de couverture du profil :

- `subsystem`;
- `target_symbol`;
- `feature_or_invariant`;
- `input`;
- `expected`;
- `evidence` (source linguistique ou décision acceptée);
- `test_kind`.

Le runtime `.gfs` n'impose pas encore tous ces champs comme syntaxe embarquée.
La matrice/profil reste donc l'autorité de provenance lorsque le format `.gfs`
ne les encode pas directement. Une sortie courante ne devient jamais un gold
par le seul fait qu'elle a été produite par GF.

## Normalisation

La normalisation retire uniquement les variations déclarées comme non sémantiques. Sa version est enregistrée et la sortie brute reste disponible.

## Mise à jour des golds

```text
gf-wordbench gold update --scenario <id>
```

L’opération affiche le diff, exige une intention explicite et ne s’exécute jamais pendant `validate`.
