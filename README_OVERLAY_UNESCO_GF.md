# GF Wordbench — overlay candidat UNESCO

Racine à utiliser : `C:\mycode\Grammatical-Framework\GF_Wordbench` (**pas** `C:\mycode\SemantiK_Architect\GF_Wordbench`).

Ajoute `tools/unesco_gf_build.py` sans modifier le cœur GF Wordbench. La fabrique l'appelle uniquement après avoir généré un dossier candidat privé. Il utilise les **commandes GF** et le **process runner natifs de Wordbench**, avec un timeout et des journaux distincts, et n'accepte un candidat que si le processus se termine sans erreur **et** produit un PGF non vide.

Exécutable GF documenté par les lanceurs Wordbench : `C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe`.

Exemple (dossier candidat généré par la fabrique) :

```powershell
py -3.12 tools/unesco_gf_build.py --candidate "C:\chemin\vers\candidates\fr" --lang fr
```

**Portée :** `PGF_BUILT_CANDIDATE_ONLY` signifie construction expérimentale, pas conformité linguistique, pas publication, pas release. Aucune grammaire n'est générée par cette commande, aucun gold n'est mis à jour. Les fichiers `.gfo/.pgf` et logs sont générés dans le dossier candidat, jamais dans les sources Wordbench.

Test ciblé : `py -3.12 -m unittest discover -s tools -p test_unesco_gf_build.py -v`.
