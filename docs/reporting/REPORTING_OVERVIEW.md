# GF Wordbench — Reporting Overview

| Champ | Valeur |
|---|---|
| Document role | Reporting and public artifact authority |
| Decision status | Accepted |
| Implementation status | Implemented |
| Verification status | Runtime and test coverage present |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-23 |

## Artefacts publics d’un run

| Fichier | Rôle |
|---|---|
| `summary.json` | Autorité machine du résultat. |
| `summary.md` | Vue humaine du même résultat. |
| `AI_READY.md` | Paquet borné pour analyse assistée. |
| `manifest.json` | Inventaire, rôles, tailles et intégrité. |
| `resolved-request.json` | Requête réellement exécutée. |
| `details/source_lock.json` | Empreinte SHA-256 du census source exact et version GF du Global Scan. |
| `details/rgl_coverage.json` | Couverture structurelle/module-level du census RGL; la couverture fonctionnelle non prouvée reste `not_assessed`. |
| `details/compendium_matrix.json` | Matrice TEST_RGL des niveaux de preuve Compendium; les niveaux non exécutés restent `not_assessed`. |

## Règles

- les rapports ne relancent aucune étape ;
- tous dérivent du même `RunResult` ;
- les chemins et preuves sont attribuables ;
- les champs persistés sont versionnés ;
- le Markdown n’est pas une API machine ;
- un consommateur externe utilise uniquement les artefacts publics et leurs schémas.

## Finalisation

Le manifeste est produit après les autres artefacts finalisés. Il ne se hache pas lui-même. Une finalisation partielle reste explicitement non complète.
