# Install this DELTA into the existing WordBench repository, never into gf-rgl.
param([string]$Destination = 'C:\mycode\Grammatical-Framework\GF_Wordbench')
$ErrorActionPreference = 'Stop'
$src = Split-Path -Parent $MyInvocation.MyCommand.Path
$dst = [System.IO.Path]::GetFullPath($Destination)
if (-not (Test-Path -LiteralPath (Join-Path $src 'pilots\practical_generation_v1\lexical_stabilization_focus14_v022.json'))) {
  throw 'Correctif v0.2.2 introuvable dans ce dossier.'
}
if (-not (Test-Path -LiteralPath (Join-Path $dst 'src\gf_wordbench\practical\pilot.py'))) {
  throw 'Installation WordBench complete introuvable. Ne pas lancer le correctif depuis Downloads.'
}
$policy = Get-Content -Raw -Encoding UTF8 (Join-Path $src 'pilots\practical_generation_v1\lexical_stabilization_focus14_v022.json') | ConvertFrom-Json
foreach ($c in $policy.changes) {
  $module = 'Defluens' + (($c.scenario -split '-' | ForEach-Object { (Get-Culture).TextInfo.ToTitleCase($_) }) -join '') + $c.lang + '.gf'
  $actual = Join-Path $dst ("pilots\practical_generation_v1\{0}\validation\inputs\{1}" -f $c.lang,$module)
  if (-not (Test-Path -LiteralPath $actual)) { throw "Source WordBench absente: $actual" }
  $hash = (Get-FileHash -LiteralPath $actual -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hash -ne $c.previous_sha256 -and $hash -ne $c.source_sha256) {
    throw "Source modifiee localement: $actual. Installation arretee sans ecraser ce fichier."
  }
}
& robocopy $src $dst /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Robocopy a echoue (code $LASTEXITCODE)." }
Write-Host 'Correctif v0.2.2 installe dans WordBench.' -ForegroundColor Green
Write-Host "cd `"$dst`"; .\Lancer_Sondes_Corrigees_14_Langues_v022.bat"
exit 0
