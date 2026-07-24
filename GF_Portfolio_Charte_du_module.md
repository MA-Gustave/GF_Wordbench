# GF Portfolio — Charte du module compagnon

**Nom de travail :** `gf-portfolio`

| Champ | Valeur |
|---|---|
| Document role | Product and module charter |
| Decision status | Recommended companion boundary accepted in principle |
| Implementation status | Not implemented |
| Verification status | Requires prototype and contract tests |
| Primary dependency | Public, versioned GF Wordbench artifacts |

## 1. Mission

> **GF Portfolio fournit une vue multi-workspace des projets GF validés par GF Wordbench, sans participer au cœur de leur validation.**

Le module agrège les faits publiés par plusieurs workspaces Wordbench. Il ne remplace ni GF, ni Wordbench, ni les critères de release propres à chaque projet.

## 2. Utilisateurs et usages

Usages principaux :

- inventorier plusieurs projets GF ;
- repérer les workspaces non exécutés ou périmés ;
- comparer couverture, diagnostics et artefacts ;
- suivre les tendances de santé ;
- construire une Everything Matrix ;
- identifier les blocages communs ;
- préparer une vue de programme ou de portefeuille.

## 3. Limites du MVP

Le MVP est strictement en lecture seule.

Il lit :

```text
workspace registration
summary.json
manifest.json
public project identity
optional public diagnostic exports
```

Il n’exécute pas :

```text
validation Wordbench
GF commands
gold updates
source modification
release promotion
arbitrary shell commands
```

## 4. Architecture recommandée

```text
CLI / Web UI
      │
      ▼
Portfolio application services
      │
      ├── WorkspaceRegistry
      ├── ArtifactCollector
      ├── CompatibilityEvaluator
      ├── InventoryBuilder
      ├── MatrixAssembler
      ├── MaturityEvaluator
      └── PortfolioReporter
      │
      ▼
Ports
      ├── WordbenchArtifactReader
      ├── PortfolioStore
      ├── Clock
      └── OptionalWorkspaceLocator
      │
      ▼
Adapters
      ├── LocalFilesystemArtifactReader
      ├── JsonPortfolioStore
      └── OptionalGitWorkspaceLocator
```

## 5. Modèle d’identité

```text
portfolio_id
workspace_id
project_id
run_id
```

Règles :

- `workspace_id` identifie l’emplacement enregistré ;
- `project_id` provient du contrat Wordbench ;
- `run_id` identifie la preuve observée ;
- une collision de `project_id` entre workspaces produit un diagnostic ;
- un workspace déplacé conserve son identité uniquement par opération explicite ;
- aucune identité n’est inférée à partir d’un nom de dossier seul.

## 6. Schémas initiaux

### 6.1 Workspace registry

```text
gf-portfolio.workspace-registry/1.0
```

Champs minimaux :

```text
workspace_id
location
label
enabled
registered_at
last_seen_at
```

### 6.2 Inventory

```text
gf-portfolio.inventory/1.0
```

Champs minimaux :

```text
portfolio_id
generated_at
collector_version
workspaces[]
project_id
latest_run_id
latest_status
freshness_status
compatibility_status
evidence_refs[]
```

### 6.3 Everything Matrix

```text
gf-portfolio.everything-matrix/1.0
```

Chaque métrique contient :

```text
metric_id
score
evidence_status
confidence
evidence_refs
observed_at
scanner_version
profile_id
```

### 6.4 Portfolio status

```text
gf-portfolio.language-status/1.0
```

Le nom de schéma peut évoluer vers `project-status` si le portefeuille agrège des projets plutôt que des langues au sens strict.

## 7. Maturité et readiness

La maturité et le readiness du portefeuille ne sont pas des statuts Wordbench.

Ils doivent :

- être calculés par un profil versionné ;
- conserver les preuves sources ;
- distinguer faits observés et estimations ;
- ne jamais remplacer le statut de release produit par Wordbench ;
- afficher chaque projet individuel à côté de l’agrégat.

Le libellé `Correcte par construction` est interdit.

Libellé recommandé pour un niveau linguistique avancé :

> **Conformité linguistique déclarée — toutes les familles de validations requises par le projet ont passé.**

## 8. Compatibilité avec Wordbench

`gf-portfolio` possède une matrice de lecteurs :

| Contrat Wordbench | Politique |
|---|---|
| Version courante | Support complet testé |
| Version précédente compatible | Lecture avec adaptateur explicite |
| Version future inconnue | Rejet ou mode partiel visible |
| Schéma invalide | Diagnostic, aucune agrégation normative |
| Manifest absent | Preuve incomplète, jamais succès implicite |

## 9. Sécurité et mutabilité

Par défaut :

```text
read_only = true
follow_symlinks = false
allow_external_commands = false
allow_source_mutation = false
```

Toute future orchestration de Wordbench doit être un sous-système séparé, allowlisté, désactivé par défaut et limité à l’interface publique `gf-wordbench`.

## 10. Roadmap

### Phase A — Lecture locale

- registre manuel de workspaces ;
- lecteurs `summary.json` et `manifest.json` ;
- inventaire ;
- diagnostics de compatibilité et de fraîcheur ;
- rapport JSON et Markdown.

### Phase B — Everything Matrix

- profil de métriques ;
- preuves ;
- cache par fingerprint ;
- score et tiers versionnés ;
- tendances historiques.

### Phase C — Interface

- CLI de navigation ;
- dashboard web ou desktop ;
- filtres et comparaisons ;
- drill-down vers les artefacts Wordbench.

### Phase D — Automatisation optionnelle

- découverte de workspaces ;
- déclenchement explicite de commandes Wordbench publiques ;
- budgets, concurrence et contrôle d’accès ;
- aucune exécution arbitraire.

## 11. Critères de réussite

Le module est prêt pour un MVP lorsque :

- trois workspaces indépendants peuvent être enregistrés ;
- leurs derniers runs sont lus sans import Python Wordbench ;
- les incompatibilités de schéma sont visibles ;
- un échec individuel reste visible dans toute vue agrégée ;
- aucune source ni gold n’est modifié ;
- les mêmes artefacts produisent la même matrice ;
- la suppression du module ne change aucun workspace Wordbench.
