# Ars Magna Defluens: installe un correctif extrait, meme s'il est dans Downloads.
# Ne modifie jamais gf-rgl, ni les journaux historiques.
[CmdletBinding()]
param([string]$Destination = 'C:\mycode\Grammatical-Framework\GF_Wordbench')
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $PSScriptRoot).Path
if (-not (Test-Path -LiteralPath (Join-Path $source 'pilots\practical_generation_v1\lexical_stabilization_focus14_v021.json'))) {
  throw "Ce dossier n'est pas le correctif v0.2.1. Extrais le ZIP d'abord."
}
if (-not (Test-Path -LiteralPath (Join-Path $Destination 'src\gf_wordbench\practical\pilot.py'))) {
  throw "WordBench complet introuvable: $Destination. Installe le correctif dans le depot complet existant."
}
$oldPythonPath = $env:PYTHONPATH
$pushed = $false
try {
  if (-not ($source -ieq (Resolve-Path -LiteralPath $Destination).Path)) {
    & robocopy.exe $source $Destination /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
    $copyCode = $LASTEXITCODE
    if ($copyCode -ge 8) { throw "Echec de la copie des fichiers ($copyCode)." }
  }
  Push-Location -LiteralPath $Destination
  $pushed = $true
  $env:PYTHONPATH = "$(Join-Path $Destination 'src');$oldPythonPath"
  $pythonLauncher = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
  $pythonArgs = @()
  if ($pythonLauncher -eq 'py') { $pythonArgs = @('-3') }
  & $pythonLauncher @pythonArgs -m gf_wordbench.practical.alignment14 verify --rgl-root 'C:\mycode\Grammatical-Framework\gf-rgl'
  if ($LASTEXITCODE -ne 0) { throw 'Les empreintes WordBench sont incoherentes apres installation.' }
  Write-Host "Correctif v0.2.1 installe et 210 sondes pre-verifiees dans $Destination" -ForegroundColor Green
  Write-Host 'Pour les 31 reparations GF: .\Lancer_Sondes_Corrigees_14_Langues.bat'
  Write-Host 'Puis: .\Lancer_Alignement_14_Langues.bat full'
}
finally {
  $env:PYTHONPATH = $oldPythonPath
  if ($pushed) { Pop-Location }
}
