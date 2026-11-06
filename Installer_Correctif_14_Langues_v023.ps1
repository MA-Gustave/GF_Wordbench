param([string]$Destination = 'C:\mycode\Grammatical-Framework\GF_Wordbench')
$ErrorActionPreference = 'Stop'
$src = Split-Path -Parent $MyInvocation.MyCommand.Path
$dst = [System.IO.Path]::GetFullPath($Destination)
$rel = 'pilots\practical_generation_v1\lexical_stabilization_focus14_v023.json'
if (-not (Test-Path -LiteralPath (Join-Path $src $rel))) { throw 'Correctif v0.2.3 introuvable.' }
if (-not (Test-Path -LiteralPath (Join-Path $dst 'src\gf_wordbench\practical\pilot.py'))) { throw 'Depot WordBench complet introuvable.' }
$policy = Get-Content -LiteralPath (Join-Path $src $rel) -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($c in $policy.changes) {
  $path = Join-Path $dst ("pilots\practical_generation_v1\{0}\validation\inputs\{1}" -f $c.lang,$c.module)
  if (-not (Test-Path -LiteralPath $path)) { throw "Source manquante : $path" }
  $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  if (($hash -ne $c.previous_sha256) -and ($hash -ne $c.source_sha256)) {
    throw "Source GF modifiee localement : $path. Installation annulee."
  }
}
# Copy only delta content, preserve RGL and prior reports.
& robocopy $src $dst /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Robocopy a echoue (code $LASTEXITCODE)." }
Write-Host "Correctif v0.2.3 installe dans $dst" -ForegroundColor Green
Write-Host 'Executer : .\Lancer_Sondes_Corrigees_14_Langues_v023.bat'
exit 0
