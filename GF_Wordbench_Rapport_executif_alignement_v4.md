# GF Wordbench — Rapport exécutif d’alignement

**Version 4 — recentrage mono-projet, séparation du portefeuille multilingue et plan de résolution des écarts**

| Champ | Valeur |
|---|---|
| Document role | Rapport exécutif d’alignement et plan directeur opérationnel |
| Decision status | Accepté — séparation du multilingue confirmée |
| Implementation status | Principalement non implémenté dans l’archive examinée |
| Verification status | Alignement documentaire ; validation par code et tests requise |
| Intended authority | Document directeur jusqu’au transfert des décisions dans leurs ADR et contrats propriétaires |
| Supersedes | Version 3 du rapport exécutif d’alignement |

## 1. Décision exécutive

GF Wordbench doit évoluer vers un :

> **Monolithe modulaire autonome, local-first, structuré selon une architecture hexagonale, dédié à un seul projet GF actif par workspace et à une seule cible normative par run.**

Le multilingue de portefeuille est entièrement retiré du périmètre de GF Wordbench.

GF Wordbench ne doit pas :

- découvrir ou maintenir un registre de plusieurs projets linguistiques actifs ;
- agréger plusieurs workspaces dans un tableau de bord de portefeuille ;
- calculer un classement comparatif entre plusieurs langues ;
- posséder un module fonctionnel `languages` consacré à l’inventaire multilingue ;
- exposer des commandes `languages scan`, `languages matrix` ou `languages show` ;
- stocker des artefacts de portefeuille tels que `language-inventory.json` ;
- sélectionner dynamiquement une langue parmi plusieurs projets actifs dans un même workspace.

Ces responsabilités appartiennent à un produit ou module compagnon séparé, désigné dans ce document par le nom de travail :

```text
gf-portfolio
```

## 2. Périmètre de GF Wordbench

GF Wordbench reste l’autorité pour un projet GF actif :

- chargement et validation de `project/project.toml` ;
- sélection des sources du projet actif ;
- scan statique borné ;
- compilation GF ;
- construction PGF ;
- exécution des scénarios `.gfs` ;
- comparaison des sorties normalisées et des golds ;
- classification directe, downstream, ambiguë ou noise ;
- budgets de run, timeouts, annulation et finalisation ;
- conservation des preuves brutes ;
- génération de `summary.json`, `summary.md`, `AI_READY.md` et `manifest.json` ;
- application des release gates du projet actif ;
- diagnostics déterministes liés au projet actif ;
- historique local et comparaison des runs du même projet.

La règle d’identité reste :

> **Un workspace GF Wordbench contient exactement un projet GF actif. Chaque run normatif résout exactement une identité de projet actif.**

Une grammaire GF multilingue peut naturellement contenir plusieurs concrétisations lorsque cela appartient au projet actif. Cette capacité GF interne ne transforme pas Wordbench en gestionnaire de plusieurs projets linguistiques.

## 3. Frontières entre produits

| Produit | Autorité | Règle de dépendance |
|---|---|---|
| **GF Wordbench** | Validation, diagnostics, preuves et release d’un projet GF actif. | Autonome. Aucune dépendance envers `gf-portfolio`, SemantiK Architect ou Kristal. |
| **gf-portfolio** | Inventaire de plusieurs workspaces, agrégation, comparaison, maturité de portefeuille et vues transversales. | Consomme uniquement les contrats publics et artefacts exportés de Wordbench. |
| **SemantiK Architect** | Source optionnelle de concepts et d’algorithmes réutilisables. | Aucun import, service ou artefact privé requis par Wordbench. |
| **Kristal** | Référentiel fixe de l’écosystème. | Hors périmètre de changement et hors dépendance du cœur Wordbench. |

Direction autorisée :

```text
gf-portfolio → contrats publics / artefacts de GF Wordbench
GF Wordbench  -X→ gf-portfolio
GF Wordbench  -X→ SemantiK Architect
GF Wordbench  -X→ Kristal
```

`gf-portfolio` ne doit pas importer les modules `internal` de Wordbench, partager sa base de données, lire son état UI privé ni réutiliser directement ses classes d’implémentation.

## 4. Architecture cible de GF Wordbench

### 4.1 Deux dimensions complémentaires

Les taxonomies concurrentes de six, huit et dix couches doivent être remplacées par deux dimensions stables :

1. **modules fonctionnels** ;
2. **anneaux de dépendance hexagonaux**.

Les anciens modèles restent historiques jusqu’à leur migration, mais ne doivent plus être présentés comme trois architectures finales simultanées.

### 4.2 Modules fonctionnels

```text
projects       configuration, identité et chargement du projet actif
runs           orchestration, budgets, continuation, finalisation et historique
validation     sélection, scan, compilation, scénarios, golds et release gates
diagnostics    normalisation, findings, classification et audits
reporting      schémas, rendus, manifestes et exports
```

Le module `languages` proposé dans la version 3 est supprimé de Wordbench.

Les métriques propres à un run ou à un projet unique restent chez leur propriétaire naturel :

- santé du run : `runs` ;
- résultats de validation : `validation` ;
- findings : `diagnostics` ;
- synthèses et exports : `reporting` ;
- identité et configuration du projet : `projects`.

### 4.3 Anneaux de dépendance

```text
domain → application → ports → adapters → entrypoints → bootstrap
```

- **domain** : statuts, résultats, règles de continuation, invariants et release gates ;
- **application** : cas d’utilisation et coordination ;
- **ports** : frontières externes ou instables ;
- **adapters** : GF natif, processus, filesystem, TOML, JSON, persistance et horloge ;
- **entrypoints** : CLI, GUI et CI ;
- **bootstrap** : composition root et câblage des implémentations.

### 4.4 Flux de référence

```text
CLI · GUI · CI
      │
      ▼
Cas d’utilisation
ValidateProject · CheckProject · UpdateGold · RunDiagnosticAudit
      │
      ▼
Domaine
statuts · résultats · continuation · release gates · findings
      │
      ▼
Ports
GF Tool · Process Executor · Artifact Store · Run History · Clock
      ▲
      │
Adaptateurs
GF natif · processus local · filesystem · TOML · JSON · persistance
```

### 4.5 Structure de paquet recommandée

```text
gf_wordbench/
├── projects/
│   ├── api.py
│   ├── models.py
│   └── internal/
├── runs/
│   ├── api.py
│   ├── models.py
│   ├── coordinator.py
│   ├── planner.py
│   ├── continuation.py
│   ├── failure_classifier.py
│   ├── release_gates.py
│   └── finalizer.py
├── validation/
│   ├── api.py
│   ├── models.py
│   ├── scanning.py
│   ├── compilation.py
│   ├── scenarios.py
│   └── golds.py
├── diagnostics/
│   ├── api.py
│   ├── models.py
│   ├── audit.py
│   ├── ambiguity.py
│   └── profiling.py
├── reporting/
│   ├── api.py
│   ├── schema_models.py
│   ├── rendering.py
│   └── manifests.py
├── ports/
│   ├── gf_tool.py
│   ├── process_executor.py
│   ├── artifact_store.py
│   ├── run_history.py
│   └── clock.py
├── adapters/
│   ├── gf_native/
│   ├── process/
│   │   ├── local_process_executor.py
│   │   └── models.py
│   ├── filesystem/
│   └── persistence/
├── entrypoints/
│   ├── cli.py
│   └── gui.py
└── bootstrap.py
```

## 5. Cas d’utilisation et ports minimaux

Cas d’utilisation publics initiaux :

```text
ValidateProjectUseCase
CheckProjectUseCase
UpdateGoldUseCase
RunDiagnosticAuditUseCase
```

Ports justifiés :

```text
GfToolPort
ProcessExecutorPort
ArtifactStorePort
RunHistoryPort
ClockPort
```

Un `ProjectRepositoryPort` n’est nécessaire que si le chargement de projet possède plusieurs implémentations réelles ou devient une frontière externe. Tant que `project/project.toml` et le filesystem local constituent l’unique mécanisme, le chargeur peut rester un composant applicatif interne testé.

Aucune interface ne doit être créée pour un helper pur ou une seule fonction locale.

## 6. Recommandations de résolution des écarts

### P0 — Taxonomies architecturales concurrentes

**Constat :** les documents décrivent au moins trois modèles de couches : dix, huit et L0–L5.

**Recommandation :**

- accepter ADR-0008 comme autorité unique ;
- conserver les modules fonctionnels et les anneaux hexagonaux ;
- transformer les anciennes couches en vues de migration non normatives ;
- ne pas renommer tout le code en une seule opération ;
- ajouter un test d’imports et une carte de migration fichier par fichier.

**Critère de sortie :** un nouveau composant peut être classé sans ambiguïté par module fonctionnel et par anneau.

### P0 — Statuts documentaires inexacts

**Recommandation :** ajouter à tout document normatif :

```text
Decision status
Implementation status
Verification status
Document role
Owner
Last verified against
```

Le mot `Final` ne doit qualifier que la décision ou le contrat, jamais l’implémentation non vérifiée.

**Critère de sortie :** aucun document ne laisse entendre qu’une capacité existe uniquement parce qu’elle est spécifiée.

### P0 — Autorités CLI contradictoires

**Recommandation :**

- `docs/usage/CLI_REFERENCE.md` devient l’unique autorité publique ;
- `docs/reference/COMMAND_REFERENCE.md` est reclassé en `COMMAND_CANDIDATES.md` non normatif ou supprimé ;
- seuls les verbes implémentés, testés et inclus dans le parser peuvent être `Canonical` ;
- les opérations internes `scan`, `compile`, `report` et `manifest` restent des stages ou sous-fonctions, sauf besoin utilisateur démontré.

**Critère de sortie :** test automatique entre documentation CLI, parser, aide `--help` et tests d’intégration.

### P0 — Frontières produits

**Recommandation :** accepter l’ADR de séparation du multilingue et ajouter :

- tests d’absence d’import vers `gf-portfolio`, SemantiK et Kristal ;
- test de démarrage de Wordbench avec ces produits absents ;
- interdiction de chemins privés ou de schémas partagés non versionnés ;
- exports publics appartenant à Wordbench.

**Critère de sortie :** suppression complète du module compagnon sans changement du comportement ou des tests Wordbench.

### P0 — Process runner

**Recommandation :** ne pas seulement déplacer le fichier. Séparer :

```text
ports/process_executor.py                 contrat abstrait de lancement
adapters/process/local_process_executor.py implémentation locale
adapters/process/models.py                modèles techniques de processus
```

L’ACL GF utilise le `ProcessExecutorPort`, mais la politique GF reste dans l’adaptateur GF.

**Critère de sortie :** aucun `subprocess`, `os.system` ou équivalent hors de l’adaptateur de processus.

### P1 — GF insuffisamment isolé

**Recommandation :** créer un `GfToolPort` unique et une ACL GF propriétaire de :

- détection de version ;
- construction des commandes ;
- capacités variant par version ;
- traduction des sorties et diagnostics ;
- vérification des `.gfo` et `.pgf` ;
- liens vers les preuves brutes ;
- normalisation versionnée.

**Critère de sortie :** le domaine ne contient ni syntaxe de commande GF, ni texte de diagnostic GF brut, ni logique de version du binaire.

### P1 — Modèle partagé trop centralisé

**Recommandation :** migrer progressivement `app/models.py` vers les propriétaires fonctionnels. Conserver un noyau partagé minimal seulement pour :

```text
identifiants stables
statuts transversaux strictement communs
EvidenceRef
horodatages et versions de schéma
```

Les modèles de processus restent dans l’adaptateur de processus.

**Critère de sortie :** chaque modèle possède un propriétaire, un cycle de vie et un contrat de sérialisation explicites.

### P1 — Risque de God Orchestrator

**Recommandation :** conserver un `RunCoordinator` mince et extraire les politiques :

```text
PipelinePlanner
ContinuationPolicy
FailureClassifier
ReleaseGateEvaluator
RunFinalizer
```

Ne pas transformer chaque politique en service distribué ou en plugin.

**Critère de sortie :** le coordinateur décrit la séquence, tandis que les règles sont testables indépendamment.

### P1 — Catalogue diagnostique non opérationnel

**Recommandation :** introduire un registre statique et allowlisté après stabilisation du premier flux vertical.

Chaque outil doit déclarer :

```text
tool_id
version
description
input_contract
allowed_flags
mutability
allowed_paths
timeout
output_limit
evidence_roles
ai_assisted
normative
```

Les outils IA restent non normatifs et ne peuvent jamais satisfaire une release gate.

**Critère de sortie :** aucun outil arbitraire ni flag non déclaré ne peut être exécuté.

### P1 — Preuves et fraîcheur

**Recommandation :** introduire un modèle commun `EvidenceRef` avec :

```text
evidence_id
artifact_path
artifact_role
producer
producer_version
observed_at
content_hash
freshness_status
```

La fraîcheur doit être évaluée par rapport au fingerprint du projet, à la version de GF, à la version du scanner et au contrat de normalisation.

**Critère de sortie :** tout diagnostic ou résultat normatif est traçable jusqu’à une preuve présente dans le manifeste.

### P2 — Interopérabilité SemantiK

**Recommandation :** différer toute interopérabilité jusqu’à stabilisation des schémas Wordbench. Préférer un adaptateur côté consommateur.

**Critère de sortie :** Wordbench ne connaît aucun format privé SemantiK ; les exports optionnels sont publics, versionnés et testés.

## 7. Nouveau module compagnon : gf-portfolio

### 7.1 Responsabilités

`gf-portfolio` peut :

- enregistrer plusieurs workspaces Wordbench ;
- découvrir leurs artefacts publics ;
- afficher leur dernière exécution connue ;
- vérifier la fraîcheur des preuves ;
- construire une Everything Matrix de portefeuille ;
- calculer des scores ou tiers transversaux versionnés ;
- comparer tendances, couverture, blocages et readiness ;
- signaler les workspaces absents, ambigus ou périmés ;
- produire des vues agrégées sans masquer un échec individuel.

### 7.2 Non-responsabilités initiales

Le MVP ne doit pas :

- importer le code interne de Wordbench ;
- modifier les projets GF ;
- mettre à jour les golds ;
- décider une release à la place de Wordbench ;
- partager la base de données ou l’état UI de Wordbench ;
- lancer des commandes arbitraires ;
- imposer SemantiK ou Kristal.

### 7.3 Contrats consommés

Contrats minimaux à stabiliser côté Wordbench :

```text
summary.json
manifest.json
resolved-project.json ou bloc équivalent dans summary.json
run metadata
schema_id
schema_version
project_id
run_id
mode
overall_status
started_at
finished_at
gf_version
artifact references
```

`gf-portfolio` possède ses propres schémas :

```text
gf-portfolio.workspace-registry/1.0
gf-portfolio.inventory/1.0
gf-portfolio.everything-matrix/1.0
gf-portfolio.language-status/1.0
```

Les schémas de portefeuille ne doivent pas être ajoutés au cœur de Wordbench.

## 8. ADRs à créer ou mettre à jour

### ADR-0008 — Hexagonal Modular Monolith

Maintenir, avec cinq modules fonctionnels Wordbench et sans module `languages`.

### ADR-0009 — GF Anti-Corruption Boundary

Maintenir.

### ADR-0010 — Run Budget and Finalization

Maintenir.

### ADR-0011 — Separate Multilanguage Portfolio

Remplace l’ancien ADR proposé « Language Inventory and Everything Matrix » dans Wordbench.

Il décide :

- Wordbench reste mono-projet actif ;
- le portefeuille multilingue est un produit séparé ;
- la direction des dépendances est unidirectionnelle ;
- les contrats consommés sont publics et versionnés ;
- les schémas de portefeuille appartiennent au produit compagnon ;
- l’agrégation ne peut pas masquer les résultats individuels.

### ADR-0012 — Independent Products and Optional Interoperability

Maintenir, en ajoutant `gf-portfolio` aux produits optionnels non requis.

### ADR-0013 — Diagnostic Tool Registry and Safe Execution

Maintenir.

## 9. Mise à jour documentaire

### 9.1 Documents Wordbench à créer

```text
docs/architecture/DATA_MODEL.md
docs/architecture/IMPLEMENTATION_ALIGNMENT.md
docs/architecture/PRODUCT_BOUNDARIES.md
docs/diagnostics/TOOL_CATALOG.md
docs/diagnostics/DIAGNOSTIC_AUDIT.md
docs/operations/TOOLS_REGISTRY.md
docs/decisions/ADR-0008-HEXAGONAL-MODULAR-MONOLITH.md
docs/decisions/ADR-0009-GF-ANTI-CORRUPTION-BOUNDARY.md
docs/decisions/ADR-0010-RUN-BUDGET-AND-FINALIZATION.md
docs/decisions/ADR-0011-SEPARATE-MULTILANGUAGE-PORTFOLIO.md
docs/decisions/ADR-0012-INDEPENDENT-PRODUCTS-AND-OPTIONAL-INTEROPERABILITY.md
docs/decisions/ADR-0013-DIAGNOSTIC-TOOL-REGISTRY-AND-SAFE-EXECUTION.md
```

### 9.2 Documents retirés du plan Wordbench

```text
docs/languages/LANGUAGE_INVENTORY.md
docs/languages/EVERYTHING_MATRIX.md
docs/languages/MATURITY_AND_READINESS.md
docs/schemas/LANGUAGE_INTELLIGENCE_SCHEMAS.md
```

Ces documents, s’ils sont utiles, doivent être créés dans `gf-portfolio` avec des identifiants de schéma propres au nouveau produit.

### 9.3 Documents à réviser

| Document | Action |
|---|---|
| `ARCHITECTURE_OVERVIEW.md` | Remplacer les anciennes taxonomies par modules et anneaux ; confirmer un projet actif. |
| `COMPONENT_MAP.md` | Décrire les cinq modules, les ports et adaptateurs ; retirer l’inventaire multilingue. |
| `DEPENDENCY_RULES.md` | Définir la matrice unique et les tests de non-couplage. |
| `PROCESS_EXECUTION_MODEL.md` | Séparer port et adaptateur local sans changement silencieux de contrat. |
| `DATA_MODEL.md` | Répartir les modèles par propriétaire et ajouter `EvidenceRef`. |
| `ARTIFACT_MODEL.md` | Garder uniquement les artefacts d’un run ou projet Wordbench. |
| `REPORTING_OVERVIEW.md` | Exposer les données publiques nécessaires au consommateur externe sans vue portefeuille. |
| `CLI_REFERENCE.md` | Autorité unique ; aucune commande `languages`. |
| `COMMAND_REFERENCE.md` | Reclasser ou supprimer. |
| `PRODUCT_OVERVIEW.md` | Réaffirmer le workbench mono-projet. |
| `SCOPE_AND_NON_GOALS.md` | Ajouter explicitement le portefeuille multilingue aux non-objectifs. |
| `ADR-0001` | Maintenir ; ajouter un lien vers ADR-0011. |

## 10. Plan d’exécution recommandé

### Phase 0 — Décisions et nettoyage documentaire

- accepter ADR-0008 à ADR-0013 ;
- retirer toutes les sections multilingues du plan Wordbench ;
- reclasser `COMMAND_REFERENCE.md` ;
- corriger les métadonnées de statut ;
- établir `IMPLEMENTATION_ALIGNMENT.md` ;
- définir les cinq modules et les cinq ports initiaux.

**Gate :** aucune documentation Wordbench ne promet un registre, un scan ou une matrice multilingue.

### Phase 1 — Tranche verticale minimale

Implémenter :

```text
validate --mode quick
→ charger le projet actif
→ sélectionner une cible/fichier du projet
→ scan statique
→ compilation via GfToolPort
→ RunResult
→ summary.json
→ summary.md
→ manifest.json
```

**Gate :** flux exécutable, testé, sans GUI, sans SemantiK, sans Kristal et sans `gf-portfolio`.

### Phase 2 — Architecture de processus et GF

- introduire `ProcessExecutorPort` ;
- implémenter `LocalProcessExecutor` ;
- introduire `GfToolPort` et l’ACL GF ;
- centraliser timeouts, annulation et preuves brutes ;
- ajouter les tests de processus sans GF réel ;
- ajouter une suite d’intégration GF séparée.

**Gate :** aucun lancement externe hors de l’adaptateur et aucune sémantique GF brute dans le domaine.

### Phase 3 — Orchestration et finalisation

- extraire planner, continuation, classifier, gates et finalizer ;
- réserver un budget de finalisation ;
- écrire les artefacts atomiquement ;
- garantir un manifeste cohérent après timeout ou annulation.

**Gate :** un run interrompu produit un état final explicite et des preuves partielles vérifiables.

### Phase 4 — Scénarios, golds et release

- scénarios `.gfs` ;
- normalisation ;
- gold comparison ;
- PGF ;
- régression ;
- release gates ;
- diagnostics avancés.

**Gate :** aucune preuve manquante ne peut produire un statut release `OK`.

### Phase 5 — Registre d’outils et GUI

- ajouter le registre allowlisté ;
- ajouter les workflows diagnostiques ;
- construire la GUI au-dessus des mêmes cas d’utilisation ;
- vérifier l’équivalence CLI/GUI.

**Gate :** aucune interface ne possède sa propre logique de validation.

### Phase 6 — gf-portfolio séparé

Seulement après stabilisation des schémas Wordbench :

- créer un dépôt ou paquet indépendant ;
- implémenter un registre de workspaces ;
- lire les artefacts publics ;
- produire inventory, matrix et status ;
- ajouter les comparaisons et tendances ;
- conserver toute orchestration distante comme capacité ultérieure optionnelle.

**Gate :** `gf-portfolio` peut être installé ou supprimé sans modifier Wordbench.

## 11. Contrôles automatisés requis

`contracts check --strict` doit notamment détecter :

1. imports privés entre modules ;
2. cycles de dépendances ;
3. imports d’adaptateurs depuis le domaine ;
4. appels `subprocess` hors adaptateur ;
5. commandes GF construites hors ACL GF ;
6. modèles de processus dans le domaine ;
7. écritures d’artefacts hors propriétaire ;
8. références de preuve absentes du manifeste ;
9. commandes documentées absentes du parser ;
10. claims `Implemented` sans tests ;
11. release `OK` avec preuve normative manquante ;
12. dépendance obligatoire envers `gf-portfolio`, SemantiK ou Kristal ;
13. schémas `gf-portfolio.*` présents dans le paquet Wordbench ;
14. commandes ou dossiers Wordbench `languages` dédiés au portefeuille ;
15. opérations IA utilisées comme autorité normative.

## 12. Critères d’acceptation de la version 4

La version 4 remplace la version 3 lorsque :

- la séparation du multilingue est acceptée ;
- ADR-0001 reste applicable ;
- ADR-0011 formalise le module compagnon ;
- le module `languages` est retiré de la cible Wordbench ;
- les commandes et schémas de portefeuille sont retirés de Wordbench ;
- les recommandations P0 possèdent un propriétaire et un critère de sortie ;
- l’état réel de l’implémentation reste suivi dans `IMPLEMENTATION_ALIGNMENT.md`.

## 13. Conclusion

La cible révisée est plus simple et plus cohérente :

> **GF Wordbench valide, explique et libère un projet GF actif. `gf-portfolio` observe et compare plusieurs workspaces Wordbench sans devenir une dépendance de leur exécution.**

Cette séparation préserve le modèle mono-projet accepté, réduit le risque de God Product, clarifie les schémas et permet de développer le portefeuille seulement après stabilisation des contrats Wordbench.
