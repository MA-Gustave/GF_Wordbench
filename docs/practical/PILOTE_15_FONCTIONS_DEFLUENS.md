# Ars Magna Defluens — pilote pratique GF de 15 capacités

**Version du pilote :** 0.1.1 (3 novembre 2026) — **premier test GF réel `Eng smoke` confirmé** (sortie candidate « Mira is ready », code 0 ; sans gold approuvé).

## Ce qui a été réalisé

- 15 opérations d'information et d'instruction issues du profil `profiles/practical_generation_v1.json` ; 5 facultatives restent hors périmètre.
- Trois ensembles pilotes : `Eng` (anglais), `Fre` (français), `Sqi` (albanais).
- 45 scripts GF natifs `.gfs` (un par scénario et langue), 45 modules GF abstraits et 45 modules concrets utilisant `SyntaxEng/Fre/Sqi` et `ParadigmsEng/Fre/Sqi`.
- Contrôle de syntaxe des scénarios WordBench et des empreintes SHA-256 des entrées GF ; une modification de source non répercutée bloque l'exécution.
- Exécution avec le **mécanisme de processus GF de WordBench**, temporisation, journaux stdout/stderr distincts, copie des entrées dans un dossier jetable ; aucun changement dans `gf-rgl`.
- Rapport indépendant `pilot_run.json`, extraits `.candidate.txt` et `review_template.json` avec approbation initialement `false`.

Le pilote est **une première couche d'exécution**, pas encore une campagne de certification ni un résultat `ready` consommable par Observatory. Ce dernier requiert un rapport WordBench canonique accompagné d'un manifeste de preuves vérifié.

## Essai recommandé sur Windows

Depuis le répertoire du dépôt GF WordBench, avec Python 3.11+ :

```bat
Lancer_Pilote_Pratique.bat Eng check
Lancer_Pilote_Pratique.bat Eng smoke
```

Le premier ne lance pas GF : il vérifie 15 scénarios et les sources verrouillées. Le second lance **un seul scénario** réel (fait au présent), limité à 120 secondes. Ensuite, pour la campagne complète :

```bat
Lancer_Pilote_Pratique.bat Eng full
Lancer_Pilote_Pratique.bat Fre full
Lancer_Pilote_Pratique.bat Sqi full
```

Chaque programme lit par défaut :

- `C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe`
- `C:\mycode\Grammatical-Framework\gf-rgl`
- `C:\Users\<user>\Downloads\Ars_Magna_Defluens\practical_pilot_runs`

Pour d'autres emplacements, invoquer le module Python directement :

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
py -3 -m gf_wordbench.practical.pilot run --language Eng `
  --gf-executable "C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe" `
  --rgl-root "C:\mycode\Grammatical-Framework\gf-rgl" `
  --output-root "$HOME\Downloads\Ars_Magna_Defluens\practical_pilot_runs" `
  --export-zip --timeout 120 --scenario factual-present
```

Le `--scenario` est facultatif, et peut être répété pour un sous-ensemble. Le pilote ne lance aucune compilation lors d'un simple `check`.

## À récupérer après le test

Dans `Downloads/Ars_Magna_Defluens/practical_pilot_runs/defluens-pilot-Eng-<date>/` :

- `pilot_run.json` : bilan par capacité, sans faux succès ;
- `scenarios/factual-present.stdout.txt`, `.stderr.txt` : preuves brutes ;
- `scenarios/factual-present.candidate.txt` : sortie générée, si la sonde a abouti ;
- `review_template.json` : support à la revue linguistique (toutes les décisions initialement `approved: false`).

**Le BAT crée également `defluens-pilot-Eng-<date>.zip` au même niveau que ce dossier.** Le ZIP conserve le JSON, les sources compilées, les sorties et les journaux. Les anciens rapports situés sous `GF_Observatory_Diagnostic` ne sont ni déplacés ni supprimés.

**Envoie le ZIP (ou le `pilot_run.json` et le journal de toute sonde en erreur)** : cela permettra de corriger les expressions GF incompatibles avec ta version de RGL, d'abord en anglais, ensuite dans les deux autres langues.

## Interprétation stricte

| Statut pilote | Signification |
|---|---|
| `candidate_for_review` | GF a produit une sortie non vide dans un segment valide, mais elle n'a **pas** été approuvée linguistiquement. |
| `probe_failed` | GF ou le processus a échoué / signalé un problème. Diagnostic à analyser : cela ne prouve pas l'absence de capacité. |
| `timeout` | Délai dépassé, sans conclusion linguistique. |
| `unverified` | Aucune preuve valide n'existe encore. |

Le score pratique WordBench `passed` et le statut Observatory `ready` restent **indisponibles** tant qu'une référence gold approuvée n'a pas été comparée et que le manifeste WordBench n'a pas été vérifié. L'extraction d'une phrase ou un code de retour `0` ne suffit pas.

## Séparation des responsabilités

- **GF/RGL** : génère les constructions depuis `SyntaxXXX` et `ParadigmsXXX` ;
- **WordBench** : réalise les tests pilotes, conserve les traces et permettra la future comparaison gold canonique ;
- **Ars Magna Defluens** : pilotera ensuite les séries de langues et les reprises ;
- **Observatory** : lira les preuves canoniques validées lorsque le raccordement sera terminé.

Les lexèmes fournis dans les modules concrets sont **des amorces provisoires**. Le français et l'albanais en particulier peuvent nécessiter des paramètres morphologiques propres à chaque langue avant toute revue. L'utilisateur peut modifier les entrées de tests, puis relancer `python tools/generate_practical_pilots.py` pour recalculer les verrous SHA (cela écrase les sources du pilote, jamais des RGL).
