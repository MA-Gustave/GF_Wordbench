# Ars Magna Defluens — Alignement RGL ciblé, v0.2.0

## Ce que nous avons réellement fait

Cette version travaille exclusivement sur **14 langues** : Eng, Fre, Spa, Ger, Dut,
Swe, Dan, Nor, Nno, Fin, Est, Afr, Ita, Por. Elle préserve **les mêmes 15
intentions sémantiques**; elle ne cherche pas une couverture exhaustive des temps
verbaux, aspects, modes ou constructions stylistiques.

Le moteur de génération se fonde désormais, pour les scénarios pertinents, sur les
**sources réelles du Lexicon RGL** : `book_N`, `house_N`, `say_VS` et, lorsqu'une
implémentation existe, `ready_A`. `LexiconXXX` est ouvert comme ressource `L`,
selon un patron attesté dans `ConstructionEng.gf`, `ConstructionFre.gf`, etc.

Autres adaptations : le genre féminin explicitement donné au **personnage-test**
Mira lorsqu'il est exprimable par `mkPN`, le genre de quelques substantifs
(`réunion`, `Besprechung`, `Gerät`), des infinitifs de *retour* plus précis en
Dan/Nor, et une hypothèse `anteriorAnt` pour l'événement passé accompli en
Fre/Spa/Ita. Ce dernier point demande un contrôle réel par GF et une évaluation
sémantique locale. Le présent, le passé-événement, le passé-état et le futur
restent les seules quatre intentions temporelles obligatoires.

**115 modules concrets** ont été réécrits, et leurs scripts/manifestes sont
rescellés avec SHA-256. Les **95 autres** ne changent pas. Toutes les 210
signatures de pilotage passent le contrôle WordBench statique.

**Ce qui n'est pas établi :** aucune de ces modifications n'a encore été compilée
par le véritable GF 3.12 Windows dans cette livraison. Aucun statut `gold`
linguistique n'est approuvé, aucune RGL n'a été modifiée, et une génération
correcte ne prouve pas une compétence générale dans une langue. La précédente
campagne 210/210 demeure un **point de comparaison historique**, pas une preuve
pour les nouveaux modules.

## Références, provenance et limitations

Les réalisations lexicales sont vérifiées par lecture des fichiers
`gf-rgl/src/<langue>/LexiconXXX.gf` et les SHA-256 de `ParadigmsXXX.gf` et
`LexiconXXX.gf` sont consignés dans le rapport d'alignement. Cette provenance
est propre aux copies transmises au moment de la proposition, sans prétendre
connaître un commit Git exact.

Le Compendium conserve l'autorité sur la réparation de la **RGL** elle-même;
les changements actuels sont exclusivement des **grammaires de sondes
WordBench**. Observatory reste un lecteur de preuves et Defluens une couche
future d'orchestration. Aucun schéma préexistant n'est redéfini.

La protection dans `tools/generate_practical_pilots.py` empêche une régénération
sans avertissement qui effacerait nos sources alignées. Un éventuel reset
complet exige `--reset-alignment` et devrait être réservé à une migration
volontaire, après archivage des sources et des preuves.

## Utilisation Windows

Dézipper le correctif **à la racine de `GF_Wordbench`**, sans écraser les
fichiers `.git` ou les projets des autres langues.

```powershell
cd 'C:\mycode\Grammatical-Framework\GF_Wordbench'
.\Lancer_Alignement_14_Langues.bat check
.\Lancer_Alignement_14_Langues.bat smoke
.\Lancer_Alignement_14_Langues.bat full
.\Lancer_Alignement_14_Langues.bat compare
explorer "$env:USERPROFILE\Downloads\Ars_Magna_Defluens\practical_pilot_runs"
```

Le ZIP final `defluens-batch-full-*.zip` donnera les **phrases GF réellement
reproduites** avec les nouveaux modules. Réévaluer alors les sens et comparer
avec les **210 sorties historiques**. Les anciens rapports ne sont jamais écrasés.

Modes supplémentaires : `plan` (audit RGL et prévisualisation), `apply`
(idempotent, reconstruction contrôlée des modules). Les rapports de ces deux
modes vont dans `Downloads\Ars_Magna_Defluens\alignment14`.

Le mode `compare` choisit le ZIP complet le plus récent dont **les 210 SHA**
correspondent aux sources de la version installée. Un ancien ZIP est rejeté,
et le rapport `alignment14_comparison.json` détaille la nouvelle sortie face
à la revue IA historique non certifiée. Une phrase différente n’est pas
automatiquement une meilleure phrase.
