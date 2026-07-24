# ADR-0012 — Independent Products and Optional Interoperability

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Owner | GF Wordbench maintainers |
| Last reviewed | 2026-07-24 |

## Contexte

GF Wordbench peut coexister avec d’autres produits qui partagent certains concepts, formats ou besoins d’analyse.

Cette proximité fonctionnelle ne justifie pas :

- une base de données privée commune ;
- un service obligatoire partagé ;
- un package interne commun ;
- une dépendance d’exécution réciproque ;
- une synchronisation directe des états privés ;
- une fusion des responsabilités produit.

Chaque produit doit conserver son propre cycle de vie, son stockage, ses migrations, sa configuration, ses tests, sa distribution et ses responsabilités.

## Décision

> **GF Wordbench et les produits externes restent indépendants. Toute interopérabilité est optionnelle, versionnée, fondée sur des contrats publics et orientée consommateur.**

GF Wordbench doit pouvoir être installé, démarré, utilisé, testé et publié sans produit externe.

Lorsqu’un produit externe consomme des données de Wordbench :

- Wordbench publie un artefact ou contrat public versionné ;
- le consommateur choisit explicitement de l’utiliser ;
- l’adaptateur spécifique appartient de préférence au consommateur ;
- le consommateur ne lit ni ne modifie le stockage privé de Wordbench ;
- Wordbench ne dépend pas du runtime, de la configuration ou de l’état privé du consommateur.

Cette décision s’applique notamment à `gf-portfolio`.

`gf-portfolio` peut lire les artefacts publics finalisés de plusieurs workspaces GF Wordbench afin de produire des inventaires, comparaisons, tendances ou vues de portefeuille. GF Wordbench ne requiert pas `gf-portfolio` et ne lui délègue aucune responsabilité nécessaire à la validation d’un projet actif.

## Conséquences

### Conséquences positives

- les produits peuvent être installés, mis à jour et supprimés indépendamment ;
- les pannes ou migrations d’un produit ne bloquent pas les autres ;
- les frontières de propriété restent explicites ;
- les contrats publics peuvent évoluer par versionnement et compatibilité contrôlée ;
- chaque produit conserve ses propres exigences de sécurité, de rétention et de sauvegarde ;
- les consommateurs peuvent implémenter leurs adaptateurs sans imposer leur modèle interne à Wordbench.

### Contraintes

- aucun consommateur ne peut dépendre d’un détail privé non versionné ;
- une évolution incompatible d’un contrat public exige une nouvelle version, une migration ou une période de dépréciation documentée ;
- les artefacts publics doivent distinguer clairement leur identité, leur version, leur producteur et leur état de finalisation ;
- une intégration facultative ne doit jamais devenir une condition implicite de démarrage, de validation, de rapport ou de release ;
- les exemples d’intégration ne deviennent pas des dépendances normatives.

## Frontière de propriété

| Élément | Propriétaire |
|---|---|
| Validation d’un projet GF actif | GF Wordbench |
| Configuration privée de Wordbench | GF Wordbench |
| Schémas et stockage privés de Wordbench | GF Wordbench |
| Artefacts publics produits par Wordbench | GF Wordbench |
| Registre multi-workspaces | `gf-portfolio` |
| Agrégation, comparaison et tendances de portefeuille | `gf-portfolio` |
| Adaptateur consommant les artefacts Wordbench | Le consommateur, sauf contrat public générique explicitement possédé par Wordbench |
| État privé du consommateur | Le consommateur |

## Alternatives rejetées

### Base de données partagée

Une base commune couplerait les migrations, la disponibilité, la sécurité, les sauvegardes et les cycles de publication des produits.

### Service externe obligatoire

Un service requis au démarrage ou pendant la validation empêcherait le fonctionnement autonome de Wordbench.

### Package privé partagé

Un package interne partagé créerait un couplage de versions et permettrait aux produits de dépendre de modèles qui ne constituent pas des contrats publics stables.

### Lecture directe du stockage privé

La lecture des fichiers d’état, bases, caches ou répertoires internes d’un autre produit contournerait le versionnement et transférerait implicitement la propriété de ses détails d’implémentation.

### Adaptateurs imposés au fournisseur

Placer systématiquement dans Wordbench les intégrations propres à chaque consommateur ferait croître son périmètre avec chaque produit externe et inverserait la direction normale de dépendance.

## Critères de conformité

La décision est respectée lorsque :

- GF Wordbench fonctionne sans installation, service, base, package ou configuration appartenant à un produit externe ;
- les tests de Wordbench ne requièrent aucun runtime externe non nécessaire à ses propres responsabilités ;
- toute donnée destinée à un consommateur externe est publiée par un contrat public explicitement versionné ;
- les consommateurs n’accèdent pas au stockage privé de Wordbench ;
- Wordbench ne lit ni ne modifie l’état privé d’un consommateur ;
- les adaptateurs propres à un consommateur restent hors du cœur de Wordbench ;
- les changements incompatibles des contrats publics suivent une politique de versionnement, migration ou dépréciation ;
- `gf-portfolio` peut être ajouté ou supprimé sans modifier le fonctionnement autonome de GF Wordbench ;
- la documentation propriétaire de chaque produit respecte cette frontière.

## Références

- `docs/decisions/ADR-0001-SINGLE-ACTIVE-LANGUAGE.md`
- `docs/decisions/ADR-0011-SEPARATE-PORTFOLIO.md`
- `docs/architecture/PRODUCT_BOUNDARIES.md`
- `docs/INTERFILE_CONTRACT_LOCK.md`
- `docs/PERSISTED_SCHEMA_LOCK.md`
