# Defluens — Stabilisation lexicale v0.2.1 (14 langues)

Cette version corrige des **sondes WordBench**, et non les sources de la RGL. Les 14 langues et les 15 capacités restent inchangées; aucun temps verbal optionnel n’est ajouté.

## Évidence du cycle précédent

Le rapport GF réel du 3 novembre 2026 (`defluens-batch-full-20261103T194811Z-5485600.zip`) contient 210/210 générations candidates, zéro sonde en échec, 115 sources modifiées par la v0.2.0, et 36 chaînes de sortie modifiées par rapport au bilan historique. Les 210 résultats **ne sont pas des golds**.

## Réparations proposées

Les modifications v0.2.1 privilégient (a) les formes irrégulières réellement présentes dans `Irreg<Lang>.gf`, (b) les paradigmes de flexion explicitement documentés dans `Paradigms<Lang>.gf`, (c) des substitutions lexicales conservatrices quand le sens historique était erroné. Tous les changements sont décrits dans `pilots/practical_generation_v1/lexical_stabilization_focus14_v021.json`.

**Risques à vérifier sous GF Windows :** surcharge `mkV` des préfixes en allemand et néerlandais, nouveau verbe pronominal français, choix de copule pour l’état passé espagnol/portugais, inflexions scandinaves et auxiliaires des passés composés. Les scripts SHA-256 et manifests ont été mis à jour. GF n’est pas installé dans cet environnement; les expressions sont des propositions non certifiées.

## Exécuter

Copier le correctif à la racine du dépôt `GF_Wordbench`, pas depuis Downloads.

```powershell
cd 'C:\mycode\Grammatical-Framework\GF_Wordbench'
.\Lancer_Alignement_14_Langues.bat check
.\Lancer_Sondes_Corrigees_14_Langues.bat
.\Lancer_Alignement_14_Langues.bat full
.\Lancer_Alignement_14_Langues.bat compare
```

Les sondes non modifiées restent dans leur état v0.2.0. **L’absence de diff de sortie ne vaut pas validation linguistique.** La nouvelle campagne et son ZIP serviront à examiner les gains et régressions sans modifier le rapport antérieur.

## Problèmes restant explicitement ouverts

- Estonien : la condition dans `conditional-instruction` disparaît, et le marquage `&+` demeure dans certaines sorties.
- Français : des marqueurs de liaison `&+` apparaissent dans les logs bruts; traiter la tokenisation en conservant toujours le brut.
- Portugais : le passé simple accompli demande un choix de réalisation plus fin que `pastTense` tel qu’exposé par ces sondes.
- Afrikaans : passés, infinitifs des modaux et négation impérative demandent une stratégie linguistique spécifique.
- Plusieurs variantes lexicales peuvent rester acceptables; ne jamais exiger l’identité de chaînes entre les langues.


Le lanceur sélectif écrit un unique ZIP `defluens-stabilization-v021-*.zip` sous `Downloads/Ars_Magna_Defluens/practical_pilot_runs`. Le lot complet reste disponible avec `Lancer_Alignement_14_Langues.bat full`.
