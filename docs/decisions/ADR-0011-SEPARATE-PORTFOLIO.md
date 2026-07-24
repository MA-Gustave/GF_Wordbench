# ADR-0011 — Separate Portfolio Product

| Champ | Valeur |
|---|---|
| Document role | Architectural decision record |
| Decision status | Accepted |
| Owner | GF Wordbench maintainers |
| Alignment authority | `docs/DOCUMENTATION_ALIGNMENT_LOCK.md` |
| Last reviewed | 2026-07-24 |

## Contexte

GF Wordbench valide un seul projet GF actif dans un workspace donné.

La gestion de plusieurs workspaces introduit des responsabilités différentes :

- découverte et enregistrement de plusieurs workspaces ;
- navigation entre plusieurs projets GF ;
- agrégation de résultats ;
- comparaison entre projets ou langues ;
- suivi transversal de préparation et de qualité ;
- conservation d’un état propre au portefeuille.

Ces responsabilités ne relèvent ni de la validation d’un projet actif ni du cycle de vie d’une exécution Wordbench.

## Décision

> **La gestion de plusieurs workspaces et les vues agrégées appartiennent à un produit compagnon indépendant nommé `gf-portfolio`.**

GF Wordbench reste mono-projet :

- un workspace Wordbench contient exactement un projet GF actif ;
- une exécution résout exactement un projet actif et une cible normative ;
- Wordbench ne contient aucun registre de plusieurs workspaces ;
- Wordbench ne fournit aucune vue agrégée multi-projets ou multilingue.

Le produit `gf-portfolio` peut consommer les artefacts publics et versionnés produits par GF Wordbench.

La direction de dépendance autorisée est :

```text
gf-portfolio -> artefacts publics versionnés de GF Wordbench
```

La dépendance inverse est interdite :

```text
GF Wordbench -X-> runtime, code, stockage ou configuration de gf-portfolio
```

GF Wordbench doit pouvoir démarrer, valider, produire ses rapports et exécuter ses tests sans installation ni disponibilité de `gf-portfolio`.

## Conséquences

### Pour GF Wordbench

- l’identité du workspace reste simple et non ambiguë ;
- `project/project.toml` décrit un seul projet actif ;
- les schémas Wordbench ne contiennent aucun registre Portfolio ;
- les interfaces CLI et GUI ne proposent aucun sélecteur multi-projets ;
- les rapports décrivent une seule exécution et un seul projet actif ;
- les modules Wordbench ne dépendent d’aucun composant privé de `gf-portfolio`.

### Pour `gf-portfolio`

- le produit possède son propre stockage, ses propres schémas et son propre cycle de vie ;
- il découvre ou enregistre plusieurs workspaces Wordbench ;
- il lit les artefacts publics Wordbench sans les modifier ;
- il gère lui-même l’agrégation, la comparaison et les vues transversales ;
- il reste un consommateur optionnel des sorties Wordbench.

### Pour les artefacts publics

Les artefacts destinés à être consommés par `gf-portfolio` doivent être :

- versionnés ;
- stables ;
- documentés ;
- associés à un projet et à une exécution ;
- lisibles sans accès aux modules internes de Wordbench ;
- consommés en lecture seule.

## Alternatives rejetées

### Intégrer le portefeuille au cœur de Wordbench

Cette option est rejetée parce qu’elle :

- contredit l’identité mono-projet du workspace ;
- introduit un second cycle de vie dans le produit ;
- élargit inutilement les schémas et l’état applicatif ;
- mélange validation locale et orchestration transversale ;
- augmente le couplage entre projets indépendants.

### Ajouter un sélecteur de projet dans Wordbench

Cette option est rejetée parce qu’elle transforme implicitement Wordbench en gestionnaire de plusieurs projets et rend l’identité active dépendante de l’interface ou de l’état local.

### Partager une base de données entre Wordbench et Portfolio

Cette option est rejetée parce qu’elle crée une dépendance d’exécution, mélange les propriétaires de schémas et empêche l’autonomie complète de Wordbench.

## Critères de vérification

- un workspace Wordbench ne contient qu’un seul projet actif ;
- une exécution Wordbench ne référence qu’un seul projet et une seule cible normative ;
- aucun schéma Wordbench ne contient de registre de workspaces ou d’état d’agrégation ;
- aucun module Wordbench n’importe ou n’appelle `gf-portfolio` ;
- Wordbench fonctionne sans installation ni disponibilité de `gf-portfolio` ;
- `gf-portfolio` consomme uniquement des artefacts publics versionnés ;
- les artefacts consommés restent propriété de Wordbench et sont lus sans mutation ;
- la documentation propriétaire ne contredit pas cette décision.

## Documents affectés

Cette décision gouverne notamment :

```text
docs/PRODUCT_OVERVIEW.md
docs/SCOPE_AND_NON_GOALS.md
docs/architecture/PRODUCT_BOUNDARIES.md
docs/architecture/ARCHITECTURE_OVERVIEW.md
docs/architecture/DEPENDENCY_RULES.md
docs/projects/PROJECT_MODEL.md
docs/configuration/PROJECT_TOML_REFERENCE.md
docs/configuration/APPLICATION_STATE_REFERENCE.md
docs/PERSISTED_SCHEMA_LOCK.md
docs/INTERFILE_CONTRACT_LOCK.md
docs/DOCUMENTATION_ALIGNMENT_LOCK.md
```
