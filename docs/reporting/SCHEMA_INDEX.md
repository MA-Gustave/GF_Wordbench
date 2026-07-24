# GF Wordbench — Schema Index

| Champ | Valeur |
|---|---|
| Document role | Persisted schema authority |
| Decision status | Accepted |
| Implementation status | Not implemented |
| Verification status | Documentation review required |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

| Schema ID | Rôle |
|---|---|
| `gf-wordbench.project/1.0` | Configuration portable du projet actif. |
| `gf-wordbench.app-state/1.0` | Préférences locales non normatives. |
| `gf-wordbench.run-summary/1.0` | Résultat machine d’un run. |
| `gf-wordbench.artifact-manifest/1.0` | Inventaire des artefacts. |
| `gf-wordbench.scenario-output/1.0` | Sortie normalisée d’un scénario. |
| `gf-wordbench.scenario-gold/1.0` | Métadonnées d’une référence revue. |

## Règles

- `schema_id` et `schema_version` sont obligatoires ;
- un changement incompatible incrémente la version majeure ;
- un lecteur rejette explicitement une version future inconnue ;
- une migration ne modifie jamais silencieusement la preuve source ;
- les schémas d’un autre produit n’appartiennent pas à cet index.
