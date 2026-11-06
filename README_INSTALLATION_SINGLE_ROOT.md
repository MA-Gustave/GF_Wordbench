# GF WordBench — installation dans la racine Git existante

**Racine canonique sur cette machine :**

`C:\mycode\Grammatical-Framework\GF_Wordbench\GF_Wordbench\.git`

Le répertoire qui contient `.git`, `pyproject.toml`, `src`, `docs`, `tests`,
`pilots` et `Qualification_Langues_Utiles.pyw` est **le dépôt WordBench**.
Le répertoire parent `GF_Wordbench` sert de contenant; il ne doit pas être
utilisé comme deuxième copie Python.

```text
C:\mycode\Grammatical-Framework\
  GF_Wordbench\
    GF_Wordbench\       <-- dépôt Git, UNE SEULE racine de code
      .git\             <-- existant, conservé
      pyproject.toml
      README.md
      src\gf_wordbench\
      tests\
      pilots\
      Qualification_Langues_Utiles.pyw
      launch_gui.bat
  gf-3.12-windows\gf.exe
  gf-rgl\src\
```

## Mise à jour in situ (sans supprimer .git)

1. Fermer WordBench et interrompre toute campagne en cours.
2. Copier le dossier du dépôt en sauvegarde ou faire un commit/sauvegarde
   des modifications locales. L'archive contient des sources, **pas** `.git`.
3. Extraire **directement dans le répertoire contenant `.git`** :

```powershell
$repo = 'C:\mycode\Grammatical-Framework\GF_Wordbench\GF_Wordbench'
$zip  = "$env:USERPROFILE\Downloads\GF_WordBench_v1.2.1_GIT_ROOT_CONTENTS.zip"
if (-not (Test-Path -LiteralPath "$repo\.git")) { throw 'Racine Git incorrecte : .git absent' }
Expand-Archive -LiteralPath $zip -DestinationPath $repo -Force
Test-Path "$repo\GF_Wordbench"       # attendu : False
Test-Path "$repo\pyproject.toml"     # attendu : True
Test-Path "$repo\.git"               # attendu : True
```

**Ne pas** extraire le ZIP à `Grammatical-Framework` ou dans le dossier
contenant `GF_Wordbench` : l'archive est volontairement sans préfixe.

## Lancer

```powershell
Set-Location 'C:\mycode\Grammatical-Framework\GF_Wordbench\GF_Wordbench'
py -3 -m pip install -e .
.\launch_gui.bat
```

Dans la fenêtre Qt, utiliser **Run → Practical Qualification…**.
Par défaut, les 14 langues actuellement retenues sont sélectionnées et le mode
`full` vérifie les 15 capacités linguistiques pratiques par langue (210
sondes). Aucun temps verbal additionnel ni capacité facultative n'est ajouté.
La réussite technique ne remplace pas la revue linguistique humaine.

## Vérification sans compiler GF

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
py -3 -m gf_wordbench.practical.batch check --languages Eng Fre Spa Ger Dut Swe Dan Nor Nno Fin Est Afr Ita Por
```

Le dossier `.git`, les environnements virtuels et les sorties de campagne ne
font pas partie de la livraison. Le contenu externe au dépôt n'est pas effacé.
