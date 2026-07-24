# ADR-0010 — Run Budget and Finalization

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-24 |

## Contexte

Un run peut rencontrer un timeout, une annulation, une interruption de processus ou un échec tardif tout en devant produire un état terminal cohérent et vérifiable.

Des timeouts indépendants par étape ne suffisent pas. Une étape peut consommer tout le temps disponible, empêcher l’arrêt propre des processus enfants et ne laisser aucune marge pour publier les résultats déjà obtenus.

## Décision

> **Chaque run possède un budget global, des budgets d’étapes et une réserve de finalisation protégée.**

Le budget global borne la durée totale du run. Chaque étape reçoit un budget compatible avec le temps restant, sans pouvoir consommer la réserve de finalisation.

Lorsque le budget disponible hors réserve est épuisé, insuffisant ou annulé, le run cesse de démarrer de nouveaux travaux et passe en finalisation.

La finalisation doit :

- arrêter ou terminer proprement les processus enfants encore actifs ;
- conserver les résultats et preuves déjà produits ;
- attribuer un état terminal explicite au run et aux étapes incomplètes ;
- écrire les résultats disponibles de manière atomique ;
- produire les artefacts minimaux nécessaires au diagnostic ;
- empêcher toute publication de release `OK` lorsque les travaux requis sont incomplets.

La finalisation est idempotente : une nouvelle tentative ne doit ni corrompre les artefacts existants ni transformer un résultat incomplet en succès.

## Invariants

- La réserve de finalisation n’est pas disponible pour l’exécution normale des étapes.
- Un budget d’étape ne prolonge jamais le budget global.
- Aucune nouvelle étape n’est lancée lorsque son exécution compromettrait la réserve de finalisation.
- Un timeout, une annulation ou un échec tardif conduit à un état terminal explicite.
- Les résultats partiels ne sont jamais présentés comme un run complet.
- Une release ne peut être `OK` que si toutes les conditions obligatoires ont été exécutées et satisfaites.
- Les écritures terminales sont atomiques ou récupérables sans ambiguïté.

## Conséquences

L’orchestrateur doit suivre le temps restant du run et allouer les budgets d’étapes à partir de cette valeur.

Les adaptateurs de processus doivent permettre l’arrêt contrôlé des processus enfants et retourner les informations disponibles même lorsqu’une commande est interrompue.

Les modèles de résultats et les rapports doivent distinguer clairement :

- une étape réussie ;
- une étape échouée ;
- une étape expirée ;
- une étape annulée ;
- une étape non exécutée ;
- un run partiellement finalisé ou incomplet.

La réserve de finalisation améliore la fiabilité des artefacts terminaux, mais réduit volontairement le temps utilisable par les étapes normales.

## Alternatives rejetées

### Timeouts indépendants sans budget global

Cette approche permet à plusieurs étapes de consommer successivement une durée non bornée à l’échelle du run et ne garantit aucune marge de finalisation.

### Utiliser tout le budget pour l’exécution

Cette approche maximise le temps de travail apparent, mais peut empêcher l’arrêt des enfants, l’écriture atomique des résultats et la publication d’un état terminal vérifiable.

### Traiter la finalisation comme une étape ordinaire

Cette approche permet aux étapes précédentes de consommer le temps nécessaire à la finalisation et ne protège donc pas la production des artefacts terminaux.

## Critères de vérification

- les tests couvrent le budget global, les budgets d’étapes et la réserve de finalisation ;
- les tests couvrent les timeouts, annulations, échecs tardifs et arrêts de processus enfants ;
- les tests démontrent qu’aucun nouveau travail ne consomme la réserve de finalisation ;
- les tests démontrent que les résultats terminaux sont écrits atomiquement ou récupérables ;
- les tests démontrent qu’un run incomplet ne peut pas produire une release `OK` ;
- les documents propriétaires des modèles de résultats, de l’exécution des processus, des erreurs, des artefacts et des release gates respectent cette décision.
