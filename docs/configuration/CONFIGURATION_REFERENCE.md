# GF Wordbench — Configuration Reference

| Champ | Valeur |
|---|---|
| Document role | Configuration precedence authority |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Ordre de résolution

```text
framework defaults
→ project/project.toml
→ local environment configuration
→ explicit CLI or GUI overrides
→ immutable resolved request
```

## Propriétaires

| Donnée | Propriétaire |
|---|---|
| Identité et politique du projet | `project/project.toml` |
| Chemins locaux GF/RGL/output | environnement ou état local |
| Valeurs par défaut globales | framework |
| Choix d’un run | requête explicite |

La configuration est résolue une seule fois avant exécution. Les stages reçoivent un objet résolu et ne relisent pas indépendamment l’environnement.
