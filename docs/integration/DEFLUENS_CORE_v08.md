# Candidate PGF builder — Defluens v0.8

`tools/build_semantik_profile3_candidate.py` accepte désormais les profils `defluens-core-fr-1` et `defluens-core-en-1` en plus des anciens profils v0.5/v0.7.

**Autorité des sources :** `SemantiK_Architect/profiles/defluens-core-1/` (abstract GF commun, deux grammaires concrètes, pont, lexique, profil et suite par langue). WordBench copie les fichiers approuvés, compile avec GF officiel/RGL locale, puis produit `grammar.pgf`, les artefacts SA, un `pipeline.lock.json` aux empreintes SHA-256 et `build-report.json`.

Exemples (Windows; remplacer les chemins si installation différente) :

```powershell
$wb = 'C:\mycode\Grammatical-Framework\GF_Wordbench'
$sa = 'C:\mycode\SemantiK_Architect\SemantiK_Architect'
$gf = 'C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe'
$rgl = 'C:\mycode\Grammatical-Framework\gf-rgl'
$out = "$env:USERPROFILE\Downloads\Ars_Magna_Defluens\semantik_candidates"
python "$wb\tools\build_semantik_profile3_candidate.py" --semantik-root $sa --gf-exe $gf --rgl-root $rgl --profile defluens-core-fr-1 --output "$out\defluens-core-fr-1" --timeout 420 --force
python "$wb\tools\build_semantik_profile3_candidate.py" --semantik-root $sa --gf-exe $gf --rgl-root $rgl --profile defluens-core-en-1 --output "$out\defluens-core-en-1" --timeout 420 --force
```

Aucun artéfact n'est publié, aucun système de grammaticalité n'est remplacé; un PGF absent ou invalide bloque la prévisualisation Semantic Architect. Les sondes pratiques de WordBench continuent séparément.
