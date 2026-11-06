# Rapport d’applicabilité des patterns du Senior Architect Codex à GF Wordbench

**Date d’analyse :** 2026-07-24  
**Base GF Wordbench :** export documentaire `GF_Wordbench_20260724_120940_*`  
**Référence :** `Senior_Architect_Codex(5).txt`

## 1. Portée et limite de validation

Cette analyse compare les patterns du Codex avec les ADR, contrats, guides d’architecture, documents de validation, documents de projet et scripts présents dans l’export GF Wordbench.

L’export contient les volumes suivants :

- racine ;
- `docs/` ;
- `templates/` ;
- `project/` ;
- `tools/`.

Il ne contient pas le code applicatif principal ni sa suite de tests. Par conséquent :

- l’**adoption documentaire et architecturale** peut être validée ;
- la **présence effective dans le code** ne peut pas être certifiée depuis cet export ;
- une décision ADR acceptée ne constitue pas, à elle seule, une preuve d’implémentation.

## 2. Conclusion exécutive

GF Wordbench applique correctement les patterns structurels et de résilience qui correspondent à sa nature :

- monolithe modulaire ;
- architecture hexagonale ;
- anti-corruption layer autour de GF ;
- budgets de temps et finalisation réservée ;
- continuation contrôlée et préservation des preuves ;
- opérations idempotentes ou atomiques aux frontières sensibles ;
- journalisation structurée et corrélation par identifiants de run/opération.

Le Codex est principalement conçu pour les systèmes distribués : microservices, trafic réseau, bases distribuées, brokers, déploiements progressifs et infrastructure à grande échelle. GF Wordbench est au contraire défini comme une application locale au premier plan, sans démon, file de messages, base obligatoire ou service réseau. La majorité des patterns distribués ne doivent donc pas être ajoutés tant que leur problème déclencheur n’existe pas.

## 3. Légende

| Statut | Sens |
|---|---|
| **Adopté** | Le pattern correspond directement à une décision ou à un contrat Wordbench. |
| **Adapté** | Le besoin est couvert sous une forme locale ou simplifiée, sans implémenter la forme distribuée complète du Codex. |
| **Conditionnel** | Inutile actuellement, mais à reconsidérer si une dépendance ou un mode d’exploitation précis apparaît. |
| **Non requis** | Le problème traité par le pattern n’existe pas dans l’architecture actuelle. Son ajout serait de la surarchitecture. |

## 4. Matrice complète des 33 patterns

| # | Pattern | Statut | Validation pour GF Wordbench |
|---:|---|---|---|
| 1 | Circuit Breaker | **Conditionnel** | Pas de service réseau permanent ni de chaîne de microservices. À envisager uniquement pour de futurs outils distants ou API externes présentant des défaillances répétées. |
| 2 | Bulkhead | **Adapté** | Isolation par processus GF, scénarios en processus frais, séparation des propriétaires de stages et planification séquentielle bornée. Il ne s’agit pas de pools de ressources indépendants au sens serveur. |
| 3 | Exponential Backoff + Jitter | **Conditionnel** | Les retries automatiques sont volontairement désactivés par défaut afin de préserver déterminisme, provenance et absence d’effets dupliqués. À ajouter seulement pour une erreur transitoire réseau clairement classifiée. |
| 4 | Graceful Degradation | **Adopté** | Continuation des travaux indépendants, visibilité des avertissements, stages optionnels non bloquants, préservation des preuves partielles et finalisation contrôlée. |
| 5 | Rate Limiting / Throttling | **Adapté** | Wordbench utilise budgets globaux et par stage, limites de sortie, concurrence bornée et registre d’outils limité. Il n’existe pas de trafic multi-utilisateur nécessitant un limiteur de requêtes. |
| 6 | Timeout Budgets | **Adopté** | ADR dédié, délais finis pour chaque processus, budget global, budgets de stages et réserve protégée de finalisation. |
| 7 | Strangler Fig | **Adapté** | La migration depuis GF Audit utilise lecture des formes historiques, écriture canonique séparée et confinement de la compatibilité dans les loaders/migrateurs. Il n’y a toutefois ni proxy de trafic ni coexistence de services. |
| 8 | Anti-Corruption Layer | **Adopté** | ADR dédié. Toutes les interactions GF passent par `GfToolPort` et les adaptateurs GF ; les formats, commandes et diagnostics externes ne doivent pas contaminer le domaine. |
| 9 | Sidecar | **Non requis** | Aucun déploiement en pods ou service nécessitant un compagnon d’infrastructure. Les responsabilités communes restent dans les adaptateurs et services internes. |
| 10 | Hexagonal Architecture | **Adopté** | Architecture explicitement organisée en domaine, application, ports, adaptateurs, entrypoints et bootstrap. |
| 11 | Backend for Frontend | **Non requis** | CLI et GUI doivent partager la même frontière applicative et les mêmes politiques. Créer des backends distincts introduirait une divergence contraire aux contrats. |
| 12 | CQRS | **Non requis** | Pas de domaine transactionnel complexe ni de besoins de mise à l’échelle asymétrique lecture/écriture. Les rapports sont des vues dérivées, mais cela ne constitue pas du CQRS. |
| 13 | Event Sourcing | **Non requis** | Les runs et preuves sont conservés, mais ils ne reconstruisent pas l’état applicatif par rejeu d’événements. Ne pas confondre historique de preuves et event sourcing. |
| 14 | Saga | **Non requis** | Aucune transaction distribuée entre services autonomes. Les étapes du pipeline sont une orchestration locale avec dépendances, pas une saga. |
| 15 | Idempotency | **Adopté** | Finalisation idempotente, écritures atomiques ou remplaçables, retries autorisés seulement pour opérations idempotentes et interdiction d’écraser les preuves précédentes. Aucun mécanisme HTTP `Idempotency-Key` n’est requis. |
| 16 | Transactional Outbox | **Non requis** | Pas de base transactionnelle couplée à un broker de messages. |
| 17 | Sharding / Partitioning | **Non requis** | Pas de stockage distribué ni de volume démontré exigeant une partition horizontale. |
| 18 | Cache-Aside | **Non requis** | Les contrats privilégient les preuves courantes et rejettent les artefacts périmés. Ajouter un cache applicatif risquerait de réduire la confiance sans besoin démontré. |
| 19 | Static Content Offloading / CDN | **Non requis** | Pas de distribution publique de contenu statique à grande échelle. |
| 20 | Dead Letter Queue | **Non requis** | Aucun broker ni consommateur asynchrone. |
| 21 | Pub/Sub | **Non requis** | Aucun bus d’événements requis. Les modules communiquent localement via frontières applicatives explicites. |
| 22 | Claim Check | **Non requis** | Les références vers des fichiers de preuve ressemblent superficiellement au pattern, mais elles ne transportent pas de gros payloads via une file de messages. |
| 23 | Blue-Green Deployment | **Non requis** | Wordbench est un produit local/package, pas un service routé entre deux environnements actifs. |
| 24 | Canary Release | **Non requis** | Aucun trafic de production à fractionner. Les validations de release et compatibilité sont le mécanisme approprié. |
| 25 | Immutable Infrastructure | **Non requis** | L’immutabilité des résultats, manifests ou artefacts est pertinente, mais ce n’est pas de l’infrastructure immuable. |
| 26 | Distributed Tracing | **Adapté** | `run_id`, identifiants d’opération, stages, sujets et chemins de preuve fournissent une corrélation locale. OpenTelemetry et propagation interservices ne sont pas justifiés. |
| 27 | Health Check API | **Adapté** | Préflight, résolution GF, sonde de version, validation des chemins et du répertoire de sortie couvrent la santé locale. Une API `/health` n’a pas de sens sans mode démon/service. |
| 28 | Log Aggregation | **Adapté** | `master.log`, logs structurés, stdout/stderr séparés et répertoire de run constituent une agrégation locale par run. Aucun collecteur central n’est nécessaire. |
| 29 | Metrics & Alerting | **Conditionnel** | Quelques métriques peuvent être enregistrées, mais alerting et dashboards ne sont utiles que pour une exécution non supervisée, un service persistant ou une flotte CI significative. |
| 30 | Cell-Based Architecture | **Non requis** | Aucun besoin d’isolation par cellule, de blast radius régional ou d’échelle massive. |
| 31 | Modular Monolith | **Adopté** | Choix architectural central : un seul déploiement, cinq modules fonctionnels cohésifs et frontières strictes. |
| 32 | Sidecarless Service Mesh / eBPF | **Non requis** | Pas de mesh, pods ou communication interservices. |
| 33 | Data Mesh | **Non requis** | Pas d’organisation de domaines de données distribués ni de plateforme analytique multi-équipes. |

## 5. Ce qui paraît déjà solidement couvert

### 5.1 Structure

- monolithe modulaire ;
- séparation fonctionnelle `projects`, `runs`, `validation`, `diagnostics`, `reporting` ;
- direction de dépendance hexagonale ;
- ports et adaptateurs ;
- bootstrap comme composition root ;
- CLI et GUI sur la même frontière applicative.

### 5.2 Intégration GF

- GF reste l’autorité sémantique ;
- frontière `GfToolPort` ;
- construction de commandes centralisée ;
- exécution externe centralisée ;
- stdout et stderr séparés ;
- diagnostics externes convertis vers les modèles Wordbench ;
- outils diagnostiques exécutables allowlistés.

### 5.3 Résilience d’exécution

- timeouts finis ;
- budget global ;
- budgets de stages ;
- réserve de finalisation ;
- arrêt contrôlé des processus enfants ;
- conservation des preuves partielles ;
- distinction timeout, annulation, échec de lancement et échec GF ;
- retries interdits par défaut et bornés lorsqu’ils sont explicitement autorisés.

### 5.4 Observabilité et preuve

- identifiants de run et d’opération ;
- journal maître structuré ;
- traces brutes distinctes ;
- résultats structurés ;
- manifest avec empreintes ;
- conservation des erreurs antérieures lors d’un retry ;
- rapports dérivés des résultats et non d’une nouvelle exécution.

## 6. Ce qui pourrait manquer — à confirmer dans le code et les tests

Les points suivants sont déjà prescrits par la documentation, mais leur implémentation ne peut pas être prouvée avec l’export fourni.

### Priorité 1 — Tests d’architecture

Vérifier l’existence de tests qui prouvent :

1. l’interdiction d’importer les adaptateurs depuis le domaine ou l’application ;
2. le passage de toute opération GF par `GfToolPort` ;
3. l’absence de construction de commandes GF dans le domaine ;
4. l’unicité de l’orchestrateur de run ;
5. l’absence de politique différente entre CLI et GUI.

### Priorité 2 — Tests de budgets et de finalisation

Vérifier :

1. budget global épuisé avant lancement d’un nouveau stage ;
2. réserve de finalisation réellement protégée ;
3. terminaison de l’arbre de processus après timeout ;
4. préservation de stdout/stderr partiels ;
5. finalisation idempotente ;
6. écriture atomique de `summary.json` et `manifest.json` ;
7. absence d’artefact périmé accepté après un échec.

### Priorité 3 — Tests de continuation contrôlée

Vérifier :

1. un échec de fichier ne bloque pas les sujets indépendants ;
2. un prérequis échoué bloque ses dépendants ;
3. un stage optionnel reste visible sans modifier abusivement le statut global ;
4. la poursuite après échec ne transforme jamais un échec en succès ;
5. un mode fail-fast produit des `SKIPPED` explicites.

### Priorité 4 — Tests de retry et d’idempotence

Vérifier :

1. aucun retry implicite après timeout ;
2. chaque tentative utilise un identifiant et des chemins de preuve distincts ;
3. la première tentative n’est jamais écrasée ;
4. seules les opérations explicitement idempotentes sont retryables ;
5. les builds GF, scénarios et mises à jour de gold ne sont pas relancés automatiquement.

### Priorité 5 — Observabilité locale

Vérifier :

1. présence constante de `run_id`, stage, opération et sujet dans le journal maître ;
2. commandes journalisées identiques aux commandes exécutées, après redaction ;
3. stdout/stderr toujours séparés ;
4. limites de taille visibles et non silencieuses ;
5. tracebacks conservés dans les artefacts de débogage sans fuite de secrets.

## 7. Patterns à ne pas ajouter maintenant

Les patterns suivants doivent rester absents tant que leur déclencheur n’existe pas :

```text
CQRS
Event Sourcing
Saga
Transactional Outbox
Sidecar
BFF
Sharding
Cache-Aside
CDN
DLQ
Pub/Sub
Claim Check
Blue-Green
Canary
Immutable Infrastructure
Cell-Based Architecture
Sidecarless Service Mesh
Data Mesh
```

Leur ajout créerait de nouvelles sources de défaillance, de configuration, de synchronisation et de maintenance sans résoudre un besoin actuel.

## 8. Déclencheurs futurs explicites

| Évolution future | Patterns à reconsidérer |
|---|---|
| Outils IA ou diagnostics appelés via réseau | Circuit Breaker, Backoff + Jitter, Rate Limiting |
| Wordbench devient un démon ou un service réseau | Health Check API, Metrics & Alerting |
| Exécutions concurrentes multi-utilisateurs | Bulkheads de ressources, Rate Limiting |
| Broker de messages introduit | Pub/Sub, DLQ, Claim Check, Transactional Outbox, idempotence de consommateurs |
| Base distribuée ou plusieurs services transactionnels | Saga, éventuellement CQRS/Event Sourcing selon les besoins |
| Déploiement serveur continu avec trafic réel | Blue-Green, Canary, Immutable Infrastructure |
| Plusieurs instances ou services coopèrent | Distributed Tracing réel |
| Échelle ou blast radius massif démontré | Sharding, Cell-Based Architecture |

## 9. Recommandation documentaire

Créer un document court :

```text
docs/architecture/PATTERN_APPLICABILITY.md
```

Il devrait contenir :

- la matrice des 33 patterns ;
- le statut `Adopté`, `Adapté`, `Conditionnel` ou `Non requis` ;
- le problème déclencheur ;
- le propriétaire de la décision ;
- les tests qui prouvent les patterns adoptés ;
- les conditions précises qui autorisent de reconsidérer un pattern non requis.

Ce document éviterait que de futures corrections ou propositions réintroduisent des architectures distribuées contraires au caractère local et mono-déploiement de GF Wordbench.

## 10. Verdict

L’architecture documentaire est cohérente avec le Codex lorsqu’on applique le principe le plus important du Codex lui-même : **ne pas introduire un pattern sans le problème qu’il résout**.

Le manque principal n’est pas l’absence de nouveaux patterns. Le manque à vérifier est la preuve que les patterns déjà décidés sont effectivement respectés par le code et les tests.
