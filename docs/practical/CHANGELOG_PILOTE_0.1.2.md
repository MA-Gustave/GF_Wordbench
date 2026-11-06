# Ars Magna Defluens — WordBench practical pilot v0.1.2

## Motif du correctif

Rapport réel `Eng full` du 3 novembre 2026 (`20261103T150609Z-1043700`) : **9 candidates** et **6 erreurs de sonde**, aucune expiration. Les résultats sont des exécutions GF 3.12 authentiques, mais **aucun gold linguistique n'est approuvé**.

Les six erreurs de compilation appartiennent aux **sondes de validation**, et ne sont pas une preuve d'incapacité de la RGL anglaise.

## Corrections appliquées (Eng, Fre et Sqi)

| Capacité | Cause constatée dans `Eng full` | Correctif |
|---|---|---|
| `temporal-order` | `mkAdv` résolu comme paradigme lexical `Str -> Adv`, au lieu de `Prep -> NP -> Adv` | Appel qualifié `Syntax<Lang>.mkAdv` |
| `condition-real` | `mkS S Subj S` est une surcharge inexistante | `mkS (Syntax<Lang>.mkAdv if_Subj <condition>) <principale>` |
| `source-attribution` | `mkVS` reçoit `Str` alors que ce paradigme attend `V` | `mkVS (mkV "...")` |
| `quantity` | Parenthèse fermante supplémentaire | Rééquilibrage de l'expression |
| `location` | Même collision `mkAdv` que `temporal-order` | Appel qualifié `Syntax<Lang>.mkAdv` |
| `conditional-instruction` | Même collision `mkAdv`, mais avec `Subj -> S -> Adv` | Appel qualifié `Syntax<Lang>.mkAdv` |

Le **générateur** `tools/generate_practical_pilots.py` est corrigé pour que ces changements survivent aux régénérations. Les `.gf`, `.gfs` et `pilot_manifest.json` des **trois** langues ont été régénérés avec leurs empreintes SHA-256 cohérentes.

## Protection des preuves

La sortie GF contenant une erreur de compilation entre deux marqueurs ne doit jamais apparaître dans `candidate` ou dans le modèle de revue. Les erreurs restent dans `.stdout.txt`/`.stderr.txt`, avec `status = probe_failed` et `candidate = null`.

Le répertoire de résultats et les ZIP automatiques restent **dans Downloads**, comme en v0.1.1 : `%USERPROFILE%\Downloads\Ars_Magna_Defluens\practical_pilot_runs`.

## Validation et limites

- Contrôles Python locaux des scénarios/empreintes, tests de l'outil de lancement et faux exécutable GF pour les erreurs.
- **Pas d'essai avec `gf.exe` 3.12 sous Windows** dans l'environnement de création. Refaire `Lancer_Pilote_Pratique.bat Eng full` pour confirmer la compilation.
- `candidate_for_review` n'est pas `passed` et ne certifie aucune des 15 fonctions linguistiques.
- Les variantes françaises et albanaises utilisent encore des lexèmes provisoires et nécessitent leurs propres essais/revues.

## Installation

Décompresser **le correctif** à la racine `C:\mycode\Grammatical-Framework\GF_Wordbench` (les chemins du ZIP commencent par `src/`, `tools/`, `pilots/`, `tests/`, `docs/`). Puis :

```powershell
.\Lancer_Pilote_Pratique.bat Eng full
```

Envoyer le nouveau ZIP généré dans Downloads pour continuer le diagnostic.
