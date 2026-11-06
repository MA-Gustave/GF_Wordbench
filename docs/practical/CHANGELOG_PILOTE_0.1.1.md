# Ars Magna Defluens — pilote pratique 0.1.1

2026-11-03

- Premier essai GF natif observé pour `Eng smoke` : le scénario `factual-present` a généré `Mira is ready` avec code retour 0, sans approbation gold. Aucun des 15 critères sémantiques n'a été déclaré prêt sur cette seule base.
- Le lanceur `Lancer_Pilote_Pratique.bat` enregistre **les prochaines exécutions** dans `%USERPROFILE%\Downloads\Ars_Magna_Defluens\practical_pilot_runs`.
- Avec ce lanceur, chaque exécution `smoke` / `full` génère aussi un ZIP (`defluens-pilot-<code>-<run-id>.zip`) à côté du dossier du résultat. Le ZIP inclut `pilot_run.json`, `review_template.json`, les candidats, les journaux et les inputs de test.
- Pour la CLI directe, l'option `--export-zip` active l'archive ; `--output-root` continue de choisir la destination.
- Les rapports existants sous `GF_Observatory_Diagnostic` ne sont ni modifiés ni supprimés.
- Les scénarios sont inchangés ; la validation linguistique reste soumise à une revue et à une référence gold approuvée.
