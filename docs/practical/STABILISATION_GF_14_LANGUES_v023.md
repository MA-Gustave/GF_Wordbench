# Ars Magna Defluens — stabilisation GF v0.2.3

## Source de diagnostic

Rapport réel Windows `defluens-stabilization-v022-20261103T211036Z-0097800.zip` : 4 candidats, 3 erreurs GF, 0 timeout.

| Code | Scénario | Diagnostic réel GF 3.12 | Correction proposée |
|---|---|---|---|
| Afr | obligation | `type of youSg_Pron expected Str` | Construire la chaîne en utilisant les champs nominatif du pronom et des verbes typés `V` |
| Afr | possibility | `no overload instance of ParadigmsAfr.mkPN` | Utiliser le nom invariable `Mira` et les formes verbales RGL typées `V` |
| Por | conditional-instruction | `constant not found: Sg`, `P3` | Importer `CommonRomance` (qui étend `ParamX`) et qualifier `C.Sg` / `C.P3` |

Les quatre sondes déjà générées correctement (Afr/past-event, Afr/prohibition, Est/conditional-instruction, Por/past-event) sont inchangées.

## Périmètre et critères

- Trois scénarios corrigés sur les 210 existants ; aucune nouvelle catégorie sémantique ni obligation de couvrir tous les temps.
- Verrouillage SHA-256 des modules GF et scripts `.gfs` mis à jour dans les manifestes.
- Ne modifie **jamais** `gf-rgl`, aucun `.gold` approuvé, aucune couverture sémantique certifiée automatiquement.
- Les propositions utilisent des formes verbales calculées par `ParadigmsAfr` et `BeschPor`, sans chaînes contenant une phrase cible complète.
- Il faut tester sur GF 3.12 Windows pour confirmer types, linéarisation et grammaticalité.

## Installation

Depuis la racine du dépôt **complet** WordBench, après superposition du correctif :

```powershell
.\Lancer_Sondes_Corrigees_14_Langues_v023.bat
```

Le ZIP `defluens-stabilization-v023-*.zip` est créé dans `%USERPROFILE%\Downloads\Ars_Magna_Defluens\practical_pilot_runs`. Envoie-le même si l'un des trois scénarios échoue.
