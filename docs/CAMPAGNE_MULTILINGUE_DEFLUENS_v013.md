# Ars Magna Defluens — campagne pratique multilingue v0.1.3

## Usage sous Windows

Dans `C:\mycode\Grammatical-Framework\GF_Wordbench` :

```powershell
.\Lancer_Campagne_Multilingue.bat check
.\Lancer_Campagne_Multilingue.bat smoke
.\Lancer_Campagne_Multilingue.bat full
```

Par défaut : **20 langues préparées**, **1 scénario** par langue en mode `smoke`, **15 scénarios** par langue en mode `full` (**300 sondes potentielles**). Tu peux cibler un sous-ensemble :

```powershell
.\Lancer_Campagne_Multilingue.bat full Fre Sqi Spa Ger Ita
```

Pour choisir les codes, voir `pilots/practical_generation_v1/language_catalog.json`. Les langues présentes ont des **lexèmes provisoires non approuvés** : tous les résultats GF sont des **candidats soumis à revue**, jamais une couverture linguistique certifiée. Une défaillance d'une sonde peut provenir de sa formulation ou du constructeur GF, pas d'une impossibilité de la langue.

## Résultats

Les rapports vont dans :

`%USERPROFILE%\Downloads\Ars_Magna_Defluens\practical_pilot_runs`

Chaque campagne crée :

- `defluens-batch-smoke-<id>/batch_summary.json` — états consolidés, conservés après **chaque langue**.
- `defluens-batch-smoke-<id>/batch_summary.csv` — feuille récapitulative, compatible Excel.
- `defluens-batch-smoke-<id>/languages/` — sorties GF complètes et ZIP par langue.
- `defluens-batch-smoke-<id>.zip` — **une seule archive globale à envoyer** (rapports et journaux, sans les binaires `.gfo`).

Le lancement ne modifie **jamais** les sources GF RGL. Une langue en erreur n'empêche pas les autres tests. Un délai de 90 secondes est appliqué par sonde et le lanceur arrête de programmer de nouvelles langues après 45 minutes (les résultats réalisés sont conservés). Le temps maximal n'interrompt pas un scénario déjà lancé.

**Attention :** `candidate_for_review` signifie que GF a émis un texte non vide sans erreur détectée; la justesse des mots, de la syntaxe, du sens et de l'idiomaticité n'a pas été confirmée. `probe_failed` / `setup_error` signifient échec de sonde ou outillage, pas impossibilité linguistique; `timeout` n'est pas un échec grammatical prouvé. `semantic_coverage_verified` reste toujours `false`.

## Limites actuelles

- GF 3.12 Windows n'est pas disponible dans notre environnement de préparation; les profils ajoutés sont vérifiés statiquement, **pas exécutés sur une vraie RGL**.
- La campagne exécute les pilotes existants; elle **n'est pas encore le mécanisme définitif d'orchestration GitOps** d'Ars Magna Defluens.
- Les scores de couverture certifiée seront définis seulement après revue humaine et rapprochement avec les preuves canoniques WordBench.
- Pour une extension au-delà des 20 langues préparées, ajouter les lexèmes au catalogue, régénérer les profils puis les vérifier; ne pas fabriquer de sortie certifiée.
