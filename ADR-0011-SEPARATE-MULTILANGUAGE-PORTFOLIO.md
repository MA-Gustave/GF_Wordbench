# ADR-0011 — Separate Multilanguage Portfolio from GF Wordbench

| Champ | Valeur |
|---|---|
| ADR ID | ADR-0011 |
| Status | Accepted |
| Decision date | 2026-07-23 |
| Implementation status | Not implemented |
| Verification status | Documentary decision; code verification pending |
| Owners | GF Wordbench maintainers |
| Supersedes | Proposed ADR-0011 Language Inventory and Everything Matrix |
| Related decisions | ADR-0001, ADR-0008, ADR-0012 |

## 1. Contexte

ADR-0001 établit qu’un workspace GF Wordbench contient exactement un projet GF actif et qu’un run résout exactement une identité de projet.

La version 3 du rapport d’alignement proposait d’ajouter dans Wordbench :

- la découverte de plusieurs cibles ;
- un inventaire de langues ;
- une Everything Matrix ;
- une maturité et un readiness de portefeuille ;
- des commandes `languages` ;
- des artefacts d’agrégation multi-cibles.

Ces capacités introduiraient une seconde identité dans le cœur de Wordbench et contrediraient son modèle mono-projet.

## 2. Décision

> **Toutes les responsabilités de portefeuille multilingue sont exclues de GF Wordbench et confiées à un module ou produit compagnon indépendant.**

Nom de travail du produit compagnon :

```text
gf-portfolio
```

GF Wordbench reste responsable d’un seul projet actif par workspace.

`gf-portfolio` peut agréger plusieurs workspaces, mais uniquement en consommant leurs contrats publics et leurs artefacts versionnés.

## 3. Conséquences pour GF Wordbench

GF Wordbench ne contient pas :

- de registre multi-workspace ;
- de module fonctionnel `languages` pour le portefeuille ;
- de commande `languages scan`, `languages matrix` ou `languages show` ;
- de schéma `gf-wordbench.language-inventory` ;
- de schéma `gf-wordbench.everything-matrix` de portefeuille ;
- de schéma `gf-wordbench.language-status` de portefeuille ;
- de score comparatif entre projets ;
- de sélection dynamique de plusieurs projets actifs ;
- de tableau de bord transversal.

Wordbench peut exposer les résultats publics d’un projet actif :

```text
summary.json
manifest.json
project identity
run identity
validation mode
overall status
GF version
artifact references
timestamps
schema versions
```

## 4. Conséquences pour gf-portfolio

`gf-portfolio` possède :

- le registre de workspaces ;
- l’inventaire multi-projets ;
- l’Everything Matrix ;
- les scores et tiers transversaux ;
- la comparaison et les tendances ;
- la fraîcheur des observations ;
- les schémas persistés du portefeuille ;
- les vues et rapports agrégés.

Ses schémas utilisent son propre espace de noms :

```text
gf-portfolio.workspace-registry/1.0
gf-portfolio.inventory/1.0
gf-portfolio.everything-matrix/1.0
gf-portfolio.language-status/1.0
```

## 5. Direction des dépendances

Autorisé :

```text
gf-portfolio → artefacts publics GF Wordbench
```

Interdit :

```text
GF Wordbench → gf-portfolio
gf-portfolio → modules internal de GF Wordbench
partage d’une base interne
partage de l’état UI privé
partage de classes d’implémentation
```

L’intégration par paquet Python public reste différée. Le contrat initial repose sur des artefacts de fichier versionnés, plus stables et plus faciles à vérifier.

## 6. Règles d’agrégation

Un résultat agrégé :

- ne masque jamais l’échec d’un workspace individuel ;
- conserve le lien vers la preuve source ;
- distingue `missing`, `stale`, `invalid` et `not_applicable` ;
- ne transforme pas l’absence de preuve en score nul ou en succès ;
- identifie la version du calcul et des scanners ;
- reste reproductible à entrées et versions identiques.

## 7. Migration documentaire

À retirer du plan Wordbench :

```text
docs/languages/LANGUAGE_INVENTORY.md
docs/languages/EVERYTHING_MATRIX.md
docs/languages/MATURITY_AND_READINESS.md
docs/schemas/LANGUAGE_INTELLIGENCE_SCHEMAS.md
```

À créer dans `gf-portfolio` si requis :

```text
docs/architecture/PORTFOLIO_ARCHITECTURE.md
docs/inventory/WORKSPACE_DISCOVERY.md
docs/matrix/EVERYTHING_MATRIX.md
docs/scoring/MATURITY_AND_READINESS.md
docs/schemas/PORTFOLIO_SCHEMAS.md
```

## 8. Contrôles

Les tests Wordbench doivent vérifier :

- aucune dépendance vers `gf-portfolio` ;
- aucun schéma `gf-portfolio.*` dans le paquet Wordbench ;
- aucune commande publique `languages` de portefeuille ;
- démarrage et tests avec `gf-portfolio` absent.

Les tests `gf-portfolio` doivent vérifier :

- lecture de plusieurs versions supportées de `summary.json` et `manifest.json` ;
- rejet explicite des versions incompatibles ;
- traçabilité de chaque agrégat ;
- absence de mutation des workspaces par défaut ;
- déterminisme des matrices ;
- absence de masquage des échecs individuels.

## 9. Alternatives rejetées

### Maintenir le multilingue dans Wordbench

Rejeté : introduit une seconde identité, élargit le produit et contredit ADR-0001.

### Partager directement les modules Python internes

Rejeté : crée un couplage de version et contourne les contrats publics.

### Utiliser une base de données commune

Rejeté : partage la propriété des données et rend les produits impossibles à déployer indépendamment.

### Faire de SemantiK Architect le portefeuille obligatoire

Rejeté : Wordbench doit rester autonome et SemantiK conserve son propre domaine applicatif.

## 10. Critères d’acceptation

Cette décision est considérée implémentée lorsque :

- toute référence au portefeuille multilingue est retirée des contrats Wordbench ;
- ADR-0001 reste inchangé ou est seulement clarifié ;
- les exports publics nécessaires sont versionnés ;
- `gf-portfolio` possède ses propres schémas ;
- les tests de non-dépendance passent ;
- l’installation ou la suppression de `gf-portfolio` ne modifie aucun comportement Wordbench.
