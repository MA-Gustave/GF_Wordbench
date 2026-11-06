# Ars Magna Defluens / GF WordBench v0.2.2

## Démarrage à partir de v0.2.1

Les deux archives `defluens-batch-full-20261103T202946Z-8615600.zip` sont identiques (SHA-256 identique).
La régression réelle de v0.2.1 confirme 210/210 sorties candidates, 0 échec et 0 délai.
La revue IA est reconduite avec empreintes égales pour les 210 sources/scripts : 197 acceptables, 7 défauts, 4 jonctions `&+` à présenter correctement, 2 interprétations futures contextuelles. Aucun gold certifié.

## Sept propositions de réparation GF (non exécutées ici)

| Langue | Capacité | Avant | Réalisation recherchée | Méthode RGL |
|---|---|---|---|---|
| Afr | past-event | `Mira aankom` | `Mira het aangekom` | `anteriorAnt`, paradigme avec participe explicite |
| Afr | obligation | `jy moet te wag` | `jy moet wag` | composition du modal fini et infinitif RGL sans `te` |
| Afr | possibility | `Mira kan te terugkeer` | `Mira kan terugkeer` | même construction locale avec modal `kan` |
| Afr | prohibition | `wag nie` | `moenie wag nie` | impératif RGL encadré par la négation afrikaans |
| Est | conditional-instruction | `oota` | `oota kui Mira saabub` | impératif et subordonnée RGL assemblés après réalisation |
| Por | past-event | `Mira chegava` | `Mira chegou` | `RPasse` de `TPastSimple` dans la RGL portugaise |
| Por | conditional-instruction | `espere se Mira chega` | `espere se Mira chegar` | futur du subjonctif dans `BeschPor.chegar_Besch` |

Il s'agit de propositions **GF** : leurs signatures ont été vérifiées dans le code RGL fourni; l'exécution de leur combinaison exige GF 3.12 sur Windows. Aucun correctif RGL n'est appliqué directement.

## Rendu des marqueurs GF

`gf_wordbench.practical.review022` produit un `candidate_rendered_preview` pour `&+` et préserve `candidate_raw`, son empreinte et les journaux. Les quatre cas actuels sont Fre/factual-negation, Fre/prohibition, Est/obligation et Est/possibility. La prévisualisation n'est pas une transformation de la preuve ni une approbation linguistique.

## Incertitudes conservées

Fin/future-reference et Est/future-reference restent idiomatiques en contexte mais insuffisamment ancrées temporellement si la phrase est isolée. De futures variantes devront ajouter un adverbe temporel. Cela ne nécessite pas l'inventaire complet des conjugaisons.

## Commandes

```powershell
cd 'C:\mycode\Grammatical-Framework\GF_Wordbench'
.\Lancer_Sondes_Corrigees_14_Langues_v022.bat
```

Le ZIP de résultat `defluens-stabilization-v022-*.zip` sera enregistré dans `Downloads\Ars_Magna_Defluens\practical_pilot_runs`. Envoie cette archive **même si certaines sondes échouent**.

Une fois les sept sondes évaluées, relancer la campagne intégrale `Lancer_Alignement_14_Langues.bat full`. Tous les statuts restent candidats; aucune certification automatique.
