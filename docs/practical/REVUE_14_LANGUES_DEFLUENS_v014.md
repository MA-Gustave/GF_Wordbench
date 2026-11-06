# Ars Magna Defluens — Validation linguistique ciblée 14 langues (v0.1.4)

## Portée

`Eng Fre Spa Ger Dut Swe Dan Nor Nno Fin Est Afr Ita Por`.
Les six autres langues du lot v0.1.3 sont exclues de cette phase. Il s'agit des
**14 langues qui ont produit 15 candidates sur 15** dans le test GF du 3 novembre 2026.
La sélection est fixe, et indépendante du défaut de 20 langues du lanceur ancien.

## Procédure

Dans le dossier `GF_Wordbench`, utiliser :

```bat
Lancer_Revue_14_Langues.bat audit
```

Sans lancer GF, cette commande charge le **dernier rapport ZIP FULL** conservé dans
`%USERPROFILE%\Downloads\Ars_Magna_Defluens\practical_pilot_runs`, isole
les 14 langues, vérifie la cohérence des 210 sorties (rapport, candidat brut,
marqueurs de journal, empreintes de code et de script) et prépare :

- `defluens-review14-<batch-id>\Revue_14_langues.html` : revue humaine interactive hors ligne ;
- `review14_summary.json` : matrice machine, empreintes de preuves, alertes non exhaustives ;
- `review14_candidates.csv` : export facile à filtrer ;
- `defluens-review14-<batch-id>.zip` : archive partageable de la revue.

Ouvrir `Revue_14_langues.html`, filtrer les alertes, examiner aussi les phrases
sans alerte, fournir le nom du réviseur, enregistrer chaque décision, puis
**Exporter mes décisions JSON**. Une approbation n'est admise que si la référence
est rigoureusement identique à la phrase réellement produite par GF. Une forme
corrigée sera classée « à corriger », pas « approuvée ».

Pour vérifier les décisions (sans retester GF) :

```bat
Lancer_Revue_14_Langues.bat finalize "C:\chemin\vers\defluens-review14-decisions-....json"
```

La commande retrouve automatiquement le bon ZIP source par son SHA-256, même
après une nouvelle campagne, et produit `review14_results.json`. Elle refuse
les décisions dupliquées, les empreintes modifiées, les approbations anonymes
et les rejets sans justification. Ne produit **aucun gold canonique**.

## Répétabilité (test renforcé)

```bat
Lancer_Revue_14_Langues.bat repeat
Lancer_Revue_14_Langues.bat compare
```

`repeat` lance réellement GF pour **14 × 15 = 210** scénarios ; il n'inclut
aucune des six autres langues. `compare` compare les 210 phrases et les
empreintes de script/module entre les deux dernières campagnes complètes.
Une sortie identique est une preuve de répétabilité, PAS une preuve de correction
sémantique générale.

## Ce qui n'est pas encore certifié

- La validité linguistique des 210 phrases n'est pas prouvée par la seule exécution.
- Les 59 signalements du premier rapport sont des hypothèses de revue ciblées,
  non exhaustives et associées **à la chaîne de sortie exacte**.
- Les 151 sorties sans signalement restent tout autant non vérifiées.
- Aucun changement automatique n'est appliqué aux fichiers RGL ou aux golds.
- L'intégration finale au processus WordBench canonique d'approbation des golds
  devra être faite après revue, corrections et nouveau test.
