# ADR-0009 — GF Anti-Corruption Boundary

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-24 |

## Contexte

Les commandes, options, diagnostics, formats de sortie et capacités de Grammatical Framework peuvent varier selon l’opération, la plateforme et la version de GF.

Sans frontière dédiée, la syntaxe GF, les règles de lancement de processus, l’interprétation des diagnostics et la validation des artefacts se disperseraient dans les stages de validation, le domaine, les interfaces et les rapports. Cette dispersion créerait plusieurs interprétations concurrentes du comportement de GF.

## Décision

> **Toutes les interactions avec GF passent par `GfToolPort` et une Anti-Corruption Layer dédiée.**

`GfToolPort` expose des requêtes et résultats structurés propres à GF Wordbench. L’Anti-Corruption Layer traduit ces contrats vers les commandes GF et reconvertit les sorties de GF en preuves et résultats structurés.

La frontière couvre notamment :

- la résolution de l’exécutable GF ;
- la construction des commandes et arguments ;
- les différences entre versions et plateformes ;
- la sélection du répertoire de travail et des chemins GF ;
- la transmission des scripts et entrées `.gfs` ;
- la capture de stdout, stderr, du code de sortie, des délais et des interruptions ;
- l’interprétation des diagnostics GF ;
- la vérification de fraîcheur et d’identité des artefacts `.gfo` et `.pgf` ;
- le rattachement des résultats aux preuves brutes de l’exécution courante.

Le domaine, les cas d’usage, les stages de validation, la CLI, la GUI et les rapports ne construisent pas directement de commandes GF et n’interprètent pas directement la syntaxe de sortie propre à GF.

## Conséquences

- Les détails de GF restent confinés dans les adaptateurs de l’Anti-Corruption Layer.
- Les modules applicatifs utilisent des contrats structurés et indépendants de la syntaxe de ligne de commande.
- Les différences de version sont traitées à un seul endroit.
- Les diagnostics bruts sont conservés avant toute normalisation ou classification.
- Les artefacts générés sont attribués à l’exécution courante avant d’être déclarés valides.
- Les tests peuvent remplacer `GfToolPort` par un double contrôlé sans exécuter GF.
- Toute nouvelle opération GF doit étendre le port et son adaptateur plutôt que contourner la frontière.

## Alternatives rejetées

### Construire les commandes GF dans chaque stage

Cette approche dupliquerait la résolution des chemins, les options, la gestion des versions et l’interprétation des erreurs.

### Exposer directement les processus GF au domaine

Cette approche introduirait des dépendances vers le système d’exploitation, les codes de sortie et les formats de sortie externes dans les modèles métier.

### Interpréter les diagnostics dans les interfaces ou les rapports

Cette approche produirait des classifications différentes selon le point d’entrée et permettrait aux couches de présentation de redéfinir le résultat d’une validation.

## Critères de vérification

- toute invocation GF passe par `GfToolPort` ;
- aucun stage, domaine, point d’entrée ou rapport ne construit directement une commande GF ;
- les requêtes et résultats du port sont structurés et testables ;
- stdout, stderr, code de sortie, durée et état de terminaison sont conservés ;
- les différences de version sont couvertes par les adaptateurs et leurs tests ;
- les diagnostics sont normalisés sans détruire les preuves brutes ;
- les artefacts `.gfo` et `.pgf` sont attribués à l’exécution courante ;
- les erreurs de lancement, délais, échecs GF et artefacts manquants restent distincts ;
- `docs/EXTERNAL_TOOL_CONTRACT_LOCK.md` et `docs/INTERFILE_CONTRACT_LOCK.md` restent cohérents avec cette décision.
